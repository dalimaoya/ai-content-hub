"""微信聊天记录通道 — 读取本地微信数据库

依赖: pip install ai-content-hub[wechat-chat]
技术方案: 基于 PyWxDump (https://github.com/xaoyaoo/PyWxDump)

认证方式:
  - 无需API认证，读取本地数据库文件
  - 首次使用需先解密数据库（参考PyWxDump）
  - 配置项:
    - channels.wechat-chat.wx_dir: 微信数据目录
    - channels.wechat-chat.merge_dir: 解密后的数据库目录
    - channels.wechat-chat.contacts: 要采集的联系人wxid列表

注意: 此通道仅适用于Windows，且需要微信登录状态
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from ..core.base import BaseChannel
from ..core.models import ContentItem, ContentType, Channel


class WechatChatChannel(BaseChannel):
    """微信聊天记录采集"""

    name = "wechat-chat"
    display_name = "微信聊天记录"
    description = "读取本地微信聊天记录并入库"
    supported_content_types = [ContentType.CHAT]

    def __init__(self, config: dict):
        super().__init__(config)
        self.wx_dir = config.get("wx_dir", "")
        self.merge_dir = config.get("merge_dir", "")
        self.contacts = config.get("contacts", [])
        self.msg_types = config.get("msg_types", [1, 49])

    def validate_config(self) -> list[str]:
        errors = []
        if not self.merge_dir and not self.wx_dir:
            errors.append("微信数据目录未配置（channels.wechat-chat.wx_dir 或 merge_dir）")
        return errors

    async def scan(self, full: bool = False) -> AsyncIterator[ContentItem]:
        merge_path = self._get_merge_path()
        if not merge_path or not merge_path.exists():
            self.logger.warning("微信解密数据库不存在，请先运行PyWxDump解密")
            return

        msg_db = merge_path / "MSG.db"
        micro_msg_db = merge_path / "MicroMsg.db"

        if not msg_db.exists():
            self.logger.error(f"MSG.db 不存在: {msg_db}")
            return

        contact_map = self._get_contact_map(micro_msg_db)

        conn = sqlite3.connect(str(msg_db))
        try:
            cursor = conn.cursor()

            conditions = []
            params = []

            if self.msg_types:
                placeholders = ",".join("?" * len(self.msg_types))
                conditions.append(f"Type IN ({placeholders})")
                params.extend(self.msg_types)

            if self.contacts:
                placeholders = ",".join("?" * len(self.contacts))
                conditions.append(f"StrTalker IN ({placeholders})")
                params.extend(self.contacts)

            where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"SELECT MsgSvrID, StrTalker, Type, CreateTime, StrContent FROM MSG{where_clause} ORDER BY CreateTime DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            self.logger.info(f"获取到 {len(rows)} 条微信聊天记录")

            for row in rows:
                item = self._parse_msg(row, contact_map)
                if item:
                    yield item
        finally:
            conn.close()

    async def parse(self, url: str) -> ContentItem | None:
        """微信聊天记录不支持URL解析"""
        return None

    def _get_merge_path(self) -> Path | None:
        if self.merge_dir:
            return Path(self.merge_dir)
        if self.wx_dir:
            return Path(self.wx_dir) / "merge"
        return None

    def _get_contact_map(self, micro_msg_db: Path) -> dict[str, str]:
        contact_map = {}
        if not micro_msg_db.exists():
            return contact_map
        try:
            conn = sqlite3.connect(str(micro_msg_db))
            cursor = conn.cursor()
            cursor.execute("SELECT UserName, NickName, Alias FROM Contact")
            for row in cursor.fetchall():
                wxid = row[0]
                nickname = row[1] or row[2] or wxid
                contact_map[wxid] = nickname
            conn.close()
        except Exception as e:
            self.logger.warning(f"读取联系人失败: {e}")
        return contact_map

    def _parse_msg(self, row: tuple, contact_map: dict[str, str]) -> ContentItem | None:
        try:
            msg_id, talker, msg_type, create_time, content = row

            if msg_type == 1:
                text = content or ""
                if len(text.strip()) < 5:
                    return None
            elif msg_type == 49:
                text = self._parse_rich_msg(content)
                if not text:
                    return None
            else:
                return None

            contact_name = contact_map.get(talker, talker)
            created_at = datetime.fromtimestamp(create_time).isoformat() if create_time else ""

            return ContentItem(
                id=f"wechat_chat_{msg_id}",
                title=f"与{contact_name}的对话 - {created_at[:10]}",
                content=text[:5000],
                channel=Channel.WECHAT_CHAT,
                content_type=ContentType.CHAT,
                author=contact_name,
                created_at=created_at,
                tags=["微信", "聊天记录"],
                metadata={"talker_wxid": talker, "msg_type": msg_type},
            )
        except Exception as e:
            self.logger.warning(f"解析微信消息失败: {e}")
            return None

    def _parse_rich_msg(self, content: str) -> str:
        try:
            if not content:
                return ""
            if content.startswith("<"):
                return self._parse_xml_content(content)
            return content
        except Exception:
            return str(content)[:500]

    @staticmethod
    def _parse_xml_content(xml_str: str) -> str:
        title_match = re.search(r"<title>(.*?)</title>", xml_str)
        title = title_match.group(1) if title_match else ""

        desc_match = re.search(r"<des>(.*?)</des>", xml_str)
        desc = desc_match.group(1) if desc_match else ""

        parts = []
        if title:
            parts.append(f"**{title}**")
        if desc:
            parts.append(desc)
        return "\n".join(parts) if parts else xml_str[:500]



