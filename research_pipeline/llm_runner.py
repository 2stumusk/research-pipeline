"""LLM Runner - unified interface for calling LLMs with retry logic.

This replaces the original codex_runner.py with a provider-agnostic implementation.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from .llm_providers import LLMError, LLMProvider, LLMResponse, get_provider


logger = logging.getLogger(__name__)


class LLMRunnerError(Exception):
    """Exception raised by LLMRunner."""
    pass


class LLMRunner:
    """Unified LLM runner with retry logic and structured output validation.

    This class abstracts away the differences between LLM providers
    and provides a consistent interface for the pipeline.
    """

    def __init__(
        self,
        provider: str = "claude",
        model: str | None = None,
        api_key: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        timeout: int = 120,
    ):
        """Initialize LLM runner.

        Args:
            provider: Provider name ("claude", "openai")
            model: Model name (optional, uses provider default if None)
            api_key: API key (optional, reads from environment if None)
            max_retries: Maximum number of retries on failure
            retry_delay: Delay between retries in seconds
            timeout: Request timeout in seconds
        """
        self.provider_name = provider
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        try:
            self.provider: LLMProvider = get_provider(
                provider,
                model=model,
                api_key=api_key,
                timeout=timeout,
            )
        except ValueError as exc:
            raise LLMRunnerError(f"Failed to initialize provider: {exc}") from exc

        # Validate configuration
        try:
            self.provider.validate_config()
        except LLMError as exc:
            raise LLMRunnerError(f"Provider configuration invalid: {exc}") from exc

    def run(
        self,
        prompt: str,
        system_prompt: str | None = None,
        json_schema: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Run LLM with retry logic.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            json_schema: If provided, enforces structured JSON output
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse

        Raises:
            LLMRunnerError: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    json_schema=json_schema,
                    **kwargs,
                )

                # If JSON schema was provided, validate structured output exists
                if json_schema and response.structured_output is None:
                    raise LLMRunnerError(
                        "Expected structured output but got None. "
                        "The LLM may have refused to use the required format."
                    )

                logger.info(
                    f"LLM call succeeded (provider={self.provider_name}, "
                    f"model={response.model}, "
                    f"tokens={response.usage})"
                )

                return response

            except LLMError as exc:
                last_error = exc
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{self.max_retries}): {exc}"
                )

                # Don't retry on certain errors
                if "api key" in str(exc).lower() or "unauthorized" in str(exc).lower():
                    raise LLMRunnerError(f"Authentication failed: {exc}") from exc

                # Wait before retry (exponential backoff)
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)

        # All retries failed
        raise LLMRunnerError(
            f"LLM call failed after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        ) from last_error

    def run_with_schema_file(
        self,
        prompt: str,
        system_prompt: str | None,
        schema_path: Path,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run LLM with JSON schema loaded from file.

        This is a convenience method for the common pattern of:
        1. Load JSON schema from file
        2. Call LLM with structured output
        3. Return the validated JSON object

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            schema_path: Path to JSON schema file
            **kwargs: Additional provider-specific parameters

        Returns:
            Validated JSON object matching the schema

        Raises:
            LLMRunnerError: If schema file not found or LLM call fails
        """
        # Load schema
        if not schema_path.exists():
            raise LLMRunnerError(f"Schema file not found: {schema_path}")

        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise LLMRunnerError(
                f"Invalid JSON schema in {schema_path}: {exc}"
            ) from exc

        # Call LLM
        response = self.run(
            prompt=prompt,
            system_prompt=system_prompt,
            json_schema=schema,
            **kwargs,
        )

        # Return structured output
        if response.structured_output is None:
            raise LLMRunnerError(
                "Expected structured output but got None. "
                "This should not happen after validation."
            )

        return response.structured_output


# Backward compatibility: keep the CodexError name
CodexError = LLMRunnerError


def create_runner_from_config(config: dict[str, Any]) -> LLMRunner:
    """Create LLMRunner from configuration dict.

    Args:
        config: Configuration dict with keys:
            - provider: "claude" or "openai"
            - model: Model name (optional)
            - api_key_env: Environment variable name for API key (optional)
            - max_retries: Max retries (optional, default 3)
            - timeout: Timeout in seconds (optional, default 120)
            - temperature: Temperature for sampling (optional, default 0.0)
            - max_tokens: Max tokens in response (optional, default 4096)

    Returns:
        Configured LLMRunner

    Example config:
        {
            "provider": "claude",
            "model": "claude-3-5-sonnet-20241022",
            "api_key_env": "ANTHROPIC_API_KEY",
            "max_retries": 3,
            "timeout": 120,
            "temperature": 0.0,
            "max_tokens": 4096
        }
    """
    import os

    provider = config.get("provider", "claude")
    model = config.get("model")
    api_key_env = config.get("api_key_env")

    # Read API key from environment if specified
    api_key = None
    if api_key_env:
        api_key = os.getenv(api_key_env)

    runner = LLMRunner(
        provider=provider,
        model=model,
        api_key=api_key,
        max_retries=config.get("max_retries", 3),
        retry_delay=config.get("retry_delay", 2.0),
        timeout=config.get("timeout", 120),
    )

    # Override provider-level settings if specified in config
    temperature = config.get("temperature")
    if temperature is not None:
        runner.provider.temperature = temperature

    max_tokens = config.get("max_tokens")
    if max_tokens is not None:
        runner.provider.max_tokens = max_tokens

    return runner


def create_runner_from_yaml(
    config_path: Path, stage: str = "triage"
) -> LLMRunner:
    """Create LLMRunner from YAML config file.

    Args:
        config_path: Path to config YAML file
        stage: Stage name (triage, synthesis, deep_dive, qc)

    Returns:
        Configured LLMRunner for the specified stage
    """
    from .config_loader import load_llm_config, get_stage_config

    llm_config = load_llm_config(config_path)
    stage_config = get_stage_config(llm_config, stage)

    return create_runner_from_config(stage_config)
