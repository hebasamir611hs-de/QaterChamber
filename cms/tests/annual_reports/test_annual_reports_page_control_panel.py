"""
cms/tests/annual_reports/test_annual_reports_page_control_panel.py —
Control_Panel cases of PBI 130712 ("QC - Insights & Media - 004 - Annual
Reports", Azure suite 140371, plan 137724) that target the page-level
singleton object `manage-annual-reports-page` (hero + Report Archive section
header). The per-report object (`manage-ann-rpt`) is covered by
test_annual_reports_control_panel.py.

ACCOUNT: none of these cases names a role. Every edit and publish runs as the
Site Content Editor (156488) — the role that owns page content and publishes
directly ("As an Editor, what you publish here goes live straight away.") —
in an auth-free context, with the signed-in userId re-checked before each
save. TEST_USER is used only by the `singleton` fixture, to snapshot the record
before the test and restore it afterwards.

TEST_OWNED SINGLETON: `QCDEMO-130712-PAGE-MAIN` (entry 144940) is the real
live page content and the only record the public page reads. Each test:
  - snapshots every field (EN + AR), Active Status, the banner file and its
    bytes (sha256) BEFORE it changes anything, and refuses to start when the
    record does not look like the real content (blank / QCTEST values left
    over from an interrupted run);
  - restores whatever differs in the fixture teardown, re-publishes, and
    verifies the restore from a fresh open (values + banner bytes + row
    status Published) — a restore that does not verify fails the run loudly;
  - never deletes, never unpublishes, never creates a record on this object.
All tests share one xdist group so two of them never touch the record at once.

PUBLIC CHECKS run in a fresh logged-out context, after the CMS reports the
save and after Active Status is confirmed ticked (standards.md: Published AND
Active Status are both required for visibility). The page record the public
fragment itself fetches (`/o/c/annualreportspages/...`) is kept as network
evidence. Budget: 20 s polling at 2 s (cms-profile.md measures ~0 s
propagation; each poll is a full page load).

SUBSTITUTIONS (case literal -> what runs), disclosed:
  - 143662 "banner.gif" -> a uniquely named copy of
    fixtures/annual_reports_page_qctest_banner.gif (Documents & Media refuses
    repeated same-name uploads); 143660/143663 likewise.
  - 143664 "Select Status=Published": this object has NO page "Status"
    picklist — the only status controls are the `Active Status` checkbox and
    the editorial workflow's Publish button. The case is run as: Active Status
    ticked + Publish (the observed controls are attached as evidence).
  - 143827 / 143828 "page Status remains unpublished": the singleton is the
    live, Published page; taking it offline is an outage. The equivalent
    "nothing was published" is asserted instead: the row status and the
    stored Arabic values are unchanged after the refused attempt.

SKIPPED:
  - 143650, 143654, 143658, 143669, 143713, 143717: field character-limit
    cases, skipped by QA decision (run 2026-10-04).
  - 143665 / 143666: both start by creating a NEW record on this singleton
    object; it could not be removed again (no deletes on this object), so
    they are blocked pending a QA decision. 143665 still records, read-only,
    what the create form offers as a "Status" control.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import allure
import pytest

from cms.pages.annual_reports.annual_reports_page_admin_page import (
    ARCHIVE_FIELDS,
    EYEBROW,
    HERO_DESCRIPTION,
    HERO_FIELDS,
    MSG_ARABIC_REQUIRED_AR,
    MSG_ARABIC_REQUIRED_EN,
    MSG_SAVED_AND_PUBLISHED,
    PAGE_TITLE,
    QCTEST_MARK,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    SECTION_BADGE,
    SECTION_DESCRIPTION,
    SECTION_TITLE,
    SINGLETON_ENTRY_CODE,
    AnnualReportsPageAdminPage,
    AnnualReportsPublicView,
    norm,
    unique_copy,
)
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from core.utils.reporting import attach_screenshot
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context
from config.settings import settings

PBI = "130712"
AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
SINGLETON_GROUP = pytest.mark.xdist_group("annual_reports_page_144940")
FIXTURES = Path(__file__).resolve().parent / "fixtures"
BANNER_JPG_1_5MB = str(FIXTURES / "annual_reports_page_qctest_banner_1_5mb.jpg")
BANNER_GIF = str(FIXTURES / "annual_reports_page_qctest_banner.gif")
BANNER_PNG_2_5MB = str(FIXTURES / "annual_reports_page_qctest_banner_2_5mb.png")

PUBLIC_REFLECT_TIMEOUT = 20.0
PUBLIC_POLL = 2.0
CONTACT_URL = "https://qcdev.ihorizons.com/en/contact-us"

FIELD_LIMIT_SKIP = pytest.mark.skip(reason="field character-limit case skipped by QA decision (run 2026-10-04)")
NEW_RECORD_BLOCKED = (
    "BLOCKED pending a QA decision: this case starts by creating a NEW record on the Annual Reports Page "
    "object, whose only record ({code}) is the live page. A second record could not be removed again "
    "(no deletes are allowed on this object), so automation does not create one."
).format(code=SINGLETON_ENTRY_CODE)


def _case(tc_id: str, title: str, story: str, category=pytest.mark.functional_low,
          severity=allure.severity_level.NORMAL, extra=()):
    def wrap(fn):
        fn = allure.title(title)(fn)
        fn = allure.severity(severity)(fn)
        fn = allure.epic("Insights & Media")(fn)
        fn = allure.feature("Annual Reports — Control Panel")(fn)
        fn = allure.story(story)(fn)
        fn = allure.label("pbi", PBI)(fn)
        fn = allure.label("testcase", tc_id)(fn)
        for mark in (pytest.mark.control_panel, pytest.mark.media, category, pytest.mark.pbi_130712,
                     getattr(pytest.mark, f"tc_{tc_id}"), SINGLETON_GROUP, *extra):
            fn = mark(fn)
        return fn
    return wrap


# ===========================================================================
# Fixtures
# ===========================================================================
class SingletonGuard:
    def __init__(self, baseline: dict, banner_path: str):
        self.baseline = baseline
        self.banner_path = banner_path


def _looks_real(baseline: dict) -> list[str]:
    """Values that do not look like the real page content (blank or QCTEST)."""
    bad = []
    for key in AnnualReportsPageAdminPage.text_keys():
        value = norm(baseline.get(key))
        if not value or QCTEST_MARK in value or "QCTEST" in value:
            bad.append(f"{key}={baseline.get(key)!r}")
    if not baseline.get("banner_sha256"):
        bad.append("banner: no file stored")
    if not baseline.get("active_status"):
        bad.append("Active Status unticked")
    if baseline.get("row_status") != STATUS_PUBLISHED:
        bad.append(f"row status {baseline.get('row_status')!r}")
    return bad


@pytest.fixture
def singleton(browser, tmp_path):
    """TEST_OWNED guard for QCDEMO-130712-PAGE-MAIN: snapshot first (TEST_USER),
    restore + verify afterwards (fresh TEST_USER context). The restore runs in
    teardown so a failing test's evidence is captured before it."""
    ctx = new_context(browser)  # TEST_USER storageState — snapshot/restore only
    try:
        keeper = AnnualReportsPageAdminPage(ctx.new_page())
        baseline = keeper.snapshot()
        banner_path = keeper.download_banner(str(tmp_path))
    finally:
        ctx.close()
    allure.attach(repr(baseline), name="singleton baseline (before the test)")
    bad = _looks_real(baseline)
    if bad:
        pytest.fail(
            f"PRECONDITION: {SINGLETON_ENTRY_CODE} does not look like the real live page content ({bad}); "
            f"refusing to edit it — restore it by hand first (an earlier run may have been interrupted)."
        )
    if not banner_path or hashlib.sha256(Path(banner_path).read_bytes()).hexdigest() != baseline["banner_sha256"]:
        pytest.fail("PRECONDITION: the original Hero Banner bytes could not be captured for the restore")
    yield SingletonGuard(baseline, banner_path)

    ctx = new_context(browser)
    report = None
    try:
        keeper = AnnualReportsPageAdminPage(ctx.new_page())
        report = keeper.restore(baseline, banner_path)
    finally:
        ctx.close()
    allure.attach(
        f"changed before restore: {report['changed'] if report else '?'}\n"
        f"remaining after restore: {report['remaining'] if report else '?'}\n"
        f"final: {report['final'] if report else '?'}",
        name="TEST_OWNED restore of the singleton",
    )
    if report is None or report["remaining"]:
        raise AssertionError(
            f"SINGLETON NOT RESTORED: {SINGLETON_ENTRY_CODE} still differs from its baseline in "
            f"{report['remaining'] if report else 'unknown fields'} — fix it by hand (baseline attached)."
        )


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public read (standards.md)."""
    contexts = []

    def _make():
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        return ctx.new_page()

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# Helpers (test layer — no raw Playwright)
# ===========================================================================
def _editor(page) -> AnnualReportsPageAdminPage:
    """Signs in as the Site Content Editor in this auth-free context; skips
    (never falls back) when the account cannot sign in or is not the pinned one."""
    admin = AnnualReportsPageAdminPage(page)
    outcome = admin.login_as_role(ROLE_EDITOR)
    if outcome == "auth_failed":
        pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{ROLE_EDITOR}'")
    if outcome != "ok":
        pytest.fail(f"login as '{ROLE_EDITOR}' neither succeeded nor showed Liferay's refusal banner")
    admin.open_list()
    user_id, _ = admin.signed_in_user()
    if user_id != ROLE_USER_IDS[ROLE_EDITOR]:
        pytest.skip(f"PRECONDITION: '{ROLE_EDITOR}' signs in as userId {user_id!r}, "
                    f"not the pinned {ROLE_USER_IDS[ROLE_EDITOR]}")
    return admin


def _pinned(admin: AnnualReportsPageAdminPage) -> None:
    user_id, _ = admin.signed_in_user()
    assert user_id == ROLE_USER_IDS[ROLE_EDITOR], (
        f"the session is now userId {user_id!r}, not the pinned {ROLE_EDITOR} ({ROLE_USER_IDS[ROLE_EDITOR]}) — "
        f"nothing from here on would be attributable to that role"
    )


def _assert_refusal_on(outcome: dict, keys: set, what: str) -> None:
    """The refused attempt must point at the control(s) under test — a
    refusal caused by some other control would prove nothing about the case."""
    flagged = AnnualReportsPageAdminPage.flagged_controls(outcome)
    assert keys & flagged or (not flagged and outcome["new_bars"]), (
        f"Publish was refused, but not because of {what}: the attempt flagged {sorted(flagged) or 'no control'} "
        f"({outcome['errors_by_control']}, invalid events {outcome['native_invalid_events']})"
    )


def _publish(admin: AnnualReportsPageAdminPage, what: str) -> dict:
    """Clicks Publish as the pinned Editor and returns what the page showed."""
    _pinned(admin)
    admin.submit()
    outcome = admin.outcome()
    allure.attach(repr(outcome), name=f"Publish outcome ({what})")
    try:
        attach_screenshot(admin.page.screenshot(), f"130712-page {what}", settings.project_name,
                          settings.reports_dir)
    except Exception:  # noqa: BLE001 — evidence only
        pass
    return outcome


def _require_active_status(admin: AnnualReportsPageAdminPage) -> None:
    """User rule + standards.md: Active Status must be stored ticked (and the
    record Published) before ANY public check."""
    admin.open_singleton()
    ticked = admin.active_status_checked()
    status = admin.singleton_row_status()
    allure.attach(f"Active Status ticked: {ticked}\nrow status: {status}", name="Active Status precondition")
    if not ticked or status != STATUS_PUBLISHED:
        pytest.fail(f"PRECONDITION NOT MET: the page record stores Active Status={ticked} with status {status!r}; "
                    f"both 'ticked' and 'Published' are required before checking the public page")


def _public(anon_pages, predicate, locale: str, tc_id: str) -> tuple[bool, AnnualReportsPublicView]:
    """Publish-then-poll on the delivery surface in ONE logged-out context.
    Attaches the page-record network evidence and a screenshot."""
    view = AnnualReportsPublicView(anon_pages())
    matched = {"ok": False}

    def _check() -> bool:
        view.open_public(locale)
        matched["ok"] = bool(predicate(view))
        return matched["ok"]

    try:
        wait_until(_check, timeout=PUBLIC_REFLECT_TIMEOUT, poll=PUBLIC_POLL)
    except WaitTimeoutError:
        pass
    allure.attach(view.network_summary(), name=f"public page record ({locale}) — network evidence")
    try:
        attach_screenshot(view.page.screenshot(), f"{tc_id}-public-{locale}", settings.project_name,
                          settings.reports_dir)
    except Exception:  # noqa: BLE001
        pass
    record = view.page_record()
    if record and record.get("activeStatus") is not True:
        pytest.fail(f"the page record the public fragment fetched has activeStatus={record.get('activeStatus')!r}")
    return matched["ok"], view


PUBLIC_GETTER = {
    EYEBROW.key: "eyebrow", PAGE_TITLE.key: "title", HERO_DESCRIPTION.key: "hero_desc",
    SECTION_BADGE.key: "badge", SECTION_TITLE.key: "section_title", SECTION_DESCRIPTION.key: "section_desc",
}


def _plain(html: str) -> str:
    return norm(re.sub(r"<[^>]+>", " ", html)).replace(" .", ".")


def _prime_with_temporary_value(admin, anon_pages, tc_id: str, field) -> None:
    """When the case's literal value equals the live baseline, publish a
    temporary QCTEST value first and see it live, so the case's own publish
    has to change both the stored record and the public page (no false green)."""
    temp_en, temp_ar = f"QCTEST-130712-{tc_id} EN", f"QCTEST-130712-{tc_id} AR"
    with allure.step(f"Baseline equals the case value: publish a temporary {field.label} first"):
        admin.open_singleton()
        admin.fill_field(field, temp_en)
        admin.fill_field(field, temp_ar, arabic=True)
        outcome = _publish(admin, f"{tc_id}-prime")
    assert outcome["reloaded"], f"could not publish the temporary {field.label}: {outcome}"
    getter = PUBLIC_GETTER[field.key]
    ok, view = _public(anon_pages, lambda v: getattr(v, getter)() == temp_en, "en", f"{tc_id}-prime")
    assert ok, f"the temporary {field.label} {temp_en!r} never reached the live page: {getattr(view, getter)()!r}"


def _valid_value_case(page, anon_pages, tc_id: str, field, en_value: str, ar_value: str,
                      singleton=None) -> None:
    """Enter EN/AR, Publish, then the live page (EN and AR) must show them."""
    admin = _editor(page)
    if singleton is not None and (
        norm(singleton.baseline[field.key]) == norm(en_value)
        or norm(singleton.baseline[field.key + "_ar"]) == norm(ar_value)
    ):
        _prime_with_temporary_value(admin, anon_pages, tc_id, field)
    with allure.step(f"Open the Annual Reports Page record and enter {field.label} EN {en_value!r} / AR {ar_value!r}"):
        admin.open_singleton()
        admin.fill_field(field, en_value)
        admin.fill_field(field, ar_value, arabic=True)
        accepted = (admin.field_text(field), admin.field_text(field, arabic=True))
    with allure.step("Publish"):
        outcome = _publish(admin, tc_id)
    with allure.step("Re-open the record and read the stored values"):
        admin.open_singleton()
        stored = (admin.field_text(field), admin.field_text(field, arabic=True))
    assert accepted == (en_value, ar_value), f"the fields did not take the values as entered: {accepted}"
    assert outcome["reloaded"], f"Publish did not go through: {AnnualReportsPageAdminPage.refusal_text(outcome)} {outcome}"
    assert AnnualReportsPageAdminPage.success_message(outcome), (
        f"no {MSG_SAVED_AND_PUBLISHED!r} message after Publish (the save itself went through); "
        f"edit-bar messages shown: {outcome['banners']}"
    )
    assert (norm(stored[0]), norm(stored[1])) == (norm(en_value), norm(ar_value)), (
        f"values did not persist: stored EN={stored[0]!r} AR={stored[1]!r}"
    )
    _require_active_status(admin)
    getter = PUBLIC_GETTER[field.key]
    want_en = _plain(en_value) if field.rich else norm(en_value)
    want_ar = _plain(ar_value) if field.rich else norm(ar_value)
    with allure.step("Load the live Annual Reports page (EN and AR) in a fresh logged-out context"):
        en_ok, en_view = _public(anon_pages, lambda v: getattr(v, getter)() == want_en, "en", tc_id)
        ar_ok, ar_view = _public(anon_pages, lambda v: getattr(v, getter)() == want_ar, "ar", tc_id)
    assert en_ok, f"the live EN page does not show {field.label} {want_en!r}; it shows {getattr(en_view, getter)()!r}"
    assert ar_ok, f"the live AR page does not show {field.label} {want_ar!r}; it shows {getattr(ar_view, getter)()!r}"


def _blank_case(page, singleton, tc_id: str, field, value: str,
                admin: AnnualReportsPageAdminPage | None = None) -> dict:
    """Set `field` EN to `value` (empty / whitespace), Publish, require a
    refused publish with a required-field message and the stored value kept."""
    admin = admin or _editor(page)
    with allure.step(f"Set {field.label} (EN) to {value!r}"):
        admin.open_singleton()
        admin.fill_field(field, value)
        entered = admin.field_text(field)
        native_before = admin.field_native_message(field)
    with allure.step("Attempt Publish"):
        outcome = _publish(admin, tc_id)
    with allure.step("Re-open the record and read the stored value"):
        admin.open_singleton()
        stored = admin.field_text(field)
    refusal = AnnualReportsPageAdminPage.refusal_text(outcome)
    allure.attach(f"entered={entered!r}; native message on the field before Publish={native_before!r}; "
                  f"refusal={refusal!r}", name="validation evidence")
    assert entered == value, f"the field did not take {value!r}: {entered!r}"
    assert not outcome["reloaded"], (
        f"Publish was NOT blocked with {field.label} (EN) = {value!r}: the record was saved and published "
        f"(stored value now {stored!r}; edit-bar messages {outcome['banners']})"
    )
    _assert_refusal_on(outcome, {f"ObjectField_{field.name}"}, f"{field.label} (EN)")
    target_msgs = " | ".join([outcome["native_invalid_events"].get(f"ObjectField_{field.name}", ""),
                              outcome["errors_by_control"].get(f"ObjectField_{field.name}", "")] + outcome["new_bars"])
    assert re.search(r"required|fill out|fill in", target_msgs, re.I), (
        f"Publish was blocked but no required-field validation message was shown for {field.label}: {outcome}"
    )
    assert norm(stored) == norm(singleton.baseline[field.key]), (
        f"the stored {field.label} changed to {stored!r} although Publish was refused"
    )
    return outcome


ARABIC_MSG_WORDING_BUG = "148073"  # Azure bug for the Arabic-required message wording (143827/143828)


def _arabic_empty_case(page, singleton, tc_id: str, fields) -> None:
    """Leave the AR twins of `fields` empty (EN filled), attempt Publish in the
    English and the Arabic interface; require the bilingual refusal message
    and nothing published."""
    admin = _editor(page)
    results = {}
    for locale, expected in (("en", MSG_ARABIC_REQUIRED_EN), ("ar", MSG_ARABIC_REQUIRED_AR)):
        with allure.step(f"[{locale.upper()} interface] fill EN, leave {[f.label for f in fields]} AR empty"):
            admin.open_singleton(locale)
            for field in fields:
                admin.fill_field(field, singleton.baseline[field.key])
                admin.clear_field(field, arabic=True)
            emptied = [admin.field_text(f, arabic=True) for f in fields]
        with allure.step(f"[{locale.upper()} interface] attempt Publish"):
            outcome = _publish(admin, f"{tc_id}-{locale}")
            shown = admin.visible_text() if not outcome["reloaded"] else ""
            shot = Path("reports/screenshots") / f"tc{tc_id}_arabic_required_{locale}.png"
            shot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(shot), full_page=True)
            allure.attach.file(str(shot), name=f"[{locale}] refusal screen", attachment_type=allure.attachment_type.PNG)
        results[locale] = {"expected": expected, "emptied": emptied, "outcome": outcome,
                           "refusal": AnnualReportsPageAdminPage.refusal_text(outcome),
                           "message_shown": expected in AnnualReportsPageAdminPage.refusal_text(outcome)
                           or expected in shown}
    with allure.step("Re-open the record: stored Arabic values and status"):
        admin.open_singleton()
        stored_ar = {f.key: admin.field_text(f, arabic=True) for f in fields}
        status = admin.singleton_row_status()
    allure.attach(repr(results), name="Arabic-empty attempts (EN and AR interface)")
    for locale, res in results.items():
        assert res["emptied"] == [""] * len(fields), f"[{locale}] the Arabic fields did not empty: {res['emptied']}"
        assert not res["outcome"]["reloaded"], (
            f"[{locale} interface] Publish was NOT blocked with the Arabic fields empty — the record was saved"
        )
        _assert_refusal_on(res["outcome"], {f"qc-ar-{f.name}" for f in fields}, f"[{locale}] the empty Arabic fields")
    changed = {k: v for k, v in stored_ar.items() if norm(v) != norm(singleton.baseline[k + "_ar"])}
    assert not changed, f"stored Arabic content changed although Publish was refused: {changed}"
    assert status == STATUS_PUBLISHED, f"the page status changed to {status!r} after the refused publish"
    # QA decision 2026-10-04: the block is the behaviour under test; a wording-only
    # difference is tracked as a low-priority bug and recorded here, not failed on.
    wording = {loc: res["refusal"] for loc, res in results.items() if not res["message_shown"]}
    if wording:
        allure.attach(
            f"Known wording bug {ARABIC_MSG_WORDING_BUG}: expected {MSG_ARABIC_REQUIRED_EN!r} / "
            f"{MSG_ARABIC_REQUIRED_AR!r}, shown {wording!r}",
            name="Arabic-required message wording (known bug)",
        )


# ===========================================================================
# Rich text — 143578 / 143579 / 143656
# ===========================================================================
HERO_RICH_HTML = (
    "<h2>QCTEST-130712 Annual reports at a glance</h2>"
    "<ul><li>Yearly institutional achievements</li><li>Strategic initiatives</li></ul>"
    f'<p>Questions? <a href="{CONTACT_URL}">Contact us</a></p>'
)
HERO_SHORT_RICH_HTML = (
    "<ul><li>QCTEST-130712 yearly reports</li></ul>"
    f'<p><a href="{CONTACT_URL}">Contact Qatar Chamber</a></p>'
)
ARCHIVE_RICH_HTML = (
    "<p>QCTEST-130712 Browse <strong>published annual reports</strong> and "
    f'<a href="{CONTACT_URL}">contact us</a> for printed copies.</p>'
)


def _author_rich(admin, field, html: str, tc_id: str) -> tuple[str, dict, str]:
    admin.open_singleton()
    admin.fill_field(field, html)
    entered = admin.field_text(field)
    outcome = _publish(admin, tc_id)
    admin.open_singleton()
    stored = admin.field_text(field)
    return entered, outcome, stored


@AUTH_FREE_PAGE
@_case("143578", "Hero Description rich text (heading, bullets, link) renders unstripped on the live page",
       "Rich text rendering", category=pytest.mark.ui)
def test_143578_hero_description_rich_text_renders_unstripped(page, singleton, anon_pages):
    # Azure TC 143578 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    with allure.step("Author Hero Description with a heading, a 2-item bullet list and a link; Publish"):
        entered, outcome, stored = _author_rich(admin, HERO_DESCRIPTION, HERO_RICH_HTML, "143578")
    assert entered == HERO_RICH_HTML, f"the editor did not take the content: {entered!r}"
    assert outcome["reloaded"], f"Publish did not go through: {outcome}"
    assert AnnualReportsPageAdminPage.success_message(outcome), f"no publish success message: {outcome['banners']}"
    assert norm(stored) == norm(HERO_RICH_HTML), f"the stored Hero Description differs: {stored!r}"
    _require_active_status(admin)
    with allure.step("Load the live Annual Reports page"):
        ok, view = _public(anon_pages, lambda v: "QCTEST-130712 Annual reports at a glance" in v.hero_desc(),
                           "en", "143578")
        rendered = view.rich_structure(view.HERO_DESC)
    allure.attach(repr(rendered), name="rendered hero description")
    assert ok, f"the live page does not show the new Hero Description: {view.hero_desc()!r}"
    assert not rendered.get("raw_tags_visible"), f"markup is shown as raw text: {rendered.get('text')!r}"
    assert [h["text"] for h in rendered["headings"]] == ["QCTEST-130712 Annual reports at a glance"], (
        f"the heading does not render as a heading: {rendered['headings']}"
    )
    assert any(lst["items"] == ["Yearly institutional achievements", "Strategic initiatives"]
               for lst in rendered["lists"]), f"the bullet list does not render as a real 2-item list: {rendered['lists']}"
    link = [a for a in rendered["links"] if a["text"] == "Contact us"]
    assert link and link[0]["href"] == CONTACT_URL, f"the link is missing or mis-targeted: {rendered['links']}"
    assert link[0]["visible"] and link[0]["clickable"], f"the link is not a visible, clickable anchor: {link[0]}"


@AUTH_FREE_PAGE
@_case("143579", "Report Archive Section Description rich text renders unstripped on the live page",
       "Rich text rendering", category=pytest.mark.ui)
def test_143579_section_description_rich_text_renders_unstripped(page, singleton, anon_pages):
    # Azure TC 143579 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    with allure.step("Author Section Description with a bold phrase and a link; Publish"):
        entered, outcome, stored = _author_rich(admin, SECTION_DESCRIPTION, ARCHIVE_RICH_HTML, "143579")
    assert entered == ARCHIVE_RICH_HTML, f"the field did not take the content: {entered!r}"
    assert outcome["reloaded"], f"Publish did not go through: {outcome}"
    assert AnnualReportsPageAdminPage.success_message(outcome), f"no publish success message: {outcome['banners']}"
    assert norm(stored) == norm(ARCHIVE_RICH_HTML), f"the stored Section Description differs: {stored!r}"
    _require_active_status(admin)
    with allure.step("Load the live page"):
        ok, view = _public(anon_pages, lambda v: "QCTEST-130712 Browse" in v.section_desc(), "en", "143579")
        rendered = view.rich_structure(view.ARCHIVE_DESC)
        markup = view.same_markup(view.ARCHIVE_DESC, ARCHIVE_RICH_HTML)
    allure.attach(f"{rendered}\n{markup}", name="rendered section description")
    assert ok, f"the live page does not show the new Section Description: {view.section_desc()!r}"
    bold = [b for b in rendered["bold"] if b["text"] == "published annual reports"]
    assert bold and int(bold[0]["weight"]) >= 600, f"the bold phrase does not render bold: {rendered['bold']}"
    link = [a for a in rendered["links"] if a["text"] == "contact us"]
    assert link and link[0]["href"] == CONTACT_URL and link[0]["clickable"], (
        f"the link does not render as a clickable anchor: {rendered['links']}"
    )
    assert markup["equal"], (
        f"the live markup is not identical to what was authored:\n rendered {markup['rendered']!r}\n "
        f"authored {markup['authored']!r}"
    )


@AUTH_FREE_PAGE
@_case("143656", "A valid Hero Description with a bullet and a link is saved and displayed", "Hero — Hero Description")
def test_143656_valid_hero_description_saved_and_displayed(page, singleton, anon_pages):
    # Azure TC 143656 | PBI 130712 | account: Site Content Editor
    assert len(HERO_SHORT_RICH_HTML) <= 200
    admin = _editor(page)
    with allure.step("Enter a rich-text description (<=200 chars) with a bullet and a link; Publish"):
        entered, outcome, stored = _author_rich(admin, HERO_DESCRIPTION, HERO_SHORT_RICH_HTML, "143656")
    assert entered == HERO_SHORT_RICH_HTML
    assert outcome["reloaded"], f"Publish did not go through: {outcome}"
    assert AnnualReportsPageAdminPage.success_message(outcome), f"no publish success message: {outcome['banners']}"
    assert norm(stored) == norm(HERO_SHORT_RICH_HTML), f"the stored Hero Description differs: {stored!r}"
    _require_active_status(admin)
    with allure.step("Load the live page"):
        ok, view = _public(anon_pages, lambda v: "QCTEST-130712 yearly reports" in v.hero_desc(), "en", "143656")
        rendered = view.rich_structure(view.HERO_DESC)
    allure.attach(repr(rendered), name="rendered hero description")
    assert ok, f"the live page does not show the new Hero Description: {view.hero_desc()!r}"
    assert not rendered.get("raw_tags_visible"), f"markup is shown as raw text: {rendered.get('text')!r}"
    assert any(lst["items"] == ["QCTEST-130712 yearly reports"] for lst in rendered["lists"]), (
        f"the bullet does not render as a list item: {rendered['lists']}"
    )
    link = [a for a in rendered["links"] if a["text"] == "Contact Qatar Chamber"]
    assert link and link[0]["href"] == CONTACT_URL and link[0]["clickable"], f"link not intact: {rendered['links']}"


# ===========================================================================
# Valid values — 143648 / 143652 / 143667 / 143711 / 143715
# ===========================================================================
@AUTH_FREE_PAGE
@_case("143648", "A valid Eyebrow Label (EN/AR) is saved and displayed on the hero", "Hero — Eyebrow Label")
def test_143648_valid_eyebrow_saved_and_displayed(page, singleton, anon_pages):
    # Azure TC 143648 | PBI 130712 | account: Site Content Editor
    _valid_value_case(page, anon_pages, "143648", EYEBROW, "Insights & Media", "الإعلام والمنشورات", singleton=singleton)


@AUTH_FREE_PAGE
@_case("143652", "A valid Page Title (EN/AR) is saved and displayed", "Hero — Page Title")
def test_143652_valid_page_title_saved_and_displayed(page, singleton, anon_pages):
    # Azure TC 143652 | PBI 130712 | account: Site Content Editor
    _valid_value_case(page, anon_pages, "143652", PAGE_TITLE, "Annual Reports", "التقارير السنوية", singleton=singleton)


@AUTH_FREE_PAGE
@_case("143667", "A valid Section Badge (Report archive) is saved and displayed", "Report Archive — Section Badge")
def test_143667_valid_section_badge_saved_and_displayed(page, singleton, anon_pages):
    # Azure TC 143667 | PBI 130712 | account: Site Content Editor. "AR equivalent" = the page's own AR badge.
    _valid_value_case(page, anon_pages, "143667", SECTION_BADGE, "Report archive", "أرشيف التقارير", singleton=singleton)


@AUTH_FREE_PAGE
@_case("143711", "A valid Section Title (Institutional reporting by year) is saved and displayed",
       "Report Archive — Section Title")
def test_143711_valid_section_title_saved_and_displayed(page, singleton, anon_pages):
    # Azure TC 143711 | PBI 130712 | account: Site Content Editor
    _valid_value_case(page, anon_pages, "143711", SECTION_TITLE, "Institutional reporting by year",
                      "التقارير المؤسسية حسب السنة", singleton=singleton)


SECTION_DESCRIPTION_EN = ("<p>QCTEST-130712 Browse the Chamber's published annual reports by year and open or "
                          "download each PDF.</p>")
SECTION_DESCRIPTION_AR = "<p>QCTEST-130712 تصفح التقارير السنوية المنشورة للغرفة حسب السنة واعرض أو حمّل كل ملف PDF.</p>"


@AUTH_FREE_PAGE
@_case("143715", "A valid Section Description is saved and rendered correctly", "Report Archive — Section Description")
def test_143715_valid_section_description_saved_and_displayed(page, singleton, anon_pages):
    # Azure TC 143715 | PBI 130712 | account: Site Content Editor (<=300 chars each)
    assert len(SECTION_DESCRIPTION_EN) <= 300 and len(SECTION_DESCRIPTION_AR) <= 300
    _valid_value_case(page, anon_pages, "143715", SECTION_DESCRIPTION, SECTION_DESCRIPTION_EN, SECTION_DESCRIPTION_AR, singleton=singleton)


# ===========================================================================
# Empty / whitespace — required-field validation
# ===========================================================================
@AUTH_FREE_PAGE
@_case("143649", "An empty Eyebrow Label (EN) is rejected on publish", "Hero — Eyebrow Label",
       severity=allure.severity_level.CRITICAL)
def test_143649_empty_eyebrow_rejected(page, singleton):
    _blank_case(page, singleton, "143649", EYEBROW, "")


@AUTH_FREE_PAGE
@_case("143651", "A whitespace-only Eyebrow Label is rejected as empty", "Hero — Eyebrow Label")
def test_143651_whitespace_eyebrow_rejected_as_empty(page, singleton):
    # Azure TC 143651 — "the same required-field validation as a truly empty field":
    # the empty attempt runs first as the reference, then the whitespace attempt.
    admin = _editor(page)
    empty = _blank_case(page, singleton, "143651-empty-reference", EYEBROW, "", admin)
    blank = _blank_case(page, singleton, "143651", EYEBROW, "     ", admin)
    allure.attach(f"empty: {AnnualReportsPageAdminPage.refusal_text(empty)!r}\n"
                  f"whitespace: {AnnualReportsPageAdminPage.refusal_text(blank)!r}", name="empty vs whitespace")


@AUTH_FREE_PAGE
@_case("143653", "An empty Page Title (EN) is rejected on publish", "Hero — Page Title",
       severity=allure.severity_level.CRITICAL)
def test_143653_empty_page_title_rejected(page, singleton):
    _blank_case(page, singleton, "143653", PAGE_TITLE, "")


@AUTH_FREE_PAGE
@_case("143655", "A whitespace-only Page Title is rejected as empty", "Hero — Page Title")
def test_143655_whitespace_page_title_rejected(page, singleton):
    _blank_case(page, singleton, "143655", PAGE_TITLE, "   ")


@AUTH_FREE_PAGE
@_case("143657", "An empty Hero Description (EN) is rejected on publish", "Hero — Hero Description",
       severity=allure.severity_level.CRITICAL)
def test_143657_empty_hero_description_rejected(page, singleton):
    _blank_case(page, singleton, "143657", HERO_DESCRIPTION, "")


@AUTH_FREE_PAGE
@_case("143659", "A whitespace-only Hero Description is rejected as empty", "Hero — Hero Description")
def test_143659_whitespace_hero_description_rejected(page, singleton):
    _blank_case(page, singleton, "143659", HERO_DESCRIPTION, "  \n  \n  ")


@AUTH_FREE_PAGE
@_case("143668", "An empty Section Badge (EN) is rejected on publish", "Report Archive — Section Badge",
       severity=allure.severity_level.CRITICAL)
def test_143668_empty_section_badge_rejected(page, singleton):
    _blank_case(page, singleton, "143668", SECTION_BADGE, "")


@AUTH_FREE_PAGE
@_case("143670", "A whitespace-only Section Badge is rejected as empty", "Report Archive — Section Badge")
def test_143670_whitespace_section_badge_rejected(page, singleton):
    _blank_case(page, singleton, "143670", SECTION_BADGE, "    ")


@AUTH_FREE_PAGE
@_case("143712", "An empty Section Title (EN) is rejected on publish", "Report Archive — Section Title",
       severity=allure.severity_level.CRITICAL)
def test_143712_empty_section_title_rejected(page, singleton):
    _blank_case(page, singleton, "143712", SECTION_TITLE, "")


@AUTH_FREE_PAGE
@_case("143714", "A whitespace-only Section Title is rejected as empty", "Report Archive — Section Title")
def test_143714_whitespace_section_title_rejected(page, singleton):
    _blank_case(page, singleton, "143714", SECTION_TITLE, "   ")


@AUTH_FREE_PAGE
@_case("143716", "An empty Section Description (EN) is rejected on publish", "Report Archive — Section Description",
       severity=allure.severity_level.CRITICAL)
def test_143716_empty_section_description_rejected(page, singleton):
    _blank_case(page, singleton, "143716", SECTION_DESCRIPTION, "")


@AUTH_FREE_PAGE
@_case("143718", "A whitespace-only Section Description is rejected as empty", "Report Archive — Section Description")
def test_143718_whitespace_section_description_rejected(page, singleton):
    _blank_case(page, singleton, "143718", SECTION_DESCRIPTION, " \n \n ")


# ===========================================================================
# Arabic content required — 143827 / 143828
# ===========================================================================
@AUTH_FREE_PAGE
@_case("143827", 'Publishing the hero content is blocked when its Arabic fields are empty ("Arabic content is required.")',
       "Bilingual", category=pytest.mark.functional_high, severity=allure.severity_level.BLOCKER,
       extra=(pytest.mark.bilingual,))
def test_143827_hero_arabic_fields_empty_blocks_publish(page, singleton):
    _arabic_empty_case(page, singleton, "143827", HERO_FIELDS)


@AUTH_FREE_PAGE
@_case("143828", 'Publishing the report-archive content is blocked when its Arabic fields are empty '
                 '("Arabic content is required.")',
       "Bilingual", category=pytest.mark.functional_high, severity=allure.severity_level.BLOCKER,
       extra=(pytest.mark.bilingual,))
def test_143828_archive_arabic_fields_empty_blocks_publish(page, singleton):
    _arabic_empty_case(page, singleton, "143828", ARCHIVE_FIELDS)


# ===========================================================================
# Hero Banner — 143660 / 143661 / 143662 / 143663
# ===========================================================================
@AUTH_FREE_PAGE
@_case("143660", "A valid Hero Banner (JPG, 1.5MB) is uploaded and displayed", "Hero — Hero Banner")
def test_143660_valid_banner_uploaded_and_displayed(page, singleton, anon_pages):
    # Azure TC 143660 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    upload = unique_copy(BANNER_JPG_1_5MB)
    stem = Path(upload).stem
    with allure.step("Upload a 1.5MB JPG banner"):
        admin.open_singleton()
        picker = admin.try_banner_upload(upload)
        pending = admin.banner_pending_name()
    with allure.step("Publish"):
        outcome = _publish(admin, "143660")
    with allure.step("Re-open the record and read the stored banner"):
        admin.open_singleton()
        stored = admin.banner_file_name()
    allure.attach(f"picker={picker}\npending={pending!r}\nstored={stored!r}", name="upload evidence")
    assert picker["accepted"] and picker["added"] and not picker["rejection"], f"the JPG upload did not succeed: {picker}"
    assert outcome["reloaded"], f"Publish did not go through: {outcome}"
    assert AnnualReportsPageAdminPage.success_message(outcome), f"no publish success message: {outcome['banners']}"
    assert stored.startswith(stem), f"the banner was not stored: {stored!r} (uploaded {stem})"
    _require_active_status(admin)
    with allure.step("Load the live page and locate the banner"):
        ok, view = _public(anon_pages, lambda v: stem in v.hero_banner_render().get("var_url", ""), "en", "143660")
        render = view.hero_banner_render()
        image_status = view.resource_status(render.get("var_url", ""))
    allure.attach(f"{render}\nimage HTTP status: {image_status}", name="hero banner rendering")
    assert ok, f"the live hero does not reference the new banner at all: {render}"
    assert image_status == 200, f"the banner URL the hero references does not load (HTTP {image_status})"
    assert render["backgrounds"] or any(i["loaded"] for i in render["imgs"]), (
        "the new banner is passed to the hero (CSS variable --qc-ar-hero-img-url) and loads, but it is not "
        "displayed: no element or pseudo-element of the hero uses it as a background image and no <img> shows "
        f"it (hero background: {render.get('hero_bg')!r})"
    )


@AUTH_FREE_PAGE
@_case("143661", "Publishing without a Hero Banner is blocked", "Hero — Hero Banner",
       severity=allure.severity_level.CRITICAL)
def test_143661_publish_without_banner_blocked(page, singleton):
    # Azure TC 143661 | PBI 130712 | account: Site Content Editor
    admin = _editor(page)
    with allure.step("Leave Hero Banner empty (Remove file)"):
        admin.open_singleton()
        admin.remove_banner()
    with allure.step("Attempt Publish"):
        outcome = _publish(admin, "143661")
    with allure.step("Re-open the record and read the stored banner"):
        admin.open_singleton()
        stored = admin.banner_file_name()
        stored_sha = hashlib.sha256(admin.banner_bytes()).hexdigest() if stored else ""
    refusal = AnnualReportsPageAdminPage.refusal_text(outcome)
    allure.attach(f"stored after attempt: {stored!r}; refusal: {refusal!r}", name="evidence")
    assert not outcome["reloaded"], (
        f"Publish was NOT blocked with no Hero Banner: the page was saved and published without a banner "
        f"(stored banner now {stored or 'none'!r}; messages {outcome['banners']})"
    )
    _assert_refusal_on(outcome, {"ObjectField_heroBanner"}, "the missing Hero Banner")
    assert re.search(r"required|fill out|select a file", refusal, re.I), (
        f"Publish was blocked but no required-field message was shown for Hero Banner: {outcome}"
    )
    assert stored_sha == singleton.baseline["banner_sha256"], "the stored banner changed although Publish was refused"


@AUTH_FREE_PAGE
@_case("143662", "An unsupported Hero Banner format (GIF) is rejected", "Hero — Hero Banner")
def test_143662_unsupported_banner_format_rejected(page, singleton):
    # Azure TC 143662 | PBI 130712 | account: Site Content Editor. Nothing is saved.
    admin = _editor(page)
    upload = unique_copy(BANNER_GIF)
    with allure.step("Attempt to upload banner.gif"):
        admin.open_singleton()
        picker = admin.try_banner_upload(upload)
        pending = admin.banner_pending_name()
        try:
            attach_screenshot(admin.page.screenshot(), "143662-after-upload", settings.project_name,
                              settings.reports_dir)
        except Exception:  # noqa: BLE001
            pass
    with allure.step("Leave without saving; re-open and read the stored banner"):
        admin.open_singleton()
        stored = admin.banner_file_name()
    allure.attach(f"picker={picker}\npending={pending!r}\nstored={stored!r}", name="upload evidence")
    assert not picker["added"] and Path(upload).stem not in pending, (
        f"the GIF was accepted and attached to the field (pending {pending!r}): {picker}"
    )
    assert re.search(r"extension|not supported|file type|format|not allowed", picker["rejection"], re.I), (
        f"the GIF was not attached, but no unsupported-file-type message was shown: {picker}"
    )
    assert stored == singleton.baseline["banner_file"], f"the stored banner changed: {stored!r}"


@AUTH_FREE_PAGE
@_case("143663", "An oversized Hero Banner (>2MB) is rejected", "Hero — Hero Banner")
def test_143663_oversized_banner_rejected(page, singleton):
    # Azure TC 143663 | PBI 130712 | account: Site Content Editor. Nothing is saved.
    admin = _editor(page)
    upload = unique_copy(BANNER_PNG_2_5MB)
    with allure.step("Attempt to upload a 2.5MB PNG"):
        admin.open_singleton()
        help_text = admin.banner_help_text()
        picker = admin.try_banner_upload(upload)
        pending = admin.banner_pending_name()
        try:
            attach_screenshot(admin.page.screenshot(), "143663-after-upload", settings.project_name,
                              settings.reports_dir)
        except Exception:  # noqa: BLE001
            pass
    with allure.step("Leave without saving; re-open and read the stored banner"):
        admin.open_singleton()
        stored = admin.banner_file_name()
    allure.attach(f"help={help_text!r}\npicker={picker}\npending={pending!r}\nstored={stored!r}",
                  name="upload evidence")
    assert stored == singleton.baseline["banner_file"], f"the stored banner changed: {stored!r}"
    assert not picker["added"] and Path(upload).stem not in pending, (
        f"a 2.5MB PNG was ACCEPTED and attached to the Hero Banner field (pending {pending!r}); the field's own "
        f"help line reads {help_text!r} — expected it rejected as larger than 2MB"
    )
    assert re.search(r"size|no larger than|exceed|too large|maximum", picker["rejection"], re.I), (
        f"the 2.5MB PNG was not attached, but no oversized-file message was shown: {picker}"
    )


# ===========================================================================
# Page status — 143664 / 143665 (143666 is covered on a report record in test_annual_reports_control_panel.py)
# ===========================================================================
@AUTH_FREE_PAGE
@_case("143664", "Setting page Status=Published takes effect on save", "Page status",
       severity=allure.severity_level.CRITICAL)
def test_143664_page_status_published_takes_effect(page, singleton, anon_pages):
    # Azure TC 143664 | PBI 130712 | account: Site Content Editor.
    # Substitution (module docstring): no Status picklist exists; Status=Published is
    # Active Status ticked + Publish.
    admin = _editor(page)
    with allure.step("Select Status=Published (Active Status ticked)"):
        admin.open_singleton()
        controls = admin.status_like_controls()
        admin.set_active_status(True)
        ticked = admin.active_status_checked()
        submit_label = admin.submit_button_label()
    allure.attach(repr(controls), name="status-like controls on the form")
    with allure.step("Save (Publish)"):
        outcome = _publish(admin, "143664")
        status = admin.singleton_row_status()
    _require_active_status(admin)
    with allure.step("Load the live page in a fresh logged-out context"):
        ok, view = _public(anon_pages, lambda v: v.http_status() == 200 and bool(v.title()), "en", "143664")
    assert ticked and submit_label == "Publish", f"Active Status ticked={ticked}, submit button {submit_label!r}"
    assert outcome["reloaded"], f"the save did not go through: {outcome}"
    assert AnnualReportsPageAdminPage.success_message(outcome), f"no publish success message: {outcome['banners']}"
    assert status == STATUS_PUBLISHED, f"the page record's status is {status!r}, not Published"
    assert ok, f"the live page is not accessible: HTTP {view.http_status()}, title {view.title()!r}"


@AUTH_FREE_PAGE
@_case("143665", "Leaving page Status unselected blocks save", "Page status")
def test_143665_page_status_unselected_blocks_save(page):
    # Azure TC 143665 | PBI 130712 — BLOCKED (see NEW_RECORD_BLOCKED). Read-only:
    # records what the create form offers as a Status control, then skips.
    admin = _editor(page)
    admin.open_new_entry_form_readonly()
    controls = admin.status_like_controls()
    allure.attach(f"labels: {admin.form_labels()}\nstatus-like controls: {controls}",
                  name="create form — status controls (not submitted)")
    pytest.skip(f"{NEW_RECORD_BLOCKED} Read-only evidence: the create form's only status-like controls are "
                f"{[(c['label'] or c['name'], c['type'], 'required' if c['required'] else 'not required') for c in controls]}.")


# ===========================================================================
# Field character-limit cases — skipped by QA decision (run 2026-10-04)
# ===========================================================================
@FIELD_LIMIT_SKIP
@_case("143650", "An Eyebrow Label exceeding 60 characters is rejected at the boundary", "Hero — Eyebrow Label")
def test_143650_eyebrow_over_60_rejected(page):
    pass


@FIELD_LIMIT_SKIP
@_case("143654", "A Page Title exceeding 120 characters is rejected at the boundary", "Hero — Page Title")
def test_143654_page_title_over_120_rejected(page):
    pass


@FIELD_LIMIT_SKIP
@_case("143658", "A Hero Description exceeding 200 characters is rejected at the boundary", "Hero — Hero Description")
def test_143658_hero_description_over_200_rejected(page):
    pass


@FIELD_LIMIT_SKIP
@_case("143669", "A Section Badge exceeding 100 characters is rejected at the boundary", "Report Archive — Section Badge")
def test_143669_section_badge_over_100_rejected(page):
    pass


@FIELD_LIMIT_SKIP
@_case("143713", "A Section Title exceeding 150 characters is rejected at the boundary", "Report Archive — Section Title")
def test_143713_section_title_over_150_rejected(page):
    pass


@FIELD_LIMIT_SKIP
@_case("143717", "A Section Description exceeding 300 characters is rejected at the boundary",
       "Report Archive — Section Description")
def test_143717_section_description_over_300_rejected(page):
    pass
