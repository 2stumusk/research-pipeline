#!/usr/bin/env python3
"""Simple integration test: Config loading and LLM call."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_config_loading():
    """Test loading configuration."""
    print("\n" + "=" * 60)
    print("Test 1: Configuration Loading")
    print("=" * 60)

    try:
        from research_pipeline.config_loader import load_llm_config, get_stage_config

        # Test loading new format config
        config_path = Path("config/config.v0.2.yaml")
        if not config_path.exists():
            print(f"⚠️  Config file not found: {config_path}")
            print("Skipping this test...")
            return True

        llm_config = load_llm_config(config_path)
        print(f"✅ Loaded LLM config: {llm_config.get('provider')}")

        # Test stage-specific config
        for stage in ["triage", "synthesis", "deep_dive", "qc"]:
            stage_config = get_stage_config(llm_config, stage)
            print(f"   {stage}: temp={stage_config['temperature']}, "
                  f"max_tokens={stage_config['max_tokens']}")

        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_runner_creation():
    """Test creating LLM runner from config."""
    print("\n" + "=" * 60)
    print("Test 2: Runner Creation")
    print("=" * 60)

    try:
        from research_pipeline.llm_runner import create_runner_from_yaml

        config_path = Path("config/config.v0.2.yaml")
        if not config_path.exists():
            print(f"⚠️  Config file not found: {config_path}")
            print("Using fallback config...")
            # Create minimal config for testing
            from research_pipeline.llm_runner import LLMRunner
            runner = LLMRunner(provider="claude")
        else:
            runner = create_runner_from_yaml(config_path, stage="triage")

        print(f"✅ Created runner: {runner.provider_name}")
        print(f"   Model: {runner.provider.get_model_name()}")
        print(f"   Temperature: {runner.provider.temperature}")
        print(f"   Max tokens: {runner.provider.max_tokens}")

        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mock_llm_call():
    """Test mock LLM call (without actually calling API)."""
    print("\n" + "=" * 60)
    print("Test 3: Mock LLM Call Structure")
    print("=" * 60)

    try:
        from research_pipeline.llm_runner import LLMRunner, LLMRunnerError

        # This tests the structure without actual API call
        runner = LLMRunner(provider="claude", api_key="fake_key_for_testing")

        print(f"✅ Runner initialized: {runner.provider_name}")
        print(f"   Provider: {type(runner.provider).__name__}")
        print(f"   Max retries: {runner.max_retries}")

        # We won't actually call run() here to avoid API costs
        print("   (Skipping actual API call to save costs)")

        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "#" * 60)
    print("# Integration Test Suite - Day 2")
    print("#" * 60)

    results = {
        "config_loading": test_config_loading(),
        "runner_creation": test_runner_creation(),
        "mock_llm_call": test_mock_llm_call(),
    }

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())
    print("\n" + ("=" * 60))
    if all_passed:
        print("✅ All tests passed!")
        print("\nNext step: Run 'python tests/test_llm_providers.py' with real API key")
    else:
        print("❌ Some tests failed. Check errors above.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
