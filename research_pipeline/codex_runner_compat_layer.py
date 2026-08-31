"""DEPRECATED: Use llm_runner instead.

This module provides backward compatibility for code that imports CodexRunner.
All new code should use llm_runner.LLMRunner instead.

This compatibility layer will be removed in v0.3.0.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "codex_runner is deprecated and will be removed in v0.3.0. "
    "Please update your imports: "
    "from research_pipeline.llm_runner import LLMRunner, LLMRunnerError",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from llm_runner for backward compatibility
from .llm_runner import LLMRunner as CodexRunner
from .llm_runner import LLMRunnerError as CodexError

__all__ = ['CodexRunner', 'CodexError']
