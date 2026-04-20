# 本地Markdown输出（内置，必选）

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from ..core.base import BaseOutput
from ..core.models import ContentItem

logger = logging.getLogger(__name__)


class LocalMDOutput(BaseOutput):
    """本地Markdown文件输出 — 核心内置输出

    功能：
    - 将ContentItem保存为Markdown文件
    - 支持Obsidian同步（复制到Vault目录）
    - 按通道+类型+日期分目录
    """

    name = "local_md"
    display_name = "本地Markdown"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self._data_dir = Path(self.config.get("data_dir", "./data"))
        self._obsidian_vault = self.config.get("obsidian_vault_path", "")

    async def write(self, items: list[ContentItem]) -> int:
        """写入内容到本地Markdown文件"""
        count = 0
        for item in items:
            try:
                filepath = self._save_item(item)
                count += 1

                # Obsidian同步
                if self._obsidian_vault:
                    self._sync_to_obsidian(item, filepath)

            except Exception as e:
                logger.error(f"写入 {item.id} 失败: {e}")

        return count

    async def setup(self) -> dict:
        """创建数据目录"""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        return {"name": self.name, "data_dir": str(self._data_dir), "status": "ready"}

    def _save_item(self, item: ContentItem) -> Path:
        """保存单个ContentItem"""
        from ..core.storage import StorageManager
        sm = StorageManager(self._data_dir)
        filepath = sm.save_item(item)
        sm.persist()
        return filepath

    def _sync_to_obsidian(self, item: ContentItem, src: Path) -> None:
        """同步到Obsidian Vault"""
        # 敏感内容不同步
        if item.is_sensitive:
            return

        vault = Path(self._obsidian_vault)
        if not vault.exists():
            return

        # 按通道名分目录
        channel_names = {
            "bilibili": "B站收藏",
            "wechat": "微信文章",
            "zsxq": "知识星球",
            "getnote": "Get笔记",
            "zhihu": "知乎",
            "xiaohongshu": "小红书",
            "quick_note": "随笔记录",
            "wechat_chat": "微信聊天",
        }
        channel_dir = channel_names.get(item.channel.value, item.channel.value)
        dest_dir = vault / channel_dir / src.parent.name  # 保留年月子目录
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        if not dest.exists():
            shutil.copy2(src, dest)

    def validate_config(self) -> bool:
        """本地MD总是可用"""
        return True

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "data_dir": str(self._data_dir),
            "obsidian_vault": self._obsidian_vault or "未配置",
            "config_valid": True,
        }
