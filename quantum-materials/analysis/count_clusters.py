"""
Count topic clusters, methods and material families in the harvested corpus.

Usage:  /usr/bin/python3 count_clusters.py [--live] [--top-families N] [--bigrams N]

Default input is the per-record classification cache analysis/classified.jsonl
(written by build_classified.py; trailing + preceding windows only). If that
file is missing, or --live is given, every corpus/*.jsonl record (NOT
corpus/raw/) is classified on the fly with taxonomy.classify_record, which
also reports the "outside" window.

For each server and window it reports:
  - records, in-scope N (and how many came in via arXiv category vs keyword)
  - per-cluster counts, multi-label and primary
  - unclassified-in-scope count and fraction
  - per-method counts (experimental / computational)
  - per cluster: the top material families
Also lists the most frequent title bigrams among in-scope-but-unclassified
records (trailing + preceding windows) to guide taxonomy refinement.

Writes quantum-materials/analysis/cluster_counts.json.
"""

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import taxonomy as tx  # noqa: E402

CORPUS_DIR = os.path.join(os.path.dirname(HERE), "corpus")
CLASSIFIED_PATH = os.path.join(HERE, "classified.jsonl")
OUTPUT_PATH = os.path.join(HERE, "cluster_counts.json")

WINDOWS = ["trailing", "preceding", "outside"]

STOPWORDS = set("""
a an the of in on for and or with to from by at as via into its their using under
is are be we our this that these those between toward towards based new study
""".split())


# ---------------------------------------------------------------------------
# Input: labelled records, either from the cache or classified live
# ---------------------------------------------------------------------------

def load_corpus():
    """Yield (server_file_id, record) from corpus/*.jsonl, skipping bad lines."""
    paths = sorted(glob.glob(os.path.join(CORPUS_DIR, "*.jsonl")))
    for path in paths:
        file_id = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                yield file_id, record


def load_titles():
    """(server, id) -> title for every corpus record."""
    titles = {}
    for file_id, record in load_corpus():
        server = record.get("server") or file_id
        titles[(server, record.get("id"))] = record.get("title") or ""
    return titles


def labelled_from_cache():
    """Yield (server, window, labels, title) from analysis/classified.jsonl."""
    titles = load_titles()
    with open(CLASSIFIED_PATH, encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            title = titles.get((row["server"], row["id"]), "")
            yield row["server"], row["window"], row, title


def labelled_live():
    """Yield (server, window, labels, title), classifying every corpus record now."""
    seen_ids = set()
    for file_id, record in load_corpus():
        server = record.get("server") or file_id
        key = (server, record.get("id"))
        if record.get("id") is not None:
            if key in seen_ids:
                continue
            seen_ids.add(key)
        window = record.get("window") or "outside"
        yield server, window, tx.classify_record(record), record.get("title") or ""


# ---------------------------------------------------------------------------
# Counting
# ---------------------------------------------------------------------------

def new_bucket():
    return {
        "n_records": 0,
        "n_in_scope": 0,
        "n_in_scope_by_category": 0,
        "n_in_scope_by_keyword_only": 0,
        "clusters_multi": Counter(),
        "clusters_primary": Counter(),
        "n_unclassified_in_scope": 0,
        "methods": Counter(),
        "cluster_families": defaultdict(Counter),
    }


def title_bigrams(title):
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]+", tx.normalize_text(title).lower())
    words = [w for w in words if w not in STOPWORDS and len(w) > 1]
    return [words[i] + " " + words[i + 1] for i in range(len(words) - 1)]


def add_record(bucket, labels):
    """Add one labelled record to a server/window bucket. Returns True if unclassified in scope."""
    bucket["n_records"] += 1
    if not labels["in_scope"]:
        return False
    bucket["n_in_scope"] += 1
    if labels["scope_reason"] == "category":
        bucket["n_in_scope_by_category"] += 1
    else:
        bucket["n_in_scope_by_keyword_only"] += 1
    for key in labels["clusters"]:
        bucket["clusters_multi"][key] += 1
        for family in labels["families"]:
            bucket["cluster_families"][key][family] += 1
    for method in labels["methods"]:
        bucket["methods"][method] += 1
    if labels["primary_cluster"]:
        bucket["clusters_primary"][labels["primary_cluster"]] += 1
        return False
    bucket["n_unclassified_in_scope"] += 1
    return True


def bucket_summary(b, top_families):
    n = b["n_in_scope"]
    return {
        "n_records": b["n_records"],
        "n_in_scope": n,
        "n_in_scope_by_category": b["n_in_scope_by_category"],
        "n_in_scope_by_keyword_only": b["n_in_scope_by_keyword_only"],
        "clusters_multi": dict((k, b["clusters_multi"][k]) for k in tx.CLUSTER_KEYS),
        "clusters_primary": dict((k, b["clusters_primary"][k]) for k in tx.CLUSTER_KEYS),
        "n_unclassified_in_scope": b["n_unclassified_in_scope"],
        "unclassified_fraction": round(b["n_unclassified_in_scope"] / n, 4) if n else None,
        "methods": dict((k, b["methods"][k]) for k in tx.METHODS),
        "cluster_top_families": dict(
            (k, b["cluster_families"][k].most_common(top_families))
            for k in tx.CLUSTER_KEYS if b["cluster_families"][k]
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--live", action="store_true", help="classify the corpus now instead of reading classified.jsonl")
    parser.add_argument("--top-families", type=int, default=5)
    parser.add_argument("--bigrams", type=int, default=30)
    args = parser.parse_args()

    use_cache = os.path.exists(CLASSIFIED_PATH) and not args.live
    records = labelled_from_cache() if use_cache else labelled_live()

    buckets = defaultdict(lambda: defaultdict(new_bucket))  # server -> window -> bucket
    unclassified_bigrams = defaultdict(Counter)              # server -> Counter
    taxonomy_versions = Counter()
    for server, window, labels, title in records:
        taxonomy_versions[labels.get("taxonomy_version")] += 1
        unclassified = add_record(buckets[server][window], labels)
        if unclassified and window != "outside":
            unclassified_bigrams[server].update(title_bigrams(title))

    output = {
        "taxonomy_version": tx.TAXONOMY_VERSION,
        "input": "analysis/classified.jsonl" if use_cache else "corpus/*.jsonl classified live",
        "input_taxonomy_versions": dict(taxonomy_versions),
        "windows_note": ("trailing and preceding windows only (classified.jsonl)" if use_cache
                         else "all windows incl. outside"),
        "scope_description": tx.SCOPE_DESCRIPTION,
        "corpus_dir": CORPUS_DIR,
        "cluster_order": tx.CLUSTER_KEYS,
        "residual_clusters": tx.RESIDUAL_CLUSTER_KEYS,
        "cluster_labels": tx.CLUSTER_LABELS,
        "method_kinds": tx.METHOD_KINDS,
        "servers": {},
        "unclassified_title_bigrams": {},
    }
    for server in sorted(buckets):
        output["servers"][server] = {}
        for window in WINDOWS:
            if window in buckets[server]:
                output["servers"][server][window] = bucket_summary(buckets[server][window], args.top_families)
    all_bigrams = Counter()
    for server, counter in unclassified_bigrams.items():
        output["unclassified_title_bigrams"][server] = counter.most_common(args.bigrams)
        all_bigrams.update(counter)
    output["unclassified_title_bigrams"]["ALL"] = all_bigrams.most_common(args.bigrams)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=1, ensure_ascii=False)

    print_report(output)
    print("\ninput: " + output["input"])
    print("wrote " + OUTPUT_PATH)


def print_report(output):
    if not output["servers"]:
        print("No corpus records found under " + output["corpus_dir"])
        return
    for server, windows in output["servers"].items():
        for window, s in windows.items():
            print("=" * 78)
            print("%s / %s: records=%d in_scope=%d (category=%d, keyword-only=%d) unclassified=%d (%s)"
                  % (server, window, s["n_records"], s["n_in_scope"], s["n_in_scope_by_category"],
                     s["n_in_scope_by_keyword_only"], s["n_unclassified_in_scope"],
                     "n/a" if s["unclassified_fraction"] is None else "%.1f%%" % (100 * s["unclassified_fraction"])))
            if not s["n_in_scope"]:
                continue
            print("  %-36s %8s %8s   top families" % ("cluster", "multi", "primary"))
            for key in output["cluster_order"]:
                families = s["cluster_top_families"].get(key, [])
                family_text = ", ".join("%s:%d" % (f, c) for f, c in families[:3])
                print("  %-36s %8d %8d   %s" % (key, s["clusters_multi"][key], s["clusters_primary"][key], family_text))
            print("  methods:")
            for kind in ("experimental", "computational"):
                items = [(k, v) for k, v in s["methods"].items() if output["method_kinds"][k] == kind]
                items.sort(key=lambda kv: -kv[1])
                print("    %s: %s" % (kind, ", ".join("%s=%d" % kv for kv in items)))
    bigrams = output["unclassified_title_bigrams"].get("ALL", [])
    if bigrams:
        print("=" * 78)
        print("Top title bigrams among in-scope but unclassified records (trailing+preceding):")
        for bigram, count in bigrams:
            print("  %5d  %s" % (count, bigram))


if __name__ == "__main__":
    main()
