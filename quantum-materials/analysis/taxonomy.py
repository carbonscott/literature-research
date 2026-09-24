"""
Transparent keyword taxonomy for the quantum-materials preprint landscape.

Taxonomy v2 (frozen). See TAXONOMY_CHANGELOG.md for the v1 -> v2 changes and
precision_audit_v2.json for the per-cluster precision spot-check.

Everything here is plain data (regex strings) plus a few small functions:

    normalize_text(text)        -> text with LaTeX/HTML/unicode noise removed
    record_text(record)         -> normalized "title. abstract" of a corpus record
    record_title(record)        -> normalized title of a corpus record
    scope_hits(text)            -> list of QM scope keyword names that match
    in_scope(record)            -> bool   (the scope rule, see SCOPE_DESCRIPTION)
    scope_reason(record)        -> "category" | "keyword" | None
    classify(text, title=None)  -> list of cluster keys (multi-label)
    primary_cluster(text, title=None) -> first matching cluster in CLUSTERS order, or None
    find_methods(text)          -> list of method keys
    find_families(text)         -> list of material-family keys
    classify_record(record)     -> dict with every label for one corpus record

Case rules (so patterns stay readable):
  * QM_SCOPE, CLUSTERS and METHODS patterns are compiled CASE-INSENSITIVE.
    Acronyms and chemical formulas inside them are wrapped in cs(...), which
    makes that piece case-sensitive (e.g. cs(r"\\bSTM\\b") will not match "stm").
  * MATERIAL_FAMILIES patterns are compiled CASE-SENSITIVE (formulas);
    plain-word names inside them are wrapped in ci(...) to be case-insensitive.

Title-only patterns: some phrases are usually passing mentions when they appear
in an abstract ("... relevant to strongly correlated systems"). A cluster's
`title_patterns` count only when they match the TITLE. classify(text, title)
needs the normalized title for that; if title is None the whole text is used
(convenient for tests, where the text is a title).

Always call normalize_text() before matching, so that arXiv forms such as
"La$_3$Ni$_2$O$_7$", "La_3Ni_2O_7" or "La₃Ni₂O₇" all become "La3Ni2O7".

All regexes are compiled once at import time (bottom of this file).
"""

import html
import re

TAXONOMY_VERSION = "v2"


def cs(pattern):
    """Make a sub-pattern case-sensitive inside a case-insensitive regex."""
    return "(?-i:" + pattern + ")"


def ci(pattern):
    """Make a sub-pattern case-insensitive inside a case-sensitive regex."""
    return "(?i:" + pattern + ")"


# Guards for chemical formulas: not glued to a preceding letter/digit, and not
# followed by a lowercase letter or digit (so "MnTe" does not match "MnTe2").
L = r"(?<![A-Za-z0-9])"
R = r"(?![a-z0-9])"


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

_SUBSCRIPT_DIGITS = {
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
    "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "₊": "+", "₋": "-", "⁺": "+", "⁻": "-",
}

_DASHES = ["\u2212", "\u2010", "\u2011", "\u2012", "\u2013", "\u2014"]

_LATEX_GREEK = [
    ("\\delta", "δ"), ("\\Delta", "Δ"), ("\\alpha", "α"), ("\\beta", "β"),
    ("\\gamma", "γ"), ("\\kappa", "κ"), ("\\lambda", "λ"), ("\\mu", "μ"),
    ("\\nu", "ν"), ("\\pi", "π"), ("\\sigma", "σ"), ("\\tau", "τ"),
    ("\\phi", "φ"), ("\\chi", "χ"), ("\\psi", "ψ"), ("\\omega", "ω"),
    ("\\theta", "θ"), ("\\epsilon", "ε"), ("\\varepsilon", "ε"),
]

_LATEX_ACCENTS = [
    ("{\\'e}", "é"), ("\\'{e}", "é"), ("\\'e", "é"),
    ('{\\"o}', "ö"), ('\\"{o}', "ö"), ('\\"o', "ö"),
    ('{\\"u}', "ü"), ('\\"{u}', "ü"), ('\\"u', "ü"),
]


def normalize_text(text):
    """Return plain text suitable for regex matching.

    - HTML/JATS tags stripped and entities unescaped
    - LaTeX math markup removed: $, _, ^, {, }, \\mathrm, \\rm, \\text ...
      ("La$_{3}$Ni$_2$O$_{7-\\delta}$" -> "La3Ni2O7-δ")
    - unicode subscripts -> digits, micro sign -> Greek mu, dashes -> "-"
    - whitespace collapsed
    Case is preserved (formulas and acronyms are case-sensitive).
    """
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    for accent, letter in _LATEX_ACCENTS:
        text = text.replace(accent, letter)
    text = re.sub(r"\\(?:mathrm|mathit|mathbf|textrm|textit|textbf|text|rm|it|bf)\b", "", text)
    for command, letter in _LATEX_GREEK:
        text = text.replace(command, letter)
    for char in "$_^{}":
        text = text.replace(char, "")
    for sub, digit in _SUBSCRIPT_DIGITS.items():
        text = text.replace(sub, digit)
    text = text.replace("\u00b5", "μ")  # micro sign -> Greek mu
    for dash in _DASHES:
        text = text.replace(dash, "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def record_text(record):
    """Normalized 'title. abstract' for a corpus record (dict)."""
    title = record.get("title") or ""
    abstract = record.get("abstract") or ""
    return normalize_text(title + ". " + abstract)


def record_title(record):
    """Normalized title of a corpus record (dict)."""
    return normalize_text(record.get("title") or "")


# ---------------------------------------------------------------------------
# Scope rule (Q: which records count as "quantum materials" at all?)
# ---------------------------------------------------------------------------

SCOPE_ARXIV_CATEGORIES = ["cond-mat.str-el", "cond-mat.supr-con"]

# name -> regex (case-insensitive; cs() pieces case-sensitive)
QM_SCOPE = {
    "topological": r"\btopological(?:ly)?[- ](?:insulator|semimetal|superconduct\w*|phase|state|order|band|surface|edge|crystalline|invariant|material|magnon|magnet\w*|quantum|nodal|hall|matter|protected|charge|spin|metal|kondo|excitation|defect mode)|\bhigher[- ]order topolog",
    "moire_twisted": r"\bmoir[eé]|\btwisted (?:bi|tri|double[- ]bi|multi|mono)layer|\btwisted (?:graphene|WSe2|MoTe2|MoSe2|WS2|TMD|homobilayer|heterobilayer|van der waals)|\bmagic[- ]angle|\btwist[- ]angle|\btwistronic",
    "correlated_electrons": r"\bstrongly[- ]correlated|\bcorrelated (?:electron|insulator|metal|state|phase|material|oxide|system|topolog|flat|quantum)|\belectron(?:ic)?[- ]correlation|\bHubbard[- ](?:model|physics|system|ladder|interaction|band|chain|lattice|type)|\b(?:extended|Fermi|Bose)[- ]Hubbard|\bt-J model|\bHund'?s (?:metal|coupling)",
    "superconductivity": r"\bsuperconduct",
    "spin_liquid": r"\bspin[- ]liquid|\bspinon",
    "frustrated_magnetism": r"\bfrustrat\w* (?:magnet|antiferromagnet|spin|quantum magnet|lattice)|\bmagnetic(?:ally)? frustrat|\bKitaev(?![- ]chain)|\bspin[- ]ice|\bpyrochlore (?:magnet|lattice|antiferromagnet)|\bquantum magnet(?:s|ism)?\b",
    "altermagnet": r"\baltermagnet|\bnon-?relativistic spin[- ]split",
    "kagome": r"\bkagom[eé]",
    "weyl_dirac_semimetal": r"\bWeyl[- ](?:semimetal|fermion|node|point|metal|cone)|\bDirac[- ](?:semimetal|fermion|cone|node|material|nodal|point)|\bnodal[- ](?:line|loop|ring|point|chain)",
    "heavy_fermion_kondo": r"\bheavy[- ]fermion|\bKondo\b",
    "charge_density_wave": r"\bcharge[- ]density[- ]wave|" + cs(r"\bCDWs?\b") + r"|\bcharge[- ]order|\bpair[- ]density[- ]wave|\bspin[- ]density[- ]wave|\bdensity[- ]wave (?:order|state|instabilit|transition)",
    "qah_chern": r"\bquantum anomalous hall|\bchern insulator|\bfractional chern|\bfractional quantum (?:anomalous |spin )?hall|\bquantum hall|" + cs(r"\bF?QAHE?\b"),
    "majorana": r"\bmajorana|\bparafermion",
    "flat_band": r"\bflat[- ]bands?\b",
    "excitonic_insulator": r"\bexcitonic insulat|\bexciton (?:condensat|insulator|crystal|solid)|\binterlayer exciton|\bmoir[eé] exciton",
    "vdw_magnet": r"\bvan der waals (?:magnet|ferromagnet|antiferromagnet|magnetic)|\b(?:2D|two-dimensional) (?:ferro|antiferro)?magnet|" + cs(L + r"(?:CrI3|CrBr3|CrSBr|Fe3GeTe2|Fe3GaTe2|NiPS3|FePS3|MnPS3|Cr2Ge2Te6)"),
    "multiferroic": r"\bmultiferroic|\bmagnetoelectric (?:coupling|effect|multiferroic)",
    "mott": cs(r"\bMott(?![- ](?:Schottky|Gurney|formula for))\b"),
    "quantum_criticality": r"\bquantum[- ]critical",
    "nematic": r"\bnematicity|\belectronic nematic|\bnematic (?:fluctuation|order|superconduct|susceptibility|quantum|transition|phase)",
    "strange_metal": r"\bstrange[- ]metal|\bplanckian|\bnon-fermi[- ]liquid|\bmarginal fermi liquid",
    "skyrmion": r"\bskyrmion|\bantiskyrmion|\bhopfion|\bmerons?\b",
    "berry_curvature": r"\bberry (?:curvature|phase|connection)|\bquantum (?:metric|geometry)",
    "quantum_spin_hall": r"\bquantum spin hall|" + cs(r"\bQSHE?\b"),
    "wigner_crystal": r"\bwigner (?:crystal|solid|molecule)",
    "luttinger_anyon": r"\bluttinger liquid|\banyon|\bfractionali[sz]",
    "quantum_magnetism": r"\bHeisenberg (?:model|antiferromagnet|chain|ladder|magnet)|\bJ1-J2|\bspin[- ](?:chain|ladder)s?\b|\bXXZ (?:model|chain)",
    "flagship_materials": cs(L + r"(?:La3Ni2O7|La4Ni3O10|La2PrNi2O7|NdNiO2|CsV3Sb5|KV3Sb5|RbV3Sb5|ScV6Sn6|RuCl3|UTe2|CeRh2As2|YbRh2Si2|MnBi2Te4|CrSb|Mn5Si3|LaH10|H3S|LaBeH8|CaH6|YH6|YBa2Cu3O|Bi2Sr2CaCu2O|FeSe|BaFe2As2|Sr2RuO4|Ta2NiSe5|EuCd2As2|Co3Sn2S2)"),
    "quantum_materials_phrase": r"\bquantum materials?\b",
    "material_classes": r"\bcuprate|\bnickelate|\biron[- ](?:pnictide|chalcogenide|selenide|based superconduct)|\bpnictide|\biridate|\bruthenate|\bheavy[- ]electron",
}

# If a scope keyword matches but its veto phrase also matches, that keyword is
# ignored (e.g. "superconducting magnet" for fusion, "nematic liquid crystal").
SCOPE_CONTEXT_VETO = {
    "superconductivity": r"\bsuperconducting (?:magnet|coil|cable|tape|wire|fault[- ]current|maglev|qubit|quantum (?:processor|computer|circuit)|resonator|cavit|radio[- ]frequency|RF|nanowire single|transmission line|generator|motor|bearing|undulator|solenoid)|\bSRF\b|\bHTS (?:tape|coil|cable|magnet)|\bSNSPD|\bsingle[- ]photon detector",
    "nematic": r"\bliquid[- ]crystal|\bactive nematic|\bnematic elastomer|\bnematogen|\bmesogen",
    "moire_twisted": r"\bmoir[eé][- ](?:fringe|effect|method|technique|metrology|deflectometry|interferometr|topograph|profilometr)|\bmoir[eé] pattern (?:analysis|measurement of strain)",
    "majorana": r"\bneutrinos?\b|\bmajorana mass|\bneutrinoless",
    "flat_band": r"\bphotonic flat band|\bflat[- ]band (?:photonic|laser|lattice of waveguides)",
    # v2: classical-wave topology (photonic / acoustic / mechanical /
    # electric-circuit metamaterials) is not a quantum material
    "topological": r"\btopological (?:photonic|photonics|acoustic|acoustics|phononic|mechanical|laser|lasing|metamaterial|circuit|data analysis|optimi[sz]ation)|\bphotonic (?:topolog|crystal|lattice|waveguide)|\bacoustic (?:topolog|metamaterial|crystal|wave)|\bmechanical (?:metamaterial|lattice)|\btopolectric|\bmetamaterials?\b|\bphononic crystal|\btopology optimi",
}


def scope_hits(text):
    """Names of QM_SCOPE keywords matching normalized text (after vetoes)."""
    hits = []
    for name, regex in _SCOPE_COMPILED:
        if not regex.search(text):
            continue
        veto = _SCOPE_VETO_COMPILED.get(name)
        if veto is not None and veto.search(text):
            continue
        hits.append(name)
    return hits


def in_scope(record, text=None):
    """Scope rule.

    arXiv records: in scope if categories include cond-mat.str-el or
    cond-mat.supr-con, OR title+abstract hits any QM_SCOPE keyword.
    Other servers: in scope if title+abstract hits any QM_SCOPE keyword.
    `text` may be passed if record_text(record) was already computed.
    """
    if record.get("server") == "arxiv":
        categories = record.get("categories") or []
        for category in SCOPE_ARXIV_CATEGORIES:
            if category in categories:
                return True
    if text is None:
        text = record_text(record)
    return len(scope_hits(text)) > 0


def scope_reason(record, text=None):
    """Why a record is in scope: "category" (arXiv category rule),
    "keyword" (QM_SCOPE keyword hit), or None (out of scope)."""
    if record.get("server") == "arxiv":
        categories = record.get("categories") or []
        for category in SCOPE_ARXIV_CATEGORIES:
            if category in categories:
                return "category"
    if text is None:
        text = record_text(record)
    if scope_hits(text):
        return "keyword"
    return None


# ---------------------------------------------------------------------------
# Topic clusters (Q1). Ordered MOST SPECIFIC -> MOST GENERIC:
#   material-specific superconductor families, then specific material classes
#   (kagome, altermagnets, rhombohedral graphene), then phenomena, then
#   broad correlated-electron physics, then cross-cutting approaches
#   (ultrafast/nonequilibrium, ML/AI), then three v2 FALLBACK clusters that
#   only become primary when nothing more specific matched:
#   generic magnetism, quantum many-body theory, other superconductivity.
# primary_cluster() returns the first match in this order.
# Each cluster has:
#   patterns        matched against normalized "title. abstract" under the
#                   v2 EVIDENCE RULE (has_evidence): a title hit, or at least
#                   two hits in title+abstract (one passing mention is not enough)
#   title_patterns  (optional) phrases that count only when they are in the title
#   exclude         the cluster is NOT assigned if any of these match the text
#   residual        (optional, v2 fallbacks) assigned ONLY when no earlier
#                   cluster matched, so a record gets at most one residual
#                   cluster and its multi-label count equals its primary count
# ---------------------------------------------------------------------------

CLUSTERS = [
    {
        "key": "nickelate_sc",
        "label": "Nickelates (bilayer/trilayer & infinite-layer) and nickelate superconductivity",
        "patterns": [
            r"\bnickelates?\b",
            cs(r"Ni2O7|Ni3O10|Ni3O11|Ni5O12|NiO2" + R),
            r"\binfinite[- ]layer nickel",
        ],
        "exclude": [],
    },
    {
        "key": "cuprate_sc",
        "label": "Cuprate superconductivity",
        "patterns": [
            r"\bcuprates?\b",
            cs(L + r"(?:YBCO|LSCO|LBCO|NCCO|PCCO|BSCCO|Bi-?22[01][12]|Bi-?2223|Hg-?12[01][1-3]|Tl-?2201|Y-?123)" + R),
            cs(L + r"(?:REBCO|ReBCO|GdBCO|EuBCO|SmBCO|NdBCO|DyBCO)" + R + r"|Ba2Cu3O|Sr2Ca\d?Cu\d?O|Ba2Ca\d?Cu\d?O|YBa2Cu3O|Bi2Sr2CaCu2O|Bi2Sr2CuO|Bi2Sr2Ca2Cu3O|HgBa2|La2-xSrxCuO4|La2-xBaxCuO4|Nd2-xCexCuO4|Pr2-xCexCuO4|La2CuO4|CuO2(?:[- ]?plane)"),
        ],
        "exclude": [],
    },
    {
        "key": "iron_based_sc",
        "label": "Iron-based superconductivity (pnictides & chalcogenides)",
        "patterns": [
            r"\biron[- ](?:based|pnictide|chalcogenide|selenide|arsenide)",
            cs(r"\bFe-based") + r" superconduct",
            cs(L + r"(?:FeSe|FeTe|FeS)(?![a-z])"),
            cs(r"Fe\(Te,\s?Se\)|Fe\(Se,\s?Te\)|Fe2As2|Fe2\(As|FeAsO|LiFeAs|NaFeAs|Fe4As4|Fe2Se2(?!O)|FeAs" + R),
        ],
        "exclude": [],
    },
    {
        "key": "hydride_high_pressure_sc",
        "label": "Hydride / high-pressure superconductivity (incl. room-temperature SC claims)",
        "patterns": [
            r"\b(?:super)?hydrides?\b.{0,80}superconduct|superconduct.{0,80}\b(?:super)?hydrides?\b",
            r"\bsuperhydride|\bclathrate hydride|\bternary hydride",
            cs(L + r"(?:H3S|LaH10|LaH9|YH6|YH9|YH4|CaH6|CeH9|CeH10|ThH10|LaBeH8|LaB2H8|LuH3|Lu-H-N|MgIrH6)" + R),
            r"\bpressure[- ]induced superconduct|\bsuperconduct\w* (?:under|at) (?:high |megabar )?pressure|\bhigh[- ]pressure superconduct",
            r"\broom[- ]temperature superconduct|" + cs(r"\bLK-99\b"),
        ],
        "exclude": [],
    },
    {
        "key": "kagome",
        "label": "Kagome metals & kagome materials",
        "patterns": [
            r"\bkagom[eé]",
            cs(r"V3Sb5|V6Sn6|Mn6Sn6|Cr3Sb5|Ti3Bi5|Co3Sn2S2|Fe3Sn2" + R + r"|" + L + r"CoSn" + R),
        ],
        "exclude": [],
    },
    {
        "key": "altermagnetism",
        "label": "Altermagnetism, p-wave/unconventional magnets & non-relativistic spin splitting",
        "patterns": [
            r"\baltermagnet|\balter-magnet",
            r"\bnon-?relativistic spin[- ]split|\bspin[- ]split(?:ting)? (?:collinear )?antiferromagnet|\bspin[- ]splitter",
            # v2: odd-parity "p-wave magnets" are the sibling of altermagnets
            r"\b[pf]-wave magnet|\bodd-parity magnet|\bunconventional magnet(?:s|ism)\b",
            cs(L + r"(?:CrSb|Mn5Si3|KV2Se2O|V2Te2O|V2Se2O)" + R),
        ],
        "exclude": [],
    },
    {
        "key": "fractional_qah_chern",
        "label": "Fractional / quantum anomalous Hall & Chern insulators (incl. quantum Hall, Landau levels)",
        "patterns": [
            r"\bquantum anomalous hall|\bfractional (?:quantum )?anomalous hall|" + cs(r"\bF?QAHE?\b"),
            r"\bfractional chern|\bchern insulator|\bchern bands?\b|\bfractional quantum (?:spin )?hall|" + cs(r"\bFQHE?\b"),
            # v2: generic "anyon" moved to quantum_many_body_theory (lattice-model anyons)
            r"\bcomposite fermion|\bfractional(?:ly)? charged",
        ],
        # v2 audit: plain "quantum Hall" / "Landau levels" in an abstract were
        # often context (cavities, Casimir forces, generic topology), so these
        # count only in the title.
        "title_patterns": [r"\bquantum hall|\blandau levels?\b|\blandau quantization"],
        "exclude": [],
    },
    {
        "key": "rhombohedral_multilayer_graphene",
        "label": "Rhombohedral / multilayer (untwisted) graphene",
        "patterns": [
            r"\brhombohedral(?:ly)?[- ](?:stacked |multilayer |trilayer |tetralayer |pentalayer |hexalayer |heptalayer |few-layer |n-layer )?graphene",
            r"\brhombohedral (?:multilayer|trilayer|tetralayer|pentalayer|hexalayer|heptalayer|stacking)",
            cs(r"\bABCA?B?C?[- ]stacked|\bABC (?:trilayer|graphene)"),
            r"\b(?:bernal|AB)[- ](?:stacked )?(?:bilayer|trilayer)|\b(?:multilayer|few[- ]layer|trilayer|tetralayer|pentalayer|hexalayer|heptalayer) graphene",
            r"(?<!twisted )(?<!double )(?<!twisted double )\bbilayer graphene",
        ],
        "exclude": [r"\btwisted (?:bi|tri|double|multi|mono)[- ]?(?:bi)?layer|\bmagic[- ]angle|\btwist angle|\bhelical trilayer|\bmoir[eé] (?:bi|tri)layer graphene"],
    },
    {
        "key": "moire_twisted_2d",
        "label": "Moire & twisted 2D systems (TBG, twisted TMDs, moire heterostructures)",
        "patterns": [
            r"\bmoir[eé]",
            r"\btwisted (?:bi|tri|double[- ]bi|multi|mono)layer|\btwisted mono-?bilayer|\bhelical trilayer|\btwisted (?:graphene|WSe2|MoTe2|MoSe2|WS2|TMD|homobilayer|heterobilayer|van der waals|heterostructure)",
            r"\bmagic[- ]angle|\btwist[- ]angle|\btwistronic",
            cs(r"\b(?:MA)?TBG\b|\btMoTe2\b|\btWSe2\b|\btMoSe2\b|\bTDBG\b|\bTTG\b"),
        ],
        "exclude": [r"\bmoir[eé][- ](?:fringe|effect|method|technique|metrology|deflectometry|interferometr|profilometr)|\bmagic[- ]angle spinning"],
    },
    {
        "key": "unconventional_topological_sc",
        "label": "Unconventional & topological superconductivity, Majorana, SC diode/Josephson devices",
        "patterns": [
            r"\bmajorana|\bparafermion|\btopological superconduct|\btopological qubit|\bkitaev chain|\bzero[- ]bias (?:conductance )?peak",
            r"\bchiral superconduct|\b(?:spin[- ])?triplet (?:superconduct|pairing|supercurrent)|\bp-wave(?! magnet)|\bf-wave(?! magnet)|\bunconventional (?:superconduct|pairing)|\bnodal superconduct|\bising superconduct",
            r"\bpair[- ]density[- ]wave|" + cs(r"\bPDW\b|\bFFLO\b") + r"|\bfinite[- ]momentum (?:pairing|cooper)",
            r"\bsuperconducting diode|\b(?:josephson )?diode effect|\bnonreciprocal (?:supercurrent|critical current|superconduct)|\bjosephson|\bandreev|\bproximity[- ]induced superconduct|\bsuperconducting proximity|\b(?:yu-)?shiba",
            cs(r"\bSr2RuO4\b|\bUTe2\b|\bCeRh2As2\b"),
        ],
        "exclude": [],
    },
    {
        "key": "spin_liquid_frustrated",
        "label": "Quantum spin liquids & frustrated magnetism (Kitaev, triangular, pyrochlore)",
        "patterns": [
            r"\bspin[- ]liquid|" + cs(r"\bQSLs?\b") + r"|\bspinons?\b",
            r"\bfrustrat\w* (?:magnet|antiferromagnet|spin|quantum|lattice)|\bmagnetic(?:ally)? frustrat|\bgeometric(?:al|ally)? frustrat",
            r"(?<!Ye-)\bKitaev(?![- ]chain)",  # not Kitaev chains, not Sachdev-Ye-Kitaev
            cs(r"RuCl3|Na2IrO3|Li2IrO3|H3LiIr2O6|Na2Co2TeO6|Na3Co2SbO6|Co2\(AsO4\)2|YbMgGaO4|NaYbSe2|NaYbO2|KYbSe2|Cu3Zn\(OH\)6Cl2|ZnCu3\(OH\)6Cl2|Ce2Zr2O7|Yb2Ti2O7|Dy2Ti2O7|Ho2Ti2O7"),
            r"\bspin[- ]ice|\bpyrochlore|\bshastry[- ]sutherland|\bherbertsmithite|\btriangular[- ]lattice (?:antiferromagnet|magnet|heisenberg|quantum)|\bvalence[- ]bond (?:solid|crystal)|\bJ1-J2|\bresonating[- ]valence[- ]bond|" + cs(r"\bRVB\b"),
        ],
        "exclude": [],
    },
    {
        "key": "heavy_fermion_kondo_qcp",
        "label": "Heavy fermions, Kondo physics & metallic quantum criticality",
        "patterns": [
            r"\bheavy[- ](?:fermion|electron|quasiparticle)|\bKondo\b|\bmixed[- ]valen|\bintermediate valen|\bhidden order|\b[45]f[- ](?:electron|state|orbital|band|moment|hybridi[sz]ation)s?|\bf-electron|\bvalence (?:transition|fluctuation)s?",
            # v2: quantum criticality only in metallic / f-electron settings; generic
            # quantum phase transitions of spin or lattice models go to quantum_many_body_theory
            r"\b(?:metallic|itinerant|kondo|heavy[- ]fermion|ferromagnetic|antiferromagnetic|magnetic|nematic) quantum critical|\bquantum critical (?:metals?|fermi|fluctuations in (?:a |the )?metal)|\bkondo breakdown|\blocal quantum critical",
            cs(L + r"(?:UTe2|CeRh2As2|CeCoIn5|CeRhIn5|CeIrIn5|YbRh2Si2|URu2Si2|UPt3|UBe13|CeCu2Si2|UCoGe|URhGe|UGe2|CeCu6|CeCu6-xAux|CePd2Si2|CeSb2|YbAl3|YbB12|SmB6|CeAl3|Ce3Bi4Pt3|CeSiI|UPd2Al3|UNi2Al3|YbCuAl)" + R),
        ],
        "exclude": [],
    },
    {
        "key": "vdw_magnets_topological_magnetism",
        "label": "2D/van der Waals magnets, skyrmions, topological magnetism, multiferroics & spintronics/magnonics",
        "patterns": [
            r"\bvan der waals (?:magnet|ferromagnet|antiferromagnet|magnetic)|\b(?:2D|two-dimensional|layered) (?:ferro|antiferro)?magnet",
            cs(L + r"(?:CrI3|CrBr3|CrCl3|CrSBr|Fe3GeTe2|Fe3GaTe2|Fe4GeTe2|Fe5GeTe2|FexGeTe2|Fe3-xGeTe2|NiPS3|FePS3|MnPS3|CoPS3|NiPSe3|MnPSe3|CrPS4|Cr2Ge2Te6|CrGeTe3|VI3|NiI2|CrTe2|Cr2Te3|MnBi2Te4|MnSi|Cu2OSeO3|GaV4S8|MnGe)" + R),
            r"\bskyrmion|\bantiskyrmion|\bhopfion|\bmerons?\b|\btopological (?:magnet|spin texture|hall)|\bspin texture|\bdzyaloshinskii|\bchiral (?:magnet|helimagnet)|\bhelimagnet",
            r"\bmagnons?\b|\bmagnonic|\bspin[- ]orbit torque|(?<!quantum )\bspin hall|\bspin pumping|\bspin seebeck|\bmultiferroic|\bmagnetoelectric|\bspintronic",
        ],
        "exclude": [],
    },
    {
        "key": "cdw_nematic_excitonic",
        "label": "Charge/spin density waves, nematicity, Wigner crystals & excitonic insulators/excitons",
        "patterns": [
            r"\bcharge[- ]density[- ]waves?|" + cs(r"\bCDWs?\b|\bSDWs?\b") + r"|\bcharge[- ]order|\bstripe (?:order|phase)|\bspin[- ]density[- ]wave|\bpeierls (?:transition|instabilit|distortion|insulator|chain|phase transition)|\bspin-peierls",
            r"\bnematicity|\belectronic nematic|\bnematic (?:fluctuation|order|superconduct|susceptibility|quantum|transition|phase|state)",
            r"\bwigner (?:crystal|solid|molecule)",
            r"\bexcitonic insulat|\bexciton (?:condensat|insulator|crystal|solid|superfluid)|\bexcitons?\b|\bexcitonic\b|\bexciton[- ]polariton",
            cs(L + r"(?:Ta2NiSe5|1T-TiSe2|TiSe2|1T-TaS2|TaS2|TaSe2|LaTe3|ErTe3|CeTe3|RTe3)" + R),
        ],
        "exclude": [r"\bliquid[- ]crystal|\bactive nematic|\bnematic elastomer|\bnematic fluid|\bferroelectric nematic"],
    },
    {
        "key": "topological_insulators_semimetals",
        "label": "Topological insulators & semimetals (Weyl/Dirac/nodal), band topology incl. non-Hermitian",
        "patterns": [
            # v2: "topological order" moved to quantum_many_body_theory and
            # Berry curvature / quantum geometry moved to flat_band_quantum_geometry.
            r"\btopological (?:insulator|semimetal|crystalline|band|invariant|surface|edge|material|nodal|quantum chemistry|metal|kondo|magnetoelectric|charge pump|phase|state|matter|transition|properties)|\bhigher[- ]order topolog|\baxion insulator|\bfragile topolog|\bsymmetry indicator|\bobstructed atomic",
            r"\bweyl\b|\bdirac[- ](?:semimetal|fermion|cone|node|material|point|nodal)|\bnodal[- ](?:line|loop|ring|chain|point|surface)|\btriple[- ]point fermion|\bmultifold fermion|\bkramers[- ]weyl",
            r"\bquantum spin hall|" + cs(r"\bQSHE?\b") + r"|\bspin[- ]momentum locking|\bZ2 (?:invariant|topolog)",
            r"\bnon-?hermitian (?:topolog|skin|band|chern|SSH)|\bskin effect",
            r"\bband inversion|\bbulk[- ]boundary correspondence|\bwinding numbers?",
            cs(L + r"(?:Bi2Se3|Bi2Te3|Sb2Te3|MnBi2Te4|MnBi4Te7|TaAs|NbAs|TaP|NbP|Cd3As2|Na3Bi|ZrTe5|HfTe5|EuCd2As2|EuIn2As2|EuSn2As2|PtTe2|PdTe2|CoSi|RhSi|ZrSiS|GdPtBi|Td-MoTe2|Td-WTe2|WTe2|Bi4Br4|Bi4I4|BiSb|Pb1-xSnxTe|SnTe)" + R),
        ],
        "exclude": [r"\btopological (?:data analysis|optimi[sz]ation)|\btopology optimi[sz]ation|\btopological photonic|\bphotonic topolog|\btopological acoustic|\bacoustic topolog|\bmetamaterial|\bphononic crystal|\bmechanical topolog|\btopological lase|\bplasmas?\b|\bnon-hermitian photonic|\bphotonic (?:lattice|crystal|waveguide|system|platform|braid|hopf)|\bsplit-ring",
                    # v2 audit: interacting topological order (anyons, SPT, TQFT, mixed
                    # states) is quantum_many_body_theory, not band topology
                    r"\banyons?\b|\banyonic|\bF-symbols?|\bmixed[- ]state|\bhigher berry|\btopological(?:ly)? order|" + cs(r"\bTQFTs?\b|\bSPTs?\b") + r"|\bfusion categor|\bsymmetry[- ]protected topological"],
    },
    {
        # v2 NEW. Plain flat-band and quantum-geometry papers get their own
        # cluster. It sits AFTER kagome / moire / rhombohedral graphene /
        # topological clusters, so flat bands in those systems keep the more
        # specific primary label; this cluster is primary only for flat bands
        # and band geometry studied on their own (Lieb lattices, quantum metric,
        # nonlinear Hall, flat-band superconductivity, ...).
        "key": "flat_band_quantum_geometry",
        "label": "Flat bands & quantum geometry (quantum metric, Berry curvature; anomalous, nonlinear & orbital Hall responses)",
        "patterns": [
            r"\bflat[- ]?bands?\b|\b(?:quasi|nearly)[- ]flat bands?|\bdispersionless bands?|\bLieb lattice|\bcompact localized states?",
            r"\bquantum (?:metric|geometry|geometric tensor)|\bquantum[- ]geometric|\bband geometry|\bberry curvature|\bnonlinear (?:anomalous )?hall",
            r"\borbital (?:hall|magnetization|angular momentum texture)|\bberry (?:phase|connection)",
            # v2: intrinsic anomalous Hall / Nernst responses are Berry-curvature physics
            r"\banomalous (?:hall|nernst)",
        ],
        "exclude": [r"\bphotonic flat[- ]?band|\bflat[- ]?band (?:photonic|laser|lattice of waveguides)|\bphotonic lattice"],
    },
    {
        "key": "mott_hubbard_strange_metal",
        "label": "Mott/Hubbard physics, strange metals & correlated oxides",
        "patterns": [
            cs(r"\bMott(?![- ](?:Schottky|Gurney))\b") + r"|\bHubbard[- ](?:model|physics|system|ladder|interaction|band|chain|lattice|type)|\b(?:extended|fermi|bose)[- ]hubbard|\bt-J model|\bhund(?:ness|'?s (?:metal|coupling|rule|physics|exchange))",
            r"\bstrange[- ]metal|\bplanckian|\bnon-fermi[- ]liquid|\bmarginal fermi liquid|\blinear[- ]in[- ](?:T|temperature) resistiv|" + cs(r"\bSYK\b") + r"|\bsachdev-ye-kitaev",
            r"\bstrongly[- ]correlated (?:electron|material|metal|oxide|insulator|compound)s?\b|\bcorrelated (?:electron|insulator|metal|oxide|material)s?\b|\bpseudogap|\bmetal[- ]insulator transition|\borbital[- ]selective|\bdoped antiferromagnet|\bdoped mott",
            r"\bdynamical mean[- ]field|" + cs(r"\b(?:DFT\+|LDA\+|c|C-|cluster )?DMFT\b") + r"|\bmanganites?\b|\bcolossal magnetoresist",
            r"\btwo-dimensional electron gas at|" + cs(r"LaAlO3/SrTiO3|KTaO3|\bSrTiO3\b|\bVO2\b|\bV2O3\b|NiS2|NdNiO3|SmNiO3|Sr2IrO4|Sr3Ir2O7|Ca2RuO4|Sr3Ru2O7"),
        ],
        # v2: generic correlation phrases ("... a challenge for strongly
        # correlated systems", quantum-chemistry "electron correlation") are
        # mostly framing in abstracts, so they count only in the title.
        "title_patterns": [
            r"\bstrongly[- ]correlated|\bcorrelated (?:state|phase|system|flat)|\belectron(?:ic)?[- ]correlation",
        ],
        "exclude": [],
    },
    {
        "key": "ultrafast_floquet_noneq",
        "label": "Ultrafast, Floquet & nonequilibrium quantum materials",
        "patterns": [
            r"\bultrafast|\bpump[- ]probe|\bfloquet|\blight[- ](?:induced|driven|enhanced|controlled)|\bphoto-?induced|\bphoto-?excit|\btime-resolved|" + cs(r"\btr-?ARPES\b"),
            r"\bfemtosecond|\battosecond|\bpicosecond|\bterahertz[- ](?:driven|pump|field[- ]driven)|\bcoherent phonon|\blaser[- ]driven|\bhigh[- ]harmonic generation|" + cs(r"\bHHG\b") + r"|\bprethermal|\bhidden (?:phase|state) (?:induced|reached|by light)",
        ],
        # v2: generic "non-equilibrium" matched many-body dynamics theory and
        # SC resonator papers, so it counts only in the title.
        "title_patterns": [r"\bnon-?equilibrium|\bout[- ]of[- ]equilibrium"],
        "exclude": [],
    },
    {
        "key": "ml_ai",
        "label": "Machine learning / AI for quantum materials",
        "patterns": [
            r"\bmachine[- ]learn|\bneural[- ]network|\bdeep[- ]learn|\bartificial intelligence|" + cs(r"\bAI\b|\bLLMs?\b|\bGNNs?\b|\bNQS\b"),
            r"\blarge language model|\bgraph neural|\bgenerative (?:model|AI|adversarial|diffusion)|\bdiffusion model|\bfoundation model|\btransformer[- ](?:based|model|architecture|network)",
            r"\bactive learning|\bautonomous (?:lab|experiment|discovery|synthesis)|\bself-driving lab|\bbayesian optimi[sz]ation|\bneural (?:quantum state|network quantum state)|\bmaterials informatics|\bdata-driven (?:discovery|search|design|screening)|\bhigh-throughput (?:screening|search|calculation|computational)",
        ],
        "exclude": [],
    },
    # ------------------------------------------------------------------
    # v2 FALLBACK clusters (primary only if nothing above matched)
    # ------------------------------------------------------------------
    {
        # Magnetism that is not frustrated / spin-liquid, not vdW / skyrmion /
        # spintronics, not altermagnetic: magnetic order and quantum magnets,
        # spin-chain / ladder / dimer COMPOUNDS, spin-orbit-entangled and
        # multipolar magnets. Model-only spin chains go to quantum_many_body_theory.
        "key": "quantum_magnetism_ferroic_order",
        "residual": True,
        "label": "Quantum & low-dimensional magnetism and ferroic order (antiferro/ferrimagnets, spin-chain/ladder/dimer compounds, spin-orbit-entangled & multipolar magnets, ferroelectric/ferroaxial order)",
        "patterns": [
            r"\bantiferromagnet|\bferrimagnet|\bferromagnet|\bmagnetic (?:order|ordering|structure|ground state|phase transition|phase diagram|excitation|anisotropy|moment|exchange|interaction|transition|susceptibility|insulator|semiconductor|compound|material|propert(?:y|ies))s?\b|\bmagnetism\b",
            r"\bspin[- ](?:waves?|dimers?|gaps?|glass|reorientation|excitations?|flop|singlets?|nematic|peierls)\b|\bmagnetization (?:plateau|process|step)|\bmagnetic (?:multipole|octupole|quadrupole)|\bmultipolar (?:order|phase|magnet)",
            r"\bspin[- ]orbit[- ]entangled|\bj ?eff ?= ?[13]/2|\bn[ée]el (?:order|temperature|state|phase)|\bexchange (?:interaction|coupling|constant|parameter)s?|\bsingle[- ]molecule magnet|\bspin[- ]phonon|\bmagneto-?elastic|\bmagnetocaloric",
            r"\bquantum magnet(?:s|ism)?\b|\bspin[- ](?:chain|ladder|dimer) (?:compound|material|magnet|system)|\bdimeri[sz]ed (?:antiferromagnet|chain|magnet|spin)",
            # v2: non-magnetic ferroic order (ferroelectric, ferroaxial, polar metals)
            r"\bferroelectric|\bferroaxial|\bpolar metals?\b|\bferroic",
        ],
        "exclude": [r"\bliquid[- ]crystal|\bnematic fluid|\bferroelectric nematic"],
    },
    {
        # Theory of quantum many-body systems that is not tied to a material
        # family: tensor networks, spin-chain / lattice-gauge models,
        # generalized (non-invertible, higher-form, subsystem) symmetries,
        # SPT & topological order, anyons in lattice models, scars /
        # fragmentation / thermalization, entanglement, CFT & criticality.
        "key": "quantum_many_body_theory",
        "residual": True,
        "label": "Quantum many-body theory & generalized symmetries (tensor networks, spin-chain & lattice-gauge models, non-invertible/higher-form symmetries, SPT/topological order & anyons, scars, entanglement)",
        "patterns": [
            # tensor networks
            r"\btensor[- ]networks?|\bmatrix[- ]product (?:state|operator)s?|\bprojected entangled|\btensor renormali[sz]ation|" + cs(r"\b(?:i|fi|t)?DMRG\b|\b(?:i)?PEPS\b|\bMERA\b|\bTEBD\b|\bTDVP\b|\bVUMPS\b"),
            # lattice gauge theories
            r"\blattice gauge|\bgauge theor(?:y|ies)|\bquantum link model|\bschwinger model|\bgauging\b",
            # generalized symmetries and anomalies
            r"\bnon-?invertible|\bhigher[- ]form|\b(?:one|two|1|2|p)-form symmetr|\bgenerali[sz]ed symmetr|\bcategorical symmetr|\bfusion categor|\bsymTFT|\bsymmetry TFT|\bhigher[- ]group|\b2-group|\bsubsystem symmetr|\bdipole (?:symmetr|conserv)|\bmultipole symmetr|\bmodulated symmetr|\bkramers[- ]wannier|\bduality defects?|\blieb-schultz-mattis|\b't hooft anomal|\banomaly (?:matching|inflow)|\bsymmetry[- ]protected topological|" + cs(r"\bSPTs?\b") + r"|\bsymmetry fractionali[sz]|\bstrong-to-weak|\b(?:mixed|gravitational|parity|fermionic|global) anomal|\banomaly[- ]free|\bsymmetry[- ]enforced|\bgaplessness",
            # topological order, anyons, topological codes
            r"\btopological(?:ly)? order|\btoric code|\bquantum double|\bstring[- ]net|\bfractons?\b|\bfractonic|\banyons?\b|\banyonic|\bnon-abelian (?:statistics|topological order)|\btopological entanglement entropy|\btopological quantum field theor|" + cs(r"\bTQFTs?\b") + r"|\blevin-wen|\bquantum (?:error[- ]correct\w*|LDPC) codes?|\bqLDPC|\bstabilizer codes?|\bsurface codes?",
            # non-equilibrium many-body dynamics
            r"\bmany[- ]body scars?|\bquantum (?:many-body )?scars?|\bscarred|\bhilbert[- ]space fragmentation|\bfragmented hilbert|\bmany[- ]body locali[sz]|" + cs(r"\bMBL\b|\bETH\b") + r"|\beigenstate thermali[sz]ation|\bthermali[sz]ation|\bintegrab(?:le|ility)|\bbethe ansatz|\bquantum chaos|\bscrambling|\boperator (?:growth|spreading)|\bkrylov complexity|\bmeasurement[- ]induced|\bmonitored (?:quantum|circuits?|dynamics|fermions?|systems?)|\brandom (?:unitary |quantum )?circuits?|\bnon-?stabilizerness|\btime crystals?|\bquantum quench|\bdynamical quantum phase transition|\bopen quantum many-body|\bmixed[- ]state (?:phase|topolog|order)",
            # entanglement, CFT, criticality, RG
            r"\bentanglement (?:entropy|entropies|spectrum|spectra|hamiltonian|negativity|dynamics|growth|scaling|transition|structure|asymmetry)|\bconformal field|" + cs(r"\bCFTs?\b") + r"|\bconformal (?:bootstrap|defect|boundary|invariance|manifold)|\bfuzzy sphere|\bdeconfined (?:quantum )?critical|\brenormali[sz]ation[- ]group|\bquantum phase transitions?|\bquantum[- ]critical|" + cs(r"\bQCPs?\b") + r"|\bcentral charge|\bkibble-zurek|\buniversality class",
            # spin-chain, lattice and field-theory models
            r"\bspin[- ](?:1/2 |1 |one-half |s )?(?:chains?|ladders?)\b|\b(?:quantum )?spin models?|\bXXZ|\bXY[Z]? (?:model|chain)s?|\bheisenberg (?:model|chain|ladder)|\bising (?:model|chain|ladder|field theory)|\btransverse[- ]field ising|\bAKLT|\bhaldane (?:chain|phase|gap)|\bhaldane-shastry|\bpotts model|\bquantum rotor|\bdimer models?|\brydberg (?:atom )?(?:arrays?|ladders?|chains?|lattices?)|\bquantum lattice models?|\blattice models?\b|\bsu-schrieffer-heeger|\bgross-neveu|\bsine-gordon|\bbosoni[sz]ation|\bluttinger liquid|\btomonaga|\bquantum many[- ]body|\bmany[- ]body (?:systems?|physics|dynamics|states?|problems?|hamiltonians?|ground states?|wave ?functions?)",
            # many-body methods and concepts (Fermi liquids, diagrammatics, QMC)
            r"\bpolarons?\b|\bpolaronic|\bfermi[- ]liquids?\b|\belectron gas|\bdiagrammatic|\bgreen'?s functions?|\bself-energ|\bfeynman diagram|\bquantum monte carlo|\bsign problem|\bvariational monte carlo|\bquantum field theor(?:y|ies)|\bpath[- ]integral|\bkrylov|\blanczos|\bkeldysh|\bkadanoff",
            # quantum simulation of lattice models, open / dissipative many-body dynamics
            r"\bquantum simulat(?:ion|ions|or|ors)\b|\blindbladian|\bliouvillian|\bopen quantum systems?|\bdissipative (?:quantum|many-body|dynamics)",
        ],
        "exclude": [],
    },
    {
        # Superconductivity that is not in any family / unconventional /
        # hydride cluster above: conventional (phonon-mediated) and newly
        # reported superconductors, high-entropy alloys, 2D films, vortices,
        # superconducting devices (incl. qubit / resonator materials and
        # losses) and applied superconductors. Colour superconductivity (QCD),
        # holographic superconductors and neutron-star matter are excluded.
        "key": "other_superconductivity",
        "residual": True,
        "label": "Other superconductivity & superfluidity (conventional/phonon-mediated & new superconductors, vortices, SC films & devices incl. qubit/resonator materials, applied SC, superfluid He)",
        "patterns": [
            r"\bsuperconduct",
            r"\bmeissner|\bcooper pairs?|" + cs(r"\bBCS\b") + r"|\bbardeen-cooper|\babrikosov|\bpearl vort|\bflux(?:[- ]flow| pinning| creep)|\bvortex (?:pinning|lattice|matter|dynamics|core)|\bkinetic inductance|\bsuperfluid (?:stiffness|density)",
            # v2: other pairing condensates (superfluid 3He/4He, atomic Fermi superfluids)
            r"\bsuperfluid(?:ity|s)?\b|\bhelium[- ][34]\b|" + cs(r"\b[34]He\b"),
            cs(L + r"(?:MgB2|Nb3Sn|Nb3Ge|NbN|NbTiN|NbTi|V3Si|K3C60|Rb3C60)" + R),
            # superconducting quantum-device materials (cross-listed in cond-mat.supr-con)
            r"\btransmons?\b|\bfluxonium|\bsuperconducting (?:qubit|resonator|circuit|quantum circuit)s?|\btwo-level systems?\b.{0,60}\b(?:qubit|resonator)",
        ],
        "exclude": [r"\bcolou?r superconduct|\bholographic superconduct|\bneutron stars?"],
    },
]


def has_evidence(regex, text, title):
    """Evidence rule (v2): the cluster pattern matches the TITLE, or it matches
    at least twice in "title. abstract". A single passing mention in the
    abstract ("... as in the cuprates") is not enough.
    With title == text (no separate title given) one match suffices."""
    if regex.search(title):
        return True
    first = regex.search(text)
    if first is None:
        return False
    return regex.search(text, first.end()) is not None


def classify(text, title=None):
    """Multi-label: all cluster keys whose patterns match normalized `text`.

    A cluster matches when its patterns pass has_evidence() (title hit, or
    at least two hits in `text`), or when one of its title-only patterns
    matches the title. `title` must be the normalized title; if it is None,
    `text` is used as the title (then a single hit anywhere suffices).
    Residual (fallback) clusters are only tried when nothing else matched,
    and at most one of them is assigned.
    """
    if title is None:
        title = text
    keys = []
    for cluster in _CLUSTERS_COMPILED:
        if cluster["residual"] and keys:
            break  # residual clusters come last and only fill empty slots
        matched = has_evidence(cluster["pattern"], text, title)
        if not matched and cluster["title_pattern"] is not None:
            matched = cluster["title_pattern"].search(title) is not None
        if not matched:
            continue
        if cluster["exclude"] is not None and cluster["exclude"].search(text):
            continue
        keys.append(cluster["key"])
    return keys


def primary_cluster(text, title=None):
    """First matching cluster in CLUSTERS order (most specific first), or None."""
    keys = classify(text, title)
    if keys:
        return keys[0]
    return None

CLUSTER_KEYS = [cluster["key"] for cluster in CLUSTERS]
CLUSTER_LABELS = dict((cluster["key"], cluster["label"]) for cluster in CLUSTERS)
RESIDUAL_CLUSTER_KEYS = [cluster["key"] for cluster in CLUSTERS if cluster.get("residual")]


# ---------------------------------------------------------------------------
# Methods (Q4). key -> {"kind": experimental|computational, "label", "pattern"}
# Patterns are case-insensitive; acronyms wrapped in cs().
# ---------------------------------------------------------------------------

METHODS = {
    "arpes": {
        "kind": "experimental", "label": "ARPES / photoemission",
        "pattern": cs(r"\b(?:tr-?|nano-?|spin-?|micro-?)?ARPES\b|\bXPS\b|\bHAXPES\b") + r"|\bangle[- ]resolved photo-?(?:emission|electron)|\bphotoemission spectroscop",
    },
    "stm_sts": {
        "kind": "experimental", "label": "STM / STS / QPI",
        "pattern": cs(r"\b(?:SI-|SP-)?STM\b|\bSTS\b|\bQPI\b|\bAFM\b microscop") + r"|\bscanning tunnel+ing|\bquasiparticle interference|\bspectroscopic imaging|\bscanning (?:probe|single-electron transistor)|\bspin-polarized STM",
    },
    "neutron_scattering": {
        "kind": "experimental", "label": "Neutron scattering",
        "pattern": r"\bneutron (?:scattering|diffraction|spectroscop|spin[- ]echo|reflectometry|powder)|\binelastic neutron|\bpolari[sz]ed neutron|\bsmall[- ]angle neutron|" + cs(r"\bSANS\b"),
    },
    "rixs_resonant_xray": {
        "kind": "experimental", "label": "RIXS / resonant & soft x-ray spectroscopy",
        "pattern": cs(r"\bRIXS\b|\bREXS\b|\bRXS\b|\bXMCD\b|\bXMLD\b|\bXAS\b|\bXANES\b|\bEXAFS\b") + r"|\bresonant (?:inelastic |elastic |soft )?x-ray|\bx-ray absorption|\bx-ray magnetic (?:circular|linear) dichroism",
    },
    "musr": {
        "kind": "experimental", "label": "muSR",
        "pattern": cs(r"\b[μ]SR\b|\bmuSR\b|μ\+SR") + r"|\bmuon[- ]spin (?:rotation|relaxation|resonance|spectroscop)|\bmuon spectroscop",
    },
    "nmr_nqr": {
        "kind": "experimental", "label": "NMR / NQR",
        "pattern": cs(r"\bNMR\b|\bNQR\b") + r"|\bnuclear magnetic resonance|\bnuclear quadrupole|\bknight shift|\bspin[- ]lattice relaxation rate",
    },
    "magnetotransport_hall": {
        "kind": "experimental", "label": "Magnetotransport / Hall / resistivity",
        "pattern": r"\bmagneto-?transport|\bmagneto-?resistance|\bhall (?:effect|resistance|resistivity|conductivity|coefficient|measurement|response|signal|bar|angle|plateau)|\banomalous hall|\bplanar hall|\bnernst|\bthermal hall|\bresistivity|\belectrical transport|\btransport (?:measurement|experiment|properties|evidence|signature)|\bcritical current|\bsupercurrent|\bnonreciprocal transport",
    },
    "quantum_oscillations": {
        "kind": "experimental", "label": "Quantum oscillations",
        "pattern": r"\bquantum oscillation|\bde haas|\bshubnikov|" + cs(r"\bSdH\b|\bdHvA\b") + r"|\blandau fan|\bfermi[- ]surface (?:mapping|topology from)",
    },
    "optical_raman_ir": {
        "kind": "experimental", "label": "Optical / infrared / THz / Raman / magneto-optics",
        "pattern": r"\braman|\binfrared|\bterahertz|" + cs(r"\bTHz\b|\bMOKE\b|\bSHG\b|\bFTIR\b|\bPL\b") + r"|\boptical (?:conductivity|spectroscop|reflectivity|absorption|response|transmission|measurement)|\bphotoluminescence|\bellipsometr|\bmagneto-?optic|\bkerr (?:rotation|effect|microscop)|\bsecond[- ]harmonic generation|\breflectance (?:spectroscop|contrast)|\bnano-?(?:imaging|infrared|IR)\b|\bs-SNOM",
    },
    "ultrafast_pump_probe": {
        "kind": "experimental", "label": "Ultrafast pump-probe / time-resolved",
        "pattern": r"\bpump[- ]probe|\bultrafast|\btime[- ]resolved|\bfemtosecond|\battosecond|" + cs(r"\btr-?ARPES\b|\btr-?XRD\b|\bUED\b|\bXFEL\b") + r"|\bultrafast electron diffraction|\bfree[- ]electron laser|\bcoherent phonon",
    },
    "thermodynamics_specific_heat": {
        "kind": "experimental", "label": "Specific heat / magnetization / thermodynamics",
        "pattern": r"\bspecific heat|\bheat capacity|\bthermal expansion|\bmagnetostriction|\bmagneti[sz]ation (?:measurement|data|curve)|\bmagnetic susceptibility|\bthermal conductivity|\bcalorimetr|\bthermodynamic (?:measurement|evidence|probe|signature)|\belastocaloric|\bdilatometr|\btorque magnetometr|" + cs(r"\bSQUID magnetometr"),
    },
    "diffraction_structure": {
        "kind": "experimental", "label": "X-ray / electron diffraction & electron microscopy",
        "pattern": r"\bx-ray (?:diffraction|scattering|crystallograph|diffuse)|" + cs(r"\bXRD\b|\bLEED\b|\bRHEED\b|\b(?:4D-)?STEM\b|\bTEM\b|\bHRTEM\b|\bEELS\b|\bPDF\b analysis") + r"|\belectron (?:diffraction|microscop|energy[- ]loss)|\bsingle[- ]crystal diffraction|\bsynchrotron (?:x-ray|diffraction|radiation)|\bdiffuse scattering|\bpair distribution function|\bcrystal structure (?:determin|refine|solution)|\brietveld",
    },
    "high_pressure_dac": {
        "kind": "experimental", "label": "High pressure / diamond anvil cell",
        "pattern": r"\bhigh[- ]pressure|\bdiamond[- ]anvil|" + cs(r"\bDACs?\b|\bGPa\b") + r"|\bunder (?:hydrostatic |uniaxial )?pressure|\bhydrostatic pressure|\bpressure[- ](?:induced|tuned|dependent|driven)|\buniaxial (?:pressure|stress|strain)|\bmegabar|\bpiston[- ]cylinder",
    },
    "thin_film_growth_mbe": {
        "kind": "experimental", "label": "Thin-film growth (MBE, PLD, CVD, sputtering)",
        "pattern": r"\bmolecular[- ]beam epitax|" + cs(r"\bMBE\b|\bPLD\b|\bCVD\b|\bALD\b|\bMOCVD\b") + r"|\bpulsed[- ]laser deposit|\bchemical vapou?r deposit|\bthin[- ]films?\b|\bepitax|\bsputter|\bfilm growth|\bheterostructure growth|\bfreestanding (?:membrane|film)|\batomic layer deposit",
    },
    "nv_quantum_sensing": {
        "kind": "experimental", "label": "NV-center / quantum sensing / scanning SQUID magnetometry",
        "pattern": r"\bnitrogen[- ]vacanc|" + cs(r"\bNV\b(?:[- ]center|[- ]centre| magnetometr| sensor| spin)|\bNV[- ]?centers?\b|\bNV magnetometr|\bSQUID[- ]on[- ]tip|\bscanning SQUID") + r"|\bquantum sens|\bdiamond (?:magnetometr|quantum sensor)|\bscanning magnetometr|\bspin qubit sensor|\bwide-field magnetic imaging",
    },
    "dft_first_principles": {
        "kind": "computational", "label": "DFT / first-principles",
        "pattern": r"\bfirst[- ]principles?|\bdensity[- ]functional theory|\bab[- ]initio|" + cs(r"\bDFT\b|\bVASP\b|\bGGA\b|\bPBE\b|\bLDA\b|\bQuantum ESPRESSO\b|\bDFT\+U\b|\bLDA\+U\b|\bGGA\+U\b") + r"|\belectronic structure calculation|\bband[- ]structure calculation",
    },
    "dmft": {
        "kind": "computational", "label": "DMFT / DFT+DMFT / cluster DMFT",
        "pattern": cs(r"\b(?:DFT\+|LDA\+|GW\+|c|C-|cluster )?DMFT\b|\bDCA\b|\bEDMFT\b") + r"|\bdynamical mean[- ]field|\bdynamical cluster approximation",
    },
    "qmc": {
        "kind": "computational", "label": "Quantum Monte Carlo",
        "pattern": r"\bquantum monte carlo|" + cs(r"\b(?:D|AF|V|S|P|CT-|CT)?QMC\b") + r"|\bdeterminant(?:al|al quantum)? monte carlo|\bsign problem|\bstochastic series expansion|\bpath[- ]integral monte carlo|\bdiagrammatic monte carlo|\bcontinuous[- ]time (?:quantum )?monte carlo",
    },
    "dmrg_tensor_networks": {
        "kind": "computational", "label": "DMRG / tensor networks",
        "pattern": cs(r"\b(?:i)?DMRG\b|\b(?:i)?PEPS\b|\bMPS\b|\bTEBD\b|\bVUMPS\b|\bMERA\b|\bTDVP\b|\bPEPO\b|\bMPO\b") + r"|\bdensity[- ]matrix renormali[sz]ation|\btensor[- ]network|\bmatrix[- ]product (?:state|operator)|\bprojected entangled[- ]pair",
    },
    "exact_diagonalization": {
        "kind": "computational", "label": "Exact diagonalization",
        "pattern": r"\bexact(?:ly)?[- ]diagonali[sz]|\blanczos|" + cs(r"\bED\b (?:calculation|study|simulation|results)"),
    },
    "hartree_fock_mean_field": {
        "kind": "computational", "label": "Hartree-Fock / mean field / RPA / BdG",
        "pattern": r"\bhartree[- ]fock|(?<!dynamical )(?<!dynamic )\bmean[- ]field|\brandom[- ]phase approximation|" + cs(r"\bRPA\b|\bBdG\b|\bHF\b (?:calculation|study|ground state)|\bSCHF\b") + r"|\bbogoliubov[- ]de[- ]gennes|\bginzburg[- ]landau|\bparton (?:mean|construction)|\bslave[- ](?:boson|spin|rotor|particle)|\bfunctional renormali[sz]ation|" + cs(r"\bFRG\b") + r"|\bparquet",
    },
    "tight_binding_continuum": {
        "kind": "computational", "label": "Tight-binding / Wannier / continuum & effective models",
        "pattern": r"\btight[- ]binding|\bwannier|\bcontinuum model|\bbistritzer|\bk[·.]p\b|\bk dot p\b|\blow[- ]energy (?:effective )?(?:model|hamiltonian|theory)|\beffective (?:model|hamiltonian|lattice model|field theory)|\bminimal model|\bmodel hamiltonian|\bspin[- ]wave theory|\blinear spin[- ]wave|\bkitaev model|\bhaldane model",
    },
    "machine_learning": {
        "kind": "computational", "label": "Machine learning / neural networks",
        "pattern": r"\bmachine[- ]learn|\bneural[- ]network|\bdeep[- ]learn|\bartificial intelligence|" + cs(r"\bAI\b|\bLLMs?\b|\bGNNs?\b|\bNQS\b|\bMLIPs?\b|\bMLFF\b") + r"|\blarge language model|\bgraph neural|\bgenerative (?:model|AI)|\bdiffusion model|\btransformer[- ](?:based|model|architecture|network)|\bneural (?:quantum state|operator)|\bmachine-learned (?:interatomic |force)|\binteratomic potential|\bbayesian optimi[sz]ation|\bactive learning",
    },
    "gw_beyond_dft": {
        "kind": "computational", "label": "GW / BSE / hybrid functionals / quantum chemistry (beyond DFT)",
        "pattern": cs(r"(?<!\d )(?<!\d)\bGW\b(?! scale)|\bG0W0\b|\bQSGW\b|\bBSE\b|\bHSE(?:06)?\b|\bCCSD|\bCASSCF\b|\bRPA correlation") + r"|\bbethe[- ]salpeter|\bhybrid functional|\bquasiparticle self-consistent|\bcoupled[- ]cluster|\bmany[- ]body perturbation theory|\bembedding (?:theory|method)|\bquantum chemistry calculation",
    },
    "phonon_electron_phonon": {
        "kind": "computational", "label": "Phonons / electron-phonon / Eliashberg",
        "pattern": r"\belectron[- ]phonon|\beliashberg|\bphonon (?:dispersion|spectr|calculation|band|mode|softening|instabilit|mediated)|" + cs(r"\bDFPT\b|\bEPW\b|\bSSCHA\b") + r"|\bdensity[- ]functional perturbation|\bmcmillan|\ballen[- ]dynes|\banharmonic|\bself-consistent harmonic|\bstochastic self-consistent",
    },
}


def find_methods(text):
    """Method keys whose pattern matches normalized `text`."""
    return [key for key, regex in _METHODS_COMPILED if regex.search(text)]


METHOD_KINDS = dict((key, spec["kind"]) for key, spec in METHODS.items())


# ---------------------------------------------------------------------------
# Material families (Q3). Compiled CASE-SENSITIVE; ci() pieces insensitive.
# ---------------------------------------------------------------------------

MATERIAL_FAMILIES = {
    "cuprates": ci(r"\bcuprates?\b") + r"|" + L + r"(?:REBCO|ReBCO|GdBCO|EuBCO|SmBCO|NdBCO|DyBCO|YBCO|LSCO|LBCO|NCCO|PCCO|BSCCO|Bi-?22[01][12]|Bi-?2223|Hg-?12[01][1-3]|Tl-?2201)" + R + r"|Ba2Cu3O|Sr2Ca\d?Cu\d?O|Ba2Ca\d?Cu\d?O|YBa2Cu3O|Bi2Sr2CaCu2O|Bi2Sr2CuO|Bi2Sr2Ca2Cu3O|HgBa2|La2-xSrxCuO4|La2-xBaxCuO4|Nd2-xCexCuO4|Pr2-xCexCuO4|La2CuO4|CuO2[- ]?plane",
    "nickelates_bilayer_trilayer_rp": r"Ni2O7|Ni3O10|Ni3O11|" + ci(r"\b(?:bilayer|trilayer|ruddlesden[- ]popper) nickelate"),
    "nickelates_infinite_layer": r"NiO2" + R + r"|Ni5O12|Ni4O10|" + ci(r"\binfinite[- ]layer nickel|\bsquare[- ]planar nickelate"),
    "iron_pnictides_chalcogenides": L + r"(?:FeSe|FeTe|FeS)(?![a-z])|Fe\(Te,\s?Se\)|Fe\(Se,\s?Te\)|Fe2As2|FeAsO|LiFeAs|NaFeAs|Fe4As4|Fe2Se2|FeAs" + R + r"|" + ci(r"\biron[- ](?:pnictide|chalcogenide|selenide|arsenide|based superconduct)"),
    "av3sb5_kagome": r"V3Sb5|" + ci(r"\bAV3Sb5"),
    "other_kagome_metals": r"V6Sn6|Mn6Sn6|Cr3Sb5|Ti3Bi5|Co3Sn2S2|Fe3Sn2|Mn3Sn" + R + r"|" + L + r"(?:FeGe|CoSn|Ni3In|Fe3Ge|YCr6Ge6)" + R,
    "graphene_multilayers": ci(r"\bgraphene\b|\bgraphite\b") + r"|\b(?:MA)?TBG\b|\bTDBG\b",
    "tmds": L + r"(?:(?:1T'?-|2H-|3R-|Td-|t)?(?:MoTe2|WSe2|MoS2|WS2|MoSe2|WTe2|NbSe2|NbS2|TaS2|TaSe2|TiSe2|PtSe2|ZrSe2|HfSe2|VSe2|ReS2))" + R + r"|" + ci(r"\btransition[- ]metal dichalcogenide") + r"|\bTMDs?\b|\bTMDCs?\b",
    "hbn": r"\bhBN\b|\bh-BN\b|" + ci(r"\bhexagonal boron nitride"),
    "mnbi2te4_bi2se3_tetradymites": L + r"(?:MnBi2Te4|MnBi4Te7|MnSb2Te4|Bi2Se3|Bi2Te3|Sb2Te3|Bi2Te2Se|BiSbTeSe2)" + R + r"|\(Bi,\s?Sb\)2Te3|\(Bi1-xSbx\)2Te3",
    "altermagnet_candidates": L + r"(?:RuO2|MnTe|CrSb|Mn5Si3|KV2Se2O|MnF2|FeF2|CoF2|V2Te2O|V2Se2O|Fe2O3|CrO2|LaMnO3|MnSe2|FeSb2|Mn5Ge3|CoNb4Se8|NiS)" + R + r"|α-MnTe",
    "kitaev_materials": r"RuCl3|Na2IrO3|Li2IrO3|H3LiIr2O6|Ag3LiIr2O6|Cu2IrO3|Na2Co2TeO6|Na3Co2SbO6|Co2\(AsO4\)2|Co2\(PO4\)2|CoTiO3|" + ci(r"\bkitaev materials?|\bhoneycomb cobaltate|\bhoneycomb iridate"),
    "ute2_heavy_fermion_f_electron": L + r"(?:UTe2|CeRh2As2|CeCoIn5|CeRhIn5|CeIrIn5|YbRh2Si2|URu2Si2|UPt3|UBe13|CeCu2Si2|UCoGe|URhGe|UGe2|CeCu6|CePd2Si2|CeSb2|YbAl3|YbB12|SmB6|CeAl3|Ce3Bi4Pt3|CeSiI|UPd2Al3|UNi2Al3|CeRu2Si2|CeAgBi2|YbCu2Si2|USbTe|UPd2Si2|CeRhSn|CeIn3)" + R,
    "hydrides": L + r"(?:H3S|LaH10|LaH9|YH6|YH9|YH4|CaH6|CeH9|CeH10|ThH10|LaBeH8|LaB2H8|LuH3|Lu-H-N|MgIrH6|LaSc2H24|\(La,\s?Ce\)H9|\(La,\s?Y\)H10|YCeH\d+|LaCeH\d+)" + R + r"|" + ci(r"\bsuperhydride|\bclathrate hydride|\bternary hydride|\blanthanum hydride|\byttrium hydride|\bsulfur hydride|\blutetium hydride|\bcalcium hydride superconduct"),
    "vdw_magnets": L + r"(?:CrI3|CrBr3|CrCl3|CrSBr|Fe3GeTe2|Fe3GaTe2|Fe4GeTe2|Fe5GeTe2|FexGeTe2|Fe3-xGeTe2|NiPS3|FePS3|MnPS3|CoPS3|NiPSe3|MnPSe3|CrPS4|Cr2Ge2Te6|CrGeTe3|VI3|NiI2|CrTe2|Cr2Te3|FeCl2|CrSiTe3|Cr2Si2Te6|MnBi2Te4)" + R,
    "ruthenates": L + r"(?:Sr2RuO4|Sr3Ru2O7|Ca2RuO4|SrRuO3|Ca3Ru2O7|CaRuO3)" + R + r"|" + ci(r"\bruthenates?\b"),
    "srtio3_ktao3_oxide_interfaces": L + r"(?:SrTiO3|LaAlO3|KTaO3|EuO|LaTiO3|GdTiO3)" + R + r"|LaAlO3/SrTiO3|" + ci(r"\boxide interface|\boxide heterostructure"),
    "magnetic_topological_eu_compounds": L + r"(?:EuCd2As2|EuIn2As2|EuSn2As2|EuCd2P2|EuZn2As2|EuMnBi2|EuAl4|EuB6|EuSn2P2|EuCuAs|EuAgAs|EuTiO3|GdPtBi|Mn3Ge|Co2MnGa|Fe3Sn|MnSi2Te4)" + R,
    "weyl_dirac_semimetals": L + r"(?:TaAs|NbAs|TaP|NbP|Cd3As2|Na3Bi|ZrTe5|HfTe5|PtTe2|PdTe2|CoSi|RhSi|ZrSiS|ZrSiSe|PtBi2|PtSn4|MoP|WP2|MoTe2|WTe2|TaIrTe4|NbIrTe4|Bi4Br4|Bi4I4|SnTe|Pb1-xSnxTe|LaAlGe|PrAlGe|CeAlGe|NdAlSi)" + R,
    "b20_chiral_magnets_skyrmion_hosts": L + r"(?:MnSi|MnGe|Cu2OSeO3|GaV4S8|GaV4Se8|Fe1-xCoxSi|FeCoSi|Co8Zn8Mn4|Co8Zn10Mn2|Gd2PdSi3|Gd3Ru4Al12|GdRu2Si2|EuPtSi|Mn1.4PtSn|MnPtSn)" + R,
    "iridates_mott_oxides": L + r"(?:Sr2IrO4|Sr3Ir2O7|Nd2Ir2O7|Pr2Ir2O7|Eu2Ir2O7|Y2Ir2O7|VO2|V2O3|NiS2|NdNiO3|SmNiO3|LaNiO3|PrNiO3|Ca2RuO4|NiO|MnO|CoO|FeO|LaMnO3|La1-xSrxMnO3|LaVO3|YVO3|YTiO3|Ti2O3|1T-TaS2)" + R + r"|" + ci(r"\biridates?\b|\bmanganites?\b|\brare[- ]earth nickelate"),
    "frustrated_rare_earth_and_triangular": L + r"(?:YbMgGaO4|NaYbSe2|NaYbO2|NaYbS2|KYbSe2|CsYbSe2|Ce2Zr2O7|Ce2Sn2O7|Ce2Hf2O7|Yb2Ti2O7|Dy2Ti2O7|Ho2Ti2O7|Tb2Ti2O7|Er2Ti2O7|Pr2Zr2O7|ZnCu3\(OH\)6Cl2|Cu3Zn\(OH\)6Cl2|Ba3CoSb2O9|Ba3CuSb2O9|SrCu2\(BO3\)2|KCeS2|CsCeSe2|Ca10Cr7O28|Cs2CuCl4|Cs2CuBr4|NaCaNi2F7|CePdAl|K2Ni2\(SO4\)3|Na2BaCo\(PO4\)2|YCu3\(OH\)6)" + R + r"|" + ci(r"\bherbertsmithite|\bpyrochlore"),
    "excitonic_insulator_cdw_materials": L + r"(?:Ta2NiSe5|Ta2NiS5|1T-TiSe2|TiSe2|LaTe3|ErTe3|CeTe3|TbTe3|GdTe3|RTe3|NbSe3|TaTe4|K0.3MoO3|BaNi2As2|Ta2Pd3Te5|InAs/GaSb|InAs/GaInSb)" + R,
    "semiconductor_2deg_and_qw": L + r"(?:InAs|InSb|GaAs|AlGaAs|GaN|HgTe|CdTe|ZnO)" + R + r"|Ge/SiGe|" + ci(r"\bquantum wells?\b|\bnanowires?\b"),
}


def find_families(text):
    """Material-family keys whose pattern matches normalized `text`."""
    return [key for key, regex in _FAMILIES_COMPILED if regex.search(text)]


def classify_record(record):
    """All taxonomy labels for one corpus record (dict), as a plain dict.

    Out-of-scope records get empty cluster/method/family lists and
    primary_cluster None, so counts are always restricted to the scope rule.
    """
    text = record_text(record)
    reason = scope_reason(record, text)
    labels = {
        "in_scope": reason is not None,
        "scope_reason": reason,
        "clusters": [],
        "primary_cluster": None,
        "methods": [],
        "families": [],
        "taxonomy_version": TAXONOMY_VERSION,
    }
    if reason is None:
        return labels
    clusters = classify(text, record_title(record))
    labels["clusters"] = clusters
    labels["primary_cluster"] = clusters[0] if clusters else None
    labels["methods"] = find_methods(text)
    labels["families"] = find_families(text)
    return labels


# ---------------------------------------------------------------------------
# Human-readable scope description
# ---------------------------------------------------------------------------

SCOPE_DESCRIPTION = (
    "Quantum-materials scope rule (taxonomy " + TAXONOMY_VERSION + "; the v1 rule plus one extra context veto). "
    "An arXiv record is IN SCOPE if its categories include "
    + " or ".join(SCOPE_ARXIV_CATEGORIES)
    + ", OR its normalized title+abstract matches any QM keyword group. "
    "Records from other servers are in scope only via the keyword groups. "
    "Keyword groups: topological phases (topological insulator/semimetal/superconductor/"
    "order/magnon/..., higher-order topology); moire & twisted layers (moire, twisted bilayer, "
    "magic angle, twist angle); correlated electrons (strongly correlated, Hubbard model, t-J, "
    "Hund's metal; NOT 'Hubbard U' DFT+U corrections); superconductivity; spin liquids/spinons; "
    "frustrated magnetism (Kitaev, spin ice, pyrochlore magnets, quantum magnets); altermagnets; "
    "kagome; Weyl/Dirac/nodal-line semimetals; heavy fermion/Kondo; charge/spin/pair density "
    "waves and charge order; quantum (anomalous/fractional) Hall and Chern insulators; Majorana/"
    "parafermions; flat bands; excitonic insulators/interlayer excitons; van der Waals/2D "
    "magnets (CrI3, CrSBr, Fe3GeTe2, ...); multiferroics/magnetoelectrics; Mott (not "
    "Mott-Schottky/Mott-Gurney); quantum criticality; electronic nematicity; strange metals/"
    "Planckian/non-Fermi liquids; skyrmions/hopfions/merons; Berry curvature/quantum geometry; "
    "quantum spin Hall; Wigner crystals; Luttinger liquids/anyons/fractionalization; and "
    "named classes (cuprate, nickelate, iron pnictide/chalcogenide, iridate, ruthenate). "
    "Context vetoes drop a keyword when it only appears in an engineering/soft-matter sense: "
    "superconductivity in superconducting magnets/cables/qubits/resonators/SRF/SNSPDs, "
    "nematic in liquid crystals/active nematics, moire in moire-fringe metrology, and "
    "photonic flat bands; and (new in v2) 'topological' in classical-wave contexts (topological "
    "photonics/acoustics/mechanics, metamaterials, phononic crystals, topolectric circuits, "
    "topological lasers, topological data analysis/optimization)."
)


# ---------------------------------------------------------------------------
# Compilation (done once at import)
# ---------------------------------------------------------------------------

def _join(patterns):
    return "|".join("(?:" + p + ")" for p in patterns)


_SCOPE_COMPILED = [(name, re.compile(p, re.IGNORECASE)) for name, p in QM_SCOPE.items()]
_SCOPE_VETO_COMPILED = dict((name, re.compile(p, re.IGNORECASE)) for name, p in SCOPE_CONTEXT_VETO.items())

def _compile_or_none(patterns):
    if not patterns:
        return None
    return re.compile(_join(patterns), re.IGNORECASE)


_CLUSTERS_COMPILED = []
for _cluster in CLUSTERS:
    _CLUSTERS_COMPILED.append({
        "key": _cluster["key"],
        "pattern": re.compile(_join(_cluster["patterns"]), re.IGNORECASE),
        "title_pattern": _compile_or_none(_cluster.get("title_patterns")),
        "residual": _cluster.get("residual", False),
        "exclude": _compile_or_none(_cluster["exclude"]),
    })

_METHODS_COMPILED = [(key, re.compile(spec["pattern"], re.IGNORECASE)) for key, spec in METHODS.items()]
_FAMILIES_COMPILED = [(key, re.compile(p)) for key, p in MATERIAL_FAMILIES.items()]
