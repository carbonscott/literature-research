"""Tests for verify_citations.py using a temporary corpus and findings file.

Run with:  python3 quantum-materials/tests/test_verify_citations.py
"""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import verify_citations  # noqa: E402

CORPUS_RECORDS = {
    "arxiv.jsonl": [
        {"id": "arXiv:2510.00575", "server": "arxiv", "window": "trailing"},
        {"id": "arXiv:2411.01234", "server": "arxiv", "window": "preceding"},
        {"id": "arXiv:2601.11111", "server": "arxiv", "window": "trailing"},
    ],
    "chemrxiv.jsonl": [
        {"id": "doi:10.26434/chemrxiv-2025-abc12", "server": "chemrxiv", "window": "trailing"},
    ],
    "hal.jsonl": [
        {"id": "hal:hal-04567890", "server": "hal", "window": "trailing"},
    ],
    "osti.jsonl": [
        {"id": "osti:2345678", "server": "osti", "window": None},
    ],
}

# A record in raw/ must be ignored.
RAW_RECORD = {"id": "arXiv:2599.99999", "server": "arxiv", "window": "trailing"}

FINDINGS = """# Findings

Intro cites nothing under a question: arXiv:2601.11111.

## Q1 Landscape
- Kagome work (arXiv:2510.00575v2), and again `arXiv:2510.00575`.
- Chemistry: doi:10.26434/CHEMRXIV-2025-ABC12;
- HAL: hal:hal-04567890]
| table cell arXiv:2411.01234 |

## Q2 Momentum
- osti:2345678.
- Not harvested: arXiv:2599.99999, doi:10.9999/missing-one).
- Bare IDs do not count: 2510.00575 10.1234/xyz

## Other section
- arXiv:2601.11111
"""


class VerifyCitationsTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.corpus_dir = os.path.join(self.temp_dir, "corpus")
        os.makedirs(os.path.join(self.corpus_dir, "raw"))
        for filename, records in CORPUS_RECORDS.items():
            with open(os.path.join(self.corpus_dir, filename), "w", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record) + "\n")
        with open(os.path.join(self.corpus_dir, "raw", "arxiv.jsonl"), "w") as handle:
            handle.write(json.dumps(RAW_RECORD) + "\n")
        self.findings_path = os.path.join(self.temp_dir, "findings.md")
        with open(self.findings_path, "w", encoding="utf-8") as handle:
            handle.write(FINDINGS)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def run_main(self, findings_path=None):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            status = verify_citations.main([
                "--findings", findings_path or self.findings_path,
                "--corpus-dir", self.corpus_dir,
            ])
        return status, buffer.getvalue()

    def test_counts_and_missing(self):
        status, output = self.run_main()
        # Unique cited: 2601.11111, 2510.00575, chemrxiv doi, hal, 2411.01234,
        # osti, 2599.99999, missing doi -> 8 total, 2 missing.
        self.assertIn("cited IDs: 8 | found in corpus: 6 | missing: 2", output)
        self.assertEqual(output.strip().splitlines()[-1],
                         "cited IDs: 8 | found in corpus: 6 | missing: 2")
        self.assertIn("  arxiv:2599.99999", output)
        self.assertIn("  doi:10.9999/missing-one", output)
        self.assertEqual(status, 1)

    def test_corpus_summary_ignores_raw(self):
        _, output = self.run_main()
        lines = output.splitlines()
        self.assertEqual(lines[0], "harvested corpus: 6 records")
        self.assertEqual(lines[1], "  arxiv: 3")  # largest count first
        self.assertIn("arxiv by window: trailing=2 | preceding=1 | outside=0", output)

    def test_version_stripping_and_case(self):
        self.assertEqual(verify_citations.normalize_id("arXiv:2510.00575v2"), "arxiv:2510.00575")
        self.assertEqual(verify_citations.normalize_id("ARXIV:2510.00575"), "arxiv:2510.00575")
        self.assertEqual(verify_citations.normalize_id("doi:10.26434/ChemRxiv-X"),
                         "doi:10.26434/chemrxiv-x")

    def test_trailing_punctuation(self):
        text = "(arXiv:2510.00575). `doi:10.1234/AbC`, hal:hal-01234567]; osti:42|"
        self.assertEqual(verify_citations.extract_citations(text), [
            "arxiv:2510.00575", "doi:10.1234/abc", "hal:hal-01234567", "osti:42"])

    def test_per_question_tally(self):
        _, output = self.run_main()
        self.assertIn("  Q1: 4", output)  # 2510.00575 (twice), doi, hal, 2411.01234
        self.assertIn("  Q2: 3", output)  # osti, 2599.99999, missing doi

    def test_success_exit_status(self):
        good_path = os.path.join(self.temp_dir, "good.md")
        with open(good_path, "w") as handle:
            handle.write("## Q1\narXiv:2510.00575v3 and doi:10.26434/chemrxiv-2025-ABC12.\n")
        status, output = self.run_main(good_path)
        self.assertEqual(status, 0)
        self.assertIn("cited IDs: 2 | found in corpus: 2 | missing: 0", output)

    def test_no_citations_fails(self):
        empty_path = os.path.join(self.temp_dir, "empty.md")
        with open(empty_path, "w") as handle:
            handle.write("## Q1\nNothing here.\n")
        status, output = self.run_main(empty_path)
        self.assertEqual(status, 1)
        self.assertIn("cited IDs: 0 | found in corpus: 0 | missing: 0", output)


if __name__ == "__main__":
    unittest.main()
