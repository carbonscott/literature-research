"""Apply reviewed text edits and catalog changes proposed by audit agents.

Text edits (to report/parts/*.html) are JSON arrays of
  {"file": "q4.html", "old": "...", "new": "...", ...}
Items with an empty "old" (e.g. confirmed claims) are skipped. An edit is applied
only if "old" occurs exactly once in the file; otherwise it is reported and skipped.

Catalog changes (to notes/catalog_general.json / notes/catalog_facility.json) are
JSON arrays of
  {"name": "...", "lane": "general|facility", "field": "autonomy", "old": "...", "new": "..."}
A change is applied only if the row exists and its current value equals "old".

Usage (from the repository root):
  python agents-in-science-workflow/report/apply_edits.py --text notes/audit_iter3_q4.json ...
  python agents-in-science-workflow/report/apply_edits.py --catalog notes/audit_iter3_catalog.json
Paths are relative to the campaign folder.
"""
import argparse
import json
import os

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))
CAMPAIGN_DIR = os.path.dirname(REPORT_DIR)
PARTS_DIR = os.path.join(REPORT_DIR, "parts")
CATALOG_FILES = {
    "general": os.path.join(CAMPAIGN_DIR, "notes", "catalog_general.json"),
    "facility": os.path.join(CAMPAIGN_DIR, "notes", "catalog_facility.json"),
}


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def apply_text_edits(edit_path):
    """Apply old->new replacements to parts files; return (applied, skipped) counts."""
    applied, skipped = 0, 0
    for edit in load_json(edit_path):
        old, new = edit.get("old", ""), edit.get("new", "")
        if not old or old == new:
            continue
        part_path = os.path.join(PARTS_DIR, edit["file"])
        with open(part_path, encoding="utf-8") as handle:
            text = handle.read()
        count = text.count(old)
        if count != 1:
            skipped += 1
            print("  SKIP %s: 'old' found %d times: %.90r" % (edit["file"], count, old))
            continue
        with open(part_path, "w", encoding="utf-8") as handle:
            handle.write(text.replace(old, new))
        applied += 1
    return applied, skipped


def apply_catalog_changes(change_path):
    """Apply field changes to the lane catalog files; return (applied, skipped) counts."""
    catalogs = {lane: load_json(path) for lane, path in CATALOG_FILES.items()}
    applied, skipped = 0, 0
    for change in load_json(change_path):
        rows = [row for row in catalogs.get(change.get("lane"), []) if row["name"] == change["name"]]
        if len(rows) != 1:
            skipped += 1
            print("  SKIP catalog: row %r in lane %r not found" % (change["name"], change.get("lane")))
            continue
        row, field = rows[0], change["field"]
        if row.get(field) != change["old"] and str(row.get(field)) != str(change["old"]):
            skipped += 1
            print("  SKIP catalog: %r %s is %r, expected %r" % (change["name"], field, row.get(field), change["old"]))
            continue
        row[field] = int(change["new"]) if field == "year" else change["new"]
        applied += 1
    for lane, path in CATALOG_FILES.items():
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(catalogs[lane], handle, indent=1, ensure_ascii=False)
    return applied, skipped


def main():
    parser = argparse.ArgumentParser(description="Apply audit edits to report parts and catalog files.")
    parser.add_argument("--text", nargs="*", default=[], help="JSON files of text edits (relative to the campaign folder)")
    parser.add_argument("--catalog", nargs="*", default=[], help="JSON files of catalog changes (relative to the campaign folder)")
    args = parser.parse_args()
    for path in args.text:
        applied, skipped = apply_text_edits(os.path.join(CAMPAIGN_DIR, path))
        print("%s: %d applied, %d skipped" % (path, applied, skipped))
    for path in args.catalog:
        applied, skipped = apply_catalog_changes(os.path.join(CAMPAIGN_DIR, path))
        print("%s: %d applied, %d skipped" % (path, applied, skipped))


if __name__ == "__main__":
    main()
