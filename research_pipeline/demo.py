from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import AppConfig
from .render import (
    render_clusters,
    render_dashboard,
    render_deep_dive_markdown,
    render_index_csv,
    render_one_pager,
    render_qc,
    render_risk_catalyst,
    render_top10,
    write_machine_outputs,
)
from .utils import atomic_write_text


def build_demo(config: AppConfig) -> Path:
    output_dir = config.root / "outputs" / "demo"
    output_dir.mkdir(parents=True, exist_ok=True)
    run_meta = {
        "run_id": "demo",
        "run_date": "2026-08-21",
        "session": "0900",
        "started_at": "2026-08-21T01:00:00+00:00",
        "completed_at": "2026-08-21T01:10:00+00:00",
        "report_count": 5,
        "cluster_count": 3,
        "deep_dive_count": 1,
        "dry_run": True,
        "errors": [],
    }
    cards: list[dict[str, Any]] = [
        {
            "report_id": "demo_optics_1",
            "institution": "示例券商A",
            "report_date": "2026-08-21",
            "title": "1.6T光模块需求上修与材料瓶颈",
            "companies": [{"name": "中际旭创", "ticker": "300308", "market": "CN"}],
            "primary_industry": "光通信",
            "themes": ["1.6T", "光模块", "AI资本开支"],
            "report_type": "industry_update",
            "rating": {"current": "买入", "previous": "买入", "change": "maintain"},
            "target_price": {"current": 180.0, "previous": 165.0, "currency": "CNY", "change_pct": 9.1},
            "core_conclusion": "需求上修主要来自交付节奏前移，但高功率CW与EML供应仍是收入兑现的关键约束。",
            "new_information": [
                {"claim": "1.6T批量交付时间提前一个季度", "page": 4, "evidence_type": "institution_view", "impact": "上修2027年收入可见度"},
                {"claim": "高功率CW供应缺口延续至2027年上半年", "page": 7, "evidence_type": "management_statement", "impact": "限制短期出货弹性"},
            ],
            "key_metrics": [],
            "estimate_changes": [{"metric": "净利润", "period": "2027E", "old_value": 90.0, "new_value": 99.0, "unit": "亿元", "change_pct": 10.0, "page": 5}],
            "catalysts": [{"date_or_window": "2026Q4", "event": "1.6T规模交付", "affected_assets": ["中际旭创", "新易盛"], "direction": 2, "page": 4}],
            "risks": [{"risk": "光芯片和激光器供应不及预期", "affected_assets": ["光模块链"], "severity": "high", "page": 7}],
            "a_share_mapping": [{"company": "天孚通信", "ticker": "300394", "relationship": "direct", "logic": "高速光器件价值量提升", "confidence": 82}],
            "delta_from_prior": ["2027E净利润上调10%", "量产时间由2027Q1提前至2026Q4"],
            "evidence_gaps": [],
            "score_components": {"watchlist_relevance": 20, "novelty": 18, "earnings_valuation_impact": 14, "catalyst_certainty": 13, "consensus_divergence": 7, "evidence_quality": 8, "actionability": 9, "duplicate_penalty": 0, "stale_penalty": 0, "unverified_penalty": 2},
            "importance_score": 87,
            "priority_score": 87,
            "direction_score": 2,
            "confidence_score": 84,
            "recommended_action": "must_read_full",
            "source_pages_used": [4, 5, 7],
            "duplicate_hint": "",
            "watchlist_matches": [],
            "event_title": "1.6T交付前移与材料约束",
            "source_file": "",
            "scanned_pages": [],
        },
        {
            "report_id": "demo_memory_1",
            "institution": "示例券商B",
            "report_date": "2026-08-21",
            "title": "HBM4需求强劲但先进封装良率决定供给",
            "companies": [{"name": "SK海力士", "ticker": "000660.KS", "market": "KR"}],
            "primary_industry": "存储",
            "themes": ["HBM4", "DRAM", "先进封装"],
            "report_type": "company_update",
            "rating": {"current": "买入", "previous": "买入", "change": "maintain"},
            "target_price": {"current": 520000, "previous": 500000, "currency": "KRW", "change_pct": 4.0},
            "core_conclusion": "需求并非主要矛盾，供给弹性取决于TSV、键合和良率爬坡，价格维持强势。",
            "new_information": [{"claim": "HBM4良率爬坡慢于晶圆投入增长", "page": 6, "evidence_type": "institution_view", "impact": "支持价格和毛利率"}],
            "key_metrics": [], "estimate_changes": [],
            "catalysts": [{"date_or_window": "未来一季", "event": "客户认证更新", "affected_assets": ["HBM供应链"], "direction": 2, "page": 8}],
            "risks": [{"risk": "竞争对手认证进度快于预期", "affected_assets": ["SK海力士"], "severity": "medium", "page": 9}],
            "a_share_mapping": [{"company": "通富微电", "ticker": "002156", "relationship": "indirect", "logic": "先进封装景气映射", "confidence": 55}],
            "delta_from_prior": ["供给约束由晶圆产能转向封装良率"], "evidence_gaps": [],
            "score_components": {}, "importance_score": 78, "priority_score": 78, "direction_score": 2, "confidence_score": 80,
            "recommended_action": "read_summary", "source_pages_used": [6,8,9], "duplicate_hint": "", "watchlist_matches": [], "event_title": "HBM4供给约束", "source_file": "", "scanned_pages": [],
        },
        {
            "report_id": "demo_macro_1",
            "institution": "示例券商C",
            "report_date": "2026-08-21",
            "title": "日元利差交易波动风险上升",
            "companies": [], "primary_industry": "宏观", "themes": ["日元", "利差交易", "全球流动性"], "report_type": "macro",
            "rating": {"current": "", "previous": "", "change": "unknown"}, "target_price": {"current": None, "previous": None, "currency": "", "change_pct": None},
            "core_conclusion": "日本政策预期与美债波动叠加，可能造成全球科技资产风险预算阶段性收缩。",
            "new_information": [{"claim": "日元波动率和跨币种基差同步走高", "page": 3, "evidence_type": "reported_fact", "impact": "提升去杠杆风险"}],
            "key_metrics": [], "estimate_changes": [], "catalysts": [],
            "risks": [{"risk": "日元快速升值触发carry unwind", "affected_assets": ["全球科技股"], "severity": "critical", "page": 5}],
            "a_share_mapping": [{"company": "A股科技成长", "ticker": "", "relationship": "negative", "logic": "海外风险预算收缩可能压制估值", "confidence": 70}],
            "delta_from_prior": ["风险权重由美联储转向日本政策与日元波动"], "evidence_gaps": [], "score_components": {},
            "importance_score": 82, "priority_score": 82, "direction_score": -2, "confidence_score": 76, "recommended_action": "must_read_full", "source_pages_used": [3,5], "duplicate_hint": "", "watchlist_matches": [], "event_title": "日元carry风险", "source_file": "", "scanned_pages": [],
        },
        {
            "report_id": "demo_pcb_1", "institution": "示例券商D", "report_date": "2026-08-21", "title": "AI PCB高阶材料需求延续", "companies": [{"name": "生益科技", "ticker": "600183", "market": "CN"}], "primary_industry": "PCB/CCL", "themes": ["M8", "HVLP", "AI服务器"], "report_type": "company_update", "rating": {"current": "买入", "previous": "买入", "change": "maintain"}, "target_price": {"current": 55, "previous": 50, "currency": "CNY", "change_pct": 10}, "core_conclusion": "产品结构改善延续，但市场已部分计价，新增信息主要是产线良率改善。", "new_information": [{"claim": "高阶材料良率继续改善", "page": 5, "evidence_type": "management_statement", "impact": "支撑毛利率"}], "key_metrics": [], "estimate_changes": [], "catalysts": [], "risks": [], "a_share_mapping": [], "delta_from_prior": ["盈利预测未上修，目标价主要来自估值倍数"], "evidence_gaps": [], "score_components": {}, "importance_score": 68, "priority_score": 68, "direction_score": 1, "confidence_score": 73, "recommended_action": "read_summary", "source_pages_used": [5], "duplicate_hint": "", "watchlist_matches": [], "event_title": "AI PCB材料升级", "source_file": "", "scanned_pages": []
        },
        {
            "report_id": "demo_repeat_1", "institution": "示例券商E", "report_date": "2026-08-21", "title": "重复事件简评", "companies": [{"name": "中际旭创", "ticker": "300308", "market": "CN"}], "primary_industry": "光通信", "themes": ["1.6T"], "report_type": "event_comment", "rating": {"current": "买入", "previous": "买入", "change": "maintain"}, "target_price": {"current": 178, "previous": 170, "currency": "CNY", "change_pct": 4.7}, "core_conclusion": "观点与市场共识接近，缺乏新增数据。", "new_information": [], "key_metrics": [], "estimate_changes": [], "catalysts": [], "risks": [], "a_share_mapping": [], "delta_from_prior": [], "evidence_gaps": ["缺乏新增一手证据"], "score_components": {}, "importance_score": 42, "priority_score": 42, "direction_score": 1, "confidence_score": 60, "recommended_action": "index_only", "source_pages_used": [], "duplicate_hint": "与demo_optics_1高度重复", "watchlist_matches": [], "event_title": "1.6T交付前移与材料约束", "source_file": "", "scanned_pages": []
        },
    ]
    clusters = [
        {"cluster_id": "demo_cluster_1", "event_title": "1.6T交付前移与材料约束", "event_date": "2026-08-21", "primary_theme": "光通信", "companies": ["中际旭创"], "report_ids": ["demo_optics_1", "demo_repeat_1"], "consensus_points": ["1.6T需求保持强劲", "材料供给限制短期出货"], "disagreements": [{"topic": "量产提前幅度", "positions": [{"institution": "示例券商A", "view": "提前一个季度", "report_id": "demo_optics_1"}, {"institution": "示例券商E", "view": "未给出明确时间", "report_id": "demo_repeat_1"}], "investment_relevance": "决定2027年盈利上修幅度"}], "genuinely_new_information": ["高功率CW供应缺口延续至2027年上半年"], "best_report_id": "demo_optics_1", "best_report_reason": "新增数据和页码最完整", "a_share_implications": ["光模块龙头收入可见度提升", "上游高功率光源仍是瓶颈"], "risk_signals": ["材料供应不足"], "catalyst_signals": ["2026Q4规模交付"], "cluster_importance": 90, "cluster_direction": 2, "confidence": 84},
        {"cluster_id": "demo_cluster_2", "event_title": "HBM4供给约束", "event_date": "2026-08-21", "primary_theme": "HBM", "companies": ["SK海力士"], "report_ids": ["demo_memory_1"], "consensus_points": ["需求强劲，供给由封装良率决定"], "disagreements": [], "genuinely_new_information": ["良率成为主要约束"], "best_report_id": "demo_memory_1", "best_report_reason": "唯一报告", "a_share_implications": ["先进封装景气维持"], "risk_signals": [], "catalyst_signals": ["客户认证"], "cluster_importance": 78, "cluster_direction": 2, "confidence": 80},
        {"cluster_id": "demo_cluster_3", "event_title": "日元carry风险", "event_date": "2026-08-21", "primary_theme": "全球流动性", "companies": [], "report_ids": ["demo_macro_1"], "consensus_points": ["日元波动可能触发去杠杆"], "disagreements": [], "genuinely_new_information": ["跨币种基差同步走高"], "best_report_id": "demo_macro_1", "best_report_reason": "唯一报告", "a_share_implications": ["科技成长估值可能受压"], "risk_signals": ["carry unwind"], "catalyst_signals": [], "cluster_importance": 82, "cluster_direction": -2, "confidence": 76},
    ]
    digest = {
        "executive_view": "今日增量信息集中在AI硬件交付前移与全球流动性风险上升：基本面仍强，但短期风险预算可能因日元carry波动收缩。",
        "top_changes": [
            {"title": "1.6T交付节奏前移", "why_it_matters": "提高2027年收入可见度，但材料瓶颈限制短期弹性。", "affected_assets": ["中际旭创", "新易盛", "天孚通信"], "direction": 2, "confidence": 84, "report_ids": ["demo_optics_1"]},
            {"title": "HBM4供给约束转向封装良率", "why_it_matters": "价格和毛利率支撑强于单纯晶圆扩产逻辑。", "affected_assets": ["SK海力士", "先进封装链"], "direction": 2, "confidence": 80, "report_ids": ["demo_memory_1"]},
            {"title": "日元carry去杠杆风险抬升", "why_it_matters": "可能压缩全球科技资产风险预算。", "affected_assets": ["A股科技成长", "全球科技股"], "direction": -2, "confidence": 76, "report_ids": ["demo_macro_1"]},
        ],
        "risk_alerts": [{"title": "日元快速升值触发去杠杆", "why_it_matters": "流动性冲击可能先于基本面反映。", "affected_assets": ["全球科技股"], "direction": -2, "confidence": 76, "report_ids": ["demo_macro_1"]}],
        "earnings_upgrades": [{"company": "中际旭创", "ticker": "300308", "metric": "净利润", "period": "2027E", "change": "+10.0%", "report_id": "demo_optics_1"}],
        "earnings_downgrades": [],
        "biggest_disagreements": ["1.6T量产提前幅度及高功率CW供应缓解时间"],
        "watchlist_relevance": ["中际旭创：交付前移但材料约束仍在", "生益科技：目标价上调主要来自估值而非盈利"],
        "next_7d_catalysts": [],
        "reading_order": ["demo_optics_1", "demo_macro_1", "demo_memory_1", "demo_pcb_1", "demo_repeat_1"],
        "data_gaps": ["高功率CW实际扩产和良率数据仍需验证"],
    }
    deep = {
        "report_id": "demo_optics_1", "one_sentence_conclusion": "需求前移构成盈利上修，但材料供给决定兑现速度。", "report_core": ["1.6T量产提前", "2027E盈利上修", "高功率CW和EML仍短缺"], "genuinely_new_information": cards[0]["new_information"], "key_data": [], "argument_chain": [{"step": 1, "claim": "云厂商资本开支上修", "evidence": "客户订单与交付计划前移", "page": 4, "weakness": "订单可能因材料短缺延后"}, {"step": 2, "claim": "模块收入和利润上修", "evidence": "量产时间提前且产品价值量提升", "page": 5, "weakness": "价格下降可能抵消部分产品升级"}], "critical_assumptions": [{"assumption": "高功率CW供应按计划改善", "why_it_matters": "决定出货能否兑现", "failure_signal": "交付再次延后或毛利率不升", "page": 7}], "changes_vs_prior": cards[0]["delta_from_prior"], "earnings_impact": "2027E净利润上调10%，主要来自出货提前。", "valuation_impact": "目标价同时受到盈利上修和估值倍数小幅提升影响。", "a_share_mapping": cards[0]["a_share_mapping"], "catalyst_timeline": cards[0]["catalysts"], "risks_and_disconfirming_evidence": cards[0]["risks"], "failure_conditions": ["1.6T客户部署延后", "高功率光源良率未改善", "价格下降快于成本下降"], "scenarios": [{"name": "bull", "conditions": ["量产按期且材料缓解"], "earnings_impact": "盈利进一步上修", "valuation_impact": "高估值维持", "asset_implication": "龙头与上游器件共同受益", "probability": 25}, {"name": "base", "conditions": ["交付前移但受材料限制"], "earnings_impact": "盈利按当前上修兑现", "valuation_impact": "估值震荡", "asset_implication": "龙头优于纯概念标的", "probability": 55}, {"name": "bear", "conditions": ["供应瓶颈延续且价格下行"], "earnings_impact": "盈利下修", "valuation_impact": "估值压缩", "asset_implication": "板块回撤", "probability": 20}], "tracking_indicators": [{"indicator": "1.6T月度出货", "frequency": "月度", "threshold_or_signal": "持续环比增长", "why_it_matters": "验证量产前移"}, {"indicator": "高功率CW交期", "frequency": "月度", "threshold_or_signal": "交期缩短", "why_it_matters": "验证供应缓解"}], "final_judgment": "中期逻辑强化，但短期交易应重点监控供应瓶颈与估值消化。", "confidence": 84
    }
    deep_dir = output_dir / "deep_dive"
    deep_dir.mkdir(exist_ok=True)
    deep_path = deep_dir / "demo-optics.md"
    atomic_write_text(deep_path, render_deep_dive_markdown(deep, cards[0], clusters[0]))
    deep_paths = {"demo_optics_1": deep_path}
    qc = {"passed": True, "summary": "演示数据格式检查通过。", "issues": []}
    write_machine_outputs(output_dir, run_meta=run_meta, cards=cards, clusters=clusters, deep_dives={"demo_optics_1": deep}, digest=digest, qc=qc)
    render_one_pager(output_dir, run_meta, digest, cards, clusters)
    render_top10(output_dir, cards, deep_paths, 10)
    render_clusters(output_dir, clusters)
    render_index_csv(output_dir, cards)
    render_risk_catalyst(output_dir, cards, digest)
    render_qc(output_dir, qc)
    render_dashboard(output_dir, run_meta, digest, cards, clusters, 10)
    return output_dir
