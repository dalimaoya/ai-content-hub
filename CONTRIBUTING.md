# 贡献指南

感谢你对 AI Content Hub 的关注！欢迎提交 Issue 和 Pull Request。

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/dalimaoya/ai-content-hub.git
cd ai-content-hub

# 安装开发模式（包含所有通道）
pip install -e ".[all,dev]"

# 运行测试
pytest

# 代码检查
ruff check src/
```

## 添加新通道

### 1. 创建通道文件

在 `src/ai_content_hub/channels/` 下创建新文件，如 `my_channel.py`：

```python
"""我的通道 — 简要描述

依赖: pip install ai-content-hub[my-channel]
认证方式: 说明如何获取凭据
"""

from __future__ import annotations
from typing import AsyncIterator

from ..core.base import BaseChannel
from ..core.models import ContentItem, ContentType, Channel


class MyChannel(BaseChannel):
    name = "my-channel"           # 唯一标识（小写+连字符）
    display_name = "我的通道"       # 用户可见名称
    description = "采集XXX内容"     # 一句话描述
    supported_content_types = [ContentType.ARTICLE]

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "")

    def validate_config(self) -> list[str]:
        """验证配置是否完整，返回错误信息列表"""
        errors = []
        if not self.api_key:
            errors.append("API Key未配置（channels.my-channel.api_key）")
        return errors

    async def scan(self, full: bool = False) -> AsyncIterator[ContentItem]:
        """定时扫描采集"""
        # 实现你的采集逻辑
        async for raw_item in self._fetch_items():
            yield ContentItem(
                id=f"my_channel_{raw_item['id']}",
                title=raw_item["title"],
                content=raw_item["content"],
                channel=Channel.MY_CHANNEL,  # 需要在models.py中添加
                content_type=ContentType.ARTICLE,
                url=raw_item.get("url", ""),
                author=raw_item.get("author", ""),
                tags=["我的通道"],
                metadata={},
            )

    async def parse(self, url: str) -> ContentItem | None:
        """解析单个URL"""
        if "my-site.com" not in url:
            return None
        # 实现你的解析逻辑
        return item
```

### 2. 注册通道

**models.py** — 添加 Channel 枚举值：

```python
class Channel(str, Enum):
    # ... 已有值 ...
    MY_CHANNEL = "my_channel"
```

**channels/\_\_init\_\_.py** — 添加导入：

```python
from .my_channel import MyChannel
```

**pyproject.toml** — 添加 entry_point：

```toml
[project.entry-points."ai_content_hub.channels"]
my-channel = "ai_content_hub.channels.my_channel:MyChannel"
```

可选依赖：

```toml
[project.optional-dependencies]
my-channel = ["some-library>=1.0"]
```

### 3. 测试

```bash
# 测试通道导入
python -c "from ai_content_hub.channels import MyChannel; print('OK')"

# 测试CLI识别
ai-content-hub status

# 测试扫描
ai-content-hub scan --channel my-channel
```

## 代码规范

- Python 3.10+，使用 `from __future__ import annotations`
- 类型注解必须加
- `async/await` 异步编程
- Windows GBK 兼容：所有脚本开头加 UTF-8 reconfigure
- Ruff 检查：`ruff check src/`
- 行宽 100

## 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档
refactor: 重构
chore: 构建/CI
```

## 项目结构

```
src/ai_content_hub/
├── core/           # 核心层（不要改，除非你确定）
├── channels/       # 采集通道（每个文件一个通道）
├── outputs/        # 输出目标
├── mcp/            # MCP Server
└── cli.py          # CLI入口
```

## 有问题？

先看 [Issues](https://github.com/dalimaoya/ai-content-hub/issues)，没有就新建一个。
