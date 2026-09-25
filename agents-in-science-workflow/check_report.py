"""Independent checker for agents-in-science-workflow/findings.html.

The checker reads only the HTML page and the network. It does not import
report/build_report.py and does not read refs.json or catalog.json, so it
checks what a reader of the page actually gets.

HTML contract
-------------
Question sections
    Six sections <section class="question" id="q1"> ... id="q6". Each has an
    <h2> heading and exactly one <p class="answer"> (the one-line answer).
    A citation is <a class="cite" href="#ref-N">. The citations of a section
    are all such links inside it, nested subsections included. Each section
    must cite at least 3 distinct references. (The printed heading drops a
    leading "Q1"/"Q1:" so the line does not read "Q1 Q1 ...".)
Q1 taxonomy
    #q1 contains <table id="taxonomy">. Each placed system is
        <span class="sys" data-stage="STAGE" data-autonomy="LEVEL">Name</span>
    STAGE is a stage slug or the full stage name (case does not matter):
        literature   Literature & ideation
        hypothesis   Hypothesis generation
        experiment   Experiment design & self-driving labs
        analysis     Data analysis & simulation
        writing      Writing & review
    LEVEL is any non-empty autonomy label. Systems are counted by distinct
    name: at least 25 must be placed, covering all 5 stages.
Q2 structure
    #q2 contains elements (normally <div>) with id="q2-established",
    id="q2-claims" and id="q2-benchmarks"; each holds at least one citation.
Q6 discussion prompts
    #q6 contains <ol id="discussion-prompts"> with 6 to 10 <li class="prompt">.
    Each prompt holds at least one citation and at least one link to a Q1-Q5
    section: href="#q1" ... "#q5", or a sub-anchor starting with #q1 ... #q5
    such as "#q2-claims". The link target id must exist in the page.
Appendix
    <section id="appendix"> contains
        <section id="catalog"> with <table id="catalog-table"> (one <tr> with
            <td> cells per system; at least 25 rows),
        <section id="glossary"> with a <dl> of <dt>/<dd> terms,
        <section id="method-notes">.
References
    <section id="references"> contains <ol class="references"> whose items are
        <li id="ref-N" data-kind="doi|arxiv|url" data-id="...">
    with a <span class="ref-title">, numbered ref-1 ... ref-N in order.
    data-id is a bare DOI, a bare arXiv ID or a full URL, and the item holds a
    link to it (https://doi.org/ID, https://arxiv.org/abs/ID, or the URL).
    At least 30 references; every one cited outside the list; no link to a
    #ref-N that has no list item.
Self-contained
    Nothing is loaded from outside the file: no <script src>, <link href>,
    <img src/srcset>, <iframe src>, <source src/srcset>, <video src/poster>,
    <audio src>, <track src>, <embed src>, <object data>, <input type=image
    src>, SVG <image>/<use> href, or CSS url(...)/@import in <style> blocks or
    style="" attributes. data: URIs and #fragments are fine, and so are
    outbound <a href> links.

Reference resolution (skipped with --offline; nothing is cached between runs)
    doi    Crossref https://api.crossref.org/works/{doi}; if Crossref has no
           record, https://doi.org/{doi} with CSL-JSON content negotiation
           (covers DataCite DOIs). The fetched title must match.
    arxiv  arXiv API id_list query, up to 50 IDs per request. The entry must
           exist (not an error entry) and its title must match.
    url    GET must end with HTTP 200-399 after redirects.
    Titles are normalized (HTML-unescape, strip tags, Unicode NFKD without
    accents, lowercase, non-alphanumerics to spaces, collapsed whitespace).
    They match if equal, or difflib ratio >= 0.92, or one is a word-boundary
    prefix of the other and the shorter has at least 5 words.

Usage (from the repository root, or from inside agents-in-science-workflow/)
    python agents-in-science-workflow/check_report.py [PATH] [--offline]
Exit code 0 if OVERALL is PASS, 1 otherwise. Set the environment variable
CONTACT_EMAIL to add mailto= to Crossref requests (Crossref's polite pool).
"""
import argparse
import difflib
import html
import http.client
import json
import os
import re
import socket
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ElementTree
from html.parser import HTMLParser

CAMPAIGN_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CAMPAIGN_DIR)
DEFAULT_REPORT_PATH = os.path.join(CAMPAIGN_DIR, "findings.html")

# ---- Pass thresholds ------------------------------------------------------
MIN_CITES_PER_QUESTION = 3
MIN_TAXONOMY_SYSTEMS = 25
MIN_CATALOG_ROWS = 25
MIN_PROMPTS = 6
MAX_PROMPTS = 10
MIN_REFERENCES = 30

# Stage slug -> full stage name. data-stage may use either form.
STAGES = {
    "literature": "Literature & ideation",
    "hypothesis": "Hypothesis generation",
    "experiment": "Experiment design & self-driving labs",
    "analysis": "Data analysis & simulation",
    "writing": "Writing & review",
}
STAGE_LOOKUP = {}
for _slug, _name in STAGES.items():
    STAGE_LOOKUP[_slug] = _slug
    STAGE_LOOKUP[_name.lower()] = _slug

Q2_PARTS = [("established", "q2-established"), ("claims", "q2-claims"), ("benchmarks", "q2-benchmarks")]
REFERENCE_KINDS = ("doi", "arxiv", "url")

# ---- Network settings -----------------------------------------------------
USER_AGENT = "literature-research-check/1.0 (+https://github.com/carbonscott/literature-research)"
REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
BACKOFF_SECONDS = [2, 4, 8]
MAX_RETRY_AFTER_SECONDS = 60
# Minimum gap between the end of one request and the start of the next, per host.
MIN_GAP_SECONDS = {"export.arxiv.org": 3.1, "api.crossref.org": 0.3}
DEFAULT_MIN_GAP_SECONDS = 0.5
ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_BATCH_SIZE = 50
ATOM = "{http://www.w3.org/2005/Atom}"
URL_READ_LIMIT_BYTES = 65536
# Characters left as they are when percent-encoding a URL (urllib only sends ASCII).
URL_SAFE_CHARACTERS = ":/?#[]@!$&'()*+,;=%~"

TITLE_RATIO_THRESHOLD = 0.92
PREFIX_MIN_WORDS = 5

REF_TARGET = re.compile(r"^#ref-(\d+)$")
REF_ITEM_ID = re.compile(r"^ref-(\d+)$")
QUESTION_LINK = re.compile(r"^#(q[1-5](?![0-9]).*)$")
HTML_TAG = re.compile(r"<[^>]*>")
NON_ALPHANUMERIC = re.compile(r"[\W_]+")
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE | re.DOTALL)
CSS_IMPORT_STRING = re.compile(r"@import\s+(['\"])(.*?)\1", re.IGNORECASE)
SRCSET_DESCRIPTOR = re.compile(r"^\d+(\.\d+)?[wx]$")


# ===========================================================================
# A small HTML tree built with html.parser
# ===========================================================================
VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
                 "meta", "param", "source", "track", "wbr"}
NO_TEXT_ELEMENTS = {"script", "style"}


class Element:
    """One HTML element: tag, attributes, parent and children (Elements or strings)."""

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = {name: (value if value is not None else "") for name, value in attrs}
        self.parent = parent
        self.children = []

    def get(self, name):
        """Attribute value, or "" if the attribute is absent."""
        return self.attrs.get(name, "")

    def has_class(self, class_name):
        return class_name in self.get("class").split()


class TreeBuilder(HTMLParser):
    """Builds an Element tree. End tags close the nearest open element with that tag."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("#document", [], None)
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        element = Element(tag, attrs, self.current)
        self.current.children.append(element)
        if tag not in VOID_ELEMENTS:
            self.current = element

    def handle_startendtag(self, tag, attrs):
        self.current.children.append(Element(tag, attrs, self.current))

    def handle_endtag(self, tag):
        node = self.current
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is not self.root:  # stray end tags are ignored
            self.current = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def parse_html(text):
    builder = TreeBuilder()
    builder.feed(text)
    builder.close()
    return builder.root


def iter_elements(node):
    """All elements below node, in document order."""
    for child in node.children:
        if isinstance(child, Element):
            yield child
            yield from iter_elements(child)


def find_all(node, tag=None, class_name=None):
    """Elements below node with the given tag and/or class."""
    if node is None:
        return []
    return [element for element in iter_elements(node)
            if (tag is None or element.tag == tag) and (class_name is None or element.has_class(class_name))]


def find_by_id(node, element_id):
    """First element below node with the given id, or None."""
    if node is None:
        return None
    for element in iter_elements(node):
        if element.get("id") == element_id:
            return element
    return None


def is_inside(element, ancestor):
    node = element.parent
    while node is not None:
        if node is ancestor:
            return True
        node = node.parent
    return False


def collapse_whitespace(text):
    return " ".join(text.split())


def text_of(node):
    """Visible text below node (no script/style), whitespace-collapsed."""
    pieces = []

    def collect(current):
        for child in current.children:
            if isinstance(child, str):
                pieces.append(child)
            elif child.tag not in NO_TEXT_ELEMENTS:
                collect(child)

    collect(node)
    return collapse_whitespace("".join(pieces))


def cite_numbers(node):
    """Reference numbers of all <a class="cite" href="#ref-N"> below node."""
    numbers = []
    for link in find_all(node, "a", "cite"):
        match = REF_TARGET.match(link.get("href").strip())
        if match:
            numbers.append(int(match.group(1)))
    return numbers


def verdict(passed):
    return "PASS" if passed else "FAIL"


def yes_no(flag):
    return "yes" if flag else "no"


# ===========================================================================
# Structural checks. Each returns (lines to print, passed).
# ===========================================================================
def check_question(root, number):
    """Heading, one-line answer and citations of one question section."""
    label = "Q%d" % number
    section = find_by_id(root, "q%d" % number)
    if section is None or section.tag != "section" or not section.has_class("question"):
        return ['%s MISSING: no <section class="question" id="q%d">  FAIL' % (label, number)], False

    passed = True
    headings = find_all(section, "h2")
    if headings:
        # Drop a leading "Q1", "Q1:" or "Q1 ·" so the line does not read "Q1 Q1 ...".
        heading = text_of(headings[0])
        heading = re.sub(r"^%s\b[\s.:·—–-]*" % label, "", heading) or heading
        lines = ["%s %s" % (label, heading)]
    else:
        lines = ["%s (no <h2> heading)  FAIL" % label]
        passed = False

    answers = find_all(section, "p", "answer")
    if len(answers) == 1:
        lines.append("  answer: " + text_of(answers[0]))
    else:
        lines.append('  answer: FAIL (found %d <p class="answer">, need exactly 1)' % len(answers))
        passed = False

    distinct = sorted(set(cite_numbers(section)))
    enough = len(distinct) >= MIN_CITES_PER_QUESTION
    lines.append("  cites: %s (%d distinct) %s (need >= %d)"
                 % (distinct, len(distinct), verdict(enough), MIN_CITES_PER_QUESTION))
    return lines, passed and enough


def check_taxonomy(root):
    """Systems placed in the Q1 taxonomy table, by stage and autonomy level."""
    table = find_by_id(find_by_id(root, "q1"), "taxonomy")
    notes = []
    names = set()
    stages = set()
    autonomy_levels = set()
    if table is None or table.tag != "table":
        notes.append('  no <table id="taxonomy"> inside #q1')
    else:
        for span in find_all(table, "span", "sys"):
            name = text_of(span)
            stage = STAGE_LOOKUP.get(collapse_whitespace(span.get("data-stage")).lower())
            autonomy = collapse_whitespace(span.get("data-autonomy"))
            if not name or stage is None or not autonomy:
                notes.append("  not placed: %r (data-stage=%r, data-autonomy=%r)"
                             % (name, span.get("data-stage"), span.get("data-autonomy")))
                continue
            names.add(name.lower())
            stages.add(stage)
            autonomy_levels.add(autonomy.lower())
    passed = len(names) >= MIN_TAXONOMY_SYSTEMS and len(stages) == len(STAGES)
    line = ("Q1 taxonomy: %d systems placed; stages covered %d/%d; autonomy levels used %d  %s (need >= %d systems, %d/%d stages)"
            % (len(names), len(stages), len(STAGES), len(autonomy_levels), verdict(passed),
               MIN_TAXONOMY_SYSTEMS, len(STAGES), len(STAGES)))
    return [line] + notes, passed


def check_q2_structure(root):
    """Q2 keeps established results, claims and benchmarks in separate cited blocks."""
    q2 = find_by_id(root, "q2")
    flags = []
    notes = []
    for label, part_id in Q2_PARTS:
        part = find_by_id(q2, part_id)
        has_cite = part is not None and bool(cite_numbers(part))
        if part is None:
            notes.append('  no id="%s" inside #q2' % part_id)
        elif not has_cite:
            notes.append("  #%s has no citation" % part_id)
        flags.append((label, has_cite))
    passed = all(flag for _, flag in flags)
    line = "Q2 structure: " + " ".join("%s=%s" % (label, yes_no(flag)) for label, flag in flags) + "  " + verdict(passed)
    return [line] + notes, passed


def check_catalog(root):
    """Rows of the appendix system catalog."""
    table = find_by_id(root, "catalog-table")
    rows = [row for row in find_all(table, "tr") if find_all(row, "td")]
    passed = len(rows) >= MIN_CATALOG_ROWS
    return ["catalog rows: %d  %s (need >= %d)" % (len(rows), verdict(passed), MIN_CATALOG_ROWS)], passed


def check_prompts(root):
    """Q6 discussion prompts, each tied to a citation and to a Q1-Q5 section."""
    ids_in_page = {element.get("id") for element in iter_elements(root) if element.get("id")}
    prompt_list = find_by_id(find_by_id(root, "q6"), "discussion-prompts")
    notes = []
    prompts = []
    if prompt_list is None or prompt_list.tag != "ol":
        notes.append('  no <ol id="discussion-prompts"> inside #q6')
    else:
        prompts = find_all(prompt_list, "li", "prompt")

    tied = 0
    for index, prompt in enumerate(prompts, start=1):
        problems = []
        if not cite_numbers(prompt):
            problems.append("no citation")
        question_targets = []
        for link in find_all(prompt, "a"):
            match = QUESTION_LINK.match(link.get("href").strip())
            if match:
                question_targets.append(match.group(1))
        if not question_targets:
            problems.append("no link to #q1-#q5")
        elif not any(target in ids_in_page for target in question_targets):
            problems.append("links to missing ids: " + ", ".join("#" + target for target in question_targets))
        if problems:
            notes.append("  prompt %d: %s" % (index, "; ".join(problems)))
        else:
            tied += 1
    count = len(prompts)
    passed = MIN_PROMPTS <= count <= MAX_PROMPTS and tied == count
    line = ("discussion prompts: %d (each tied to Q1-Q5 evidence: %d/%d)  %s (need %d-%d, all tied)"
            % (count, tied, count, verdict(passed), MIN_PROMPTS, MAX_PROMPTS))
    return [line] + notes, passed


def check_appendix(root):
    """Catalog, glossary and method-notes sections inside the appendix."""
    appendix = find_by_id(root, "appendix")
    notes = [] if appendix is not None else ['  no <section id="appendix">']

    def appendix_section(section_id):
        section = find_by_id(appendix, section_id)
        return section if section is not None and section.tag == "section" else None

    catalog = appendix_section("catalog")
    glossary = appendix_section("glossary")
    method_notes = appendix_section("method-notes")
    has_catalog = catalog is not None and find_by_id(catalog, "catalog-table") is not None
    has_glossary = glossary is not None and any(find_all(dl, "dt") for dl in find_all(glossary, "dl"))
    has_method_notes = method_notes is not None
    passed = has_catalog and has_glossary and has_method_notes
    line = ("appendix sections present: catalog=%s glossary=%s method-notes=%s  %s"
            % (yes_no(has_catalog), yes_no(has_glossary), yes_no(has_method_notes), verdict(passed)))
    return [line] + notes, passed


# ---- External resources ---------------------------------------------------
# Attributes that make the browser load something automatically.
RESOURCE_ATTRIBUTES = {
    "script": ["src"],
    "link": ["href"],
    "img": ["src", "srcset"],
    "iframe": ["src"],
    "source": ["src", "srcset"],
    "video": ["src", "poster"],
    "audio": ["src"],
    "track": ["src"],
    "embed": ["src"],
    "object": ["data"],
    "image": ["href", "xlink:href"],  # SVG
    "use": ["href", "xlink:href"],    # SVG
}


def is_external(url):
    """True unless the value is empty, a data: URI or a #fragment."""
    value = url.strip()
    return bool(value) and not value.lower().startswith("data:") and not value.startswith("#")


def srcset_urls(srcset):
    """URLs in a srcset value (width/density descriptors dropped)."""
    tokens = [token.strip(",") for token in srcset.split()]
    return [token for token in tokens if token and not SRCSET_DESCRIPTOR.match(token)]


def css_urls(css):
    """URLs referenced by url(...) and @import "..." in CSS text (comments ignored)."""
    css = CSS_COMMENT.sub(" ", css)
    urls = [match.group(2) for match in CSS_URL.finditer(css)]
    urls.extend(match.group(2) for match in CSS_IMPORT_STRING.finditer(css))
    return urls


def find_external_resources(root):
    """Descriptions of everything the page would load from outside the file."""
    found = []
    for element in iter_elements(root):
        attributes = list(RESOURCE_ATTRIBUTES.get(element.tag, []))
        if element.tag == "input" and element.get("type").lower() == "image":
            attributes.append("src")
        for attribute in attributes:
            value = element.get(attribute)
            urls = srcset_urls(value) if attribute == "srcset" else [value]
            for url in urls:
                if is_external(url):
                    found.append("<%s %s> %s" % (element.tag, attribute, url.strip()))
        if element.tag == "style":
            css_text = "".join(child for child in element.children if isinstance(child, str))
            for url in css_urls(css_text):
                if is_external(url):
                    found.append("<style> %s" % url.strip())
        if element.get("style"):
            for url in css_urls(element.get("style")):
                if is_external(url):
                    found.append('<%s style=""> %s' % (element.tag, url.strip()))
    return found


def check_external_resources(root):
    found = find_external_resources(root)
    lines = ["external resources loaded: %d" % len(found)] + ["  " + item for item in found]
    return lines, not found


# ===========================================================================
# Reference list
# ===========================================================================
def expected_link(kind, ref_id):
    """Where the list item's link should point for this data-kind / data-id."""
    if kind == "doi":
        return "https://doi.org/" + ref_id
    if kind == "arxiv":
        return "https://arxiv.org/abs/" + ref_id
    return ref_id


def reference_label(ref):
    """E.g. 'ref 12 doi:10.x/y', 'ref 3 arXiv:2304.05332' or 'ref 5 https://...'."""
    prefix = {"doi": "doi:", "arxiv": "arXiv:", "url": ""}.get(ref["kind"], ref["kind"] + ":")
    return "ref %s %s%s" % (ref["number"], prefix, ref["id"])


def reference_problem(ref):
    """A structural problem with one list item, or "" if there is none."""
    if ref["kind"] not in REFERENCE_KINDS:
        return "data-kind must be one of %s (got %r)" % (", ".join(REFERENCE_KINDS), ref["kind"])
    if not ref["id"]:
        return "missing data-id"
    if ref["kind"] == "url" and not ref["id"].lower().startswith(("http://", "https://")):
        return "data-id of a url reference must start with http:// or https://"
    if not ref["title"]:
        return 'missing or empty <span class="ref-title">'
    target = expected_link(ref["kind"], ref["id"]).lower()
    if not any(urllib.parse.unquote(href).strip().lower() == target for href in ref["links"]):
        return "no link to %s in the list item" % expected_link(ref["kind"], ref["id"])
    return ""


def read_reference_list(root):
    """Return (references, numbering_problems) from <section id="references">."""
    section = find_by_id(root, "references")
    if section is None:
        return [], ['no <section id="references">']
    lists = find_all(section, "ol", "references")
    if not lists:
        return [], ['no <ol class="references"> inside #references']

    items = [child for child in lists[0].children if isinstance(child, Element) and child.tag == "li"]
    references = []
    problems = []
    for position, item in enumerate(items, start=1):
        match = REF_ITEM_ID.match(item.get("id"))
        number = int(match.group(1)) if match else None
        if number != position:
            problems.append("numbering: item %d has id=%r (expected 'ref-%d')" % (position, item.get("id"), position))
        title_spans = find_all(item, "span", "ref-title")
        references.append({
            "number": number if number is not None else "?%d" % position,
            "kind": item.get("data-kind").strip().lower(),
            "id": item.get("data-id").strip(),
            "title": text_of(title_spans[0]) if title_spans else "",
            "links": [link.get("href") for link in find_all(item, "a") if link.get("href")],
        })
    return references, problems


# ===========================================================================
# Network
# ===========================================================================
class RedirectHandler(urllib.request.HTTPRedirectHandler):
    """Also follow HTTP 308 redirects, which urllib ignores before Python 3.11."""

    def http_error_308(self, request, response, code, message, headers):
        return self.http_error_302(request, response, 307, message, headers)


def parse_retry_after(value):
    """Seconds from a Retry-After header (0 if missing or not a number)."""
    try:
        return min(int(value), MAX_RETRY_AFTER_SECONDS)
    except (TypeError, ValueError):
        return 0


class HttpClient:
    """GET requests with a minimum gap per host, retries and backoff."""

    def __init__(self):
        self.opener = urllib.request.build_opener(RedirectHandler)
        self.last_request_end = {}

    def wait_for_host(self, host):
        gap = MIN_GAP_SECONDS.get(host, DEFAULT_MIN_GAP_SECONDS)
        last_end = self.last_request_end.get(host)
        if last_end is not None:
            remaining = gap - (time.monotonic() - last_end)
            if remaining > 0:
                time.sleep(remaining)

    def get(self, url, accept="*/*", max_bytes=None):
        """Return (status, body, error). status is None if no HTTP response arrived.

        Retries up to MAX_RETRIES times on 429, 5xx, timeouts, dropped connections
        and failed DNS lookups (socket.gaierror, which is often transient on shared
        clusters); other errors are returned at once.
        """
        url = urllib.parse.quote(url, safe=URL_SAFE_CHARACTERS)
        host = urllib.parse.urlsplit(url).netloc.lower()
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
        status, error = None, ""
        for attempt in range(MAX_RETRIES + 1):
            self.wait_for_host(host)
            retry_after = 0
            try:
                with self.opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                    body = response.read(max_bytes) if max_bytes else response.read()
                    return response.status, body, ""
            except urllib.error.HTTPError as http_error:
                http_error.close()
                status, error = http_error.code, "HTTP %d" % http_error.code
                if status != 429 and status < 500:
                    return status, b"", error
                retry_after = parse_retry_after(http_error.headers.get("Retry-After"))
            except urllib.error.URLError as url_error:
                if not isinstance(url_error.reason, (socket.timeout, TimeoutError, ConnectionError, socket.gaierror)):
                    return None, b"", "network error: %s" % url_error.reason
                status, error = None, "network error: %s" % url_error.reason
            except (socket.timeout, TimeoutError, ConnectionError, http.client.HTTPException) as network_error:
                status, error = None, "network error: %s" % (str(network_error) or type(network_error).__name__)
            except OSError as other_error:  # e.g. an SSL error while reading
                return None, b"", "network error: %s" % other_error
            finally:
                self.last_request_end[host] = time.monotonic()
            if attempt < MAX_RETRIES:
                time.sleep(max(BACKOFF_SECONDS[attempt], retry_after))
        return status, b"", "%s (after %d retries)" % (error, MAX_RETRIES)


def normalize_title(title):
    """Lowercase words only: no tags, entities, accents or punctuation."""
    text = HTML_TAG.sub("", html.unescape(title))
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = NON_ALPHANUMERIC.sub(" ", text.lower())
    return " ".join(text.split())


def titles_match(listed, fetched):
    listed_words = normalize_title(listed)
    fetched_words = normalize_title(fetched)
    if not listed_words or not fetched_words:
        return False
    if listed_words == fetched_words:
        return True
    if difflib.SequenceMatcher(None, listed_words, fetched_words).ratio() >= TITLE_RATIO_THRESHOLD:
        return True
    shorter, longer = sorted([listed_words, fetched_words], key=len)
    return len(shorter.split()) >= PREFIX_MIN_WORDS and longer.startswith(shorter + " ")


def compare_titles(listed, fetched_titles, source):
    """Return (resolved, reason) after comparing the listed title with fetched ones."""
    fetched_titles = [title for title in fetched_titles if title and title.strip()]
    if not fetched_titles:
        return False, "%s record has no title" % source
    if any(titles_match(listed, fetched) for fetched in fetched_titles):
        return True, ""
    shown = collapse_whitespace(HTML_TAG.sub("", html.unescape(fetched_titles[0])))
    return False, "title mismatch: listed '%s' vs fetched '%s' (%s)" % (listed, shown, source)


def as_title_list(value):
    """A CSL or Crossref title field (string or list) as a list of strings."""
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)] if value else []


def resolve_doi(client, doi, listed_title):
    """Crossref first; doi.org content negotiation if Crossref has no record."""
    quoted_doi = urllib.parse.quote(doi, safe="/")
    crossref_url = "https://api.crossref.org/works/" + quoted_doi
    contact_email = os.environ.get("CONTACT_EMAIL", "").strip()
    if contact_email:
        crossref_url += "?mailto=" + urllib.parse.quote(contact_email)
    status, body, error = client.get(crossref_url, accept="application/json")
    if status == 200:
        try:
            message = json.loads(body.decode("utf-8"))["message"]
        except (ValueError, KeyError, TypeError):
            message = None
        if isinstance(message, dict):
            titles = as_title_list(message.get("title"))
            subtitles = as_title_list(message.get("subtitle"))
            if titles:
                titles.extend(titles[0] + " " + subtitle for subtitle in subtitles)
            return compare_titles(listed_title, titles, "Crossref")
    crossref_result = error or "HTTP %s" % status

    status, body, error = client.get("https://doi.org/" + quoted_doi, accept="application/vnd.citationstyles.csl+json")
    if status == 200:
        try:
            record = json.loads(body.decode("utf-8"))
        except ValueError:
            record = None
        if isinstance(record, dict):
            return compare_titles(listed_title, as_title_list(record.get("title")), "doi.org")
        return False, "not resolved: Crossref %s; doi.org returned no CSL-JSON record" % crossref_result
    return False, "not resolved: Crossref %s; doi.org %s" % (crossref_result, error or "HTTP %s" % status)


def arxiv_base_id(arxiv_id):
    """'arXiv:2304.05332v2' -> '2304.05332'."""
    text = arxiv_id.strip()
    if text.lower().startswith("arxiv:"):
        text = text[len("arxiv:"):]
    return re.sub(r"v\d+$", "", text)


def fetch_arxiv_titles(client, arxiv_ids):
    """One arXiv API request. Return ({base_id: title}, problem)."""
    query = urllib.parse.urlencode({"id_list": ",".join(arxiv_ids), "max_results": str(len(arxiv_ids))}, safe=",/")
    status, body, error = client.get(ARXIV_API_URL + "?" + query, accept="application/atom+xml")
    if status != 200:
        return {}, "arXiv API request failed: %s" % (error or "HTTP %s" % status)
    try:
        feed = ElementTree.fromstring(body)
    except ElementTree.ParseError as parse_error:
        return {}, "arXiv API returned unreadable XML (%s)" % parse_error
    titles = {}
    api_errors = []
    for entry in feed.findall(ATOM + "entry"):
        entry_id = (entry.findtext(ATOM + "id") or "").strip()
        if "/api/errors" in entry_id:
            api_errors.append(collapse_whitespace(entry.findtext(ATOM + "summary") or "error entry"))
            continue
        titles[arxiv_base_id(entry_id.split("/abs/")[-1])] = entry.findtext(ATOM + "title") or ""
    problem = ("arXiv API error: " + "; ".join(api_errors)) if api_errors else ""
    return titles, problem


def lookup_arxiv_titles(client, arxiv_ids):
    """Return {arxiv_id: (title or None, problem)} using batched requests.

    IDs missing from a batch answer (for example because another ID in the
    batch was malformed) are looked up again on their own.
    """
    results = {}
    for start in range(0, len(arxiv_ids), ARXIV_BATCH_SIZE):
        batch = arxiv_ids[start:start + ARXIV_BATCH_SIZE]
        titles, problem = fetch_arxiv_titles(client, batch)
        retry_alone = []
        for arxiv_id in batch:
            title = titles.get(arxiv_base_id(arxiv_id))
            if title is not None:
                results[arxiv_id] = (title, "")
            elif len(batch) > 1:
                retry_alone.append(arxiv_id)
            else:
                results[arxiv_id] = (None, problem or "not found in the arXiv API")
        for arxiv_id in retry_alone:
            titles, problem = fetch_arxiv_titles(client, [arxiv_id])
            title = titles.get(arxiv_base_id(arxiv_id))
            results[arxiv_id] = (title, "") if title is not None else (None, problem or "not found in the arXiv API")
    return results


def resolve_url(client, url):
    status, _, error = client.get(url, accept="text/html,application/xhtml+xml,*/*;q=0.8",
                                  max_bytes=URL_READ_LIMIT_BYTES)
    if status is not None and 200 <= status <= 399:
        return True, ""
    return False, "fetch failed: %s" % (error or "HTTP %s" % status)


def resolve_references(references):
    """Return a list of (resolved, reason), one per reference, in the same order."""
    client = HttpClient()
    results = [None] * len(references)
    arxiv_indexes = [index for index, ref in enumerate(references) if ref["kind"] == "arxiv"]
    arxiv_ids = sorted({references[index]["id"].strip() for index in arxiv_indexes})
    arxiv_titles = lookup_arxiv_titles(client, arxiv_ids) if arxiv_ids else {}
    for index in arxiv_indexes:
        ref = references[index]
        title, problem = arxiv_titles[ref["id"].strip()]
        results[index] = compare_titles(ref["title"], [title], "arXiv") if title is not None else (False, problem)
    for index, ref in enumerate(references):
        if ref["kind"] == "doi":
            results[index] = resolve_doi(client, ref["id"], ref["title"])
        elif ref["kind"] == "url":
            results[index] = resolve_url(client, ref["id"])
    return results


def check_references(root, offline):
    """Resolve references and check that every citation closes."""
    references, numbering_problems = read_reference_list(root)
    section = find_by_id(root, "references")
    listed_numbers = {ref["number"] for ref in references}

    cited_numbers = set()
    dangling_numbers = set()
    for link in find_all(root, "a"):
        match = REF_TARGET.match(link.get("href").strip())
        if not match:
            continue
        number = int(match.group(1))
        if number not in listed_numbers:
            dangling_numbers.add(number)
        if link.has_class("cite") and not is_inside(link, section):
            cited_numbers.add(number)

    # One failure reason per reference ("" = no problem). Structural problems come first;
    # only structurally sound references are resolved over the network.
    failure_reasons = [reference_problem(ref) for ref in references]
    structure_ok = not any(failure_reasons)
    if offline:
        resolved_text = failed_text = "skipped"
        failed_count = 0
    else:
        sound_positions = [position for position, reason in enumerate(failure_reasons) if not reason]
        sound_references = [references[position] for position in sound_positions]
        kinds = [ref["kind"] for ref in sound_references]
        print("(resolving %d references: %d arXiv, %d DOI, %d URL ...)"
              % (len(sound_references), kinds.count("arxiv"), kinds.count("doi"), kinds.count("url")),
              file=sys.stderr, flush=True)
        results = resolve_references(sound_references)
        for position, (resolved, reason) in zip(sound_positions, results):
            if not resolved:
                failure_reasons[position] = reason
        failed_count = sum(1 for reason in failure_reasons if reason)
        resolved_text, failed_text = str(len(references) - failed_count), str(failed_count)

    problem_lines = ["  %s %s" % (reference_label(ref), reason)
                     for ref, reason in zip(references, failure_reasons) if reason]
    uncited = [ref for ref in references if ref["number"] not in cited_numbers]
    for ref in uncited:
        problem_lines.append("  %s uncited: never cited outside the reference list" % reference_label(ref))
    for number in sorted(dangling_numbers):
        problem_lines.append('  dangling #ref-%d: linked but there is no <li id="ref-%d">' % (number, number))
    problem_lines.extend("  " + problem for problem in numbering_problems)
    if len(references) < MIN_REFERENCES:
        problem_lines.append("  too few references: %d (need >= %d)" % (len(references), MIN_REFERENCES))

    line = ("references: %d | resolved: %s | failed: %s | uncited: %d | dangling: %d"
            % (len(references), resolved_text, failed_text, len(uncited), len(dangling_numbers)))
    passed = (structure_ok and failed_count == 0 and not uncited and not dangling_numbers
              and not numbering_problems and len(references) >= MIN_REFERENCES)
    return [line] + problem_lines, passed


# ===========================================================================
# Main
# ===========================================================================
def display_path(path):
    """Path relative to the repository root when inside it, else absolute."""
    relative = os.path.relpath(path, REPO_ROOT)
    return path if relative.startswith("..") else relative


def main():
    parser = argparse.ArgumentParser(description="Check findings.html against the report contract.")
    parser.add_argument("path", nargs="?", default=DEFAULT_REPORT_PATH,
                        help="page to check (default: agents-in-science-workflow/findings.html)")
    parser.add_argument("--offline", action="store_true", help="skip network resolution of references")
    args = parser.parse_args()
    sys.stdout.reconfigure(errors="replace")

    path = os.path.abspath(args.path)
    if not os.path.isfile(path):
        print("report: %s (missing)" % display_path(path))
        print("OVERALL: FAIL")
        return 1
    with open(path, encoding="utf-8") as handle:
        root = parse_html(handle.read())
    print("report: %s (%d bytes)" % (display_path(path), os.path.getsize(path)))

    other_checks = [check_taxonomy, check_q2_structure, check_catalog, check_prompts, check_appendix,
                    check_external_resources]
    results = [check_question(root, number) for number in range(1, 7)]
    results += [check(root) for check in other_checks]
    all_passed = True
    for lines, passed in results:
        print("\n".join(lines))
        all_passed = all_passed and passed
    sys.stdout.flush()

    lines, passed = check_references(root, args.offline)
    print("\n".join(lines))
    all_passed = all_passed and passed

    suffix = " (offline: references not resolved)" if args.offline else ""
    print("OVERALL: %s%s" % (verdict(all_passed), suffix))
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
