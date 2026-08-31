from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import pymupdf

from research_pipeline.config import AppConfig, load_config
from research_pipeline.pdf_ingest import discover_pdfs, extract_pdf, parse_report_filename


def temp_config(root: Path) -> AppConfig:
    base = load_config()
    data = copy.deepcopy(base.data)
    cfg = AppConfig(root, data, root / "config.yaml")
    cfg.ensure_directories()
    watchlist = cfg.path("watchlist")
    watchlist.write_text("market,ticker,name,holding,priority,theme,notes\n", encoding="utf-8")
    return cfg


class FilenameAndPdfTests(unittest.TestCase):
    def test_parse_common_chinese_filename(self) -> None:
        parsed = parse_report_filename(
            Path("汇丰-生益科技（600183）：产品结构更优、产能更大；买入-260819.pdf")
        )
        self.assertEqual(parsed.institution, "汇丰")
        self.assertEqual(parsed.report_date, "2026-08-19")
        self.assertEqual(parsed.company, "生益科技")
        self.assertEqual(parsed.ticker, "600183")
        self.assertNotIn("260819", parsed.title)
        uncovered = parse_report_filename(
            Path("高盛-小菜园（0999.HK，未覆盖）：1H26 NDR要点-260819.pdf")
        )
        self.assertEqual(uncovered.company, "小菜园")
        self.assertEqual(uncovered.ticker, "0999.HK")

    def test_discover_is_recursive_and_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "行业").mkdir()
            (root / "a.pdf").write_bytes(b"x")
            (root / "行业" / "B.PDF").write_bytes(b"x")
            (root / "c.txt").write_text("x")
            found = discover_pdfs(root)
            self.assertEqual({p.name for p in found}, {"a.pdf", "B.PDF"})

    def test_extract_pdf_preserves_physical_pages_and_hash_dedup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = temp_config(root)
            inbox = cfg.path("inbox") / "2026-08-21"
            inbox.mkdir(parents=True)
            pdf = inbox / "高盛-测试公司（300001）：盈利预测上调-260821.pdf"

            doc = pymupdf.open()
            for i in range(3):
                page = doc.new_page()
                page.insert_text((72, 72), f"PDF page {i+1} 核心观点 盈利预测 {100+i}%")
            doc.save(pdf)
            doc.close()

            first = extract_pdf(pdf, cfg)
            copy_path = inbox / "同一报告改名.pdf"
            copy_path.write_bytes(pdf.read_bytes())
            second = extract_pdf(copy_path, cfg)

            self.assertEqual(first["report_id"], second["report_id"])
            self.assertEqual(first["page_count"], 3)
            self.assertEqual(first["extraction_status"], "success")
            text = Path(first["full_text_path"]).read_text(encoding="utf-8")
            self.assertIn("## PDF Page 1", text)
            self.assertIn("## PDF Page 3", text)
            self.assertTrue(Path(first["triage_excerpt_path"]).exists())


if __name__ == "__main__":
    unittest.main()
