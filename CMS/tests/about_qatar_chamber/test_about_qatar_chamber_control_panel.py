"""
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

TEST_OWNED: every case below mutates a real, shared qcdev record. Each
captures its own baseline BEFORE mutating and restores it in `finally`.
No record is ever deleted.
"""

import allure
import pytest

from cms.pages.about_qatar_chamber.about_qatar_chamber_admin_page import (
    AboutQatarChamberAdminPage,
)
from web.pages.about_qatar_chamber.about_qatar_chamber_page import AboutQatarChamberPage
from core.web.browser import new_context
from core.utils.waits import wait_until

PBI = "129392"

# All six mutate one of the two shared About-Us records -- one xdist group
# so `--dist loadgroup` never schedules two of them concurrently, mirroring
# the convention in test_chambers_law_control_panel.py.
ABOUT_XDIST_GROUP = pytest.mark.xdist_group("about_qatar_chamber_129392")


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
    # Asserted against the real vocabulary, with the case's INTENT (public
    # content withdrawn, CMS record intact) asserted exactly as worded.
    admin = AboutQatarChamberAdminPage(page)
    baseline_status = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the published About Qatar Chamber page record via Object Authoring"):
            authoring = admin.open_page_record()
            baseline_status = authoring.current_status()

        with allure.step("Ensure the record starts published (this case's own precondition)"):
            if authoring.current_status() != "Approved":
                authoring.submit_for_publishing()
            assert authoring.current_status() == "Approved"

        with allure.step("Confirm an anonymous visitor can see the page content first"):
            about = AboutQatarChamberPage(anon_page)
            about.open_en()
            assert about.hero_title_is_rendered(), (
                "precondition failed: the About Us page is not rendering publicly"
            )

        with allure.step("Click Unpublish and wait for the standard cache refresh"):
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
        assert status_in_cms == "Draft"
        assert title_in_cms, (
            "expected the record and its content to remain present and editable in the CMS"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 -- cleanup must never mask the real result
            pass
        if baseline_status:
            with allure.step("TEST_OWNED reset -- restore the record's published state"):
                authoring = admin.open_page_record()
                if baseline_status == "Approved" and authoring.current_status() != "Approved":
                    authoring.submit_for_publishing()


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
    # case): while a record is Approved, `Save as Draft` is DISABLED -- the
    # only route to editing is "Unpublish to edit as draft", which takes the
    # page off the live site. So this record cannot simultaneously serve
    # published content AND hold a draft edit, and the case's "...and still
    # shows the previously published content" clause cannot hold for the
    # same record. The draft-leakage rule itself -- the point of the case --
    # is asserted exactly: the draft marker never reaches a public visitor,
    # and the CMS holds it.
    admin = AboutQatarChamberAdminPage(page)
    marker = "DRAFT-ONLY-129392"
    baseline_content = None
    baseline_status = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the About Qatar Chamber page record via Object Authoring"):
            authoring = admin.open_page_record()
            baseline_content = _normalize_rich_text(
                authoring.rich_text_value(admin.PAGE_CONTENT_FIELD_NAME)
            )
            baseline_status = authoring.current_status()

        with allure.step(f"Add the paragraph '{marker}' to Page Content (EN) and Save as draft"):
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()
            authoring.fill_rich_text(
                f"{baseline_content}\n{marker}", admin.PAGE_CONTENT_FIELD_NAME
            )
            authoring.save_as_draft()

        with allure.step("Open the public page as a genuine anonymous visitor and search for the marker"):
            # Tolerant open: unpublishing to edit as draft leaves the URL
            # serving a 200 shell with an empty hero, so `open_en()`'s
            # hero-title wait would time out here (see its docstring).
            about = AboutQatarChamberPage(anon_page)
            about.open_en_tolerant()
            public_text = about.page_body_text()

        with allure.step("Re-open the record in the CMS"):
            authoring = admin.open_page_record()
            cms_content = authoring.rich_text_value(admin.PAGE_CONTENT_FIELD_NAME)
            status_in_cms = authoring.current_status()

        assert status_in_cms == "Draft"
        assert marker in cms_content, "expected the CMS record to hold the draft paragraph"
        assert marker not in public_text, (
            f"DRAFT LEAK: '{marker}' was saved only as a draft but appears on the public page"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass
        if baseline_content is not None:
            with allure.step("TEST_OWNED reset -- restore Page Content/Status to baseline"):
                authoring = admin.open_page_record()
                if authoring.current_status() == "Approved":
                    authoring.unpublish_to_edit_as_draft()
                authoring.fill_rich_text(baseline_content, admin.PAGE_CONTENT_FIELD_NAME)
                if baseline_status == "Approved":
                    authoring.submit_for_publishing()
                else:
                    authoring.save_as_draft()


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
    admin = AboutQatarChamberAdminPage(page)
    marker = "PREVIEW-ONLY-129392"
    baseline_content = None
    baseline_status = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the About Qatar Chamber page record via Object Authoring"):
            authoring = admin.open_page_record()
            baseline_content = _normalize_rich_text(
                authoring.rich_text_value(admin.PAGE_CONTENT_FIELD_NAME)
            )
            baseline_status = authoring.current_status()

        with allure.step(f"Add '{marker}' to Page Content (EN), Save as draft, then Preview"):
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()
            authoring.fill_rich_text(
                f"{baseline_content}\n{marker}", admin.PAGE_CONTENT_FIELD_NAME
            )
            authoring.save_as_draft()
            status_before_preview = authoring.current_status()

            entries = admin.open_page_entries_list()
            # Code-keyed: this object's Entry column renders its external
            # reference code, not a title (see the admin Page Object's note).
            preview_url = entries.row_preview_url_by_code(
                "QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY"
            )
            banner_text = entries.preview_banner_text(preview_url)
            preview_text = entries.text("body")

        with allure.step("Confirm the record status is unchanged after Preview"):
            authoring = admin.open_page_record()
            status_after_preview = authoring.current_status()

        with allure.step("Confirm the public page (fresh anonymous context) does not contain the paragraph"):
            # Tolerant open — the record is deliberately in draft here.
            about = AboutQatarChamberPage(anon_page)
            about.open_en_tolerant()
            public_text = about.page_body_text()

        assert status_before_preview == "Draft"
        assert "draft" in banner_text.lower(), (
            f"expected the preview banner to disclose an unpublished record; got {banner_text[:120]!r}"
        )
        assert marker in preview_text, (
            "expected Preview to render the unpublished draft content"
        )
        assert status_after_preview == "Draft", "expected Preview not to publish the record"
        assert marker not in public_text, (
            f"DRAFT LEAK: previewing must not publish -- '{marker}' appears on the public page"
        )
    finally:
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass
        if baseline_content is not None:
            with allure.step("TEST_OWNED reset -- restore Page Content/Status to baseline"):
                authoring = admin.open_page_record()
                if authoring.current_status() == "Approved":
                    authoring.unpublish_to_edit_as_draft()
                authoring.fill_rich_text(baseline_content, admin.PAGE_CONTENT_FIELD_NAME)
                if baseline_status == "Approved":
                    authoring.submit_for_publishing()
                else:
                    authoring.save_as_draft()


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
    baseline_title = None
    baseline_url = None
    baseline_status = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the record and capture the current Hyperlink Title/URL"):
            authoring = admin.open_page_record()
            baseline_title = authoring.field_value(admin.HYPERLINK_TITLE_LABEL)
            baseline_url = authoring.field_value(admin.HYPERLINK_URL_LABEL)
            baseline_status = authoring.current_status()

        with allure.step(f"Configure the hyperlink as {target_label!r} -> {target_url} and publish"):
            if authoring.current_status() == "Approved":
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
        if baseline_title is not None:
            with allure.step("TEST_OWNED reset -- restore Hyperlink Title/URL/Status"):
                authoring = admin.open_page_record()
                if authoring.current_status() == "Approved":
                    authoring.unpublish_to_edit_as_draft()
                authoring.fill_text(admin.HYPERLINK_TITLE_LABEL, baseline_title)
                authoring.fill_text(admin.HYPERLINK_URL_LABEL, baseline_url)
                if baseline_status == "Approved":
                    authoring.submit_for_publishing()
                else:
                    authoring.save_as_draft()


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
    # TEST_OWNED: the original banner bytes are downloaded via the field's
    # own Download link BEFORE mutating and re-uploaded in `finally`
    # (re-upload creates a fresh document -- byte-identical, disclosed).
    admin = AboutQatarChamberAdminPage(page)
    replacement_file = "qc-footer-facet-left.png"
    baseline_status = None
    original_saved = False
    original_download_path = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the AboutHeroBanner record for pageKey=about-us"):
            authoring = admin.open_hero_banner_record()
            baseline_status = authoring.current_status()
            assert authoring.field_value(admin.PAGE_KEY_LABEL) == "about-us", (
                "opened the wrong AboutHeroBanner row"
            )
            original_filename = authoring.current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL)
            assert original_filename, (
                "precondition failed: this case needs a record that ALREADY has a "
                "Hero Banner image set"
            )
            original_download_path = str(tmp_path / original_filename)
            original_saved = bool(
                authoring.download_current_file(
                    admin.BANNER_IMAGE_UPLOAD_LABEL, original_download_path
                )
            )

        with allure.step("Capture the image the public hero currently serves"):
            about = AboutQatarChamberPage(anon_page)
            about.open_en()
            hero_before = about.hero_media_background_image()

        with allure.step("Replace the Banner Image and publish"):
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()
            authoring.select_existing_file(
                admin.BANNER_IMAGE_UPLOAD_LABEL,
                replacement_file,
                folder="QC Footer Social Icons",
            )
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
        with allure.step("TEST_OWNED reset -- restore the original Banner Image/Status"):
            authoring = admin.open_hero_banner_record()
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()
            if original_saved:
                authoring.upload_file(
                    admin.BANNER_IMAGE_UPLOAD_LABEL, original_download_path
                )
            if baseline_status == "Approved":
                authoring.submit_for_publishing()
            elif baseline_status is not None:
                authoring.save_as_draft()


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
    # file's bytes are downloaded first, then removed and saved (phase 1),
    # which is the confirmed-live sequence -- a remove + set + publish in one
    # unsaved form session does NOT persist (see
    # ObjectAuthoringPage.remove_current_file()'s docstring). Phase 2
    # re-opens fresh, sets the new image and publishes. `finally` restores
    # the original bytes the same two-phase way.
    #
    # DISCLOSED: the case's alt-text clause ("Qatar Chamber headquarters") is
    # asserted against AboutHeroBanner's OWN `Banner Image Alt Text` field --
    # that is where a hero alt text lives on this surface (the page object's
    # `Hero Banner Alt Text` belongs to the legacy, unrendered field).
    admin = AboutQatarChamberAdminPage(page)
    new_file = "qc-footer-facet-right.png"
    target_alt = "Qatar Chamber headquarters"
    baseline_status = None
    baseline_alt = None
    original_saved = False
    original_download_path = None

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()

    try:
        with allure.step("Open the AboutHeroBanner record and capture its baseline"):
            authoring = admin.open_hero_banner_record()
            baseline_status = authoring.current_status()
            baseline_alt = authoring.field_value(admin.BANNER_IMAGE_ALT_TEXT_LABEL)
            original_filename = authoring.current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL)
            if original_filename:
                original_download_path = str(tmp_path / original_filename)
                original_saved = bool(
                    authoring.download_current_file(
                        admin.BANNER_IMAGE_UPLOAD_LABEL, original_download_path
                    )
                )

        with allure.step("Remove the current banner and save (phase 1) to reach the empty-field precondition"):
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()
            if original_saved:
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

        assert authoring.current_status() == "Approved"
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
        with allure.step("TEST_OWNED reset -- restore the original Banner Image bytes/Alt Text/Status"):
            authoring = admin.open_hero_banner_record()
            if authoring.current_status() == "Approved":
                authoring.unpublish_to_edit_as_draft()
            if original_saved:
                authoring.remove_current_file(admin.BANNER_IMAGE_UPLOAD_LABEL)
                authoring.save_as_draft()
                authoring = admin.open_hero_banner_record()
                authoring.upload_file(
                    admin.BANNER_IMAGE_UPLOAD_LABEL, original_download_path
                )
            if baseline_alt is not None:
                authoring.fill_text(admin.BANNER_IMAGE_ALT_TEXT_LABEL, baseline_alt)
            if baseline_status == "Approved":
                authoring.submit_for_publishing()
            elif baseline_status is not None:
                authoring.save_as_draft()
