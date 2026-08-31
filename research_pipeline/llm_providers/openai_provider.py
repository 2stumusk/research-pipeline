"""OpenAI API provider."""

from __future__ import annotations

import json
import os
from typing import Any

from .base import LLMError, LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI API provider.

    Requires: pip install openai
    Environment: OPENAI_API_KEY
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._client: Any = None

    def _default_model(self) -> str:
        return "gpt-4o-2024-08-06"

    def _get_client(self) -> Any:
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                import openai
            except ImportError as exc:
                raise LLMError(
                    "openai package not installed. "
                    "Install with: pip install openai"
                ) from exc

            api_key = self.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise LLMError(
                    "OPENAI_API_KEY not found. "
                    "Set it via environment variable or pass api_key parameter."
                )

            self._client = openai.OpenAI(api_key=api_key)

        return self._client

    def validate_config(self) -> None:
        """Validate OpenAI configuration."""
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("OPENAI_API_KEY not set")

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        json_schema: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response using OpenAI API.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            json_schema: If provided, uses structured output (response_format)
            **kwargs: Additional parameters for OpenAI API

        Returns:
            LLMResponse

        Raises:
            LLMError: If API call fails or JSON validation fails
        """
        client = self._get_client()
        model = self.get_model_name()

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build request parameters
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        # If JSON schema provided, use structured output
        if json_schema:
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "schema": json_schema,
                    "strict": True,
                }
            }

        try:
            response = client.chat.completions.create(**params)
        except Exception as exc:
            raise LLMError(f"OpenAI API call failed: {exc}") from exc

        # Extract content
        content = response.choices[0].message.content or ""

        # Parse structured output if JSON schema was used
        structured_output = None
        if json_schema and content:
            try:
                structured_output = json.loads(content)
            except json.JSONDecodeError as exc:
                raise LLMError(f"Failed to parse JSON response: {exc}") from exc

        # Extract usage
        usage = None
        if hasattr(response, "usage") and response.usage:
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

        return LLMResponse(
            content=content,
            structured_output=structured_output,
            usage=usage,
            model=response.model,
            raw_response=response,
        )
