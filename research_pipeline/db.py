from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from .utils import utc_now_iso


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS reports (
    report_id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    extracted_dir TEXT NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    page_count INTEGER NOT NULL DEFAULT 0,
    text_chars INTEGER NOT NULL DEFAULT 0,
    scanned_pages_json TEXT NOT NULL DEFAULT '[]',
    parsed_report_date TEXT NOT NULL DEFAULT '',
    parsed_institution TEXT NOT NULL DEFAULT '',
    parsed_title TEXT NOT NULL DEFAULT '',
    parsed_company TEXT NOT NULL DEFAULT '',
    parsed_ticker TEXT NOT NULL DEFAULT '',
    extraction_status TEXT NOT NULL DEFAULT 'pending',
    extraction_error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS report_cards (
    report_id TEXT PRIMARY KEY REFERENCES reports(report_id) ON DELETE CASCADE,
    card_json TEXT NOT NULL,
    importance_score INTEGER NOT NULL DEFAULT 0,
    priority_score INTEGER NOT NULL DEFAULT 0,
    direction_score INTEGER NOT NULL DEFAULT 0,
    confidence_score INTEGER NOT NULL DEFAULT 0,
    recommended_action TEXT NOT NULL DEFAULT 'index_only',
    analysis_version TEXT NOT NULL DEFAULT 'v1',
    analyzed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    run_date TEXT NOT NULL,
    session TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL DEFAULT '',
    input_count INTEGER NOT NULL DEFAULT 0,
    new_count INTEGER NOT NULL DEFAULT 0,
    output_dir TEXT NOT NULL DEFAULT '',
    errors_json TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_runs_date_session ON runs(run_date, session, status);

CREATE TABLE IF NOT EXISTS run_reports (
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    report_id TEXT NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'ingested',
    PRIMARY KEY (run_id, report_id)
);

CREATE TABLE IF NOT EXISTS clusters (
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    cluster_id TEXT NOT NULL,
    cluster_json TEXT NOT NULL,
    PRIMARY KEY (run_id, cluster_id)
);

CREATE TABLE IF NOT EXISTS deep_dives (
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    report_id TEXT NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    deep_json TEXT NOT NULL,
    markdown_path TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (run_id, report_id)
);
"""


class ResearchDB:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "ResearchDB":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.close()

    def get_report_by_sha(self, sha256: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM reports WHERE sha256 = ?", (sha256,)).fetchone()
        return dict(row) if row else None

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM reports WHERE report_id = ?", (report_id,)).fetchone()
        return dict(row) if row else None

    def upsert_report(self, report: dict[str, Any]) -> None:
        now = utc_now_iso()
        self.conn.execute(
            """
            INSERT INTO reports (
                report_id, sha256, file_name, file_path, extracted_dir, file_size,
                page_count, text_chars, scanned_pages_json, parsed_report_date,
                parsed_institution, parsed_title, parsed_company, parsed_ticker,
                extraction_status, extraction_error, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(report_id) DO UPDATE SET
                file_name=excluded.file_name,
                file_path=excluded.file_path,
                extracted_dir=excluded.extracted_dir,
                file_size=excluded.file_size,
                page_count=excluded.page_count,
                text_chars=excluded.text_chars,
                scanned_pages_json=excluded.scanned_pages_json,
                parsed_report_date=excluded.parsed_report_date,
                parsed_institution=excluded.parsed_institution,
                parsed_title=excluded.parsed_title,
                parsed_company=excluded.parsed_company,
                parsed_ticker=excluded.parsed_ticker,
                extraction_status=excluded.extraction_status,
                extraction_error=excluded.extraction_error,
                updated_at=excluded.updated_at
            """,
            (
                report["report_id"],
                report["sha256"],
                report["file_name"],
                report["file_path"],
                report["extracted_dir"],
                int(report.get("file_size", 0)),
                int(report.get("page_count", 0)),
                int(report.get("text_chars", 0)),
                json.dumps(report.get("scanned_pages", []), ensure_ascii=False),
                report.get("parsed_report_date", ""),
                report.get("parsed_institution", ""),
                report.get("parsed_title", ""),
                report.get("parsed_company", ""),
                report.get("parsed_ticker", ""),
                report.get("extraction_status", "pending"),
                report.get("extraction_error", ""),
                report.get("created_at", now),
                now,
            ),
        )
        self.conn.commit()

    def create_run(self, run_id: str, run_date: str, session: str, output_dir: str) -> None:
        self.conn.execute(
            """
            INSERT INTO runs(run_id, run_date, session, status, started_at, output_dir)
            VALUES (?, ?, ?, 'running', ?, ?)
            """,
            (run_id, run_date, session, utc_now_iso(), output_dir),
        )
        self.conn.commit()

    def update_run_counts(self, run_id: str, input_count: int, new_count: int) -> None:
        self.conn.execute(
            "UPDATE runs SET input_count = ?, new_count = ? WHERE run_id = ?",
            (input_count, new_count, run_id),
        )
        self.conn.commit()

    def finish_run(self, run_id: str, status: str, errors: list[dict[str, Any]] | None = None) -> None:
        self.conn.execute(
            "UPDATE runs SET status = ?, completed_at = ?, errors_json = ? WHERE run_id = ?",
            (status, utc_now_iso(), json.dumps(errors or [], ensure_ascii=False), run_id),
        )
        self.conn.commit()

    def has_successful_run(self, run_date: str, session: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM runs WHERE run_date = ? AND session = ? AND status = 'success' LIMIT 1",
            (run_date, session),
        ).fetchone()
        return bool(row)

    def add_run_report(self, run_id: str, report_id: str, status: str = "ingested") -> None:
        self.conn.execute(
            """
            INSERT INTO run_reports(run_id, report_id, status)
            VALUES (?, ?, ?)
            ON CONFLICT(run_id, report_id) DO UPDATE SET status = excluded.status
            """,
            (run_id, report_id, status),
        )
        self.conn.commit()

    def update_run_report_status(self, run_id: str, report_id: str, status: str) -> None:
        self.conn.execute(
            "UPDATE run_reports SET status = ? WHERE run_id = ? AND report_id = ?",
            (status, run_id, report_id),
        )
        self.conn.commit()

    def get_card(self, report_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT card_json FROM report_cards WHERE report_id = ?", (report_id,)
        ).fetchone()
        return json.loads(row["card_json"]) if row else None

    def store_card(self, report_id: str, card: dict[str, Any], analysis_version: str = "v1") -> None:
        self.conn.execute(
            """
            INSERT INTO report_cards(
                report_id, card_json, importance_score, priority_score,
                direction_score, confidence_score, recommended_action,
                analysis_version, analyzed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(report_id) DO UPDATE SET
                card_json=excluded.card_json,
                importance_score=excluded.importance_score,
                priority_score=excluded.priority_score,
                direction_score=excluded.direction_score,
                confidence_score=excluded.confidence_score,
                recommended_action=excluded.recommended_action,
                analysis_version=excluded.analysis_version,
                analyzed_at=excluded.analyzed_at
            """,
            (
                report_id,
                json.dumps(card, ensure_ascii=False),
                int(card.get("importance_score", 0)),
                int(card.get("priority_score", 0)),
                int(card.get("direction_score", 0)),
                int(card.get("confidence_score", 0)),
                card.get("recommended_action", "index_only"),
                analysis_version,
                utc_now_iso(),
            ),
        )
        self.conn.commit()

    def get_cards_for_run(self, run_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT rc.card_json
            FROM run_reports rr
            JOIN report_cards rc ON rc.report_id = rr.report_id
            WHERE rr.run_id = ?
            """,
            (run_id,),
        ).fetchall()
        return [json.loads(row["card_json"]) for row in rows]

    def iter_recent_cards(self, limit: int = 500) -> Iterable[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT card_json FROM report_cards ORDER BY analyzed_at DESC LIMIT ?", (limit,)
        ).fetchall()
        for row in rows:
            yield json.loads(row["card_json"])

    def find_prior_cards(
        self,
        company: str = "",
        ticker: str = "",
        exclude_report_id: str = "",
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        company_norm = company.strip().lower()
        ticker_norm = ticker.strip().lower()
        matches: list[dict[str, Any]] = []
        for card in self.iter_recent_cards(limit=800):
            if card.get("report_id") == exclude_report_id:
                continue
            companies = card.get("companies", []) or []
            hit = False
            for item in companies:
                name = str(item.get("name", "")).strip().lower()
                code = str(item.get("ticker", "")).strip().lower()
                if ticker_norm and code and ticker_norm == code:
                    hit = True
                if company_norm and name and (company_norm in name or name in company_norm):
                    hit = True
            if hit:
                matches.append(card)
            if len(matches) >= limit:
                break
        return matches

    def store_clusters(self, run_id: str, clusters: list[dict[str, Any]]) -> None:
        self.conn.execute("DELETE FROM clusters WHERE run_id = ?", (run_id,))
        self.conn.executemany(
            "INSERT INTO clusters(run_id, cluster_id, cluster_json) VALUES (?, ?, ?)",
            [
                (run_id, cluster["cluster_id"], json.dumps(cluster, ensure_ascii=False))
                for cluster in clusters
            ],
        )
        self.conn.commit()

    def get_latest_deep_dive(self, report_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT dd.deep_json
            FROM deep_dives dd
            JOIN runs r ON r.run_id = dd.run_id
            WHERE dd.report_id = ? AND r.status IN ('success', 'partial')
            ORDER BY r.completed_at DESC, r.started_at DESC
            LIMIT 1
            """,
            (report_id,),
        ).fetchone()
        return json.loads(row["deep_json"]) if row else None

    def store_deep_dive(
        self, run_id: str, report_id: str, deep_data: dict[str, Any], markdown_path: str = ""
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO deep_dives(run_id, report_id, deep_json, markdown_path)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(run_id, report_id) DO UPDATE SET
                deep_json=excluded.deep_json,
                markdown_path=excluded.markdown_path
            """,
            (run_id, report_id, json.dumps(deep_data, ensure_ascii=False), markdown_path),
        )
        self.conn.commit()
