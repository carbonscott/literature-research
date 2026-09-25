"""Merge the research lanes' notes into the report's input files.

Reads (from ../notes/):
  q1.refs.json ... q5.refs.json          references gathered by each lane
  catalog_general.json, catalog_facility.json   catalog rows

Writes (next to this script):
  refs.json         one entry per distinct work (deduplicated by DOI / arXiv ID / URL)
  catalog.json      all catalog rows, with ref_key rewritten to the canonical key
  key_aliases.json  {lane key: canonical key} for every key that was merged away

The first lane that lists a work (in the order q1, q4, q2, q3, q5) supplies its
canonical key and metadata. Report text must use canonical keys.

Usage (from the repository root):
  python agents-in-science-workflow/report/merge_notes.py
"""
import json
import os
import re

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_DIR = os.path.join(os.path.dirname(REPORT_DIR), "notes")

# Order decides which lane's key becomes canonical for a shared work.
LANE_FILES = ["q1.refs.json", "q4.refs.json", "q2.refs.json", "q3.refs.json", "q5.refs.json"]
CATALOG_FILES = ["catalog_general.json", "catalog_facility.json"]

# The same work cited as an arXiv preprint by one lane and as its published
# DOI by another. ID matching cannot see these; the published version wins.
PREPRINT_TO_PUBLISHED = {
    "eaa": "q4_eaa",          # arXiv 2602.15294 -> npj Comput Mater 2026
    "neudiff": "q4_neudiff",  # arXiv 2602.16812 -> J Appl Cryst 2026
}


def identity_of(ref):
    """Return a normalized identifier so the same work from two lanes compares equal."""
    kind = ref["kind"]
    value = ref["id"].strip()
    if kind == "doi":
        value = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", value, flags=re.I).lower()
    elif kind == "arxiv":
        value = re.sub(r"^arxiv:", "", value, flags=re.I)
        value = re.sub(r"v\d+$", "", value)
    elif kind == "url":
        value = value.rstrip("/")
    return kind + ":" + value


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main():
    merged_refs = []
    canonical_key_by_identity = {}
    aliases = {}
    lane_key_counts = {}

    for lane_file in LANE_FILES:
        lane_refs = load_json(os.path.join(NOTES_DIR, lane_file))
        lane_key_counts[lane_file] = len(lane_refs)
        for ref in lane_refs:
            if ref["key"] in PREPRINT_TO_PUBLISHED:
                aliases[ref["key"]] = PREPRINT_TO_PUBLISHED[ref["key"]]
                continue
            identity = identity_of(ref)
            if identity in canonical_key_by_identity:
                canonical_key = canonical_key_by_identity[identity]
                if ref["key"] != canonical_key:
                    if aliases.get(ref["key"], canonical_key) != canonical_key:
                        raise SystemExit("lane key %r means different works in different lanes (%s vs %s); rename it in the notes"
                                         % (ref["key"], aliases[ref["key"]], canonical_key))
                    aliases[ref["key"]] = canonical_key
                continue
            if any(existing["key"] == ref["key"] for existing in merged_refs):
                raise SystemExit("key %r names two different works (%s)" % (ref["key"], identity))
            canonical_key_by_identity[identity] = ref["key"]
            ref = dict(ref)
            ref["lane"] = lane_file.split(".")[0]
            merged_refs.append(ref)

    known_keys = {ref["key"] for ref in merged_refs}
    ambiguous = sorted(key for key in aliases if key in known_keys)
    if ambiguous:
        raise SystemExit("keys are both canonical and aliased (rename them in the notes): %s" % ", ".join(ambiguous))
    merged_catalog = []
    for catalog_file in CATALOG_FILES:
        for row in load_json(os.path.join(NOTES_DIR, catalog_file)):
            row = dict(row)
            row["lane"] = "facility" if "facility" in catalog_file else "general"
            row["ref_key"] = aliases.get(row["ref_key"], row["ref_key"])
            if row["ref_key"] not in known_keys:
                raise SystemExit("catalog row %r cites unknown key %r" % (row["name"], row["ref_key"]))
            merged_catalog.append(row)

    with open(os.path.join(REPORT_DIR, "refs.json"), "w", encoding="utf-8") as handle:
        json.dump(merged_refs, handle, indent=1, ensure_ascii=False)
    with open(os.path.join(REPORT_DIR, "catalog.json"), "w", encoding="utf-8") as handle:
        json.dump(merged_catalog, handle, indent=1, ensure_ascii=False)
    with open(os.path.join(REPORT_DIR, "key_aliases.json"), "w", encoding="utf-8") as handle:
        json.dump(aliases, handle, indent=1, sort_keys=True)

    kinds = {}
    for ref in merged_refs:
        kinds[ref["kind"]] = kinds.get(ref["kind"], 0) + 1
    print("lane refs:", lane_key_counts, "total", sum(lane_key_counts.values()))
    print("merged refs:", len(merged_refs), kinds)
    print("aliases (duplicates merged):", len(aliases))
    print("catalog rows:", len(merged_catalog))


if __name__ == "__main__":
    main()
