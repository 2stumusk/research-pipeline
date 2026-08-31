"""Base LLM Provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


@dataclass
class LLMResponse:
    """Standardized LLM response.

    Attributes:
        content: The text response from the LLM
        structured_output: If JSON schema was provided, the validated JSON object
        usage: Token usage statistics (dict with 'input_tokens', 'output_tokens')
        model: The actual model that was used
        raw_response: Original response object from the provider (for debugging)
    """
    content: str
    structured_output: dict[str, Any] | None = None
    usage: dict[str, int] | None = None
    model: str = ""
    raw_response: Any = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All providers must implement this interface to ensure consistency.
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        timeout: int = 120,
    ):
        """Initialize the provider.

        Args:
            model: Model name. If None, use provider default.
            api_key: API key. If None, will try to read from environment.
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        """
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        json_schema: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            json_schema: If provided, force structured JSON output matching this schema
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with content and optional structured output

        Raises:
            LLMError: If the API call fails or validation fails
        """
        pass

    @abstractmethod
    def validate_config(self) -> None:
        """Validate that the provider is properly configured.

        Should check:
        - API key is available
        - Model is valid
        - Network connectivity (optional)

        Raises:
            LLMError: If configuration is invalid
        """
        pass

    def get_model_name(self) -> str:
        """Get the actual model name that will be used.

        Returns:
            Model name string
        """
        return self.model or self._default_model()

    @abstractmethod
    def _default_model(self) -> str:
        """Return the default model name for this provider."""
        pass
