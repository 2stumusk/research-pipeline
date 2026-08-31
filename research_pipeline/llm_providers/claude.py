"""Anthropic Claude API provider."""

from __future__ import annotations

import json
import os
from typing import Any

from .base import LLMError, LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API provider.

    Requires: pip install anthropic
    Environment: ANTHROPIC_API_KEY
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._client: Any = None

    def _default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    def _get_client(self) -> Any:
        """Lazy-load the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:
                raise LLMError(
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
                ) from exc

            api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise LLMError(
                    "ANTHROPIC_API_KEY not found. "
                    "Set it via environment variable or pass api_key parameter."
                )

            self._client = anthropic.Anthropic(api_key=api_key)

        return self._client

    def validate_config(self) -> None:
        """Validate Claude configuration."""
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY not set")

        # Basic validation of model name
        model = self.get_model_name()
        if not model.startswith("claude-"):
            raise LLMError(f"Invalid Claude model name: {model}")

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        json_schema: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response using Claude API.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            json_schema: If provided, uses tool-based structured output
            **kwargs: Additional parameters for Claude API

        Returns:
            LLMResponse

        Raises:
            LLMError: If API call fails or JSON validation fails
        """
        client = self._get_client()
        model = self.get_model_name()

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Build request parameters
        params: dict[str, Any] = {
            "model": model,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "messages": messages,
        }

        if system_prompt:
            params["system"] = system_prompt

        # If JSON schema provided, use tool-based structured output
        if json_schema:
            params["tools"] = [
                {
                    "name": "structured_output",
                    "description": "Return structured data matching the schema",
                    "input_schema": json_schema,
                }
            ]
            params["tool_choice"] = {"type": "tool", "name": "structured_output"}

        try:
            response = client.messages.create(**params)
        except Exception as exc:
            raise LLMError(f"Claude API call failed: {exc}") from exc

        # Extract content
        content = ""
        structured_output = None

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use" and block.name == "structured_output":
                structured_output = block.input

        # Extract usage
        usage = None
        if hasattr(response, "usage"):
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }

        return LLMResponse(
            content=content,
            structured_output=structured_output,
            usage=usage,
            model=response.model,
            raw_response=response,
        )
