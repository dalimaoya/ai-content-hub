# AI Content Hub CLI

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Annotated, Optional

# Windows下强制UTF-8输出
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import typer
from rich.console import Console
from rich.table import Table

from .core import HubConfig, ChannelRegistry, OutputRegistry, ContentItem
from .core.storage import StorageManager

console = Console()
app = typer.Typer(
    name="ai-content-hub",
    help="📡 个人知识采集中枢 — 多平台内容统一采集、整理、同步",
    no_args_is_help=True,
)


def _load_config(config_path: str | None = None) -> HubConfig:
    """加载配置"""
    # 按优先级查找配置文件
    search_paths = [
        config_path,
        "./config.yaml",
        "./config/config.yaml",
        str(Path.home() / ".ai-content-hub" / "config.yaml"),
    ]
    for p in search_paths:
        if p and Path(p).exists():
            return HubConfig(p)
    return HubConfig()


def _discover_plugins(registry: ChannelRegistry | OutputRegistry) -> int:
    """从entry_points发现插件"""
    return registry.discover_from_entry_points()


# ─── init ────────────────────────────────────────────────────────

@app.command()
def init(
    config_path: Annotated[Optional[str], typer.Option(help="配置文件路径")] = None,
):
    """🚀 初始化配置（交互式引导）"""
    console.print("[bold cyan]🚀 AI Content Hub 初始化配置[/bold cyan]")
    console.print()

    config = HubConfig()
    data_dir = typer.prompt("📁 数据存储路径", default="./data")
    config.set("data_dir", data_dir)

    obsidian_vault = typer.prompt("🔗 Obsidian Vault路径（可选，回车跳过）", default="")
    if obsidian_vault:
        config.set("outputs.obsidian_vault_path", obsidian_vault)

    console.print("\n[bold]── 采集通道配置 ──[/bold]")

    for ch_name, ch_label in [
        ("bilibili", "📺 B站收藏"),
        ("wechat", "📰 微信文章"),
        ("zsxq", "🌐 知识星球"),
        ("getnote", "📝 Get笔记"),
        ("zhihu", "💡 知乎"),
        ("xiaohongshu", "📕 小红书"),
        ("douyin", "🎵 抖音"),
        ("youtube", "📺 YouTube"),
        ("rss", "📡 RSS"),
        ("quicknote", "✍️ 随笔记录"),
    ]:
        enabled = typer.confirm(f"  {ch_label}", default=False)
        config.set(f"channels.{ch_name}.enabled", enabled)

    console.print("\n[bold]── 输出配置 ──[/bold]")

    for out_name, out_label in [
        ("notion", "📝 Notion"),
        ("feishu", "💬 飞书"),
    ]:
        enabled = typer.confirm(f"  {out_label}", default=False)
        config.set(f"outputs.{out_name}.enabled", enabled)

    # 保存
    save_path = config_path or "./config.yaml"
    config.save(save_path)
    console.print(f"\n[green]✅ 配置已保存到 {save_path}[/green]")
    console.print("[cyan]运行 `ai-content-hub scan` 开始首次采集[/cyan]")


# ─── scan ────────────────────────────────────────────────────────

@app.command()
def scan(
    channel: Annotated[Optional[str], typer.Option("--channel", "-c", help="指定通道")] = None,
    full: Annotated[bool, typer.Option("--full", help="全量扫描")] = False,
    config_path: Annotated[Optional[str], typer.Option("--config", help="配置文件路径")] = None,
):
    """🔍 扫描采集通道"""
    config = _load_config(config_path)
    registry = ChannelRegistry()
    _discover_plugins(registry)

    # 确定要扫描的通道
    if channel:
        channels = [channel]
    else:
        channels = [name for name, cfg in config.channels_config.items() if cfg.get("enabled", False)]

    if not channels:
        console.print("[yellow]没有启用的通道，请运行 `ai-content-hub init`[/yellow]")
        return

    storage = StorageManager(config.data_dir)

    for ch_name in channels:
        ch_class = registry.get(ch_name)
        if not ch_class:
            console.print(f"[red]未知通道: {ch_name}[/red]")
            continue

        ch_config = config.channel_config(ch_name)
        ch_instance = ch_class(config=ch_config)

        if not ch_instance.validate_config():
            console.print(f"[yellow]⚠️ {ch_instance.display_name} 配置不完整，跳过[/yellow]")
            continue

        console.print(f"\n[bold]扫描 {ch_instance.display_name}...[/bold]")

        count = 0
        try:
            async def _do_scan():
                nonlocal count
                async for item in ch_instance.scan(incremental=not full):
                    # 检查去重
                    if storage.is_processed(item.id):
                        continue
                    filepath = storage.save_item(item)
                    count += 1
                    console.print(f"  [green]+[/green] {item.title[:60]}")

            asyncio.run(_do_scan())
            storage.update_last_sync(ch_name)
            storage.persist()
            console.print(f"  [cyan]新增 {count} 条[/cyan]")
        except Exception as e:
            console.print(f"  [red]扫描失败: {e}[/red]")


# ─── parse ───────────────────────────────────────────────────────

@app.command()
def parse(
    url: Annotated[str, typer.Argument(help="URL或ID")],
    config_path: Annotated[Optional[str], typer.Option("--config", help="配置文件路径")] = None,
):
    """🔗 解析URL（自动识别通道）"""
    config = _load_config(config_path)
    registry = ChannelRegistry()
    _discover_plugins(registry)
    storage = StorageManager(config.data_dir)

    # URL → 通道自动映射
    import re
    url_patterns = {
        r"mp\.weixin\.qq\.com": "wechat",
        r"bilibili\.com/video/": "bilibili",
        r"BV[\w]+": "bilibili",
        r"zhihu\.com": "zhihu",
        r"xiaohongshu\.com": "xiaohongshu",
        r"douyin\.com": "douyin",
        r"youtube\.com/watch": "youtube",
        r"youtu\.be/": "youtube",
    }

    detected_channel = None
    for pattern, ch_name in url_patterns.items():
        if re.search(pattern, url):
            detected_channel = ch_name
            break

    if not detected_channel:
        console.print("[red]无法识别URL对应的通道[/red]")
        return

    ch_class = registry.get(detected_channel)
    if not ch_class:
        console.print(f"[red]通道 {detected_channel} 未安装[/red]")
        return

    ch_config = config.channel_config(detected_channel)
    ch_instance = ch_class(config=ch_config)

    console.print(f"[cyan]识别为 {ch_instance.display_name}，正在解析...[/cyan]")

    async def _do_parse():
        return await ch_instance.parse(url)

    item = asyncio.run(_do_parse())

    if item:
        filepath = storage.save_item(item)
        storage.persist()
        console.print(f"[green]✅ 解析成功[/green]")
        console.print(f"  标题: {item.title}")
        console.print(f"  保存: {filepath}")
    else:
        console.print("[red]❌ 解析失败[/red]")


# ─── sync ────────────────────────────────────────────────────────

@app.command()
def sync(
    obsidian: Annotated[bool, typer.Option("--obsidian", help="同步到Obsidian")] = False,
    notion: Annotated[bool, typer.Option("--notion", help="同步到Notion")] = False,
    feishu: Annotated[bool, typer.Option("--feishu", help="同步到飞书")] = False,
    all_outputs: Annotated[bool, typer.Option("--all", help="同步全部输出")] = False,
    config_path: Annotated[Optional[str], typer.Option("--config", help="配置文件路径")] = None,
):
    """📤 同步内容到输出目标"""
    config = _load_config(config_path)
    out_registry = OutputRegistry()
    _discover_plugins(out_registry)

    # 本地MD总是内置的
    targets = ["local_md"]

    if all_outputs or obsidian or config.is_output_enabled("obsidian"):
        pass  # local_md handles obsidian via config
    if all_outputs or notion or config.is_output_enabled("notion"):
        targets.append("notion")
    if all_outputs or feishu or config.is_output_enabled("feishu"):
        targets.append("feishu")

    console.print(f"[cyan]同步到: {', '.join(targets)}[/cyan]")

    # 读取本地索引，发送到各输出
    storage = StorageManager(config.data_dir)
    items = []

    for out_name in targets:
        out_class = out_registry.get(out_name)
        if not out_class:
            # 内置输出
            if out_name == "local_md":
                from .outputs.local_md import LocalMDOutput
                out_class = LocalMDOutput
            else:
                console.print(f"[yellow]输出 {out_name} 未安装[/yellow]")
                continue

        out_config = config.output_config(out_name)
        if out_name == "local_md":
            out_config["data_dir"] = str(config.data_dir)
            out_config["obsidian_vault_path"] = config.get("outputs.obsidian_vault_path", "")

        out_instance = out_class(config=out_config)

        async def _do_write():
            return await out_instance.write(items)

        count = asyncio.run(_do_write())
        console.print(f"  {out_instance.display_name}: {count} 条")


# ─── status ──────────────────────────────────────────────────────

@app.command()
def status(
    config_path: Annotated[Optional[str], typer.Option("--config", help="配置文件路径")] = None,
):
    """📊 查看各通道状态"""
    config = _load_config(config_path)
    registry = ChannelRegistry()
    _discover_plugins(registry)
    storage = StorageManager(config.data_dir)

    table = Table(title="📡 AI Content Hub 状态")
    table.add_column("通道", style="cyan")
    table.add_column("启用", style="green")
    table.add_column("配置", style="yellow")
    table.add_column("已采集", style="magenta")
    table.add_column("最后同步", style="blue")

    stats = storage.get_stats()
    for ch_name, ch_class in registry.list_all().items():
        enabled = config.is_channel_enabled(ch_name)
        ch_instance = ch_class(config=config.channel_config(ch_name))
        config_valid = ch_instance.validate_config()
        collected = stats.get("by_channel", {}).get(ch_name, 0)
        last_sync = stats.get("last_sync", {}).get(ch_name, "从未")

        table.add_row(
            ch_instance.display_name,
            "✅" if enabled else "❌",
            "✅" if config_valid else "⚠️",
            str(collected),
            last_sync[:16] if last_sync != "从未" else last_sync,
        )

    console.print(table)


# ─── note (随笔记录) ────────────────────────────────────────────

@app.command()
def note(
    content: Annotated[str, typer.Argument(help="记录内容")],
    category: Annotated[str, typer.Option("--category", "-C", help="分类(idea/meeting/credential/forward/todo/bookmark/diary/quote)")] = "",
    tags: Annotated[str, typer.Option("--tags", "-t", help="标签(逗号分隔)")] = "",
    config_path: Annotated[Optional[str], typer.Option("--config", help="配置文件路径")] = None,
):
    """✍️ 快速记录随笔"""
    config = _load_config(config_path)
    storage = StorageManager(config.data_dir)

    from .channels.quicknote import QuickNoteChannel
    qn = QuickNoteChannel()

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    async def _do_create():
        return await qn.create(content, category=category, tags=tag_list)

    item = asyncio.run(_do_create())
    filepath = storage.save_item(item)
    storage.persist()

    console.print(f"[green]✅ 已记录[/green] [{item.category}] {item.title[:60]}")
    console.print(f"  保存: {filepath}")


# ─── mcp ─────────────────────────────────────────────────────────

@app.command()
def mcp(
    config_path: Annotated[Optional[str], typer.Option("--config", help="配置文件路径")] = None,
):
    """🤖 启动MCP Server"""
    console.print("[cyan]启动 AI Content Hub MCP Server...[/cyan]")

    try:
        from .mcp.server import run_mcp_server
        run_mcp_server(config_path)
    except ImportError:
        console.print("[red]请安装MCP依赖: pip install ai-content-hub[mcp][/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
