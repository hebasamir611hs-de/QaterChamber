"""web/tests/sitemap/test_sitemap_web.py — PBI 131053 "QC - 001 -
Sitemap.XML" (GLOBAL service), Web platform.

Source: the 11 approved, Automation-tagged cases of Azure Test Plan 137724 /
suite 140391 (ADO #141690, #141691, #141692, #141693, #141694, #141699,
#141700, #141701, #141703, #141704, #141707). All are Platform=Web, so all 11
live in this single module; no Control_Panel/CMS test was written or run for
this PBI (explicitly out of scope for this batch).

NO BROWSER IS LAUNCHED HERE. Every runnable case asserts on an HTTP response
and an XML document, so these tests use the browserless `api_request_context`
/ `api_context_factory` fixtures (conftest.py -> core/web/browser.py::
new_api_context) instead of the `page` fixture. Two consequences worth
knowing before reading a failure:
  * the conftest failure hook has no page to screenshot, and there is no
    video/trace for these tests — the diagnostic evidence is the
    status/content-type/body-preview text attachment SitemapPage.fetch()
    attaches to every request instead;
  * the APIRequestContext is created with NO storageState, so every request
    below is genuinely anonymous — which is also what makes #141707's
    logged-out premise real (standards.md's "Draft/Unpublish Public-
    Visibility Checks — Mandatory Logged-Out Context" rule).

DEVIATION FROM THE WRITTEN CASES — RECORDED, NOT SILENTLY "FIXED"
-----------------------------------------------------------------
The cases were authored assuming `/sitemap.xml` returns a flat `<urlset>`.
Live (read-only, 2026-09-23) it returns a **`<sitemapindex>`** in the
sitemaps.org 0.9 namespace holding 342 child sitemaps, each of which IS a
`<urlset>` with `<url><loc>`/`<lastmod>`/`<changefreq>` entries. A sitemap
index is explicitly valid under the 0.9 protocol, so **this is not a product
bug and no bug was filed**. The tests therefore accept either valid sitemap
root and follow the index into its children; they do not assert the cases'
literal "root element is urlset" wording, and no assertion was weakened to
get there. Full evidence trail in
web/pages/sitemap/sitemap_page.py's module docstring.

BOUNDED SAMPLING
----------------
342 children is too many to fetch per test, so the structural cases read a
bounded sample: SitemapPage.CHILD_SITEMAP_SAMPLE_SIZE = 5 children for the
schema/structure checks (#141694, #141701) and
SitemapPage.BILINGUAL_SCAN_CHILD_LIMIT = 10 for the language-variant scan
(#141703, #141704), which early-exits as soon as both variants are seen — the
first child alone carries both live. Every assertion message reports how many
children were actually scanned out of the real total.

PER-CASE NOTES
--------------
* #141694 names a specific page with `lastmod = 2026-09-10`. That fixture
  page does not exist on qcdev, so the exact-date precondition was NOT
  available; the test asserts the case's STRUCTURAL rule instead (every
  `<url>` exposes a `<loc>`, and every `<lastmod>` present is valid ISO-8601)
  across the bounded sample. Stated here rather than faked.
* 5 of the 11 cases (#141691, #141692, #141693, #141699, #141700) are
  `@pytest.mark.skip` with their exact blocking reason: each needs CMS
  publish/unpublish/draft/archive preconditions, i.e. writes against the real
  live site. Per standards.md's "Destructive-Precondition Tests Must Use
  Disposable Test Data" rule step 4, a case whose state cannot be built
  within this batch's scope stays skipped with the concrete reason — it is
  not faked, and no CMS path was written.
* Marker note: this session had **no Azure read tool available**, so only the
  tags supplied with the batch were used. The 6 runnable cases carry their
  full supplied axis set. The 5 skipped cases carry Platform (`web`),
  Service (`global_`), Axis B and Axis C, plus `workflow` where the batch
  named it — **no Axis-1/Axis-4 marker was invented for them** because their
  Lifecycle/Category tags were not supplied. Add those markers when the tags
  are read back from Azure.
"""

import allure
import pytest

from web.pages.sitemap.sitemap_page import SITEMAP_NS, SitemapPage

PBI = "131053"


# ── #141690 — sitemap is publicly reachable and is valid, well-formed XML ──
@allure.epic("GLOBAL")
@allure.feature("Sitemap.XML")
@allure.story("Availability & well-formedness")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("/sitemap.xml is publicly reachable and is valid, well-formed XML in the sitemaps.org 0.9 namespace")
@allure.label("pbi", PBI)
@allure.label("testcase", "141690")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_131053
@pytest.mark.tc_141690
@pytest.mark.traceability("ADO-141690")
def test_sitemap_xml_is_reachable_and_well_formed(api_request_context):
    """ADO-141690 | PBI 131053 — GET /sitemap.xml returns HTTP 200 with an XML
    content-type and a well-formed sitemaps.org 0.9 document."""
    # Arrange
    sitemap = SitemapPage(api_request_context)

    # Act
    document = sitemap.fetch_sitemap_index()
    root, parse_error = sitemap.try_parse(document)

    # Assert
    assert document.status == 200, (
        f"GET {document.url} returned HTTP {document.status}, expected 200"
    )
    assert sitemap.is_xml_content_type(document.content_type), (
        f"content-type was {document.content_type!r}, expected an XML type"
    )
    assert parse_error is None, f"{document.url} is not well-formed XML: {parse_error}"
    assert sitemap.is_sitemap_root(root), (
        f"root element is {{{sitemap.namespace_of(root)}}}{sitemap.local_name(root)}; "
        f"expected a sitemaps.org 0.9 root (sitemapindex or urlset). "
        f"This deployment serves a sitemapindex — valid per the 0.9 protocol."
    )


# ── #141691 — SKIPPED: needs QCTEST fixture pages in the CMS ───────────────
@allure.epic("GLOBAL")
@allure.feature("Sitemap.XML")
@allure.story("Published-page coverage")
@allure.title("Sitemap lists every published page and omits the unpublished one")
@allure.label("pbi", PBI)
@allure.label("testcase", "141691")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_131053
@pytest.mark.tc_141691
@pytest.mark.traceability("ADO-141691")
@pytest.mark.skip(
    reason="BLOCKED — the case's precondition needs fixture pages "
    "QCTEST-SITEMAP-01/02/03 published and QCTEST-SITEMAP-04 unpublished on "
    "qcdev. Those pages do not exist, and creating them is a CMS "
    "(Control_Panel) write operation explicitly excluded from this Web-only, "
    "strictly read-only batch. Not faked, and no CMS path was written — per "
    "standards.md's Destructive-Precondition rule, step 4."
)
def test_sitemap_lists_published_pages_and_omits_unpublished(api_request_context):
    ...


# ── #141692 — SKIPPED: needs a CMS publish ─────────────────────────────────
@allure.epic("GLOBAL")
@allure.feature("Sitemap.XML")
@allure.story("Publish propagation")
@allure.title("Newly published page appears in the sitemap")
@allure.label("pbi", PBI)
@allure.label("testcase", "141692")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_131053
@pytest.mark.tc_141692
@pytest.mark.traceability("ADO-141692")
@pytest.mark.skip(
    reason="BLOCKED — the case's precondition requires PUBLISHING a page via "
    "the CMS, a Control_Panel write against the real live site. This batch is "
    "Web-only and strictly read-only (no publish/unpublish/draft/archive/"
    "create/delete against qcdev), so the state cannot be reached here. Not "
    "faked — standards.md's Destructive-Precondition rule, step 4."
)
def test_newly_published_page_appears_in_sitemap(api_request_context):
    ...


# ── #141693 — SKIPPED: needs a CMS unpublish (destructive) ─────────────────
@allure.epic("GLOBAL")
@allure.feature("Sitemap.XML")
@allure.story("Unpublish propagation")
@allure.title("Unpublished page is removed from the sitemap")
@allure.label("pbi", PBI)
@allure.label("testcase", "141693")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_131053
@pytest.mark.tc_141693
@pytest.mark.traceability("ADO-141693")
@pytest.mark.skip(
    reason="BLOCKED — the case's precondition requires UNPUBLISHING a real "
    "page on qcdev: a destructive Control_Panel write against real shared "
    "content, excluded from this Web-only read-only batch and forbidden "
    "without its own explicit, ID-named user approval (standards.md's "
    "Destructive-Precondition rule, steps 4-5). Not faked, not attempted."
)
def test_unpublished_page_is_removed_from_sitemap(api_request_context):
    ...


# ── #141694 — every <url> exposes <loc>; any <lastmod> is valid ISO-8601 ───
@allure.epic("GLOBAL")
@allure.feature("Sitemap.XML")
@allure.story("URL entry structure")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Every <url> entry exposes a <loc>, and any <lastmod> present is a valid ISO-8601 date")
@allure.label("pbi", PBI)
@allure.label("testcase", "141694")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_131053
@pytest.mark.tc_141694
@pytest.mark.traceability("ADO-141694")
def test_url_entries_expose_loc_and_valid_lastmod(api_request_context):
    """ADO-141694 | PBI 131053 — structural rule across a bounded sample.

    The approved case names a specific page whose `lastmod` should read
    2026-09-10. That fixture page does not exist on qcdev, so the exact-date
    precondition was NOT available; asserted here is the case's underlying
    structural rule instead — stated in the module docstring, not faked.
    """
    # Arrange
    sitemap = SitemapPage(api_request_context)

    # Act
    entries, children_scanned, total_children = sitemap.sampled_url_entries()

    # Assert
    assert entries, (
        f"no <url> entries found in the first {children_scanned} of "
        f"{total_children} child sitemaps"
    )
    missing_loc = sitemap.entries_missing_loc(entries)
    assert not missing_loc, (
        f"{len(missing_loc)} of {len(entries)} <url> entries have no <loc> "
        f"(sampled {children_scanned} of {total_children} child sitemaps)"
    )
    invalid_lastmod = sitemap.invalid_lastmod_values(entries)
    assert not invalid_lastmod, (
        f"non-ISO-8601 <lastmod> values: {invalid_lastmod[:5]} "
        f"(sampled {children_scanned} of {total_children} child sitemaps)"
    )


# ── #141699 — SKIPPED: needs a Draft page created in the CMS ───────────────
@allure.epic("GLOBAL")
@allure.feature("Sitemap.XML")
@allure.story("Draft exclusion")
@allure.title("Draft page is excluded from the sitemap")
@allure.label("pbi", PBI)
@allure.label("testcase", "141699")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_low
@pytest.mark.pbi_131053
@pytest.mark.tc_141699
@pytest.mark.traceability("ADO-141699")
@pytest.mark.skip(
    reason="BLOCKED — the case's precondition requires CREATING a Draft page "
    "via the CMS, a Control_Panel write excluded from this Web-only, strictly "
    "read-only batch (no content creation against qcdev). Not faked and no "
    "CMS path was written — standards.md's Destructive-Precondition rule, "
    "step 4."
)
def test_draft_page_is_excluded_from_sitemap(api_request_context):
    ...


# ── #141700 — SKIPPED: needs Rejected/Archived pages in the CMS ────────────
@allure.epic("GLOBAL")
@allure.feature("Sitemap.XML")
@allure.story("Rejected / Archived exclusion")
@allure.title("Rejected and Archived pages are excluded from the sitemap")
@allure.label("pbi", PBI)
@allure.label("testcase", "141700")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.workflow
@pytest.mark.functional_low
@pytest.mark.pbi_131053
@pytest.mark.tc_141700
@pytest.mark.traceability("ADO-141700")
@pytest.mark.skip(
    reason="BLOCKED — the case's precondition requires pages in Rejected / "
    "Archived workflow states, reachable only through CMS (Control_Panel) "
    "writes against the real live site. Excluded from this Web-only, strictly "
    "read-only batch; not faked — standards.md's Destructive-Precondition "
    "rule, step 4."
)
def test_rejected_and_archived_pages_are_excluded_from_sitemap(api_request_context):
    ...


# ── #141701 — document conforms to the sitemap protocol 0.9 schema ─────────
@allure.epic("GLOBAL")
@allure.feature("Sitemap.XML")
@allure.story("Protocol 0.9 conformance")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Sitemap conforms to the sitemaps.org 0.9 protocol: namespace, well-formedness, valid child elements, UTF-8")
@allure.label("pbi", PBI)
@allure.label("testcase", "141701")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.pbi_131053
@pytest.mark.tc_141701
@pytest.mark.traceability("ADO-141701")
def test_sitemap_conforms_to_protocol_09_schema(api_request_context):
    """ADO-141701 | PBI 131053 — validates the index document itself plus a
    bounded sample of SitemapPage.CHILD_SITEMAP_SAMPLE_SIZE (5) child
    sitemaps out of the 342 the index lists; fetching all 342 per test would
    turn a protocol check into a crawl."""
    # Arrange
    sitemap = SitemapPage(api_request_context)

    # Act
    index = sitemap.fetch_sitemap_index()
    index_root, index_parse_error = sitemap.try_parse(index)

    # Assert — the index document itself
    assert index.status == 200, f"GET {index.url} returned HTTP {index.status}"
    assert index_parse_error is None, f"index is not well-formed XML: {index_parse_error}"
    assert sitemap.namespace_of(index_root) == SITEMAP_NS, (
        f"index namespace is {sitemap.namespace_of(index_root)!r}, "
        f"expected the sitemaps.org 0.9 namespace"
    )
    assert sitemap.is_sitemap_root(index_root), (
        f"index root element is {sitemap.local_name(index_root)!r}"
    )
    assert sitemap.declares_utf8(index.content_type), (
        f"index content-type {index.content_type!r} does not declare UTF-8"
    )
    assert sitemap.decodes_as_utf8(index), "index body is not valid UTF-8"
    index_invalid = sitemap.invalid_child_elements(index_root)
    assert not index_invalid, f"index carries non-protocol elements: {index_invalid[:10]}"

    # Act + Assert — a bounded sample of the child sitemaps
    sampled, total_children = sitemap.sample_child_documents()
    assert sampled, f"index listed {total_children} children but none could be sampled"
    for child_url, child, child_root, child_parse_error in sampled:
        assert child.status == 200, f"{child_url} returned HTTP {child.status}"
        assert child_parse_error is None, f"{child_url} is not well-formed XML: {child_parse_error}"
        assert sitemap.is_sitemap_root(child_root), (
            f"{child_url} root is "
            f"{{{sitemap.namespace_of(child_root)}}}{sitemap.local_name(child_root)}"
        )
        assert sitemap.declares_utf8(child.content_type), (
            f"{child_url} content-type {child.content_type!r} does not declare UTF-8"
        )
        assert sitemap.decodes_as_utf8(child), f"{child_url} body is not valid UTF-8"
        child_invalid = sitemap.invalid_child_elements(child_root)
        assert not child_invalid, (
            f"{child_url} carries non-protocol elements: {child_invalid[:10]}"
        )


# ── #141703 — an English URL variant is present ────────────────────────────
@allure.epic("GLOBAL")
@allure.feature("Sitemap.XML")
@allure.story("Bilingual coverage")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An English URL variant (no /ar/ prefix) is present among the sitemap's <url> entries")
@allure.label("pbi", PBI)
@allure.label("testcase", "141703")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_131053
@pytest.mark.tc_141703
@pytest.mark.traceability("ADO-141703")
def test_english_url_variant_is_present(api_request_context):
    """ADO-141703 | PBI 131053 — bounded scan of up to
    SitemapPage.BILINGUAL_SCAN_CHILD_LIMIT (10) child sitemaps, early-exiting
    once both language variants are seen."""
    # Arrange
    sitemap = SitemapPage(api_request_context)

    # Act
    variants = sitemap.language_variant_sample()

    # Assert
    assert variants.english_url, (
        f"no English URL variant found in {variants.entries_seen} <url> entries "
        f"across the first {variants.children_scanned} of "
        f"{variants.total_children} child sitemaps"
    )
    assert sitemap.is_english_url(variants.english_url), (
        f"{variants.english_url} is not an English (non-/ar/) variant of this site"
    )


# ── #141704 — an Arabic URL variant is present, distinct from the EN one ───
@allure.epic("GLOBAL")
@allure.feature("Sitemap.XML")
@allure.story("Bilingual coverage")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An Arabic URL variant (/ar/ prefix) is present and distinct from the English one")
@allure.label("pbi", PBI)
@allure.label("testcase", "141704")
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_131053
@pytest.mark.tc_141704
@pytest.mark.traceability("ADO-141704")
def test_arabic_url_variant_is_present_and_distinct(api_request_context):
    """ADO-141704 | PBI 131053 — same bounded scan as #141703; asserts the AR
    variant exists and is a different URL from the EN one."""
    # Arrange
    sitemap = SitemapPage(api_request_context)

    # Act
    variants = sitemap.language_variant_sample()

    # Assert
    assert variants.arabic_url, (
        f"no Arabic (/ar/) URL variant found in {variants.entries_seen} <url> "
        f"entries across the first {variants.children_scanned} of "
        f"{variants.total_children} child sitemaps"
    )
    assert sitemap.is_arabic_url(variants.arabic_url), (
        f"{variants.arabic_url} does not carry this site's Arabic path prefix"
    )
    assert variants.arabic_url != variants.english_url, (
        f"the Arabic and English variants resolved to the same URL: "
        f"{variants.arabic_url}"
    )


# ── #141707 — anonymous/crawler request is served without an auth challenge ─
@allure.epic("GLOBAL")
@allure.feature("Sitemap.XML")
@allure.story("Anonymous crawler access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An anonymous, unauthenticated (Googlebot) request returns the sitemap with no login redirect or auth challenge")
@allure.label("pbi", PBI)
@allure.label("testcase", "141707")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.pbi_131053
@pytest.mark.tc_141707
@pytest.mark.traceability("ADO-141707")
def test_anonymous_crawler_request_is_served_without_auth_challenge(api_context_factory):
    """ADO-141707 | PBI 131053 — issued from a FRESH APIRequestContext that
    loads no storageState and carries no cookie from any other test, with a
    real Googlebot User-Agent, so the logged-out premise is genuine
    (standards.md's mandatory logged-out-context rule)."""
    # Arrange — a fresh, genuinely anonymous crawler context
    crawler_context = api_context_factory(user_agent=SitemapPage.GOOGLEBOT_USER_AGENT)
    sitemap = SitemapPage(crawler_context)

    # Act
    document = sitemap.fetch_sitemap_index()
    root, parse_error = sitemap.try_parse(document)

    # Assert
    assert document.status == 200, (
        f"anonymous Googlebot GET {document.url} returned HTTP {document.status}, "
        f"expected 200 with no auth challenge"
    )
    assert not sitemap.is_login_redirect(document), (
        f"anonymous request was answered with a login/auth challenge instead of "
        f"the sitemap (status {document.status}, content-type "
        f"{document.content_type!r})"
    )
    assert sitemap.is_xml_content_type(document.content_type), (
        f"content-type was {document.content_type!r}, expected an XML type"
    )
    assert parse_error is None, f"anonymous response is not well-formed XML: {parse_error}"
    assert sitemap.is_sitemap_root(root), (
        f"anonymous response root is {sitemap.local_name(root)!r}, "
        f"expected sitemapindex or urlset"
    )
