from __future__ import annotations

import json
import logging
import re
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .codex_runner import CodexError, CodexRunner
from .config import AppConfig
from .db import ResearchDB
from .pdf_ingest import discover_pdfs, extract_pdf
from .render import (
    render_clusters,
    render_dashboard,
    render_deep_dive_markdown,
    render_index_csv,
    render_one_pager,
    render_qc,
    render_risk_catalyst,
    render_top10,
    update_latest_link,
    write_machine_outputs,
)
from .scoring import (
    apply_cluster_duplicate_penalties,
    fallback_card,
    load_watchlist,
    normalize_and_score_card,
)
from .utils import (
    atomic_write_text,
    local_now,
    process_lock,
    safe_relative,
    sha256_file,
    slugify,
    utc_now_iso,
    write_json,
)


class PipelineError(RuntimeError):
    pass


def validate_session_name(session: str) -> bool:
    """Validate session name: 0900, 2100, gui-HHMMSS, or gui-HHMMSS-<6 lowercase hex>.

    Rejects path delimiters, traversal, and invalid time fields.

    Args:
        session: Session identifier string

    Returns:
        True if valid, False otherwise
    """
    if not session or len(session) > 64:
        return False
    # Reject path-like patterns
    if "/" in session or "\\" in session or ".." in session:
        return False
    # Accept standard times
    if session in {"0900", "2100"}:
        return True
    # Accept gui-HHMMSS or gui-HHMMSS-<6 lowercase hex>
    if re.match(r'^gui-\d{6}$', session):
        # Validate time fields: HH in 00-23, MM/SS in 00-59
        time_part = session[4:]
        hh, mm, ss = int(time_part[0:2]), int(time_part[2:4]), int(time_part[4:6])
        return 0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59
    if re.match(r'^gui-\d{6}-[a-f0-9]{6}$', session):
        time_part = session[4:10]
        hh, mm, ss = int(time_part[0:2]), int(time_part[2:4]), int(time_part[4:6])
        return 0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59
    # Accept safe alphanumeric
    if re.match(r'^[a-zA-Z0-9_-]+$', session):
        return True
    return False


def _validate_run_date(run_date: str) -> str:
    try:
        parsed = datetime.strptime(run_date, "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise PipelineError("date 必须是真实的 YYYY-MM-DD 日期") from exc
    if parsed.strftime("%Y-%m-%d") != run_date:
        raise PipelineError("date 必须是零补齐的 YYYY-MM-DD 日期")
    return run_date


def _render_prompt(template: Path, replacements: dict[str, str]) -> str:
    text = template.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _chunks_by_size(items: list[dict[str, Any]], max_reports: int, max_chars: int) -> list[list[dict[str, Any]]]:
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0
    for item in items:
        excerpt_path = Path(item["triage_excerpt_path"])
        try:
            size = len(excerpt_path.read_text(encoding="utf-8"))
        except OSError:
            size = 0
        if current and (len(current) >= max_reports or current_chars + size > max_chars):
            batches.append(current)
            current = []
            current_chars = 0
        current.append(item)
        current_chars += size
    if current:
        batches.append(current)
    return batches


def _find_cluster_for_report(clusters: list[dict[str, Any]], report_id: str) -> dict[str, Any] | None:
    for cluster in clusters:
        if report_id in (cluster.get("report_ids", []) or []):
            return cluster
    return None


def _fallback_clusters(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for card in cards:
        company = ""
        ticker = ""
        if card.get("companies"):
            company = card["companies"][0].get("name", "")
            ticker = card["companies"][0].get("ticker", "")
        if ticker or company:
            key = f"company::{ticker or company}::{card.get('report_date','')}::{card.get('report_type','')}"
        else:
            key = f"single::{card.get('report_id')}"
        groups.setdefault(key, []).append(card)

    clusters: list[dict[str, Any]] = []
    for index, group in enumerate(groups.values(), 1):
        best = max(group, key=lambda c: c.get("importance_score", 0))
        company_names = []
        for card in group:
            company_names.extend([x.get("name", "") for x in card.get("companies", []) if x.get("name")])
        clusters.append(
            {
                "cluster_id": f"fallback_{index:03d}",
                "event_title": best.get("event_title") or best.get("title", ""),
                "event_date": best.get("report_date", ""),
                "primary_theme": (best.get("themes") or [best.get("primary_industry", "未分类")])[0],
                "companies": sorted(set(company_names)),
                "report_ids": [card["report_id"] for card in group],
                "consensus_points": [card.get("core_conclusion", "") for card in group if card.get("core_conclusion")][:3],
                "disagreements": [],
                "genuinely_new_information": [
                    item.get("claim", "")
                    for card in group
                    for item in (card.get("new_information", []) or [])[:2]
                    if item.get("claim")
                ][:5],
                "best_report_id": best["report_id"],
                "best_report_reason": "按重要性和置信度确定的本地兜底结果；尚未完成语义聚类。",
                "a_share_implications": [
                    f"{m.get('company','')}（{m.get('ticker','')}）：{m.get('logic','')}"
                    for m in (best.get("a_share_mapping", []) or [])[:4]
                ],
                "risk_signals": [x.get("risk", "") for x in (best.get("risks", []) or [])[:4]],
                "catalyst_signals": [x.get("event", "") for x in (best.get("catalysts", []) or [])[:4]],
                "cluster_importance": int(best.get("importance_score", 0)),
                "cluster_direction": int(best.get("direction_score", 0)),
                "confidence": int(best.get("confidence_score", 0)),
            }
        )
    return clusters


def _sanitize_clusters(raw: list[dict[str, Any]], cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid_ids = {card["report_id"] for card in cards}
    used: set[str] = set()
    clean: list[dict[str, Any]] = []
    for index, cluster in enumerate(raw, 1):
        ids = []
        for report_id in cluster.get("report_ids", []) or []:
            if report_id in valid_ids and report_id not in used:
                ids.append(report_id)
                used.add(report_id)
        if not ids:
            continue
        cluster = dict(cluster)
        cluster["cluster_id"] = str(cluster.get("cluster_id") or f"cluster_{index:03d}")
        cluster["report_ids"] = ids
        if cluster.get("best_report_id") not in ids:
            cluster["best_report_id"] = ids[0]
        clean.append(cluster)
    for report_id in sorted(valid_ids - used):
        card = next(card for card in cards if card["report_id"] == report_id)
        clean.extend(_fallback_clusters([card]))
        clean[-1]["cluster_id"] = f"single_{len(clean):03d}"
    return clean


def _is_earnings_estimate(metric: str) -> bool:
    normalized = metric.strip().lower()
    excluded = (
        "target price",
        "price target",
        "目标价",
        "估值",
        "市盈率",
        "市净率",
        "市销率",
        "multiple",
        "wacc",
        "terminal value",
    )
    included = (
        "eps",
        "revenue",
        "sales",
        "profit",
        "income",
        "ebit",
        "ebitda",
        "margin",
        "fcf",
        "cash flow",
        "收入",
        "营收",
        "销售额",
        "利润",
        "净利",
        "毛利",
        "利润率",
        "现金流",
    )
    return not any(token in normalized for token in excluded) and any(
        token in normalized for token in included
    )


def _format_estimate_change(item: dict[str, Any]) -> str:
    metric = str(item.get("metric", ""))
    unit = str(item.get("unit", "")).strip()
    old_value = item.get("old_value")
    new_value = item.get("new_value")
    change = item.get("change_pct")
    is_margin = "margin" in metric.lower() or "率" in metric

    if is_margin and isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
        point_change = new_value - old_value
        relative = f"（相对{change:+.1f}%）" if isinstance(change, (int, float)) else ""
        return f"{old_value:g}% → {new_value:g}%, {point_change:+g}个百分点{relative}"
    if old_value is not None and new_value is not None:
        relative = f"（{change:+.1f}%）" if isinstance(change, (int, float)) else ""
        return f"{old_value} → {new_value}{(' ' + unit) if unit else ''}{relative}"
    if isinstance(change, (int, float)):
        return f"{change:+.1f}%"
    return f"{old_value} → {new_value}{(' ' + unit) if unit else ''}"


def _explicit_next_7d_catalysts(
    cards: list[dict[str, Any]], run_date: str
) -> list[dict[str, Any]]:
    try:
        base = datetime.strptime(run_date, "%Y-%m-%d")
    except (TypeError, ValueError):
        return []
    start = base + timedelta(days=1)
    end = base + timedelta(days=7)
    selected: list[dict[str, Any]] = []
    for card in cards:
        for item in card.get("catalysts", []) or []:
            raw = str(item.get("date_or_window", ""))
            candidates = re.findall(r"(20\d{2})[-/\u5e74](\d{1,2})[-/\u6708](\d{1,2})(?:\u65e5)?", raw)
            if not candidates:
                candidates = [
                    (str(base.year), month, day)
                    for month, day in re.findall(r"(\d{1,2})\u6708(\d{1,2})\u65e5", raw)
                ]
            for year, month, day in candidates:
                try:
                    event_date = datetime(int(year), int(month), int(day))
                except ValueError:
                    continue
                if start <= event_date <= end:
                    selected.append(item)
                    break
            if len(selected) >= 12:
                return selected
    return selected


def _fallback_digest(
    cards: list[dict[str, Any]], clusters: list[dict[str, Any]], run_date: str = ""
) -> dict[str, Any]:
    ordered = sorted(cards, key=lambda c: (c.get("priority_score", 0), c.get("confidence_score", 0)), reverse=True)
    top_changes = []
    for card in ordered[:7]:
        top_changes.append(
            {
                "title": card.get("title", ""),
                "why_it_matters": card.get("core_conclusion", ""),
                "affected_assets": [
                    x.get("name") or x.get("ticker") for x in card.get("companies", []) if x.get("name") or x.get("ticker")
                ],
                "direction": int(card.get("direction_score", 0)),
                "confidence": int(card.get("confidence_score", 0)),
                "report_ids": [card["report_id"]],
            }
        )
    negative_cards = [c for c in ordered if c.get("direction_score", 0) <= -1]
    risk_alerts = [
        {
            "title": card.get("title", ""),
            "why_it_matters": (card.get("risks") or [{"risk": card.get("core_conclusion", "")}])[0].get("risk", ""),
            "affected_assets": [x.get("name") or x.get("ticker") for x in card.get("companies", [])],
            "direction": int(card.get("direction_score", 0)),
            "confidence": int(card.get("confidence_score", 0)),
            "report_ids": [card["report_id"]],
        }
        for card in negative_cards[:7]
    ]
    upgrades = []
    downgrades = []
    for card in cards:
        company = card.get("companies", [{}])[0] if card.get("companies") else {}
        for item in card.get("estimate_changes", []) or []:
            change = item.get("change_pct")
            if not _is_earnings_estimate(str(item.get("metric", ""))):
                continue
            if isinstance(change, (int, float)) and abs(change) < 0.05:
                continue
            row = {
                "company": company.get("name", ""),
                "ticker": company.get("ticker", ""),
                "metric": item.get("metric", ""),
                "period": item.get("period", ""),
                "change": _format_estimate_change(item),
                "report_id": card["report_id"],
            }
            if isinstance(change, (int, float)) and change > 0:
                upgrades.append(row)
            elif isinstance(change, (int, float)) and change < 0:
                downgrades.append(row)
    disagreements = [
        f"{cluster.get('event_title','')}：{item.get('topic','')}"
        for cluster in clusters
        for item in (cluster.get("disagreements", []) or [])
    ][:5]
    watch_items = []
    for card in ordered:
        if card.get("watchlist_matches"):
            watch_items.append(f"{card.get('title','')}：{card.get('core_conclusion','')}")
        if len(watch_items) >= 7:
            break
    catalysts = _explicit_next_7d_catalysts(ordered, run_date)
    return {
        "executive_view": "本次综合摘要由本地兜底逻辑生成；建议在 LLM 可用后重新运行，以获得跨报告共识与分歧分析。",
        "top_changes": top_changes,
        "risk_alerts": risk_alerts,
        "earnings_upgrades": upgrades[:20],
        "earnings_downgrades": downgrades[:20],
        "biggest_disagreements": disagreements,
        "watchlist_relevance": watch_items,
        "next_7d_catalysts": catalysts,
        "reading_order": [card["report_id"] for card in ordered[:15]],
        "data_gaps": ["综合摘要未由 LLM 语义合成，机构分歧与事件去重可能不完整。"],
    }


def _build_digest_input(
    run_meta: dict[str, Any],
    cards: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    deep_dives: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Keep synthesis evidence while excluding fields already expanded elsewhere.

    Full cards, clusters and deep dives are still written to the machine outputs.  The
    synthesis model only needs the fields below; sending every nested analytical field
    can exceed practical CLI latency on large daily batches.
    """

    card_fields = (
        "report_id",
        "title",
        "institution",
        "report_date",
        "report_type",
        "companies",
        "primary_industry",
        "themes",
        "rating",
        "target_price",
        "core_conclusion",
        "new_information",
        "key_metrics",
        "estimate_changes",
        "a_share_mapping",
        "risks",
        "catalysts",
        "evidence_gaps",
        "watchlist_matches",
        "priority_score",
        "importance_score",
        "direction_score",
        "confidence_score",
        "analysis_status",
        "extraction_status",
        "scanned_pages",
        "source_pages_used",
        "event_cluster_id",
        "event_title",
        "recommended_action",
        "delta_from_prior",
    )
    deep_fields = (
        "report_id",
        "one_sentence_conclusion",
        "genuinely_new_information",
        "changes_vs_prior",
        "earnings_impact",
        "valuation_impact",
        "a_share_mapping",
        "catalyst_timeline",
        "risks_and_disconfirming_evidence",
        "final_judgment",
        "confidence",
    )

    return {
        "run": run_meta,
        "cards": [{key: card[key] for key in card_fields if key in card} for card in cards],
        "clusters": clusters,
        "deep_dives": {
            report_id: {key: deep[key] for key in deep_fields if key in deep}
            for report_id, deep in deep_dives.items()
        },
    }


class ResearchPipeline:
    def __init__(self, config: AppConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self.runner = CodexRunner(config, logger)
        self.watchlist = load_watchlist(config.path("watchlist"))


    def _input_dir(self, run_date: str, input_dir: Path | None = None) -> Path:
        return input_dir.resolve() if input_dir else self.config.path("inbox") / run_date

    def _archive_sources(self, run_date: str, source_dir: Path, pdfs: list[Path]) -> list[str]:
        """Copy successfully processed inputs into the archive without deleting originals."""
        archive_root = self.config.path("archive") / run_date
        archived: list[str] = []
        for pdf in pdfs:
            try:
                relative = pdf.relative_to(source_dir)
            except ValueError:
                relative = Path(pdf.name)
            destination = archive_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.resolve() == pdf.resolve():
                continue

            source_hash = sha256_file(pdf)
            if destination.exists():
                if sha256_file(destination) == source_hash:
                    archived.append(str(destination.resolve()))
                    continue
                destination = destination.with_name(
                    f"{destination.stem}-{source_hash[:8]}{destination.suffix}"
                )
                counter = 2
                while destination.exists() and sha256_file(destination) != source_hash:
                    destination = destination.with_name(
                        f"{destination.stem}-{counter}{destination.suffix}"
                    )
                    counter += 1
                if destination.exists():
                    archived.append(str(destination.resolve()))
                    continue
            shutil.copy2(pdf, destination)
            archived.append(str(destination.resolve()))
        return archived

    def ingest(self, run_date: str, input_dir: Path | None = None, force: bool = False) -> list[dict[str, Any]]:
        _validate_run_date(run_date)
        source_dir = self._input_dir(run_date, input_dir)
        source_dir.mkdir(parents=True, exist_ok=True)
        pdfs = discover_pdfs(source_dir)
        reports: dict[str, dict[str, Any]] = {}
        with ResearchDB(self.config.path("database")) as db:
            for index, pdf in enumerate(pdfs, 1):
                self.logger.info("提取 PDF %s/%s：%s", index, len(pdfs), pdf.name)
                metadata = extract_pdf(pdf, self.config, force=force)
                db.upsert_report(metadata)
                reports[metadata["report_id"]] = metadata
        return list(reports.values())

    def run(
        self,
        *,
        run_date: str,
        session: str,
        input_dir: Path | None = None,
        force: bool = False,
        dry_run: bool = False,
        deep_dive: bool = True,
        run_qc: bool = True,
    ) -> dict[str, Any]:
        _validate_run_date(run_date)
        # Validate session
        if not validate_session_name(session):
            raise PipelineError("session 格式无效：必须是 0900/2100、gui-HHMMSS、gui-HHMMSS-<hex> 或安全的字母数字串")
        if not dry_run and not self.runner.available():
            raise PipelineError("LLM provider 未配置或不可用；请设置 API Key（ANTHROPIC_API_KEY 或 OPENAI_API_KEY），或使用 --dry-run。")

        output_dir = self.config.path("outputs") / f"{run_date}-{session}"
        output_dir.mkdir(parents=True, exist_ok=True)
        work_dir = output_dir / "machine" / "work"
        work_dir.mkdir(parents=True, exist_ok=True)
        run_id = f"{run_date.replace('-','')}-{session}-{uuid.uuid4().hex[:8]}"
        run_meta = {
            "run_id": run_id,
            "run_date": run_date,
            "session": session,
            "started_at": utc_now_iso(),
            "source_dir": str(self._input_dir(run_date, input_dir)),
            "output_dir": str(output_dir.resolve()),
            "dry_run": dry_run,
        }
        errors: list[dict[str, Any]] = []
        lock_path = self.config.path("database").parent / "pipeline.lock"

        with process_lock(lock_path), ResearchDB(self.config.path("database")) as db:
            db.create_run(run_id, run_date, session, str(output_dir.resolve()))
            try:
                source_dir = self._input_dir(run_date, input_dir)
                source_dir.mkdir(parents=True, exist_ok=True)
                pdfs = discover_pdfs(source_dir)
                if not pdfs:
                    db.finish_run(run_id, "no_input", [{"stage": "ingest", "message": f"目录中没有 PDF：{source_dir}"}])
                    return {"status": "no_input", **run_meta, "message": f"目录中没有 PDF：{source_dir}"}

                reports_by_id: dict[str, dict[str, Any]] = {}
                for index, pdf in enumerate(pdfs, 1):
                    try:
                        self.logger.info("入库 %s/%s：%s", index, len(pdfs), pdf.name)
                        metadata = extract_pdf(pdf, self.config, force=force)
                        db.upsert_report(metadata)
                        reports_by_id[metadata["report_id"]] = metadata
                        if metadata.get("extraction_status") != "success":
                            errors.append(
                                {
                                    "stage": "extract",
                                    "severity": "warning",
                                    "report_id": metadata["report_id"],
                                    "file": str(pdf),
                                    "message": metadata.get("extraction_error") or "PDF 文本提取失败",
                                }
                            )
                    except Exception as exc:
                        errors.append({"stage": "ingest", "file": str(pdf), "message": str(exc)})
                        self.logger.exception("PDF 入库失败：%s", pdf)

                reports = list(reports_by_id.values())
                if not reports:
                    raise PipelineError("所有 PDF 均入库失败")
                for report in reports:
                    db.add_run_report(run_id, report["report_id"], report.get("extraction_status", "ingested"))

                cards_by_id: dict[str, dict[str, Any]] = {}
                pending: list[dict[str, Any]] = []
                for report in reports:
                    existing = db.get_card(report["report_id"])
                    reuse = bool(self.config.get("pipeline.reuse_existing_cards", True)) and not force
                    if existing and reuse:
                        card = normalize_and_score_card(existing, report, self.config, self.watchlist)
                        cards_by_id[report["report_id"]] = card
                        if card.get("analysis_status") == "fallback":
                            errors.append(
                                {
                                    "stage": "triage",
                                    "severity": "warning",
                                    "report_id": report["report_id"],
                                    "message": (card.get("evidence_gaps") or ["复用的降级卡仍未完成有效分析"])[0],
                                }
                            )
                    elif report.get("extraction_status") != "success" or int(report.get("text_chars", 0)) < 200:
                        reason = report.get("extraction_error") or "可提取文本过少，可能是扫描版 PDF"
                        card = normalize_and_score_card(fallback_card(report, reason), report, self.config, self.watchlist)
                        cards_by_id[report["report_id"]] = card
                        db.store_card(report["report_id"], card)
                        if report.get("extraction_status") == "success":
                            errors.append(
                                {
                                    "stage": "triage",
                                    "severity": "warning",
                                    "report_id": report["report_id"],
                                    "message": reason,
                                }
                            )
                    else:
                        pending.append(report)
                db.update_run_counts(run_id, len(reports), len(pending))

                if pending and not dry_run:
                    prior_dir = work_dir / "prior"
                    prior_dir.mkdir(parents=True, exist_ok=True)
                    for report in pending:
                        prior = db.find_prior_cards(
                            company=report.get("parsed_company", ""),
                            ticker=report.get("parsed_ticker", ""),
                            exclude_report_id=report["report_id"],
                        )
                        prior_path = prior_dir / f"{report['report_id']}.json"
                        write_json(prior_path, {"prior_cards": prior})
                        report["prior_cards_path"] = str(prior_path.resolve())

                    batches = _chunks_by_size(
                        pending,
                        int(self.config.get("pipeline.batch_max_reports", 4)),
                        int(self.config.get("pipeline.batch_max_chars", 260000)),
                    )
                    self.logger.info("待初筛 %s 份，拆分为 %s 个 LLM 批次", len(pending), len(batches))
                    max_workers = max(1, int(self.config.get("codex.max_parallel", 3)))

                    def process_batch(batch_index: int, batch: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
                        manifest_path = work_dir / f"triage_batch_{batch_index:03d}.manifest.json"
                        manifest = {
                            "run_id": run_id,
                            "run_date": run_date,
                            "reports": [
                                {
                                    "report_id": report["report_id"],
                                    "file_name": report["file_name"],
                                    "parsed_metadata": {
                                        "institution": report.get("parsed_institution", ""),
                                        "report_date": report.get("parsed_report_date", ""),
                                        "title": report.get("parsed_title", ""),
                                        "company": report.get("parsed_company", ""),
                                        "ticker": report.get("parsed_ticker", ""),
                                    },
                                    "triage_excerpt_path": report["triage_excerpt_path"],
                                    "full_text_path": report["full_text_path"],
                                    "prior_cards_path": report["prior_cards_path"],
                                    "scanned_pages": report.get("scanned_pages", []),
                                }
                                for report in batch
                            ],
                        }
                        write_json(manifest_path, manifest)
                        prompt = _render_prompt(
                            self.config.root / "prompts" / "triage.md",
                            {
                                "MANIFEST_PATH": safe_relative(manifest_path, self.config.root),
                                "WATCHLIST_PATH": safe_relative(self.config.path("watchlist"), self.config.root),
                                "RUN_DATE": run_date,
                            },
                        )
                        output_path = work_dir / f"triage_batch_{batch_index:03d}.output.json"
                        data = self.runner.run_structured(
                            stage="triage",
                            prompt=prompt,
                            schema_path=self.config.root / "schemas" / "triage_batch.schema.json",
                            output_path=output_path,
                            audit_dir=work_dir / "audit",
                            label=f"triage_batch_{batch_index:03d}",
                        )
                        return [r["report_id"] for r in batch], data

                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = {
                            executor.submit(process_batch, index, batch): (index, batch)
                            for index, batch in enumerate(batches, 1)
                        }
                        for future in as_completed(futures):
                            index, batch = futures[future]
                            expected_ids = {report["report_id"] for report in batch}
                            try:
                                _, result = future.result()
                                returned: set[str] = set()
                                for raw_card in result.get("reports", []):
                                    report_id = raw_card.get("report_id", "")
                                    if report_id not in expected_ids or report_id in returned:
                                        continue
                                    card = normalize_and_score_card(raw_card, reports_by_id[report_id], self.config, self.watchlist)
                                    cards_by_id[report_id] = card
                                    db.store_card(report_id, card)
                                    db.update_run_report_status(run_id, report_id, "triaged")
                                    returned.add(report_id)
                                missing = expected_ids - returned
                                for report_id in missing:
                                    reason = f"LLM 初筛批次 {index} 未返回该 report_id"
                                    card = normalize_and_score_card(fallback_card(reports_by_id[report_id], reason), reports_by_id[report_id], self.config, self.watchlist)
                                    cards_by_id[report_id] = card
                                    db.store_card(report_id, card)
                                    errors.append({"stage": "triage", "report_id": report_id, "message": reason})
                            except Exception as exc:
                                self.logger.exception("初筛批次失败：%s", index)
                                for report in batch:
                                    reason = f"LLM 初筛失败：{exc}"
                                    card = normalize_and_score_card(fallback_card(report, reason), report, self.config, self.watchlist)
                                    cards_by_id[report["report_id"]] = card
                                    db.store_card(report["report_id"], card)
                                    errors.append({"stage": "triage", "report_id": report["report_id"], "message": str(exc)})
                elif pending and dry_run:
                    for report in pending:
                        card = normalize_and_score_card(
                            fallback_card(report, "dry-run：未调用 LLM"), report, self.config, self.watchlist
                        )
                        cards_by_id[report["report_id"]] = card

                cards = [cards_by_id[report["report_id"]] for report in reports if report["report_id"] in cards_by_id]
                cards_path = work_dir / "cards_precluster.json"
                write_json(cards_path, {"reports": cards})

                clusters: list[dict[str, Any]]
                if not dry_run:
                    try:
                        prompt = _render_prompt(
                            self.config.root / "prompts" / "cluster.md",
                            {"CARDS_PATH": safe_relative(cards_path, self.config.root), "RUN_DATE": run_date},
                        )
                        result = self.runner.run_structured(
                            stage="synthesis",
                            prompt=prompt,
                            schema_path=self.config.root / "schemas" / "clusters.schema.json",
                            output_path=work_dir / "clusters.output.json",
                            audit_dir=work_dir / "audit",
                            label="clusters",
                        )
                        clusters = _sanitize_clusters(result.get("clusters", []), cards)
                    except Exception as exc:
                        errors.append({"stage": "cluster", "message": str(exc)})
                        self.logger.exception("事件聚类失败，使用本地兜底")
                        clusters = _fallback_clusters(cards)
                else:
                    clusters = _fallback_clusters(cards)

                cards = apply_cluster_duplicate_penalties(cards, clusters, reports_by_id, self.config, self.watchlist)
                cards_by_id = {card["report_id"]: card for card in cards}
                for card in cards:
                    db.store_card(card["report_id"], card)
                db.store_clusters(run_id, clusters)

                deep_dives: dict[str, dict[str, Any]] = {}
                deep_paths: dict[str, Path] = {}
                if deep_dive and not dry_run:
                    deep_candidates = [
                        card
                        for card in sorted(cards, key=lambda c: c.get("priority_score", 0), reverse=True)
                        if card.get("importance_score", 0) >= int(self.config.get("pipeline.min_deep_dive_score", 65))
                        and reports_by_id[card["report_id"]].get("extraction_status") == "success"
                    ][: int(self.config.get("pipeline.deep_dive_n", 10))]
                    deep_dir = output_dir / "deep_dive"
                    deep_dir.mkdir(parents=True, exist_ok=True)

                    def process_deep(card: dict[str, Any]) -> tuple[str, dict[str, Any]]:
                        report_id = card["report_id"]
                        report = reports_by_id[report_id]
                        item_dir = work_dir / "deep" / report_id
                        item_dir.mkdir(parents=True, exist_ok=True)
                        card_path = item_dir / "card.json"
                        cluster_path = item_dir / "cluster.json"
                        prior_path = item_dir / "prior.json"
                        manifest_path = item_dir / "manifest.json"
                        write_json(card_path, card)
                        write_json(cluster_path, _find_cluster_for_report(clusters, report_id) or {})
                        with ResearchDB(self.config.path("database")) as thread_db:
                            prior = thread_db.find_prior_cards(
                                company=report.get("parsed_company", ""),
                                ticker=report.get("parsed_ticker", ""),
                                exclude_report_id=report_id,
                                limit=8,
                            )
                        write_json(prior_path, {"prior_cards": prior})
                        write_json(
                            manifest_path,
                            {
                                "report_id": report_id,
                                "full_text_path": report["full_text_path"],
                                "card_path": str(card_path.resolve()),
                                "cluster_path": str(cluster_path.resolve()),
                                "prior_cards_path": str(prior_path.resolve()),
                            },
                        )
                        prompt = _render_prompt(
                            self.config.root / "prompts" / "deep_dive.md",
                            {"MANIFEST_PATH": safe_relative(manifest_path, self.config.root)},
                        )
                        result = self.runner.run_structured(
                            stage="deep_dive",
                            prompt=prompt,
                            schema_path=self.config.root / "schemas" / "deep_dive.schema.json",
                            output_path=item_dir / "output.json",
                            audit_dir=work_dir / "audit",
                            label=f"deep_{report_id}",
                        )
                        if result.get("report_id") != report_id:
                            raise CodexError(f"深度分析返回了错误 report_id：{result.get('report_id')}")
                        return report_id, result

                    def store_deep_result(card: dict[str, Any], result: dict[str, Any]) -> None:
                        report_id = card["report_id"]
                        deep_dives[report_id] = result
                        filename = f"{slugify(card.get('title',''))[:70]}-{report_id[-8:]}.md"
                        md_path = deep_dir / filename
                        atomic_write_text(
                            md_path,
                            render_deep_dive_markdown(
                                result, card, _find_cluster_for_report(clusters, report_id)
                            ),
                        )
                        deep_paths[report_id] = md_path
                        db.store_deep_dive(run_id, report_id, result, str(md_path.resolve()))

                    deep_to_process: list[dict[str, Any]] = []
                    reused_deep_count = 0
                    reuse_deep = bool(self.config.get("pipeline.reuse_existing_deep_dives", True)) and not force
                    for card in deep_candidates:
                        cached = db.get_latest_deep_dive(card["report_id"]) if reuse_deep else None
                        if cached and cached.get("report_id") == card["report_id"]:
                            store_deep_result(card, cached)
                            reused_deep_count += 1
                        else:
                            deep_to_process.append(card)
                    if reused_deep_count:
                        self.logger.info("复用已有深度分析 %s 份，新增执行 %s 份", reused_deep_count, len(deep_to_process))

                    max_workers = max(1, min(int(self.config.get("codex.max_parallel", 3)), 3))
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        future_map = {executor.submit(process_deep, card): card for card in deep_to_process}
                        for future in as_completed(future_map):
                            card = future_map[future]
                            report_id = card["report_id"]
                            try:
                                _, result = future.result()
                                store_deep_result(card, result)
                            except Exception as exc:
                                errors.append({"stage": "deep_dive", "report_id": report_id, "message": str(exc)})
                                self.logger.exception("深度分析失败：%s", report_id)

                digest_input = _build_digest_input(run_meta, cards, clusters, deep_dives)
                digest_input_path = work_dir / "digest_input.json"
                write_json(digest_input_path, digest_input)
                if not dry_run:
                    try:
                        prompt = _render_prompt(
                            self.config.root / "prompts" / "digest.md",
                            {
                                "DIGEST_INPUT_PATH": safe_relative(digest_input_path, self.config.root),
                                "RUN_DATE": run_date,
                                "NEXT_7D_START": (
                                    datetime.strptime(run_date, "%Y-%m-%d") + timedelta(days=1)
                                ).strftime("%Y-%m-%d"),
                                "NEXT_7D_END": (
                                    datetime.strptime(run_date, "%Y-%m-%d") + timedelta(days=7)
                                ).strftime("%Y-%m-%d"),
                            },
                        )
                        digest = self.runner.run_structured(
                            stage="synthesis",
                            prompt=prompt,
                            schema_path=self.config.root / "schemas" / "digest.schema.json",
                            output_path=work_dir / "digest.output.json",
                            audit_dir=work_dir / "audit",
                            label="digest",
                        )
                    except Exception as exc:
                        errors.append({"stage": "digest", "message": str(exc)})
                        self.logger.exception("综合摘要失败，使用本地兜底")
                        digest = _fallback_digest(cards, clusters, run_date)
                else:
                    digest = _fallback_digest(cards, clusters, run_date)

                run_meta.update(
                    {
                        "input_pdf_count": len(pdfs),
                        "duplicate_pdf_count": max(0, len(pdfs) - len(reports)),
                        "report_count": len(cards),
                        "extracted_success_count": sum(
                            1 for report in reports if report.get("extraction_status") == "success"
                        ),
                        "fallback_card_count": sum(
                            1 for card in cards if card.get("analysis_status") == "fallback"
                        ),
                        "cluster_count": len(clusters),
                        "deep_dive_count": len(deep_dives),
                        "errors": errors,
                    }
                )
                write_machine_outputs(
                    output_dir,
                    run_meta=run_meta,
                    cards=cards,
                    clusters=clusters,
                    deep_dives=deep_dives,
                    digest=digest,
                )
                render_one_pager(output_dir, run_meta, digest, cards, clusters)
                render_top10(output_dir, cards, deep_paths, int(self.config.get("pipeline.top_n", 10)))
                render_clusters(output_dir, clusters)
                render_index_csv(output_dir, cards, str(self.config.get("output.csv_encoding", "utf-8-sig")))
                render_risk_catalyst(output_dir, cards, digest)
                if bool(self.config.get("pipeline.output_html", True)):
                    render_dashboard(output_dir, run_meta, digest, cards, clusters, int(self.config.get("pipeline.top_n", 10)))

                qc: dict[str, Any]
                if run_qc and not dry_run:
                    qc_manifest_path = work_dir / "qc_manifest.json"
                    qc_files = [
                        str((output_dir / name).resolve())
                        for name in (
                            "00-今日研报一页纸.md",
                            "01-今日必读Top10.md",
                            "02-主题共识与分歧.md",
                            "03-全量研报索引.csv",
                            "04-风险与催化跟踪.md",
                        )
                    ]
                    top_source_files = [
                        reports_by_id[card["report_id"]]["full_text_path"]
                        for card in sorted(cards, key=lambda c: c.get("priority_score", 0), reverse=True)[:10]
                    ]
                    write_json(
                        qc_manifest_path,
                        {
                            "output_files": qc_files,
                            "report_cards_path": str((output_dir / "machine" / "report_cards.json").resolve()),
                            "clusters_path": str((output_dir / "machine" / "clusters.json").resolve()),
                            "source_texts_for_spot_check": top_source_files,
                        },
                    )
                    try:
                        prompt = _render_prompt(
                            self.config.root / "prompts" / "qc.md",
                            {"QC_MANIFEST_PATH": safe_relative(qc_manifest_path, self.config.root)},
                        )
                        qc = self.runner.run_structured(
                            stage="qc",
                            prompt=prompt,
                            schema_path=self.config.root / "schemas" / "qc.schema.json",
                            output_path=work_dir / "qc.output.json",
                            audit_dir=work_dir / "audit",
                            label="qc",
                        )
                    except Exception as exc:
                        errors.append({"stage": "qc", "message": str(exc)})
                        qc = {
                            "passed": False,
                            "summary": "自动质量检查未完成；其他分析文件已生成。",
                            "issues": [
                                {
                                    "severity": "warning",
                                    "category": "other",
                                    "report_id": "",
                                    "file": "",
                                    "message": str(exc),
                                    "suggested_action": "检查 LLM 日志后重新运行 QC。",
                                }
                            ],
                        }
                else:
                    qc = {
                        "passed": dry_run,
                        "summary": "dry-run 未调用 Codex QC。" if dry_run else "本次按参数跳过 QC。",
                        "issues": [],
                    }
                render_qc(output_dir, qc)

                archived_paths: list[str] = []
                if (
                    not dry_run
                    and not errors
                    and bool(self.config.get("pipeline.archive_after_success", False))
                ):
                    try:
                        archived_paths = self._archive_sources(run_date, source_dir, pdfs)
                    except Exception as exc:
                        errors.append(
                            {
                                "stage": "archive",
                                "severity": "warning",
                                "message": str(exc),
                            }
                        )
                        self.logger.exception("成功后归档失败")

                final_status = "dry_run" if dry_run else "partial" if errors else "success"
                run_meta.update(
                    {
                        "status": final_status,
                        "completed_at": utc_now_iso(),
                        "archive_copy_count": len(archived_paths),
                        "archive_copies": archived_paths,
                        "errors": errors,
                    }
                )
                write_machine_outputs(
                    output_dir,
                    run_meta=run_meta,
                    cards=cards,
                    clusters=clusters,
                    deep_dives=deep_dives,
                    digest=digest,
                    qc=qc,
                )
                update_latest_link(self.config.path("outputs"), output_dir)
                db.finish_run(run_id, final_status, errors)
                dashboard_path = output_dir / "dashboard.html"
                return {
                    "status": final_status,
                    **run_meta,
                    "output_dir": str(output_dir.resolve()),
                    "dashboard": str(dashboard_path.resolve()) if dashboard_path.exists() else "",
                }
            except Exception as exc:
                errors.append({"stage": "fatal", "message": str(exc)})
                db.finish_run(run_id, "failed", errors)
                self.logger.exception("研报流水线失败")
                raise

    def scheduler_tick(self) -> list[dict[str, Any]]:
        timezone_name = str(self.config.get("project.timezone", "Asia/Shanghai"))
        now = local_now(timezone_name)
        catchup = float(self.config.get("automation.catchup_hours", 4))
        results: list[dict[str, Any]] = []
        schedules = [str(value) for value in self.config.get("automation.schedules", ["09:00", "21:00"])]
        with ResearchDB(self.config.path("database")) as db:
            for schedule in schedules:
                try:
                    hour, minute = [int(part) for part in schedule.split(":", 1)]
                except Exception:
                    self.logger.warning("忽略无效计划时间：%s", schedule)
                    continue
                scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if now < scheduled or now > scheduled + timedelta(hours=catchup):
                    continue
                run_date = scheduled.strftime("%Y-%m-%d")
                session = f"{hour:02d}{minute:02d}"
                if session not in {"0900", "2100"}:
                    continue
                if db.has_successful_run(run_date, session):
                    continue
                source_dir = self._input_dir(run_date)
                if not discover_pdfs(source_dir):
                    self.logger.info("计划 %s 到达，但目录暂无 PDF：%s", session, source_dir)
                    continue
                results.append({"run_date": run_date, "session": session})
        # Run outside the DB context; the pipeline opens its own connection and lock.
        completed = []
        for item in results:
            completed.append(self.run(run_date=item["run_date"], session=item["session"]))
        return completed
