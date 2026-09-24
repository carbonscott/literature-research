#!/usr/bin/env python3
"""Q5 Beyond arXiv: what do the non-arXiv servers add to the quantum-materials landscape?

Reads only local files:
    corpus/<server>.jsonl, corpus/arxiv.jsonl
    corpus/crossref_harvest_log.json, corpus/native_harvest_log.json
    analysis/q5_audit.json      (hand-written audit labels; see --print-sample)
    analysis/classified.jsonl   (optional; taxonomy v2 topic labels)

Writes analysis/q5.json.

Usage:
    python3 q5_beyond_arxiv.py --print-sample   # print the deterministic audit sample to label
    python3 q5_beyond_arxiv.py                  # compute everything -> analysis/q5.json

Audit sample: for each server, records inside the two windows are sorted by id and
random.Random(11).sample(...) picks up to 25 (a fresh Random(11) per server).
"""

import argparse
import collections
import json
import os
import random
import re
import sys
import unicodedata

ANALYSIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(ANALYSIS_DIR)
CORPUS_DIR = os.path.join(PROJECT_DIR, "corpus")
AUDIT_PATH = os.path.join(ANALYSIS_DIR, "q5_audit.json")
CLASSIFIED_PATH = os.path.join(ANALYSIS_DIR, "classified.jsonl")
OUTPUT_PATH = os.path.join(ANALYSIS_DIR, "q5.json")

CROSSREF_SERVERS = ["chemrxiv", "researchsquare", "preprints_org", "techrxiv"]
NATIVE_SERVERS = ["zenodo", "hal", "osti"]
SERVERS = CROSSREF_SERVERS + NATIVE_SERVERS

AUDIT_SAMPLE_SIZE = 25
AUDIT_SEED = 11
JACCARD_THRESHOLD = 0.8
AUDIT_LABELS = ["on_topic_research", "off_topic", "fringe_or_pseudoscience",
                "duplicate_of_arxiv", "dataset_or_report"]
IN_WINDOWS = ("trailing", "preceding")

# Very common title words carry no identity; dropping them makes Jaccard stricter.
STOPWORDS = set("a an the of in on and or for to with by from at as via is are its "
                "into under using based between near".split())


# ------------------------------------------------------------------ loading

def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_server(server):
    return load_jsonl(os.path.join(CORPUS_DIR, server + ".jsonl"))


def load_json(name):
    with open(os.path.join(CORPUS_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


def in_window(records):
    return [r for r in records if r.get("window") in IN_WINDOWS]


# ------------------------------------------------------------------ title normalization

LATEX_COMMAND = re.compile(r"\\[a-zA-Z]+")
NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_title(title):
    """Lowercase, drop accents, LaTeX commands, $ and punctuation; collapse spaces."""
    text = unicodedata.normalize("NFKD", title or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = LATEX_COMMAND.sub(" ", text)
    text = text.replace("$", " ").lower()
    text = NON_ALNUM.sub(" ", text)
    return " ".join(text.split())


def title_tokens(normalized):
    return frozenset(t for t in normalized.split() if t not in STOPWORDS)


def jaccard(tokens_a, tokens_b):
    union = len(tokens_a | tokens_b)
    return len(tokens_a & tokens_b) / union if union else 0.0


# ------------------------------------------------------------------ arXiv title index

class ArxivTitleIndex(object):
    """Exact-title lookup plus prefix-filtered token-set Jaccard search.

    Prefix filtering: order each title's tokens from rarest to most common. Two sets
    with Jaccard >= t must share at least one token among the first
    len(A) - ceil(t * len(A)) + 1 tokens of A, so indexing only those "prefix"
    tokens finds every candidate pair without comparing against all titles.
    """

    def __init__(self, arxiv_records, threshold):
        self.threshold = threshold
        self.exact = {}
        self.ids = set()
        self.token_sets = []
        self.record_ids = []
        for record in arxiv_records:
            self.ids.add(record["id"])
            normalized = normalize_title(record["title"])
            if not normalized:
                continue
            self.exact.setdefault(normalized, record["id"])
            self.token_sets.append(title_tokens(normalized))
            self.record_ids.append(record["id"])
        self.doc_freq = collections.Counter(t for s in self.token_sets for t in s)
        self.prefix_index = collections.defaultdict(list)
        for position, tokens in enumerate(self.token_sets):
            for token in self.prefix_tokens(tokens):
                self.prefix_index[token].append(position)

    def prefix_tokens(self, tokens):
        ordered = sorted(tokens, key=lambda t: (self.doc_freq.get(t, 0), t))
        min_overlap = int(-(-self.threshold * len(ordered) // 1))  # ceil
        return ordered[:len(ordered) - min_overlap + 1]

    def find(self, title):
        """Return (match_type, arxiv_id, score) or (None, None, 0.0)."""
        normalized = normalize_title(title)
        if not normalized:
            return None, None, 0.0
        if normalized in self.exact:
            return "exact", self.exact[normalized], 1.0
        tokens = title_tokens(normalized)
        if len(tokens) < 4:
            return None, None, 0.0  # too short for a reliable fuzzy match
        best_score, best_id = 0.0, None
        candidates = set()
        for token in self.prefix_tokens(tokens):
            candidates.update(self.prefix_index.get(token, ()))
        for position in candidates:
            score = jaccard(tokens, self.token_sets[position])
            if score > best_score:
                best_score, best_id = score, self.record_ids[position]
        if best_score >= self.threshold:
            return "near", best_id, round(best_score, 3)
        return None, None, 0.0


def arxiv_overlap(records, index):
    """Per-record arXiv overlap: declared arXiv id and/or title match."""
    rows = []
    for record in records:
        match_type, match_id, score = index.find(record["title"])
        declared = record.get("arxiv_id")
        rows.append({
            "id": record["id"],
            "declared_arxiv_id": declared,
            "declared_in_arxiv_corpus": bool(declared) and ("arXiv:" + declared.replace("arXiv:", "")) in index.ids,
            "title_match": match_type,
            "title_match_id": match_id,
            "title_match_score": score,
            "on_arxiv": bool(declared) or match_type is not None,
        })
    return rows


def summarize_overlap(rows):
    n = len(rows)
    declared = sum(1 for r in rows if r["declared_arxiv_id"])
    exact = sum(1 for r in rows if r["title_match"] == "exact")
    near = sum(1 for r in rows if r["title_match"] == "near")
    title_any = exact + near
    declared_and_title = sum(1 for r in rows if r["declared_arxiv_id"] and r["title_match"])
    on_arxiv = sum(1 for r in rows if r["on_arxiv"])
    return {
        "n": n,
        "declared_arxiv_id": declared,
        "declared_arxiv_share": share(declared, n),
        "declared_found_in_arxiv_corpus": sum(1 for r in rows if r["declared_in_arxiv_corpus"]),
        "title_exact": exact,
        "title_near": near,
        "title_dup_share": share(title_any, n),
        "declared_and_title": declared_and_title,
        "on_arxiv_union": on_arxiv,
        "arxiv_dup_share": share(on_arxiv, n),
        "near_match_examples": [
            {"id": r["id"], "arxiv": r["title_match_id"], "score": r["title_match_score"]}
            for r in rows if r["title_match"] == "near"][:5],
    }


def share(part, whole):
    return round(part / whole, 4) if whole else None


# ------------------------------------------------------------------ query-level yield

def crossref_yield(log, server):
    entry = log["servers"][server]
    summary = entry["summary"]
    terms = [{"term": t["term"], "api_total": t["total_results"], "fetched": t["fetched"],
              "kept": t["kept_after_phrase_filter"]} for t in entry["terms"]]
    return {
        "api_total": summary["crossref_total_results_sum"],
        "fetched": summary["fetched_sum"],
        "kept_hits": summary["kept_sum"],
        "unique_records": summary["unique_records"],
        "kept_per_fetched": share(summary["kept_sum"], summary["fetched_sum"]),
        "truncated_terms": summary["truncated_terms"],
        "top_terms": terms_by_kept(terms),
        "zero_yield_terms": [t["term"] for t in terms if t["kept"] == 0],
    }


def native_yield(log, server):
    entry = log["servers"][server]
    terms = [{"term": t["term"], "api_total": t["api_total"], "fetched": t["fetched"],
              "kept": t["kept"]} for t in entry["terms"]]
    fetched = sum(t["fetched"] for t in terms)
    kept = sum(t["kept"] for t in terms)
    return {
        "api_total": sum(t["api_total"] for t in terms),
        "fetched": fetched,
        "kept_hits": kept,
        "unique_records": entry["unique_kept"],
        "kept_per_fetched": share(kept, fetched),
        "truncated_terms": [t["term"] for t in entry["terms"] if t["truncated"]],
        "top_terms": terms_by_kept(terms),
        "zero_yield_terms": [t["term"] for t in terms if t["kept"] == 0],
    }


def terms_by_kept(terms, limit=6):
    ordered = sorted(terms, key=lambda t: -t["kept"])
    return [[t["term"], t["kept"], t["api_total"]] for t in ordered[:limit] if t["kept"]]


# ------------------------------------------------------------------ publication linkage & dates

JOURNAL_DOI_EXCLUDE = ("10.2172/", "10.5281/", "10.26434/", "10.21203/", "10.20944/", "10.36227/")


def publication_linkage(server, records):
    """Share of records with evidence of a journal version."""
    n = len(records)
    if server in CROSSREF_SERVERS:
        linked = sum(1 for r in records if r["extra"].get("is_preprint_of"))
        how = "Crossref relation is-preprint-of (extra.is_preprint_of)"
    elif server == "hal":
        linked = sum(1 for r in records if r.get("doi"))
        how = "HAL doiId_s present (journal DOI attached to a record still typed as preprint)"
    elif server == "osti":
        linked = sum(1 for r in records if r["extra"].get("journal_name")
                     or (r.get("doi") and not r["doi"].startswith(JOURNAL_DOI_EXCLUDE)))
        how = "OSTI journal_name or a non-OSTI DOI (most OSTI records ARE journal accepted manuscripts)"
    else:
        linked = 0
        how = "not recorded in harvest (Zenodo related_identifiers were not kept)"
    return {"linked": linked, "share": share(linked, n), "method": how}


def date_caveats(server, records):
    """Server-specific evidence that `date` is not the first public posting."""
    n = len(records)
    if server == "osti":
        types = collections.Counter(r["extra"].get("product_type") for r in records)
        article_types = collections.Counter(r["extra"].get("article_type") or "none" for r in records)
        later_entry = sum(1 for r in records if r["extra"].get("entry_date", "")[:7] > r["date"][:7])
        return {
            "product_type": dict(types.most_common()),
            "article_type": dict(article_types.most_common()),
            "entry_month_after_publication_month": later_entry,
            "note": "date = OSTI publication_date (journal/report date), not first posting; "
                    "entry_date lags; many items were on arXiv months earlier.",
        }
    if server == "hal":
        produced_older = sum(1 for r in records
                             if (r["extra"].get("producedDate") or "9999")[:10] < r["date"])
        return {
            "produced_before_submitted": produced_older,
            "note": "Harvest kept docType UNDEFINED (preprint). HAL retypes a deposit once its "
                    "journal version is added, so older windows lose records: survivorship bias "
                    "toward recent, still-unpublished preprints.",
        }
    if server == "zenodo":
        differs = sum(1 for r in records if (r["extra"].get("created") or "")[:10] != r["date"])
        return {
            "publication_date_differs_from_upload": differs,
            "note": "date = user-declared publication_date (upload date only if partial).",
        }
    later_versions = sum(1 for r in records if len(r["extra"].get("versions") or []) > 1)
    return {
        "records_with_multiple_versions": later_versions,
        "note": "date = posted date of v1 (Crossref posted-content); window filter used posted date.",
    }


def dup_share_by_quarter(records, overlap_rows):
    """arXiv-duplicate share per calendar quarter of the server's `date`."""
    totals = collections.defaultdict(lambda: [0, 0])
    for record in records:
        quarter = "%sQ%d" % (record["date"][:4], (int(record["date"][5:7]) - 1) // 3 + 1)
        totals[quarter][0] += 1
        totals[quarter][1] += 1 if overlap_rows[record["id"]]["on_arxiv"] else 0
    return {q: {"n": n, "dup_share": share(d, n)} for q, (n, d) in sorted(totals.items())}


# The arXiv corpus starts 2024-09-24, but journal-dated OSTI records typically follow
# their arXiv version by months (median lead ~4 months), so early-dated OSTI records
# look "unique" only because their arXiv version predates the harvest. Records dated
# from this cutoff on have their arXiv versions (if any) inside the arXiv corpus.
LATE_CUTOFF = "2026-01-01"


def late_dup_share(records, overlap_rows):
    late = [r for r in records if r["date"] >= LATE_CUTOFF]
    dups = sum(1 for r in late if overlap_rows[r["id"]]["on_arxiv"])
    return {"cutoff": LATE_CUTOFF, "n": len(late), "dup_share": share(dups, len(late))}


def monthly_counts(records):
    return dict(sorted(collections.Counter(r["date"][:7] for r in records).items()))


def top_first_authors(records, limit=5):
    counts = collections.Counter(r["authors"][0] for r in records if r.get("authors"))
    return counts.most_common(limit)


# ------------------------------------------------------------------ audit

def audit_sample(records):
    ordered = sorted(in_window(records), key=lambda r: r["id"])
    rng = random.Random(AUDIT_SEED)
    return rng.sample(ordered, min(AUDIT_SAMPLE_SIZE, len(ordered)))


def print_sample(server_records, overlap_by_id):
    for server in SERVERS:
        print("=" * 30, server)
        for record in audit_sample(server_records[server]):
            overlap = overlap_by_id[record["id"]]
            flag = ""
            if overlap["on_arxiv"]:
                flag = " [ARXIV declared=%s title=%s %s]" % (
                    overlap["declared_arxiv_id"], overlap["title_match"], overlap["title_match_id"])
            extra = record["extra"]
            kind = extra.get("product_type") or extra.get("group_title") or ""
            print("\n## %s | %s | %s%s" % (record["id"], record["date"], kind, flag))
            print("T: " + record["title"])
            print("A: " + (record.get("abstract") or "")[:700])


def load_audit():
    if not os.path.exists(AUDIT_PATH):
        sys.exit("missing %s; run --print-sample and label first" % AUDIT_PATH)
    with open(AUDIT_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def audit_rates(server, entries, expected_ids):
    got_ids = [e["id"] for e in entries]
    if sorted(got_ids) != sorted(expected_ids):
        sys.exit("audit ids for %s do not match the deterministic sample" % server)
    counts = collections.Counter(e["label"] for e in entries)
    unknown = set(counts) - set(AUDIT_LABELS)
    if unknown:
        sys.exit("unknown labels for %s: %s" % (server, unknown))
    n = len(entries)
    not_duplicate = n - counts["duplicate_of_arxiv"]
    rates = {label: share(counts[label], n) for label in AUDIT_LABELS}
    on_topic_content = counts["on_topic_research"] + sum(
        1 for e in entries if e.get("dup_content") == "on_topic")
    return {
        "n": n,
        "counts": {label: counts[label] for label in AUDIT_LABELS},
        "rates": rates,
        # Subject relevance regardless of arXiv overlap (duplicates judged on content).
        "on_topic_content_rate_incl_duplicates": share(on_topic_content, n),
        # Used for the unique estimate: on-topic share among records NOT on arXiv,
        # so the arXiv-duplicate share is not subtracted twice.
        "on_topic_rate_among_non_duplicates": share(counts["on_topic_research"], not_duplicate),
        "interval_95_on_topic_non_dup": wilson_interval(counts["on_topic_research"], not_duplicate),
    }


def wilson_interval(successes, n, z=1.96):
    if not n:
        return None
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]


def unique_estimate(n_kept, dup_share, on_topic_non_dup, interval):
    """kept * (1 - arXiv duplicate share) * on-topic rate among non-duplicates."""
    if on_topic_non_dup is None:
        return None
    not_on_arxiv = n_kept * (1 - (dup_share or 0.0))
    estimate = {"point": round(not_on_arxiv * on_topic_non_dup, 1)}
    if interval:
        estimate["range_95"] = [round(not_on_arxiv * interval[0], 1),
                                round(not_on_arxiv * interval[1], 1)]
    return estimate


# ------------------------------------------------------------------ arXiv lead time (date caveat)

def arxiv_lead_days(records, overlap_rows, arxiv_dates):
    """Days by which the matched arXiv record precedes the server's `date`."""
    leads = []
    for record in records:
        match_id = overlap_rows[record["id"]]["title_match_id"]
        if match_id and match_id in arxiv_dates:
            leads.append(days_between(arxiv_dates[match_id], record["date"]))
    if not leads:
        return None
    leads.sort()
    return {"n": len(leads), "median_days": leads[len(leads) // 2],
            "share_arxiv_first": share(sum(1 for d in leads if d > 0), len(leads)),
            "min": leads[0], "max": leads[-1]}


def days_between(earlier, later):
    import datetime
    parse = lambda s: datetime.datetime.strptime(s[:10], "%Y-%m-%d").date()
    return (parse(later) - parse(earlier)).days


# ------------------------------------------------------------------ small API checks (opt-in)

API_CHECKS_PATH = os.path.join(ANALYSIS_DIR, "q5_api_checks.json")
USER_AGENT = "qm-preprint-landscape/0.1 (non-commercial literature survey)"
WINDOW_BOUNDS = {"preceding": ("2024-09-24", "2025-09-23"),
                 "trailing": ("2025-09-24", "2026-09-23")}


def polite_get(url, params):
    import time
    import requests
    time.sleep(1.5)  # stays below 1 request per second
    response = requests.get(url, params=params, timeout=60,
                            headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    response.raise_for_status()
    return response.json()


def hal_count(query, doc_type, window, require_arxiv=False):
    start, end = WINDOW_BOUNDS[window]
    params = [("q", '"%s"' % query), ("fq", "docType_s:%s" % doc_type),
              ("fq", "submittedDate_tdate:[%sT00:00:00Z TO %sT23:59:59Z]" % (start, end)),
              ("rows", 0), ("wt", "json")]
    if require_arxiv:
        params.append(("fq", "arxivId_s:*"))
    return polite_get("https://api.archives-ouvertes.fr/search/", params)["response"]["numFound"]


def zenodo_preprint_total(window, query=None):
    start, end = WINDOW_BOUNDS[window]
    q = "publication_date:[%s TO %s]" % (start, end)
    if query:
        q = '"%s" AND %s' % (query, q)
    params = {"q": q, "type": "publication", "subtype": "preprint", "size": 1}
    return polite_get("https://zenodo.org/api/records", params)["hits"]["total"]


def crossref_posted_total(prefix, window):
    start, end = WINDOW_BOUNDS[window]
    params = {"filter": "type:posted-content,from-posted-date:%s,until-posted-date:%s" % (start, end),
              "rows": 0}
    return polite_get("https://api.crossref.org/prefixes/%s/works" % prefix, params)["message"]["total-results"]


def run_api_checks():
    """About 16 calls: HAL doc-type survivorship, Zenodo and Crossref base volumes."""
    checks = {"hal_superconductivity": {}, "zenodo_all_preprints": {},
              "crossref_all_posted_content": {}}
    for window in WINDOW_BOUNDS:
        checks["hal_superconductivity"][window] = {
            "preprint_UNDEFINED": hal_count("superconductivity", "UNDEFINED", window),
            "journal_ART": hal_count("superconductivity", "ART", window),
            "journal_ART_with_arxiv": hal_count("superconductivity", "ART", window, True),
        }
        checks["zenodo_all_preprints"][window] = zenodo_preprint_total(window)
        for server, prefix in [("researchsquare", "10.21203"), ("chemrxiv", "10.26434"),
                               ("preprints_org", "10.20944")]:
            checks["crossref_all_posted_content"].setdefault(server, {})[window] = \
                crossref_posted_total(prefix, window)
    checks["note"] = ("HAL counts use submittedDate; ART = journal article. "
                      "Zenodo/Crossref totals are all-subject base volumes for normalization.")
    with open(API_CHECKS_PATH, "w", encoding="utf-8") as fh:
        json.dump(checks, fh, indent=1)
    print(json.dumps(checks, indent=1))


def load_api_checks():
    if not os.path.exists(API_CHECKS_PATH):
        return None
    with open(API_CHECKS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ optional topic distribution

def topic_distribution(server_records):
    if not os.path.exists(CLASSIFIED_PATH):
        return {"available": False, "note": "analysis/classified.jsonl not present; skipped"}
    wanted = {r["id"]: server for server, recs in server_records.items() for r in recs}
    per_server = collections.defaultdict(collections.Counter)
    version = None
    for row in load_jsonl(CLASSIFIED_PATH):
        version = row.get("taxonomy_version", version)
        server = wanted.get(row.get("id"))
        if server is None:
            continue
        clusters = row.get("clusters") or ([row["cluster"]] if row.get("cluster") else [])
        for cluster in clusters or ["unclassified"]:
            per_server[server][cluster] += 1
    return {"available": True, "taxonomy_version": version,
            "top_clusters": {s: c.most_common(6) for s, c in per_server.items()}}


# ------------------------------------------------------------------ main

def build_report(server_records, overlap_rows, arxiv_dates, crossref_log, native_log):
    audit = load_audit()
    report = {"servers": {}, "method": method_notes(), "api_checks": load_api_checks()}
    for server in SERVERS:
        records = in_window(server_records[server])
        rows = [overlap_rows[r["id"]] for r in records]
        overlap = summarize_overlap(rows)
        expected = [r["id"] for r in audit_sample(server_records[server])]
        rates = audit_rates(server, audit.get(server, []), expected)
        yields = crossref_yield(crossref_log, server) if server in CROSSREF_SERVERS \
            else native_yield(native_log, server)
        by_window = collections.Counter(r["window"] for r in records)
        trailing = by_window["trailing"]
        report["servers"][server] = {
            "records_in_file": len(server_records[server]),
            "records_trailing": trailing,
            "records_preceding": by_window["preceding"],
            "records_outside_windows": len(server_records[server]) - len(records),
            "yield": yields,
            "arxiv_overlap": overlap,
            "publication_linkage": publication_linkage(server, records),
            "date_caveats": date_caveats(server, records),
            "monthly_counts": monthly_counts(records),
            "top_first_authors": top_first_authors(records),
            "arxiv_lead_days_for_title_matches": arxiv_lead_days(records, overlap_rows, arxiv_dates),
            "arxiv_dup_share_by_quarter": dup_share_by_quarter(records, overlap_rows),
            "arxiv_dup_share_late_dated": late_dup_share(records, overlap_rows),
            "audit": rates,
            "unique_on_topic_estimate_both_windows": unique_estimate(
                len(records), overlap["arxiv_dup_share"],
                rates["on_topic_rate_among_non_duplicates"], rates["interval_95_on_topic_non_dup"]),
            "unique_on_topic_estimate_trailing": unique_estimate(
                trailing, overlap["arxiv_dup_share"],
                rates["on_topic_rate_among_non_duplicates"], rates["interval_95_on_topic_non_dup"]),
        }
        # Sensitivity: use the dup share of late-dated records (censoring-corrected for OSTI;
        # for fast-posting servers it is instead right-censored, i.e. too low).
        late = report["servers"][server]["arxiv_dup_share_late_dated"]["dup_share"]
        report["servers"][server]["unique_on_topic_estimate_both_windows_late_dup_share"] = \
            unique_estimate(len(records), late, rates["on_topic_rate_among_non_duplicates"],
                            rates["interval_95_on_topic_non_dup"])
    report["topic_distribution"] = topic_distribution(server_records)
    return report


def method_notes():
    return {
        "windows": {"trailing": "2025-09-24..2026-09-23", "preceding": "2024-09-24..2025-09-23"},
        "title_normalization": "NFKD accent strip, drop LaTeX commands and $, lowercase, "
                               "non-alphanumerics -> space; stopwords dropped for Jaccard",
        "near_match": "token-set Jaccard >= %.2f, titles with >= 4 tokens" % JACCARD_THRESHOLD,
        "on_arxiv": "declared arXiv id OR exact/near title match to corpus/arxiv.jsonl "
                    "(arXiv corpus is a category/term-limited harvest, so this is a lower bound)",
        "audit_sample": "in-window records sorted by id; random.Random(11).sample, up to 25/server",
        "unique_estimate": "in-window records * (1 - arxiv_dup_share) * on-topic rate among "
                           "audited non-duplicates; range from the Wilson 95% interval",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--print-sample", action="store_true")
    parser.add_argument("--api-checks", action="store_true",
                        help="make ~16 small HAL/Zenodo/Crossref count queries -> q5_api_checks.json")
    args = parser.parse_args()
    if args.api_checks:
        run_api_checks()
        return

    server_records = {s: load_server(s) for s in SERVERS}
    arxiv_records = load_server("arxiv")
    arxiv_dates = {r["id"]: r["date"] for r in arxiv_records}
    index = ArxivTitleIndex(arxiv_records, JACCARD_THRESHOLD)
    all_records = [r for s in SERVERS for r in server_records[s]]
    overlap_rows = {row["id"]: row for row in arxiv_overlap(all_records, index)}

    if args.print_sample:
        print_sample(server_records, overlap_rows)
        return

    report = build_report(server_records, overlap_rows, arxiv_dates,
                          load_json("crossref_harvest_log.json"),
                          load_json("native_harvest_log.json"))
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)
    print_table(report)


def print_table(report):
    header = "%-15s %5s %5s %8s %6s %6s %6s %6s %s" % (
        "server", "T", "P", "kept/f", "arXiv", "onTop", "fringe", "data", "unique(T+P) [95%]")
    print(header)
    for server, row in report["servers"].items():
        audit = row["audit"]["rates"]
        estimate = row["unique_on_topic_estimate_both_windows"] or {}
        print("%-15s %5d %5d %8s %6s %6s %6s %6s %s %s" % (
            server, row["records_trailing"], row["records_preceding"],
            row["yield"]["kept_per_fetched"], row["arxiv_overlap"]["arxiv_dup_share"],
            audit["on_topic_research"], audit["fringe_or_pseudoscience"],
            audit["dataset_or_report"], estimate.get("point"), estimate.get("range_95")))


if __name__ == "__main__":
    main()
