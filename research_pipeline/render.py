from __future__ import annotations

import csv
import html
import json
import os
from pathlib import Path
from typing import Any

from .config import AppConfig
from .utils import atomic_write_text, slugify, write_json


def direction_label(value: int) -> str:
    labels = {
        -3: "重大负面",
        -2: "明确负面",
        -1: "边际负面",
        0: "中性",
        1: "边际正面",
        2: "明确正面",
        3: "显著正面",
    }
    return labels.get(int(value), "中性")


def action_label(value: str) -> str:
    return {
        "must_read_full": "必须读原文",
        "read_summary": "重点摘要",
        "theme_only": "主题汇总",
        "index_only": "仅保留索引",
    }.get(value, value or "仅保留索引")


def _company_text(card: dict[str, Any]) -> str:
    values = []
    for company in card.get("companies", []) or []:
        name = str(company.get("name", "")).strip()
        ticker = str(company.get("ticker", "")).strip()
        if name or ticker:
            values.append(f"{name}（{ticker}）" if name and ticker else name or ticker)
    return "、".join(values) or "—"


def _md_list(items: list[str], empty: str = "无") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def render_deep_dive_markdown(
    deep: dict[str, Any], card: dict[str, Any], cluster: dict[str, Any] | None = None
) -> str:
    lines = [
        f"# 深度分析：{card.get('title', '')}",
        "",
        f"> 机构：{card.get('institution', '—')}｜日期：{card.get('report_date', '—')}｜公司：{_company_text(card)}",
        f"> 重要性：{card.get('importance_score', 0)}｜方向：{direction_label(card.get('direction_score', 0))}｜置信度：{card.get('confidence_score', 0)}",
        "",
        "## 一句话结论",
        "",
        deep.get("one_sentence_conclusion", ""),
        "",
        "## 报告核心内容",
        "",
        _md_list(deep.get("report_core", [])),
        "",
        "## 真正新增信息",
        "",
    ]
    for item in deep.get("genuinely_new_information", []) or []:
        page = item.get("page")
        page_text = f"（PDF第{page}页）" if page else "（页码待核实）"
        lines.append(f"- **{item.get('claim', '')}** {page_text}：{item.get('impact', '')}")

    lines.extend(["", "## 关键数据", ""])
    if deep.get("key_data"):
        lines.extend(
            [
                "| 指标 | 期间 | 数值 | 单位/币种 | 变化 | 页码 |",
                "|---|---|---:|---|---|---:|",
            ]
        )
        for item in deep["key_data"]:
            value = item.get("value_text") or item.get("value")
            unit = "/".join(x for x in [item.get("unit", ""), item.get("currency", "")] if x)
            lines.append(
                f"| {item.get('metric','')} | {item.get('period','')} | {value if value is not None else '—'} | {unit or '—'} | {item.get('change_direction','')} | {item.get('page') or '—'} |"
            )
    else:
        lines.append("- 无可可靠提取的关键数据。")

    lines.extend(["", "## 论据与推理链", ""])
    for step in deep.get("argument_chain", []) or []:
        page = f"PDF第{step.get('page')}页" if step.get("page") else "页码待核实"
        lines.append(
            f"{step.get('step', '')}. **{step.get('claim', '')}**  \n"
            f"   证据：{step.get('evidence', '')}（{page}）  \n"
            f"   薄弱点：{step.get('weakness', '') or '未识别'}"
        )

    lines.extend(["", "## 关键假设及脆弱点", ""])
    for item in deep.get("critical_assumptions", []) or []:
        lines.append(
            f"- **{item.get('assumption','')}**：{item.get('why_it_matters','')}；失效信号：{item.get('failure_signal','')}。"
        )

    lines.extend(
        [
            "",
            "## 相对历史观点的变化",
            "",
            _md_list(deep.get("changes_vs_prior", []), "无可用历史比较"),
            "",
            "## 盈利与估值影响",
            "",
            f"**盈利：** {deep.get('earnings_impact','')}\n\n**估值：** {deep.get('valuation_impact','')}",
            "",
            "## A股产业链映射",
            "",
        ]
    )
    for item in deep.get("a_share_mapping", []) or []:
        lines.append(
            f"- **{item.get('company','')}（{item.get('ticker','')}）**｜{item.get('relationship','')}｜置信度{item.get('confidence',0)}：{item.get('logic','')}"
        )

    lines.extend(["", "## 催化时间表", ""])
    for item in deep.get("catalyst_timeline", []) or []:
        lines.append(
            f"- **{item.get('date_or_window','')}**：{item.get('event','')}；方向{item.get('direction',0)}；页码{item.get('page') or '待核实'}。"
        )

    lines.extend(["", "## 风险、反证与失效条件", ""])
    for item in deep.get("risks_and_disconfirming_evidence", []) or []:
        lines.append(f"- **{item.get('severity','')}**：{item.get('risk','')}（页码{item.get('page') or '待核实'}）")
    lines.append("")
    lines.append(_md_list(deep.get("failure_conditions", []), "未识别明确失效条件"))

    lines.extend(["", "## 三情景", ""])
    for scenario in deep.get("scenarios", []) or []:
        lines.append(f"### {scenario.get('name','').upper()}｜概率 {scenario.get('probability',0)}%")
        lines.append(_md_list(scenario.get("conditions", [])))
        lines.append(f"\n- 盈利影响：{scenario.get('earnings_impact','')}")
        lines.append(f"- 估值影响：{scenario.get('valuation_impact','')}")
        lines.append(f"- 资产含义：{scenario.get('asset_implication','')}")
        lines.append("")

    lines.extend(["## 后续跟踪指标", ""])
    for item in deep.get("tracking_indicators", []) or []:
        lines.append(
            f"- **{item.get('indicator','')}**｜{item.get('frequency','')}｜信号：{item.get('threshold_or_signal','')}｜意义：{item.get('why_it_matters','')}"
        )

    if cluster:
        lines.extend(
            [
                "",
                "## 所属事件簇",
                "",
                f"- 事件：{cluster.get('event_title','')}",
                f"- 覆盖报告：{len(cluster.get('report_ids', []))}份",
                f"- 最佳原始报告：{cluster.get('best_report_id','')}",
            ]
        )
    lines.extend(
        [
            "",
            "## 最终判断",
            "",
            deep.get("final_judgment", ""),
            "",
            f"> 深度分析置信度：{deep.get('confidence',0)}。仅用于研究整理，不构成投资建议。",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_one_pager(
    output_dir: Path,
    run_meta: dict[str, Any],
    digest: dict[str, Any],
    cards: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
) -> Path:
    cards_by_id = {card.get("report_id", ""): card for card in cards}

    def evidence_reference(report_ids: list[str]) -> str:
        references: list[str] = []
        for report_id in report_ids:
            card = cards_by_id.get(report_id, {})
            institution = str(card.get("institution", "")).strip() or "机构未知"
            pages = sorted(
                {
                    int(page)
                    for page in (card.get("source_pages_used", []) or [])
                    if isinstance(page, (int, float)) and int(page) > 0
                }
            )
            page_text = "、".join(str(page) for page in pages) if pages else "【未获取到】"
            references.append(f"{institution}｜{report_id}｜PDF第{page_text}页")
        return "；".join(references) or "【未获取到】"

    def estimate_reference(item: dict[str, Any]) -> str:
        report_id = str(item.get("report_id", ""))
        card = cards_by_id.get(report_id, {})
        pages: set[int] = set()
        item_metric = str(item.get("metric", ""))
        item_period = str(item.get("period", ""))
        for estimate in card.get("estimate_changes", []) or []:
            estimate_metric = str(estimate.get("metric", ""))
            if (
                (
                    estimate_metric == item_metric
                    or item_metric in estimate_metric
                    or estimate_metric in item_metric
                )
                and (
                    str(estimate.get("period", "")) == item_period
                    or str(estimate.get("period", "")) in item_period
                )
                and isinstance(estimate.get("page"), (int, float))
            ):
                pages.add(int(estimate["page"]))
        institution = str(card.get("institution", "")).strip() or "机构未知"
        page_text = "、".join(str(page) for page in sorted(pages) if page > 0) or "【未获取到】"
        return f"{institution}｜{report_id}｜PDF第{page_text}页"

    lines = [
        f"# {run_meta['run_date']} {run_meta['session']}｜今日研报一页纸",
        "",
        f"> 共处理 {len(cards)} 份研报，形成 {len(clusters)} 个事件簇。",
        "",
        "## 总体判断",
        "",
        digest.get("executive_view", "暂无综合判断。"),
        "",
        "## 今天最重要的变化",
        "",
    ]
    for index, item in enumerate(digest.get("top_changes", []) or [], 1):
        assets = "、".join(item.get("affected_assets", [])) or "未指定"
        lines.append(
            f"{index}. **{item.get('title','')}**｜{direction_label(item.get('direction',0))}｜置信度{item.get('confidence',0)}  \n"
            f"   {item.get('why_it_matters','')}  \n"
            f"   影响：{assets}  \n"
            f"   证据：{evidence_reference(item.get('report_ids', []) or [])}"
        )
    lines.extend(["", "## 风险警报", ""])
    for item in digest.get("risk_alerts", []) or []:
        lines.append(
            f"- **{item.get('title','')}**｜{direction_label(item.get('direction',0))}｜置信度{item.get('confidence',0)}：{item.get('why_it_matters','')}  \n"
            f"  证据：{evidence_reference(item.get('report_ids', []) or [])}"
        )
    if not digest.get("risk_alerts"):
        lines.append("- 暂无达到高优先级的新增风险。")

    lines.extend(["", "## 盈利预测变化", "", "### 上调"])
    lines.append(
        _md_list(
            [
                f"{x.get('company','')}（{x.get('ticker','')}）｜{x.get('period','')} {x.get('metric','')}：{x.get('change','')}｜{estimate_reference(x)}"
                for x in digest.get("earnings_upgrades", []) or []
            ],
            "无明确上调",
        )
    )
    lines.extend(["", "### 下调"])
    lines.append(
        _md_list(
            [
                f"{x.get('company','')}（{x.get('ticker','')}）｜{x.get('period','')} {x.get('metric','')}：{x.get('change','')}｜{estimate_reference(x)}"
                for x in digest.get("earnings_downgrades", []) or []
            ],
            "无明确下调",
        )
    )

    lines.extend(
        [
            "",
            "## 机构分歧最大的主题",
            "",
            _md_list(digest.get("biggest_disagreements", []), "暂无显著分歧"),
            "",
            "## 与观察池/持仓最相关",
            "",
            _md_list(digest.get("watchlist_relevance", []), "暂无高相关新增信息"),
            "",
            "## 未来7天催化",
            "",
        ]
    )
    for item in digest.get("next_7d_catalysts", []) or []:
        lines.append(
            f"- **{item.get('date_or_window','')}**：{item.get('event','')}；影响{('、'.join(item.get('affected_assets', [])) or '未指定')}；方向{item.get('direction',0)}。"
        )
    if not digest.get("next_7d_catalysts"):
        lines.append("- 未提取到明确的未来7天催化。")

    lines.extend(["", "## 待读与待核实", "", _md_list(digest.get("data_gaps", []), "无重大证据缺口")])
    path = output_dir / "00-今日研报一页纸.md"
    atomic_write_text(path, "\n".join(lines).strip() + "\n")
    return path


def render_top10(
    output_dir: Path,
    cards: list[dict[str, Any]],
    deep_paths: dict[str, Path],
    top_n: int,
) -> Path:
    ordered = sorted(cards, key=lambda c: (c.get("priority_score", 0), c.get("confidence_score", 0)), reverse=True)[:top_n]
    lines = ["# 今日必读 Top 10", "", "## 排名总览", "", "| 排名 | 报告 | 机构 | 重要性 | 方向 | 置信度 | 动作 |", "|---:|---|---|---:|---|---:|---|"]
    for idx, card in enumerate(ordered, 1):
        lines.append(
            f"| {idx} | {card.get('title','')} | {card.get('institution','')} | {card.get('importance_score',0)} | {direction_label(card.get('direction_score',0))} | {card.get('confidence_score',0)} | {action_label(card.get('recommended_action',''))} |"
        )

    for idx, card in enumerate(ordered, 1):
        lines.extend(
            [
                "",
                f"## {idx}. {card.get('title','')}",
                "",
                f"> 机构：{card.get('institution','—')}｜日期：{card.get('report_date','—')}｜公司：{_company_text(card)}",
                f"> 重要性：{card.get('importance_score',0)}｜优先级：{card.get('priority_score',0)}｜方向：{direction_label(card.get('direction_score',0))}｜置信度：{card.get('confidence_score',0)}",
                "",
                card.get("core_conclusion", ""),
                "",
                "**真正新增：**",
            ]
        )
        for item in (card.get("new_information", []) or [])[:5]:
            lines.append(f"- {item.get('claim','')}（PDF第{item.get('page') or '待核实'}页）")
        if not card.get("new_information"):
            lines.append("- 未识别到高置信度新增信息。")
        lines.extend(["", "**相对历史变化：**", _md_list((card.get("delta_from_prior", []) or [])[:5], "无可用历史比较")])
        risk_items = [x.get("risk", "") for x in (card.get("risks", []) or [])[:4] if x.get("risk")]
        lines.extend(["", "**主要风险：**", _md_list(risk_items, "原文未披露或未提取")])
        if card["report_id"] in deep_paths:
            rel = os.path.relpath(deep_paths[card["report_id"]], output_dir)
            lines.extend(["", f"[打开该报告深度分析]({rel})"])
        source = card.get("source_file", "")
        if source:
            lines.extend(["", f"原始文件：`{source}`"])
    path = output_dir / "01-今日必读Top10.md"
    atomic_write_text(path, "\n".join(lines).strip() + "\n")
    return path


def render_clusters(output_dir: Path, clusters: list[dict[str, Any]]) -> Path:
    lines = ["# 主题共识与分歧", ""]
    ordered = sorted(clusters, key=lambda c: c.get("cluster_importance", 0), reverse=True)
    if not ordered:
        lines.append("本次未形成可靠事件聚类。")
    for idx, cluster in enumerate(ordered, 1):
        lines.extend(
            [
                f"## {idx}. {cluster.get('event_title','')}",
                "",
                f"> 主题：{cluster.get('primary_theme','')}｜覆盖{len(cluster.get('report_ids', []))}份｜重要性{cluster.get('cluster_importance',0)}｜{direction_label(cluster.get('cluster_direction',0))}｜置信度{cluster.get('confidence',0)}",
                "",
                "### 共识",
                "",
                _md_list(cluster.get("consensus_points", [])),
                "",
                "### 分歧",
                "",
            ]
        )
        if cluster.get("disagreements"):
            for item in cluster["disagreements"]:
                lines.append(f"- **{item.get('topic','')}**：{item.get('investment_relevance','')}")
                for pos in item.get("positions", []):
                    lines.append(f"  - {pos.get('institution','')}：{pos.get('view','')}")
        else:
            lines.append("- 暂无实质分歧。")
        lines.extend(
            [
                "",
                "### 真正新增证据",
                "",
                _md_list(cluster.get("genuinely_new_information", []), "无高置信度新增证据"),
                "",
                "### A股含义",
                "",
                _md_list(cluster.get("a_share_implications", []), "暂无明确映射"),
                "",
                f"**最佳原始报告：** `{cluster.get('best_report_id','')}` — {cluster.get('best_report_reason','')}",
                "",
            ]
        )
    path = output_dir / "02-主题共识与分歧.md"
    atomic_write_text(path, "\n".join(lines).strip() + "\n")
    return path


def render_index_csv(output_dir: Path, cards: list[dict[str, Any]], encoding: str = "utf-8-sig") -> Path:
    path = output_dir / "03-全量研报索引.csv"
    fields = [
        "report_id",
        "机构",
        "日期",
        "标题",
        "公司",
        "行业",
        "主题",
        "重要性",
        "优先级",
        "方向分",
        "方向",
        "置信度",
        "动作",
        "评级",
        "目标价",
        "币种",
        "事件簇",
        "核心结论",
        "证据缺口",
        "扫描页",
        "原始文件",
    ]
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for card in sorted(cards, key=lambda c: c.get("priority_score", 0), reverse=True):
            target = card.get("target_price", {}) or {}
            rating = card.get("rating", {}) or {}
            writer.writerow(
                {
                    "report_id": card.get("report_id", ""),
                    "机构": card.get("institution", ""),
                    "日期": card.get("report_date", ""),
                    "标题": card.get("title", ""),
                    "公司": _company_text(card),
                    "行业": card.get("primary_industry", ""),
                    "主题": " / ".join(card.get("themes", []) or []),
                    "重要性": card.get("importance_score", 0),
                    "优先级": card.get("priority_score", 0),
                    "方向分": card.get("direction_score", 0),
                    "方向": direction_label(card.get("direction_score", 0)),
                    "置信度": card.get("confidence_score", 0),
                    "动作": action_label(card.get("recommended_action", "")),
                    "评级": rating.get("current", ""),
                    "目标价": target.get("current", ""),
                    "币种": target.get("currency", ""),
                    "事件簇": card.get("event_title", ""),
                    "核心结论": card.get("core_conclusion", ""),
                    "证据缺口": "；".join(card.get("evidence_gaps", []) or []),
                    "扫描页": ",".join(map(str, card.get("scanned_pages", []) or [])),
                    "原始文件": card.get("source_file", ""),
                }
            )
    return path


def render_risk_catalyst(output_dir: Path, cards: list[dict[str, Any]], digest: dict[str, Any]) -> Path:
    lines = ["# 风险与催化跟踪", "", "## 风险", "", "| 级别 | 风险 | 相关报告 | 页码 |", "|---|---|---|---:|"]
    risk_rows = []
    for card in cards:
        for risk in card.get("risks", []) or []:
            risk_rows.append((risk.get("severity", "medium"), risk.get("risk", ""), card.get("report_id", ""), risk.get("page")))
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    for severity, risk, report_id, page in sorted(risk_rows, key=lambda x: severity_order.get(x[0], 0), reverse=True):
        lines.append(f"| {severity} | {risk} | {report_id} | {page or '—'} |")
    if not risk_rows:
        lines.append("| — | 未提取到明确风险 | — | — |")

    lines.extend(["", "## 催化", "", "| 时间 | 事件 | 影响资产 | 方向 | 来源 | 页码 |", "|---|---|---|---:|---|---:|"])
    catalyst_rows = []
    for card in cards:
        for item in card.get("catalysts", []) or []:
            catalyst_rows.append(
                (
                    item.get("date_or_window", ""),
                    item.get("event", ""),
                    "、".join(item.get("affected_assets", []) or []),
                    item.get("direction", 0),
                    card.get("report_id", ""),
                    item.get("page"),
                )
            )
    for row in catalyst_rows:
        lines.append(f"| {row[0]} | {row[1]} | {row[2] or '—'} | {row[3]} | {row[4]} | {row[5] or '—'} |")
    if not catalyst_rows:
        lines.append("| — | 未提取到明确催化 | — | 0 | — | — |")
    path = output_dir / "04-风险与催化跟踪.md"
    atomic_write_text(path, "\n".join(lines).strip() + "\n")
    return path


def render_qc(output_dir: Path, qc: dict[str, Any]) -> Path:
    lines = ["# 质量检查", "", f"> 结论：{'通过' if qc.get('passed') else '存在待修正问题'}", "", qc.get("summary", ""), ""]
    if qc.get("issues"):
        lines.extend(["| 严重级别 | 类别 | 报告 | 文件 | 问题 | 建议 |", "|---|---|---|---|---|---|"])
        for item in qc["issues"]:
            lines.append(
                f"| {item.get('severity','')} | {item.get('category','')} | {item.get('report_id','')} | {item.get('file','')} | {item.get('message','')} | {item.get('suggested_action','')} |"
            )
    else:
        lines.append("未发现实质性问题。")
    path = output_dir / "05-质量检查.md"
    atomic_write_text(path, "\n".join(lines).strip() + "\n")
    return path


def render_dashboard(
    output_dir: Path,
    run_meta: dict[str, Any],
    digest: dict[str, Any],
    cards: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    top_n: int,
) -> Path:
    ordered = sorted(cards, key=lambda c: c.get("priority_score", 0), reverse=True)
    top = ordered[:top_n]
    must_read = sum(1 for c in cards if c.get("recommended_action") == "must_read_full")
    negative = sum(1 for c in cards if c.get("direction_score", 0) <= -2)
    positive = sum(1 for c in cards if c.get("direction_score", 0) >= 2)

    def cls(direction: int) -> str:
        return "pos" if direction > 0 else "neg" if direction < 0 else "neu"

    cards_html = []
    for idx, card in enumerate(top, 1):
        source_link = ""
        source = card.get("source_file", "")
        if source:
            try:
                source_link = f'<a href="{html.escape(Path(source).resolve().as_uri())}">原始PDF</a>'
            except ValueError:
                source_link = ""
        new_items = "".join(
            f"<li>{html.escape(str(item.get('claim','')))} <small>p.{item.get('page') or '?'}</small></li>"
            for item in (card.get("new_information", []) or [])[:3]
        ) or "<li>未识别到高置信度新增信息</li>"
        cards_html.append(
            f"""
            <article class="report-card">
              <div class="rank">{idx}</div>
              <div class="report-main">
                <div class="eyebrow">{html.escape(str(card.get('institution','')))} · {html.escape(str(card.get('report_date','')))} · {html.escape(_company_text(card))}</div>
                <h3>{html.escape(str(card.get('title','')))}</h3>
                <p>{html.escape(str(card.get('core_conclusion','')))}</p>
                <ul>{new_items}</ul>
                <div class="links">{source_link}</div>
              </div>
              <div class="scorebox">
                <strong>{card.get('importance_score',0)}</strong><span>重要性</span>
                <em class="{cls(card.get('direction_score',0))}">{html.escape(direction_label(card.get('direction_score',0)))}</em>
                <small>置信度 {card.get('confidence_score',0)}</small>
              </div>
            </article>
            """
        )

    changes_html = "".join(
        f"<li><strong>{html.escape(str(item.get('title','')))}</strong><span class='{cls(item.get('direction',0))}'>{html.escape(direction_label(item.get('direction',0)))}</span><p>{html.escape(str(item.get('why_it_matters','')))}</p></li>"
        for item in digest.get("top_changes", []) or []
    ) or "<li>暂无综合变化。</li>"

    cluster_html = "".join(
        f"<div class='cluster'><h4>{html.escape(str(c.get('event_title','')))}</h4><p>{html.escape('；'.join(c.get('consensus_points', [])[:3]))}</p><small>{len(c.get('report_ids', []))}份报告 · 重要性{c.get('cluster_importance',0)}</small></div>"
        for c in sorted(clusters, key=lambda x: x.get("cluster_importance", 0), reverse=True)[:6]
    ) or "<div class='cluster'>未形成可靠事件簇</div>"

    document = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{run_meta['run_date']} 研报仪表盘</title>
<style>
:root{{--bg:#f5f6f8;--paper:#fff;--text:#16181d;--muted:#6b7280;--line:#e5e7eb;--pos:#b42318;--neg:#175cd3;--neu:#475467;--accent:#101828}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.55}}
.container{{max-width:1240px;margin:0 auto;padding:32px 24px 72px}} header{{display:flex;justify-content:space-between;gap:24px;align-items:end;margin-bottom:24px}} h1{{font-size:32px;margin:0}} .sub{{color:var(--muted)}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0}} .stat{{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:18px}} .stat strong{{display:block;font-size:28px}} .stat span{{color:var(--muted);font-size:13px}}
.grid{{display:grid;grid-template-columns:1.15fr .85fr;gap:18px;margin-bottom:22px}} .panel{{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:22px}} .panel h2{{margin-top:0}} .view{{font-size:17px}}
.change-list{{padding-left:22px}} .change-list li{{margin-bottom:14px}} .change-list span{{font-size:12px;margin-left:8px}} .change-list p{{margin:4px 0;color:var(--muted)}}
.report-card{{display:grid;grid-template-columns:44px 1fr 110px;gap:14px;background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:18px;margin-bottom:12px}} .rank{{font-size:26px;font-weight:700;color:#98a2b3}} .eyebrow{{font-size:12px;color:var(--muted)}} h3{{margin:4px 0 8px;font-size:18px}} .report-main p{{margin:0 0 8px}} .report-main ul{{margin:0;padding-left:20px;color:#344054}} .report-main small{{color:var(--muted)}} .links a{{font-size:13px;color:#175cd3;text-decoration:none}}
.scorebox{{text-align:right;border-left:1px solid var(--line);padding-left:14px}} .scorebox strong{{display:block;font-size:30px}} .scorebox span,.scorebox small{{display:block;color:var(--muted);font-size:12px}} .scorebox em{{display:block;font-style:normal;font-size:13px;margin:8px 0}}
.pos{{color:var(--pos)}} .neg{{color:var(--neg)}} .neu{{color:var(--neu)}} .clusters{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}} .cluster{{border:1px solid var(--line);border-radius:12px;padding:14px}} .cluster h4{{margin:0 0 6px}} .cluster p{{margin:0 0 8px;color:#344054}} .cluster small{{color:var(--muted)}}
@media(max-width:820px){{.grid{{grid-template-columns:1fr}}.stats{{grid-template-columns:repeat(2,1fr)}}.report-card{{grid-template-columns:34px 1fr}}.scorebox{{grid-column:2;text-align:left;border-left:0;padding-left:0;display:flex;gap:12px;align-items:center}}.clusters{{grid-template-columns:1fr}}header{{display:block}}}}
</style>
</head>
<body><main class="container">
<header><div><div class="sub">A股研报智能筛选系统</div><h1>{run_meta['run_date']} · {run_meta['session']}</h1></div><div class="sub">本地生成 · 非投资建议</div></header>
<section class="stats"><div class="stat"><strong>{len(cards)}</strong><span>研报总数</span></div><div class="stat"><strong>{len(clusters)}</strong><span>事件簇</span></div><div class="stat"><strong>{must_read}</strong><span>必须读原文</span></div><div class="stat"><strong>{positive}/{negative}</strong><span>明确正面 / 明确负面</span></div></section>
<section class="grid"><div class="panel"><h2>总体判断</h2><p class="view">{html.escape(str(digest.get('executive_view','暂无综合判断。')))}</p></div><div class="panel"><h2>今日关键变化</h2><ol class="change-list">{changes_html}</ol></div></section>
<section><h2>今日必读</h2>{''.join(cards_html)}</section>
<section class="panel"><h2>主要事件簇</h2><div class="clusters">{cluster_html}</div></section>
</main></body></html>"""
    path = output_dir / "dashboard.html"
    atomic_write_text(path, document)
    return path


def write_machine_outputs(
    output_dir: Path,
    *,
    run_meta: dict[str, Any],
    cards: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    deep_dives: dict[str, dict[str, Any]],
    digest: dict[str, Any],
    qc: dict[str, Any] | None = None,
) -> Path:
    machine = output_dir / "machine"
    machine.mkdir(parents=True, exist_ok=True)
    write_json(machine / "run.json", run_meta)
    write_json(machine / "report_cards.json", {"reports": cards})
    write_json(machine / "clusters.json", {"clusters": clusters})
    write_json(machine / "deep_dives.json", deep_dives)
    write_json(machine / "digest.json", digest)
    if qc is not None:
        write_json(machine / "qc.json", qc)
    return machine


def update_latest_link(outputs_root: Path, output_dir: Path) -> None:
    latest = outputs_root / "latest"
    try:
        if latest.is_symlink() or latest.exists():
            if latest.is_dir() and not latest.is_symlink():
                return
            latest.unlink()
        latest.symlink_to(output_dir.resolve(), target_is_directory=True)
    except OSError:
        atomic_write_text(outputs_root / "LATEST.txt", str(output_dir.resolve()) + "\n")
