"""
Q4 Methods: which experimental and computational techniques do quantum-materials
preprints use, and how did that change between the two windows?

Usage (from anywhere; Python 3.6, stdlib only):

    /usr/bin/python3 analysis/methods.py                   # recount, write analysis/methods.json
    /usr/bin/python3 analysis/methods.py --audit-sample    # print the v2 precision-audit sample
    /usr/bin/python3 analysis/methods.py --audit-sample --refined
                                                            # print the re-audit sample (refined tags)
    /usr/bin/python3 analysis/methods.py --audit-sample --dropped
                                                            # print records the refinement dropped

Inputs
  analysis/classified.jsonl   ids, windows, in-scope flag, clusters and v2 method tags (taxonomy v2)
  corpus/arxiv.jsonl (+ corpus/arxiv_supplement.jsonl)    title + abstract text

Population: in-scope arXiv records in the trailing / preceding windows (from classified.jsonl).
Non-arXiv servers are left out: they are few, keyword-selected, and their abstracts are uneven.

Method lexicon
  The 25 METHODS regexes of taxonomy.py (v2) were precision spot-checked (10 trailing in-scope
  arXiv records per method, random.Random(7); verdicts in analysis/methods_precision_audit.json).
  The question was "does the paper USE the technique", not "does it mention it". For experimental
  methods that means the authors measured with it; a theory paper that computes a Hall
  conductivity or proposes an STM signature does not count.

  Seven methods scored below 70% and are refined here (REFINED_METHODS). Each refined method
  has two parts:
    * strong:  phrases that almost always mean the technique was used; one match is enough.
    * weak:    broader phrases that are often passing mentions. A weak match counts only if
               (1) the text has a context cue:
                   - experimental methods: EXPERIMENT_CUE ("measured", "samples", "we grew" ...),
                     or a reliable experimental probe (RELIABLE_EXPERIMENTAL_PROBES), or at
                     least no THEORY_CUE ("theory", "model", "calculations", "DFT" ...);
                   - computational methods: COMPUTATION_CUE ("calculated", "simulations" ...);
               (2) at least one weak match is not hedged, i.e. the 80 characters before it
                   contain none of the HEDGE words ("propose", "predict", "could", "reported",
                   "accessible", ...).
    High pressure additionally needs two unhedged weak matches (weak_min_hits = 2).
    Strong matches must also be unhedged (so "can be implemented with spin-resolved scanning
    tunneling microscopy" does not count).
  The other 18 methods keep their v2 taxonomy.py pattern unchanged (plain "any match").

Statistics (see compute_* functions)
  share      = papers tagged with the method / in-scope papers, per window
  R          = share_trailing / share_preceding
  95% CI     = exp(log R +- 1.96 * sqrt(1/T + 1/P + 1/scope_T + 1/scope_P))  (Poisson approx.)
"""

import argparse
import json
import math
import os
import random
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import taxonomy as tx  # noqa: E402

CLASSIFIED_PATH = os.path.join(HERE, "classified.jsonl")
ARXIV_PATHS = [os.path.join(PROJECT, "corpus", "arxiv.jsonl"),
               os.path.join(PROJECT, "corpus", "arxiv_supplement.jsonl")]
OUTPUT_PATH = os.path.join(HERE, "methods.json")

WINDOWS = ["trailing", "preceding"]
AUDIT_SEED = 7
AUDIT_SAMPLE_SIZE = 10
Z95 = 1.96
cs = tx.cs


# ---------------------------------------------------------------------------
# Context cues used by the refined (weak) patterns
# ---------------------------------------------------------------------------

# Words showing the authors did an experiment (measured, grew, fabricated samples ...).
EXPERIMENT_CUE = re.compile(
    r"\bmeasur(?:e|ed|es|ing|ements?)\b|\bwe (?:observe|observed|detect|fabricat\w*|grow|grew|"
    r"synthesi[sz]\w*|prepared?)\b|\bexperimentally (?:observ|demonstrat|realiz|reveal|show|"
    r"find|found|establish|determin)\w*|\bour (?:experiments?|measurements?|data|observations?)\b|"
    r"\bsamples?\b|\bsingle[- ]crystals?\b|\bcrystals? (?:were|was) grown|\bthin[- ]film samples?|"
    r"\bobservations?\b|\bmicroscop(?:y|ies|es?)\b",  # not "microscopic"
    re.IGNORECASE)

# Words showing the authors did a calculation.
COMPUTATION_CUE = re.compile(
    r"\bcalculat\w*|\bcomput\w*|\bfirst[- ]principles?|\bab[- ]initio|\bdensity[- ]functional|"
    r"\bsimulat\w*|\bmolecular dynamics|" + cs(r"\bDFT\b"),
    re.IGNORECASE)

# Words showing a theory / computation paper. For experimental methods a weak match is
# rejected when the text has THEORY_CUE but no EXPERIMENT_CUE.
THEORY_CUE = re.compile(
    r"\bwe (?:propose|predict|theoretically|develop|derive|construct|introduce)\b|\btheor(?:y|ies|etical|etically)\b|"
    r"\bfirst[- ]principles?|\bab[- ]initio|\bdensity[- ]functional|\bcalculat\w*|\bhamiltonians?\b|"
    r"\bmodels?\b|\bsimulat\w*|\bformula\b|\bformalism\b|" + cs(r"\bDFT\b"),
    re.IGNORECASE)

# Words right before a match that turn it into a proposal, prediction or citation.
HEDGE = re.compile(
    r"\b(?:propos\w*|predict\w*|could|would|might|may|can be|accessible|detectable|future|"
    r"motivat\w*|previous\w*|reported|suggested|expected|proposal|promising|envision\w*|"
    r"recent\w*|earlier|prior|absence)\b",
    re.IGNORECASE)
HEDGE_WINDOW = 80

# Experimental v2 methods whose audited precision was >= 80% (methods_precision_audit.json),
# except thin-film growth, which also fires on theory papers about films.
# If one of them matches, the paper is experimental enough to trust a weak match of another probe.
RELIABLE_EXPERIMENTAL_PROBES = ["arpes", "neutron_scattering", "rixs_resonant_xray", "musr",
                                "nmr_nqr", "diffraction_structure"]


# ---------------------------------------------------------------------------
# Refined patterns for the seven methods with v2 precision < 70%
# (kind and label stay as in taxonomy.py; only the matching rule changes)
# ---------------------------------------------------------------------------

REFINED_METHODS = {
    "stm_sts": {
        # v2 problems: proposals ("detectable via quasiparticle interference imaging"),
        # comparisons ("reproducing ... scanning tunneling spectra"), generic "scanning probes".
        "strong": cs(r"\b(?:SI-|SP-)STM\b|\bSTM (?:measurements?|images?|topograph\w*|stud(?:y|ies)|"
                     r"experiments?|spectra|spectroscopy)\b|\bSTS (?:measurements?|spectra|maps?)\b")
                  + r"|\bspectroscopic[- ]imaging scanning tunnel+ing|\bspin[- ]polari[sz]ed (?:STM|scanning tunnel+ing)"
                  r"|\bscanning tunnel+ing (?:microscopy|spectroscopy) (?:measurements?|stud(?:y|ies)|experiments?|"
                  r"images?|reveals?|shows?|observations?)\b|\b(?:using|by|with|via|through|employ\w*|perform\w*|combin\w*|describe) "
                  r"(?:[\w/-]+ ){0,3}scanning tunnel+ing",
        "weak": cs(r"\bSTM\b|\bSTS\b|\bQPI\b") + r"|\bscanning tunnel+ing|\bquasiparticle interference",
    },
    "magnetotransport_hall": {
        # v2 problems: theory of anomalous Hall / tunnelling magnetoresistance (DFT, models),
        # "skyrmion Hall angle", fractional quantum Hall "effect" theory, cited earlier reports.
        "strong": r"\b(?:magneto-?transport|electrical transport|transport|resistivity|resistance|"
                  r"magneto-?resistance|hall|nernst) (?:measurements?|data|experiments?)\b"
                  r"|\bmeasured (?:resistivity|resistance|hall|magnetoresistance|longitudinal|transverse)"
                  r"|\bwe (?:measure|observe|observed|report) (?:a |an |the )?(?:[\w-]+ ){0,3}"
                  r"(?:magnetoresistance|hall (?:effect|resistance|signal|response|conductivity)|resistivity)",
        "weak": r"\bmagneto-?transport|\bmagneto-?resistance|\bhall (?:effect|resistance|resistivity|"
                r"conductivity|coefficient|response|signal|bar|plateau)|\banomalous hall|\bplanar hall|"
                r"\bnernst|\bthermal hall|\bresistivity|\bcritical current|\bsupercurrent|\bnonreciprocal transport",
    },
    "quantum_oscillations": {
        # v2 problems: theory papers on oscillations, "Einstein-de Haas" effect,
        # "quantum oscillations" of spin correlations, passing citations.
        "strong": r"\b(?:shubnikov[- ]de[- ]haas|de[- ]haas[- ]van[- ]alphen|quantum) oscillations? "
                  r"(?:measurements?|experiments?|data|were|are observed|observed)\b"
                  r"|\bobserv\w* (?:[\w-]+ ){0,3}(?:shubnikov|de[- ]haas[- ]van|quantum oscillation)"
                  + r"|" + cs(r"\b(?:SdH|dHvA) (?:oscillations?|measurements?|frequenc\w*)"),
        "weak": r"\bquantum oscillation|\bshubnikov|(?<!einstein-)(?<!einstein )\bde[- ]haas[- ]van|"
                + cs(r"\bSdH\b|\bdHvA\b") + r"|\blandau fan",
    },
    "optical_raman_ir": {
        # v2 problems: DFT "optical response/absorption" calculations, "infrared" in the
        # field-theory sense, THz as a frequency unit in theory, second-harmonic in theory.
        "strong": r"\braman (?:spectroscop\w*|scattering|spectra|measurements?)|\b(?:time-domain |"
                  r"two-dimensional )?(?:terahertz|THz) (?:spectroscop\w*|emission|measurements?|"
                  r"time-domain)|\binfrared (?:spectroscop\w*|reflectivity|transmission|measurements?)|"
                  r"\bphotoluminescence (?:spectroscop\w*|measurements?|spectra)|\bellipsometr\w*|"
                  r"\bkerr (?:rotation|microscop\w*) (?:measurements?|imaging)|\bmagneto-?optical "
                  r"(?:kerr|measurements?|spectroscop\w*|imaging)|\boptical (?:reflectivity|transmission) "
                  r"(?:measurements?|spectra)|\bnano-?(?:imaging|infrared)|"
                  + cs(r"\bs-SNOM\b|\bFTIR\b|\bMOKE (?:measurements?|microscop\w*|imaging)"),
        "weak": r"\braman|\bterahertz|\bphotoluminescence|\boptical (?:conductivity|spectroscop|"
                r"reflectivity|absorption|response|transmission|measurement)|\bmagneto-?optic|"
                r"\bkerr (?:rotation|effect|microscop)|\bsecond[- ]harmonic generation|"
                r"\breflectance (?:spectroscop|contrast)|" + cs(r"\bTHz\b|\bMOKE\b|\bSHG\b|\bPL\b"),
    },
    "high_pressure_dac": {
        # v2 problems: first-principles studies "under pressure", hydride predictions,
        # "high-pressure" hydrogen in QMC, citations of pressurized nickelates.
        "strong": r"\bdiamond[- ]anvil|\bpiston[- ]cylinder|\bpressure[- ]transmitting|\bpressure cells?\b|"
                  r"\buniaxial (?:stress|strain|pressure) (?:cell|device|apparatus)|\bhigh[- ]pressure "
                  r"(?:measurements?|experiments?|transport|synthesis|diffraction|raman|resistance)|"
                  r"\bmeasur\w* (?:[\w-]+ ){0,3}under (?:hydrostatic |uniaxial )?pressure|"
                  r"\bsynthesi[sz]\w* (?:at|under) (?:high|elevated) pressure|\bappl\w* uniaxial (?:pressure|stress|strain)|"
                  r"\buniaxial (?:strain|stress|pressure) (?:is|was) (?:employed|applied|used)|" + cs(r"\bDACs?\b"),
        "weak": r"\bhigh[- ]pressure|" + cs(r"\bGPa\b") + r"|\bunder (?:hydrostatic |uniaxial )?pressure|"
                r"\bhydrostatic pressure|\bpressure[- ](?:induced|tuned|dependent|driven)|"
                r"\buniaxial (?:pressure|stress|strain)|\bmegabar",
        # A single weak mention ("superconductivity under high pressure in La3Ni2O7") is usually
        # context, so high-pressure work needs two unhedged weak matches (e.g. "under pressure" + "GPa").
        "weak_min_hits": 2,
    },
    "nv_quantum_sensing": {
        # v2 problems: generic "quantum sensing" (qubit thermometry, magnonic GKP states, reviews).
        # Refined: only NV / diamond / SQUID-based magnetometry and magnetic imaging, no weak part.
        # "nitrogen vacancies" (a defect in nitrides) is not the NV sensor, hence singular "vacancy".
        "strong": r"\bnitrogen[- ]vacancy\b|" + cs(r"\bNV\b(?:[- ]center|[- ]centre| magnetometr| sensor| spin)|"
                  r"\bNV[- ]?centers?\b|\bNV magnetometr|\bSQUID[- ]on[- ]tip|\bscanning SQUID")
                  + r"|\bdiamond (?:magnetometr|quantum sens)|\bscanning magnetometr|\bwide-field magnetic imaging",
        "weak": None,
    },
    "phonon_electron_phonon": {
        # v2 problems: "anharmonic" transmon levels, passing "electron-phonon interactions"
        # in experimental or proposal papers.
        "strong": r"\beliashberg|\bphonon (?:dispersion|calculation|band structure|softening|instabilit)\w*|"
                  r"\bdensity[- ]functional perturbation|\bmcmillan|\ballen[- ]dynes|\bself-consistent harmonic|"
                  r"\bstochastic self-consistent|\banharmonicity|\bquantum anharmonic|\banharmonic (?:phonon|lattice|effect|free energ|correction|"
                  r"renormali[sz])\w*|\belectron[- ]phonon (?:coupling (?:constant|strength|matrix)|"
                  r"matrix element|self-energ|calculation|spectral function)\w*|" + cs(r"\bDFPT\b|\bEPW\b|\bSSCHA\b"),
        "weak": r"\belectron[- ]phonon|\bphonon (?:spectr|mode|mediated)",
    },
}


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def _compile(pattern):
    if pattern is None:
        return None
    return re.compile(pattern, re.IGNORECASE)


V2_REGEX = dict((key, re.compile(spec["pattern"], re.IGNORECASE)) for key, spec in tx.METHODS.items())
REFINED_REGEX = dict((key, {"strong": _compile(spec["strong"]),
                            "weak": _compile(spec["weak"]),
                            "weak_min_hits": spec.get("weak_min_hits", 1)})
                     for key, spec in REFINED_METHODS.items())
METHOD_KEYS = list(tx.METHODS)
METHOD_KINDS = dict((key, spec["kind"]) for key, spec in tx.METHODS.items())
METHOD_LABELS = dict((key, spec["label"]) for key, spec in tx.METHODS.items())


def count_unhedged_matches(regex, text):
    """Number of matches of regex with no HEDGE word in the preceding HEDGE_WINDOW characters."""
    count = 0
    for match in regex.finditer(text):
        before = text[max(0, match.start() - HEDGE_WINDOW):match.start()]
        if not HEDGE.search(before):
            count += 1
    return count


def uses_reliable_probe(text):
    """True if an experimental v2 method with audited precision >= 80% also matches."""
    return any(V2_REGEX[key].search(text) for key in RELIABLE_EXPERIMENTAL_PROBES)


def has_context_cue(key, text):
    """Experimental methods: EXPERIMENT_CUE or a reliable experimental probe, or at least no
    THEORY_CUE. Computational methods: COMPUTATION_CUE."""
    if METHOD_KINDS[key] == "experimental":
        return (bool(EXPERIMENT_CUE.search(text)) or uses_reliable_probe(text)
                or not THEORY_CUE.search(text))
    return bool(COMPUTATION_CUE.search(text))


def refined_match(key, text):
    """Refined use-evidence rule for one method (see module docstring)."""
    rule = REFINED_REGEX[key]
    if count_unhedged_matches(rule["strong"], text) > 0:
        return True
    if rule["weak"] is None or not rule["weak"].search(text):
        return False
    if not has_context_cue(key, text):
        return False
    return count_unhedged_matches(rule["weak"], text) >= rule["weak_min_hits"]


def find_methods_refined(text):
    """Method keys for normalized text using the refined lexicon."""
    keys = []
    for key in METHOD_KEYS:
        if key in REFINED_REGEX:
            matched = refined_match(key, text)
        else:
            matched = bool(V2_REGEX[key].search(text))
        if matched:
            keys.append(key)
    return keys


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_population():
    """In-scope arXiv rows in either window, from classified.jsonl."""
    rows = []
    with open(CLASSIFIED_PATH, encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["server"] == "arxiv" and row["in_scope"] and row["window"] in WINDOWS:
                rows.append(row)
    return rows


def load_texts(wanted_ids):
    """id -> (normalized title, normalized 'title. abstract') for the wanted arXiv ids."""
    texts = {}
    for path in ARXIV_PATHS:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                record = json.loads(line)
                if record["id"] in wanted_ids and record["id"] not in texts:
                    texts[record["id"]] = (tx.record_title(record), tx.record_text(record))
    return texts


def attach_refined_methods(rows, texts):
    """Add row['methods_refined'] (list of keys) to every row."""
    for row in rows:
        row["methods_refined"] = find_methods_refined(texts[row["id"]][1])


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def ratio_with_ci(count_t, count_p, scope_t, scope_p):
    """Share ratio R = (T/scope_T)/(P/scope_P) with a Poisson 95% CI on log R."""
    if count_t == 0 or count_p == 0:
        return None, None, None
    ratio = (count_t / scope_t) / (count_p / scope_p)
    se_log = math.sqrt(1.0 / count_t + 1.0 / count_p + 1.0 / scope_t + 1.0 / scope_p)
    low = ratio * math.exp(-Z95 * se_log)
    high = ratio * math.exp(Z95 * se_log)
    return round(ratio, 3), round(low, 3), round(high, 3)


def rows_in(rows, window):
    return [row for row in rows if row["window"] == window]


def count_methods(rows, field):
    counts = Counter()
    for row in rows:
        counts.update(row[field])
    return counts


def compute_method_table(rows, field):
    """One entry per method: counts, shares, share ratio and CI."""
    scope = dict((w, len(rows_in(rows, w))) for w in WINDOWS)
    counts = dict((w, count_methods(rows_in(rows, w), field)) for w in WINDOWS)
    table = []
    for key in METHOD_KEYS:
        count_t, count_p = counts["trailing"][key], counts["preceding"][key]
        ratio, low, high = ratio_with_ci(count_t, count_p, scope["trailing"], scope["preceding"])
        table.append({
            "method": key, "label": METHOD_LABELS[key], "kind": METHOD_KINDS[key],
            "trailing": count_t, "preceding": count_p,
            "share_trailing": round(count_t / scope["trailing"], 4),
            "share_preceding": round(count_p / scope["preceding"], 4),
            "share_ratio": ratio, "ci95_low": low, "ci95_high": high,
            "ci_excludes_1": (low is not None and (low > 1 or high < 1)),
        })
    table.sort(key=lambda entry: -entry["trailing"])
    return table


def has_kind(methods, kind):
    return any(METHOD_KINDS[key] == kind for key in methods)


def compute_kind_totals(rows, field):
    """Per window: papers with any experimental / computational tag, both, neither."""
    result = {}
    for window in WINDOWS:
        subset = rows_in(rows, window)
        scope = len(subset)
        exp = sum(1 for row in subset if has_kind(row[field], "experimental"))
        comp = sum(1 for row in subset if has_kind(row[field], "computational"))
        both = sum(1 for row in subset if has_kind(row[field], "experimental") and has_kind(row[field], "computational"))
        no_tag = sum(1 for row in subset if not row[field])
        no_exp = scope - exp
        comp_only = sum(1 for row in subset if has_kind(row[field], "computational") and not has_kind(row[field], "experimental"))
        tag_totals = Counter(METHOD_KINDS[key] for row in subset for key in row[field])
        result[window] = {
            "in_scope": scope,
            "papers_with_experimental_tag": exp, "share_experimental": round(exp / scope, 4),
            "papers_with_computational_tag": comp, "share_computational": round(comp / scope, 4),
            "papers_with_both": both, "share_both": round(both / scope, 4),
            "papers_computational_only": comp_only, "share_computational_only": round(comp_only / scope, 4),
            "papers_no_experimental_tag": no_exp, "share_no_experimental_tag": round(no_exp / scope, 4),
            "papers_no_method_tag": no_tag, "share_no_method_tag": round(no_tag / scope, 4),
            "experimental_tag_mentions": tag_totals["experimental"],
            "computational_tag_mentions": tag_totals["computational"],
        }
    ratios = {}
    for name in ["papers_with_experimental_tag", "papers_with_computational_tag",
                 "papers_no_experimental_tag", "papers_no_method_tag", "papers_computational_only"]:
        ratio, low, high = ratio_with_ci(result["trailing"][name], result["preceding"][name],
                                         result["trailing"]["in_scope"], result["preceding"]["in_scope"])
        ratios[name] = {"share_ratio": ratio, "ci95_low": low, "ci95_high": high}
    result["share_ratios"] = ratios
    return result


def compute_top_methods_per_cluster(rows, field, top_n=3):
    """Trailing window, multi-label clusters: top methods by share of the cluster's papers."""
    result = {}
    subset = rows_in(rows, "trailing")
    for cluster in tx.CLUSTER_KEYS:
        members = [row for row in subset if cluster in row["clusters"]]
        if not members:
            continue
        counts = count_methods(members, field)
        top = [{"method": key, "count": n, "share_of_cluster": round(n / len(members), 3)}
               for key, n in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:top_n]]
        no_exp = sum(1 for row in members if not has_kind(row[field], "experimental"))
        result[cluster] = {"label": tx.CLUSTER_LABELS[cluster], "papers": len(members),
                           "share_no_experimental_tag": round(no_exp / len(members), 3), "top": top}
    return result


CO_OCCURRENCE_PAIRS = [
    ("arpes", "dft_first_principles"),
    ("stm_sts", "dft_first_principles"),
    ("dft_first_principles", "dmft"),
    ("machine_learning", "dft_first_principles"),
    ("magnetotransport_hall", "ANY_COMPUTATIONAL"),
]


def tagged(row, field, key):
    if key == "ANY_COMPUTATIONAL":
        return has_kind(row[field], "computational")
    return key in row[field]


def compute_co_occurrences(rows, field):
    """For each pair (A, B): papers with both, share of A papers that also have B, and lift."""
    result = []
    for key_a, key_b in CO_OCCURRENCE_PAIRS:
        entry = {"a": key_a, "b": key_b}
        for window in WINDOWS:
            subset = rows_in(rows, window)
            scope = len(subset)
            n_a = sum(1 for row in subset if tagged(row, field, key_a))
            n_b = sum(1 for row in subset if tagged(row, field, key_b))
            n_ab = sum(1 for row in subset if tagged(row, field, key_a) and tagged(row, field, key_b))
            lift = (n_ab * scope / (n_a * n_b)) if n_a and n_b else None
            entry[window] = {"n_a": n_a, "n_b": n_b, "n_both": n_ab,
                             "share_of_a_with_b": round(n_ab / n_a, 3) if n_a else None,
                             "lift": round(lift, 2) if lift else None}
        result.append(entry)
    return result


# ---------------------------------------------------------------------------
# Exemplars
# ---------------------------------------------------------------------------

def title_matches(key, title):
    """Does the method's (refined or v2) pattern match the title alone?"""
    if key in REFINED_REGEX:
        rule = REFINED_REGEX[key]
        return bool(rule["strong"].search(title) or (rule["weak"] is not None and rule["weak"].search(title)))
    return bool(V2_REGEX[key].search(title))


def exemplar_candidates(rows, texts, key, limit=5):
    """Trailing ids tagged with key whose TITLE matches the method; deterministic shuffle."""
    ids = sorted(row["id"] for row in rows_in(rows, "trailing")
                 if key in row["methods_refined"] and title_matches(key, texts[row["id"]][0]))
    random.Random(AUDIT_SEED).shuffle(ids)
    return [{"id": record_id, "title": texts[record_id][0]} for record_id in ids[:limit]]


def pick_methods_for_exemplars(table):
    top_exp = [e["method"] for e in table if e["kind"] == "experimental"][:4]
    top_comp = [e["method"] for e in table if e["kind"] == "computational"][:4]
    # Fastest growing: highest share ratio among methods with >= 30 trailing papers.
    growing = [e for e in table if e["trailing"] >= 30 and e["share_ratio"] is not None]
    fastest = max(growing, key=lambda e: e["share_ratio"])["method"]
    return top_exp, top_comp, fastest


# ---------------------------------------------------------------------------
# Audit sampling (printing only; verdicts are recorded by hand)
# ---------------------------------------------------------------------------

def audit_sample(ids):
    ids = sorted(ids)
    if len(ids) <= AUDIT_SAMPLE_SIZE:
        return ids
    return random.Random(AUDIT_SEED).sample(ids, AUDIT_SAMPLE_SIZE)


def print_audit_sample(rows, texts, field, keys, dropped=False):
    trailing = rows_in(rows, "trailing")
    for key in keys:
        if dropped:
            ids = [r["id"] for r in trailing if key in r["methods"] and key not in r["methods_refined"]]
        else:
            ids = [r["id"] for r in trailing if key in r[field]]
        print("=" * 20, key, "tagged:", len(ids))
        for record_id in audit_sample(ids):
            title, text = texts[record_id]
            print("##", record_id, "|", title)
            print("    ", text[len(title):][:900])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def v2_consistency(rows, texts):
    """How many rows get different v2 tags when re-matched from corpus text (should be 0)."""
    mismatches = 0
    for row in rows:
        again = [key for key in METHOD_KEYS if V2_REGEX[key].search(texts[row["id"]][1])]
        if again != row["methods"]:
            mismatches += 1
    return mismatches


def build_output(rows, texts):
    table_refined = compute_method_table(rows, "methods_refined")
    table_v2 = compute_method_table(rows, "methods")
    top_exp, top_comp, fastest = pick_methods_for_exemplars(table_refined)
    exemplar_keys = top_exp + top_comp + [fastest]
    return {
        "description": "Q4 methods: counts of in-scope arXiv preprints per method (refined lexicon), "
                       "trailing vs preceding window; see analysis/methods.py docstring.",
        "taxonomy_version": tx.TAXONOMY_VERSION,
        "population": "in-scope arXiv records (analysis/classified.jsonl) in the trailing "
                      "(2025-09-24..2026-09-23) and preceding (2024-09-24..2025-09-23) windows",
        "in_scope": dict((w, len(rows_in(rows, w))) for w in WINDOWS),
        "refined_methods": sorted(REFINED_METHODS),
        "ci_formula": "exp(log R +- 1.96*sqrt(1/T+1/P+1/scope_T+1/scope_P))",
        "v2_retag_mismatches": v2_consistency(rows, texts),
        "methods": table_refined,
        "methods_v2_unrefined": table_v2,
        "kind_totals": compute_kind_totals(rows, "methods_refined"),
        "kind_totals_v2_unrefined": compute_kind_totals(rows, "methods"),
        "top_methods_per_cluster_trailing": compute_top_methods_per_cluster(rows, "methods_refined"),
        "co_occurrences": compute_co_occurrences(rows, "methods_refined"),
        "exemplar_methods": {"top_experimental": top_exp, "top_computational": top_comp,
                             "fastest_growing": fastest},
        "exemplar_candidates": dict((key, exemplar_candidates(rows, texts, key)) for key in exemplar_keys),
    }


def main():
    parser = argparse.ArgumentParser(description="Q4 methods counts")
    parser.add_argument("--audit-sample", action="store_true", help="print audit sample and exit")
    parser.add_argument("--refined", action="store_true", help="sample from refined tags (refined methods only)")
    parser.add_argument("--dropped", action="store_true", help="sample v2-tagged records the refinement dropped")
    parser.add_argument("--method", default=None, help="restrict --audit-sample to one method")
    args = parser.parse_args()

    rows = load_population()
    texts = load_texts(set(row["id"] for row in rows))
    attach_refined_methods(rows, texts)

    if args.audit_sample:
        if args.method:
            keys = [args.method]
        elif args.refined or args.dropped:
            keys = sorted(REFINED_METHODS)
        else:
            keys = METHOD_KEYS
        field = "methods_refined" if args.refined else "methods"
        print_audit_sample(rows, texts, field, keys, dropped=args.dropped)
        return

    output = build_output(rows, texts)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=1, ensure_ascii=False)
    print("wrote", OUTPUT_PATH)
    for entry in output["methods"]:
        print("%-30s %-13s T=%5d P=%5d shareT=%.3f R=%s [%s, %s]" % (
            entry["method"], entry["kind"], entry["trailing"], entry["preceding"],
            entry["share_trailing"], entry["share_ratio"], entry["ci95_low"], entry["ci95_high"]))


if __name__ == "__main__":
    main()
