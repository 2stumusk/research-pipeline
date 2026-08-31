from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .config import AppConfig
from .utils import atomic_write_text, read_json, write_json


class CodexError(RuntimeError):
    pass


class CodexRunner:
    def __init__(self, config: AppConfig, logger: Any) -> None:
        self.config = config
        self.logger = logger
        self.binary = str(config.get("codex.binary", "codex"))

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    def version(self) -> str:
        if not self.available():
            return ""
        try:
            result = subprocess.run(
                [self.binary, "--version"], capture_output=True, text=True, timeout=20, check=False
            )
            return (result.stdout or result.stderr).strip()
        except Exception:
            return ""

    @staticmethod
    def _subprocess_environment(working_root: Path) -> dict[str, str]:
        environment: dict[str, str] = {}
        for key, value in os.environ.items():
            try:
                key.encode("utf-8")
                value.encode("utf-8")
            except UnicodeEncodeError:
                continue
            environment[key] = value
        for key in ("_", "OLDPWD", "VIRTUAL_ENV", "PYTHONHOME", "PYTHONPATH"):
            environment.pop(key, None)
        environment["PWD"] = str(working_root.resolve())
        environment.setdefault("LANG", "en_US.UTF-8")
        return environment

    def _build_command(
        self,
        stage: str,
        prompt: str,
        schema_path: Path,
        output_path: Path,
        working_root: Path | None = None,
    ) -> list[str]:
        working_root = (working_root or self.config.root).resolve()
        sandbox = str(self.config.get("codex.sandbox", "read-only"))
        approval = str(self.config.get("codex.ask_for_approval", "never"))
        model = str(self.config.get(f"codex.models.{stage}", "") or "").strip()
        effort = str(self.config.get(f"codex.reasoning_effort.{stage}", "medium"))
        verbosity = str(self.config.get(f"codex.verbosity.{stage}", "low"))

        cmd = [
            self.binary,
            "--cd",
            str(working_root),
            "--ask-for-approval",
            approval,
            "--sandbox",
            sandbox,
        ]
        if model:
            cmd.extend(["--model", model])
        cmd.extend(["--config", f'model_reasoning_effort="{effort}"'])
        cmd.extend(["--config", f'model_verbosity="{verbosity}"'])
        if not bool(self.config.get("codex.web_search", False)):
            cmd.extend(["--config", "tools.web_search=false"])

        # Flags below are specific to `codex exec` in the current CLI reference.
        cmd.extend(["exec", "--color", "never", "--ephemeral"])
        if bool(self.config.get("codex.isolate_user_config", True)):
            cmd.append("--ignore-user-config")
        if bool(self.config.get("codex.ignore_rules", True)):
            cmd.append("--ignore-rules")
        if not (working_root / ".git").exists():
            cmd.append("--skip-git-repo-check")
        cmd.extend(
            [
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(output_path),
                prompt,
            ]
        )
        return cmd

    def _build_runtime_workspace(
        self,
        prompt: str,
        schema_path: Path,
        runtime_root: Path,
    ) -> tuple[str, Path, Path]:
        """Copy only declared inputs into an ASCII temporary workspace.

        This keeps Codex tool execution independent from non-ASCII project paths and prevents
        the model from reading files that were not explicitly listed by the pipeline.
        """
        for relative in (Path("AGENTS.md"), Path(".agents"), Path(".codex")):
            source = self.config.root / relative
            destination = runtime_root / relative
            if source.is_dir():
                shutil.copytree(source, destination, dirs_exist_ok=True)
            elif source.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

        inputs_dir = runtime_root / "inputs"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        copied: dict[Path, Path] = {}

        def resolve_file(raw: str) -> Path | None:
            candidate = Path(raw).expanduser()
            if not candidate.is_absolute():
                candidate = self.config.root / candidate
            try:
                candidate = candidate.resolve()
            except OSError:
                return None
            return candidate if candidate.is_file() else None

        def is_path_key(key: str) -> bool:
            return key == "path" or key.endswith("_path") or key.endswith("_paths") or key in {
                "output_files",
                "source_texts_for_spot_check",
            }

        def rewrite_value(value: Any, key: str = "") -> Any:
            if isinstance(value, dict):
                return {item_key: rewrite_value(item_value, item_key) for item_key, item_value in value.items()}
            if isinstance(value, list):
                return [rewrite_value(item, key) for item in value]
            if isinstance(value, str) and is_path_key(key):
                source = resolve_file(value)
                if source is not None:
                    return str(copy_input(source).relative_to(runtime_root))
            return value

        def copy_input(source: Path) -> Path:
            source = source.resolve()
            if source in copied:
                return copied[source]
            suffix = "".join(source.suffixes[-2:]) if source.name.endswith(".schema.json") else source.suffix
            destination = inputs_dir / f"input_{len(copied) + 1:04d}{suffix}"
            copied[source] = destination
            if source.suffix.lower() == ".json":
                try:
                    with source.open("r", encoding="utf-8") as handle:
                        payload = json.load(handle)
                    atomic_write_text(
                        destination,
                        json.dumps(rewrite_value(payload), ensure_ascii=False, indent=2) + "\n",
                    )
                    return destination
                except (OSError, UnicodeError, json.JSONDecodeError):
                    pass
            shutil.copy2(source, destination)
            return destination

        path_line = re.compile(r"(?m)^(输入清单|输入文件|观察池)：\s*(.+?)\s*$")

        def replace_path_line(match: re.Match[str]) -> str:
            raw = match.group(2).strip()
            source = resolve_file(raw)
            if source is None:
                return match.group(0)
            destination = copy_input(source)
            return f"{match.group(1)}：{destination.relative_to(runtime_root)}"

        runtime_prompt = path_line.sub(replace_path_line, prompt)
        runtime_schema = runtime_root / "schemas" / schema_path.name
        runtime_schema.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(schema_path, runtime_schema)
        runtime_output = runtime_root / "output" / "result.json"
        runtime_output.parent.mkdir(parents=True, exist_ok=True)
        return runtime_prompt, runtime_schema, runtime_output

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
        if not self.available():
            raise CodexError(
                "未检测到 Codex CLI。请先运行官方安装命令并完成登录，再执行正式分析。"
            )
        schema = read_json(schema_path)
        if not isinstance(schema, dict):
            raise CodexError(f"无效 JSON Schema：{schema_path}")
        validator = Draft202012Validator(schema)

        audit_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = audit_dir / f"{label}.prompt.md"
        runtime_prompt_path = audit_dir / f"{label}.runtime.prompt.md"
        stdout_path = audit_dir / f"{label}.stdout.log"
        stderr_path = audit_dir / f"{label}.stderr.log"
        atomic_write_text(prompt_path, prompt)

        retries = int(self.config.get("codex.retries", 2))
        timeout = int(self.config.get("codex.timeout_seconds", 1800))
        last_error = ""

        isolate_runtime = bool(self.config.get("codex.isolate_runtime_workspace", True))
        with tempfile.TemporaryDirectory(prefix="a-share-codex-") as temp_dir:
            runtime_root = Path(temp_dir)
            if isolate_runtime:
                runtime_prompt, runtime_schema, runtime_output = self._build_runtime_workspace(
                    prompt, schema_path, runtime_root
                )
                atomic_write_text(runtime_prompt_path, runtime_prompt)
            else:
                runtime_root = self.config.root
                runtime_prompt = prompt
                runtime_schema = schema_path
                runtime_output = output_path

            for attempt in range(1, retries + 2):
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.unlink(missing_ok=True)
                runtime_output.unlink(missing_ok=True)
                cmd = self._build_command(
                    stage,
                    runtime_prompt,
                    runtime_schema,
                    runtime_output,
                    working_root=runtime_root,
                )
                self.logger.info("Codex %s：第 %s 次执行", label, attempt)
                started = time.monotonic()
                try:
                    result = subprocess.run(
                        cmd,
                        cwd=runtime_root,
                        env=self._subprocess_environment(runtime_root),
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        check=False,
                    )
                except subprocess.TimeoutExpired as exc:
                    last_error = f"执行超时（{timeout}s）"
                    timeout_stderr = exc.stderr or ""
                    if isinstance(timeout_stderr, bytes):
                        timeout_stderr = timeout_stderr.decode("utf-8", errors="replace")
                    atomic_write_text(stderr_path, timeout_stderr + "\n" + last_error)
                    continue
                except OSError as exc:
                    raise CodexError(f"无法启动 Codex：{exc}") from exc

                elapsed = time.monotonic() - started
                atomic_write_text(stdout_path, result.stdout or "")
                atomic_write_text(stderr_path, result.stderr or "")
                if result.returncode != 0:
                    last_error = f"Codex 返回码 {result.returncode}；耗时 {elapsed:.1f}s"
                    self.logger.warning("%s：%s", label, last_error)
                    continue
                if not runtime_output.exists():
                    last_error = "Codex 未生成结构化输出文件"
                    continue
                try:
                    with runtime_output.open("r", encoding="utf-8") as handle:
                        data = json.load(handle)
                except Exception as exc:
                    last_error = f"输出不是有效 JSON：{exc}"
                    continue

                errors = sorted(validator.iter_errors(data), key=lambda err: list(err.path))
                if errors:
                    preview = "; ".join(
                        f"{'/'.join(map(str, err.path)) or '<root>'}: {err.message}" for err in errors[:5]
                    )
                    last_error = f"JSON Schema 校验失败：{preview}"
                    continue
                write_json(output_path, data)
                self.logger.info("Codex %s 完成，耗时 %.1fs", label, elapsed)
                return data

        raise CodexError(f"{label} 失败：{last_error or '未知错误'}")
