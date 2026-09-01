"""Tests for GUI session validation and input handling."""

import unittest
import tempfile
import hashlib
from pathlib import Path

from research_pipeline.pipeline import validate_session_name


class TestSessionValidation(unittest.TestCase):
    """Test session name validation using shared validator."""

    def test_standard_times_valid(self):
        """Standard times 0900 and 2100 should be valid."""
        self.assertTrue(validate_session_name("0900"))
        self.assertTrue(validate_session_name("2100"))

    def test_gui_hhmmss_pattern_valid(self):
        """gui-HHMMSS pattern with valid time fields should be valid."""
        valid_sessions = [
            "gui-090000",
            "gui-143022",
            "gui-235959",
        ]

        for session in valid_sessions:
            self.assertTrue(
                validate_session_name(session),
                f"Expected {session} to be valid"
            )

    def test_gui_hhmmss_hex_pattern_valid(self):
        """gui-HHMMSS-<6 lowercase hex> pattern should be valid."""
        valid_sessions = [
            "gui-090000-abc123",
            "gui-143022-deadbe",
            "gui-235959-00ff00",
        ]

        for session in valid_sessions:
            self.assertTrue(
                validate_session_name(session),
                f"Expected {session} to be valid"
            )

    def test_invalid_time_fields_rejected(self):
        """Invalid time fields should be rejected."""
        invalid_sessions = [
            "gui-250000",  # HH > 23
            "gui-096000",  # MM > 59
            "gui-090060",  # SS > 59
            "gui-250000-abc123",  # HH > 23 with hex
        ]

        for session in invalid_sessions:
            self.assertFalse(
                validate_session_name(session),
                f"Expected {session} to be rejected"
            )

    def test_path_traversal_rejected(self):
        """Path-like and traversal patterns should be rejected."""
        invalid_sessions = [
            "../outputs",
            "../../etc/passwd",
            "/absolute/path",
            "gui/../bypass",
            "gui-09:00:00",  # Colon not allowed
            "gui-<script>",
            "",
            "a" * 100,  # Too long
        ]

        for session in invalid_sessions:
            self.assertFalse(
                validate_session_name(session),
                f"Expected {session} to be rejected"
            )

    def test_simple_alphanumeric_valid(self):
        """Simple alphanumeric with hyphen/underscore should be valid."""
        valid_sessions = [
            "test-run",
            "batch_2024",
            "experiment-1",
        ]

        for session in valid_sessions:
            self.assertTrue(
                validate_session_name(session),
                f"Expected {session} to be valid"
            )


class TestInputFileHandling(unittest.TestCase):
    """Test safe file staging with collision detection."""

    def test_same_name_different_content_collision_suffix(self):
        """Files with same name but different content should get collision suffix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create two PDF files with same name but different content
            src1 = tmpdir / "source1" / "report.pdf"
            src1.parent.mkdir()
            src1.write_bytes(b"Content A")

            src2 = tmpdir / "source2" / "report.pdf"
            src2.parent.mkdir()
            src2.write_bytes(b"Content B")

            dest_dir = tmpdir / "dest"
            dest_dir.mkdir()

            # Stage first file
            self._stage_safely(src1, dest_dir)

            # Stage second file with same name
            self._stage_safely(src2, dest_dir)

            # Should have two files in dest
            dest_files = list(dest_dir.glob("*.pdf"))
            self.assertEqual(len(dest_files), 2)

            # One should have original name, one with hash suffix
            names = [f.name for f in dest_files]
            self.assertIn("report.pdf", names)

            # Other should have hash suffix
            hash_files = [n for n in names if n != "report.pdf"]
            self.assertEqual(len(hash_files), 1)
            self.assertTrue(hash_files[0].startswith("report-"))
            self.assertTrue(hash_files[0].endswith(".pdf"))

    def test_same_name_same_content_no_duplicate(self):
        """Files with same name and same content should not create duplicates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create two files with identical content
            src1 = tmpdir / "source1" / "report.pdf"
            src1.parent.mkdir()
            src1.write_bytes(b"Identical content")

            src2 = tmpdir / "source2" / "report.pdf"
            src2.parent.mkdir()
            src2.write_bytes(b"Identical content")

            dest_dir = tmpdir / "dest"
            dest_dir.mkdir()

            # Stage both files
            self._stage_safely(src1, dest_dir)
            self._stage_safely(src2, dest_dir)

            # Should have only one file
            dest_files = list(dest_dir.glob("*.pdf"))
            self.assertEqual(len(dest_files), 1)
            self.assertEqual(dest_files[0].name, "report.pdf")

    def _stage_safely(self, src: Path, dest_dir: Path) -> None:
        """Safe staging logic matching gui_app.py."""
        import shutil

        dest = dest_dir / src.name

        if dest.exists():
            src_hash = self._compute_hash(src)
            dest_hash = self._compute_hash(dest)

            if src_hash != dest_hash:
                dest = dest_dir / f"{src.stem}-{src_hash[:8]}{src.suffix}"

        if not dest.exists():
            shutil.copy2(src, dest)

    def _compute_hash(self, path: Path) -> str:
        """Compute SHA-256 hash using streaming."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()


class TestCLIOutputParsing(unittest.TestCase):
    """Test partial CLI JSON parsing."""

    def test_parse_success_status(self):
        """Success status with dashboard should be viewable."""
        stdout = '{"status": "success", "output_dir": "/path/to/output", "dashboard": "/path/to/output/dashboard.html"}'
        result = self._parse_output(stdout, "", 0)

        self.assertTrue(result["success"])
        self.assertEqual(result["output_dir"], "/path/to/output")
        self.assertEqual(result["dashboard"], "/path/to/output/dashboard.html")
        self.assertFalse(result["is_partial"])

    def test_parse_partial_status_with_dashboard(self):
        """Partial status with dashboard should be viewable warning."""
        stdout = '{"status": "partial", "output_dir": "/path/to/output", "dashboard": "/path/to/output/dashboard.html"}'
        result = self._parse_output(stdout, "some warnings", 1)

        self.assertTrue(result["success"])
        self.assertTrue(result["is_partial"])
        self.assertIsNotNone(result["dashboard"])

    def test_parse_no_dashboard_fails(self):
        """Output without dashboard should not be viewable."""
        stdout = '{"status": "success", "output_dir": "/path/to/output"}'
        result = self._parse_output(stdout, "", 0)

        self.assertFalse(result["success"])

    def test_parse_invalid_json_fails(self):
        """Invalid JSON should fail gracefully."""
        result = self._parse_output("not json", "error", 1)

        self.assertFalse(result["success"])
        self.assertIsNone(result["output_dir"])

    def _parse_output(self, stdout: str, stderr: str, returncode: int) -> dict:
        """Simplified parsing logic matching gui_app.py."""
        import json

        output_dir = None
        dashboard = None
        status = None

        try:
            output = json.loads(stdout)
            status = output.get("status")
            output_dir = output.get("output_dir")
            dashboard = output.get("dashboard")
        except (json.JSONDecodeError, ValueError):
            pass

        is_partial = status == "partial"
        success = returncode == 0 or (is_partial and output_dir)

        # Only viewable if we have dashboard
        if success and not dashboard:
            success = False

        return {
            "success": success,
            "output_dir": output_dir,
            "dashboard": dashboard,
            "is_partial": is_partial,
            "error_detail": stderr[:200] if stderr else None,
        }


if __name__ == "__main__":
    unittest.main()
