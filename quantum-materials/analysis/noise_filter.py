#!/usr/bin/env python3
"""Q6 noise filter: score contested / unreplicated preprint claims.

Reads corpus/*.jsonl (local only, no network) and the claim definitions with
hand-read stance labels in analysis/q6_claims.py, then

  1. checks that every cited id exists in the corpus,
  2. counts topic hits and labelled supportive / critical / neutral preprints per claim,
  3. computes the checkable noise score (features F1-F7 below) with evidence,
  4. sweeps the whole arXiv corpus for Comment / Reply / null-result / Revisiting titles
     and withdrawn / retracted records,
  5. writes analysis/q6.json and prints a short report.

Noise score (a claim is flagged NOISY if score >= 3):

  F1 +2  no independent-group replication in the corpus: no supportive EXPERIMENT by a
         group other than the original group (and the originals are not themselves two
         independent observations)
  F2 +1  per Comment / Reply / Response record or null-result experiment in the thread
         (in window), max +2
  F3 +3  an original or supportive record says it is withdrawn / retracted (arXiv comment)
  F4 +1  the original abstract uses single-sample / filamentary / onset-only / small-fraction
         / "signs of possible" language
  F5 +1  original has no DOI, journal-ref or "accepted/in press" note > 12 months after posting
     -1  original is linked to a peer-reviewed venue (metadata, or known_venue from scout notes)
  F6 +1  there are positive follow-ups and ALL of them come from the original group
  F7 +1  (added in this iteration) critical in-window records outnumber supportive ones

A claim that is not NOISY but has F1 = +2 (single group, nothing independent yet) is
marked "watch".

"Same group" = the record shares at least one author (first initial + surname) with the
claim's original_group list. Distinct groups are counted by last author, with every
original-group paper merged into one group.

Usage:  python3 analysis/noise_filter.py
"""

import datetime
import glob
import json
import os
import re
import sys
import unicodedata
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
QM_DIR = os.path.dirname(HERE)
CORPUS_DIR = os.path.join(QM_DIR, "corpus")
OUTPUT_PATH = os.path.join(HERE, "q6.json")
sys.path.insert(0, HERE)

import taxonomy  # noqa: E402
from q6_claims import CLAIMS, Q6_SELECTION  # noqa: E402

RUN_DATE = datetime.date(2026, 9, 23)
NOISY_THRESHOLD = 3
WINDOWS = ("trailing", "preceding")

# --------------------------------------------------------------------------- regexes

# F4: weak-evidence language in the original abstract
WEAK_EVIDENCE = re.compile(
    r"\bonset\b|filamentar|volume fraction|fractions? \(?<|<\s?\d+(?:\.\d+)?\s?%|"
    r"sample[- ]dependen|single (?:sample|device)\b|\bone device\b|signs? of possible|"
    r"\bpossible (?:high|room)[- ]temperature superconduct|local superconductivity|"
    r"not reproducib|\bhints? of\b",
    re.IGNORECASE)

# F5: arXiv comment field that links to a venue
VENUE_NOTE = re.compile(r"\b(?:accepted|in press|to appear|published in)\b", re.IGNORECASE)

# F3 and sweep: the record itself is withdrawn / retracted (not "supersedes a withdrawn ...")
WITHDRAWN = re.compile(
    r"(?:paper|article|manuscript|submission|version|preprint) (?:has been|is being|is|was) withdrawn"
    r"|withdrawn by the (?:submitting )?authors?|(?:have|has) withdrawn this"
    r"|\bretracted\b|(?<!deformation )\bretraction\b",
    re.IGNORECASE)

# Sweep categories (title only). Order matters: first match wins.
SWEEP_PATTERNS = OrderedDict([
    ("comment_reply", re.compile(
        r"\bcomment on\b|\breply to\b|^reply\b|\bresponse to (?:the |recent )?(?:comments?|critique|arxiv)"
        r"|matters arising|\brebuttal\b", re.IGNORECASE)),
    ("null_result", re.compile(
        r"(?<!in the )(?<!presence or )(?<!presence versus )\babsence of\b|\bno evidence\b|\bfailure to\b",
        re.IGNORECASE)),
    ("revisit", re.compile(r"^revisit|\bre-?examination\b|^reexamin", re.IGNORECASE)),
])

# --------------------------------------------------------------------------- corpus


def load_corpus():
    """All corpus records keyed by canonical id (corpus/raw is ignored)."""
    records = {}
    for path in sorted(glob.glob(os.path.join(CORPUS_DIR, "*.jsonl"))):
        with open(path) as handle:
            for line in handle:
                record = json.loads(line)
                records[record["id"]] = record
    return records


def strip_accents(text):
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def person_key(name):
    """'Takasada Shibauchi', 'T. Shibauchi', 'Shibauchi, T.' -> 't shibauchi'."""
    name = strip_accents(name or "").strip()
    if "," in name:  # OSTI style "Surname, Given"
        surname, given = [part.strip() for part in name.split(",", 1)]
    else:
        parts = name.replace(".", ". ").split()
        if not parts:
            return ""
        surname, given = parts[-1], " ".join(parts[:-1])
    initial = given[:1].lower() if given else ""
    return "%s %s" % (initial, surname.lower())


def last_author_key(record):
    authors = record.get("authors") or []
    return person_key(authors[-1]) if authors else ""


def is_peer_reviewed(record):
    extra = record.get("extra") or {}
    if record.get("server") == "arxiv":
        if record.get("doi") or extra.get("journal_ref"):
            return True
        return bool(VENUE_NOTE.search(extra.get("comment") or ""))
    return bool(extra.get("is_preprint_of"))


def is_withdrawn(record):
    return bool(WITHDRAWN.search((record.get("extra") or {}).get("comment") or ""))


def age_days(record):
    date = datetime.datetime.strptime(record["date"], "%Y-%m-%d").date()
    return (RUN_DATE - date).days


def short(record):
    return {"id": record["id"], "date": record["date"], "window": record["window"],
            "title": taxonomy.normalize_text(record["title"]),
            "last_author": (record.get("authors") or [""])[-1]}

# --------------------------------------------------------------------------- claims


def original_group_keys(claim, records):
    names = list(claim.get("original_group") or [])
    if not names:
        for original_id in claim["original_ids"]:
            authors = records[original_id].get("authors") or []
            if authors:
                names.append(authors[-1])
    return set(person_key(name) for name in names)


def same_group(record, group_keys):
    return any(person_key(name) in group_keys for name in record.get("authors") or [])


def topic_hits(claim, records):
    patterns = [re.compile(p, re.IGNORECASE) for p in claim["topic_patterns"]]
    hits = []
    for record in records.values():
        text = taxonomy.record_text(record)
        if all(p.search(text) for p in patterns):
            hits.append(record)
    return hits


def labelled_records(claim, records):
    """(record, stance, kind, note, same_group) for each label."""
    group = original_group_keys(claim, records)
    rows = []
    for record_id, (stance, kind, note) in claim["labels"].items():
        record = records[record_id]
        rows.append({"record": record, "stance": stance, "kind": kind, "note": note,
                     "same_group": same_group(record, group)})
    return rows


def count_groups(rows, stance):
    """Distinct research groups (last author; original group merged into one)."""
    groups = set()
    for row in rows:
        if row["stance"] != stance:
            continue
        groups.add("ORIGINAL" if row["same_group"] else last_author_key(row["record"]))
    return len(groups)


def tally(rows):
    in_window = [r for r in rows if r["record"]["window"] in WINDOWS]
    counts = {}
    for stance in ("supportive", "critical", "neutral"):
        subset = [r for r in in_window if r["stance"] == stance]
        counts[stance] = {
            "all": len(subset),
            "experiments": sum(1 for r in subset if r["kind"] == "exp"),
            "trailing": sum(1 for r in subset if r["record"]["window"] == "trailing"),
            "preceding": sum(1 for r in subset if r["record"]["window"] == "preceding"),
            "distinct_groups": count_groups(subset, stance),
        }
    counts["supportive"]["independent_experiments"] = sum(
        1 for r in in_window
        if r["stance"] == "supportive" and r["kind"] == "exp" and not r["same_group"])
    return counts

# --------------------------------------------------------------------------- features


def feature_f1(claim, rows, originals):
    independent = [r for r in rows if r["stance"] == "supportive" and r["kind"] == "exp"
                   and not r["same_group"]]
    if independent:
        return 0, "independent supportive experiments: " + ", ".join(
            r["record"]["id"] for r in independent[:6])
    if claim.get("originals_independent") and len(originals) >= 2:
        return 0, "originals are two independent observations: " + ", ".join(
            o["id"] for o in originals)
    return 2, "no supportive experiment from outside the original group in the corpus"


def feature_f2(rows):
    hits = [r for r in rows if r["record"]["window"] in WINDOWS
            and (r["kind"] == "comment" or (r["stance"] == "critical" and r["kind"] == "exp"))]
    if not hits:
        return 0, "no Comment/Reply or null-result preprint in window"
    ids = [r["record"]["id"] for r in hits]
    return min(2, len(hits)), "%d Comment/Reply/null records, e.g. %s" % (len(hits), ", ".join(ids[:5]))


def feature_f3(rows, originals):
    candidates = list(originals) + [r["record"] for r in rows if r["stance"] == "supportive"]
    withdrawn = [rec["id"] for rec in candidates if is_withdrawn(rec)]
    if withdrawn:
        return 3, "withdrawn/retracted: " + ", ".join(withdrawn)
    return 0, "no withdrawal/retraction note on original or supportive records"


def feature_f4(originals):
    for record in originals:
        text = taxonomy.record_text(record)
        match = WEAK_EVIDENCE.search(text)
        if match:
            start = max(0, match.start() - 50)
            return 1, "%s: '...%s...'" % (record["id"], text[start:match.end() + 50])
    if not originals:
        return 0, "no original record in corpus"
    return 0, "no weak-evidence phrase in original abstract(s)"


def feature_f5(claim, originals):
    reviewed = [o["id"] for o in originals if is_peer_reviewed(o)]
    if reviewed:
        return -1, "peer-reviewed venue in metadata: " + ", ".join(reviewed)
    if claim.get("known_venue"):
        return -1, "venue known from scout notes: " + claim["known_venue"]
    if not originals:
        return 0, "no original record in corpus"
    oldest = max(originals, key=age_days)
    if age_days(oldest) > 365:
        return 1, "%s: no DOI/journal-ref %d days after posting" % (oldest["id"], age_days(oldest))
    return 0, "%s: no venue yet, but only %d days old" % (oldest["id"], age_days(oldest))


def feature_f6(rows):
    positive = [r for r in rows if r["stance"] == "supportive"]
    if not positive:
        return 0, "no positive follow-ups at all"
    if all(r["same_group"] for r in positive):
        return 1, "all %d positive follow-ups share the original group: %s" % (
            len(positive), ", ".join(r["record"]["id"] for r in positive))
    return 0, "%d of %d positive follow-ups from other groups" % (
        sum(1 for r in positive if not r["same_group"]), len(positive))


def feature_f7(counts):
    supportive, critical = counts["supportive"]["all"], counts["critical"]["all"]
    if critical > supportive:
        return 1, "critical %d > supportive %d (in window)" % (critical, supportive)
    return 0, "critical %d <= supportive %d (in window)" % (critical, supportive)


def score_claim(claim, records):
    originals = [records[i] for i in claim["original_ids"]]
    rows = labelled_records(claim, records)
    counts = tally(rows)
    features = OrderedDict()
    features["F1_no_independent_replication"] = feature_f1(claim, rows, originals)
    features["F2_comment_reply_null"] = feature_f2(rows)
    features["F3_withdrawn_retracted"] = feature_f3(rows, originals)
    features["F4_weak_evidence_language"] = feature_f4(originals)
    features["F5_publication_linkage"] = feature_f5(claim, originals)
    features["F6_positive_only_from_original_group"] = feature_f6(rows)
    features["F7_critical_outnumber_supportive"] = feature_f7(counts)
    score = sum(value for value, _ in features.values())
    hits = topic_hits(claim, records)
    return {
        "key": claim["key"],
        "name": claim["name"],
        "claim": claim["claim"],
        "material": claim["material"],
        "status": claim["status"],
        "status_note": claim["status_note"],
        "noise_score": score,
        "noisy": score >= NOISY_THRESHOLD,
        # single-group claim that the score does not (yet) flag, e.g. young and peer reviewed
        "watch": score < NOISY_THRESHOLD and features["F1_no_independent_replication"][0] == 2,
        "features": OrderedDict((k, {"points": v, "evidence": e}) for k, (v, e) in features.items()),
        "counts_in_window": counts,
        "topic_hits": {
            "patterns": claim["topic_patterns"],
            "trailing": sum(1 for r in hits if r["window"] == "trailing"),
            "preceding": sum(1 for r in hits if r["window"] == "preceding"),
            "labelled_share": "%d labelled of %d in-window topic hits" % (
                sum(1 for r in hits if r["window"] in WINDOWS and r["id"] in claim["labels"]),
                sum(1 for r in hits if r["window"] in WINDOWS)),
        },
        "originals": [short(o) for o in originals],
        "evidence": [dict(short(r["record"]), stance=r["stance"], kind=r["kind"],
                          same_group=r["same_group"], note=r["note"]) for r in rows],
    }

# --------------------------------------------------------------------------- sweep


def sweep_arxiv(records):
    """Comment/Reply, null-result and Revisiting titles plus withdrawn records (arxiv.jsonl only)."""
    rows = []
    for record in records.values():
        if record["server"] != "arxiv" or (record.get("extra") or {}).get("supplement"):
            continue
        title = taxonomy.normalize_text(record["title"])
        category = None
        for name, pattern in SWEEP_PATTERNS.items():
            if pattern.search(title):
                category = name
                break
        if is_withdrawn(record):
            category = "withdrawn" if category is None else category + "+withdrawn"
        if category is None:
            continue
        text = taxonomy.record_text(record)
        rows.append(dict(short(record), category=category,
                         in_scope=taxonomy.in_scope(record, text),
                         cluster=taxonomy.primary_cluster(text)))
    rows.sort(key=lambda row: (row["category"], row["date"]))
    counts = Counter()
    clusters = Counter()
    for row in rows:
        for part in row["category"].split("+"):
            counts[(part, str(row["window"]))] += 1
        if row["category"] != "revisit":
            clusters[row["cluster"] or "unclassified"] += 1
    table = OrderedDict()
    for part in ("comment_reply", "null_result", "revisit", "withdrawn"):
        table[part] = {w: counts[(part, w)] for w in WINDOWS}
    return {
        "definition": {name: pattern.pattern for name, pattern in SWEEP_PATTERNS.items()},
        "withdrawn_definition": WITHDRAWN.pattern,
        "scope": "corpus/arxiv.jsonl titles (supplement excluded); withdrawn from extra.comment",
        "counts_by_window": table,
        "in_scope_share": "%d of %d" % (sum(1 for r in rows if r["in_scope"]), len(rows)),
        "top_clusters_excluding_revisit": clusters.most_common(10),
        "records": rows,
    }

# --------------------------------------------------------------------------- main


def check_ids(records):
    missing = []
    for claim in CLAIMS:
        for record_id in list(claim["original_ids"]) + list(claim["labels"]):
            if record_id not in records:
                missing.append((claim["key"], record_id))
    return missing


def filter_definition():
    return OrderedDict([
        ("threshold", "noisy if score >= %d" % NOISY_THRESHOLD),
        ("F1", "+2 no independent-group supportive experiment in corpus"),
        ("F2", "+1 per in-window Comment/Reply/Response or null-result experiment, max +2"),
        ("F3", "+3 original or supportive record withdrawn/retracted (arXiv comment)"),
        ("F4", "+1 single-sample / filamentary / onset-only / small-fraction language in original abstract"),
        ("F5", "+1 original lacks DOI/journal-ref/'accepted' note > 12 months after posting; "
               "-1 if linked to a peer-reviewed venue"),
        ("F6", "+1 positive follow-ups exist and all share an author with the original group"),
        ("F7", "+1 in-window critical records outnumber supportive ones (added this iteration)"),
        ("same_group", "shares >= 1 author (first initial + surname) with original_group"),
        ("distinct_groups", "distinct last authors; original-group papers merged into one"),
    ])


def print_report(output):
    print("Q6 noise filter (run date %s)" % RUN_DATE)
    print("%-36s %-21s %5s %5s  %-9s %-9s" % ("claim", "status", "score", "noisy", "sup(grp)", "crit(grp)"))
    for result in sorted(output["claims"], key=lambda r: -r["noise_score"]):
        counts = result["counts_in_window"]
        print("%-36s %-21s %5d %5s  %3d (%2d)  %3d (%2d)" % (
            result["key"][:36], result["status"], result["noise_score"],
            "yes" if result["noisy"] else ("watch" if result["watch"] else "no"),
            counts["supportive"]["all"], counts["supportive"]["distinct_groups"],
            counts["critical"]["all"], counts["critical"]["distinct_groups"]))
    print("\nsweep counts (arXiv titles / comments):")
    for name, by_window in output["sweep"]["counts_by_window"].items():
        print("  %-14s trailing %3d  preceding %3d" % (name, by_window["trailing"], by_window["preceding"]))
    print("  top clusters:", output["sweep"]["top_clusters_excluding_revisit"][:6])


def main():
    records = load_corpus()
    missing = check_ids(records)
    if missing:
        for key, record_id in missing:
            print("MISSING in corpus: %s (%s)" % (record_id, key))
        sys.exit(1)
    claims = [score_claim(claim, records) for claim in CLAIMS]
    by_key = dict((c["key"], c) for c in claims)
    output = OrderedDict([
        ("generated", RUN_DATE.isoformat()),
        ("windows", {"trailing": ["2025-09-24", "2026-09-23"], "preceding": ["2024-09-24", "2025-09-23"]}),
        ("filter_definition", filter_definition()),
        ("q6_selection", sorted(Q6_SELECTION, key=lambda k: -by_key[k]["noise_score"])),
        ("claims", claims),
        ("sweep", sweep_arxiv(records)),
    ])
    with open(OUTPUT_PATH, "w") as handle:
        json.dump(output, handle, indent=1, ensure_ascii=False)
    print_report(output)
    print("\nwrote %s" % OUTPUT_PATH)


if __name__ == "__main__":
    main()
