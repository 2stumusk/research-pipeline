#!/usr/bin/env python3
"""Credential-free architecture smoke checks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def check_config_provider():
    """Verify load_config + normalize_llm_config reports 'codex' provider."""
    from research_pipeline.config import load_config
    from research_pipeline.config_loader import normalize_llm_config

    app_config = load_config()
    llm_config = normalize_llm_config(app_config)

    assert llm_config.get('provider') == 'codex', f"Expected provider 'codex', got {llm_config.get('provider')}"
    return True


def check_pipeline_uses_codex():
    """Verify ResearchPipeline uses CodexRunner, not llm_adapter."""
    import inspect
    from research_pipeline import pipeline

    source = inspect.getsource(pipeline)

    # Check for codex_runner usage
    assert 'codex_runner' in source.lower() or 'CodexRunner' in source, \
        "ResearchPipeline should reference codex_runner/CodexRunner"

    # Check llm_adapter is NOT used
    assert 'llm_adapter' not in source, \
        "ResearchPipeline should not reference llm_adapter"

    return True


def check_stage_config():
    """Verify get_stage_config carries codex base_url and stage defaults offline."""
    from research_pipeline.config_loader import get_stage_config

    mock_config = {
        'provider': 'codex',
        'base_url': 'https://api.codex.example.com/v1',
        'model': 'codex-medium',
        'temperature': 0.7,
        'max_tokens': 4000
    }

    stage_cfg = get_stage_config(mock_config, 'triage')

    assert 'base_url' in stage_cfg, "Stage config should preserve base_url"
    assert stage_cfg['base_url'] == mock_config['base_url'], "base_url should match source"
    assert 'temperature' in stage_cfg, "Stage config should have temperature default"
    assert 'max_tokens' in stage_cfg, "Stage config should have max_tokens default"

    return True


def check_session_validation():
    """Verify validate_session_name accepts valid sessions, rejects path traversal."""
    from research_pipeline.pipeline import validate_session_name

    # Valid session names: 0900, 2100, gui-HHMMSS, gui-HHMMSS-sixlowercasehex
    assert validate_session_name('0900'), "Should accept 0900 session"
    assert validate_session_name('2100'), "Should accept 2100 session"
    assert validate_session_name('gui-153045'), "Should accept gui-HHMMSS session"
    assert validate_session_name('gui-091530-a3f9c1'), "Should accept gui-HHMMSS-hex session"

    # Invalid: path traversal attempts
    assert not validate_session_name('../etc/passwd'), "Should reject parent directory traversal"
    assert not validate_session_name('../../secret'), "Should reject multiple parent traversals"
    assert not validate_session_name('/abs/path'), "Should reject absolute path"
    assert not validate_session_name('sub/../dir'), "Should reject embedded traversal"

    return True


def main():
    """Run all checks."""
    checks = [
        ('Config provider=codex', check_config_provider),
        ('Pipeline uses CodexRunner', check_pipeline_uses_codex),
        ('Stage config offline', check_stage_config),
        ('Session validation', check_session_validation),
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
