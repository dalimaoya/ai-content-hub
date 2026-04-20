# AI Content Hub MCP Server

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


def run_mcp_server(config_path: str | None = None):
    """启动MCP Server"""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise ImportError("请安装MCP依赖: pip install ai-content-hub[mcp]")

    from ..core import HubConfig, ChannelRegistry, OutputRegistry, ContentItem, HubEvent
    from ..core.storage import StorageManager

    mcp = FastMCP("AI Content Hub")

    # 加载配置
    config = HubConfig(config_path)
    channel_registry = ChannelRegistry()
    output_registry = OutputRegistry()
    channel_registry.discover_from_entry_points()
    output_registry.discover_from_entry_points()
    storage = StorageManager(config.data_dir)

    @mcp.tool()
    async def scan_channel(channel: str = "", full: bool = False) -> str:
        """扫描采集通道获取新内容

        Args:
            channel: 通道名(bilibili/wechat/zsxq/getnote等)，空=全部
            full: 是否全量扫描
        """
        if channel:
            channels = [channel]
        else:
            channels = [n for n, c in config.channels_config.items() if c.get("enabled", False)]

        if not channels:
            return "没有启用的通道"

        results = []
        for ch_name in channels:
            ch_class = channel_registry.get(ch_name)
            if not ch_class:
                results.append(f"❌ 未知通道: {ch_name}")
                continue

            ch_instance = ch_class(config=config.channel_config(ch_name))
            if not ch_instance.validate_config():
                results.append(f"⚠️ {ch_instance.display_name} 配置不完整")
                continue

            count = 0
            async for item in ch_instance.scan(incremental=not full):
                if storage.is_processed(item.id):
                    continue
                storage.save_item(item)
                count += 1

            storage.update_last_sync(ch_name)
            storage.persist()
            results.append(f"✅ {ch_instance.display_name}: 新增 {count} 条")

        return "\n".join(results)

    @mcp.tool()
    async def parse_url(url: str) -> str:
        """解析URL获取内容（微信文章/B站视频等，自动识别通道）

        Args:
            url: 内容URL
        """
        import re
        url_patterns = {
            r"mp\.weixin\.qq\.com": "wechat",
            r"bilibili\.com/video/": "bilibili",
            r"BV[\w]+": "bilibili",
            r"zhihu\.com": "zhihu",
            r"xiaohongshu\.com": "xiaohongshu",
            r"douyin\.com": "douyin",
            r"youtube\.com/watch": "youtube",
        }

        detected = None
        for pattern, ch_name in url_patterns.items():
            if re.search(pattern, url):
                detected = ch_name
                break

        if not detected:
            return "❌ 无法识别URL对应的通道"

        ch_class = channel_registry.get(detected)
        if not ch_class:
            return f"❌ 通道 {detected} 未安装"

        ch_instance = ch_class(config=config.channel_config(detected))
        item = await ch_instance.parse(url)

        if item:
            storage.save_item(item)
            storage.persist()
            return f"✅ 解析成功\n标题: {item.title}\n通道: {item.channel.value}\n类型: {item.content_type.value}"
        return "❌ 解析失败"

    @mcp.tool()
    async def quick_note(
        content: str,
        category: str = "",
        tags: str = "",
    ) -> str:
        """快速记录一条随笔，自动分类入库

        Args:
            content: 记录内容
            category: 分类(idea/meeting/credential/forward/todo/bookmark/diary/quote)，空=自动推断
            tags: 标签(逗号分隔)

        分类说明:
        - idea: 💡灵感  - meeting: 📋纪要  - credential: 🔐密码(加密存储)
        - forward: 📎临时转发  - todo: ✅待办  - bookmark: 🔖书签
        - diary: 📔日记  - quote: 📖摘录
        """
        from ..channels.quicknote import QuickNoteChannel
        qn = QuickNoteChannel()
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        item = await qn.create(content, category=category, tags=tag_list)
        storage.save_item(item)
        storage.persist()
        return f"✅ 已记录 [{item.category}] {item.title[:60]}"

    @mcp.tool()
    async def get_status() -> str:
        """获取各通道状态概览"""
        stats = storage.get_stats()
        lines = ["📊 AI Content Hub 状态\n"]
        for ch, count in stats.get("by_channel", {}).items():
            last = stats.get("last_sync", {}).get(ch, "从未")
            lines.append(f"  {ch}: {count} 条 (最后同步: {last[:16]})")
        lines.append(f"\n总计: {stats.get('total_items', 0)} 条")
        return "\n".join(lines)

    @mcp.tool()
    async def get_daily_summary() -> str:
        """获取今日采集摘要"""
        stats = storage.get_stats()
        lines = ["📡 AI Content Hub 今日摘要\n"]
        for ch, count in stats.get("by_channel", {}).items():
            lines.append(f"  {ch}: {count} 条")
        lines.append(f"\n总计: {stats.get('total_items', 0)} 条")
        return "\n".join(lines)

    @mcp.tool()
    async def search_content(query: str, top_k: int = 10) -> str:
        """搜索已采集的内容（标题/标签匹配）

        Args:
            query: 搜索关键词
            top_k: 返回数量
        """
        results = storage.search_index(query, limit=top_k)
        if not results:
            return f"未找到与「{query}」相关的内容"

        lines = [f"搜索「{query}」找到 {len(results)} 条:\n"]
        for r in results:
            lines.append(f"  [{r.get('channel', '')}] {r.get('title', '')[:60]}")
        return "\n".join(lines)

    mcp.run()


if __name__ == "__main__":
    run_mcp_server()
