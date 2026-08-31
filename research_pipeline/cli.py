from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .codex_runner import CodexRunner
from .config import ConfigError, load_config
from .db import ResearchDB
from .demo import build_demo
from .pipeline import PipelineError, ResearchPipeline
from .scoring import load_watchlist
from .utils import configure_logging, local_now


def _default_date(config: Any) -> str:
    return local_now(str(config.get("project.timezone", "Asia/Shanghai"))).strftime("%Y-%m-%d")


def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="a-share-research", description="A股研报智能筛选系统")
    parser.add_argument("--config", type=Path, help="配置文件路径")
    parser.add_argument("--verbose", action="store_true", help="输出调试日志")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="初始化目录和数据库")
    sub.add_parser("doctor", help="检查 Python、Codex、配置、数据库和写权限")

    ingest = sub.add_parser("ingest", help="只入库并提取 PDF，不调用 Codex")
    ingest.add_argument("--date", dest="run_date")
    ingest.add_argument("--input-dir", type=Path)
    ingest.add_argument("--force", action="store_true")

    run = sub.add_parser("run", help="执行完整研报流水线")
    run.add_argument("--date", dest="run_date")
    run.add_argument("--session", choices=["0900", "2100"], default="0900")
    run.add_argument("--input-dir", type=Path)
    run.add_argument("--force", action="store_true")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--no-deep-dive", action="store_true")
    run.add_argument("--no-qc", action="store_true")

    sub.add_parser("demo", help="生成不调用 Codex 的演示输出")
    sub.add_parser("scheduler-tick", help="按配置时区检查并执行到点任务")
    return parser


def doctor(config: Any, verbose: bool = False) -> int:
    logger = configure_logging(config.path("logs") / "doctor.log", verbose)
    checks: list[dict[str, Any]] = []

    checks.append({"name": "Python", "ok": sys.version_info >= (3, 11), "detail": sys.version.split()[0]})
    for module in ("pymupdf", "yaml", "jsonschema", "jinja2"):
        try:
            __import__(module)
            checks.append({"name": f"Python模块 {module}", "ok": True, "detail": "已安装"})
        except Exception as exc:
            checks.append({"name": f"Python模块 {module}", "ok": False, "detail": str(exc)})

    runner = CodexRunner(config, logger)
    checks.append({"name": "Codex CLI", "ok": runner.available(), "detail": runner.version() or "未安装"})
    checks.append({"name": "Git仓库", "ok": (config.root / ".git").exists(), "detail": str(config.root / ".git")})

    try:
        with ResearchDB(config.path("database")) as db:
            db.conn.execute("SELECT 1").fetchone()
        checks.append({"name": "SQLite", "ok": True, "detail": str(config.path("database"))})
    except Exception as exc:
        checks.append({"name": "SQLite", "ok": False, "detail": str(exc)})

    try:
        test_path = config.path("logs") / ".write-test"
        test_path.write_text("ok", encoding="utf-8")
        test_path.unlink()
        checks.append({"name": "工作区写权限", "ok": True, "detail": str(config.root)})
    except Exception as exc:
        checks.append({"name": "工作区写权限", "ok": False, "detail": str(exc)})

    watchlist = load_watchlist(config.path("watchlist"))
    checks.append({"name": "观察池", "ok": bool(watchlist), "detail": f"{len(watchlist)} 条"})

    print("\nA股研报系统环境检查\n" + "=" * 36)
    for item in checks:
        mark = "✅" if item["ok"] else "❌"
        print(f"{mark} {item['name']}: {item['detail']}")
    failed = [item for item in checks if not item["ok"]]
    if failed:
        print("\n存在未通过项。Codex CLI 缺失时仍可运行 demo 和 --dry-run。")
        return 1
    print("\n全部检查通过。")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        return 2
    logger = configure_logging(config.path("logs") / "pipeline.log", args.verbose)

    try:
        if args.command == "init":
            config.ensure_directories()
            with ResearchDB(config.path("database")):
                pass
            _print_json({"status": "initialized", "root": str(config.root), "database": str(config.path("database"))})
            return 0
        if args.command == "doctor":
            return doctor(config, args.verbose)
        if args.command == "demo":
            output = build_demo(config)
            _print_json({"status": "success", "output_dir": str(output.resolve()), "dashboard": str((output / "dashboard.html").resolve())})
            return 0

        pipeline = ResearchPipeline(config, logger)
        if args.command == "ingest":
            run_date = args.run_date or _default_date(config)
            reports = pipeline.ingest(run_date, args.input_dir, args.force)
            _print_json({"status": "success", "run_date": run_date, "report_count": len(reports), "reports": [{"report_id": r["report_id"], "file_name": r["file_name"], "page_count": r["page_count"], "scanned_pages": r["scanned_pages"], "status": r["extraction_status"]} for r in reports]})
            return 0
        if args.command == "run":
            run_date = args.run_date or _default_date(config)
            result = pipeline.run(
                run_date=run_date,
                session=args.session,
                input_dir=args.input_dir,
                force=args.force,
                dry_run=args.dry_run,
                deep_dive=not args.no_deep_dive,
                run_qc=bool(config.get("pipeline.run_qc", True)) and not args.no_qc,
            )
            _print_json(result)
            return 0 if result.get("status") in {"success", "dry_run", "no_input"} else 1
        if args.command == "scheduler-tick":
            result = pipeline.scheduler_tick()
            _print_json({"status": "success", "runs": result})
            return 0
    except (PipelineError, ConfigError) as exc:
        logger.error(str(exc))
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("已中止。", file=sys.stderr)
        return 130
    except Exception as exc:
        logger.exception("未处理异常")
        print(f"执行失败：{exc}", file=sys.stderr)
        return 1
    return 0
