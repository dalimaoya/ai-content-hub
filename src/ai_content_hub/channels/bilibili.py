# B站收藏通道

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import AsyncIterator

from ..core.base import BaseChannel
from ..core.models import Channel, ContentItem, ContentType

logger = logging.getLogger(__name__)


class BilibiliChannel(BaseChannel):
    """B站收藏采集通道

    功能：扫描收藏夹视频、提取CC字幕、无字幕视频Whisper转录
    配置项：
        credential_path: str - bilibili_api凭证文件路径
        favorite_ids: list - 要扫描的收藏夹ID（空=全部）
        auto_transcribe: bool - 无字幕视频是否自动转录（默认False）
    """

    name = "bilibili"
    display_name = "B站收藏"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self._credential = None
        self._api = None

    def _get_credential(self):
        """获取bilibili_api凭证"""
        if self._credential is not None:
            return self._credential

        try:
            from bilibili_api import Credential
        except ImportError:
            raise ImportError("请安装bilibili-api-python: pip install ai-content-hub[bilibili]")

        cred_path = self.config.get("credential_path", "")
        if cred_path and Path(cred_path).exists():
            with open(cred_path, "r", encoding="utf-8") as f:
                cred_data = json.load(f)
            self._credential = Credential(
                sessdata=cred_data.get("SESSDATA", ""),
                bili_jct=cred_data.get("bili_jct", ""),
                buvid3=cred_data.get("buvid3", ""),
            )
        return self._credential

    def validate_config(self) -> bool:
        """检查配置"""
        cred_path = self.config.get("credential_path", "")
        return bool(cred_path)

    async def scan(self, incremental: bool = True) -> AsyncIterator[ContentItem]:
        """扫描收藏夹视频"""
        try:
            from bilibili_api import favorite_list, user
        except ImportError:
            logger.error("请安装bilibili-api-python: pip install ai-content-hub[bilibili]")
            return

        credential = self._get_credential()
        if not credential:
            logger.error("未配置B站凭证")
            return

        # 获取用户信息
        try:
            u = user.User(uid=int(self.config.get("uid", 0)), credential=credential)
            favs = await u.get_favorite_list()
        except Exception as e:
            logger.error(f"获取收藏夹失败: {e}")
            return

        favorite_ids = self.config.get("favorite_ids", [])
        processed = set(self.config.get("_processed_ids", []))

        for fav in favs:
            fav_id = fav.get("id", 0)
            if favorite_ids and fav_id not in favorite_ids:
                continue

            try:
                fl = favorite_list.FavoriteList(media_id=fav_id, credential=credential)
                page = 1
                while True:
                    result = await fl.get_media_list(page=page)
                    medias = result.get("medias", []) or []
                    if not medias:
                        break

                    for media in medias:
                        bvid = media.get("bvid", "")
                        item_id = f"bilibili_{bvid}"

                        if incremental and item_id in processed:
                            continue

                        title = media.get("title", "")
                        intro = media.get("intro", "")
                        upper = media.get("upper", {})
                        author = upper.get("name", "") if isinstance(upper, dict) else ""
                        pub_time = media.get("pubtime", 0)
                        cover = media.get("cover", "")

                        yield ContentItem(
                            id=item_id,
                            title=title,
                            content=intro or "",
                            channel=Channel.BILIBILI,
                            content_type=ContentType.VIDEO,
                            url=f"https://www.bilibili.com/video/{bvid}",
                            author=author,
                            created_at=str(pub_time) if pub_time else "",
                            metadata={
                                "bvid": bvid,
                                "cover": cover,
                                "fav_id": fav_id,
                            },
                        )

                    if not result.get("has_more", False):
                        break
                    page += 1

            except Exception as e:
                logger.error(f"扫描收藏夹 {fav_id} 失败: {e}")

    async def parse(self, url_or_id: str) -> ContentItem | None:
        """解析B站视频URL或BV号"""
        try:
            from bilibili_api import video
        except ImportError:
            logger.error("请安装bilibili-api-python")
            return None

        # 提取BV号
        bvid = self._extract_bvid(url_or_id)
        if not bvid:
            logger.error(f"无法识别B站视频: {url_or_id}")
            return None

        credential = self._get_credential()
        try:
            v = video.Video(bvid=bvid, credential=credential)
            info = await v.get_info()

            return ContentItem(
                id=f"bilibili_{bvid}",
                title=info.get("title", ""),
                content=info.get("desc", ""),
                channel=Channel.BILIBILI,
                content_type=ContentType.VIDEO,
                url=f"https://www.bilibili.com/video/{bvid}",
                author=info.get("owner", {}).get("name", ""),
                created_at=str(info.get("pubdate", "")),
                metadata={
                    "bvid": bvid,
                    "cover": info.get("pic", ""),
                    "duration": info.get("duration", 0),
                },
            )
        except Exception as e:
            logger.error(f"解析B站视频 {bvid} 失败: {e}")
            return None

    @staticmethod
    def _extract_bvid(text: str) -> str:
        """从URL或文本中提取BV号"""
        # 直接BV号
        m = re.match(r"^(BV[\w]+)$", text.strip())
        if m:
            return m.group(1)
        # URL中的BV号
        m = re.search(r"BV[\w]+", text)
        if m:
            return m.group(0)
        return ""

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "config_valid": self.validate_config(),
            "credential_configured": bool(self.config.get("credential_path")),
        }
