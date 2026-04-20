# AI Content Hub 通道和输出抽象基类

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from .models import ContentItem


class BaseChannel(ABC):
    """采集通道基类 — 所有通道必须继承此类

    实现指南：
    1. 定义 name 和 display_name 类属性
    2. 实现 scan() 方法 — 扫描新内容
    3. 实现 parse() 方法 — 解析单个URL/ID
    4. 可选覆盖 validate_config() 和 get_status()
    """

    # 子类必须覆盖
    name: str = ""               # 通道唯一标识，如 "bilibili"
    display_name: str = ""       # 显示名称，如 "B站收藏"

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    async def scan(self, incremental: bool = True) -> AsyncIterator[ContentItem]:
        """扫描并返回新内容

        Args:
            incremental: True=增量扫描（只获取上次之后的新内容），False=全量扫描

        Yields:
            ContentItem: 采集到的内容项
        """
        ...
        # 让它成为异步生成器
        if False:  # pragma: no cover
            yield  # type: ignore

    @abstractmethod
    async def parse(self, url_or_id: str) -> ContentItem | None:
        """解析单个URL或ID，返回ContentItem

        Args:
            url_or_id: 内容的URL或唯一标识

        Returns:
            ContentItem 或 None（解析失败时）
        """
        ...

    def validate_config(self) -> bool:
        """检查配置是否完整，子类可覆盖"""
        return True

    def get_status(self) -> dict:
        """返回通道状态信息，子类可覆盖"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "status": "unknown",
            "config_valid": self.validate_config(),
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"


class BaseOutput(ABC):
    """输出目标基类 — 所有输出插件必须继承此类

    实现指南：
    1. 定义 name 和 display_name 类属性
    2. 实现 write() 方法 — 写入内容
    3. 可选覆盖 setup() 和 notify()
    """

    name: str = ""               # 输出目标标识，如 "notion"
    display_name: str = ""       # 显示名称，如 "Notion"

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    async def write(self, items: list[ContentItem]) -> int:
        """写入内容，返回成功写入数量

        Args:
            items: 要写入的内容列表

        Returns:
            成功写入的数量
        """
        ...

    async def setup(self) -> dict:
        """首次运行初始化（如创建Notion Database），子类可覆盖

        Returns:
            初始化结果信息
        """
        return {"name": self.name, "status": "ready"}

    async def notify(self, event) -> bool:
        """发送通知，子类可覆盖

        Args:
            event: HubEvent 实例

        Returns:
            是否发送成功
        """
        return False

    def validate_config(self) -> bool:
        """检查配置是否完整，子类可覆盖"""
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
