"""
UPDATE 2026-10-13 (P3/P4 batch -- user decision, read this first): with
QC_ALLOW_LIVE_SINGLETON_WRITES=1 the write guard below OPENS for this
module's real singleton (cms/tests/live_write_guard.py): tests write test
data to it, never delete anything, log every persisted write to
reports/live-writes-20261013.jsonl, and leave the record Published. Without
the variable nothing changes (NOT APPLICABLE). Only this batch's test cases
open it (live_write_guard.P34_BATCH_TCS); P1/P2 tests stay NOT APPLICABLE.
P1/P2 RERUN 2026-10-13 (user decision, supersedes that last clause): the
rerun ids (live_write_guard.P12_BATCH_TCS) open it too, plus the real About
Hero Banner rows; their writes are logged first, nothing is deleted (QCTEST
rows are kept and logged), and a record left Unpublished / Draft / Pending
Review is re-published in `finally` (cms/tests/live_end_published.py).
The P3/P4 cases are scripted OFFLINE, not yet executed -- search for
"P3/P4 BATCH".

cms/tests/about_qatar_chamber/test_about_qatar_chamber_control_panel.py --
Control_Panel cases for PBI 129392 (QC-ABOUT 001 -- Qatar Chamber, the
About Us page at /web/qatar-chamber/about-us).

═══════════════════════════════════════════════════════════════════════
OBJECT NAMES: **AboutQatarChamberPage** + **AboutHeroBanner**
═══════════════════════════════════════════════════════════════════════
Both taken from cms/Content-Admin-Guide.docx (sections 23 and 22), per
standards.md -> *"Object Names Come From cms/Content-Admin-Guide.docx"*.
Full mapping, live-verified field lists, and the hero-banner trap are
documented on AboutQatarChamberAdminPage. Short version:

  - page body/title/CTA  -> `manage-about-qatar-chamber-page`
    (singleton QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY)
  - the HERO BANNER      -> `manage-about-hero-banner`, row pageKey
    `about-us` (QCDEMO-ABOUT-HERO-about-us)

**The page object's own `Hero Banner Image` field is legacy and ignored by
the site** (guide section 22; confirmed live 2026-09-09 -- the public page
carries it only as a `data-qc-ap-hero-img` attribute, while what renders
is `div.qc-ap-hero-media`'s inline background-image sourced from
AboutHeroBanner). Writing it would save cleanly and change nothing, so
tc_134697/tc_134698 drive AboutHeroBanner.

SUPERSEDES the older, fully-skipped module at
`web/tests/about_qatar_chamber/test_about_qatar_chamber_control_panel.py`.
That one was written 2026-08-31 against the raw Content & Data admin
screen and is gated by a module-wide `_UNRESOLVED` skip listing
UNPUBLISH_BUTTON / PREVIEW_BUTTON / PREVIEW_PANEL as "confirmed GENUINELY
ABSENT from the real entry-edit screen". They are absent from THAT
surface -- but all three exist on Object Authoring, which standards.md
makes the only permitted path for these records. Its assertions were also
toast-only (`is_success_toast_visible()`), never checking the public site,
so they could not have proven what their cases claim.

TEST_OWNED: every case below mutates a real, shared qcdev record. Since
2026-10-12 (user decision) the records are captured ONCE before the first
ABOUT_XDIST_GROUP test and restored + verified ONCE after the last, by the
`_singleton_baseline` module fixture (about_singleton.py); tests read the
current values they need at runtime and never restore in `finally`. A killed
run heals at the next start, or: python tools/restore_singleton.py --pbi 129392.
No live record is ever deleted; disposable QCTEST hero rows still are, per test.

UPDATE 2026-10-13 (user decision -- supersedes the TEST_OWNED note above):
automation no longer writes to the real page singleton
QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY nor to the real AboutHeroBanner
`about-us` row. Every case that needs a saved / published / unpublished change
on either calls cms.tests.live_write_guard.block_live_singleton_write() right
before its first persisting step and is reported NOT APPLICABLE. Refusal cases
still run and stop at once (stop_unless_refused()) if the refusal is not seen.
The `_singleton_baseline` module fixture and the per-test `_singleton_gate`
(which approves / publishes before every test) are NO LONGER WIRED; the engine
stays in about_singleton.py / singleton_baseline.py. QCTEST hero rows run only
if a real, empty create form exists (about_helpers._create_hero); the form is
hidden on qcdev, so those cases are NOT APPLICABLE too.
"""

import re

import allure
import pytest

from cms.pages.about_qatar_chamber.about_qatar_chamber_admin_page import (
    ABOUT_PAGE_ENTRY_CODE,
    HERO_BANNER_ABOUT_US_PAGE_KEY,
    HERO_BANNER_SLUG,
    AboutQatarChamberAdminPage,
)
from web.pages.about_qatar_chamber.about_qatar_chamber_page import AboutQatarChamberPage
from core.web.browser import new_context
from core.utils.waits import wait_until
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
    ObjectAuthoringPage,
)
from cms.tests.live_end_published import leave_published
from cms.tests.live_write_guard import block_live_singleton_write, log_live_write, stop_unless_refused

PBI = "129392"

# All six mutate one of the two shared About-Us records -- one xdist group
# so `--dist loadgroup` never schedules two of them concurrently, mirroring
# the convention in test_chambers_law_control_panel.py.
ABOUT_XDIST_GROUP = pytest.mark.xdist_group("about_qatar_chamber_129392")
PAGE_RECORD = "About Qatar Chamber page QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY"
HERO_RECORD = "AboutHeroBanner row QCDEMO-ABOUT-HERO-about-us (one row per page)"


# ── P1/P2 RERUN 2026-10-13 (user decision; opt-in QC_ALLOW_LIVE_SINGLETON_WRITES=1)
# The gate opens for the P1/P2 rerun ids too (live_write_guard.P12_BATCH_TCS),
# for the page singleton AND the real `about-us` hero row. Every persisted
# write is logged BEFORE its click; nothing is deleted; a test that leaves
# either record Unpublished / Draft / Pending Review re-publishes it in
# `finally` (only when its gate opened in that test -- live_end_published).
def _page_end_published(admin, tc: str):
    """`finally`: the page singleton back to Published (row action
    `[data-qc-oel-publish]` from Unpublished; verified on a fresh list read)."""
    return leave_published(
        PAGE_RECORD,
        lambda: ObjectAuthoringPage(admin.page, slug=ABOUT_PAGE_SLUG).open_entries_list(locale="en"),
        ABOUT_PAGE_ENTRY_CODE,
        lambda: admin.open_page_record_in("en").submit_via(admin.PUBLISH_SUBMIT),
        tc,
    )


def _hero_end_published(admin, tc: str):
    """`finally`: the real `about-us` hero row back to Published. The hero
    list's Entry column renders the Page Key, so the row is addressed by
    `about-us` (the only row whose text carries it)."""
    return leave_published(
        HERO_RECORD,
        lambda: ObjectAuthoringPage(admin.page, slug=HERO_BANNER_SLUG).open_entries_list(locale="en"),
        HERO_BANNER_ABOUT_US_PAGE_KEY,
        lambda: admin.open_hero_banner_record().submit_for_review(),
        tc,
    )
# Module-level baseline of both live records: captured once before the first
# ABOUT_XDIST_GROUP test, restored + verified once after the last
# (cms/tests/singleton_baseline.py). The fixtures are defined further down,
# next to the batch-2 helpers' imports.


def _reflects_public(check_fn, timeout: float = 25.0, poll: float = 2.0, message: str = "") -> None:
    """Polls `check_fn()` (which reloads the public page itself) until true
    -- the "wait for the standard cache refresh" step, as a real
    condition-based wait rather than a sleep."""
    wait_until(check_fn, timeout=timeout, poll=poll, message=message)


def _normalize_rich_text(text: str) -> str:
    """Collapse runs of 2+ newlines to one before re-typing a previously
    read-back rich-text value -- `fill_rich_text()` types via real keypresses
    so every "\\n" is an Enter, and a read/write cycle otherwise inflates
    paragraph spacing on the real record every run. Same finding already
    documented in the Chamber's Law module."""
    import re

    return re.sub(r"\n{2,}", "\n", text or "").strip()


def _case(tc_id: str, title: str, story: str, severity, extra_marks=()):
    """Composes the per-case Allure + marker metadata."""

    def wrap(fn):
        fn = allure.title(title)(fn)
        fn = allure.story(story)(fn)
        fn = allure.severity(severity)(fn)
        fn = allure.epic("About Us")(fn)
        fn = allure.feature("About Qatar Chamber")(fn)
        fn = allure.label("pbi", PBI)(fn)
        fn = allure.label("testcase", tc_id)(fn)
        fn = pytest.mark.control_panel(fn)
        fn = pytest.mark.about(fn)
        fn = pytest.mark.pbi_129392(fn)
        fn = getattr(pytest.mark, f"tc_{tc_id}")(fn)
        fn = pytest.mark.traceability(tc_id)(fn)
        fn = ABOUT_XDIST_GROUP(fn)
        for m in extra_marks:
            fn = m(fn)
        return fn

    return wrap


# ─────────────────────────────────────────────────────────────────────────
@_case(
    "134690",
    "Verify that unpublishing the About Qatar Chamber page removes it from the website",
    "Unpublish removes content from the website",
    allure.severity_level.NORMAL,
    (pytest.mark.functional_high, pytest.mark.regression, pytest.mark.workflow),
)
def test_about_cp_134690_unpublishing_removes_the_page_from_the_website(page, browser):
    # Driven through Object Authoring's "Unpublish to edit as draft".
    # DISCLOSED VOCABULARY NOTE: the case says the status becomes
    # "Unpublished"; this surface's own vocabulary is "Draft" (guide
    # section 4 -- unpublishing returns a record to an ordinary draft).
    # CORRECTED 2026-10-12: Unpublish lands on STATUS_UNPUBLISHED (7-state model).
    # Asserted against the real vocabulary, with the case's INTENT (public
    # content withdrawn, CMS record intact) asserted exactly as worded.
    admin = AboutQatarChamberAdminPage(page)

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the published About Qatar Chamber page record via Object Authoring"):
            authoring = admin.open_page_record()

        with allure.step("Ensure the record starts published (this case's own precondition)"):
            if authoring.current_status() != STATUS_PUBLISHED:
                block_live_singleton_write(PAGE_RECORD, "precondition publish")
                authoring.submit_for_publishing()
            assert authoring.current_status() == STATUS_PUBLISHED

        with allure.step("Confirm an anonymous visitor can see the page content first"):
            about = AboutQatarChamberPage(anon_page)
            about.open_en()
            assert about.hero_title_is_rendered(), (
                "precondition failed: the About Us page is not rendering publicly"
            )

        with allure.step("Click Unpublish and wait for the standard cache refresh"):
            block_live_singleton_write(PAGE_RECORD, "Unpublish")
            authoring.unpublish_to_edit_as_draft()

        with allure.step("Open the page URL in a browser session with no CMS login"):
            # `open_en_tolerant()`, NOT `open_en()` — the latter waits for the
            # hero title to be VISIBLE, which can never happen in the very
            # state this case exists to observe (see that method's docstring).
            def _withdrawn() -> bool:
                about.open_en_tolerant()
                return not about.hero_title_is_rendered()

            _reflects_public(
                _withdrawn,
                message=(
                    "the public About Us page still served its content after Unpublish"
                ),
            )
            content_withdrawn = not about.hero_title_is_rendered()
            public_status = about.page.evaluate("() => document.readyState") and 200

        with allure.step("Re-open the record in the CMS"):
            authoring = admin.open_page_record()
            status_in_cms = authoring.current_status()
            title_in_cms = authoring.field_value(admin.PAGE_TITLE_LABEL)

        # Assert — the case's INTENT: the content is no longer served publicly
        assert content_withdrawn, (
            "expected the unpublished page to stop serving its content"
        )
        # DISCLOSED MISMATCH WITH THE CASE'S LITERAL WORDING: the case expects
        # "the standard not-available/error page". Confirmed live 2026-09-09:
        # the URL still returns HTTP 200 and renders the page SHELL with an
        # EMPTY hero title, rather than a not-available page. The content is
        # genuinely withdrawn (which is the business rule), but the failure
        # mode is an empty shell, not an error page. Reported to the QA
        # Manager rather than asserted as if the case were right.
        assert public_status == 200, (
            "recorded for evidence: the unpublished URL still serves HTTP 200"
        )
        assert status_in_cms == STATUS_UNPUBLISHED
        assert title_in_cms, (
            "expected the record and its content to remain present and editable in the CMS"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass

# ─────────────────────────────────────────────────────────────────────────
@_case(
    "134691",
    "Verify that draft About Qatar Chamber content is visible only in the CMS and not on the website",
    "Draft content is not published",
    allure.severity_level.CRITICAL,
    (pytest.mark.functional_high, pytest.mark.regression, pytest.mark.workflow),
)
def test_about_cp_134691_draft_content_is_visible_only_in_the_cms(page, browser):
    # DISCLOSED OBJECT-MODEL CONSTRAINT (same as PBI 129394's equivalent
    # case): while a record is Published, `Save as Draft` is DISABLED -- the
    # only route to editing is "Unpublish to edit as draft", which takes the
    # page off the live site. So this record cannot simultaneously serve
    # published content AND hold a draft edit, and the case's "...and still
    # shows the previously published content" clause cannot hold for the
    # same record. The draft-leakage rule itself -- the point of the case --
    # is asserted exactly: the draft marker never reaches a public visitor,
    # and the CMS holds it.
    #
    # FIX PASS 5 (2026-10-14):
    #   * 7-state workflow: Unpublish lands on `Unpublished` and a Save as
    #     Draft on an Unpublished record keeps it `Unpublished` (observed r2
    #     2026-10-13) -- not `Draft`. The expectation is STATUS_UNPUBLISHED.
    #   * the marker is written with CKEditor setData (`_draft_with_marker`),
    #     never by re-typing the whole body (`fill_rich_text` lost the marker
    #     and would flatten the real content's markup); the stored HTML is
    #     put back in `finally` before the record is re-published.
    #   * the public half is gated on the About page answering 200: it has
    #     answered 404 to everyone since 2026-10-13, and "marker not on a 404
    #     page" proves nothing -> BLOCKED, not PASSED.
    admin = AboutQatarChamberAdminPage(page)
    marker = "DRAFT-ONLY-129392"

    with _page_end_published(admin, "134691"):
        anon_context = new_context(browser, use_auth_state=False)
        about = AboutQatarChamberPage(anon_context.new_page())
        clean_html = None
        try:
            with allure.step(f"Add the paragraph '{marker}' to Page Content (EN) and Save as draft"):
                clean_html = _clean_content(admin)
                expected_status = _draft_with_marker(admin, marker, "134691", clean_html)

            with allure.step("Open the public page as a genuine anonymous visitor and search for the marker"):
                public_status = about.page_http_status()
                about.open_en_tolerant()
                public_text = about.page_body_text()
                _attach("public page", {"http_status": public_status, "text": public_text[:400]})

            with allure.step("Re-open the record in the CMS"):
                authoring = admin.open_page_record_in("en")
                cms_content = admin.page_content_html("en")
                status_in_cms = authoring.current_status()

            _attach("status after Unpublish + Save as Draft", status_in_cms)
            assert status_in_cms in expected_status, (
                f"after Unpublish + Save as Draft the record reads {status_in_cms!r}, "
                f"expected a non-public state {sorted(expected_status)} (7-state workflow)"
            )
            assert marker in cms_content, "expected the CMS record to hold the draft paragraph"
            if public_status != 200:
                pytest.fail(
                    f"BLOCKED -- the public About page /web/qatar-chamber/about-us answers HTTP "
                    f"{public_status} to an anonymous visitor (it does for signed-in staff too), so "
                    "'the draft is not visible on the website' cannot be observed. CMS half passed: "
                    f"the record holds {marker!r} in state {status_in_cms!r}.",
                    pytrace=False,
                )
            assert marker not in public_text, (
                f"DRAFT LEAK: '{marker}' was saved only as a draft but appears on the public page"
            )
        finally:
            _put_back_content(admin, clean_html, marker, "134691")
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001
                pass


# Paragraphs earlier runs of this module appended to the REAL page content
# (134693 left `<p>CACHE-CHECK-129392</p>` stored and published, 2026-10-13).
_ABOUT_TEST_MARKERS = re.compile(
    r"\s*<p>\s*(?:CACHE-CHECK|DRAFT-ONLY|PREVIEW-ONLY|VERSION-[12])-129392\s*</p>\s*"
)


def _clean_content(admin) -> str:
    """The page record's Page Content (EN) as stored now, minus any test
    marker paragraph -- what `_put_back_content()` writes back."""
    admin.open_page_record_in("en")
    return _ABOUT_TEST_MARKERS.sub("\n", admin.page_content_html("en")).rstrip() + "\n"


def _draft_with_marker(admin, marker: str, tc: str, clean_html: str) -> set:
    """Unpublish (if Published) and Save as Draft the page record with
    `<p>marker</p>` appended to `clean_html` via CKEditor setData. Asserts the
    marker was stored; returns the NON-PUBLIC states the record may then read.

    Live 2026-10-14: reopening right after the Unpublish click opened the
    record still Published (Save as Draft disabled -> 30 s click timeout), so
    the Unpublish is now proved on a fresh read before the form is reopened.
    The site's own save code turns an Unpublished record into a Draft before
    a Save as Draft PUT (`/o/qc-object-status/edit-as-draft`, ADO 148039), so
    after the save the record reads Draft -- or Unpublished if that move did
    not happen; either is a non-public state, and the exact one is attached."""
    authoring = admin.open_page_record_in("en")
    block_live_singleton_write(PAGE_RECORD, "unpublish + Save as Draft of Page Content")
    if authoring.current_status() == STATUS_PUBLISHED:
        log_live_write(PAGE_RECORD, "<workflow>", STATUS_UNPUBLISHED, tc, action="unpublish",
                       note="Unpublish to edit as draft (re-published in finally)")
        authoring.unpublish_to_edit_as_draft()
        authoring.wait_for_status(STATUS_UNPUBLISHED, timeout=60)
    authoring = admin.open_page_record_in("en")
    admin.set_page_content_html(_with_content(clean_html, f"<p>{marker}</p>"), "en")
    log_live_write(PAGE_RECORD, "Page Content (EN)", f"<current content> + <p>{marker}</p>", tc,
                   action="save-draft", note="Save as Draft (content put back in finally)")
    authoring.save_as_draft()
    stored = _wait_stored(admin, lambda: marker in admin.page_content_html("en"), True)
    assert stored is True, f"precondition: Save as Draft did not store {marker!r}"
    return {STATUS_DRAFT, STATUS_UNPUBLISHED}


def _put_back_content(admin, clean_html, marker: str, tc: str) -> None:
    """`finally`: the Page Content (EN) read before the test (minus test
    markers) written back with Save as Draft, so `_page_end_published` then
    re-publishes the real content, not the marker. Never raises."""
    if clean_html is None:
        return
    try:
        authoring = admin.open_page_record_in("en")
        current = admin.page_content_html("en")
        if not _ABOUT_TEST_MARKERS.search(current):
            return
        block_live_singleton_write(PAGE_RECORD, "put back the Page Content read before the test")
        if authoring.current_status() == STATUS_PUBLISHED:
            log_live_write(PAGE_RECORD, "<workflow>", STATUS_UNPUBLISHED, tc, action="unpublish",
                           note="Unpublish to put back the content (re-published in finally)")
            authoring.unpublish_to_edit_as_draft()
            authoring = admin.open_page_record_in("en")
        admin.set_page_content_html(clean_html, "en")
        log_live_write(PAGE_RECORD, "Page Content (EN)", "<the content read before the test, test markers removed>",
                       tc, action="save-draft", note=f"put back after {marker}")
        authoring.save_as_draft()
        ok = _wait_stored(admin, lambda: not _ABOUT_TEST_MARKERS.search(admin.page_content_html("en")), True)
        _attach("content put back", {"ok": ok})
    except Exception as exc:  # noqa: BLE001 -- cleanup never masks the result
        _attach("content put back FAILED -- fix by hand", repr(exc))

# ─────────────────────────────────────────────────────────────────────────
@_case(
    "134692",
    "Verify that Preview renders unpublished About Qatar Chamber content without publishing it",
    "Preview renders draft content",
    allure.severity_level.NORMAL,
    (pytest.mark.functional_high, pytest.mark.regression, pytest.mark.workflow),
)
def test_about_cp_134692_preview_renders_unpublished_content(page, browser):
    # Preview is a STAFF surface (guide section 6: it renders drafts to
    # signed-in staff), so it is read through the AUTHENTICATED `page`,
    # while public visibility is read through a fresh anonymous context --
    # standards.md's mandatory logged-out rule. That split is the case.
    #
    # FIX PASS 5 (2026-10-14): r2 previewed a draft that never held the
    # marker (`fill_rich_text` did not store it). Live 2026-10-14 the row's
    # Preview link (`about-us?qcPreview=...`) renders the record's full body
    # for staff (the Published record's own CACHE-CHECK paragraph was there).
    # Now the marker is written with setData and proved stored BEFORE the
    # preview; status expectations follow the 7-state workflow; the public
    # half is gated on the page answering 200 (BLOCKED otherwise).
    admin = AboutQatarChamberAdminPage(page)
    marker = "PREVIEW-ONLY-129392"

    with _page_end_published(admin, "134692"):
        anon_context = new_context(browser, use_auth_state=False)
        about = AboutQatarChamberPage(anon_context.new_page())
        clean_html = None
        try:
            with allure.step(f"Add '{marker}' to Page Content (EN), Save as draft, then Preview"):
                clean_html = _clean_content(admin)
                expected_status = _draft_with_marker(admin, marker, "134692", clean_html)
                status_before_preview = admin.open_page_record_in("en").current_status()
                entries = admin.open_page_entries_list()
                # Code-keyed: this object's Entry column renders its external
                # reference code, not a title (see the admin Page Object's note).
                preview_url = entries.row_preview_url_by_code(ABOUT_PAGE_ENTRY_CODE)
                banner_text = entries.preview_banner_text(preview_url)
                preview_text = entries.rendered_body_text()
                _attach("preview", {"url": preview_url, "banner": banner_text, "text": preview_text[:600]})

            with allure.step("Confirm the record status is unchanged after Preview"):
                status_after_preview = admin.open_page_record_in("en").current_status()

            with allure.step("Confirm the public page (fresh anonymous context) does not contain the paragraph"):
                public_status = about.page_http_status()
                about.open_en_tolerant()
                public_text = about.page_body_text()
                _attach("public page", {"http_status": public_status, "text": public_text[:400]})

            assert status_before_preview in expected_status, (
                f"the draft reads {status_before_preview!r}, expected one of {sorted(expected_status)}"
            )
            assert "visitors do not see it" in banner_text.lower() or "draft" in banner_text.lower(), (
                f"expected the preview banner to disclose an unpublished record; got {banner_text[:120]!r}"
            )
            assert marker in preview_text, (
                "expected Preview to render the unpublished draft content"
            )
            assert status_after_preview == status_before_preview, (
                f"Preview changed the record status to {status_after_preview!r}"
            )
            if public_status != 200:
                pytest.fail(
                    f"BLOCKED -- the public About page /web/qatar-chamber/about-us answers HTTP "
                    f"{public_status} to an anonymous visitor, so 'previewing must not publish' "
                    "cannot be observed publicly. Staff half passed: Preview rendered "
                    f"{marker!r} and the record stayed {status_after_preview!r}.",
                    pytrace=False,
                )
            assert marker not in public_text, (
                f"DRAFT LEAK: previewing must not publish -- '{marker}' appears on the public page"
            )
        finally:
            _put_back_content(admin, clean_html, marker, "134692")
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001
                pass

# ─────────────────────────────────────────────────────────────────────────
@_case(
    "134694",
    "Verify that a hyperlink configured in the CMS opens its destination from the public page",
    "Configured hyperlink resolves on the public page",
    allure.severity_level.NORMAL,
    (pytest.mark.functional_high, pytest.mark.regression, pytest.mark.redirect, pytest.mark.web),
)
def test_about_cp_134694_configured_hyperlink_opens_its_destination(page, browser):
    # DISCLOSED MECHANISM CHANGE: the case says to configure the hyperlink
    # "inside Page Content (EN)". On this object the hyperlink is NOT authored
    # inside the rich text -- AboutQatarChamberPage has DEDICATED
    # `Hyperlink Title` + `Hyperlink URL` fields (guide section 23:
    # "hyperlinkTitle + hyperlinkUrl -- the call-to-action button label +
    # link"), confirmed live, and they render as the page's CTA button. The
    # dedicated fields are driven here and the CTA asserted; the case should
    # be reworded -- escalated to the QA Manager.
    admin = AboutQatarChamberAdminPage(page)
    target_label = "Qatar Chamber Services"
    target_url = "https://www.qatarchamber.com"

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the record"):
            authoring = admin.open_page_record()

        with allure.step(f"Configure the hyperlink as {target_label!r} -> {target_url} and publish"):
            block_live_singleton_write(PAGE_RECORD, "publish of Hyperlink Title / URL")
            if authoring.current_status() == STATUS_PUBLISHED:
                authoring.unpublish_to_edit_as_draft()
            authoring.fill_text(admin.HYPERLINK_TITLE_LABEL, target_label)
            authoring.fill_text(admin.HYPERLINK_URL_LABEL, target_url)
            authoring.submit_for_publishing()

        with allure.step("Open the public page and locate the link"):
            about = AboutQatarChamberPage(anon_page)

            def _cta_updated() -> bool:
                about.open_en()
                return about.cta_label_text().strip() == target_label

            _reflects_public(
                _cta_updated,
                message="the public page never reflected the configured hyperlink",
            )
            cta_visible = about.is_cta_visible()
            cta_label = about.cta_label_text().strip()
            cta_href = about.cta_href() or ""

        assert cta_visible, "expected the configured hyperlink to render as a clickable anchor"
        assert cta_label == target_label
        assert cta_href.rstrip("/") == target_url.rstrip("/"), (
            f"expected the link to point at {target_url}; got {cta_href!r}"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass

# ─────────────────────────────────────────────────────────────────────────
@_case(
    "134697",
    "Verify that replacing the Hero Banner image updates the image shown on the website",
    "Hero Banner image replacement",
    allure.severity_level.NORMAL,
    (pytest.mark.functional_high, pytest.mark.regression, pytest.mark.web),
)
def test_about_cp_134697_replacing_the_hero_banner_updates_the_website(page, browser, tmp_path):
    # Drives **AboutHeroBanner** (pageKey=about-us), NOT the page object's
    # legacy `Hero Banner Image` field -- see the module docstring's trap
    # note. A replace selects the new file straight over the existing one
    # (no remove/two-phase step; that is only needed for a first-time set).
    # DISCLOSED: the case's literal `hero-new.jpg` is not the target -- an
    # existing Documents & Media file is picked via Select File, per the
    # QA Manager's instruction for this surface.
    # TEST_OWNED: the live `about-us` row (incl. its banner bytes) is in the
    # module snapshot and restored ONCE at module end -- no per-test restore.
    admin = AboutQatarChamberAdminPage(page)
    replacement_file = "qc-footer-facet-left.png"

    with _hero_end_published(admin, "134697"):
        anon_context = new_context(browser, use_auth_state=False)
        anon_page = anon_context.new_page()

        try:
            with allure.step("Open the AboutHeroBanner record for pageKey=about-us"):
                authoring = admin.open_hero_banner_record()
                assert authoring.field_value(admin.PAGE_KEY_LABEL) == "about-us", (
                    "opened the wrong AboutHeroBanner row"
                )
                original_filename = authoring.current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL)
                assert original_filename, (
                    "precondition failed: this case needs a record that ALREADY has a "
                    "Hero Banner image set"
                )

            with allure.step("Capture the image the public hero currently serves"):
                about = AboutQatarChamberPage(anon_page)
                about.open_en()
                hero_before = about.hero_media_background_image()

            with allure.step("Replace the Banner Image and publish"):
                block_live_singleton_write(HERO_RECORD, "replace + publish the Banner Image")
                if authoring.current_status() == STATUS_PUBLISHED:
                    log_live_write(HERO_RECORD, "<workflow>", STATUS_UNPUBLISHED, "134697", action="unpublish",
                                   note="Unpublish to edit as draft (re-published in finally)")
                    authoring.unpublish_to_edit_as_draft()
                authoring.select_existing_file(
                    admin.BANNER_IMAGE_UPLOAD_LABEL,
                    replacement_file,
                    folder="QC Footer Social Icons",
                )
                log_live_write(HERO_RECORD, admin.BANNER_IMAGE_UPLOAD_LABEL, replacement_file, "134697",
                               action="upload", note=f"replaces {original_filename!r}; then Submit for Publishing")
                authoring.submit_for_publishing()

            with allure.step("Open the public page after the standard cache refresh and read the hero image"):
                def _hero_replaced() -> bool:
                    about.open_en()
                    return "qc-footer-facet-left" in about.hero_media_background_image()

                _reflects_public(
                    _hero_replaced,
                    message="the public hero never reflected the replacement image",
                )
                hero_after = about.hero_media_background_image()

            assert "qc-footer-facet-left" in hero_after, (
                f"expected the hero to serve {replacement_file!r}; got {hero_after[:160]!r}"
            )
            assert hero_after != hero_before, (
                "expected the hero to STOP serving the previous image"
            )
        finally:
            try:
                anon_context.close()
            except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
                pass


# ─────────────────────────────────────────────────────────────────────────
@_case(
    "134698",
    "Verify that uploading a Hero Banner image for the first time publishes it to the website",
    "Hero Banner image first upload",
    allure.severity_level.NORMAL,
    (pytest.mark.functional_high, pytest.mark.regression, pytest.mark.web),
)
def test_about_cp_134698_uploading_a_hero_banner_first_time_publishes_it(page, browser, tmp_path):
    # Drives **AboutHeroBanner** (pageKey=about-us) -- see the trap note.
    #
    # This record already HAS a banner, so the case's "no Hero Banner image
    # set" precondition is reached deliberately and reversibly: the current
    # file is removed and saved (phase 1), which is the confirmed-live
    # sequence -- a remove + set + publish in one unsaved form session does
    # NOT persist (see ObjectAuthoringPage.remove_current_file()'s
    # docstring). Phase 2 re-opens fresh, sets the new image and publishes.
    # The original bytes, alt text and status are in the module snapshot and
    # restored ONCE at module end -- no per-test restore.
    #
    # DISCLOSED: the case's alt-text clause ("Qatar Chamber headquarters") is
    # asserted against AboutHeroBanner's OWN `Banner Image Alt Text` field --
    # that is where a hero alt text lives on this surface (the page object's
    # `Hero Banner Alt Text` belongs to the legacy, unrendered field).
    admin = AboutQatarChamberAdminPage(page)
    new_file = "qc-footer-facet-right.png"
    target_alt = "Qatar Chamber headquarters"

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the AboutHeroBanner record and read its current Banner Image"):
            authoring = admin.open_hero_banner_record()
            original_filename = authoring.current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL)

        with allure.step("Remove the current banner and save (phase 1) to reach the empty-field precondition"):
            block_live_singleton_write(HERO_RECORD, "remove + save, then publish a new Banner Image")
            if authoring.current_status() == STATUS_PUBLISHED:
                authoring.unpublish_to_edit_as_draft()
            if original_filename:
                authoring.remove_current_file(admin.BANNER_IMAGE_UPLOAD_LABEL)
                authoring.save_as_draft()

        with allure.step("Re-open fresh, upload the Hero Banner image, set its alt text, and publish (phase 2)"):
            authoring = admin.open_hero_banner_record()
            assert authoring.current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL) == "", (
                "expected the Banner Image field to be genuinely empty after the phase-1 remove+save"
            )
            authoring.select_existing_file(
                admin.BANNER_IMAGE_UPLOAD_LABEL,
                new_file,
                folder="QC Footer Social Icons",
            )
            authoring.fill_text(admin.BANNER_IMAGE_ALT_TEXT_LABEL, target_alt)
            authoring.submit_for_publishing()
            authoring = admin.open_hero_banner_record()

        with allure.step("Open the public page after the standard cache refresh and read the hero"):
            about = AboutQatarChamberPage(anon_page)

            def _hero_published() -> bool:
                about.open_en()
                return "qc-footer-facet-right" in about.hero_media_background_image()

            _reflects_public(
                _hero_published,
                message="the public hero never reflected the newly-uploaded image",
            )
            hero_after = about.hero_media_background_image()
            hero_visible = about.is_hero_visible()

        assert authoring.current_status() == STATUS_PUBLISHED
        assert new_file in authoring.current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL)
        assert authoring.field_value(admin.BANNER_IMAGE_ALT_TEXT_LABEL) == target_alt
        assert hero_visible, "expected the hero banner to render on the public page"
        assert "qc-footer-facet-right" in hero_after, (
            f"expected the hero to serve {new_file!r}; got {hero_after[:160]!r}"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass


# ═════════════════════════════════════════════════════════════════════════
# BATCH 2 -- 2026-10-12: the remaining 29 PBI 129392 cases.
# Scripted OFFLINE (another engineer held the single qcdev browser session):
# no locator below was read live on THIS object; the uncertain ones carry a
# `# VERIFY-LIVE:` note on AboutQatarChamberAdminPage.
#
# HISTORY -- superseded 2026-10-13 (no singleton writes; fixture + gate not
# wired). TEST_OWNED discipline for the singleton (QCDEMO-129392-...-ENTRY) and the
# live AboutHeroBanner `about-us` row -- restore ONCE per run (2026-10-12):
#   1. `_singleton_baseline` (module fixture, about_singleton.py) heals from
#      an interrupted run's snapshot (incl. the old dirty.json marker), then
#      captures the FULL state -- text EN/AR, Page Content HTML EN/AR
#      (CKEditor getData, never typed), Content Image + Banner Image bytes,
#      Active Status, workflow status -- to
#      reports/backups/129392_about_qatar_chamber_<stamp>/ BEFORE any test.
#   2. Per test, `_singleton_gate` only normalises the page record's STATUS
#      back to Published; tests read current values via `_about_current()`.
#   3. After the last ABOUT_XDIST_GROUP test the fixture restores both records
#      once and RE-READS them; a mismatch is attached and raised.
#      Killed run: python tools/restore_singleton.py --pbi 129392
# Negative cases use the form's Publish control (status=0) -- Save as Draft
# skips required-field validation by design, so it cannot prove a refusal.
# AboutHeroBanner cases run on DISPOSABLE `QCTEST-<tc>-HERO` rows, deleted
# by exact title -- the live `about-us` row is never written by them.
# ═════════════════════════════════════════════════════════════════════════
from cms.pages.about_qatar_chamber.about_qatar_chamber_admin_page import (
    ABOUT_PAGE_ENTRY_CODE,
    ABOUT_PAGE_SLUG,
)
from cms.pages.control_panel.login_page import CmsLoginPage
# About's own helpers -- never imported from another feature's test module.
from cms.tests.about_qatar_chamber.about_helpers import (
    _FormProbe,
    _attach,
    _attempt_upload,
    _create_hero,
    _fixture,
    _hero_key,
    _hero_reset,
    _open_hero,
    _publish_edit,
    _role_session,
)
from tools.fixture_factory import make_bmp, make_gif, make_jpg, make_png
from cms.tests.about_qatar_chamber.about_singleton import image_matches as _image_matches
from cms.tests.about_qatar_chamber.about_singleton import norm_html as _norm_html
from cms.tests.about_qatar_chamber.about_singleton import read_page_form as _read_open_form

ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_MEMBER = "Site Member"
ONE_MB = 1024 * 1024
SAVE_SETTLE_TIMEOUT = 90.0
PUBLIC_REFLECT_FIELD_TIMEOUT = 120.0
ABOUT_TIMEOUT = pytest.mark.timeout(300)

# NOT WIRED (user decision 2026-10-13): `module_baseline_fixture(build_baseline)`
# and `singleton_gate("about_qatar_chamber_129392")` both write to the live
# records (gate: approve/publish before every test; fixture: module-end
# restore). No test writes to them any more, so neither is attached.


# ---- Runtime state of the singleton --------------------------------------
# The capture / restore engine lives in about_singleton.py (module-level
# baseline, restored ONCE at module end). Tests only read current values.
def _about_current(admin) -> dict:
    """RUNTIME read of the page record -- the values a test compares against.
    Restores nothing and assumes no original (user decision 2026-10-12)."""
    state = _read_open_form(admin, admin.open_page_record_in("en"))
    _attach("current values (runtime read)", state)
    return state


def _wait_stored(admin, reader, expected, timeout: float = SAVE_SETTLE_TIMEOUT):
    seen = {"value": None}

    def _check() -> bool:
        admin.open_page_record_in("en")
        seen["value"] = reader()
        return seen["value"] == expected

    try:
        wait_until(_check, timeout=timeout, poll=5)
    except Exception:  # noqa: BLE001 -- the caller asserts on the value
        pass
    return seen["value"]


def _stored_now(admin, reader):
    admin.open_page_record_in("en")
    return reader()


def _close(*contexts) -> None:
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001 -- cleanup never masks the result
            pass


def _public_poll(about, check, timeout: float = PUBLIC_REFLECT_FIELD_TIMEOUT) -> bool:
    """Reloads the public page as the anonymous visitor until `check()`."""
    def _ok() -> bool:
        about.open_en_tolerant()
        return bool(check())

    try:
        _reflects_public(_ok, timeout=timeout, poll=5)
        return True
    except Exception:  # noqa: BLE001 -- the caller asserts with evidence
        return False


# ---- Case shapes (one per field type) ------------------------------------
def _case_valid_text(page, tc: str, key: str, locale: str, value: str) -> None:
    admin = AboutQatarChamberAdminPage(page)
    with allure.step("Open the About Qatar Chamber page record in Liferay CMS"):
        authoring = admin.open_page_record_in("en")
        assert admin.page_has_edit_form(), "the page record did not open in an editable form"
    block_live_singleton_write(PAGE_RECORD, f"save of {key} ({locale.upper()}) = {value!r}")
    if admin.page_text(key, locale) == value:
        # Restore-once (2026-10-12): state carries over between cases.
        interim = f"QCTEST-{tc} interim"
        with allure.step(f"Interim write: {key} ({locale.upper()}) already reads {value!r}"):
            _attach("note", "field already held the case's value; interim QCTEST value saved first")
            admin.fill_page_text(key, interim, locale)
            _publish_edit(admin, authoring)
            assert _wait_stored(admin, lambda: admin.page_text(key, locale), interim) == interim, (
                "precondition: the interim value did not persist"
            )
            authoring = admin.open_page_record_in("en")
    with allure.step(f"Enter {value!r} ({locale.upper()}) and click Save (Publish on this record)"):
        admin.fill_page_text(key, value, locale)
        native = admin.page_text_validation_message(key, locale)
        said = _publish_edit(admin, authoring)
        _attach("save outcome", said)
    with allure.step("Reload the record"):
        stored = _wait_stored(admin, lambda: admin.page_text(key, locale), value)
    assert native == "", f"the value raised a validation error: {native!r}"
    assert not said["refusal"], f"the save was refused: {said['refusal']!r}"
    assert stored == value, f"stored value is {stored!r}, expected {value!r}"


def _case_rejected_text(page, tc: str, key: str, locale: str, value: str,
                        ui_locales=("en",)) -> None:
    """Invalid/empty value: the save must be blocked and nothing persisted.
    Message wording is attached, not asserted (bug-rules: wording != bug)."""
    admin = AboutQatarChamberAdminPage(page)
    current = _about_current(admin)
    original = current[f"{key}_{locale}"]
    attempts = []
    for ui in ui_locales:
        with allure.step(f"[{ui.upper()} interface] Open the record, enter {value!r} and click Save"):
            authoring = admin.open_page_record_in(ui)
            admin.fill_page_text(key, value, locale)
            native = admin.page_text_validation_message(key, locale)
            said = _publish_edit(admin, authoring)
        with allure.step(f"[{ui.upper()} interface] Reload the record"):
            stored = _stored_now(admin, lambda: admin.page_text(key, locale))
            status = admin.open_page_record_in("en").current_status()
        attempts.append({"ui": ui, "native": native, **said, "stored": stored, "status": status})
        # 2026-10-13: stop before the next interface's click if this one went through.
        stop_unless_refused(
            stored == original and status == current["workflow"], PAGE_RECORD,
            f"[{ui.upper()} UI] Save with {key} ({locale.upper()}) = {value!r}",
            {"native": native, "refusal": said["refusal"], "stored": stored, "status": status})
    _attach("observed messages per interface language (recorded, not asserted)",
            "\n".join(repr(a) for a in attempts))
    for attempt in attempts:
        assert attempt["stored"] == original, (
            f"[{attempt['ui']} UI] the save was NOT blocked: the field now stores "
            f"{attempt['stored']!r} (was {original!r})"
        )
        assert attempt["native"] or attempt["refusal"], (
            f"[{attempt['ui']} UI] nothing was stored but no validation message was shown"
        )
        assert attempt["status"] == current["workflow"], (
            f"[{attempt['ui']} UI] the publication state changed to {attempt['status']!r}"
        )


def _case_valid_rich(page, tc: str, locale: str, html: str, must_keep: tuple) -> dict:
    admin = AboutQatarChamberAdminPage(page)
    with allure.step(f"Enter the Page Content ({locale.upper()}) body and click Save"):
        authoring = admin.open_page_record_in("en")
        admin.set_page_content_html(html, locale)
        block_live_singleton_write(PAGE_RECORD, f"save of Page Content ({locale.upper()})")
        said = _publish_edit(admin, authoring)
        _attach("save outcome", said)
    with allure.step("Reload the record"):
        stored = _wait_stored(admin, lambda: all(t in admin.page_content_html(locale) for t in must_keep), True)
        stored_html = admin.page_content_html(locale)
        direction = admin.page_content_direction(locale) if locale == "ar" else ""
    _attach("stored html", stored_html)
    assert not said["refusal"], f"the save was refused: {said['refusal']!r}"
    assert stored is True, f"Page Content ({locale.upper()}) lost authored parts: {stored_html[:400]!r}"
    return {"direction": direction}


def _case_rejected_rich(page, tc: str, locale: str) -> None:
    admin = AboutQatarChamberAdminPage(page)
    current = _about_current(admin)
    with allure.step(f"Clear the Page Content ({locale.upper()}) editor completely and click Save"):
        authoring = admin.open_page_record_in("en")
        admin.set_page_content_html("", locale)
        said = _publish_edit(admin, authoring)
        _attach("save outcome (wording recorded, not asserted)", said)
    with allure.step("Reload the record"):
        stored = _stored_now(admin, lambda: admin.page_content_html(locale))
    stop_unless_refused(_norm_html(stored) == _norm_html(current[f"content_{locale}"]), PAGE_RECORD,
                        f"Save with an empty Page Content ({locale.upper()})",
                        {"said": said, "stored": stored[:200]})
    assert _norm_html(stored) == _norm_html(current[f"content_{locale}"]), (
        f"the save was NOT blocked: Page Content ({locale.upper()}) now stores {stored[:200]!r}"
    )


def _with_content(current_html: str, extra_html: str) -> str:
    return (current_html or "") + extra_html


# ── Public rendering ─────────────────────────────────────────────────────
@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Rich text renders on the public page")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the page rich text renders headings, paragraphs, bullet lists, numbered lists, and inline links")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.web
@pytest.mark.uat
@pytest.mark.pbi_129392
@pytest.mark.tc_134675
@pytest.mark.traceability("134675")
@allure.label("pbi", "129392")
@allure.label("testcase", "134675")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134675_rich_text_renders_headings_lists_and_links(page, browser):
    admin = AboutQatarChamberAdminPage(page)
    heading = "QCTEST-134675 Heading"
    html = (
        f"<h2>{heading}</h2><p>QCTEST-134675 paragraph.</p>"
        "<ul><li>Bullet one</li><li>Bullet two</li><li>Bullet three</li></ul>"
        "<ol><li>Step one</li><li>Step two</li><li>Step three</li></ol>"
        '<p><a href="https://www.qatarchamber.com">Qatar Chamber</a></p>'
    )
    anon = new_context(browser, use_auth_state=False)
    about = AboutQatarChamberPage(anon.new_page())
    try:
        with allure.step("Set Page Content (EN) to heading + paragraph + 3 bullets + 3 numbered + one link, publish"):
            authoring = admin.open_page_record_in("en")
            admin.set_page_content_html(html, "en")
            block_live_singleton_write(PAGE_RECORD, "publish of rich-text Page Content (EN)")
            said = _publish_edit(admin, authoring)
            _attach("publish outcome", said)
        with allure.step("Open the public page in English and inspect the content block"):
            served = _public_poll(about, lambda: about.html_text_contains(heading))
            headings = about.section_heading_order()
            bullets = about.bullet_item_count()
            numbered = about.numbered_item_count()
            links = about.content_link_hrefs()
        _attach("rendered", {"headings": headings, "ul_items": bullets, "ol_items": numbered, "links": links})
        assert served, "the published content never reached the public page"
        assert heading in headings, f"the heading did not render as a heading: {headings}"
        assert about.html_text_contains("QCTEST-134675 paragraph."), "the paragraph did not render"
        assert bullets == 3, f"expected 3 bulleted items, found {bullets}"
        assert numbered == 3, f"expected 3 numbered items, found {numbered}"
        assert any((h or "").rstrip("/") == "https://www.qatarchamber.com" for h in links), (
            f"no anchor points to https://www.qatarchamber.com: {links}"
        )
    finally:
        _close(anon)


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Content Image alt text")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Content Image exposes the alt text configured in the CMS")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.web
@pytest.mark.uat
@pytest.mark.pbi_129392
@pytest.mark.tc_134676
@pytest.mark.traceability("134676")
@allure.label("pbi", "129392")
@allure.label("testcase", "134676")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134676_content_image_exposes_the_configured_alt_text(page, browser):
    admin = AboutQatarChamberAdminPage(page)
    expected = "Qatar Chamber headquarters building"
    anon = new_context(browser, use_auth_state=False)
    about = AboutQatarChamberPage(anon.new_page())
    try:
        with allure.step(f"Set Content Image Alt Text (EN) to {expected!r} and publish"):
            authoring = admin.open_page_record_in("en")
            admin.fill_page_text("alt_text", expected, "en")
            block_live_singleton_write(PAGE_RECORD, "publish of Content Image Alt Text (EN)")
            said = _publish_edit(admin, authoring)
            stored = _wait_stored(admin, lambda: admin.page_text("alt_text", "en"), expected)
            _attach("publish outcome", said)
        with allure.step("Open the public page in English and inspect the Content Image alt"):
            _public_poll(about, lambda: about.media_img_alt() == expected)
            alt = about.media_img_alt()
            visible = about.media_img_box() is not None
        assert stored == expected, f"the alt text was not saved (stored {stored!r})"
        assert visible, "the Content Image is not visible on the public page"
        assert alt == expected, f"the public Content Image alt is {alt!r}, expected {expected!r}"
    finally:
        _close(anon)


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Section order")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that all published content sections appear on the page in the configured order")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.web
@pytest.mark.uat
@pytest.mark.pbi_129392
@pytest.mark.tc_134679
@pytest.mark.traceability("134679")
@allure.label("pbi", "129392")
@allure.label("testcase", "134679")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134679_sections_render_in_the_configured_order(page, browser):
    admin = AboutQatarChamberAdminPage(page)
    sections = ("The Voice of Qatar's Private Sector", "The Chamber's competences", "Chamber Constituents:")
    html = "".join(f"<h2>{s}</h2><p>QCTEST-134679 section {i}.</p>" for i, s in enumerate(sections, 1))
    anon = new_context(browser, use_auth_state=False)
    about = AboutQatarChamberPage(anon.new_page())
    try:
        with allure.step("Configure Page Content (EN) with the three sections in order and publish"):
            authoring = admin.open_page_record_in("en")
            admin.set_page_content_html(html, "en")
            block_live_singleton_write(PAGE_RECORD, "publish of three ordered sections")
            said = _publish_edit(admin, authoring)
            _attach("publish outcome", said)
        with allure.step("Open the public page and record the section order top to bottom"):
            _public_poll(about, lambda: about.html_text_contains("QCTEST-134679 section 3."))
            order = [h for h in about.section_heading_order() if h in sections]
        _attach("rendered order", order)
        assert order == list(sections), f"sections rendered as {order}, expected {list(sections)}"
    finally:
        _close(anon)


# ── Roles ────────────────────────────────────────────────────────────────
@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Site Content Editor permissions")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Editor can create, edit, preview, publish, and unpublish the About Qatar Chamber page")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_129392
@pytest.mark.tc_134684
@pytest.mark.traceability("134684")
@allure.label("pbi", "129392")
@allure.label("testcase", "134684")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134684_editor_can_edit_preview_publish_and_unpublish(page, browser):
    # Signed in as the real Site Content Editor (never TEST_USER). DISCLOSED:
    # "create" is not reachable on a singleton (its manage page holds one
    # record and offers no Add); edit/preview/publish/unpublish are driven.
    # Row Unpublish lands on STATUS_UNPUBLISHED, its own state (not Draft).
    # `page` (TEST_USER) is used only by the gate's status precondition.
    context, editor_page = _role_session(browser, ROLE_EDITOR)
    editor = AboutQatarChamberAdminPage(editor_page)
    problems = []
    try:
        with allure.step("Sign in as Site Content Editor and open the page record"):
            if not CmsLoginPage(editor_page).has_admin_toolbar():
                problems.append("the Editor session has no CMS toolbar after sign-in")
            editor.open_page_entries_list()
            actions = editor.page_row_actions()
            authoring = editor.open_page_record_in("en")
            controls = editor.publish_control_state()
            _attach("controls", {"row": actions, "form": controls})
            if not (controls["publish"][0] and controls["publish"][1]):
                problems.append(f"the Publish control is missing/disabled: {controls['publish']}")
        with allure.step("Edit Page Title (EN) to 'About Qatar Chamber' and Publish"):
            editor.fill_page_text("page_title", "About Qatar Chamber", "en")
            block_live_singleton_write(PAGE_RECORD, f"Editor publish / unpublish; problems so far: {problems}")
            said = _publish_edit(editor, authoring)
            if said["refusal"] or editor.ACCESS_DENIED_EN in editor.body_text():
                problems.append(f"the Editor's publish was refused: {said!r}")
            status = editor.open_page_record_in("en").current_status()
            if status != STATUS_PUBLISHED:
                problems.append(f"status after the Editor's publish is {status!r}")
        with allure.step("Preview the record"):
            entries = editor.open_page_entries_list()
            banner = entries.preview_banner_text(entries.row_preview_url_by_code(ABOUT_PAGE_ENTRY_CODE))
            if editor.ACCESS_DENIED_EN in editor.body_text():
                problems.append("Access Denied shown on Preview")
            _attach("preview banner", banner)
        with allure.step("Unpublish the record (row action)"):
            entries = editor.open_page_entries_list()
            entries.unpublish_entry(ABOUT_PAGE_ENTRY_CODE)
            row_status = editor.open_page_entries_list().row_status_text_by_code(ABOUT_PAGE_ENTRY_CODE)
            if row_status != STATUS_UNPUBLISHED:
                problems.append(f"status after the Editor's unpublish is {row_status!r}")
            if editor.ACCESS_DENIED_EN in editor.body_text():
                problems.append("Access Denied shown on Unpublish")
        assert not problems, "Site Content Editor could not manage the page:\n" + "\n".join(problems)
    finally:
        _close(context)


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Site Content Author permissions")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Author can view and update assigned About Qatar Chamber page content")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129392
@pytest.mark.tc_134685
@pytest.mark.traceability("134685")
@allure.label("pbi", "129392")
@allure.label("testcase", "134685")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134685_author_can_view_and_update_page_content(page, browser):
    # As the real Site Content Author. An Author's save lands in Pending
    # Review (workflow); the next test's status precondition approves it,
    # and the module-end restore puts the content back.
    admin = AboutQatarChamberAdminPage(page)
    current = _about_current(admin)
    marker = "QCTEST-134685 author update"
    context, author_page = _role_session(browser, ROLE_AUTHOR)
    author = AboutQatarChamberAdminPage(author_page)
    with _page_end_published(admin, "134685"):
        try:
            with allure.step("Open the page record as Author"):
                authoring = author.open_page_record_in("en")
                editable = author.page_has_edit_form()
                controls = author.publish_control_state()
                denied_on_open = author.ACCESS_DENIED_EN in author.body_text()
                _attach("Author controls", {"form": controls, "denied": denied_on_open})
            with allure.step("Update Page Content (EN) and save"):
                said = {}
                if any(present and enabled for present, enabled, _ in controls.values()):
                    author.set_page_content_html(_with_content(current["content_en"], f"<p>{marker}</p>"), "en")
                    selector = author.SAVE_DRAFT_SUBMIT if controls["draft"][1] else author.PUBLISH_SUBMIT
                    block_live_singleton_write(PAGE_RECORD, f"Author's Page Content save; controls {controls}")
                    log_live_write(PAGE_RECORD, "Page Content (EN)", f"<current content> + <p>{marker}</p>", "134685",
                                   action="save-draft" if selector == author.SAVE_DRAFT_SUBMIT else "publish",
                                   note=f"Site Content Author save via {selector!r} (lands short of Published; "
                                        "re-published in finally)")
                    authoring.submit_via(selector)
                    said = {"denied": author.ACCESS_DENIED_EN in author.body_text()}
                stored = _stored_now(author, lambda: author.page_content_html("en"))
            assert editable, "the page record did not open in editable mode for the Author"
            # Live 2026-10-13: on the PUBLISHED record the Author is refused by
            # design ("Only a Content Editor can change a record once it has
            # reached the website"), fields + both submit buttons disabled.
            assert not denied_on_open, (
                "FINDING -- the Site Content Author cannot update the PUBLISHED About page; the case "
                f"expects view + update. The product shows: {authoring.access_denied_note()!r}; "
                f"submit controls {controls}")
            assert said, f"no enabled save control for the Author: {controls}"
            assert not said["denied"], "Access Denied after the Author's save"
            assert marker in stored, "the Author's Page Content change was not saved"
        finally:
            _close(context)


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Site Content Author cannot publish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Author cannot publish the About Qatar Chamber page")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.workflow
@pytest.mark.pbi_129392
@pytest.mark.tc_134686
@pytest.mark.traceability("134686")
@allure.label("pbi", "129392")
@allure.label("testcase", "134686")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134686_author_cannot_publish_the_page(page, browser):
    admin = AboutQatarChamberAdminPage(page)
    current = _about_current(admin)
    context, author_page = _role_session(browser, ROLE_AUTHOR)
    author = AboutQatarChamberAdminPage(author_page)
    try:
        with allure.step("Open the page record as Author and locate the publish control"):
            author.open_page_entries_list()
            row_attrs = author.page_row_action_attrs()
            author.open_page_record_in("en")
            controls = author.publish_control_state()
            body = author.body_text()
            _attach("Author controls", {"form": controls, "row attrs": row_attrs})
        with allure.step("Attempt to publish the page"):
            present, enabled, label = controls["publish"]
            # 2026-10-13: an enabled publish control IS the finding -- never clicked.
            stop_unless_refused(not (present and enabled), PAGE_RECORD,
                                "the Author's publish control (offered enabled, not clicked)",
                                controls["publish"])
            status_after = admin.open_page_record_in("en").current_status()
        assert not (enabled and label == "Publish"), f"an enabled 'Publish' is offered to the Author: {controls}"
        for action in ("data-qc-oel-publish", "data-qc-oel-approve", "data-qc-oel-unpublish"):
            assert action not in row_attrs, f"the page row offers {action!r} to the Author"
        assert status_after == current["workflow"], f"the publication state changed to {status_after!r}"
        assert author.ACCESS_DENIED_EN in body, "the exact Access Denied message is not shown to the Author"
    finally:
        _close(context)


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("No-permission user is denied")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a user without the required permission is denied access to the About Qatar Chamber page record")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.tc_134687
@pytest.mark.traceability("134687")
@allure.label("pbi", "129392")
@allure.label("testcase", "134687")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134687_user_without_permission_is_denied(browser):
    # Site Member: signs in, holds no content role. Read-only attempts only.
    context, member_page = _role_session(browser, ROLE_MEMBER)
    member = AboutQatarChamberAdminPage(member_page)
    results = {}
    try:
        for ui, message in (("en", member.ACCESS_DENIED_EN), ("ar", member.ACCESS_DENIED_AR)):
            with allure.step(f"[{ui.upper()}] Attempt to open the page record for editing"):
                member.open_manage_entry(ABOUT_PAGE_SLUG, ABOUT_PAGE_ENTRY_CODE, ui)
                results[ui] = (message in member.body_text(), member.has_object_form())
        _attach("per-language (message shown, editable form rendered)", results)
        for ui, (shown, editable) in results.items():
            assert not editable, f"[{ui}] the record opened in editable mode for a Site Member"
            assert shown, f"[{ui}] the exact Access Denied message was not shown"
    finally:
        _close(context)


# ── Lifecycle on the public site (as Site Content Editor) ────────────────
@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Publish makes content visible")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that publishing the About Qatar Chamber page makes the content visible on the website")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.pbi_129392
@pytest.mark.tc_134688
@pytest.mark.traceability("134688")
@allure.label("pbi", "129392")
@allure.label("testcase", "134688")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134688_publishing_makes_content_visible(page, browser):
    # `page` (TEST_USER) is used only by the gate's status precondition.
    title = "About Qatar Chamber"
    section = "The Voice of Qatar's Private Sector"
    context, editor_page = _role_session(browser, ROLE_EDITOR)
    editor = AboutQatarChamberAdminPage(editor_page)
    anon = new_context(browser, use_auth_state=False)
    about = AboutQatarChamberPage(anon.new_page())
    try:
        with allure.step("As Site Content Editor set Page Title and a section, click Publish"):
            authoring = editor.open_page_record_in("en")
            editor.fill_page_text("page_title", title, "en")
            editor.set_page_content_html(f"<h2>{section}</h2><p>QCTEST-134688 body.</p>", "en")
            block_live_singleton_write(PAGE_RECORD, "Editor publish of Page Title + a section")
            said = _publish_edit(editor, authoring)
            _attach("publish outcome", said)
            status = editor.open_page_record_in("en").current_status()
        with allure.step("Wait for the cache refresh and open the public page in English"):
            served = _public_poll(about, lambda: about.html_text_contains("QCTEST-134688 body."))
            hero_title = about.hero_title_text().strip()
            headings = about.section_heading_order()
        assert status == STATUS_PUBLISHED, f"status after the Editor's publish is {status!r}"
        assert served, "the published content never reached the public page"
        assert hero_title == title, f"public title is {hero_title!r}, expected {title!r}"
        assert section in headings, f"section {section!r} not rendered; headings {headings}"
    finally:
        _close(context, anon)


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Publish refreshes cache and writes audit log")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that publishing the About Qatar Chamber page updates the page cache and writes an audit log entry")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.pbi_129392
@pytest.mark.tc_134693
@pytest.mark.traceability("134693")
@allure.label("pbi", "129392")
@allure.label("testcase", "134693")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134693_publish_refreshes_cache_and_writes_audit_log(page, browser):
    # Audit portlet read through the TEST_USER admin session (the Editor
    # cannot read it); requires a NEW row by the Editor's own user id.
    # FIX PASS 5 (2026-10-14): checked FIRST, before any write -- the public
    # About page has answered 404 to everyone since 2026-10-13 (the About Us
    # nav link still points at it), so "the public page serves the new
    # content after the cache refresh" cannot be observed and a Publish
    # would only add a live write. Reported BLOCKED; the page is not touched
    # (fragments / layout are off-limits).
    probe_ctx = new_context(browser, use_auth_state=False)
    try:
        public_status = AboutQatarChamberPage(probe_ctx.new_page()).page_http_status()
    finally:
        _close(probe_ctx)
    if public_status != 200:
        pytest.fail(
            f"BLOCKED -- the public About page /web/qatar-chamber/about-us answers HTTP {public_status} "
            "to an anonymous visitor, so the cache-refresh half of this case cannot be observed. "
            "Nothing was written.",
            pytrace=False,
        )
    admin = AboutQatarChamberAdminPage(page)
    current = _about_current(admin)
    marker = "CACHE-CHECK-129392"
    context, editor_page = _role_session(browser, ROLE_EDITOR)
    editor = AboutQatarChamberAdminPage(editor_page)
    anon = new_context(browser, use_auth_state=False)
    about = AboutQatarChamberPage(anon.new_page())
    with _page_end_published(admin, "134693"):
        try:
            with allure.step("Sign in as Site Content Editor and note the audit state"):
                admin.open_page_entries_list()
                entry_id = admin.page_row_entry_id()
                before = admin.audit_rows_for(entry_id)
                editor.open_page_entries_list()
                editor_id = editor.current_user_id()
            with allure.step(f"Add {marker!r} to Page Content (EN) and click Publish"):
                authoring = editor.open_page_record_in("en")
                editor.set_page_content_html(_with_content(current["content_en"], f"<p>{marker}</p>"), "en")
                block_live_singleton_write(PAGE_RECORD, "Editor publish of Page Content (EN)")
                log_live_write(PAGE_RECORD, "Page Content (EN)", f"<current content> + <p>{marker}</p>", "134693",
                               action="publish", note="Site Content Editor Publish")
                said = _publish_edit(editor, authoring)
                _attach("publish outcome", said)
            with allure.step("Open the public page after the standard cache refresh"):
                served = _public_poll(about, lambda: about.html_text_contains(marker))
            with allure.step("Open the Liferay audit log filtered to this record"):
                after = admin.audit_rows_for(entry_id)
                new_rows = after[: max(len(after) - len(before), 0)]
                _attach("audit (new rows)", new_rows or after[:5])
            assert served, f"the public page did not serve {marker!r} after the cache refresh"
            assert any(r[0] == editor_id for r in new_rows), (
                f"no NEW audit entry for record {entry_id} by the Editor (user {editor_id}): {new_rows}"
            )
        finally:
            _close(context, anon)


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Republish replaces content")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that editing and republishing the About Qatar Chamber page replaces the previously published content")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.web
@pytest.mark.pbi_129392
@pytest.mark.tc_134701
@pytest.mark.traceability("134701")
@allure.label("pbi", "129392")
@allure.label("testcase", "134701")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134701_republish_replaces_previous_content(page, browser):
    admin = AboutQatarChamberAdminPage(page)
    current = _about_current(admin)
    v1, v2 = "VERSION-1-129392", "VERSION-2-129392"
    context, editor_page = _role_session(browser, ROLE_EDITOR)
    editor = AboutQatarChamberAdminPage(editor_page)
    anon = new_context(browser, use_auth_state=False)
    about = AboutQatarChamberPage(anon.new_page())
    try:
        with allure.step(f"Precondition: publish the record containing {v1!r}"):
            authoring = editor.open_page_record_in("en")
            editor.set_page_content_html(_with_content(current["content_en"], f"<p>{v1}</p>"), "en")
            block_live_singleton_write(PAGE_RECORD, "precondition publish of version 1")
            _publish_edit(editor, authoring)
            has_v1 = _wait_stored(editor, lambda: v1 in editor.page_content_html("en"), True)
        assert has_v1 is True, f"precondition failed: {v1!r} was not stored"
        with allure.step(f"Replace the paragraph with {v2!r} and publish"):
            authoring = editor.open_page_record_in("en")
            editor.set_page_content_html(_with_content(current["content_en"], f"<p>{v2}</p>"), "en")
            said = _publish_edit(editor, authoring)
            _attach("publish outcome", said)
        with allure.step("Open the public page after the standard cache refresh"):
            served = _public_poll(about, lambda: about.html_text_contains(v2))
            text = about.page_body_text()
        assert served and v2 in text, f"the public page does not show {v2!r}"
        assert v1 not in text, f"{v1!r} still appears on the public page"
    finally:
        _close(context, anon)


# ── Text fields ──────────────────────────────────────────────────────────
@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Page Title (EN)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid English Page Title is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134702
@pytest.mark.traceability("134702")
@allure.label("pbi", "129392")
@allure.label("testcase", "134702")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134702_valid_english_page_title_is_saved(page):
    _case_valid_text(page, "134702", "page_title", "en", "About Qatar Chamber")


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Page Title (EN)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty English Page Title is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134703
@pytest.mark.traceability("134703")
@allure.label("pbi", "129392")
@allure.label("testcase", "134703")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134703_empty_english_page_title_is_rejected(page):
    _case_rejected_text(page, "134703", "page_title", "en", "")


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Page Title (AR)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Arabic Page Title is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.tc_134706
@pytest.mark.traceability("134706")
@allure.label("pbi", "129392")
@allure.label("testcase", "134706")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134706_valid_arabic_page_title_is_saved(page):
    _case_valid_text(page, "134706", "page_title", "ar", "غرفة قطر")


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Page Title (AR)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a missing Arabic Page Title is rejected with the Arabic-title-required message")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.tc_134707
@pytest.mark.traceability("134707")
@allure.label("pbi", "129392")
@allure.label("testcase", "134707")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134707_missing_arabic_page_title_is_rejected(page):
    # Both interface languages; the exact wording ('Arabic title is
    # required.' / 'العنوان العربي مطلوب.') is attached, not asserted.
    _case_rejected_text(page, "134707", "page_title", "ar", "", ui_locales=("en", "ar"))


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Content Image Alt Text")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that valid image Alt Text is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134718
@pytest.mark.traceability("134718")
@allure.label("pbi", "129392")
@allure.label("testcase", "134718")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134718_valid_alt_text_is_saved(page):
    _case_valid_text(page, "134718", "alt_text", "en", "Qatar Chamber headquarters building")


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Content Image Alt Text")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that empty image Alt Text is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134719
@pytest.mark.traceability("134719")
@allure.label("pbi", "129392")
@allure.label("testcase", "134719")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134719_empty_alt_text_is_rejected(page):
    _case_rejected_text(page, "134719", "alt_text", "en", "")


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Hyperlink URL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an invalid Hyperlink URL is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.pbi_129392
@pytest.mark.tc_134734
@pytest.mark.traceability("134734")
@allure.label("pbi", "129392")
@allure.label("testcase", "134734")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134734_invalid_hyperlink_url_is_rejected(page):
    _case_rejected_text(page, "134734", "hyperlink_url", "en", "htp:/qatarchamber")


# ── Page Content (rich text) ─────────────────────────────────────────────
@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Page Content (EN)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that valid English Page Content is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134722
@pytest.mark.traceability("134722")
@allure.label("pbi", "129392")
@allure.label("testcase", "134722")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134722_valid_english_page_content_is_saved(page):
    body = ("QCTEST-134722 The Chamber represents the private sector. " * 8)[:400 - 48]
    html = (f"<h2>QCTEST-134722 Heading</h2><p>{body}</p>"
            "<ul><li>Item one</li><li>Item two</li><li>Item three</li></ul>")
    _case_valid_rich(page, "134722", "en", html,
                     ("QCTEST-134722 Heading", "<ul>", "Item one", "Item two", "Item three"))


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Page Content (EN)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that empty English Page Content is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134723
@pytest.mark.traceability("134723")
@allure.label("pbi", "129392")
@allure.label("testcase", "134723")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134723_empty_english_page_content_is_rejected(page):
    _case_rejected_rich(page, "134723", "en")


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Page Content (AR)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that valid Arabic Page Content is accepted and saved with RTL text preserved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.tc_134726
@pytest.mark.traceability("134726")
@allure.label("pbi", "129392")
@allure.label("testcase", "134726")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134726_valid_arabic_page_content_is_saved_rtl(page):
    heading = "صوت القطاع الخاص في قطر"
    body = ("تمثل غرفة قطر مصالح القطاع الخاص وتدعم نموه المستدام. " * 9)[:400 - len(heading)]
    seen = _case_valid_rich(page, "134726", "ar", f"<h2>{heading}</h2><p>{body}</p>", (heading,))
    assert seen["direction"] == "rtl", f"the Arabic editor renders {seen['direction']!r}, expected rtl"


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Page Content (AR)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that empty Arabic Page Content is rejected on save")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.tc_134727
@pytest.mark.traceability("134727")
@allure.label("pbi", "129392")
@allure.label("testcase", "134727")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134727_empty_arabic_page_content_is_rejected(page):
    _case_rejected_rich(page, "134727", "ar")


# ── Hero Banner image (disposable AboutHeroBanner rows) ──────────────────
# The hero banner is AboutHeroBanner (see module docstring trap note); the
# page object's own legacy "Hero Banner Image" field is never written.
@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Hero Banner image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid JPG Hero Banner image under 2 MB is accepted")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134710
@pytest.mark.traceability("134710")
@allure.label("pbi", "129392")
@allure.label("testcase", "134710")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134710_valid_jpg_hero_banner_is_accepted(page):
    # P1/P2 RERUN 2026-10-13 (user decision): no disposable QCTEST hero row
    # can exist on qcdev (the create form is hidden), so the case runs on the
    # REAL `about-us` hero row (QCDEMO-ABOUT-HERO-about-us) behind the opt-in
    # gate: every write logged first, nothing deleted, the row re-published
    # in `finally`. Without QC_ALLOW_LIVE_SINGLETON_WRITES=1: NOT APPLICABLE.
    admin = AboutQatarChamberAdminPage(page)
    path = _fixture("hero.jpg", make_jpg, 900 * 1024)
    with _hero_end_published(admin, "134710"):
        with allure.step("Open the About Hero Banner record for pageKey=about-us"):
            authoring = admin.open_hero_banner_record()
            assert authoring.field_value(admin.PAGE_KEY_LABEL) == HERO_BANNER_ABOUT_US_PAGE_KEY, (
                "opened the wrong AboutHeroBanner row"
            )
            original = authoring.current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL)
        with allure.step("Upload hero.jpg (JPG, 900 KB) to the Hero Banner Image and click Save"):
            block_live_singleton_write(HERO_RECORD, "upload + Publish of hero.jpg as the Banner Image")
            if authoring.current_status() == STATUS_PUBLISHED:
                log_live_write(HERO_RECORD, "<workflow>", STATUS_UNPUBLISHED, "134710", action="unpublish",
                               note="Unpublish to edit as draft (re-published in finally)")
                authoring.unpublish_to_edit_as_draft()
            authoring.upload_file(admin.BANNER_IMAGE_UPLOAD_LABEL, path)
            log_live_write(HERO_RECORD, admin.BANNER_IMAGE_UPLOAD_LABEL, "hero.jpg", "134710", action="upload",
                           note=f"900 KB JPG, replaces {original!r}; then Publish")
            said = _publish_edit(admin, authoring)
            _attach("save outcome", said)
        with allure.step("Reload the record"):
            name = admin.open_hero_banner_record().current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL)
        assert not said["refusal"], f"the valid hero.jpg was refused: {said['refusal']!r}"
        assert name.lower().startswith("hero") and ".jpg" in name.lower(), (
            f"the Hero Banner field shows {name!r}, expected hero.jpg (was {original!r})"
        )


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Hero Banner image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a Hero Banner image in an unsupported format is rejected with the format message")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.tc_134711
@pytest.mark.traceability("134711")
@allure.label("pbi", "129392")
@allure.label("testcase", "134711")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134711_unsupported_hero_banner_format_is_rejected(page):
    # Picker only -- Add is never clicked and the form is never saved, so
    # nothing can be persisted. CHANGED 2026-10-13: the hero CREATE form is
    # hidden on qcdev (open_new_hero_form() timed out, 35 s), so the picker is
    # driven on the REAL `about-us` hero row's form, read-only in effect; the
    # stored Banner Image is re-read afterwards to prove nothing changed.
    admin = AboutQatarChamberAdminPage(page)
    path = _fixture("hero.gif", make_gif, 500 * 1024)
    image_before = admin.open_hero_banner_record("en").current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL)
    outcomes = {}
    for ui in ("en", "ar"):
        with allure.step(f"[{ui.upper()} interface] Upload hero.gif (GIF, 500 KB) to the Hero Banner Image"):
            authoring = admin.open_hero_banner_record(ui)
            outcomes[ui] = _attempt_upload(admin, authoring, admin.HERO_IMAGE_FIELD_NAME, path)
    image_after = admin.open_hero_banner_record("en").current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL)
    _attach("picker outcomes (wording recorded, not asserted)", outcomes)
    for ui, outcome in outcomes.items():
        assert outcome["rejection"], (
            f"[{ui}] the GIF Hero Banner was not rejected (accepted={outcome['accepted']}; "
            f"text={outcome['picker_text'][:300]!r})"
        )
    assert image_after == image_before, (
        f"the stored Hero Banner changed from {image_before!r} to {image_after!r}")


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Hero Banner image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a Hero Banner image above 2 MB is rejected with the size message")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129392
@pytest.mark.tc_134712
@pytest.mark.traceability("134712")
@allure.label("pbi", "129392")
@allure.label("testcase", "134712")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134712_hero_banner_above_2mb_is_rejected(page):
    # File-size tolerance (project rule): up to 3 MB accepted is OK, so the
    # 2.1 MB result is recorded; a 3.1 MB file MUST be rejected (EN + AR).
    admin = AboutQatarChamberAdminPage(page)
    key = _hero_key("134712")
    exact = _fixture("hero-2mb.jpg", make_jpg, 2 * ONE_MB)
    over = _fixture("hero-oversize.jpg", make_jpg, int(2.1 * ONE_MB))
    far_over = _fixture("hero-oversize-3mb.jpg", make_jpg, int(3.1 * ONE_MB))
    outcomes = {}
    stored_name = after_name = ""
    try:
        with allure.step("Upload hero-2mb.jpg (exactly 2 MB) and click Save"):
            said = _create_hero(admin, key, exact, "QCTEST hero banner")
        if said["listed"]:
            authoring = _open_hero(admin, key)
            stored_name = authoring.current_file_name(admin.HERO_IMAGE_UPLOAD_LABEL)
            with allure.step("Upload hero-oversize.jpg (2.1 MB) -- recorded under the 3 MB tolerance"):
                outcomes["2.1MB"] = _attempt_upload(admin, authoring, admin.HERO_IMAGE_FIELD_NAME, over, size_only=True)
            for ui in ("en", "ar"):
                with allure.step(f"[{ui.upper()} interface] Upload a 3.1 MB JPG -- must be rejected"):
                    authoring = _open_hero(admin, key, locale=ui)
                    outcomes[f"3.1MB-{ui}"] = _attempt_upload(
                        admin, authoring, admin.HERO_IMAGE_FIELD_NAME, far_over, size_only=True
                    )
            after_name = _open_hero(admin, key).current_file_name(admin.HERO_IMAGE_UPLOAD_LABEL)
        _attach("outcomes", outcomes)
        assert said["listed"] and "hero-2mb" in stored_name, (
            f"the exactly-2 MB Hero Banner was not saved ({said!r}, stored {stored_name!r})"
        )
        for ui in ("en", "ar"):
            assert outcomes[f"3.1MB-{ui}"]["rejection"], f"[{ui}] a 3.1 MB Hero Banner was not rejected"
        assert after_name == stored_name, f"the stored Hero Banner changed to {after_name!r}"
    finally:
        _hero_reset(admin, key, "134712")


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Hero Banner image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that publishing without a Hero Banner image is blocked")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134713
@pytest.mark.traceability("134713")
@allure.label("pbi", "129392")
@allure.label("testcase", "134713")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134713_publishing_without_hero_banner_is_blocked(page):
    # P1/P2 RERUN 2026-10-13 (user decision): runs on the REAL `about-us` hero
    # row (no disposable QCTEST row can be created on qcdev). The Unpublish
    # that makes the form editable is a real write -> gate first; the Publish
    # with the image removed is logged as an `attempt` and must be REFUSED
    # (stop_unless_refused right after it); the row is re-published in
    # `finally`. Nothing is deleted.
    admin = AboutQatarChamberAdminPage(page)
    with _hero_end_published(admin, "134713"):
        with allure.step("Open the About Hero Banner record for pageKey=about-us"):
            authoring = admin.open_hero_banner_record()
            assert authoring.field_value(admin.PAGE_KEY_LABEL) == HERO_BANNER_ABOUT_US_PAGE_KEY, (
                "opened the wrong AboutHeroBanner row"
            )
            original = authoring.current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL)
            assert original, "precondition: the about-us hero row has no Banner Image to remove"
        with allure.step("Leave the Hero Banner Image empty and click Publish"):
            # 2026-10-13: edited IN PLACE -- a Published row's own Publish is
            # exactly "publish without a hero banner"; no Unpublish round trip.
            block_live_singleton_write(HERO_RECORD, "Publish with the Banner Image removed (in place)")
            authoring.remove_current_file(admin.BANNER_IMAGE_UPLOAD_LABEL)
            # Remove takes effect only on save, so the field cannot read empty
            # yet; the pending removal ("Undo remove" shown) is the precondition.
            removal_pending = authoring.file_removal_pending(admin.BANNER_IMAGE_UPLOAD_LABEL)
            native = _FormProbe(authoring).attachment_validation_message(admin.BANNER_IMAGE_UPLOAD_LABEL)
            log_live_write(HERO_RECORD, admin.BANNER_IMAGE_UPLOAD_LABEL, "", "134713", action="attempt",
                           note=f"Publish with the Banner Image removed (was {original!r}); expected REFUSED")
            said = _publish_edit(admin, authoring)
            _attach("publish outcome (wording recorded, not asserted)", said)
        with allure.step("Reload the record: the Banner Image is still set"):
            image_after = admin.open_hero_banner_record().current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL)
        stop_unless_refused(_image_matches(image_after, original), HERO_RECORD,
                            "Publish with the Banner Image removed",
                            {"native": native, "said": said, "image": image_after})
        assert removal_pending, "precondition: Remove file did not register (no 'Undo remove' shown)"
        assert said["refusal"] or native, (
            f"publishing WITHOUT a Hero Banner image showed no refusal (said={said!r})"
        )
        assert _image_matches(image_after, original), (
            f"publishing WITHOUT a Hero Banner image was NOT blocked: the field reads {image_after!r}"
        )


# ── Content Image (the live singleton -- bytes restored at module end) ──
@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Content Image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid PNG Content Image under 2 MB is accepted")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134714
@pytest.mark.traceability("134714")
@allure.label("pbi", "129392")
@allure.label("testcase", "134714")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134714_valid_png_content_image_is_accepted(page):
    admin = AboutQatarChamberAdminPage(page)
    path = _fixture("building.png", make_png, int(1.1 * ONE_MB))
    with allure.step("Upload building.png (PNG, 1.1 MB) to the Content Image and click Save"):
        authoring = admin.open_page_record_in("en")
        authoring.upload_file(admin.CONTENT_IMAGE_UPLOAD_LABEL, path)
        block_live_singleton_write(PAGE_RECORD, "save of a valid building.png Content Image")
        said = _publish_edit(admin, authoring)
        _attach("save outcome", said)
    with allure.step("Reload the record"):
        name = _wait_stored(
            admin, lambda: "building" in admin.open_page_record_in("en").current_file_name(
                admin.CONTENT_IMAGE_UPLOAD_LABEL), True
        )
    assert not said["refusal"], f"the upload/save was refused: {said['refusal']!r}"
    assert name is True, "the Content Image field does not show building.png after reload"


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Content Image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a Content Image in an unsupported format is rejected with the format message")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134715
@pytest.mark.traceability("134715")
@allure.label("pbi", "129392")
@allure.label("testcase", "134715")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134715_unsupported_content_image_format_is_rejected(page):
    # Picker only -- Add is never clicked and the form is never saved.
    admin = AboutQatarChamberAdminPage(page)
    path = _fixture("building.bmp", make_bmp, 400 * 1024)
    with allure.step("Open the record and read the stored Content Image"):
        authoring = admin.open_page_record_in("en")
        before = authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
    with allure.step("Upload building.bmp (BMP, 400 KB) to the Content Image"):
        outcome = _attempt_upload(admin, authoring, admin.CONTENT_IMAGE_FIELD_NAME, path)
    with allure.step("Re-open the record and confirm the stored image is unchanged"):
        after = admin.open_page_record_in("en").current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
    _attach("picker outcome (wording recorded, not asserted)", outcome)
    assert outcome["rejection"], (
        f"the BMP Content Image was not rejected (accepted={outcome['accepted']}; "
        f"text={outcome['picker_text'][:300]!r})"
    )
    assert after == before, f"the stored Content Image changed from {before!r} to {after!r}"


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Content Image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a Content Image above 2 MB is rejected at the size boundary")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134716
@pytest.mark.traceability("134716")
@allure.label("pbi", "129392")
@allure.label("testcase", "134716")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134716_content_image_above_2mb_is_rejected(page):
    # File-size tolerance: 2.1 MB recorded; 3.1 MB MUST be rejected.
    admin = AboutQatarChamberAdminPage(page)
    exact = _fixture("content-2mb.png", make_png, 2 * ONE_MB)
    over = _fixture("content-oversize.png", make_png, int(2.1 * ONE_MB))
    far_over = _fixture("content-oversize-3mb.png", make_png, int(3.1 * ONE_MB))
    outcomes = {}
    with allure.step("Upload content-2mb.png (exactly 2 MB) and click Save"):
        authoring = admin.open_page_record_in("en")
        authoring.upload_file(admin.CONTENT_IMAGE_UPLOAD_LABEL, exact)
        # The boundary case starts with a SUCCESSFUL 2 MB save (2026-10-13).
        block_live_singleton_write(PAGE_RECORD, "save of the exactly-2 MB Content Image")
        said = _publish_edit(admin, authoring)
        stored = _wait_stored(
            admin, lambda: "content-2mb" in admin.open_page_record_in("en").current_file_name(
                admin.CONTENT_IMAGE_UPLOAD_LABEL), True
        )
    stored_name = admin.open_page_record_in("en").current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
    with allure.step("Upload content-oversize.png (2.1 MB) -- recorded under the 3 MB tolerance"):
        authoring = admin.open_page_record_in("en")
        outcomes["2.1MB"] = _attempt_upload(admin, authoring, admin.CONTENT_IMAGE_FIELD_NAME, over, size_only=True)
    with allure.step("Upload a 3.1 MB PNG -- must be rejected"):
        authoring = admin.open_page_record_in("en")
        outcomes["3.1MB"] = _attempt_upload(admin, authoring, admin.CONTENT_IMAGE_FIELD_NAME, far_over, size_only=True)
    after_name = admin.open_page_record_in("en").current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
    _attach("outcomes", {"save": said, **outcomes})
    assert stored is True, f"the exactly-2 MB Content Image was not saved ({said!r})"
    assert outcomes["3.1MB"]["rejection"], "a 3.1 MB Content Image was not rejected"
    assert after_name == stored_name, f"the stored Content Image changed to {after_name!r}"


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Content Image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that publishing without a Content Image is blocked")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134717
@pytest.mark.traceability("134717")
@allure.label("pbi", "129392")
@allure.label("testcase", "134717")
@ABOUT_XDIST_GROUP
@ABOUT_TIMEOUT
def test_about_cp_134717_publishing_without_content_image_is_blocked(page):
    # Remove in-form and click Publish. A remove alone does not persist
    # without its own save (remove_current_file() docstring), so an unchanged
    # re-read proves nothing by itself: the test also requires the field to
    # read EMPTY in the form before Publish, and a POSITIVE refusal (save
    # refusal text or the field's native required message). If the publish
    # went through, the test stops with the finding (no restore runs any
    # more -- user decision 2026-10-13); the record must be checked by hand.
    admin = AboutQatarChamberAdminPage(page)
    current = _about_current(admin)
    assert current["image"], "precondition: the record has no Content Image to remove"
    with allure.step("Clear the Content Image and click Publish"):
        authoring = admin.open_page_record_in("en")
        authoring.remove_current_file(admin.CONTENT_IMAGE_UPLOAD_LABEL)
        # Remove takes effect only on save (2026-10-13): the pending removal
        # ("Undo remove" shown) is the pre-save precondition, not an empty field.
        removal_pending = authoring.file_removal_pending(admin.CONTENT_IMAGE_UPLOAD_LABEL)
        native = _FormProbe(authoring).attachment_validation_message(admin.CONTENT_IMAGE_UPLOAD_LABEL)
        log_live_write(PAGE_RECORD, admin.CONTENT_IMAGE_UPLOAD_LABEL, "", "134717", action="attempt",
                       note=f"Publish with the Content Image removed (was {current['image']!r}); "
                            "expected REFUSED")
        said = _publish_edit(admin, authoring)
        _attach("publish outcome (wording recorded, not asserted)", said)
    with allure.step("Check the record status and stored image"):
        authoring = admin.open_page_record_in("en")
        image_after = authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
        status_after = authoring.current_status()
    stop_unless_refused(_image_matches(image_after, current["image"]) and status_after == current["workflow"],
                        PAGE_RECORD, "Publish with the Content Image removed",
                        {"native": native, "said": said, "image": image_after, "status": status_after})
    assert removal_pending, "precondition: Remove file did not register (no 'Undo remove' shown)"
    assert said["refusal"] or native, (
        f"no refusal was shown for Publish without a Content Image (said={said!r})"
    )
    assert _image_matches(image_after, current["image"]), (
        f"publishing WITHOUT a Content Image was NOT blocked: the field now reads {image_after!r}"
    )
    assert status_after == current["workflow"], f"the record status changed to {status_after!r}"


# ═════════════════════════════════════════════════════════════════════════
# P3/P4 BATCH -- 2026-10-13 (scripted OFFLINE, NOT executed): 134731 134733
# 134736 134737 134738, from .claude/qa-runs/phase3-20261012/129392.p34.todo.json
# (the case text is the oracle).
#
# USER DECISION 2026-10-13 (P3/P4 batch only): these cases MAY write test
# data to the real page singleton QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY
# -- ONLY when the run sets QC_ALLOW_LIVE_SINGLETON_WRITES=1 (otherwise
# block_live_singleton_write() reports them NOT APPLICABLE, unchanged). Nothing
# is ever deleted; every persisted write is logged BEFORE its click to
# reports/live-writes-20261013.jsonl for the user's manual cleanup. Each case
# leaves the record Published (picklist + workflow).
#
# Account: QC Site Content Editor (fresh logged-in context, never TEST_USER).
# "Save" / "Publish" = the form's Publish control (status=0). A Published
# record is unpublished first (guide section 4); since a form submit on an
# Unpublished record stores without publishing (GM incident 2026-10-12), the
# record is then driven to Published through the documented row transition.
# Public checks: a fresh logged-out context.
# ═════════════════════════════════════════════════════════════════════════
from cms.tests.live_write_guard import log_live_write
from cms.tests.live_status_cases import PicklistRecord, status_draft_case, status_published_case
from cms.tests.singleton_baseline import drive_to_editable, drive_to_published, list_status

P34_TIMEOUT = pytest.mark.timeout(480)
P34_WORKFLOW_BUDGET = 150.0
QC_HYPERLINK_URL = "https://www.qatarchamber.com"


def _p34_list(editor):
    return lambda: editor.open_page_entries_list()


def _p34_editable(editor, tc: str) -> None:
    """Published -> Unpublished (row action, verified), logged first."""
    if list_status(_p34_list(editor), ABOUT_PAGE_ENTRY_CODE) == STATUS_PUBLISHED:
        log_live_write(PAGE_RECORD, "<workflow>", STATUS_UNPUBLISHED, tc, action="unpublish",
                       note="make the form editable (guide section 4)")
        drive_to_editable(_p34_list(editor), ABOUT_PAGE_ENTRY_CODE, budget=P34_WORKFLOW_BUDGET)


def _p34_published(editor, tc: str) -> str:
    """Drive the record to Published (row transitions), logged first."""
    if list_status(_p34_list(editor), ABOUT_PAGE_ENTRY_CODE) == STATUS_PUBLISHED:
        return STATUS_PUBLISHED
    log_live_write(PAGE_RECORD, "<workflow>", STATUS_PUBLISHED, tc, action="publish",
                   note="the case's Publish / end state: leave the record Published")
    return drive_to_published(
        _p34_list(editor), ABOUT_PAGE_ENTRY_CODE,
        lambda: _publish_edit(editor, editor.open_page_record_in("en")),
        budget=P34_WORKFLOW_BUDGET,
    )


from contextlib import contextmanager as _p34_contextmanager


@_p34_contextmanager
def _p34_end_published(editor, tc: str):
    """Wraps a writing case: the record is always driven back to Published.
    A failed restore never masks the case's own failure; on a passing case
    it fails the test (the live page is not Published)."""
    failed = False
    try:
        yield
    except BaseException:
        failed = True
        raise
    finally:
        problem = ""
        try:
            _p34_published(editor, tc)
        except Exception as exc:  # noqa: BLE001 -- reported below
            problem = repr(exc)
            _attach("END STATE NOT RESTORED -- check the About page record by hand", problem)
        if problem and not failed:
            raise AssertionError(f"the case passed but {PAGE_RECORD} was not left Published: {problem}")


def _p34_save_field(editor, tc: str, key: str, value: str, note: str) -> dict:
    """Make editable, enter `value` in the EN text field `key`, click
    Publish (status=0). Returns what the form said."""
    _p34_editable(editor, tc)
    authoring = editor.open_page_record_in("en")
    editor.fill_page_text(key, value, "en")
    native = editor.page_text_validation_message(key, "en")
    log_live_write(PAGE_RECORD, f"{key} (EN)", value, tc, action="publish", note=note)
    said = _publish_edit(editor, authoring)
    said["native"] = native
    _attach(f"save outcome: {key} = {value!r}", said)
    return said


def _p34_empty_optional_case(page, browser, tc: str, key: str, label: str) -> None:
    """134731 / 134736: an OPTIONAL field left empty does not block Publish,
    and the public EN page renders normally with no empty / broken link."""
    ctx, editor_page = _role_session(browser, ROLE_EDITOR)
    anon = new_context(browser, use_auth_state=False)
    editor = AboutQatarChamberAdminPage(editor_page)
    about = AboutQatarChamberPage(anon.new_page())
    try:
        with _p34_end_published(editor, tc):
            _p34_empty_optional_body(editor, about, tc, key, label)
    finally:
        _close(anon, ctx)


def _p34_empty_optional_body(editor, about, tc: str, key: str, label: str) -> None:
    with allure.step(f"Open the About Qatar Chamber page record: {label} field"):
        editor.open_page_record_in("en")
        before = editor.page_text(key, "en")
    _attach(f"{label} before (precondition: empty)", repr(before))
    with allure.step(f"Leave {label} empty, keep every mandatory field, click Publish"):
        said = _p34_save_field(editor, tc, key, "", f"{label} left empty (case step 2)")
        status = _p34_published(editor, tc)
    with allure.step("Reload the record"):
        editor.open_page_record_in("en")
        stored = editor.page_text(key, "en")
    assert not said["refusal"], f"Publish with an empty {label} was refused: {said['refusal']!r}"
    assert not said["native"], f"{label} raised a validation message when empty: {said['native']!r}"
    _attach("success message (wording/toast is a note, not asserted)", said.get("success"))
    assert stored == "", f"{label} reads {stored!r} after the save, expected empty"
    assert status == STATUS_PUBLISHED, f"the record is {status!r} after Publish"
    with allure.step("Open the About Qatar Chamber page in English (logged-out visitor)"):
        rendered = _public_poll(about, about.hero_title_is_rendered)
        cta = about.is_cta_visible()
        cta_label = about.cta_label_text().strip() if cta else ""
        cta_href = (about.cta_href() or "") if cta else ""
        links_ok = about.no_anchor_has_empty_or_void_href()
    _attach("public page", {"rendered": rendered, "cta": cta, "label": cta_label,
                            "href": cta_href, "links_ok": links_ok})
    assert rendered, "the public About Qatar Chamber page did not render its content"
    assert not (cta and not cta_label), "an empty link label is displayed on the public page"
    assert links_ok, "an anchor in the page content points to an empty / void destination"
    if cta:
        assert cta_href.startswith(("http://", "https://", "/")), (
            f"the page's link points to a malformed destination: {cta_href!r}")


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Hyperlink Title")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Hyperlink Title is allowed because the field is optional")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134731
@pytest.mark.traceability("134731")
@allure.label("pbi", "129392")
@allure.label("testcase", "134731")
@ABOUT_XDIST_GROUP
@P34_TIMEOUT
def test_about_cp_134731_empty_hyperlink_title_is_allowed(page, browser):
    block_live_singleton_write(PAGE_RECORD, "publish with an empty Hyperlink Title", tc_id="134731")
    _p34_empty_optional_case(page, browser, "134731", "hyperlink_title", "Hyperlink Title")


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Hyperlink URL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid Hyperlink URL is accepted and saved")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134733
@pytest.mark.traceability("134733")
@allure.label("pbi", "129392")
@allure.label("testcase", "134733")
@ABOUT_XDIST_GROUP
@P34_TIMEOUT
def test_about_cp_134733_valid_hyperlink_url_is_accepted_and_saved(page, browser):
    tc = "134733"
    block_live_singleton_write(PAGE_RECORD, f"save of Hyperlink URL {QC_HYPERLINK_URL}", tc_id=tc)
    ctx, editor_page = _role_session(browser, ROLE_EDITOR)
    editor = AboutQatarChamberAdminPage(editor_page)
    try:
        with _p34_end_published(editor, tc):
            _p34_valid_url_body(editor, tc)
    finally:
        _close(ctx)


def _p34_valid_url_body(editor, tc: str) -> None:
    with allure.step("Open the About Qatar Chamber page record: Hyperlink URL available"):
        editor.open_page_record_in("en")
        before = editor.page_text("hyperlink_url", "en")
    if before == QC_HYPERLINK_URL:
        # The field already holds the case's value: an interim valid URL
        # is saved first, so the case's own save is a real change.
        with allure.step("Interim write: the field already holds the case's value"):
            _p34_save_field(editor, tc, "hyperlink_url", f"{QC_HYPERLINK_URL}/?qctest={tc}", "interim value")
    with allure.step(f"Enter {QC_HYPERLINK_URL!r} as the Hyperlink URL and click Save"):
        said = _p34_save_field(editor, tc, "hyperlink_url", QC_HYPERLINK_URL, "case step 2")
    with allure.step("Reload the record"):
        stored = _wait_stored(editor, lambda: editor.page_text("hyperlink_url", "en"), QC_HYPERLINK_URL)
    assert not said["native"], f"the URL raised a validation message: {said['native']!r}"
    assert not said["refusal"], f"the save was refused: {said['refusal']!r}"
    _attach("success message (wording/toast is a note, not asserted)", said.get("success"))
    assert stored == QC_HYPERLINK_URL, f"Hyperlink URL reads {stored!r}, expected {QC_HYPERLINK_URL!r}"


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Hyperlink URL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an empty Hyperlink URL is allowed because the field is optional")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134736
@pytest.mark.traceability("134736")
@allure.label("pbi", "129392")
@allure.label("testcase", "134736")
@ABOUT_XDIST_GROUP
@P34_TIMEOUT
def test_about_cp_134736_empty_hyperlink_url_is_allowed(page, browser):
    block_live_singleton_write(PAGE_RECORD, "publish with an empty Hyperlink URL", tc_id="134736")
    _p34_empty_optional_case(page, browser, "134736", "hyperlink_url", "Hyperlink URL")


def _p34_picklist(editor) -> PicklistRecord:
    def _save(authoring) -> dict:
        return _publish_edit(editor, authoring)

    return PicklistRecord(
        record=PAGE_RECORD,
        entry_code=ABOUT_PAGE_ENTRY_CODE,
        form=editor,
        open_form=lambda: editor.open_page_record_in("en"),
        save=_save,
        open_list=_p34_list(editor),
        budget=P34_WORKFLOW_BUDGET,
    )


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Status")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Status dropdown offers and stores the Draft value")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134737
@pytest.mark.traceability("134737")
@allure.label("pbi", "129392")
@allure.label("testcase", "134737")
@ABOUT_XDIST_GROUP
@P34_TIMEOUT
def test_about_cp_134737_status_dropdown_stores_draft(page, browser):
    block_live_singleton_write(PAGE_RECORD, "Status picklist = Draft, then back to Published", tc_id="134737")
    ctx, editor_page = _role_session(browser, ROLE_EDITOR)
    try:
        # The case says the dropdown "lists Draft and Published" (not
        # "exactly"), so both must be present; extra options are attached.
        status_draft_case(_p34_picklist(AboutQatarChamberAdminPage(editor_page)), "134737", exact_options=False)
    finally:
        _close(ctx)


@allure.epic("About Us")
@allure.feature("About Qatar Chamber")
@allure.story("Status")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Status dropdown offers and stores the Published value")
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129392
@pytest.mark.tc_134738
@pytest.mark.traceability("134738")
@allure.label("pbi", "129392")
@allure.label("testcase", "134738")
@ABOUT_XDIST_GROUP
@P34_TIMEOUT
def test_about_cp_134738_status_dropdown_stores_published(page, browser):
    block_live_singleton_write(PAGE_RECORD, "Status picklist Draft precondition, then Published", tc_id="134738")
    ctx, editor_page = _role_session(browser, ROLE_EDITOR)
    try:
        status_published_case(_p34_picklist(AboutQatarChamberAdminPage(editor_page)), "134738")
    finally:
        _close(ctx)
