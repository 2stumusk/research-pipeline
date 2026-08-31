from __future__ import annotations

import copy
import logging
import os
import tempfile
import textwrap
import unittest
from pathlib import Path

import pymupdf

from research_pipeline.config import AppConfig, load_config
from research_pipeline.pipeline import ResearchPipeline


FAKE_CODEX = r'''#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path

args = sys.argv[1:]
if "--version" in args:
    print("fake-codex 1.0")
    raise SystemExit(0)

def value(flag):
    i = args.index(flag)
    return args[i + 1]

def prompt_path(label, prompt):
    for line in prompt.splitlines():
        if line.startswith(label):
            raw = line[len(label):].strip()
            if not raw:
                break
            p = Path(raw)
            return p if p.is_absolute() else Path.cwd() / p
    raise RuntimeError(f"missing path after {label!r}")

def first_company(cards):
    for card in cards:
        companies = card.get("companies") or []
        if companies:
            return companies[0]
    return {"name": "测试公司", "ticker": "300001"}

schema = Path(value("--output-schema")).name
output = Path(value("--output-last-message"))
prompt = args[-1]
if os.environ.get("FAKE_CODEX_FAIL_SCHEMA") == schema:
    print(f"forced failure for {schema}", file=sys.stderr)
    raise SystemExit(7)
log = os.environ.get("FAKE_CODEX_LOG")
if log:
    with open(log, "a", encoding="utf-8") as h:
        h.write(schema + "\n")

if schema == "triage_batch.schema.json":
    manifest = json.loads(prompt_path("输入清单：", prompt).read_text(encoding="utf-8"))
    reports = []
    for item in manifest["reports"]:
        meta = item["parsed_metadata"]
        company = meta.get("company") or "测试公司"
        ticker = meta.get("ticker") or "300001"
        reports.append({
            "report_id": item["report_id"],
            "institution": meta.get("institution") or "测试券商",
            "report_date": meta.get("report_date") or manifest["run_date"],
            "title": meta.get("title") or item["file_name"],
            "companies": [{"name": company, "ticker": ticker, "market": "CN"}],
            "primary_industry": "光通信",
            "themes": ["光模块", "测试主题"],
            "report_type": "company_update",
            "rating": {"current": "买入", "previous": "买入", "change": "maintain"},
            "target_price": {"current": 100.0, "previous": 90.0, "currency": "CNY", "change_pct": 11.1},
            "core_conclusion": "测试结论：新增数据支持盈利预期改善。",
            "new_information": [{"claim": "新增测试信息", "page": 1, "evidence_type": "institution_view", "impact": "提高收入可见度"}],
            "key_metrics": [{"metric": "收入", "period": "2027E", "value": 100.0, "value_text": "100", "unit": "亿元", "currency": "CNY", "page": 1, "change_direction": "up"}],
            "estimate_changes": [{"metric": "净利润", "period": "2027E", "old_value": 10.0, "new_value": 11.0, "unit": "亿元", "change_pct": 10.0, "page": 1}],
            "catalysts": [{"date_or_window": "未来一季", "event": "订单验证", "affected_assets": [company], "direction": 1, "page": 1}],
            "risks": [{"risk": "需求不及预期", "affected_assets": [company], "severity": "medium", "page": 2}],
            "a_share_mapping": [{"company": company, "ticker": ticker, "relationship": "direct", "logic": "报告主体", "confidence": 90}],
            "delta_from_prior": ["无可用历史卡片，无法比较"],
            "evidence_gaps": [],
            "score_components": {"watchlist_relevance": 20, "novelty": 15, "earnings_valuation_impact": 12, "catalyst_certainty": 10, "consensus_divergence": 5, "evidence_quality": 8, "actionability": 8, "duplicate_penalty": 0, "stale_penalty": 0, "unverified_penalty": 0},
            "direction_score": 1,
            "confidence_score": 82,
            "duplicate_hint": "",
            "recommended_action": "must_read_full",
            "source_pages_used": [1, 2]
        })
    data = {"reports": reports}
elif schema == "clusters.schema.json":
    cards = json.loads(prompt_path("输入文件：", prompt).read_text(encoding="utf-8"))["reports"]
    ids = [c["report_id"] for c in cards]
    first = cards[0]
    company = first_company(cards)
    data = {"clusters": [{
        "cluster_id": "cluster_test_001",
        "event_title": "测试事件聚类",
        "event_date": first["report_date"],
        "primary_theme": "光通信",
        "companies": [company["name"]],
        "report_ids": ids,
        "consensus_points": ["测试共识"],
        "disagreements": [],
        "genuinely_new_information": ["新增测试信息"],
        "best_report_id": ids[0],
        "best_report_reason": "证据最完整",
        "a_share_implications": ["测试映射"],
        "risk_signals": ["需求风险"],
        "catalyst_signals": ["订单验证"],
        "cluster_importance": 82,
        "cluster_direction": 1,
        "confidence": 82
    }], "unclustered_report_ids": []}
elif schema == "deep_dive.schema.json":
    manifest = json.loads(prompt_path("输入清单：", prompt).read_text(encoding="utf-8"))
    report_id = manifest["report_id"]
    data = {
        "report_id": report_id,
        "one_sentence_conclusion": "测试深度结论。",
        "report_core": ["核心一", "核心二"],
        "genuinely_new_information": [{"claim": "新增测试信息", "page": 1, "evidence_type": "institution_view", "impact": "提高收入可见度"}],
        "key_data": [{"metric": "收入", "period": "2027E", "value": 100.0, "value_text": "100", "unit": "亿元", "currency": "CNY", "page": 1, "change_direction": "up"}],
        "argument_chain": [{"step": 1, "claim": "需求改善", "evidence": "订单数据", "page": 1, "weakness": "仍需验证"}],
        "critical_assumptions": [{"assumption": "订单兑现", "why_it_matters": "决定盈利", "failure_signal": "订单延后", "page": 1}],
        "changes_vs_prior": ["首次覆盖"],
        "earnings_impact": "盈利上修。",
        "valuation_impact": "估值小幅提升。",
        "a_share_mapping": [{"company": "测试公司", "ticker": "300001", "relationship": "direct", "logic": "报告主体", "confidence": 90}],
        "catalyst_timeline": [{"date_or_window": "未来一季", "event": "订单验证", "affected_assets": ["测试公司"], "direction": 1, "page": 1}],
        "risks_and_disconfirming_evidence": [{"risk": "需求不及预期", "affected_assets": ["测试公司"], "severity": "medium", "page": 2}],
        "failure_conditions": ["订单延后"],
        "scenarios": [
            {"name": "bull", "conditions": ["超预期"], "earnings_impact": "上修", "valuation_impact": "扩张", "asset_implication": "正面", "probability": 25},
            {"name": "base", "conditions": ["符合预期"], "earnings_impact": "维持", "valuation_impact": "稳定", "asset_implication": "中性偏正面", "probability": 55},
            {"name": "bear", "conditions": ["不及预期"], "earnings_impact": "下修", "valuation_impact": "收缩", "asset_implication": "负面", "probability": 20}
        ],
        "tracking_indicators": [{"indicator": "订单", "frequency": "月度", "threshold_or_signal": "环比增长", "why_it_matters": "验证需求"}],
        "final_judgment": "研究结论待订单验证。",
        "confidence": 82
    }
elif schema == "digest.schema.json":
    inp = json.loads(prompt_path("输入文件：", prompt).read_text(encoding="utf-8"))
    cards = inp["cards"]
    first = cards[0]
    company = first_company(cards)
    data = {
        "executive_view": "测试综合判断。",
        "top_changes": [{"title": "测试变化", "why_it_matters": "改变盈利预期", "affected_assets": [company["name"]], "direction": 1, "confidence": 82, "report_ids": [first["report_id"]]}],
        "risk_alerts": [],
        "earnings_upgrades": [{"company": company["name"], "ticker": company.get("ticker", ""), "metric": "净利润", "period": "2027E", "change": "+10%", "report_id": first["report_id"]}],
        "earnings_downgrades": [],
        "biggest_disagreements": [],
        "watchlist_relevance": ["测试观察池相关"],
        "next_7d_catalysts": [],
        "reading_order": [c["report_id"] for c in cards],
        "data_gaps": []
    }
elif schema == "qc.schema.json":
    data = {"passed": True, "summary": "测试QC通过。", "issues": []}
else:
    raise RuntimeError(f"unknown schema: {schema}")

output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
print(json.dumps(data, ensure_ascii=False))
'''


def create_pdf(path: Path, title: str) -> None:
    doc = pymupdf.open()
    body = (
        f"{title} 核心观点 盈利预测 目标价 评级变化 订单验证 产能扩张 "
        "收入增长 毛利率改善 资本开支 出货量 关键假设 催化剂 风险提示。"
    )
    for i in range(2):
        page = doc.new_page()
        text = f"{title} 第{i+1}页\n" + "\n".join([body] * 10)
        page.insert_textbox(pymupdf.Rect(72, 72, 520, 760), text, fontsize=9)
    doc.save(path)
    doc.close()


class PipelineFakeCodexTests(unittest.TestCase):
    def test_codex_stage_failure_returns_partial_with_outputs(self) -> None:
        project_root = load_config().root
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            fake = tmp_root / "fake_codex.py"
            fake.write_text(FAKE_CODEX, encoding="utf-8")
            fake.chmod(0o755)
            base = load_config()
            data = copy.deepcopy(base.data)
            data["paths"] = {
                "inbox": str(tmp_root / "inbox"),
                "archive": str(tmp_root / "archive"),
                "extracted": str(tmp_root / "extracted"),
                "database": str(tmp_root / "database" / "research.db"),
                "outputs": str(tmp_root / "outputs"),
                "logs": str(tmp_root / "logs"),
                "watchlist": str(tmp_root / "watchlist.csv"),
            }
            data["codex"]["binary"] = str(fake)
            data["codex"]["max_parallel"] = 1
            data["codex"]["retries"] = 0
            data["pipeline"]["deep_dive_n"] = 0
            cfg = AppConfig(project_root, data, tmp_root / "config.yaml")
            cfg.ensure_directories()
            cfg.path("watchlist").write_text(
                "market,ticker,name,holding,priority,theme,notes\n",
                encoding="utf-8",
            )
            source = cfg.path("inbox") / "2026-08-21"
            source.mkdir(parents=True)
            create_pdf(source / "测试券商-失败降级-260821.pdf", "失败降级")

            old_value = os.environ.get("FAKE_CODEX_FAIL_SCHEMA")
            os.environ["FAKE_CODEX_FAIL_SCHEMA"] = "triage_batch.schema.json"
            try:
                result = ResearchPipeline(cfg, logging.getLogger("fake-partial")).run(
                    run_date="2026-08-21",
                    session="0900",
                    deep_dive=False,
                )
            finally:
                if old_value is None:
                    os.environ.pop("FAKE_CODEX_FAIL_SCHEMA", None)
                else:
                    os.environ["FAKE_CODEX_FAIL_SCHEMA"] = old_value
            self.assertEqual(result["status"], "partial")
            self.assertEqual(result["fallback_card_count"], 1)
            self.assertTrue(result["errors"])
            self.assertTrue((Path(result["output_dir"]) / "dashboard.html").exists())
            reused = ResearchPipeline(cfg, logging.getLogger("fake-partial-reuse")).run(
                run_date="2026-08-21",
                session="2100",
                deep_dive=False,
            )
            self.assertEqual(reused["status"], "partial")
            self.assertEqual(reused["fallback_card_count"], 1)
            self.assertTrue(any(item.get("stage") == "triage" for item in reused["errors"]))

    def test_live_path_and_reuse_with_fake_codex(self) -> None:
        project_root = load_config().root
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            fake = tmp_root / "fake_codex.py"
            fake.write_text(FAKE_CODEX, encoding="utf-8")
            fake.chmod(0o755)
            call_log = tmp_root / "calls.log"

            base = load_config()
            data = copy.deepcopy(base.data)
            data["paths"] = {
                "inbox": str(tmp_root / "inbox"),
                "archive": str(tmp_root / "archive"),
                "extracted": str(tmp_root / "extracted"),
                "database": str(tmp_root / "database" / "research.db"),
                "outputs": str(tmp_root / "outputs" / "daily"),
                "logs": str(tmp_root / "logs"),
                "watchlist": str(tmp_root / "watchlist.csv"),
            }
            data["codex"]["binary"] = str(fake)
            data["codex"]["max_parallel"] = 1
            data["codex"]["retries"] = 0
            data["pipeline"]["batch_max_reports"] = 4
            data["pipeline"]["deep_dive_n"] = 1
            data["pipeline"]["min_deep_dive_score"] = 65
            data["pipeline"]["archive_after_success"] = True
            cfg = AppConfig(project_root, data, tmp_root / "config.yaml")
            cfg.ensure_directories()
            cfg.path("watchlist").write_text(
                "market,ticker,name,holding,priority,theme,notes\nCN,600183,生益科技,false,5,PCB/CCL,测试\n",
                encoding="utf-8",
            )
            source = cfg.path("inbox") / "2026-08-21"
            source.mkdir(parents=True)
            create_pdf(source / "高盛-生益科技（600183）：业绩更新-260821.pdf", "生益科技")
            create_pdf(source / "摩根士丹利-光通信行业更新-260821.pdf", "光通信")

            old_log = os.environ.get("FAKE_CODEX_LOG")
            os.environ["FAKE_CODEX_LOG"] = str(call_log)
            try:
                pipeline = ResearchPipeline(cfg, logging.getLogger("fake-live"))
                first = pipeline.run(run_date="2026-08-21", session="0900")
                self.assertEqual(first["status"], "success")
                first_calls = call_log.read_text(encoding="utf-8").splitlines()
                self.assertEqual(first_calls.count("triage_batch.schema.json"), 1)
                self.assertEqual(first_calls.count("clusters.schema.json"), 1)
                self.assertEqual(first_calls.count("deep_dive.schema.json"), 1)
                self.assertEqual(first_calls.count("digest.schema.json"), 1)
                self.assertEqual(first_calls.count("qc.schema.json"), 1)
                self.assertEqual(first["archive_copy_count"], 2)
                self.assertEqual(len(list((cfg.path("archive") / "2026-08-21").glob("*.pdf"))), 2)
                self.assertEqual(len(list(source.glob("*.pdf"))), 2)

                second = pipeline.run(run_date="2026-08-21", session="2100")
                self.assertEqual(second["status"], "success")
                all_calls = call_log.read_text(encoding="utf-8").splitlines()
                second_calls = all_calls[len(first_calls):]
                self.assertNotIn("triage_batch.schema.json", second_calls)
                self.assertNotIn("deep_dive.schema.json", second_calls)
                self.assertEqual(second_calls.count("clusters.schema.json"), 1)
                self.assertEqual(second_calls.count("digest.schema.json"), 1)
                self.assertEqual(second_calls.count("qc.schema.json"), 1)
                self.assertTrue((Path(second["output_dir"]) / "dashboard.html").exists())
            finally:
                if old_log is None:
                    os.environ.pop("FAKE_CODEX_LOG", None)
                else:
                    os.environ["FAKE_CODEX_LOG"] = old_log


if __name__ == "__main__":
    unittest.main()
