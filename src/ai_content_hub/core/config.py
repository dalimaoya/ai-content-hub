# AI Content Hub 统一配置管理

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml


# 环境变量引用模式: ${VAR_NAME} 或 ${VAR_NAME:default_value}
_ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")


def _resolve_env_vars(value: Any) -> Any:
    """递归解析配置中的环境变量引用"""
    if isinstance(value, str):
        def _replace(match):
            var_name = match.group(1)
            default = match.group(2)
            env_val = os.environ.get(var_name)
            if env_val is not None:
                return env_val
            if default is not None:
                return default
            return match.group(0)  # 保持原样
        return _ENV_PATTERN.sub(_replace, value)
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars(v) for v in value]
    return value


class HubConfig:
    """统一配置管理

    支持从YAML文件加载，环境变量覆盖，嵌套访问
    """

    def __init__(self, config_path: str | Path | None = None):
        self._data: dict[str, Any] = {}
        self._config_path = Path(config_path) if config_path else None
        if self._config_path and self._config_path.exists():
            self.load(self._config_path)

    def load(self, path: str | Path) -> None:
        """从YAML文件加载配置"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        self._data = _resolve_env_vars(raw)
        self._config_path = path

    def save(self, path: str | Path | None = None) -> None:
        """保存配置到YAML文件"""
        save_path = Path(path) if path else self._config_path
        if not save_path:
            raise ValueError("未指定保存路径")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套key

        Example:
            config.get("channels.bilibili.enabled", False)
        """
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split(".")
        data = self._data
        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value

    @property
    def data_dir(self) -> Path:
        """数据存储目录"""
        d = self.get("data_dir", "./data")
        return Path(d)

    @property
    def channels_config(self) -> dict[str, Any]:
        """所有通道配置"""
        return self.get("channels", {})

    def channel_config(self, channel_name: str) -> dict[str, Any]:
        """获取指定通道配置"""
        return self.get(f"channels.{channel_name}", {})

    def is_channel_enabled(self, channel_name: str) -> bool:
        """检查通道是否启用"""
        return self.get(f"channels.{channel_name}.enabled", False)

    @property
    def outputs_config(self) -> dict[str, Any]:
        """所有输出配置"""
        return self.get("outputs", {})

    def output_config(self, output_name: str) -> dict[str, Any]:
        """获取指定输出配置"""
        return self.get(f"outputs.{output_name}", {})

    def is_output_enabled(self, output_name: str) -> bool:
        """检查输出是否启用"""
        return self.get(f"outputs.{output_name}.enabled", False)

    @property
    def events_config(self) -> dict[str, Any]:
        """事件/通知配置"""
        return self.get("events", {})

    def to_dict(self) -> dict[str, Any]:
        """导出为字典"""
        return dict(self._data)

    def __repr__(self) -> str:
        return f"HubConfig(channels={list(self.channels_config.keys())}, outputs={list(self.outputs_config.keys())})"
