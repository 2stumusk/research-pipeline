from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from research_pipeline.config import AppConfig, load_config
from research_pipeline.db import ResearchDB
from research_pipeline.scoring import (
    apply_cluster_duplicate_penalties,
    infer_market,
    load_watchlist,
    normalize_and_score_card,
)


def make_config(root: Path) -> AppConfig:
    base = load_config()
    data = copy.deepcopy(base.data)
    cfg = AppConfig(root, data, root / "config.yaml")
    cfg.ensure_directories()
    cfg.path("watchlist").write_text(
        "market,ticker,name,holding,priority,theme,notes\n"
        "CN,300308,中际旭创,true,5,光通信/光模块,当前持仓\n",
        encoding="utf-8",
    )
    return cfg


def sample_report(root: Path) -> dict:
    return {
        "report_id": "rpt_test_001",
        "sha256": "a" * 64,
        "file_name": "测试.pdf",
        "file_path": str(root / "测试.pdf"),
        "extracted_dir": str(root / "extracted" / "rpt_test_001"),
        "file_size": 100,
        "page_count": 5,
        "text_chars": 1000,
        "scanned_pages": [],
        "parsed_report_date": "2026-08-21",
        "parsed_institution": "测试券商",
        "parsed_title": "中际旭创负面风险更新",
        "parsed_company": "中际旭创",
        "parsed_ticker": "300308",
        "extraction_status": "success",
        "extraction_error": "",
    }


class ScoringAndDbTests(unittest.TestCase):
    def test_estimate_change_reconciles_material_rounding_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = normalize_and_score_card(
                {
                    "estimate_changes": [
                        {
                            "metric": "EPS",
                            "period": "2028E",
                            "old_value": 0.95,
                            "new_value": 0.96,
                            "change_pct": 2.0,
                        }
                    ],
                    "score_components": {},
                },
                sample_report(root),
                make_config(root),
                [],
            )
            estimate = result["estimate_changes"][0]
            self.assertEqual(estimate["reported_change_pct"], 2.0)
            self.assertEqual(estimate["change_pct"], 1.05)
            self.assertIn("按展示值重算", result["evidence_gaps"][0])

    def test_market_is_inferred_only_for_known_ticker_formats(self) -> None:
        self.assertEqual(infer_market("300308"), "CN")
        self.assertEqual(infer_market("2367.HK"), "HK")
        self.assertEqual(infer_market("AVGO.US"), "US")
        self.assertEqual(infer_market("DIS.UN"), "")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = normalize_and_score_card(
                {
                    "companies": [{"name": "中际旭创", "ticker": "300308", "market": ""}],
                    "score_components": {},
                },
                sample_report(root),
                make_config(root),
                [],
            )
            self.assertEqual(result["companies"][0]["market"], "CN")
            unknown_report = sample_report(root)
            unknown_report["parsed_company"] = "迪士尼"
            unknown_report["parsed_ticker"] = "DIS.UN"
            unknown = normalize_and_score_card(
                {
                    "companies": [{"name": "迪士尼", "ticker": "DIS.UN", "market": ""}],
                    "score_components": {},
                },
                unknown_report,
                make_config(root),
                [],
            )
            self.assertEqual(unknown["companies"][0]["market"], "【未获取到】")
            uncovered_report = sample_report(root)
            uncovered_report["parsed_company"] = "小菜园（0999.HK，未覆盖）"
            uncovered_report["parsed_ticker"] = ""
            uncovered = normalize_and_score_card(
                {
                    "title": "小菜园（0999.HK，未覆盖）：1H26 NDR要点",
                    "companies": [
                        {"name": "小菜园（0999.HK，未覆盖）", "ticker": "", "market": ""}
                    ],
                    "score_components": {},
                },
                uncovered_report,
                make_config(root),
                [],
            )
            self.assertEqual(
                uncovered["companies"][0],
                {"name": "小菜园", "ticker": "0999.HK", "market": "HK"},
            )

    def test_single_report_cluster_is_backfilled_without_duplicate_penalty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = make_config(root)
            report = sample_report(root)
            card = normalize_and_score_card(
                {"score_components": {"novelty": 10}, "direction_score": 1, "confidence_score": 70},
                report,
                cfg,
                [],
            )
            result = apply_cluster_duplicate_penalties(
                [card],
                [{"cluster_id": "single_001", "event_title": "单报告事件", "report_ids": [report["report_id"]], "best_report_id": report["report_id"]}],
                {report["report_id"]: report},
                cfg,
                [],
            )[0]
            self.assertEqual(result["event_cluster_id"], "single_001")
            self.assertEqual(result["event_title"], "单报告事件")
            self.assertEqual(result["score_components"]["duplicate_penalty"], 0)

    def test_source_paths_can_be_hidden_from_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = make_config(root)
            cfg.data["output"]["include_source_paths"] = False
            result = normalize_and_score_card(
                {"score_components": {}, "direction_score": 0, "confidence_score": 0},
                sample_report(root),
                cfg,
                [],
            )
            self.assertEqual(result["source_file"], "")

    def test_holding_negative_risk_boosts_priority_not_direction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = make_config(root)
            report = sample_report(root)
            card = {
                "companies": [{"name": "中际旭创", "ticker": "300308", "market": "CN"}],
                "themes": ["光模块"],
                "core_conclusion": "重大供应风险",
                "score_components": {
                    "watchlist_relevance": 5,
                    "novelty": 15,
                    "earnings_valuation_impact": 12,
                    "catalyst_certainty": 8,
                    "consensus_divergence": 6,
                    "evidence_quality": 8,
                    "actionability": 8,
                    "duplicate_penalty": 0,
                    "stale_penalty": 0,
                    "unverified_penalty": 0,
                },
                "direction_score": -2,
                "confidence_score": 80,
            }
            result = normalize_and_score_card(card, report, cfg, load_watchlist(cfg.path("watchlist")))
            self.assertEqual(result["score_components"]["watchlist_relevance"], 20)
            self.assertEqual(result["direction_score"], -2)
            self.assertEqual(result["priority_score"], result["importance_score"] + 10)
            self.assertEqual(result["recommended_action"], "must_read_full")

    def test_database_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = make_config(root)
            report = sample_report(root)
            report["created_at"] = "2026-08-21T00:00:00+00:00"
            card = normalize_and_score_card(
                {
                    "companies": [{"name": "中际旭创", "ticker": "300308", "market": "CN"}],
                    "themes": ["光模块"],
                    "score_components": {"novelty": 10},
                    "direction_score": 1,
                    "confidence_score": 70,
                },
                report,
                cfg,
                load_watchlist(cfg.path("watchlist")),
            )
            with ResearchDB(cfg.path("database")) as db:
                db.upsert_report(report)
                db.store_card(report["report_id"], card)
                loaded = db.get_card(report["report_id"])
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded["report_id"], report["report_id"])
                db.create_run("run1", "2026-08-21", "0900", str(root / "out"))
                db.add_run_report("run1", report["report_id"])
                deep = {"report_id": report["report_id"], "one_sentence_conclusion": "测试"}
                db.store_deep_dive("run1", report["report_id"], deep)
                db.finish_run("run1", "success")
                self.assertTrue(db.has_successful_run("2026-08-21", "0900"))
                self.assertEqual(db.get_latest_deep_dive(report["report_id"]), deep)


if __name__ == "__main__":
    unittest.main()
