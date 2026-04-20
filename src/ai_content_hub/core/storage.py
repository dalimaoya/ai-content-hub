# AI Content Hub 存储管理

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import ContentItem

logger = logging.getLogger(__name__)


class StorageManager:
    """统一存储管理 — 本地Markdown + 索引 + 状态"""

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.data_dir / "index.json"
        self._state_path = self.data_dir / "state.json"
        self._index: dict[str, dict] = self._load_json(self._index_path, {})
        self._state: dict[str, Any] = self._load_json(self._state_path, {
            "processed_ids": [],
            "last_sync": {},
        })

    @staticmethod
    def _load_json(path: Path, default: Any = None) -> Any:
        """加载JSON文件"""
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return default
        return default

    @staticmethod
    def _save_json(path: Path, data: Any) -> None:
        """保存JSON文件"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def content_hash(content: str) -> str:
        """计算内容哈希，用于去重"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()[:12]

    def is_processed(self, item_id: str) -> bool:
        """检查内容是否已处理"""
        return item_id in self._state.get("processed_ids", [])

    def mark_processed(self, item_id: str) -> None:
        """标记内容为已处理"""
        processed = self._state.setdefault("processed_ids", [])
        if item_id not in processed:
            processed.append(item_id)

    def update_last_sync(self, channel_name: str) -> None:
        """更新通道最后同步时间"""
        self._state.setdefault("last_sync", {})[channel_name] = datetime.now().isoformat()

    def get_last_sync(self, channel_name: str) -> str:
        """获取通道最后同步时间"""
        return self._state.get("last_sync", {}).get(channel_name, "")

    def save_item(self, item: ContentItem) -> Path:
        """保存ContentItem为Markdown文件

        Returns:
            保存的文件路径
        """
        # 构建目录: data/{channel}/{子目录}/{年月}/
        subdir = self._get_subdir(item)
        year_month = item.created_at[:7] if item.created_at else datetime.now().strftime("%Y-%m")
        save_dir = self.data_dir / item.channel.value / subdir / year_month
        save_dir.mkdir(parents=True, exist_ok=True)

        # 文件名: 日期_标题_ID
        date_str = item.created_at[:10] if item.created_at else datetime.now().strftime("%Y-%m-%d")
        safe_title = self._safe_filename(item.title[:50] if item.title else "untitled")
        filename = f"{date_str}_{safe_title}_{self.content_hash(item.id)}"
        filepath = save_dir / f"{filename}.md"

        # 写入Markdown
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(item.to_markdown())

        # 更新索引
        self._index[item.id] = {
            "filepath": str(filepath),
            "channel": item.channel.value,
            "content_type": item.content_type.value,
            "title": item.title,
            "created_at": item.created_at,
            "collected_at": item.collected_at,
            "tags": item.tags,
            "url": item.url,
        }

        # 标记已处理
        self.mark_processed(item.id)

        return filepath

    def search_index(self, query: str, channel: str | None = None, limit: int = 20) -> list[dict]:
        """搜索索引（简单的标题/标签匹配）"""
        results = []
        query_lower = query.lower()
        for item_id, info in self._index.items():
            if channel and info.get("channel") != channel:
                continue
            title = info.get("title", "").lower()
            tags = [t.lower() for t in info.get("tags", [])]
            if query_lower in title or any(query_lower in t for t in tags):
                results.append({"id": item_id, **info})
                if len(results) >= limit:
                    break
        return results

    def get_stats(self) -> dict[str, Any]:
        """获取存储统计"""
        channel_counts = {}
        for info in self._index.values():
            ch = info.get("channel", "unknown")
            channel_counts[ch] = channel_counts.get(ch, 0) + 1

        return {
            "total_items": len(self._index),
            "by_channel": channel_counts,
            "last_sync": self._state.get("last_sync", {}),
        }

    def persist(self) -> None:
        """持久化索引和状态到磁盘"""
        self._save_json(self._index_path, self._index)
        self._save_json(self._state_path, self._state)

    @staticmethod
    def _get_subdir(item: ContentItem) -> str:
        """根据内容类型确定存储子目录"""
        type_to_subdir = {
            "video": "视频",
            "article": "文章",
            "note": "笔记",
            "topic": "主题",
            "audio": "录音",
            "image": "图片",
            "chat": "聊天记录",
            "answer": "回答",
            "pin": "想法",
            "post": "笔记",
        }
        # 随笔记录按分类分目录
        if item.channel.value == "quick_note" and item.category:
            category_names = {
                "idea": "灵感", "meeting": "纪要", "credential": "密码",
                "forward": "临时转发", "todo": "待办", "bookmark": "书签",
                "diary": "日记", "quote": "摘录",
            }
            return category_names.get(item.category, item.category)

        return type_to_subdir.get(item.content_type.value, "其他")

    @staticmethod
    def _safe_filename(name: str) -> str:
        """生成安全的文件名"""
        import re
        name = re.sub(r'[\\/:*?"<>|]', '_', name)
        name = name.strip('. ')
        return name[:80] if len(name) > 80 else name
