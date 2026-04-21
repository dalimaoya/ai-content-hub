# 知识星球通道

from __future__ import annotations

import hashlib
import logging
import re
from typing import AsyncIterator

import httpx

from ..core.base import BaseChannel
from ..core.models import Channel, ContentItem, ContentType

logger = logging.getLogger(__name__)


def _calc_value_score(topic: dict) -> int:
    """计算主题价值评分 (0-5)"""
    score = 0
    if topic.get("digested"):
        score += 2
    likes = topic.get("likes_count", 0) or 0
    if likes >= 6:
        score += 3
    elif likes >= 3:
        score += 2
    elif likes >= 1:
        score += 1
    comments = topic.get("comments_count", 0) or 0
    if comments >= 4:
        score += 2
    elif comments >= 1:
        score += 1
    rewards = topic.get("rewards_count", 0) or 0
    if rewards >= 1:
        score += 1
    readers = topic.get("readers_count", 0) or 0
    if readers >= 200:
        score += 2
    elif readers >= 50:
        score += 1
    return min(score, 5)


def _score_to_stars(score: int) -> str:
    return "⭐" * score + "☆" * (5 - score)


def _extract_feishu_urls(text: str) -> list[str]:
    """从文本中提取飞书/Lark文档链接"""
    if not text:
        return []
    urls = re.findall(r'https?://[^\s<>"\']+', text)
    return [u for u in urls if any(d in u.lower() for d in ['feishu.cn', 'feishu.com', 'larkoffice.com', 'larksuite.com'])]


class ZsxqChannel(BaseChannel):
    """知识星球监测通道

    功能：扫描星球新主题、评论，提取互动数据、价值评分、article链接、飞书文档链接
    配置项：
        access_token: str - 知识星球Access Token
        group_ids: list - 要扫描的星球ID（空=全部）
    """

    name = "zsxq"
    display_name = "知识星球"

    API_BASE = "https://api.zsxq.com/v2"

    def validate_config(self) -> bool:
        return bool(self.config.get("access_token"))

    async def scan(self, incremental: bool = True) -> AsyncIterator[ContentItem]:
        """扫描知识星球新主题（含互动数据+价值评分+article+飞书链接）"""
        token = self.config.get("access_token", "")
        if not token:
            logger.error("未配置知识星球Access Token")
            return

        headers = {"Cookie": f"zsxq_access_token={token}"}
        processed = set(self.config.get("_processed_ids", []))
        target_groups = self.config.get("group_ids", [])

        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            # 获取星球列表
            groups = await self._get_groups(client, headers)
            if not groups:
                return

            for group in groups:
                group_id = str(group.get("group_id", ""))
                group_name = group.get("name", "")

                if target_groups and group_id not in target_groups:
                    continue

                # 扫描主题
                page = 1
                while True:
                    try:
                        resp = await client.get(
                            f"{self.API_BASE}/groups/{group_id}/topics",
                            params={"scope": "all", "count": 20, "page": page},
                            headers=headers,
                        )
                        if resp.status_code != 200:
                            break

                        data = resp.json()
                        topics = data.get("resp_data", {}).get("topics", [])
                        if not topics:
                            break

                        for topic in topics:
                            topic_id = str(topic.get("topic_id", ""))
                            item_id = f"zsxq_{topic_id}"

                            if incremental and item_id in processed:
                                continue

                            # 提取内容
                            talk = topic.get("talk", {})
                            text = talk.get("text", "")
                            article = talk.get("article", {})
                            
                            # 标题：优先API title → article标题 → 正文前60字
                            title = topic.get("title", "")
                            if not title and article:
                                title = article.get("title", "")
                            if not title and text:
                                title = text[:60].replace("\n", " ")
                            if not title:
                                title = "无标题"

                            # 提取作者
                            owner = talk.get("owner", {})
                            author = owner.get("name", "") if isinstance(owner, dict) else ""

                            # 提取时间（转为人类可读格式）
                            raw_time = topic.get("create_time", "")
                            created = ContentItem._format_iso(raw_time) if raw_time else ""

                            # 互动数据
                            likes_count = topic.get("likes_count", 0) or 0
                            comments_count = topic.get("comments_count", 0) or 0
                            reading_count = topic.get("reading_count", 0) or 0
                            readers_count = topic.get("readers_count", 0) or 0
                            rewards_count = topic.get("rewards_count", 0) or 0
                            digested = topic.get("digested", False)
                            score = _calc_value_score(topic)

                            # 飞书链接
                            feishu_urls = _extract_feishu_urls(text)
                            has_feishu = bool(feishu_urls)

                            # 标签
                            tags = talk.get("tags", [])
                            tag_names = [t if isinstance(t, str) else t.get("name", "") for t in tags if t]

                            yield ContentItem(
                                id=item_id,
                                title=title,
                                content=text,
                                channel=Channel.ZSXQ,
                                content_type=ContentType.TOPIC,
                                url=f"https://wx.zsxq.com/topic/{topic_id}",
                                author=author,
                                created_at=created,
                                tags=tag_names,
                                metadata={
                                    "group_id": group_id,
                                    "group_name": group_name,
                                    "topic_id": topic_id,
                                    # 互动数据
                                    "likes_count": likes_count,
                                    "comments_count": comments_count,
                                    "reading_count": reading_count,
                                    "readers_count": readers_count,
                                    "rewards_count": rewards_count,
                                    "digested": digested,
                                    # 价值评分
                                    "value_score": score,
                                    "value_stars": _score_to_stars(score),
                                    # article信息
                                    "article_url": article.get("article_url", "") if article else "",
                                    "article_title": article.get("title", "") if article else "",
                                    # 飞书链接
                                    "has_feishu_doc": has_feishu,
                                    "feishu_urls": feishu_urls,
                                },
                            )

                        # 知识星球没有明确的has_more，用返回数量判断
                        if len(topics) < 20:
                            break
                        page += 1

                    except Exception as e:
                        logger.error(f"扫描星球 {group_name} 失败: {e}")
                        break

    async def parse(self, url_or_id: str) -> ContentItem | None:
        """解析知识星球article链接内容"""
        token = self.config.get("access_token", "")
        if not token:
            return None

        headers = {
            "Cookie": f"zsxq_access_token={token}",
            "User-Agent": "Mozilla/5.0",
        }

        # 如果是articles.zsxq.com链接，抓取内容
        if "articles.zsxq.com" in url_or_id:
            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                    resp = await client.get(url_or_id, headers=headers)
                    if resp.status_code != 200:
                        return None

                    html = resp.text
                    # 去标签提取正文
                    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
                    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                    text = re.sub(r'<br\s*/?\s*>', '\n', text)
                    text = re.sub(r'</p>', '\n', text)
                    text = re.sub(r'</h[1-6]>', '\n', text)
                    text = re.sub(r'<[^>]+>', '', text)
                    text = re.sub(r'&nbsp;', ' ', text)
                    text = re.sub(r'&amp;', '&', text)
                    text = re.sub(r'\n{3,}', '\n\n', text).strip()

                    # 提取标题
                    title_match = re.search(r'<title>(.*?)</title>', html)
                    title = title_match.group(1) if title_match else "知识星球文章"

                    return ContentItem(
                        id=f"zsxq_article_{hashlib.md5(url_or_id.encode()).hexdigest()[:8]}",
                        title=title,
                        content=text,
                        channel=Channel.ZSXQ,
                        content_type=ContentType.ARTICLE,
                        url=url_or_id,
                        metadata={"article_url": url_or_id},
                    )
            except Exception as e:
                logger.error(f"解析知识星球文章失败: {e}")
                return None

        logger.warning("知识星球暂不支持非article链接解析")
        return None

    async def _get_groups(self, client: httpx.AsyncClient, headers: dict) -> list:
        """获取星球列表"""
        try:
            resp = await client.get(
                f"{self.API_BASE}/groups",
                headers=headers,
            )
            if resp.status_code == 200:
                return resp.json().get("resp_data", {}).get("groups", [])
        except Exception as e:
            logger.error(f"获取星球列表失败: {e}")
        return []

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "config_valid": self.validate_config(),
            "token_configured": bool(self.config.get("access_token")),
        }
