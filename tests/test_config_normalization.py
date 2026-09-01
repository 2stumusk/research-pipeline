"""Tests for config normalization and backward compatibility."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from research_pipeline.config_loader import (
    normalize_llm_config,
    get_stage_config,
    load_llm_config,
)


class TestConfigNormalization(unittest.TestCase):
    """Test config normalization for legacy codex and new llm formats."""

    def test_legacy_codex_maps_to_codex_provider(self):
        """Legacy codex config should map to provider: codex, not claude."""
        legacy_config = {
            "codex": {
                "binary": "codex",
                "models": {"triage": "", "synthesis": ""},
                "retries": 2,
                "timeout_seconds": 1800,
            }
        }

        normalized = normalize_llm_config(legacy_config)

        self.assertEqual(normalized["provider"], "codex")
        self.assertEqual(normalized["binary"], "codex")
        self.assertEqual(normalized["max_retries"], 2)
        self.assertEqual(normalized["timeout"], 1800)

    def test_explicit_llm_config_preserved(self):
        """Explicit llm config should be used as-is for construction only."""
        explicit_config = {
            "llm": {
                "provider": "claude",
                "model": "claude-opus-5",
                "base_url": "https://custom.api.com",
            }
        }

        normalized = normalize_llm_config(explicit_config)

        self.assertEqual(normalized["provider"], "claude")
        self.assertEqual(normalized["model"], "claude-opus-5")
        self.assertEqual(normalized["base_url"], "https://custom.api.com")

    def test_base_url_propagation(self):
        """base_url should propagate through stage configs."""
        config = {
            "codex": {
                "binary": "codex",
                "base_url": "https://proxy.example.com",
                "models": {"triage": ""},
            }
        }

        normalized = normalize_llm_config(config)
        stage_config = get_stage_config(normalized, "triage")

        self.assertEqual(stage_config["base_url"], "https://proxy.example.com")
        self.assertEqual(stage_config["provider"], "codex")

    def test_load_llm_config_alias(self):
        """load_llm_config should be backwards-compatible alias."""
        config = {
            "codex": {
                "binary": "codex",
                "models": {"triage": ""},
            }
        }

        result = load_llm_config(config)

        self.assertEqual(result["provider"], "codex")
        self.assertEqual(result["binary"], "codex")


class TestNoEnvKeyImplicitSwitch(unittest.TestCase):
    """Test that normalization contains no implicit provider selection."""

    def test_normalization_preserves_codex_provider(self):
        """Normalization should not contain implicit provider switching logic."""
        config = {
            "codex": {
                "binary": "codex",
                "models": {"triage": ""},
            }
        }

        normalized = normalize_llm_config(config)

        self.assertEqual(normalized["provider"], "codex")

    def test_explicit_codex_provider_preserved(self):
        """Explicit llm.provider=codex should remain codex."""
        config = {
            "llm": {
                "provider": "codex",
                "binary": "codex",
            }
        }

        normalized = normalize_llm_config(config)

        self.assertEqual(normalized["provider"], "codex")

    def test_no_llm_section_normalizes_to_codex(self):
        """Config with no llm section should normalize to codex."""
        config = {
            "codex": {
                "binary": "codex",
                "models": {"triage": ""},
            }
        }

        normalized = normalize_llm_config(config)

        self.assertEqual(normalized["provider"], "codex")


class TestExperimentalProviderConstruction(unittest.TestCase):
    """Test experimental provider construction with base_url and mocks."""

    def test_claude_base_url_passed_to_construction(self):
        """base_url should be passed during Claude provider construction."""
        mock_anthropic = MagicMock()
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            from research_pipeline.llm_providers.claude import ClaudeProvider

            credential = object()
            provider = ClaudeProvider(
                api_key=credential,
                base_url="https://custom.example.com/v1"
            )

            provider._get_client()

            mock_anthropic.Anthropic.assert_called_once_with(
                api_key=credential,
                base_url="https://custom.example.com/v1"
            )

    def test_openai_base_url_passed_to_construction(self):
        """base_url should be passed during OpenAI provider construction."""
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai}):
            from research_pipeline.llm_providers.openai_provider import OpenAIProvider

            credential = object()
            provider = OpenAIProvider(
                api_key=credential,
                base_url="https://custom.openai.example.com"
            )

            provider._get_client()

            mock_openai.OpenAI.assert_called_once_with(
                api_key=credential,
                base_url="https://custom.openai.example.com"
            )

    def test_llm_runner_rejects_codex_provider(self):
        """LLMRunner should reject provider='codex'."""
        from research_pipeline.llm_runner import LLMRunner, LLMRunnerError

        with self.assertRaises(LLMRunnerError) as ctx:
            LLMRunner(provider="codex")

        self.assertIn("codex", str(ctx.exception).lower())
        self.assertIn("CodexRunner", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
