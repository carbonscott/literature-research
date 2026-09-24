"""
Q2 Momentum: which topic clusters are gaining or losing share of arXiv
quantum-materials output, trailing window vs preceding window?

Usage:  /usr/bin/python3 analysis/momentum.py

Input:  analysis/classified.jsonl (taxonomy v2, per-record cache; not edited)
        corpus/arxiv.jsonl + corpus/arxiv_supplement.jsonl (titles for exemplars)
Output: analysis/momentum.json

Method (arXiv records with in_scope == true only):
  T, P            cluster count in trailing / preceding window
  scope_T/scope_P in-scope record count in each window
  share           T / scope_T and P / scope_P
  R               share ratio share_T / share_P
  raw growth      T / P - 1
  95% CI for R    exp(log R +- 1.96 * sqrt(1/T + 1/P + 1/scope_T + 1/scope_P))
                  (Poisson approximation; ignores that T is a subset of scope_T,
                  so it is slightly conservative)

Variants: primary vs multi-label counts, and full scope vs category-only
scope (records whose arXiv categories include cond-mat.str-el or
cond-mat.supr-con, i.e. scope_reason == "category").

Robustness: least-squares slope of the monthly primary share vs month index,
with a t-statistic; flags clusters whose slope sign contradicts the label.
"""

import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import taxonomy as tx  # noqa: E402

CLASSIFIED_PATH = os.path.join(HERE, "classified.jsonl")
ARXIV_CORPUS_PATHS = [
    os.path.join(PROJECT, "corpus", "arxiv.jsonl"),
    os.path.join(PROJECT, "corpus", "arxiv_supplement.jsonl"),
]
OUTPUT_PATH = os.path.join(HERE, "momentum.json")

UNCLASSIFIED = "unclassified"
Z_95 = 1.96
LABEL_RULE = ("rising if R >= 1.10 and CI lower bound > 1.0; "
              "declining if R <= 0.90 and CI upper bound < 1.0; otherwise flat.")
WINDOWS = {
    "trailing": ["2025-09-24", "2026-09-23"],
    "preceding": ["2024-09-24", "2025-09-23"],
}
EXEMPLARS_PER_CLUSTER = 3

TITLE_STOPWORDS = set("""
a an the of in on and or for with to from by at as via its their into under
between beyond near using is are be we our this that new study
""".split())


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_in_scope_arxiv():
    """arXiv records in scope, trailing or preceding window."""
    records = []
    with open(CLASSIFIED_PATH) as handle:
        for line in handle:
            record = json.loads(line)
            if record["server"] != "arxiv" or not record["in_scope"]:
                continue
            if record["window"] not in WINDOWS:
                continue
            records.append(record)
    return records


def load_arxiv_titles():
    """id -> raw title for every arXiv corpus record."""
    titles = {}
    for path in ARXIV_CORPUS_PATHS:
        if not os.path.exists(path):
            continue
        with open(path) as handle:
            for line in handle:
                record = json.loads(line)
                titles[record["id"]] = record.get("title") or ""
    return titles


def is_category_scope(record):
    return record["scope_reason"] == "category"


def primary_labels(record):
    return [record["primary_cluster"] or UNCLASSIFIED]


def multi_labels(record):
    return record["clusters"] or [UNCLASSIFIED]


# ---------------------------------------------------------------------------
# Share ratio statistics
# ---------------------------------------------------------------------------

def share_ratio_stats(trailing, preceding, scope_trailing, scope_preceding):
    """Shares, share ratio R, raw growth and a 95% Poisson CI for R."""
    stats = {
        "T": trailing,
        "P": preceding,
        "scope_T": scope_trailing,
        "scope_P": scope_preceding,
        "share_T": trailing / float(scope_trailing),
        "share_P": preceding / float(scope_preceding),
        "raw_growth": None,
        "R": None,
        "ci_low": None,
        "ci_high": None,
    }
    if preceding > 0:
        stats["raw_growth"] = trailing / float(preceding) - 1.0
    if trailing == 0 or preceding == 0:
        return stats
    ratio = stats["share_T"] / stats["share_P"]
    variance = 1.0 / trailing + 1.0 / preceding + 1.0 / scope_trailing + 1.0 / scope_preceding
    half_width = Z_95 * math.sqrt(variance)
    stats["R"] = ratio
    stats["ci_low"] = math.exp(math.log(ratio) - half_width)
    stats["ci_high"] = math.exp(math.log(ratio) + half_width)
    return stats


def momentum_label(stats):
    """Apply LABEL_RULE."""
    if stats["R"] is None:
        return "flat"
    if stats["R"] >= 1.10 and stats["ci_low"] > 1.0:
        return "rising"
    if stats["R"] <= 0.90 and stats["ci_high"] < 1.0:
        return "declining"
    return "flat"


def window_table(records, labels_of):
    """Per-cluster share-ratio stats and labels for one variant."""
    scope = Counter(record["window"] for record in records)
    counts = {"trailing": Counter(), "preceding": Counter()}
    for record in records:
        for key in labels_of(record):
            counts[record["window"]][key] += 1
    table = {}
    for key in tx.CLUSTER_KEYS + [UNCLASSIFIED]:
        stats = share_ratio_stats(counts["trailing"][key], counts["preceding"][key],
                                  scope["trailing"], scope["preceding"])
        stats["label"] = momentum_label(stats)
        table[key] = stats
    return {"scope_T": scope["trailing"], "scope_P": scope["preceding"], "clusters": table}


# ---------------------------------------------------------------------------
# Monthly share series and least-squares slope
# ---------------------------------------------------------------------------

def monthly_shares(records, labels_of):
    """Sorted month list, in-scope totals per month, and cluster -> share list."""
    totals = Counter(record["month"] for record in records)
    counts = defaultdict(Counter)
    for record in records:
        for key in labels_of(record):
            counts[key][record["month"]] += 1
    months = sorted(totals)
    series = {}
    for key in tx.CLUSTER_KEYS + [UNCLASSIFIED]:
        series[key] = [counts[key][month] / float(totals[month]) for month in months]
    return months, totals, series


def least_squares_slope(values):
    """Slope of values vs index 0..n-1, its standard error and t-statistic."""
    n = len(values)
    xs = list(range(n))
    mean_x = sum(xs) / float(n)
    mean_y = sum(values) / float(n)
    sxx = sum((x - mean_x) ** 2 for x in xs)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    residual_ss = sum((y - intercept - slope * x) ** 2 for x, y in zip(xs, values))
    standard_error = math.sqrt(residual_ss / (n - 2) / sxx)
    t_stat = slope / standard_error if standard_error > 0 else 0.0
    return {"slope_per_month": slope, "se": standard_error, "t": t_stat, "n_months": n}


def slope_sign(slope):
    if slope > 0:
        return "+"
    if slope < 0:
        return "-"
    return "0"


def contradicts(label, slope):
    return (label == "rising" and slope < 0) or (label == "declining" and slope > 0)


# ---------------------------------------------------------------------------
# Exemplars
# ---------------------------------------------------------------------------

def title_bigrams(title):
    words = [w for w in re.findall(r"[a-z0-9][a-z0-9\-]*", title.lower())
             if w not in TITLE_STOPWORDS]
    return set(zip(words, words[1:]))


def characteristic_bigrams(cluster_records, titles, direction, limit=15):
    """Title bigrams most over-represented in the trailing (rising) or
    preceding (declining) window within one cluster (smoothed ratio)."""
    by_window = {"trailing": Counter(), "preceding": Counter()}
    size = Counter()
    for record in cluster_records:
        size[record["window"]] += 1
        for bigram in title_bigrams(titles.get(record["id"], "")):
            by_window[record["window"]][bigram] += 1
    if direction == "rising":
        numerator, denominator = "trailing", "preceding"
    else:
        numerator, denominator = "preceding", "trailing"
    scored = []
    for bigram, count in by_window[numerator].items():
        if count < 4 or by_window["trailing"][bigram] < 2:
            continue
        rate_num = (count + 1.0) / (size[numerator] + 1.0)
        rate_den = (by_window[denominator][bigram] + 1.0) / (size[denominator] + 1.0)
        scored.append((rate_num / rate_den, count, bigram))
    scored.sort(reverse=True)
    return [bigram for _, _, bigram in scored[:limit]]


def pick_exemplars(cluster_key, records, titles, direction):
    """Trailing-window, primary-cluster records whose TITLE matches the
    cluster's core pattern, preferring titles that contain the bigrams most
    characteristic of the change; one exemplar per distinct bigram."""
    pattern = None
    for compiled in tx._CLUSTERS_COMPILED:
        if compiled["key"] == cluster_key:
            pattern = compiled["pattern"]
    cluster_records = [r for r in records if r["primary_cluster"] == cluster_key]
    bigrams = characteristic_bigrams(cluster_records, titles, direction)
    candidates = []
    for record in cluster_records:
        if record["window"] != "trailing" or record["id"] not in titles:
            continue
        title = tx.normalize_text(titles[record["id"]])
        if pattern is not None and not pattern.search(title):
            continue
        candidates.append((record["id"], title))
    candidates.sort()

    chosen = []
    used_ids = set()
    for bigram in bigrams:
        for record_id, title in candidates:
            if record_id in used_ids or bigram not in title_bigrams(title):
                continue
            chosen.append({"id": record_id, "title": title, "matched_bigram": " ".join(bigram)})
            used_ids.add(record_id)
            break
        if len(chosen) == EXEMPLARS_PER_CLUSTER:
            return chosen
    for record_id, title in candidates:  # fallback: any core-pattern title
        if len(chosen) == EXEMPLARS_PER_CLUSTER:
            break
        if record_id not in used_ids:
            chosen.append({"id": record_id, "title": title, "matched_bigram": None})
            used_ids.add(record_id)
    return chosen


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_variants(records):
    category_records = [r for r in records if is_category_scope(r)]
    return {
        "primary_full_scope": window_table(records, primary_labels),
        "multilabel_full_scope": window_table(records, multi_labels),
        "primary_category_scope": window_table(category_records, primary_labels),
        "multilabel_category_scope": window_table(category_records, multi_labels),
    }


def label_flips(variants):
    flips = {}
    for key in tx.CLUSTER_KEYS + [UNCLASSIFIED]:
        labels = dict((name, table["clusters"][key]["label"]) for name, table in variants.items())
        if len(set(labels.values())) > 1:
            flips[key] = labels
    return flips


def monthly_robustness(records, base_table):
    months, totals, series = monthly_shares(records, primary_labels)
    full_months = months[1:-1]  # drop partial first (from 24th) and last (to 22nd) months
    result = {}
    for key, shares in series.items():
        label = base_table[key]["label"]
        all_fit = least_squares_slope(shares)
        full_fit = least_squares_slope(shares[1:-1])
        result[key] = {
            "monthly_share": [round(s, 5) for s in shares],
            "all_months": all_fit,
            "full_months_only": full_fit,
            "slope_sign": slope_sign(all_fit["slope_per_month"]),
            "contradicts_label": contradicts(label, all_fit["slope_per_month"]),
            "contradicts_label_full_months": contradicts(label, full_fit["slope_per_month"]),
        }
    return {
        "months": months,
        "in_scope_per_month": [totals[m] for m in months],
        "full_months": full_months,
        "clusters": result,
    }


def partial_month_note(records):
    trailing_dates = sorted(r["date"] for r in records if r["window"] == "trailing")
    preceding_dates = sorted(r["date"] for r in records if r["window"] == "preceding")
    return {
        "first_date_preceding": preceding_dates[0],
        "last_date_trailing": trailing_dates[-1],
        "note": ("Month buckets are calendar months, so there are 25 of them: 2024-09 holds only "
                 "2024-09-24..30 and 2026-09 holds only 2026-09-01..%s (the data ends on %s, one day "
                 "before the window end 2026-09-23). The trailing window therefore has 364 covered "
                 "days vs 365 in the preceding window; raw growth T/P-1 is biased low by ~0.3%%, "
                 "shares and R are unaffected to first order. Slopes are reported on all 25 buckets "
                 "and on the 23 full months only." % (trailing_dates[-1][-2:], trailing_dates[-1])),
    }


def round_floats(value, digits=4):
    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, dict):
        return dict((k, round_floats(v, digits)) for k, v in value.items())
    if isinstance(value, list):
        return [round_floats(v, digits) for v in value]
    return value


def main():
    records = load_in_scope_arxiv()
    titles = load_arxiv_titles()
    variants = build_variants(records)
    base_table = variants["primary_full_scope"]["clusters"]
    monthly = monthly_robustness(records, base_table)

    exemplars = {}
    for key in tx.CLUSTER_KEYS:
        label = base_table[key]["label"]
        if label in ("rising", "declining"):
            exemplars[key] = pick_exemplars(key, records, titles, label)

    output = {
        "description": "Q2 momentum: share of arXiv in-scope records per cluster, trailing vs preceding.",
        "taxonomy_version": tx.TAXONOMY_VERSION,
        "windows": WINDOWS,
        "label_rule": LABEL_RULE,
        "ci_method": "95% CI: exp(log R +- 1.96*sqrt(1/T + 1/P + 1/scope_T + 1/scope_P)) (Poisson approximation)",
        "base_variant": "primary_full_scope",
        "variants": variants,
        "label_flips": label_flips(variants),
        "monthly": monthly,
        "partial_months": partial_month_note(records),
        "exemplars": exemplars,
    }
    with open(OUTPUT_PATH, "w") as handle:
        json.dump(round_floats(output, 5), handle, indent=1, ensure_ascii=False)
    print_summary(output)


def fmt(value, pattern="%.2f"):
    return "-" if value is None else pattern % value


def print_summary(output):
    base = output["variants"]["primary_full_scope"]
    multi = output["variants"]["multilabel_full_scope"]["clusters"]
    monthly = output["monthly"]["clusters"]
    flips = output["label_flips"]
    print("scope_T=%d scope_P=%d" % (base["scope_T"], base["scope_P"]))
    print("%-34s %5s %5s %6s %13s %9s | %5s %6s %9s | %2s %6s %6s %s" % (
        "cluster", "T", "P", "R", "95% CI", "label", "Tm", "Rm", "label_m", "sg", "t", "t_full", "flip"))
    rows = sorted(base["clusters"].items(), key=lambda kv: -(kv[1]["R"] or 0))
    for key, s in rows:
        m = multi[key]
        mo = monthly[key]
        print("%-34s %5d %5d %6s %13s %9s | %5d %6s %9s | %2s %6.2f %6.2f %s%s" % (
            key, s["T"], s["P"], fmt(s["R"]), "[%s,%s]" % (fmt(s["ci_low"]), fmt(s["ci_high"])),
            s["label"], m["T"], fmt(m["R"]), m["label"], mo["slope_sign"], mo["all_months"]["t"],
            mo["full_months_only"]["t"], "FLIP" if key in flips else "",
            " CONTRADICT" if mo["contradicts_label"] else ""))
    for key, labels in flips.items():
        print("flip", key, labels)
    for key, items in output["exemplars"].items():
        for item in items:
            print("ex", key, item["id"], item["matched_bigram"], "|", item["title"][:110])


if __name__ == "__main__":
    main()
