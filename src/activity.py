"""第二阶段：解析公告正文，获取活动页面真实 URL"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .config import ARTICLE_DETAIL_API, JOIN_BUTTON_KEYWORDS, SUFFIX_ORIGIN
from .discover import Competition
from .http_client import ApiError, get_json


@dataclass
class ArticleDetail:
    """公告详情"""

    article_id: int | None
    title: str
    body_tree: dict

    @property
    def plain_text(self) -> str:
        """提取正文纯文本"""
        parts: list[str] = []

        def walk(node):
            if isinstance(node, dict):
                if node.get("node") == "text" and node.get("text"):
                    parts.append(node["text"])
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(self.body_tree)
        return " ".join(parts)


def fetch_article_detail(article_code: str) -> ArticleDetail:
    """请求公告详情接口"""
    data = get_json(ARTICLE_DETAIL_API, params={"articleCode": article_code})
    item = data.get("data") or {}
    body = item.get("body") or "{}"
    try:
        body_tree = json.loads(body)
    except json.JSONDecodeError as e:
        raise ApiError(f"公告正文解析失败: {article_code} -> {e}") from e
    return ArticleDetail(article_id=item.get("id"), title=item.get("title", ""), body_tree=body_tree)


def extract_links(body_tree: dict) -> list[tuple[str, str]]:
    """遍历富文本树，提取 (链接文本, href) 列表"""
    links: list[tuple[str, str]] = []

    def text_of(node) -> str:
        if isinstance(node, dict):
            if node.get("node") == "text":
                return node.get("text", "")
            return "".join(text_of(c) for c in node.get("child", []))
        if isinstance(node, list):
            return "".join(text_of(c) for c in node)
        return ""

    def walk(node):
        if isinstance(node, dict):
            if node.get("node") == "element" and node.get("tag") == "a":
                href = (node.get("attr") or {}).get("href", "")
                text = text_of(node.get("child", []))
                if href:
                    links.append((text.strip(), href))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(body_tree)
    return links


def normalize_url(raw: str) -> str:
    """替换正文链接中的占位符，得到真实 URL"""
    return raw.replace("%suffixOrigin%", SUFFIX_ORIGIN).replace("%locale%", "zh-CN")


def extract_join_link(body_tree: dict, fallback_hint: str | None = None) -> str | None:
    """寻找活动参与按钮链接：
    1. 优先按钮文本（立即参与/Join Now 等）
    2. 其次任意 /activity/ 链接
    3. 最后按钮关键字命中的任意链接
    """
    links = extract_links(body_tree)
    button_kws = [k.lower() for k in JOIN_BUTTON_KEYWORDS]

    # 1. 按钮关键字命中
    for text, href in links:
        if any(k in text.lower() for k in button_kws):
            return normalize_url(href)
    # 2. /activity/ 链接
    for text, href in links:
        if "/activity/" in href:
            return normalize_url(href)
    # 3. 提示词命中（部分公告按钮文本在 child 之外）
    if fallback_hint:
        for text, href in links:
            if fallback_hint.lower() in text.lower() or fallback_hint.lower() in href.lower():
                return normalize_url(href)
    return None


def resolve_activity_url(competition: Competition) -> str | None:
    """由公告解析出活动页面真实 URL"""
    detail = fetch_article_detail(competition.article_code)
    return extract_join_link(detail.body_tree, fallback_hint=competition.title)
