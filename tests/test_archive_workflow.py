from __future__ import annotations

import unittest
from pathlib import Path


class ArchiveWorkflowTests(unittest.TestCase):
    def test_workflow_is_daily_write_scoped_and_does_not_archive_media(self) -> None:
        workflow = (
            Path(__file__).parents[1] / ".github/workflows/daily-structured-archive.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('cron: "17 5 * * *"', workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("AviramDahan/market-lens-scanner", workflow)
        self.assertIn("sparse-checkout-cone-mode: false", workflow)
        self.assertNotIn("agent_results/charts", workflow)
        self.assertNotIn("agent_results/screenshots", workflow)
        self.assertNotIn("PERSONAL_ACCESS_TOKEN", workflow)
        self.assertNotIn("PAT", workflow)
        self.assertIn("refusing to overwrite it", workflow)


if __name__ == "__main__":
    unittest.main()
