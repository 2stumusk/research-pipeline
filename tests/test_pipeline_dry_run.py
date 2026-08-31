from __future__ import annotations

import copy
import logging
import tempfile
import unittest
from pathlib import Path

import pymupdf

from research_pipeline.config import AppConfig, load_config
from research_pipeline.pipeline import (
    PipelineError,
    ResearchPipeline,
    _build_digest_input,
    _explicit_next_7d_catalysts,
    _format_estimate_change,
    _is_earnings_estimate,
)
from research_pipeline.render import render_one_pager, render_risk_catalyst


def make_config(root: Path) -> AppConfig:
    base = load_config()
    data = copy.deepcopy(base.data)
    data["pipeline"]["top_n"] = 3
    data["pipeline"]["deep_dive_n"] = 0
    cfg = AppConfig(root, data, root / "config.yaml")
    cfg.ensure_directories()
    cfg.path("watchlist").write_text(
        "market,ticker,name,holding,priority,theme,notes\nCN,600183,生益科技,false,5,PCB/CCL,观察池\n",
        encoding="utf-8",
    )
    return cfg


def create_pdf(path: Path, title: str) -> None:
    doc = pymupdf.open()
    for i in range(2):
        page = doc.new_page()
        page.insert_text((72, 72), f"{title} 第{i+1}页 核心观点 盈利预测 风险提示")
    doc.save(path)
    doc.close()


class PipelineDryRunTests(unittest.TestCase):
    def test_risk_catalyst_output_separates_direction_and_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = render_risk_catalyst(
                Path(tmp),
                [
                    {
                        "report_id": "rpt_1",
                        "risks": [],
                        "catalysts": [
                            {
                                "date_or_window": "2026-09-01",
                                "event": "测试催化",
                                "affected_assets": ["测试公司"],
                                "direction": 0,
                                "page": 1,
                            }
                        ],
                    }
                ],
                {},
            )
            rendered = path.read_text(encoding="utf-8")
            self.assertIn("| 方向 | 来源 | 页码 |", rendered)
            self.assertIn("| 0 | rpt_1 | 1 |", rendered)

    def test_one_pager_includes_report_page_and_institution_traceability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_id = "rpt_trace_1"
            cards = [
                {
                    "report_id": report_id,
                    "institution": "测试券商",
                    "source_pages_used": [1, 4],
                    "estimate_changes": [
                        {"metric": "EPS", "period": "2027E", "page": 4}
                    ],
                }
            ]
            digest = {
                "executive_view": "结论",
                "top_changes": [
                    {
                        "title": "变化",
                        "why_it_matters": "重要",
                        "affected_assets": ["测试公司"],
                        "direction": 1,
                        "confidence": 80,
                        "report_ids": [report_id],
                    }
                ],
                "risk_alerts": [],
                "earnings_upgrades": [
                    {
                        "company": "测试公司",
                        "ticker": "300001",
                        "metric": "EPS",
                        "period": "2026E/2027E",
                        "change": "+10%",
                        "report_id": report_id,
                    }
                ],
                "earnings_downgrades": [],
            }
            path = render_one_pager(
                root,
                {"run_date": "2026-08-21", "session": "0900"},
                digest,
                cards,
                [],
            )
            rendered = path.read_text(encoding="utf-8")
            self.assertIn(f"测试券商｜{report_id}｜PDF第1、4页", rendered)
            self.assertIn(f"+10%｜测试券商｜{report_id}｜PDF第4页", rendered)

    def test_digest_estimate_and_catalyst_guards(self) -> None:
        self.assertTrue(_is_earnings_estimate("2027E EPS"))
        self.assertTrue(_is_earnings_estimate("智能手机毛利率"))
        self.assertFalse(_is_earnings_estimate("目标价适用市盈率"))
        self.assertEqual(
            _format_estimate_change(
                {
                    "metric": "智能手机毛利率",
                    "old_value": 5.0,
                    "new_value": 8.0,
                    "unit": "%",
                    "change_pct": 60.0,
                }
            ),
            "5% → 8%, +3个百分点（相对+60.0%）",
        )
        cards = [
            {
                "catalysts": [
                    {"date_or_window": "2026-08-25", "event": "区间内"},
                    {"date_or_window": "4Q26", "event": "模糊远期"},
                    {"date_or_window": "2026-09-01", "event": "区间外"},
                ]
            }
        ]
        self.assertEqual(
            [item["event"] for item in _explicit_next_7d_catalysts(cards, "2026-08-21")],
            ["区间内"],
        )

    def test_digest_input_keeps_synthesis_fields_and_drops_expanded_details(self) -> None:
        card = {
            "report_id": "rpt_1",
            "title": "测试报告",
            "core_conclusion": "结论",
            "key_metrics": [{"metric": "EPS", "value": 1.0}],
            "extracted_full_text": "不应进入摘要输入",
            "source_file": "/tmp/source.pdf",
            "score_components": {"novelty": 10},
        }
        deep = {
            "report_id": "rpt_1",
            "one_sentence_conclusion": "深度结论",
            "argument_chain": [{"claim": "大段展开"}],
            "final_judgment": "保留的判断",
        }
        result = _build_digest_input(
            {"run_id": "run_1"},
            [card],
            [{"cluster_id": "cluster_1", "report_ids": ["rpt_1"]}],
            {"rpt_1": deep},
        )
        self.assertEqual(result["cards"][0]["key_metrics"][0]["metric"], "EPS")
        self.assertNotIn("extracted_full_text", result["cards"][0])
        self.assertNotIn("source_file", result["cards"][0])
        self.assertNotIn("score_components", result["cards"][0])
        self.assertEqual(result["deep_dives"]["rpt_1"]["final_judgment"], "保留的判断")
        self.assertNotIn("argument_chain", result["deep_dives"]["rpt_1"])

    def test_rejects_invalid_or_path_like_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = make_config(Path(tmp))
            pipeline = ResearchPipeline(cfg, logging.getLogger("invalid-date"))
            for value in ("2026-8-21", "2026-02-30", "../../outside"):
                with self.subTest(value=value), self.assertRaises(PipelineError):
                    pipeline.run(
                        run_date=value,
                        session="0900",
                        dry_run=True,
                        deep_dive=False,
                        run_qc=False,
                    )

    def test_full_dry_run_generates_all_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = make_config(root)
            source = cfg.path("inbox") / "2026-08-21"
            source.mkdir(parents=True)
            create_pdf(source / "高盛-生益科技（600183）：业绩更新-260821.pdf", "生益科技")
            create_pdf(source / "摩根士丹利-亚洲宏观风险更新-260821.pdf", "亚洲宏观")

            pipeline = ResearchPipeline(cfg, logging.getLogger("dry-run"))
            result = pipeline.run(
                run_date="2026-08-21",
                session="0900",
                dry_run=True,
                deep_dive=False,
                run_qc=False,
            )
            self.assertEqual(result["status"], "dry_run")
            output = Path(result["output_dir"])
            for name in (
                "00-今日研报一页纸.md",
                "01-今日必读Top10.md",
                "02-主题共识与分歧.md",
                "03-全量研报索引.csv",
                "04-风险与催化跟踪.md",
                "05-质量检查.md",
                "dashboard.html",
                "machine/report_cards.json",
            ):
                self.assertTrue((output / name).exists(), name)
            self.assertGreater((output / "03-全量研报索引.csv").stat().st_size, 50)
            self.assertEqual(result["input_pdf_count"], 2)
            self.assertEqual(result["report_count"], 2)


if __name__ == "__main__":
    unittest.main()
