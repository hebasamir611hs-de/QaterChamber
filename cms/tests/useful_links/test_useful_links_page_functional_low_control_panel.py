"""
cms/tests/useful_links/test_useful_links_page_functional_low_control_panel.py

Functional-Low, Control_Panel cases for PBI 130702 (QC - Business Gateway -
009 - Useful Links), page-level object `manage-useful-links-page`:
hero / directory-intro field validation (140700-140725) and the
Draft / Preview / Publish / Unpublish lifecycle (140778-140781).

ACCOUNT: none of these cases names a role, so they run as the default
authenticated session (TEST_USER), which this build treats as an Editor
("As an Editor, what you publish here goes live straight away."). That is
the account every lifecycle outcome below is pinned to.

"CLICK SAVE": the form has no button labelled Save. On the published
singleton "Save as Draft" is disabled and performs no validation anyway, so
"Save" is driven as the submit button (labelled "Publish" for this account) —
the only enabled save action and the only one that validates. See
UsefulLinksPageAdminPage's module docstring.

TEST_OWNED: every test edits the real singleton QCDEMO-130702-ULP-1
(entry 109803). Each captures a full snapshot BEFORE mutating and restores it
in `finally`, leaving the record Published. No record is ever deleted. All
tests share one xdist group so two of them never touch the record at once.

OUTAGE-GATED (140778, 140779, 140780, 140781): their precondition takes the
real public page off the site (Unpublish / Draft). standards.md
("Destructive-Precondition Tests Must Use Disposable Test Data", rule 5)
requires an explicit, ID-named USER approval for that on a real shared
record, and no disposable alternative exists (the public page renders the
first UsefulLinksPage record only). They are fully scripted and run only when
QC_ALLOW_USEFUL_LINKS_PAGE_OUTAGE=109803 is set.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import allure
import pytest

from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.useful_links.useful_links_page_admin_page import (
    DIRECTORY_EYEBROW,
    DIRECTORY_HEADING,
    DIRECTORY_SUBTEXT,
    EYEBROW_LABEL,
    MSG_SAVED_AND_PUBLISHED,
    PAGE_TITLE,
    SINGLETON_ENTRY_ID,
    UsefulLinksPageAdminPage,
    UsefulLinksPublicView,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

PBI = "130702"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
HERO_JPG = str(FIXTURES / "useful_links_page_qctest_hero-illustration.jpg")          # 800 KB
HERO_GIF = str(FIXTURES / "useful_links_page_qctest_hero-illustration.gif")
HERO_OVERSIZED = str(FIXTURES / "useful_links_page_qctest_hero-oversized-2_4mb.jpg")  # 2.4 MB

SINGLETON_GROUP = pytest.mark.xdist_group("useful_links_page_109803")
OUTAGE_APPROVED = os.getenv("QC_ALLOW_USEFUL_LINKS_PAGE_OUTAGE", "") == SINGLETON_ENTRY_ID
requires_outage_approval = pytest.mark.skipif(
    not OUTAGE_APPROVED,
    reason=(
        "BLOCKED pending explicit user approval: this case must take the REAL Useful Links "
        "page (UsefulLinksPage 109803) off the public site (Unpublish/Draft precondition). "
        "standards.md rule 5 of 'Destructive-Precondition Tests Must Use Disposable Test Data' "
        "requires an ID-named user approval; set QC_ALLOW_USEFUL_LINKS_PAGE_OUTAGE=109803 to run."
    ),
)
PUBLIC_POLL_TIMEOUT = 40.0


def _case(tc_id: str, title: str, severity=allure.severity_level.NORMAL, extra=()):
    def wrap(fn):
        fn = allure.title(title)(fn)
        fn = allure.severity(severity)(fn)
        fn = allure.epic("Business Gateway")(fn)
        fn = allure.feature("Useful Links")(fn)
        fn = allure.story("Useful Links Page (CMS)")(fn)
        fn = allure.label("pbi", PBI)(fn)
        fn = allure.label("testcase", tc_id)(fn)
        for mark in (pytest.mark.control_panel, pytest.mark.links, pytest.mark.functional_low,
                     pytest.mark.pbi_130702, getattr(pytest.mark, f"tc_{tc_id}"),
                     pytest.mark.traceability(tc_id), SINGLETON_GROUP, *extra):
            fn = mark(fn)
        return fn
    return wrap


# ---------------------------------------------------------------- helpers
def _poll_public(browser, predicate, locale: str = "en", timeout: float = PUBLIC_POLL_TIMEOUT):
    """Loads the public page in a FRESH logged-out context (standards.md:
    mandatory for visitor-visibility checks) until `predicate(view)` holds
    or the budget runs out. Returns the last view's observations."""
    context = new_context(browser, use_auth_state=False)
    observed = {}
    try:
        view = UsefulLinksPublicView(context.new_page())

        def _check() -> bool:
            view.open_public(locale)
            observed.update(
                status=view.http_status(), visible=view.is_content_visible(),
                eyebrow=view.eyebrow(), title=view.title(), description=view.description_text(),
                hero_src=view.hero_image_src(), intro_eyebrow=view.intro_eyebrow(),
                intro_heading=view.intro_heading(), intro_subtext=view.intro_subtext(),
                body=view.body_text(),
            )
            return bool(predicate(view))

        try:
            wait_until(_check, timeout=timeout, poll=3.0)
            observed["matched"] = True
        except WaitTimeoutError:
            observed["matched"] = False
    finally:
        context.close()
    return observed


def _restore(admin: UsefulLinksPageAdminPage, baseline: dict | None) -> None:
    if baseline is None:
        return
    # Nested so a failed content restore can never skip re-publishing 109803.
    try:
        with allure.step("TEST_OWNED reset: restore the singleton's text fields / description"):
            admin.restore_text_and_description(baseline)
    finally:
        with allure.step("TEST_OWNED reset: leave the singleton Published"):
            assert admin.ensure_published() == STATUS_PUBLISHED, "singleton could not be left Published"


def _submit_and_capture(admin: UsefulLinksPageAdminPage, field=None) -> dict:
    """Clicks the submit ("Save") button and captures, BEFORE any navigation,
    what the page said."""
    admin.submit()
    return {
        "reloaded": admin.save_reloaded(),
        "refusal": admin.refusal_text(),
        "native": admin.native_invalid_messages(),
        "field_native": admin.field_native_message(field) if field is not None and not admin.save_reloaded() else "",
        "success": admin.success_banner(),
        "report": admin.message_report(),
    }


def _assert_required_refusal(outcome: dict, stored: str, baseline_value: str, label: str) -> None:
    allure.attach(outcome["report"], name="save outcome", attachment_type=allure.attachment_type.TEXT)
    message_shown = bool(outcome["field_native"]) or "required" in outcome["refusal"].lower()
    assert not outcome["reloaded"], (
        f"expected Save to be BLOCKED for {label}, but the page saved and reloaded. {outcome['report']}"
    )
    assert message_shown, f"expected a required-field validation message for {label}. {outcome['report']}"
    assert stored == baseline_value, (
        f"prior saved {label} was overwritten: stored={stored!r}, baseline={baseline_value!r}"
    )


def _valid_save_case(page, browser, field, en_value, ar_value, check_public: bool):
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    try:
        with allure.step("Open the Useful Links Page record in Object Authoring (snapshot baseline)"):
            baseline = admin.snapshot()
        with allure.step(f"Enter {field.label} EN {en_value!r} and AR {ar_value!r}"):
            admin.fill_field(field, en_value)
            admin.fill_field(field, ar_value, arabic=True)
            accepted_en = admin.field_text(field)
            accepted_ar = admin.field_text(field, arabic=True)
        with allure.step("Click Save (the form's submit button)"):
            outcome = _submit_and_capture(admin)
        with allure.step("Re-open the record and read the stored values"):
            admin.open_singleton()
            stored_en, stored_ar = admin.field_text(field), admin.field_text(field, arabic=True)
        public = None
        if check_public:
            with allure.step("Load the public page (EN and AR) in a fresh logged-out context"):
                getter = {"directory_eyebrow": "intro_eyebrow", "directory_heading": "intro_heading",
                          "directory_subtext": "intro_subtext"}[field.key]
                public = (
                    _poll_public(browser, lambda v: getattr(v, getter)() == en_value, "en"),
                    _poll_public(browser, lambda v: getattr(v, getter)() == ar_value, "ar"),
                )
        assert accepted_en == en_value and accepted_ar == ar_value, "the fields did not accept the text"
        assert outcome["reloaded"], f"save did not go through: {outcome['report']}"
        assert MSG_SAVED_AND_PUBLISHED in outcome["success"], (
            f"no success message after saving: {outcome['report']}"
        )
        assert (stored_en, stored_ar) == (en_value, ar_value), (
            f"values did not persist: EN={stored_en!r} AR={stored_ar!r}"
        )
        if public is not None:
            en_view, ar_view = public
            assert en_view["matched"], f"EN public directory block did not render {en_value!r}: {en_view}"
            assert ar_view["matched"], f"AR public directory block did not render {ar_value!r}: {ar_view}"
    finally:
        _restore(admin, baseline)


def _empty_or_blank_case(page, field, value: str):
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    try:
        with allure.step("Open the Useful Links Page record (snapshot baseline)"):
            baseline = admin.snapshot()
        with allure.step(f"Set {field.label} EN to {value!r}"):
            admin.fill_field(field, value)
            assert admin.field_text(field) == value
        with allure.step("Click Save"):
            outcome = _submit_and_capture(admin, field)
        with allure.step("Re-open the record and read the stored value"):
            admin.open_singleton()
            stored = admin.field_text(field)
        _assert_required_refusal(outcome, stored, baseline[field.key], f"{field.label} EN = {value!r}")
    finally:
        _restore(admin, baseline)


def _over_length_case(page, field):
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    attempted = ("QCTEST" + "x" * field.limit)[: field.limit + 1]
    try:
        with allure.step("Open the Useful Links Page record (snapshot baseline)"):
            baseline = admin.snapshot()
        with allure.step(f"Type a {field.limit + 1}-character string into {field.label} EN"):
            admin.type_field(field, attempted)
            typed_len = len(admin.field_text(field))
            live_message = admin.refusal_text()
        with allure.step("Click Save"):
            outcome = _submit_and_capture(admin, field)
        with allure.step("Re-open the record and read the stored value"):
            admin.open_singleton()
            stored = admin.field_text(field)
        allure.attach(f"typed_len={typed_len}; live={live_message!r}; {outcome['report']}",
                      name="max-length outcome", attachment_type=allure.attachment_type.TEXT)
        messages = f"{live_message} | {outcome['refusal']}".lower()
        truncated = typed_len <= field.limit
        assert truncated or not outcome["reloaded"], (
            f"a {field.limit + 1}-character {field.label} was neither truncated nor blocked: {outcome['report']}"
        )
        assert any(k in messages for k in ("maximum", "exceeded", "shorten")), (
            f"no max-length validation message for {field.label}: live={live_message!r} {outcome['report']}"
        )
        assert len(stored) <= field.limit, (
            f"stored {field.label} is {len(stored)} characters, over the {field.limit} cap"
        )
    finally:
        _restore(admin, baseline)


# ======================================================== Hero Eyebrow Label
@_case("140700", "Verify that a valid Hero Eyebrow Label EN/AR saves successfully")
def test_140700_valid_hero_eyebrow_label_saves(page, browser):
    _valid_save_case(page, browser, EYEBROW_LABEL, "Business Gateway", "بوابة الأعمال", check_public=False)


@_case("140701", "Verify that an empty Hero Eyebrow Label is rejected on save")
def test_140701_empty_hero_eyebrow_label_rejected(page):
    _empty_or_blank_case(page, EYEBROW_LABEL, "")


@_case("140702", "Verify that an Eyebrow Label exceeding 60 characters is rejected", allure.severity_level.MINOR)
def test_140702_eyebrow_label_over_60_rejected(page):
    _over_length_case(page, EYEBROW_LABEL)


@_case("140703", "Verify that a whitespace-only Eyebrow Label is rejected as empty", allure.severity_level.MINOR)
def test_140703_whitespace_eyebrow_label_rejected(page):
    _empty_or_blank_case(page, EYEBROW_LABEL, " " * 5)


# ================================================================ Page Title
@_case("140704", "Verify that a valid Page Title EN/AR saves successfully")
def test_140704_valid_page_title_saves(page, browser):
    _valid_save_case(page, browser, PAGE_TITLE, "Useful Links", "روابط مفيدة", check_public=False)


@_case("140705", "Verify that an empty Page Title blocks save with the exact required-field message",
       extra=(pytest.mark.regression,))
def test_140705_empty_page_title_exact_required_message(page):
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    try:
        with allure.step("Open the Useful Links Page record (snapshot baseline)"):
            baseline = admin.snapshot()
        with allure.step("EN context: clear Page Title EN and click Save"):
            admin.clear_field(PAGE_TITLE)
            en = _submit_and_capture(admin, PAGE_TITLE)
        with allure.step("AR context: open the same record in the Arabic interface, clear Page Title EN, Save"):
            admin.open_singleton(locale="ar")
            admin.clear_field(PAGE_TITLE)
            ar = _submit_and_capture(admin, PAGE_TITLE)
        with allure.step("Re-open the record and read the stored title"):
            admin.open_singleton()
            stored = admin.field_text(PAGE_TITLE)
        allure.attach(f"EN: {en['report']}\nAR: {ar['report']}", name="messages",
                      attachment_type=allure.attachment_type.TEXT)
        assert not en["reloaded"] and not ar["reloaded"], "save was not blocked with an empty Page Title"
        assert stored == baseline["page_title"], f"prior title not retained: {stored!r}"
        assert "Page title is required." in f"{en['refusal']} {en['field_native']}", (
            "EN context: expected the exact message 'Page title is required.'; page showed "
            f"refusal={en['refusal']!r}, native={en['field_native']!r}"
        )
        assert "عنوان الصفحة مطلوب." in f"{ar['refusal']} {ar['field_native']}", (
            "AR context: expected the exact message 'عنوان الصفحة مطلوب.'; page showed "
            f"refusal={ar['refusal']!r}, native={ar['field_native']!r}"
        )
    finally:
        _restore(admin, baseline)


@_case("140706", "Verify that a Page Title exceeding 120 characters is rejected", allure.severity_level.MINOR)
def test_140706_page_title_over_120_rejected(page):
    _over_length_case(page, PAGE_TITLE)


@_case("140707", "Verify that a whitespace-only Page Title is rejected as empty", allure.severity_level.MINOR)
def test_140707_whitespace_page_title_rejected(page):
    _empty_or_blank_case(page, PAGE_TITLE, " " * 3)


# ========================================================== Hero Description
RICH_TEXT_HTML = (
    "<h2>QCTEST-130702 Useful Links heading</h2>"
    "<ul><li>QCTEST first bullet</li><li>QCTEST second bullet</li></ul>"
    '<p>Visit <a href="https://www.qatarchamber.com">Qatar Chamber</a> for details.</p>'
)


@_case("140708", "Verify that a valid Hero Description with headings, bullets and links saves successfully")
def test_140708_rich_hero_description_saves_with_formatting(page):
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    try:
        with allure.step("Open the Useful Links Page record (snapshot baseline)"):
            baseline = admin.snapshot()
        with allure.step("Enter a heading, a bullet list and a link into Hero Description EN"):
            admin.set_hero_description_source(RICH_TEXT_HTML)
            editor_text = admin.hero_description_text()
        with allure.step("Click Save"):
            outcome = _submit_and_capture(admin)
        with allure.step("Reload the record and read the stored Hero Description"):
            admin.open_singleton()
            stored = admin.hero_description_html()
        allure.attach(stored, name="stored hero description", attachment_type=allure.attachment_type.TEXT)
        assert "QCTEST-130702 Useful Links heading" in editor_text, "editor did not accept the formatted content"
        assert outcome["reloaded"], f"save did not go through: {outcome['report']}"
        assert "<h2" in stored, f"heading style lost on reload: {stored!r}"
        assert "<ul" in stored and stored.count("<li") >= 2, f"bullets lost on reload: {stored!r}"
        assert 'href="https://www.qatarchamber.com' in stored, f"link lost on reload: {stored!r}"
    finally:
        _restore(admin, baseline)


def _hero_description_blank_case(page, typed: str | None):
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    try:
        with allure.step("Open the Useful Links Page record (snapshot baseline)"):
            baseline = admin.snapshot()
        with allure.step("Clear Hero Description EN" + (f" and type {typed!r}" if typed else "")):
            admin.clear_hero_description()
            if typed:
                admin.type_into_hero_description(typed)
            mirror = admin.hero_description_required_mirror()
        with allure.step("Click Save"):
            outcome = _submit_and_capture(admin)
        with allure.step("Re-open the record and read the stored Hero Description"):
            admin.open_singleton()
            stored = admin.hero_description_html()
        allure.attach(f"required-mirror={mirror!r}; {outcome['report']}", name="save outcome",
                      attachment_type=allure.attachment_type.TEXT)
        assert not outcome["reloaded"], (
            f"expected Save to be BLOCKED for Hero Description {typed!r}, but it saved. {outcome['report']}"
        )
        assert outcome["native"] or "required" in outcome["refusal"].lower(), (
            f"no required-field validation message: {outcome['report']}"
        )
        assert " ".join(stored.split()) == " ".join(baseline["hero_description"].split()), (
            f"stored Hero Description changed: {stored!r}"
        )
    finally:
        _restore(admin, baseline)


@_case("140709", "Verify that an empty Hero Description blocks save")
def test_140709_empty_hero_description_blocks_save(page):
    _hero_description_blank_case(page, None)


@_case("140710", "Verify that a whitespace-only Hero Description is rejected as empty", allure.severity_level.MINOR)
def test_140710_whitespace_hero_description_rejected(page):
    _hero_description_blank_case(page, " ")


# =============================================================== Hero Banner
def _library_stem(file_name: str) -> str:
    """File stem without the " (N)" suffixes Documents & Media appends when
    the same name is uploaded again ("x (2).png" -> "x")."""
    return re.sub(r"(\s\(\d+\))+$", "", Path(file_name).stem)


def _restore_banner(admin: UsefulLinksPageAdminPage, baseline: dict, original_path: str) -> None:
    """Puts the ORIGINAL banner bytes back (re-uploaded under the original
    file name) when the stored banner no longer matches the baseline."""
    admin.open_singleton()
    current = admin.hero_banner_file()
    stem = _library_stem(baseline["hero_banner"])
    if _library_stem(current) == stem:
        # NOTE: a byte-identical re-upload is stored by Documents & Media as
        # "<name> (N).png" (a new library file); re-pointing at the original
        # file is not possible here - the picker's search hits the dev
        # instance's licence page. Reported in the batch report.
        return
    with allure.step(f"TEST_OWNED reset: re-upload the original banner bytes {baseline['hero_banner']!r}"):
        admin.upload_hero_banner(original_path)
        admin.submit()
        admin.open_singleton()
        assert _library_stem(admin.hero_banner_file()) == stem, (
            f"banner restore failed: stored {admin.hero_banner_file()!r}, expected {baseline['hero_banner']!r}"
        )


@_case("140711", "Verify that a valid Hero Banner image (JPG, under 2MB) uploads successfully")
def test_140711_valid_hero_banner_jpg_uploads(page, browser, tmp_path):
    admin = UsefulLinksPageAdminPage(page)
    baseline, original = None, ""
    try:
        with allure.step("Open the record and capture the current banner (bytes kept for restore)"):
            baseline = admin.snapshot()
            original = admin.download_hero_banner(str(tmp_path))
            assert original, "precondition: the singleton has no current Hero Banner to restore later"
        with allure.step("Click upload for Hero Banner and select the 800 KB JPG"):
            result = admin.try_hero_banner_upload(HERO_JPG)
            pending = admin.hero_banner_pending_name()
        with allure.step("Click Save"):
            outcome = _submit_and_capture(admin)
        with allure.step("Re-open the record and read the stored banner"):
            admin.open_singleton()
            stored = admin.hero_banner_file()
        stem = Path(HERO_JPG).stem
        with allure.step("Load the public page in a fresh logged-out context"):
            public = _poll_public(browser, lambda v: stem in v.hero_image_src())
        allure.attach(f"picker={result}; pending={pending!r}; stored={stored!r}; {outcome['report']}",
                      name="upload outcome", attachment_type=allure.attachment_type.TEXT)
        assert result["accepted"] and result["added"] and not result["rejection"], f"JPG not accepted: {result}"
        assert stem in pending, f"no preview/filename shown for the selected JPG: {pending!r}"
        assert outcome["reloaded"], f"save did not go through: {outcome['report']}"
        assert stored.startswith(stem), f"banner not stored: {stored!r}"
        assert public["matched"], f"public hero does not render the new banner: {public.get('hero_src')!r}"
    finally:
        if baseline is not None and original:
            _restore_banner(admin, baseline, original)
        _restore(admin, baseline)


@_case("140712", "Verify that an unsupported Hero Banner file format is rejected", allure.severity_level.MINOR)
def test_140712_unsupported_hero_banner_format_rejected(page, tmp_path):
    admin = UsefulLinksPageAdminPage(page)
    baseline, original = None, ""
    try:
        with allure.step("Open the record and capture the current banner"):
            baseline = admin.snapshot()
            original = admin.download_hero_banner(str(tmp_path))
        with allure.step("Click upload for Hero Banner and select hero-illustration.gif"):
            result = admin.try_hero_banner_upload(HERO_GIF)
            pending = admin.hero_banner_pending_name()
        with allure.step("Click Save"):
            outcome = _submit_and_capture(admin)
        with allure.step("Re-open the record and read the stored banner"):
            admin.open_singleton()
            stored = admin.hero_banner_file()
        allure.attach(f"picker={result}; pending={pending!r}; stored={stored!r}; {outcome['report']}",
                      name="upload outcome", attachment_type=allure.attachment_type.TEXT)
        assert result["rejection"] and not result["added"], f"GIF was not rejected: {result}"
        assert "extension" in result["rejection"].lower() or "not supported" in result["rejection"].lower(), (
            f"rejection is not a format-not-supported message: {result['rejection']!r}"
        )
        assert Path(HERO_GIF).stem not in pending, f"a preview was set for the rejected GIF: {pending!r}"
        assert stored == baseline["hero_banner"], f"banner changed after saving: {stored!r}"
    finally:
        if baseline is not None and original:
            _restore_banner(admin, baseline, original)
        _restore(admin, baseline)


@_case("140713", "Verify that a Hero Banner image over 2MB is rejected", allure.severity_level.MINOR)
def test_140713_oversized_hero_banner_rejected(page, tmp_path):
    admin = UsefulLinksPageAdminPage(page)
    baseline, original = None, ""
    try:
        with allure.step("Open the record and capture the current banner"):
            baseline = admin.snapshot()
            original = admin.download_hero_banner(str(tmp_path))
        with allure.step("Click upload for Hero Banner and select the 2.4 MB JPG"):
            result = admin.try_hero_banner_upload(HERO_OVERSIZED)
            form_feedback = admin.refusal_text()
        with allure.step("Click Save"):
            outcome = _submit_and_capture(admin)
        with allure.step("Re-open the record and read the stored banner"):
            admin.open_singleton()
            stored = admin.hero_banner_file()
        allure.attach(f"picker={result}; form={form_feedback!r}; stored={stored!r}; {outcome['report']}",
                      name="upload outcome", attachment_type=allure.attachment_type.TEXT)
        size_message = " ".join((result["rejection"], form_feedback, outcome["refusal"])).lower()
        assert any(k in size_message for k in ("size", "no larger than", "exceed", "too large")), (
            "no file-size-exceeded message for a 2.4 MB image: "
            f"picker={result['rejection']!r} form={form_feedback!r} save={outcome['refusal']!r}"
        )
        assert stored == baseline["hero_banner"], (
            f"the 2.4 MB image replaced the banner: stored {stored!r} (baseline {baseline['hero_banner']!r})"
        )
    finally:
        if baseline is not None and original:
            _restore_banner(admin, baseline, original)
        _restore(admin, baseline)


# ==================================================== Directory Intro fields
@_case("140714", "Verify that a valid Directory Intro Eyebrow EN/AR saves successfully")
def test_140714_valid_directory_eyebrow_saves(page, browser):
    _valid_save_case(page, browser, DIRECTORY_EYEBROW, "Official directory", "الدليل الرسمي", check_public=True)


@_case("140715", "Verify that an empty Directory Intro Eyebrow blocks save")
def test_140715_empty_directory_eyebrow_blocks_save(page):
    _empty_or_blank_case(page, DIRECTORY_EYEBROW, "")


@_case("140716", "Verify that a Directory Intro Eyebrow exceeding 100 characters is rejected",
       allure.severity_level.MINOR)
def test_140716_directory_eyebrow_over_100_rejected(page):
    _over_length_case(page, DIRECTORY_EYEBROW)


@_case("140717", "Verify that a whitespace-only Directory Intro Eyebrow is rejected as empty",
       allure.severity_level.MINOR)
def test_140717_whitespace_directory_eyebrow_rejected(page):
    _empty_or_blank_case(page, DIRECTORY_EYEBROW, " " * 4)


@_case("140718", "Verify that a valid Directory Intro Heading EN/AR saves successfully")
def test_140718_valid_directory_heading_saves(page, browser):
    _valid_save_case(page, browser, DIRECTORY_HEADING, "Find the right organization",
                     "ابحث عن المنظمة المناسبة", check_public=True)


@_case("140719", "Verify that an empty Directory Intro Heading blocks save")
def test_140719_empty_directory_heading_blocks_save(page):
    _empty_or_blank_case(page, DIRECTORY_HEADING, "")


@_case("140720", "Verify that a Directory Intro Heading exceeding 120 characters is rejected",
       allure.severity_level.MINOR)
def test_140720_directory_heading_over_120_rejected(page):
    _over_length_case(page, DIRECTORY_HEADING)


@_case("140721", "Verify that a whitespace-only Directory Intro Heading is rejected as empty",
       allure.severity_level.MINOR)
def test_140721_whitespace_directory_heading_rejected(page):
    _empty_or_blank_case(page, DIRECTORY_HEADING, " " * 3)


# The case says only "the subtext ... and its AR equivalent": the concrete
# values used are the page's own published copy (EN + AR).
DIRECTORY_SUBTEXT_EN = "Browse by category or search directly by organization name or website."
DIRECTORY_SUBTEXT_AR = "تصفّح حسب الفئة أو ابحث مباشرة باسم المنظمة أو موقعها الإلكتروني."


@_case("140722", "Verify that a valid Directory Intro Subtext EN/AR saves successfully")
def test_140722_valid_directory_subtext_saves(page, browser):
    _valid_save_case(page, browser, DIRECTORY_SUBTEXT, DIRECTORY_SUBTEXT_EN, DIRECTORY_SUBTEXT_AR, check_public=True)


@_case("140723", "Verify that an empty Directory Intro Subtext blocks save")
def test_140723_empty_directory_subtext_blocks_save(page):
    _empty_or_blank_case(page, DIRECTORY_SUBTEXT, "")


@_case("140724", "Verify that a Directory Intro Subtext exceeding 250 characters is rejected",
       allure.severity_level.MINOR)
def test_140724_directory_subtext_over_250_rejected(page):
    _over_length_case(page, DIRECTORY_SUBTEXT)


@_case("140725", "Verify that a whitespace-only Directory Intro Subtext is rejected as empty",
       allure.severity_level.MINOR)
def test_140725_whitespace_directory_subtext_rejected(page):
    _empty_or_blank_case(page, DIRECTORY_SUBTEXT, " " * 6)


# ================================================= Draft / Preview / Publish
DRAFT_TITLE = "QCTEST-130702 Draft Title"


def _unpublish_and_draft_change(admin: UsefulLinksPageAdminPage, new_title: str) -> str:
    """Precondition shared by 140778-140780: take the singleton to Draft with
    a Page Title change saved as a draft. Returns the resulting row status."""
    if admin.singleton_row_status() == STATUS_PUBLISHED:
        admin.unpublish_singleton()
    admin.open_singleton()
    admin.fill_field(PAGE_TITLE, new_title)
    admin.save_draft()
    return admin.singleton_row_status()


@requires_outage_approval
@_case("140778", "Verify that saving the Useful Links page as Draft keeps it hidden from the public site")
def test_140778_save_as_draft_keeps_change_off_public_site(page, browser):
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    try:
        with allure.step("Snapshot the published singleton"):
            baseline = admin.snapshot()
        with allure.step(f"Make a content change (Page Title EN = {DRAFT_TITLE!r}) and click Save as Draft"):
            status = _unpublish_and_draft_change(admin, DRAFT_TITLE)
        with allure.step("Load the public page in a fresh logged-out browser context"):
            public = _poll_public(browser, lambda v: v.title() == baseline["page_title"], timeout=20.0)
        assert status == STATUS_DRAFT, f"page status is {status!r}, expected Draft"
        assert DRAFT_TITLE not in public.get("body", ""), "DRAFT LEAK: the draft title reached the public page"
        assert public["matched"], (
            "the public page does not show the last Published content "
            f"(title {baseline['page_title']!r}); visitor saw title={public.get('title')!r}, "
            f"content visible={public.get('visible')}"
        )
    finally:
        _restore(admin, baseline)


@requires_outage_approval
@_case("140779", "Verify that Preview shows the Draft content without publishing it live",
       allure.severity_level.MINOR)
def test_140779_preview_shows_draft_not_live(page, browser):
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    try:
        with allure.step("Snapshot and put the singleton in Draft with a title change"):
            baseline = admin.snapshot()
            status = _unpublish_and_draft_change(admin, DRAFT_TITLE)
        with allure.step("Click Preview on the Draft page (CMS-authenticated preview surface)"):
            admin.open_list()
            preview_url = admin.row_preview_url_by_id(SINGLETON_ENTRY_ID)
            preview = UsefulLinksPublicView(page)
            preview.page.goto(preview_url, wait_until="domcontentloaded", timeout=90000)
            try:
                wait_until(lambda: preview.title() == DRAFT_TITLE, timeout=30.0, poll=1.0)
            except WaitTimeoutError:
                pass
            preview_title, preview_body = preview.title(), preview.body_text()
        with allure.step("In parallel, load the public page in a fresh logged-out context"):
            public = _poll_public(browser, lambda v: v.title() == baseline["page_title"], timeout=20.0)
        assert status == STATUS_DRAFT, f"precondition: status {status!r}"
        assert preview_title == DRAFT_TITLE, f"preview does not show the draft title: {preview_title!r}"
        assert "PREVIEW" in preview_body, "preview banner missing on the preview surface"
        assert DRAFT_TITLE not in public.get("body", ""), "DRAFT LEAK: the draft reached the public page"
        assert public["matched"], (
            "logged-out public page does not show the last Published content; visitor saw "
            f"title={public.get('title')!r}, visible={public.get('visible')}"
        )
    finally:
        _restore(admin, baseline)


@requires_outage_approval
@_case("140780", "Verify that Publish makes the current content live and shows the success toast",
       extra=(pytest.mark.regression, pytest.mark.web))
def test_140780_publish_makes_content_live_with_toast(page, browser):
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    new_title = "QCTEST-130702 Published Title"
    try:
        with allure.step("Snapshot and put the singleton in Draft with a title change"):
            baseline = admin.snapshot()
            history_before = len(admin.singleton_history())
            status = _unpublish_and_draft_change(admin, new_title)
        with allure.step("Click Publish on the Draft page"):
            admin.open_singleton()
            outcome = _submit_and_capture(admin)
            status_after = admin.singleton_row_status()
            history_after = admin.singleton_history()
        with allure.step("Load the public page in a fresh logged-out browser context"):
            public = _poll_public(browser, lambda v: v.title() == new_title)
        assert status == STATUS_DRAFT, f"precondition: status {status!r}"
        assert outcome["reloaded"] and MSG_SAVED_AND_PUBLISHED in outcome["success"], (
            f"no publish success message: {outcome['report']}"
        )
        assert status_after == STATUS_PUBLISHED, f"status after Publish: {status_after!r}"
        assert len(history_after) > history_before, f"publish not recorded in History: {history_after}"
        assert public["matched"], f"public page does not reflect the published title: {public.get('title')!r}"
    finally:
        _restore(admin, baseline)


@requires_outage_approval
@_case("140781", "Verify that Unpublish removes the page/content from public visibility",
       extra=(pytest.mark.web,))
def test_140781_unpublish_removes_page_from_public(page, browser):
    admin = UsefulLinksPageAdminPage(page)
    baseline = None
    try:
        with allure.step("Snapshot the published singleton"):
            baseline = admin.snapshot()
            assert admin.singleton_row_status() == STATUS_PUBLISHED, "precondition: page is not Published"
            history_before = len(admin.singleton_history())
        with allure.step("Click Unpublish on the Published page"):
            status = admin.unpublish_singleton()
            history_after = admin.singleton_history()
        with allure.step("Load the public page in a fresh logged-out browser context"):
            public = _poll_public(browser, lambda v: not v.is_content_visible())
        assert status == STATUS_UNPUBLISHED, f"status after Unpublish: {status!r}"
        assert len(history_after) > history_before, f"unpublish not recorded in History: {history_after}"
        assert public["matched"], (
            f"the unpublished page is still visible to an anonymous visitor: title={public.get('title')!r}"
        )
    finally:
        _restore(admin, baseline)
