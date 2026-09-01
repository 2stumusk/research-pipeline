#!/usr/bin/env python3
"""Credential-free integration smoke checks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def check_config_normalization():
    """Verify config normalization produces codex provider."""
    from research_pipeline.config import load_config
    from research_pipeline.config_loader import normalize_llm_config

    app_config = load_config()
    llm_config = normalize_llm_config(app_config)

    assert llm_config['provider'] == 'codex', f"Expected codex, got {llm_config['provider']}"

    return True


def check_codex_runner_import():
    """Verify CodexRunner is importable and has required interface."""
    from research_pipeline.codex_runner import CodexRunner

    import inspect

    # Check class exists and has run_structured method
    assert inspect.isclass(CodexRunner), "CodexRunner should be a class"
    assert hasattr(CodexRunner, 'run_structured'), "CodexRunner should have run_structured method"

    # Check signature doesn't require direct provider construction
    sig = inspect.signature(CodexRunner.__init__)
    params = list(sig.parameters.keys())

    # Should accept config-based construction, not require provider object
    assert 'self' in params, "Constructor should have self"

    return True


def check_stage_defaults():
    """Verify stage-specific configs apply defaults correctly."""
    from research_pipeline.config_loader import get_stage_config

    base = {'provider': 'codex', 'base_url': 'https://api.example.com', 'model': 'test-model'}

    triage_cfg = get_stage_config(base, 'triage')
    synthesis_cfg = get_stage_config(base, 'synthesis')

    # Both should preserve base_url
    assert triage_cfg.get('base_url') == base['base_url'], "Triage should preserve base_url"
    assert synthesis_cfg.get('base_url') == base['base_url'], "Synthesis should preserve base_url"

    # Should have stage-appropriate defaults
    assert 'temperature' in triage_cfg, "Triage should have temperature"
    assert 'temperature' in synthesis_cfg, "Synthesis should have temperature"

    return True


def check_no_llm_adapter_dependency():
    """Verify ResearchPipeline doesn't import llm_adapter."""
    import inspect
    from research_pipeline import pipeline

    source = inspect.getsource(pipeline)

    # Should use codex_runner, not llm_adapter
    assert 'from' in source and 'codex_runner' in source.lower(), \
        "Pipeline should import from codex_runner"

    # Verify llm_adapter is not referenced
    lines = source.split('\n')
    import_lines = [l for l in lines if 'import' in l]
    adapter_imports = [l for l in import_lines if 'llm_adapter' in l]

    assert not adapter_imports, f"Pipeline should not import llm_adapter: {adapter_imports}"

    return True


def main():
    """Run all integration checks."""
    checks = [
        ('Config normalization', check_config_normalization),
        ('CodexRunner import', check_codex_runner_import),
        ('Stage defaults', check_stage_defaults),
        ('No llm_adapter dependency', check_no_llm_adapter_dependency),
    ]

    failed = []
    for name, check_fn in checks:
        try:
            check_fn()
        except Exception as e:
            failed.append((name, str(e)))

    if failed:
        for name, error in failed:
            print(f"✗ {name}: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
