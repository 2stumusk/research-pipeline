"""Adapter to use LLMRunner with CodexRunner interface.

This allows existing code to use the new LLM architecture without major refactoring.
Integrates CostTracker for monitoring API usage costs.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .config import AppConfig
from .cost_tracker import CostTracker
from .llm_runner import LLMRunner, LLMRunnerError, create_runner_from_config
from .utils import atomic_write_text, read_json, write_json


class LLMAdapter:
    """Adapter that provides CodexRunner-compatible interface using LLMRunner."""

    def __init__(self, config: AppConfig, logger: Any) -> None:
        self.config = config
        self.logger = logger
        self.cost_tracker = CostTracker()

        # Load LLM config from YAML
        config_path = config.root / "config" / "config.yaml"
        if not config_path.exists():
            config_path = config.root / "config" / "config.v0.2.yaml"

        from .config_loader import load_llm_config
        self.llm_config = load_llm_config(config_path)

        # We'll create runners per stage on demand
        self._runners: dict[str, LLMRunner] = {}

    def available(self) -> bool:
        """Check if LLM provider is available."""
        try:
            runner = self._get_runner("triage")
            # Try to validate config
            runner.provider.validate_config()
            return True
        except Exception:
            return False

    def version(self) -> str:
        """Return provider and model info."""
        try:
            runner = self._get_runner("triage")
            provider_name = runner.provider_name
            model = runner.provider.get_model_name()
            return f"{provider_name} ({model})"
        except Exception:
            return ""

    def _get_runner(self, stage: str) -> LLMRunner:
        """Get or create runner for a specific stage."""
        if stage not in self._runners:
            from .config_loader import get_stage_config
            stage_config = get_stage_config(self.llm_config, stage)
            self._runners[stage] = create_runner_from_config(stage_config)
        return self._runners[stage]

    def run_structured(
        self,
        *,
        stage: str,
        prompt: str,
        schema_path: Path,
        output_path: Path,
        audit_dir: Path,
        label: str,
    ) -> dict[str, Any]:
        """Run LLM with structured output, mimicking CodexRunner interface.

        Args:
            stage: Stage name (triage, synthesis, deep_dive, qc)
            prompt: The prompt text
            schema_path: Path to JSON schema file
            output_path: Where to write the result JSON
            audit_dir: Directory for audit logs (prompt, stdout, stderr)
            label: Label for logging

        Returns:
            Validated JSON object matching the schema

        Raises:
            LLMRunnerError: If execution fails
        """
        # Load and validate schema
        schema = read_json(schema_path)
        if not isinstance(schema, dict):
            raise LLMRunnerError(f"Invalid JSON Schema: {schema_path}")
        validator = Draft202012Validator(schema)

        # Create audit directory and save prompt
        audit_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = audit_dir / f"{label}.prompt.md"
        stdout_path = audit_dir / f"{label}.stdout.log"
        stderr_path = audit_dir / f"{label}.stderr.log"
        atomic_write_text(prompt_path, prompt)

        # Get runner for this stage
        runner = self._get_runner(stage)

        self.logger.info("LLM %s: 开始执行", label)
        started = time.monotonic()

        try:
            # Call LLM with schema
            response = runner.run(
                prompt=prompt,
                json_schema=schema,
            )

            elapsed = time.monotonic() - started

            # Log response details
            stdout_content = f"Model: {response.model}\n"
            if response.usage:
                stdout_content += f"Usage: {response.usage}\n"
                # Track cost
                self.cost_tracker.add_usage(
                    provider=runner.provider_name,
                    model=response.model,
                    usage=response.usage,
                    stage=stage,
                )
            stdout_content += f"\nContent:\n{response.content}\n"
            atomic_write_text(stdout_path, stdout_content)
            atomic_write_text(stderr_path, "")  # Empty stderr for success

            # Validate structured output
            if response.structured_output is None:
                raise LLMRunnerError("LLM did not return structured output")

            data = response.structured_output

            # Validate against schema
            errors = sorted(validator.iter_errors(data), key=lambda err: list(err.path))
            if errors:
                preview = "; ".join(
                    f"{'/'.join(map(str, err.path)) or '<root>'}: {err.message}"
                    for err in errors[:5]
                )
                raise LLMRunnerError(f"JSON Schema validation failed: {preview}")

            # Write output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(output_path, data)

            self.logger.info("LLM %s 完成，耗时 %.1fs", label, elapsed)
            return data

        except LLMRunnerError as exc:
            elapsed = time.monotonic() - started
            error_msg = f"LLM {label} 失败: {exc}\n耗时: {elapsed:.1f}s"
            atomic_write_text(stderr_path, error_msg)
            self.logger.error(error_msg)
            raise

        except Exception as exc:
            elapsed = time.monotonic() - started
            error_msg = f"LLM {label} 未预期错误: {exc}\n耗时: {elapsed:.1f}s"
            atomic_write_text(stderr_path, error_msg)
            self.logger.exception(error_msg)
            raise LLMRunnerError(f"{label} 失败: {exc}") from exc

    def get_cost_summary(self) -> dict[str, Any]:
        """Get cost tracking summary.

        Returns:
            Cost summary dict with token counts and cost breakdown
        """
        return self.cost_tracker.get_summary()

    def format_cost_summary(self) -> str:
        """Get formatted cost summary as string.

        Returns:
            Human-readable cost summary
        """
        return self.cost_tracker.format_summary()


# For backward compatibility
CodexRunner = LLMAdapter
CodexError = LLMRunnerError
