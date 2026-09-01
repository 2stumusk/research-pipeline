"""Configuration normalization for LLM settings.

This module provides backward-compatible config normalization for both:
1. Legacy 'codex' config format (production default)
2. New 'llm' format (experimental construction-only)

The formal production pipeline uses native CodexRunner. Experimental direct
Claude/OpenAI providers are construction-only and must not be selected from
environment API key presence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .config import AppConfig


def normalize_llm_config(
    config: dict[str, Any] | AppConfig | Path,
) -> dict[str, Any]:
    """Normalize LLM configuration from multiple input formats.

    Args:
        config: Config dict, AppConfig instance, or Path to YAML file

    Returns:
        Normalized LLM config dict with provider, models, base_url, etc.
    """
    # Load from file if Path provided
    if isinstance(config, Path):
        with open(config, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    # Extract data from AppConfig
    elif isinstance(config, AppConfig):
        data = config.data
    else:
        data = config

    if not isinstance(data, dict):
        raise ValueError("Config must be a dict, AppConfig, or Path to YAML")

    # Check for explicit new llm config
    if "llm" in data:
        llm_config = dict(data["llm"])
        # Ensure base_url is present
        if "base_url" not in llm_config:
            llm_config["base_url"] = None
        return llm_config

    # Convert legacy codex format to normalized format
    # Legacy codex -> provider: codex (NOT claude)
    codex_config = data.get("codex", {})

    # Extract base_url if present in codex config
    base_url = codex_config.get("base_url")

    result = {
        "provider": "codex",  # Legacy codex maps to codex provider
        "binary": codex_config.get("binary", "codex"),
        "base_url": base_url,
        "max_retries": codex_config.get("retries", 3),
        "timeout": codex_config.get("timeout_seconds", 1800),
        "reasoning_effort": codex_config.get("reasoning_effort", {}),
        "verbosity": codex_config.get("verbosity", {}),
        "models": codex_config.get("models", {}),
        "sandbox": codex_config.get("sandbox", "read-only"),
        "ask_for_approval": codex_config.get("ask_for_approval", "never"),
        "web_search": codex_config.get("web_search", False),
        "max_parallel": codex_config.get("max_parallel", 3),
        "isolate_user_config": codex_config.get("isolate_user_config", True),
        "isolate_runtime_workspace": codex_config.get("isolate_runtime_workspace", True),
        "ignore_rules": codex_config.get("ignore_rules", True),
    }

    return result


def get_stage_config(
    llm_config: dict[str, Any], stage: str
) -> dict[str, Any]:
    """Get stage-specific LLM configuration.

    Args:
        llm_config: Base LLM config from normalize_llm_config()
        stage: Stage name (triage, synthesis, deep_dive, qc)

    Returns:
        Stage-specific config dict with optional temperature/max_tokens defaults
    """
    models_map = llm_config.get("models", {})
    reasoning_effort = llm_config.get("reasoning_effort", {})
    verbosity = llm_config.get("verbosity", {})

    # Get stage-specific model
    stage_model = models_map.get(stage) or llm_config.get("model", "")

    # Get stage-specific reasoning effort
    stage_effort = reasoning_effort.get(stage, "medium")

    # Get stage-specific verbosity
    stage_verbosity = verbosity.get(stage, "medium")

    result = {
        "provider": llm_config.get("provider", "codex"),
        "model": stage_model,
        "binary": llm_config.get("binary", "codex"),
        "base_url": llm_config.get("base_url"),
        "max_retries": llm_config.get("max_retries", 3),
        "timeout": llm_config.get("timeout", 1800),
        "reasoning_effort": stage_effort,
        "verbosity": stage_verbosity,
        "sandbox": llm_config.get("sandbox", "read-only"),
        "ask_for_approval": llm_config.get("ask_for_approval", "never"),
        "web_search": llm_config.get("web_search", False),
        "temperature": llm_config.get("temperature", 0.0),
        "max_tokens": llm_config.get("max_tokens", 4096),
    }

    return result


def load_llm_config(config: dict[str, Any] | AppConfig | Path) -> dict[str, Any]:
    """Backwards-compatible alias for normalize_llm_config.

    Accepts Path, AppConfig, or dict. Legacy no-llm config and explicit
    llm.provider=codex normalize to codex provider.

    Args:
        config: Config dict, AppConfig instance, or Path to YAML file

    Returns:
        Normalized LLM config dict
    """
    return normalize_llm_config(config)
