# AI Content Hub 插件注册表

from __future__ import annotations

import logging
from importlib.metadata import entry_points
from typing import Type

from .base import BaseChannel, BaseOutput

logger = logging.getLogger(__name__)


class ChannelRegistry:
    """通道注册表 — 管理所有已安装的采集通道插件"""

    def __init__(self):
        self._channels: dict[str, Type[BaseChannel]] = {}

    def register(self, channel_class: Type[BaseChannel]) -> None:
        """注册一个通道"""
        name = channel_class.name
        if not name:
            raise ValueError(f"通道 {channel_class} 没有设置 name 属性")
        if name in self._channels:
            logger.warning(f"通道 {name} 已注册，覆盖旧值")
        self._channels[name] = channel_class
        logger.debug(f"注册通道: {name} ({channel_class.display_name})")

    def get(self, name: str) -> Type[BaseChannel] | None:
        """获取通道类"""
        return self._channels.get(name)

    def list_all(self) -> dict[str, Type[BaseChannel]]:
        """列出所有已注册通道"""
        return dict(self._channels)

    def discover_from_entry_points(self) -> int:
        """从 entry_points 自动发现并注册通道插件

        Returns:
            新注册的通道数量
        """
        count = 0
        try:
            eps = entry_points(group="ai_content_hub.channels")
            for ep in eps:
                try:
                    channel_class = ep.load()
                    if isinstance(channel_class, type) and issubclass(channel_class, BaseChannel):
                        self.register(channel_class)
                        count += 1
                    else:
                        logger.warning(f"entry_point {ep.name} 不是 BaseChannel 子类")
                except Exception as e:
                    logger.error(f"加载通道插件 {ep.name} 失败: {e}")
        except Exception as e:
            logger.error(f"扫描 entry_points 失败: {e}")
        return count

    def __contains__(self, name: str) -> bool:
        return name in self._channels

    def __len__(self) -> int:
        return len(self._channels)

    def __repr__(self) -> str:
        names = ", ".join(self._channels.keys())
        return f"ChannelRegistry([{names}])"


class OutputRegistry:
    """输出注册表 — 管理所有已安装的输出插件"""

    def __init__(self):
        self._outputs: dict[str, Type[BaseOutput]] = {}

    def register(self, output_class: Type[BaseOutput]) -> None:
        """注册一个输出"""
        name = output_class.name
        if not name:
            raise ValueError(f"输出 {output_class} 没有设置 name 属性")
        if name in self._outputs:
            logger.warning(f"输出 {name} 已注册，覆盖旧值")
        self._outputs[name] = output_class
        logger.debug(f"注册输出: {name} ({output_class.display_name})")

    def get(self, name: str) -> Type[BaseOutput] | None:
        """获取输出类"""
        return self._outputs.get(name)

    def list_all(self) -> dict[str, Type[BaseOutput]]:
        """列出所有已注册输出"""
        return dict(self._outputs)

    def discover_from_entry_points(self) -> int:
        """从 entry_points 自动发现并注册输出插件"""
        count = 0
        try:
            eps = entry_points(group="ai_content_hub.outputs")
            for ep in eps:
                try:
                    output_class = ep.load()
                    if isinstance(output_class, type) and issubclass(output_class, BaseOutput):
                        self.register(output_class)
                        count += 1
                except Exception as e:
                    logger.error(f"加载输出插件 {ep.name} 失败: {e}")
        except Exception as e:
            logger.error(f"扫描 entry_points 失败: {e}")
        return count

    def __contains__(self, name: str) -> bool:
        return name in self._outputs

    def __len__(self) -> int:
        return len(self._outputs)

    def __repr__(self) -> str:
        names = ", ".join(self._outputs.keys())
        return f"OutputRegistry([{names}])"
