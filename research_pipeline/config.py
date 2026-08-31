from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


class ConfigError(RuntimeError):
    pass


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class AppConfig:
    def __init__(self, root: Path, data: dict[str, Any], source: Path) -> None:
        self.root = root.resolve()
        self.data = data
        self.source = source.resolve()

    def get(self, dotted: str, default: Any = None) -> Any:
        current: Any = self.data
        for part in dotted.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def path(self, name: str) -> Path:
        raw = self.get(f"paths.{name}")
        if not raw:
            raise ConfigError(f"缺少路径配置：paths.{name}")
        path = Path(str(raw)).expanduser()
        return path if path.is_absolute() else self.root / path

    def ensure_directories(self) -> None:
        for key in ("inbox", "archive", "extracted", "outputs", "logs"):
            self.path(key).mkdir(parents=True, exist_ok=True)
        self.path("database").parent.mkdir(parents=True, exist_ok=True)
        self.path("watchlist").parent.mkdir(parents=True, exist_ok=True)


def load_config(config_path: Path | None = None) -> AppConfig:
    root = Path(__file__).resolve().parents[1]
    source = config_path or root / "config" / "config.yaml"
    source = source.expanduser().resolve()
    if not source.exists():
        raise ConfigError(f"配置文件不存在：{source}")

    with source.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError("配置文件顶层必须是对象")

    local_override = root / "config.local.yaml"
    if local_override.exists() and local_override.resolve() != source:
        with local_override.open("r", encoding="utf-8") as handle:
            override = yaml.safe_load(handle) or {}
        if not isinstance(override, dict):
            raise ConfigError("config.local.yaml 顶层必须是对象")
        data = deep_merge(data, override)

    config = AppConfig(root=root, data=data, source=source)
    config.ensure_directories()
    return config
