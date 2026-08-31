"""Configuration loader for LLM settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def load_llm_config(config_path: Path) -> dict[str, Any]:
    """Load LLM configuration from YAML file.

    Supports both old 'codex' format and new 'llm' format.

    Args:
        config_path: Path to YAML config file

    Returns:
        LLM configuration dict
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # If new format exists, use it
    if "llm" in config:
        return config["llm"]

    # Otherwise, convert old codex format
    codex_config = config.get("codex", {})
    return {
        "provider": "claude",  # default to claude
        "model": "",
        "api_key_env": "ANTHROPIC_API_KEY",
        "max_retries": codex_config.get("retries", 3),
        "timeout": codex_config.get("timeout_seconds", 120),
        "reasoning_effort": codex_config.get("reasoning_effort", {}),
    }


def get_stage_config(
    llm_config: dict[str, Any], stage: str
) -> dict[str, Any]:
    """Get stage-specific LLM configuration.

    Args:
        llm_config: Base LLM config from load_llm_config()
        stage: Stage name (triage, synthesis, deep_dive, qc)

    Returns:
        Stage-specific config with temperature and max_tokens
    """
    reasoning_effort = llm_config.get("reasoning_effort", {})
    temperature_map = llm_config.get("temperature", {})
    max_tokens_map = llm_config.get("max_tokens", {})

    # Map reasoning effort to temperature (if not explicitly set)
    effort = reasoning_effort.get(stage, "medium")
    if stage not in temperature_map:
        temperature_map[stage] = {
            "low": 0.0,
            "medium": 0.0,
            "high": 0.1,
        }.get(effort, 0.0)

    # Default max tokens by stage
    if stage not in max_tokens_map:
        max_tokens_map[stage] = {
            "triage": 4096,
            "synthesis": 8192,
            "deep_dive": 16384,
            "qc": 4096,
        }.get(stage, 4096)

    return {
        "provider": llm_config["provider"],
        "model": llm_config.get("model"),
        "api_key_env": llm_config.get("api_key_env"),
        "max_retries": llm_config.get("max_retries", 3),
        "timeout": llm_config.get("timeout", 120),
        "temperature": temperature_map[stage],
        "max_tokens": max_tokens_map[stage],
    }
