#!/usr/bin/env python3
"""Test script for new LLM providers.

Usage:
    # Test Claude
    export ANTHROPIC_API_KEY=your_key_here
    python test_llm_providers.py --provider claude

    # Test OpenAI
    export OPENAI_API_KEY=your_key_here
    python test_llm_providers.py --provider openai

    # Test both
    python test_llm_providers.py --provider all
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research_pipeline.llm_runner import LLMRunner, LLMRunnerError


def test_basic_generation(provider: str):
    """Test basic text generation."""
    print(f"\n{'='*60}")
    print(f"Testing {provider.upper()} - Basic Generation")
    print('='*60)

    try:
        runner = LLMRunner(provider=provider)

        prompt = "请用一句话总结：人工智能在投资研究中的应用前景。"

        print(f"Prompt: {prompt}")
        print("\nCalling LLM...")

        response = runner.run(prompt=prompt)

        print(f"\n✅ Success!")
        print(f"Model: {response.model}")
        print(f"Usage: {response.usage}")
        print(f"\nResponse:\n{response.content}")

        return True

    except LLMRunnerError as e:
        print(f"\n❌ Failed: {e}")
        return False


def test_structured_output(provider: str):
    """Test structured JSON output."""
    print(f"\n{'='*60}")
    print(f"Testing {provider.upper()} - Structured Output")
    print('='*60)

    try:
        runner = LLMRunner(provider=provider)

        # Define JSON schema
        schema = {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "ticker": {"type": "string"},
                "sector": {"type": "string"},
                "investment_rating": {
                    "type": "string",
                    "enum": ["买入", "增持", "中性", "减持", "卖出"]
                },
                "target_price": {"type": "number"},
                "key_points": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["company", "ticker", "investment_rating", "key_points"]
        }

        prompt = """
        分析以下研报摘要，提取结构化信息：

        中微公司（688012.SH）是国内领先的半导体设备供应商，主营刻蚀设备和MOCVD设备。
        公司2026年Q2业绩超预期，营收同比增长45%，毛利率提升至48%。
        主要看点：
        1. 先进制程刻蚀设备获得多家晶圆厂订单
        2. 长鑫存储扩产带来增量需求
        3. 毛利率持续改善

        给予"买入"评级，目标价280元。
        """

        print("Schema defined:")
        print(json.dumps(schema, indent=2, ensure_ascii=False))
        print(f"\nPrompt: {prompt[:100]}...")
        print("\nCalling LLM with structured output...")

        response = runner.run(
            prompt=prompt,
            json_schema=schema
        )

        print(f"\n✅ Success!")
        print(f"Model: {response.model}")
        print(f"Usage: {response.usage}")
        print(f"\nStructured Output:")
        print(json.dumps(response.structured_output, indent=2, ensure_ascii=False))

        return True

    except LLMRunnerError as e:
        print(f"\n❌ Failed: {e}")
        return False


def test_retry_logic(provider: str):
    """Test retry logic with invalid API key."""
    print(f"\n{'='*60}")
    print(f"Testing {provider.upper()} - Retry Logic")
    print('='*60)

    try:
        # Create runner with invalid API key
        runner = LLMRunner(
            provider=provider,
            api_key="invalid_key_for_testing",
            max_retries=2
        )

        print("Attempting to call with invalid API key...")
        print("Expected: Should fail immediately without retrying")

        response = runner.run(prompt="Hello")

        print(f"\n❌ Unexpected success: {response}")
        return False

    except LLMRunnerError as e:
        if "api key" in str(e).lower() or "authentication" in str(e).lower():
            print(f"\n✅ Correctly detected auth error: {e}")
            return True
        else:
            print(f"\n⚠️  Failed with unexpected error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Test LLM providers")
    parser.add_argument(
        "--provider",
        choices=["claude", "openai", "all"],
        default="claude",
        help="Provider to test"
    )
    args = parser.parse_args()

    providers = ["claude", "openai"] if args.provider == "all" else [args.provider]

    results = {}

    for provider in providers:
        print(f"\n\n{'#'*60}")
        print(f"# Testing Provider: {provider.upper()}")
        print(f"{'#'*60}")

        provider_results = {
            "basic_generation": test_basic_generation(provider),
            "structured_output": test_structured_output(provider),
            "retry_logic": test_retry_logic(provider),
        }

        results[provider] = provider_results

    # Print summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print('='*60)

    for provider, tests in results.items():
        print(f"\n{provider.upper()}:")
        for test_name, passed in tests.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test_name}: {status}")

    # Exit code
    all_passed = all(
        all(tests.values())
        for tests in results.values()
    )

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
