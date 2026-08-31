from __future__ import annotations

import csv
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .config import AppConfig
from .utils import clamp, normalize_whitespace


@dataclass(frozen=True)
class WatchItem:
    market: str
    ticker: str
    name: str
    holding: bool
    priority: int
    theme: str
    notes: str


def _as_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "是"}


def load_watchlist(path: Path) -> list[WatchItem]:
    if not path.exists():
        return []
    items: list[WatchItem] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            name = normalize_whitespace(row.get("name", ""))
            ticker = str(row.get("ticker", "")).strip()
            if not name and not ticker:
                continue
            try:
                priority = int(row.get("priority", 0) or 0)
            except ValueError:
                priority = 0
            items.append(
                WatchItem(
                    market=str(row.get("market", "")).strip(),
                    ticker=ticker,
                    name=name,
                    holding=_as_bool(row.get("holding")),
                    priority=int(clamp(priority, 0, 5)),
                    theme=normalize_whitespace(row.get("theme", "")),
                    notes=normalize_whitespace(row.get("notes", "")),
                )
            )
    return items


def _company_candidates(card: dict[str, Any]) -> tuple[set[str], set[str]]:
    names: set[str] = set()
    tickers: set[str] = set()
    for company in card.get("companies", []) or []:
        name = normalize_whitespace(str(company.get("name", ""))).lower()
        ticker = str(company.get("ticker", "")).strip().lower()
        if name:
            names.add(name)
        if ticker:
            tickers.add(ticker)
    return names, tickers


def infer_market(ticker: str) -> str:
    normalized = str(ticker or "").strip().upper()
    if not normalized:
        return ""
    suffix_markets = (
        (".HK", "HK"),
        (".US", "US"),
        (".TW", "TW"),
        (".T", "JP"),
        (".KS", "KR"),
        (".KQ", "KR"),
    )
    for suffix, market in suffix_markets:
        if normalized.endswith(suffix):
            return market
    if len(normalized) == 6 and normalized.isdigit() and normalized[0] in "03684":
        return "CN"
    return ""


def match_watchlist(card: dict[str, Any], watchlist: list[WatchItem]) -> list[WatchItem]:
    names, tickers = _company_candidates(card)
    themes = {normalize_whitespace(str(x)).lower() for x in card.get("themes", []) or []}
    matches: list[WatchItem] = []
    for item in watchlist:
        ticker_hit = bool(item.ticker and item.ticker.lower() in tickers)
        name_norm = item.name.lower()
        name_hit = bool(name_norm and any(name_norm in name or name in name_norm for name in names))
        theme_norm = item.theme.lower()
        theme_hit = bool(theme_norm and any(part and part in " ".join(themes) for part in theme_norm.split("/")))
        if ticker_hit or name_hit or (theme_hit and item.priority >= 5):
            matches.append(item)
    return sorted(matches, key=lambda item: (item.holding, item.priority), reverse=True)


def _int_component(components: dict[str, Any], key: str, low: int, high: int) -> int:
    try:
        value = int(round(float(components.get(key, 0) or 0)))
    except (TypeError, ValueError):
        value = 0
    return int(clamp(value, low, high))


def normalize_and_score_card(
    card: dict[str, Any],
    report: dict[str, Any],
    config: AppConfig,
    watchlist: list[WatchItem],
) -> dict[str, Any]:
    card = dict(card or {})
    card["report_id"] = report["report_id"]
    card.setdefault("institution", report.get("parsed_institution", ""))
    card.setdefault("report_date", report.get("parsed_report_date", ""))
    card.setdefault("title", report.get("parsed_title", report.get("file_name", "")))
    card.setdefault("report_type", "other")
    card.setdefault("primary_industry", "未分类")
    card.setdefault("themes", [])
    card.setdefault("companies", [])
    if not card["companies"] and (report.get("parsed_company") or report.get("parsed_ticker")):
        card["companies"] = [
            {
                "name": report.get("parsed_company", ""),
                "ticker": report.get("parsed_ticker", ""),
                "market": "",
            }
        ]
    for company in card["companies"]:
        if not str(company.get("ticker", "")).strip():
            head = re.split(r"[：:]", str(card.get("title", "")), maxsplit=1)[0].strip()
            parsed = re.match(
                r"^(.*?)\s*[（(]([0-9A-Za-z.\-]+)(?:[，,][^）)]*)?[）)]\s*$",
                head,
            )
            if parsed:
                company["name"] = normalize_whitespace(parsed.group(1))
                company["ticker"] = parsed.group(2).strip()
        if not str(company.get("market", "")).strip():
            ticker = str(company.get("ticker", ""))
            company["market"] = infer_market(ticker) or ("【未获取到】" if ticker else "")
    for field in (
        "new_information",
        "key_metrics",
        "estimate_changes",
        "catalysts",
        "risks",
        "a_share_mapping",
        "delta_from_prior",
        "evidence_gaps",
        "source_pages_used",
    ):
        card.setdefault(field, [])
    for estimate in card["estimate_changes"]:
        old_value = estimate.get("old_value")
        new_value = estimate.get("new_value")
        reported_change = estimate.get("change_pct")
        if not (
            isinstance(old_value, (int, float))
            and isinstance(new_value, (int, float))
            and isinstance(reported_change, (int, float))
            and old_value != 0
        ):
            continue
        displayed_change = (new_value - old_value) / abs(old_value) * 100
        if abs(displayed_change - reported_change) <= 0.5:
            continue
        estimate["reported_change_pct"] = reported_change
        estimate["change_pct"] = round(displayed_change, 2)
        note = (
            f"{estimate.get('period','')} {estimate.get('metric','')}：机构表列变化"
            f"{reported_change:+.2f}%与展示值{old_value}→{new_value}不完全自洽；"
            f"输出按展示值重算为{displayed_change:+.2f}%，差异可能来自未四舍五入数据。"
        )
        if note not in card["evidence_gaps"]:
            card["evidence_gaps"].append(note)
    card.setdefault("core_conclusion", "")
    card.setdefault("rating", {"current": "", "previous": "", "change": "unknown"})
    card.setdefault(
        "target_price",
        {"current": None, "previous": None, "currency": "", "change_pct": None},
    )
    card.setdefault("duplicate_hint", "")
    card.setdefault("analysis_status", "analyzed")

    components = dict(card.get("score_components") or {})
    limits = {
        "watchlist_relevance": int(config.get("scoring.watchlist_relevance", 20)),
        "novelty": int(config.get("scoring.novelty", 20)),
        "earnings_valuation_impact": int(config.get("scoring.earnings_valuation_impact", 15)),
        "catalyst_certainty": int(config.get("scoring.catalyst_certainty", 15)),
        "consensus_divergence": int(config.get("scoring.consensus_divergence", 10)),
        "evidence_quality": int(config.get("scoring.evidence_quality", 10)),
        "actionability": int(config.get("scoring.actionability", 10)),
        "duplicate_penalty": int(config.get("scoring.duplicate_penalty_max", 25)),
        "stale_penalty": int(config.get("scoring.stale_penalty_max", 15)),
        "unverified_penalty": int(config.get("scoring.unverified_penalty_max", 15)),
    }
    normalized_components: dict[str, int] = {}
    for key, high in limits.items():
        normalized_components[key] = _int_component(components, key, 0, high)

    matches = match_watchlist(card, watchlist)
    if matches:
        best = matches[0]
        relationship_floor = min(limits["watchlist_relevance"], best.priority * 4)
        if best.holding:
            relationship_floor = limits["watchlist_relevance"]
        normalized_components["watchlist_relevance"] = max(
            normalized_components["watchlist_relevance"], relationship_floor
        )
    card["watchlist_matches"] = [asdict(item) for item in matches]

    positive_keys = (
        "watchlist_relevance",
        "novelty",
        "earnings_valuation_impact",
        "catalyst_certainty",
        "consensus_divergence",
        "evidence_quality",
        "actionability",
    )
    penalty_keys = ("duplicate_penalty", "stale_penalty", "unverified_penalty")
    importance = sum(normalized_components[key] for key in positive_keys) - sum(
        normalized_components[key] for key in penalty_keys
    )
    importance = int(clamp(importance, 0, 100))

    try:
        direction = int(round(float(card.get("direction_score", 0) or 0)))
    except (TypeError, ValueError):
        direction = 0
    direction = int(clamp(direction, -3, 3))
    try:
        confidence = int(round(float(card.get("confidence_score", 0) or 0)))
    except (TypeError, ValueError):
        confidence = 0
    confidence = int(clamp(confidence, 0, 100))

    holding_negative = any(item.holding for item in matches) and direction <= -2
    boost = int(config.get("scoring.holding_negative_boost", 10)) if holding_negative else 0
    priority = int(clamp(importance + boost, 0, 120))

    if priority >= 80 or (holding_negative and priority >= 70):
        action = "must_read_full"
    elif priority >= 65:
        action = "read_summary"
    elif priority >= 45:
        action = "theme_only"
    else:
        action = "index_only"

    card["score_components"] = normalized_components
    card["importance_score"] = importance
    card["priority_score"] = priority
    card["direction_score"] = direction
    card["confidence_score"] = confidence
    card["recommended_action"] = action
    card["source_file"] = (
        report.get("file_path", "") if bool(config.get("output.include_source_paths", True)) else ""
    )
    card["extracted_full_text"] = str(Path(report.get("extracted_dir", "")) / "full_text.md")
    card["extraction_status"] = report.get("extraction_status", "")
    card["scanned_pages"] = report.get("scanned_pages", [])
    return card


def fallback_card(report: dict[str, Any], reason: str = "") -> dict[str, Any]:
    companies: list[dict[str, str]] = []
    if report.get("parsed_company") or report.get("parsed_ticker"):
        companies.append(
            {
                "name": report.get("parsed_company", ""),
                "ticker": report.get("parsed_ticker", ""),
                "market": infer_market(str(report.get("parsed_ticker", "")))
                or ("【未获取到】" if report.get("parsed_ticker") else ""),
            }
        )
    return {
        "report_id": report["report_id"],
        "institution": report.get("parsed_institution", ""),
        "report_date": report.get("parsed_report_date", ""),
        "title": report.get("parsed_title", report.get("file_name", "")),
        "companies": companies,
        "primary_industry": "未分类",
        "themes": [],
        "report_type": "other",
        "rating": {"current": "", "previous": "", "change": "unknown"},
        "target_price": {"current": None, "previous": None, "currency": "", "change_pct": None},
        "core_conclusion": "自动分析未完成，已保留在全量索引中。",
        "new_information": [],
        "key_metrics": [],
        "estimate_changes": [],
        "catalysts": [],
        "risks": [
            {
                "risk": reason or report.get("extraction_error", "自动分析失败"),
                "affected_assets": [],
                "severity": "high",
                "page": None,
            }
        ],
        "a_share_mapping": [],
        "delta_from_prior": [],
        "evidence_gaps": [reason or "Codex 未返回有效结构化结果"],
        "score_components": {
            "watchlist_relevance": 0,
            "novelty": 0,
            "earnings_valuation_impact": 0,
            "catalyst_certainty": 0,
            "consensus_divergence": 0,
            "evidence_quality": 0,
            "actionability": 0,
            "duplicate_penalty": 0,
            "stale_penalty": 0,
            "unverified_penalty": 15,
        },
        "direction_score": 0,
        "confidence_score": 0,
        "duplicate_hint": "",
        "recommended_action": "index_only",
        "source_pages_used": [],
        "analysis_status": "fallback",
    }


def apply_cluster_duplicate_penalties(
    cards: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    reports_by_id: dict[str, dict[str, Any]],
    config: AppConfig,
    watchlist: list[WatchItem],
) -> list[dict[str, Any]]:
    by_id = {card["report_id"]: dict(card) for card in cards}
    max_penalty = int(config.get("scoring.duplicate_penalty_max", 25))
    for cluster in clusters:
        report_ids = [rid for rid in cluster.get("report_ids", []) if rid in by_id]
        best = cluster.get("best_report_id", "")
        penalty = min(max_penalty, 5 + (len(report_ids) - 1) * 3)
        for report_id in report_ids:
            card = by_id[report_id]
            components = dict(card.get("score_components") or {})
            if len(report_ids) > 1:
                if report_id == best:
                    components["duplicate_penalty"] = min(int(components.get("duplicate_penalty", 0)), 3)
                else:
                    components["duplicate_penalty"] = max(int(components.get("duplicate_penalty", 0)), penalty)
            card["score_components"] = components
            card["event_cluster_id"] = cluster.get("cluster_id", "")
            card["event_title"] = cluster.get("event_title", "")
            by_id[report_id] = normalize_and_score_card(
                card, reports_by_id[report_id], config, watchlist
            )
    return list(by_id.values())
