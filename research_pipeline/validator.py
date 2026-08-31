"""Configuration validator.

Validates configuration files and environment before running the pipeline.
Provides clear error messages to help users fix issues.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


class ValidationError(Exception):
    """Configuration validation error."""

    pass


class ConfigValidator:
    """Validate configuration and environment."""

    def __init__(self, config_path: Path):
        """Initialize validator.

        Args:
            config_path: Path to config.yaml
        """
        self.config_path = config_path
        self.errors = []
        self.warnings = []

    def validate_all(self) -> bool:
        """Run all validations.

        Returns:
            True if all validations pass

        Raises:
            ValidationError: If critical validation fails
        """
        self.errors = []
        self.warnings = []

        # Load config
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            raise ValidationError(f"Config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in config file: {e}")

        # Run validations
        self._validate_llm_config()
        self._validate_paths()
        self._validate_pipeline_config()
        self._validate_watchlist()

        # Report results
        if self.errors:
            error_msg = "\n".join([f"  ❌ {e}" for e in self.errors])
            raise ValidationError(f"Configuration validation failed:\n{error_msg}")

        if self.warnings:
            warning_msg = "\n".join([f"  ⚠️  {w}" for w in self.warnings])
            print(f"Configuration warnings:\n{warning_msg}\n")

        return True

    def _validate_llm_config(self) -> None:
        """Validate LLM configuration."""
        llm_config = self.config.get("llm", {})

        # Check provider
        provider = llm_config.get("provider")
        if not provider:
            self.errors.append("LLM provider not specified in config")
            return

        valid_providers = ["claude", "openai", "mock"]
        if provider not in valid_providers:
            self.errors.append(
                f"Unknown LLM provider: {provider}. "
                f"Valid options: {', '.join(valid_providers)}"
            )

        # Check API key (not required for mock)
        if provider != "mock":
            api_key_env = llm_config.get("api_key_env")
            if not api_key_env:
                self.errors.append(
                    f"api_key_env not specified for provider: {provider}"
                )
            else:
                api_key = os.getenv(api_key_env)
                if not api_key:
                    self.errors.append(
                        f"Environment variable {api_key_env} not set. "
                        f"Set it with: export {api_key_env}='your_key_here'"
                    )

        # Check reasoning effort values
        reasoning_effort = llm_config.get("reasoning_effort", {})
        valid_efforts = ["low", "medium", "high"]

        for stage, effort in reasoning_effort.items():
            if effort not in valid_efforts:
                self.warnings.append(
                    f"Invalid reasoning_effort for {stage}: {effort}. "
                    f"Valid options: {', '.join(valid_efforts)}"
                )

    def _validate_paths(self) -> None:
        """Validate required paths exist and are writable."""
        paths_config = self.config.get("paths", {})

        # Check directories that should exist or be creatable
        for key in ["inbox", "database", "outputs", "logs"]:
            path_str = paths_config.get(key)
            if not path_str:
                self.errors.append(f"Path '{key}' not specified in config")
                continue

            path = Path(path_str)

            # For database path, check parent directory
            if key == "database":
                path = path.parent

            # Try to create if doesn't exist
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.errors.append(f"Cannot create directory {path}: {e}")

        # Check watchlist file
        watchlist_path = paths_config.get("watchlist")
        if watchlist_path:
            watchlist_file = Path(watchlist_path)
            if not watchlist_file.exists():
                self.warnings.append(
                    f"Watchlist file not found: {watchlist_file}. "
                    f"Create it or copy from config/watchlist.csv"
                )

    def _validate_pipeline_config(self) -> None:
        """Validate pipeline configuration."""
        pipeline_config = self.config.get("pipeline", {})

        # Check numeric values are reasonable
        checks = [
            ("batch_max_reports", 1, 20),
            ("top_n", 1, 50),
            ("deep_dive_n", 0, 50),
            ("min_deep_dive_score", 0, 100),
        ]

        for key, min_val, max_val in checks:
            value = pipeline_config.get(key)
            if value is not None:
                if not isinstance(value, int):
                    self.errors.append(f"{key} must be an integer, got: {type(value)}")
                elif value < min_val or value > max_val:
                    self.warnings.append(
                        f"{key}={value} is outside recommended range "
                        f"[{min_val}, {max_val}]"
                    )

    def _validate_watchlist(self) -> None:
        """Validate watchlist file format."""
        paths_config = self.config.get("paths", {})
        watchlist_path = paths_config.get("watchlist")

        if not watchlist_path:
            return

        watchlist_file = Path(watchlist_path)
        if not watchlist_file.exists():
            return  # Already warned in _validate_paths

        try:
            import csv

            with open(watchlist_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Check required columns
            required_cols = ["market", "ticker", "name"]
            if rows:
                first_row = rows[0]
                missing_cols = [col for col in required_cols if col not in first_row]

                if missing_cols:
                    self.errors.append(
                        f"Watchlist missing required columns: {', '.join(missing_cols)}"
                    )

            # Check at least one entry
            if not rows:
                self.warnings.append("Watchlist is empty")

        except Exception as e:
            self.errors.append(f"Failed to read watchlist: {e}")


def validate_config(config_path: Path) -> bool:
    """Validate configuration.

    Args:
        config_path: Path to config.yaml

    Returns:
        True if validation passes

    Raises:
        ValidationError: If validation fails
    """
    validator = ConfigValidator(config_path)
    return validator.validate_all()
