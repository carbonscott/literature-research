"""Concatenate the report parts into report/source.html, in reading order.

Each part is an HTML fragment in report/parts/ (written by a section writer or
the orchestrator). Run this before build_report.py:
  python agents-in-science-workflow/report/assemble_source.py
  python agents-in-science-workflow/report/build_report.py
"""
import os

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))
PARTS_DIR = os.path.join(REPORT_DIR, "parts")
PART_ORDER = ["summary.html", "q1.html", "q2.html", "q3.html", "q4.html", "q5.html", "q6.html", "appendix.html"]


def main():
    pieces = []
    for name in PART_ORDER:
        with open(os.path.join(PARTS_DIR, name), encoding="utf-8") as handle:
            pieces.append("<!-- part: %s -->\n%s" % (name, handle.read().strip()))
    out_path = os.path.join(REPORT_DIR, "source.html")
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write("\n\n".join(pieces) + "\n")
    print("wrote %s from %d parts" % (out_path, len(pieces)))


if __name__ == "__main__":
    main()
