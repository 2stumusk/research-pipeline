"""Cost tracking for LLM API calls.

Tracks token usage and estimates costs for different LLM providers.
"""

from __future__ import annotations

from typing import Any


class CostTracker:
    """Track LLM API costs across multiple calls.

    Supports multiple providers with different pricing models.
    """

    # Pricing per 1M tokens (as of 2026-08)
    PRICING = {
        "claude": {
            "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
            "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0},
        },
        "openai": {
            "gpt-4o-2024-08-06": {"input": 2.5, "output": 10.0},
            "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        },
        "mock": {
            "mock-model-v1": {"input": 0.0, "output": 0.0},
        },
    }

    def __init__(self):
        """Initialize cost tracker."""
        self.calls = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def add_usage(
        self,
        provider: str,
        model: str,
        usage: dict[str, int],
        stage: str | None = None,
    ) -> None:
        """Record a single LLM API call.

        Args:
            provider: Provider name (claude, openai, etc.)
            model: Model name
            usage: Dict with 'input_tokens' and 'output_tokens'
            stage: Optional stage name (triage, synthesis, etc.)
        """
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        self.calls.append(
            {
                "provider": provider,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "stage": stage,
            }
        )

    def get_cost(self, provider: str | None = None, model: str | None = None) -> float:
        """Calculate total cost in USD.

        Args:
            provider: If specified, only calculate for this provider
            model: If specified, only calculate for this model

        Returns:
            Total cost in USD
        """
        total_cost = 0.0

        for call in self.calls:
            # Filter by provider/model if specified
            if provider and call["provider"] != provider:
                continue
            if model and call["model"] != model:
                continue

            # Get pricing
            call_provider = call["provider"]
            call_model = call["model"]

            if call_provider not in self.PRICING:
                continue

            # Try exact model match first, then default to first model
            pricing = self.PRICING[call_provider].get(call_model)
            if not pricing:
                # Use first available model pricing as fallback
                first_model = next(iter(self.PRICING[call_provider].keys()))
                pricing = self.PRICING[call_provider][first_model]

            # Calculate cost
            input_cost = (call["input_tokens"] / 1_000_000) * pricing["input"]
            output_cost = (call["output_tokens"] / 1_000_000) * pricing["output"]

            total_cost += input_cost + output_cost

        return total_cost

    def get_cost_by_stage(self) -> dict[str, float]:
        """Get cost breakdown by stage.

        Returns:
            Dict mapping stage name to cost in USD
        """
        stage_costs = {}

        for call in self.calls:
            stage = call["stage"] or "unknown"

            if stage not in stage_costs:
                stage_costs[stage] = 0.0

            # Get pricing
            call_provider = call["provider"]
            call_model = call["model"]

            if call_provider not in self.PRICING:
                continue

            pricing = self.PRICING[call_provider].get(call_model)
            if not pricing:
                first_model = next(iter(self.PRICING[call_provider].keys()))
                pricing = self.PRICING[call_provider][first_model]

            # Calculate cost
            input_cost = (call["input_tokens"] / 1_000_000) * pricing["input"]
            output_cost = (call["output_tokens"] / 1_000_000) * pricing["output"]

            stage_costs[stage] += input_cost + output_cost

        return stage_costs

    def get_summary(self) -> dict[str, Any]:
        """Get comprehensive cost summary.

        Returns:
            Dict with token counts, costs, and breakdown
        """
        return {
            "total_calls": len(self.calls),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": self.get_cost(),
            "cost_by_stage": self.get_cost_by_stage(),
        }

    def format_summary(self) -> str:
        """Get formatted summary as string.

        Returns:
            Human-readable cost summary
        """
        summary = self.get_summary()

        lines = [
            "=" * 60,
            "LLM API Cost Summary",
            "=" * 60,
            f"Total Calls: {summary['total_calls']}",
            f"Input Tokens: {summary['total_input_tokens']:,}",
            f"Output Tokens: {summary['total_output_tokens']:,}",
            f"Total Tokens: {summary['total_tokens']:,}",
            f"Total Cost: ${summary['total_cost_usd']:.4f} USD",
            "",
            "Cost by Stage:",
        ]

        for stage, cost in sorted(summary["cost_by_stage"].items()):
            lines.append(f"  {stage}: ${cost:.4f}")

        lines.append("=" * 60)

        return "\n".join(lines)
