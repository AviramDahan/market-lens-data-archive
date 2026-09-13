from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.build_structured_archive import build_archive, selected_files


class StructuredArchiveTests(unittest.TestCase):
    def test_archive_contains_structured_data_and_manifest_but_no_media(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            output = root / "out" / "data.zip"
            manifest_path = root / "out" / "manifest.json"
            decision = source / "agent_results/decisions/run.jsonl"
            chart = source / "agent_results/decisions/debug.png"
            screenshot = source / "agent_results/screenshots/run.png"
            tracker = source / "agent_tracker/market_lens_agent_portfolio_budget_100k.xlsx"
            for path, content in ((decision, b"{}\n"), (chart, b"png"), (screenshot, b"png"), (tracker, b"xlsx")):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

            manifest = build_archive(
                source,
                output,
                manifest_path,
                source_repository="AviramDahan/market-lens-scanner",
                source_commit="a" * 40,
                created_at="2026-09-13T00:00:00+00:00",
            )

            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                embedded = json.loads(archive.read("archive_manifest.json"))
            self.assertIn("agent_results/decisions/run.jsonl", names)
            self.assertIn("agent_tracker/market_lens_agent_portfolio_budget_100k.xlsx", names)
            self.assertNotIn("agent_results/decisions/debug.png", names)
            self.assertNotIn("agent_results/screenshots/run.png", names)
            self.assertEqual(embedded, manifest)
            self.assertEqual(json.loads(manifest_path.read_text()), manifest)
            self.assertFalse(manifest["media_included"])

    def test_credential_like_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            secret = source / "agent_results/diagnostics/.env"
            secret.parent.mkdir(parents=True)
            secret.write_text("TOKEN=secret", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "credential-like"):
                selected_files(source)

    def test_output_inside_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            decision = source / "agent_results/decisions/run.jsonl"
            decision.parent.mkdir(parents=True)
            decision.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "outside"):
                build_archive(
                    source,
                    source / "archive.zip",
                    Path(directory) / "manifest.json",
                    source_repository="repo",
                    source_commit="a" * 40,
                )


if __name__ == "__main__":
    unittest.main()
