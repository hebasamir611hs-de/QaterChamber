"""web/pages/sitemap/sitemap_page.py — SitemapPage.

Protocol-level "page object" for the public XML sitemap
(PBI 131053 / "QC - 001 - Sitemap.XML", GLOBAL service, Web platform).

WHY THIS OBJECT HOLDS NO LOCATORS
---------------------------------
Every case in this batch asserts on an HTTP response and an XML document, not
on rendered DOM — so there is nothing to extract with
`tools/extract_locators.py` and no browser is launched. The object wraps a
Playwright **APIRequestContext** (created browserless by the
`api_request_context` / `api_context_factory` fixtures in conftest.py, which
call `core/web/browser.py::new_api_context`) and exposes fetch + parse + state
queries. Assertions stay in the tests, per automation-standards.md. The same
"HTTP inside a Page Object" pattern already exists in this framework
(`web/pages/podcast/podcast_page.py`, `web/pages/home_social_icons/
home_social_icons_page.py`).

LIVE-CONFIRMED DOCUMENT STRUCTURE (qcdev, re-read read-only 2026-09-23)
-----------------------------------------------------------------------
    GET https://qcdev.ihorizons.com/sitemap.xml
      -> HTTP 200, content-type "text/xml;charset=UTF-8", 59650 bytes
      -> root element is <sitemapindex xmlns="http://www.sitemaps.org/
         schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
      -> 342 <sitemap><loc> children, each
         https://qcdev.ihorizons.com/sitemap.xml?p_l_id=39&layoutUuid=...&
         groupId=37246&privateLayout=false   (&amp;-escaped in the XML;
         ElementTree un-escapes entities on parse, so no manual unescape is
         needed once the document has been parsed)

    GET <one of those 342 children>
      -> HTTP 200, same content-type
      -> root element is <urlset ...> with <url> entries carrying
         <loc>, <lastmod> (ISO-8601 + offset, e.g. 2026-09-19T23:52:16+00:00)
         and <changefreq>, plus <xhtml:link rel="alternate" hreflang="...">
         alternates in the XHTML namespace (http://www.w3.org/1999/xhtml)
      -> the FIRST child alone already carries both language variants as
         their own <loc> entries: https://qcdev.ihorizons.com/ar/ (AR) and
         https://qcdev.ihorizons.com (EN)

**Deviation from the written test cases, recorded not "fixed":** the approved
cases were authored assuming `/sitemap.xml` is a flat `<urlset>`. This
deployment serves a `<sitemapindex>` that points at 342 per-layout child
sitemaps. A sitemap index is explicitly valid under the sitemaps.org 0.9
protocol, so this is **not** a product bug and no bug was filed — the object
follows the index into its children instead, and the tests accept either
valid sitemap root. Nothing about the cases' real intent (reachable, valid,
well-formed, bilingual, crawlable anonymously) is weakened by that.

Bounded sampling: fetching all 342 children per test would be ~342 HTTP round
trips per test. The sample bounds below are named constants for exactly that
reason; every method that samples also reports how many children it actually
read, so a failure says "not found in the first N of 342" rather than a bare
`None`.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import NamedTuple
from urllib.parse import urlsplit

import allure

from config.settings import settings, web_url

# Sitemaps protocol 0.9 namespace — the one the document must declare.
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
# XHTML namespace used by <xhtml:link rel="alternate" hreflang="..."> entries
# (a protocol-sanctioned extension, present on every <url> on this site).
XHTML_NS = "http://www.w3.org/1999/xhtml"


class SitemapDocument(NamedTuple):
    """One fetched sitemap response — raw, unparsed."""

    url: str
    status: int
    content_type: str
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


class LanguageVariantSample(NamedTuple):
    """Result of a bounded scan for EN/AR URL variants."""

    english_url: str | None
    arabic_url: str | None
    children_scanned: int
    total_children: int
    entries_seen: int


class SitemapPage:
    """Fetches and parses the public sitemap. No assertions live here."""

    # ---- Endpoints -----------------------------------------------------
    SITEMAP_PATH = "/sitemap.xml"

    # ---- Request identities --------------------------------------------
    # Real Googlebot UA string (https://developers.google.com/search/docs/
    # crawling-indexing/overview-google-crawlers) — used by the anonymous
    # crawler case to prove the sitemap is served to a search engine without
    # any login redirect or auth challenge.
    GOOGLEBOT_USER_AGENT = (
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    )

    # ---- Bounded sampling ----------------------------------------------
    # The index holds 342 child sitemaps (live count, 2026-09-23). Fetching
    # them all would be 342 HTTP requests per test, so schema/structure checks
    # read a fixed, small sample instead. 5 is enough to exercise the child
    # document shape (root element, namespace, child elements, lastmod
    # format) without turning a protocol check into a crawl.
    CHILD_SITEMAP_SAMPLE_SIZE = 5
    # Language-variant lookup gets its own, larger bound: it early-exits as
    # soon as both an EN and an AR URL are seen (live, the FIRST child already
    # carries both), so the ceiling only ever costs real requests on a site
    # whose layout changed. Separate constant so tightening the schema sample
    # can never silently shrink the bilingual search.
    BILINGUAL_SCAN_CHILD_LIMIT = 10

    # ---- Protocol vocabulary (sitemaps.org 0.9) ------------------------
    SITEMAP_ROOT_ELEMENTS = ("sitemapindex", "urlset")
    VALID_SITEMAPINDEX_CHILDREN = ("sitemap",)
    VALID_SITEMAP_ENTRY_CHILDREN = ("loc", "lastmod")
    VALID_URLSET_CHILDREN = ("url",)
    VALID_URL_CHILDREN = ("loc", "lastmod", "changefreq", "priority")
    # Namespaces a conforming document may use for child elements: the
    # sitemap namespace itself, plus XHTML for hreflang alternate links.
    ALLOWED_CHILD_NAMESPACES = (SITEMAP_NS, XHTML_NS)

    # Response body kept in the Allure attachment, in characters. These tests
    # launch no browser, so the failure hook has no screenshot/video/trace to
    # attach — this attachment is the whole diagnostic story for the module.
    ATTACHMENT_BODY_LIMIT = 2000

    def __init__(self, api_request_context):
        self.request = api_request_context

    # ---- Fetching ------------------------------------------------------
    def sitemap_url(self) -> str:
        """Absolute sitemap URL, built from WEB_BASE_URL — never hardcoded."""
        return web_url(self.SITEMAP_PATH)

    def fetch(self, url: str) -> SitemapDocument:
        """GET `url` through the anonymous APIRequestContext and attach a
        compact status/content-type/body preview to the Allure report."""
        with allure.step(f"GET {url}"):
            response = self.request.get(url)
            # Playwright lowercases response header keys.
            content_type = response.headers.get("content-type", "")
            body = response.body()
            document = SitemapDocument(
                url=url, status=response.status, content_type=content_type, body=body
            )
            # Every one of the 342 children shares the path /sitemap.xml and
            # differs only in its query (p_l_id=<layout id>), so the FIRST
            # query parameter is what makes each attachment name unique — a
            # path-only name would produce N identically-named attachments
            # and make a failed child indistinguishable in the report.
            parts = urlsplit(url)
            discriminator = parts.query.split("&")[0] if parts.query else "index"
            allure.attach(
                f"GET {url}\n"
                f"status: {document.status}\n"
                f"content-type: {content_type}\n"
                f"bytes: {len(body)}\n\n"
                f"{document.text[: self.ATTACHMENT_BODY_LIMIT]}",
                name=f"sitemap-response-{parts.path or '/'}-{discriminator}",
                attachment_type=allure.attachment_type.TEXT,
            )
            return document

    def fetch_sitemap_index(self) -> SitemapDocument:
        """GET /sitemap.xml itself (the document the cases name)."""
        return self.fetch(self.sitemap_url())

    # ---- Parsing -------------------------------------------------------
    @staticmethod
    def try_parse(document: SitemapDocument):
        """Parse a fetched document. Returns `(root, error)` — exactly one of
        the two is None — so the *test* asserts on well-formedness instead of
        this object swallowing or raising on the caller's behalf."""
        try:
            return ET.fromstring(document.body), None
        except ET.ParseError as exc:
            return None, f"{type(exc).__name__}: {exc}"

    @staticmethod
    def decodes_as_utf8(document: SitemapDocument) -> bool:
        try:
            document.body.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return True

    @staticmethod
    def namespace_of(element) -> str:
        """`{ns}tag` -> `ns` ("" when the element carries no namespace)."""
        tag = element.tag if not isinstance(element, str) else element
        return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""

    @staticmethod
    def local_name(element) -> str:
        """`{ns}tag` -> `tag`."""
        tag = element.tag if not isinstance(element, str) else element
        return tag.rsplit("}", 1)[-1]

    def root_name(self, root) -> str:
        return self.local_name(root)

    def is_sitemap_root(self, root) -> bool:
        """True for either valid sitemaps.org 0.9 root — `<sitemapindex>` (an
        index, what this deployment serves) or `<urlset>` (a flat sitemap)."""
        return (
            self.namespace_of(root) == SITEMAP_NS
            and self.local_name(root) in self.SITEMAP_ROOT_ELEMENTS
        )

    def is_index(self, root) -> bool:
        return self.local_name(root) == "sitemapindex"

    def invalid_child_elements(self, root) -> list[str]:
        """Every element inside `root` that the 0.9 protocol does not allow
        at its position, as readable `parent/child` strings. Empty list = the
        document's element vocabulary conforms."""
        invalid: list[str] = []
        if self.is_index(root):
            container, container_children = "sitemap", self.VALID_SITEMAP_ENTRY_CHILDREN
            valid_top = self.VALID_SITEMAPINDEX_CHILDREN
        else:
            container, container_children = "url", self.VALID_URL_CHILDREN
            valid_top = self.VALID_URLSET_CHILDREN

        for entry in root:
            if self.namespace_of(entry) != SITEMAP_NS or self.local_name(entry) not in valid_top:
                invalid.append(f"{self.local_name(root)}/{self.local_name(entry)}")
                continue
            for field in entry:
                ns, name = self.namespace_of(field), self.local_name(field)
                if ns == XHTML_NS and name == "link":
                    continue  # hreflang alternate — a sanctioned extension
                if ns != SITEMAP_NS or name not in container_children:
                    invalid.append(f"{container}/{name}")
        return invalid

    # ---- Index traversal -----------------------------------------------
    def child_sitemap_urls(self, index_root, limit: int | None = None) -> list[str]:
        """The `<sitemap><loc>` URLs inside a `<sitemapindex>`, oldest-first as
        served. `limit=None` returns all of them (use it only to COUNT — the
        fetch helpers below always apply a bound)."""
        locs = [
            (loc.text or "").strip()
            for loc in index_root.findall(f"{{{SITEMAP_NS}}}sitemap/{{{SITEMAP_NS}}}loc")
        ]
        locs = [loc for loc in locs if loc]
        return locs if limit is None else locs[:limit]

    def url_entries(self, urlset_root) -> list[dict]:
        """`<url>` entries of a `<urlset>` as `{"loc", "lastmod", "changefreq"}`
        dicts (missing children come back as None)."""
        entries = []
        for url_element in urlset_root.findall(f"{{{SITEMAP_NS}}}url"):
            entry = {"loc": None, "lastmod": None, "changefreq": None}
            for field in ("loc", "lastmod", "changefreq"):
                node = url_element.find(f"{{{SITEMAP_NS}}}{field}")
                if node is not None and node.text:
                    entry[field] = node.text.strip()
            entries.append(entry)
        return entries

    def sample_child_documents(self, limit: int | None = None) -> tuple[list, int]:
        """Fetch + parse a BOUNDED sample of child sitemaps.

        Returns `(documents, total_children)` where each document is a
        `(url, SitemapDocument, root_or_None, parse_error_or_None)` tuple, so
        the test can assert on every sampled child's status, namespace, root
        element and well-formedness itself.
        """
        limit = self.CHILD_SITEMAP_SAMPLE_SIZE if limit is None else limit
        index = self.fetch_sitemap_index()
        index_root, error = self.try_parse(index)
        if index_root is None:
            return [], 0
        if not self.is_index(index_root):
            # Already a flat <urlset> — the shape the cases assumed. Treat the
            # document itself as the single "child" so callers work either way.
            return [(index.url, index, index_root, None)], 1
        all_children = self.child_sitemap_urls(index_root)
        sampled = []
        for child_url in all_children[:limit]:
            child = self.fetch(child_url)
            child_root, child_error = self.try_parse(child)
            sampled.append((child_url, child, child_root, child_error))
        return sampled, len(all_children)

    def sampled_url_entries(self, limit: int | None = None) -> tuple[list[dict], int, int]:
        """Aggregated `<url>` entries across a bounded child sample.

        Returns `(entries, children_scanned, total_children)`.
        """
        sampled, total_children = self.sample_child_documents(limit=limit)
        entries: list[dict] = []
        for _url, _document, root, _error in sampled:
            if root is not None:
                entries.extend(self.url_entries(root))
        return entries, len(sampled), total_children

    # ---- Language variants ---------------------------------------------
    def is_same_site(self, url: str) -> bool:
        return urlsplit(url).netloc == urlsplit(web_url("/")).netloc

    def is_arabic_url(self, url: str) -> bool:
        """AR variant = this site's host with the configured Arabic path
        prefix (`ARABIC_PATH_PREFIX`, default `/ar`) as its first segment."""
        if not self.is_same_site(url):
            return False
        prefix = "/" + settings.arabic_path_prefix.strip("/")
        path = urlsplit(url).path or "/"
        return path == prefix or path.startswith(prefix + "/")

    def is_english_url(self, url: str) -> bool:
        """EN variant = this site's host WITHOUT the Arabic path prefix."""
        return self.is_same_site(url) and not self.is_arabic_url(url)

    def language_variant_sample(self, max_children: int | None = None) -> LanguageVariantSample:
        """Walk child sitemaps until one EN and one AR `<loc>` have been seen,
        or `max_children` children have been read — whichever comes first.

        Early-exits: live, the first child already carries both variants.
        """
        max_children = self.BILINGUAL_SCAN_CHILD_LIMIT if max_children is None else max_children
        index = self.fetch_sitemap_index()
        index_root, _error = self.try_parse(index)
        if index_root is None:
            return LanguageVariantSample(None, None, 0, 0, 0)

        if self.is_index(index_root):
            child_urls = self.child_sitemap_urls(index_root)
            total_children = len(child_urls)
            child_urls = child_urls[:max_children]
        else:
            child_urls, total_children = [], 1

        english = arabic = None
        entries_seen = 0
        scanned = 0

        def _absorb(root) -> None:
            nonlocal english, arabic, entries_seen
            for entry in self.url_entries(root):
                loc = entry["loc"]
                if not loc:
                    continue
                entries_seen += 1
                if arabic is None and self.is_arabic_url(loc):
                    arabic = loc
                elif english is None and self.is_english_url(loc):
                    english = loc

        if not child_urls:
            _absorb(index_root)
            scanned = 1
        else:
            for child_url in child_urls:
                child = self.fetch(child_url)
                child_root, _child_error = self.try_parse(child)
                scanned += 1
                if child_root is not None:
                    _absorb(child_root)
                if english and arabic:
                    break

        return LanguageVariantSample(english, arabic, scanned, total_children, entries_seen)

    # ---- Value validators ----------------------------------------------
    @staticmethod
    def is_valid_iso8601(value: str) -> bool:
        """W3C-datetime / ISO-8601 check for `<lastmod>`. Uses
        `datetime.fromisoformat` (Python 3.11+ accepts both the `+00:00`
        offset form this site emits and the `Z` form) rather than a regex, so
        an impossible date like 2026-13-45 is rejected too."""
        if not value:
            return False
        try:
            datetime.fromisoformat(value.strip())
        except ValueError:
            return False
        return True

    def invalid_lastmod_values(self, entries: list[dict]) -> list[str]:
        """Every `<lastmod>` in `entries` that is present but not valid
        ISO-8601. Entries without a `<lastmod>` are not flagged — the element
        is optional in the protocol."""
        return [
            entry["lastmod"]
            for entry in entries
            if entry.get("lastmod") is not None and not self.is_valid_iso8601(entry["lastmod"])
        ]

    @staticmethod
    def entries_missing_loc(entries: list[dict]) -> list[dict]:
        return [entry for entry in entries if not entry.get("loc")]

    @staticmethod
    def is_xml_content_type(content_type: str) -> bool:
        return "xml" in content_type.lower()

    @staticmethod
    def declares_utf8(content_type: str) -> bool:
        return "utf-8" in content_type.lower().replace(" ", "")

    @staticmethod
    def is_login_redirect(document: SitemapDocument) -> bool:
        """True when a response looks like an auth challenge/login redirect
        rather than the sitemap — used by the anonymous-crawler case."""
        if document.status in (401, 403):
            return True
        if document.status >= 300:
            return True
        lowered = document.text[:4000].lower()
        return "/c/portal/login" in lowered or "<html" in lowered
