from __future__ import annotations

import logging
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from research_pipeline.codex_runner import CodexError, CodexRunner
from research_pipeline.config import load_config
from research_pipeline.utils import read_json


class CodexCommandAndSchemaTests(unittest.TestCase):
    def test_timeout_with_byte_stderr_is_logged_without_type_error(self) -> None:
        cfg = load_config()
        runner = CodexRunner(cfg, logging.getLogger("test-timeout"))
        timeout = subprocess.TimeoutExpired("codex", 1, stderr=b"partial stderr")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(runner, "available", return_value=True), patch(
                "research_pipeline.codex_runner.subprocess.run", side_effect=timeout
            ), self.assertRaisesRegex(CodexError, "执行超时"):
                runner.run_structured(
                    stage="synthesis",
                    prompt="test prompt",
                    schema_path=cfg.root / "schemas" / "digest.schema.json",
                    output_path=root / "out.json",
                    audit_dir=root / "audit",
                    label="timeout-test",
                )
            logged = (root / "audit" / "timeout-test.stderr.log").read_text(encoding="utf-8")
            self.assertIn("partial stderr", logged)
            self.assertIn("执行超时", logged)

    def test_subprocess_environment_is_utf8_safe_and_uses_runtime_pwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_root = Path(tmp)
            environment = CodexRunner._subprocess_environment(runtime_root)
            self.assertNotIn("_", environment)
            self.assertNotIn("OLDPWD", environment)
            self.assertEqual(environment["PWD"], str(runtime_root.resolve()))
            for key, value in environment.items():
                key.encode("utf-8")
                value.encode("utf-8")

    def test_exec_specific_flags_follow_exec_subcommand(self) -> None:
        cfg = load_config()
        runner = CodexRunner(cfg, logging.getLogger("test"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cmd = runner._build_command(
                "triage",
                "test prompt",
                cfg.root / "schemas" / "triage_batch.schema.json",
                root / "out.json",
            )
        exec_index = cmd.index("exec")
        self.assertGreater(cmd.index("--color"), exec_index)
        self.assertGreater(cmd.index("--output-schema"), exec_index)
        self.assertGreater(cmd.index("--output-last-message"), exec_index)
        self.assertGreater(cmd.index("--ignore-user-config"), exec_index)
        self.assertGreater(cmd.index("--ignore-rules"), exec_index)
        self.assertIn("tools.web_search=false", cmd)
        self.assertIn("read-only", cmd)
        self.assertNotIn("danger-full-access", cmd)

    def test_all_json_schemas_are_valid_draft_2020_12(self) -> None:
        cfg = load_config()
        schemas = sorted((cfg.root / "schemas").glob("*.schema.json"))
        self.assertGreaterEqual(len(schemas), 5)
        for schema_path in schemas:
            with self.subTest(schema=schema_path.name):
                Draft202012Validator.check_schema(read_json(schema_path))


if __name__ == "__main__":
    unittest.main()
