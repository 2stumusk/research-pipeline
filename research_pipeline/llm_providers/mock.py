"""Mock LLM Provider for testing without API calls.

This provider returns predefined responses, allowing the entire pipeline
to run without a real API key or incurring any costs.
"""

from __future__ import annotations

import json
from typing import Any

from .base import LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    """Mock LLM Provider for testing.

    Returns predefined responses based on the prompt or schema.
    Useful for:
    - Testing the pipeline without API costs
    - Development without API keys
    - Regression testing with consistent outputs
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._call_count = 0

    def _default_model(self) -> str:
        return "mock-model-v1"

    def validate_config(self) -> None:
        """Mock provider always validates successfully."""
        pass

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        json_schema: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate mock response.

        Args:
            prompt: User prompt
            system_prompt: System prompt (ignored for mock)
            json_schema: If provided, generates structured output
            **kwargs: Additional parameters (ignored for mock)

        Returns:
            LLMResponse with mock content
        """
        self._call_count += 1

        # Generate structured output if schema provided
        if json_schema:
            structured_output = self._generate_mock_structured(json_schema, prompt)
            content = json.dumps(structured_output, ensure_ascii=False)
        else:
            content = self._generate_mock_text(prompt)

        # Simulate realistic token usage
        input_tokens = len(prompt.split())
        output_tokens = len(content.split())

        return LLMResponse(
            content=content,
            structured_output=structured_output if json_schema else None,
            usage={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            model=self._default_model(),
            raw_response={"mock": True, "call_count": self._call_count},
        )

    def _generate_mock_structured(
        self, schema: dict[str, Any], prompt: str
    ) -> dict[str, Any]:
        """Generate mock structured output based on schema.

        Args:
            schema: JSON Schema
            prompt: User prompt (used to customize response)

        Returns:
            Dict matching the schema
        """
        properties = schema.get("properties", {})
        result = {}

        # Detect if this is a research report scoring task
        if "importance_score" in properties:
            # Mock research report scoring
            result = {
                "importance_score": 75,
                "direction": 2,
                "confidence": 80,
                "reasoning": "这是一个模拟的研报评分结果。实际使用时会调用真实的 LLM API。",
            }

            # Add any other required fields
            for key, value_schema in properties.items():
                if key not in result:
                    result[key] = self._mock_value_for_type(value_schema)

        else:
            # Generic mock based on schema
            for key, value_schema in properties.items():
                result[key] = self._mock_value_for_type(value_schema)

        return result

    def _mock_value_for_type(self, schema: dict[str, Any]) -> Any:
        """Generate mock value based on JSON Schema type.

        Args:
            schema: JSON Schema for this field

        Returns:
            Mock value of appropriate type
        """
        type_name = schema.get("type", "string")

        if type_name == "integer":
            minimum = schema.get("minimum", 0)
            maximum = schema.get("maximum", 100)
            return (minimum + maximum) // 2

        elif type_name == "number":
            return 42.5

        elif type_name == "boolean":
            return True

        elif type_name == "array":
            items_schema = schema.get("items", {})
            # Return array with 2 mock items
            return [
                self._mock_value_for_type(items_schema),
                self._mock_value_for_type(items_schema),
            ]

        elif type_name == "object":
            properties = schema.get("properties", {})
            return {
                key: self._mock_value_for_type(value_schema)
                for key, value_schema in properties.items()
            }

        else:  # string or default
            description = schema.get("description", "")
            if description:
                return f"模拟数据: {description}"
            return "这是模拟生成的文本内容"

    def _generate_mock_text(self, prompt: str) -> str:
        """Generate mock text response.

        Args:
            prompt: User prompt

        Returns:
            Mock text response
        """
        # Basic response
        response = f"这是 MockProvider 的模拟响应（调用次数: {self._call_count}）。\n\n"

        # Try to give contextual response based on prompt
        if "总结" in prompt or "summarize" in prompt.lower():
            response += "核心要点：\n1. 这是第一个要点\n2. 这是第二个要点\n3. 这是第三个要点"

        elif "分析" in prompt or "analyze" in prompt.lower():
            response += "分析结果：\n- 优势：模拟数据显示优势明显\n- 风险：需要注意潜在风险\n- 建议：建议采取相应措施"

        elif "评分" in prompt or "score" in prompt.lower():
            response += "评分：85/100\n理由：基于模拟数据的综合评估结果。"

        else:
            response += "实际使用时，这里会显示 LLM 生成的内容。\n当前是测试模式，使用 MockProvider。"

        return response
