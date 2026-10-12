"""
cms/tests/business_opportunities/test_bizopp_sections_d_control_panel.py —
Opportunity Sections and listing Sort Order, PBI 130697 (Agent D, Phase 3,
Azure plan 137724 / suite 140361): cases 143376, 143377, 143390.

Surfaces (live recon 2026-10-07, Site Content Editor on qcdev):
  - `manage-opportunity-section`: Section Title (EN + AR), Section Number,
    Display Order, Active Status, relation "Opportunity Sections" -> parent
    Business Opportunity (picker lists parents by entry code).
  - `manage-business-opportunity`: the parent. The listing's "Sort Order" is the
    parent's "Display Order" field.
  - Public detail: sticky nav `a.qc-bod-index-row` (num + label, href
    `#qc-bod-overview|investment|gallery`); rows follow Display Order and map by
    position onto the three fixed content blocks.

Everything is a disposable `QCTEST-130697-D-<tc>-<stamp>` parent (title, 100-grid
Display Order) with QCTEST sections. Identity (title, entry id, code) is captured
right after creation; teardown deletes ONLY the captured parent through the
guarded delete (its sections go with it — deleting a section first makes the
later parent delete fail, see the findings in the run report). The 6 real
opportunities (QC-BIZOPP-130697-01..06) and their sections are never edited.

Substitutions disclosed (case wording -> what runs):
  - Display Order / Sort Order 1/2/3 -> 100/200/300 (100-grid rule; bug 147939 family).
  - 143390 "Sort Order" = the Business Opportunity's Display Order; the three
    records get conflicting Publish Dates (oldest = lowest order) so a date-driven
    list cannot pass by coincidence.
  - "Administrator" is not needed by these cases; every CMS step runs as the Site
    Content Editor (publishes directly).
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from time import monotonic

import allure
import pytest

from cms.pages.business_opportunities.opportunity_sections_d_page import (
    D_EDITOR_USER_ID,
    D_QCTEST_PREFIX,
    D_ROLE_EDITOR,
    K_ARCHIVE_DATE,
    K_PUBLISH_DATE,
    K_SORT,
    K_TITLE,
    S_TITLE,
    BizOppDetailPublicD,
    BizOppListingPublicD,
    BizOppParentDPage,
    BizOppSectionDPage,
    DEntry,
    ddmmyyyy,
)
from config.settings import PROJECT_ROOT
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
D_GROUP = pytest.mark.xdist_group("bizopp_cms_d")
STAMP = datetime.now().strftime("%m%d%H%M%S")
EVIDENCE_DIR = PROJECT_ROOT / "reports" / "evidence" / "130697_d"
EPIC = "Business Gateway"
FEATURE = "Business Opportunities — Control Panel (sections, sort order)"
MSG_PUBLISHED = "Saved and published."
PUBLIC_REFLECT_TIMEOUT = 60.0
DESKTOP = (1920, 1080)
MOBILE = (390, 844)
NAV_OBSERVED: dict[str, dict] = {}   # 143376: what the sticky nav actually rendered (rows + hrefs)


def _title(tc: str, suffix: str = "") -> str:
    return f"{D_QCTEST_PREFIX}{tc}-{STAMP}" + (f"-{suffix}" if suffix else "")


def _pad(prefix: str, length: int) -> str:
    """Text of exactly `length` characters: `prefix` then words (so wrapping is realistic)."""
    words = " lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor"
    text = prefix
    while len(text) < length:
        text += words
    return text[:length].rstrip() + "x" * (length - len(text[:length].rstrip()))


def _arabic_pad(length: int) -> str:
    words = "قسم تجريبي لاختبار الحد الأقصى لطول العنوان "
    text = ""
    while len(text) < length:
        text += words
    text = text[:length].rstrip()
    return text + "ا" * (length - len(text))


# ===========================================================================
# Fixtures
# ===========================================================================
class Registry:
    """What this test created. Only captured parents are deleted (sections cascade)."""

    def __init__(self):
        self.parents: list[DEntry] = []
        self.sections: list[DEntry] = []

    def track_parent(self, entry: DEntry) -> DEntry:
        if not entry.in_namespace():
            raise ValueError(f"{entry} is not a {D_QCTEST_PREFIX} record")
        self.parents.append(entry)
        return entry

    def track_section(self, entry: DEntry) -> DEntry:
        if not entry.in_namespace():
            raise ValueError(f"{entry} is not a {D_QCTEST_PREFIX} record")
        self.sections.append(entry)
        return entry


@pytest.fixture
def disposable(browser):
    reg = Registry()
    yield reg
    if not reg.parents and not reg.sections:
        return
    ctx = new_context(browser, use_auth_state=False)
    outcome, failures = [], []
    try:
        pg = ctx.new_page()
        parent_admin = BizOppParentDPage(pg)
        if parent_admin.login_as_role(D_ROLE_EDITOR) != "ok":
            raise AssertionError("teardown could not sign in as the Site Content Editor")
        section_admin = BizOppSectionDPage(pg)
        for entry in reversed(reg.parents):
            label = f"parent {entry.title} (id {entry.entry_id}, code {entry.code})"
            try:
                parent_admin.open_list_all()
                if not parent_admin.row_present(entry):
                    outcome.append(f"already gone: {label}")
                    continue
                parent_admin.adopt(entry)
                if parent_admin.delete_disposable_entry(entry):
                    outcome.append(f"removed {label}")
                else:
                    failures.append(f"NOT removed {label}: guarded delete refused/failed")
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{label}: {exc!r}")
        section_admin.open_list_all()
        for entry in reg.sections:
            if section_admin.row_present(entry):
                section_admin.adopt(entry)
                if section_admin.delete_disposable_entry(entry):
                    outcome.append(f"removed orphan section {entry.title} (id {entry.entry_id})")
                else:
                    failures.append(f"section {entry.title} (id {entry.entry_id}) is still on qcdev")
            else:
                outcome.append(f"section {entry.title} gone with its parent")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"teardown error: {exc!r}")
    finally:
        ctx.close()
    allure.attach("\n".join(outcome + failures) or "nothing to remove", name="QCTEST teardown")
    if failures:
        raise AssertionError("TEARDOWN LEFT QCTEST DATA BEHIND:\n" + "\n".join(failures))


@pytest.fixture
def anon_pages(browser):
    """Fresh logged-out contexts for every public read (standards.md); (w, h) viewport."""
    contexts = []

    def _make(viewport=DESKTOP, locale: str | None = None):
        ctx = new_context(browser, viewport=viewport, use_auth_state=False, locale=locale)
        contexts.append(ctx)
        return ctx.new_page()

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


# ===========================================================================
# Helpers
# ===========================================================================
def _login(page) -> tuple[BizOppParentDPage, BizOppSectionDPage]:
    admin = BizOppParentDPage(page)
    outcome = admin.login_as_role(D_ROLE_EDITOR)
    if outcome == "auth_failed":
        pytest.skip(f"PRECONDITION: Liferay refused the .env credentials for '{D_ROLE_EDITOR}'")
    if outcome != "ok":
        pytest.fail("login as the Site Content Editor neither succeeded nor showed Liferay's refusal banner")
    user_id, _ = admin.signed_in_user()
    if user_id != D_EDITOR_USER_ID:
        pytest.skip(f"PRECONDITION: Editor credentials sign in as userId {user_id!r}, not {D_EDITOR_USER_ID}")
    return admin, BizOppSectionDPage(page)


def _wait_arabic_saved(admin) -> str:
    seen = {"text": ""}

    def _done() -> bool:
        seen["text"] = admin.rendered_body_text()
        return "Arabic content saved for this record." in seen["text"] or "Arabic content was not" in seen["text"]

    try:
        wait_until(_done, timeout=25.0, poll=0.5)
    except WaitTimeoutError:
        return ""
    return "saved" if "Arabic content saved for this record." in seen["text"] else "NOT saved"


def _create_parent(admin: BizOppParentDPage, disposable: Registry, title: str, sort_order: str = "100",
                   **overrides) -> DEntry:
    """Publishes one QCTEST parent (lifecycle Published, Active ticked), captures its identity,
    registers it for teardown, THEN re-opens it and verifies the STORED values."""
    ids_before = admin.snapshot_ids()
    went_through, diagnostics, banners = False, {}, []
    data = BizOppParentDPage.parent_data(title, sort_order, **overrides)
    try:
        admin.open_create_form_en()
        admin.fill_parent(data)
        admin.click_publish()
        went_through = admin.save_went_through()
        diagnostics = admin.refusal_evidence()
        if went_through:
            banners = admin.success_messages(MSG_PUBLISHED, timeout=15.0)
            _wait_arabic_saved(admin)
        admin.evidence(f"{title} after publish")
    finally:
        try:
            entry = admin.identify_created(title, ids_before)
        except Exception as exc:  # noqa: BLE001
            allure.attach(f"{exc!r}\ncandidate rows (id:code:title): {getattr(admin,'last_candidates', [])}",
                          name=f"IDENTIFICATION FAILED for {title!r}")
            raise
        if entry:
            disposable.track_parent(entry)
    assert went_through, f"creating {title!r} did not go through: {diagnostics}"
    assert entry is not None, f"{title!r} went through but is not identifiable as exactly one NEW record"
    assert any(MSG_PUBLISHED in b for b in banners), f"no {MSG_PUBLISHED!r} after publishing {title!r}: {banners}"
    # Stored-value verification (brief rule 4): re-open and read back.
    admin.open_entry_en(entry.code)
    stored = {"active": admin.active_status_stored(), "order": admin.text_value(K_SORT),
              "publish": admin.date_stored(K_PUBLISH_DATE), "archive": admin.date_stored(K_ARCHIVE_DATE),
              "lifecycle": admin.picklist_value("lifecycleStatus")}
    allure.attach(repr(stored), name=f"stored values of {title}")
    assert stored["active"] == "true", f"{title!r} stores Active Status {stored['active']!r}"
    assert stored["order"] == sort_order, f"{title!r} stores Display Order {stored['order']!r}, not {sort_order!r}"
    assert stored["lifecycle"] == "Published", f"{title!r} stores Lifecycle Status {stored['lifecycle']!r}"
    return entry


def _create_section(sections: BizOppSectionDPage, disposable: Registry, parent: DEntry, title: str, number: str,
                    order: str, active: bool = True, title_ar: str | None = None) -> tuple[DEntry, dict]:
    ids_before = sections.snapshot_ids()
    went_through, diagnostics, banners = False, {}, []
    try:
        sections.open_create_form_en()
        sections.fill_section(title, number, order, active, title_ar=title_ar, parent=parent)
        sections.click_publish()
        went_through = sections.save_went_through()
        diagnostics = sections.refusal_evidence()
        if went_through:
            banners = sections.success_messages(MSG_PUBLISHED, timeout=15.0)
            _wait_arabic_saved(sections)
        sections.evidence(f"section {title[:40]} after publish")
    finally:
        try:
            entry = sections.identify_created(title, ids_before)
        except Exception as exc:  # noqa: BLE001
            allure.attach(f"{exc!r}\ncandidate rows (id:code:title): {getattr(sections,'last_candidates', [])}",
                          name=f"IDENTIFICATION FAILED for section {title[:40]!r}")
            raise
        if entry:
            disposable.track_section(entry)
    assert went_through, f"creating section {title[:60]!r} did not go through: {diagnostics}"
    assert entry is not None, f"section {title[:60]!r} went through but is not identifiable as exactly one NEW record"
    assert any(MSG_PUBLISHED in b for b in banners), f"no {MSG_PUBLISHED!r} after publishing section: {banners}"
    sections.open_entry_en(entry.code)
    stored = sections.read_section()
    allure.attach(repr(stored), name=f"stored values of section {title[:40]}")
    assert stored["parent"] == parent.entry_id, f"section stored parent {stored['parent']!r}, not {parent.entry_id!r}"
    return entry, stored


def _public_detail(anon_pages, code: str, locale: str, viewport=DESKTOP, expect_rows: int | None = None,
                   timeout: float = PUBLIC_REFLECT_TIMEOUT) -> tuple[BizOppDetailPublicD, list[dict]]:
    """Fresh logged-out context; polls (re-loading) until the nav shows `expect_rows` rows."""
    started = monotonic()
    holder = {}

    def _check() -> bool:
        view = BizOppDetailPublicD(anon_pages(viewport))
        view.open_detail_by_code(code, locale)
        rows = view.wait_index(timeout=12.0) if view.detail_available() else []
        holder["view"], holder["rows"] = view, rows
        return len(rows) == expect_rows if expect_rows is not None else len(rows) > 0

    try:
        wait_until(_check, timeout=timeout, poll=2.0)
    except WaitTimeoutError:
        pass
    allure.attach(f"{monotonic() - started:.1f}s", name=f"public detail latency ({locale} {viewport[0]}px)")
    return holder["view"], holder["rows"]


def _norm(text: str) -> str:
    return " ".join(text.split()).casefold()


def _evidence(view, name: str) -> str:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = str(EVIDENCE_DIR / (re.sub(r"[^\w.-]+", "_", name)[:110] + ".png"))
    try:
        png = view.page.screenshot(path=path, full_page=False)
        allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
    except Exception:  # noqa: BLE001
        pass
    return path


# ===========================================================================
# 143376 — Section Index content authors and renders in sticky-nav order
# ===========================================================================
@pytest.mark.control_panel
@pytest.mark.invest
@pytest.mark.functional_low
@pytest.mark.pbi_130697
@pytest.mark.tc_143376
@D_GROUP
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Section Index authors and renders in Display Order")
@allure.title("Section Title / Number / Display Order author and render in sticky-nav order (143376)")
def test_section_index_authors_and_renders_in_order(page, anon_pages, disposable):
    # Azure TC 143376 | Site Content Editor | Display Order 1/2/3 -> 100/200/300 (100-grid).
    admin, sections = _login(page)
    parent_title = _title("143376", "PARENT")
    with allure.step("Create + publish the QCTEST parent Business Opportunity (Active)"):
        parent = _create_parent(admin, disposable, parent_title)
    specs = [  # created OUT of order on purpose: the nav must follow Display Order, not creation order
        {"title": _title("143376", "Third"), "title_ar": f"القسم الثالث {STAMP}", "number": "03", "order": "300"},
        {"title": _title("143376", "First"), "title_ar": f"القسم الأول {STAMP}", "number": "01", "order": "100"},
        {"title": _title("143376", "Second"), "title_ar": f"القسم الثاني {STAMP}", "number": "02", "order": "200"},
    ]
    stored_all = {}
    with allure.step("Step 1-2: author 3 Active sections (Title EN/AR, Number 01/02/03, Display Order 100/200/300)"):
        for spec in specs:
            _, stored = _create_section(sections, disposable, parent, spec["title"], spec["number"], spec["order"],
                                        True, title_ar=spec["title_ar"])
            stored_all[spec["number"]] = stored
            assert (stored["title"], stored["title_ar"], stored["number"], stored["order"], stored["active"]) == \
                   (spec["title"], spec["title_ar"], spec["number"], spec["order"], "true"), \
                   f"section {spec['number']} was not stored as entered: {stored}"
    with allure.step("Step 3: the record is already published (Lifecycle Published, Active) — public read"):
        pass
    expected = sorted(specs, key=lambda s: int(s["order"]))
    problems: list[str] = []

    # The case as written: three Active sections on the record, nothing else added (no Project Gallery
    # item). The nav rows are bound BY POSITION to the three fixed blocks overview / investment / gallery,
    # so the actual rows and hrefs are recorded.
    for locale in ("en", "ar"):
        with allure.step(f"Step 4: public detail ({locale}) sticky nav order, titles, scroll-to-block"):
            view, rows = _public_detail(anon_pages, parent.code, locale)
            hrefs = [r["href"] for r in rows]
            allure.attach(json.dumps(rows, ensure_ascii=False, indent=1), name=f"OBSERVED nav rows ({locale})")
            allure.attach(f"{locale}: {len(rows)} nav row(s), hrefs {hrefs}", name=f"OBSERVED nav hrefs ({locale})")
            NAV_OBSERVED[locale] = {"rows": rows, "hrefs": hrefs}
            # User decision 2026-10-07: a nav block whose content block has no data (here the Gallery row, no
            # gallery content) is hidden BY DESIGN - correct behaviour, not a finding. Rows that exist must be in
            # Display Order with the right titles; nothing is added to the record to force a 3rd row.
            if not rows:
                problems.append(f"{locale}: the sticky nav shows no rows")
            _evidence(view, f"143376 {locale} nav rows {len(rows)}")
            key = "title" if locale == "en" else "title_ar"
            shown = rows[:3]
            if [r["num"] for r in shown] != ["01", "02", "03"][:len(shown)]:
                problems.append(f"{locale}: numbers {[r['num'] for r in shown]} are not 01/02/03 in order")
            if [_norm(r["label"]) for r in shown] != [_norm(s[key]) for s in expected][:len(shown)]:
                problems.append(f"{locale}: labels {[r['label'] for r in shown]} != "
                                f"{[s[key] for s in expected][:len(shown)]}")
            for idx, row in enumerate(shown):
                hit = view.click_row_and_target_top(idx)
                if not hit["in_view"]:
                    problems.append(f"{locale}: clicking {row['label']!r} did not scroll {hit['href']} into view ({hit})")
            _evidence(view, f"143376 {locale} nav after clicks")
    assert not problems, "PRODUCT: " + "; ".join(problems)


# ===========================================================================
# 143377 — over-length Section Title rejected; inactive section hidden
# ===========================================================================
MOBILE_OBS: dict[str, dict] = {}   # 143377: what the 390px page actually shows for the 100-char title


def _mobile_and_desktop_checks(anon_pages, code: str, locale: str, label_en_or_ar: str, problems: list[str],
                               name: str, expect_rows: int) -> None:
    """VISIBILITY (rendered, not clipped), not DOM text. Desktop: the title must be visible in a visible nav row.
    Mobile: if the section nav is hidden, that is recorded as an observation together with whether the long
    title is visible anywhere else on the page; if the nav is visible the title must be visible in it."""
    for viewport in (DESKTOP, MOBILE):
        view, rows = _public_detail(anon_pages, code, locale, viewport=viewport, expect_rows=expect_rows)
        rep = view.layout_report() if rows else {}
        vis = view.text_visibility(label_en_or_ar[:40]) if rows else {}
        obs = {"nav_visible": rep.get("navVisible"), "rows_in_dom": len(rows),
               "rows_rendered": [r["visible"] for r in rows], "title_visibility": vis}
        MOBILE_OBS[f"{locale} {viewport[0]}px"] = obs
        allure.attach(json.dumps({"layout": rep, "observation": obs}, ensure_ascii=False, indent=1, default=str),
                      name=f"layout + visibility {locale} {viewport[0]}px")
        _evidence(view, f"{name} {locale} {viewport[0]}px")
        if not rows:
            problems.append(f"{locale} {viewport[0]}px: no section nav rows rendered")
            continue
        if rep.get("pageOverflowX"):
            problems.append(f"{locale} {viewport[0]}px: page scrolls horizontally "
                            f"(scrollWidth {rep['pageScrollWidth']} > viewport {rep['viewport']})")
        if not rep.get("navVisible"):
            msg = (f"{locale} {viewport[0]}px: the section nav is HIDDEN (display none / zero size); the 100-char "
                   f"title is visible elsewhere on the page: {bool(vis.get('visible_anywhere'))} {vis}")
            allure.attach(msg, name="OBSERVATION nav hidden")
            if viewport == DESKTOP:
                problems.append(f"{locale} {viewport[0]}px: the section nav is not visible on desktop")
            continue
        for r in rep["rows"]:
            if r["rowRight"] > rep["viewport"] + 1 or r["rowLeft"] < -1:
                problems.append(f"{locale} {viewport[0]}px: nav row {r['text'][:30]!r} leaves the viewport {r}")
            if r["labelClipped"]:
                problems.append(f"{locale} {viewport[0]}px: nav label is clipped/truncated {r['text'][:30]!r}")
        if not vis.get("visible_in_nav"):
            problems.append(f"{locale} {viewport[0]}px: the 100-character title is not VISIBLE in the section nav "
                            f"(visibility check: {vis})")


@pytest.mark.control_panel
@pytest.mark.invest
@pytest.mark.functional_low
@pytest.mark.pbi_130697
@pytest.mark.tc_143377
@D_GROUP
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Section Title max length and inactive sections")
@allure.title("Section Title over max length rejected; inactive section hidden from the public sticky nav (143377)")
def test_section_title_max_length_and_inactive_hidden(page, anon_pages, disposable):
    # Azure TC 143377 | Site Content Editor | char-limit case (brief rule 7): plain field, limit read live.
    admin, sections = _login(page)
    parent = _create_parent(admin, disposable, _title("143377", "PARENT"))
    limit_probe = {}
    ids_before_101 = sections.snapshot_ids()

    with allure.step("Step 1: open the Section editor"):
        sections.open_create_form_en()
        limit_probe["maxlength attribute"] = sections.title_input_maxlength()

    over = _pad(f"{_title('143377', 'A')} ", 101)
    assert len(over) == 101
    with allure.step("Step 2: 101-character Section Title EN on Section A; Section B Active=false"):
        sections.fill_section(over, "01", "100", True, title_ar="قسم أ", parent=parent)
        typed = sections.text_value(S_TITLE)
        limit_probe["typed length kept in the field"] = len(typed)
        assert typed == over, f"the field did not keep all 101 characters (kept {len(typed)})"
    with allure.step("Step 3a: attempt to publish Section A with 101 characters"):
        sections.click_publish()
        went_through = sections.save_went_through()
        evidence = sections.refusal_evidence()
        sections.evidence("143377 101 chars refused")
        limit_probe["publish with 101 chars went through"] = went_through
        limit_probe["field errors"] = evidence.get("field_errors")
        limit_probe["edit-bar"] = evidence.get("editbar")
    allure.attach("\n".join(f"{k}: {v}" for k, v in limit_probe.items()), name="implemented limit (read live)")
    problems: list[str] = []
    if went_through:
        # A record was created that the test has to account for; identify and register it.
        entry = sections.identify_created(over, ids_before_101)   # raises loudly if it cannot be identified
        if entry:
            disposable.track_section(entry)
        problems.append("a 101-character Section Title was ACCEPTED and saved (no 100-character limit enforced)")
    else:
        messages = " | ".join(evidence.get("field_errors") or [])
        expected_msg = "Max 100 characters exceeded"
        if expected_msg.lower() not in messages.lower():
            allure.attach(f"expected: {expected_msg!r}\nactual: {messages!r}", name="WORDING DIFFERENCE (Low)")
    # Wording difference is recorded, not failed (brief rule 6): the behaviour (block at 100) is the case's.
    assert not problems, "PRODUCT: " + "; ".join(problems)

    with allure.step("Step 3b: correct Section A to exactly 100 characters (EN and AR) and publish"):
        en100 = _pad(f"{_title('143377', 'A')} ", 100)
        ar100 = _arabic_pad(100)
        assert len(en100) == 100 and len(ar100) == 100
        entry_a, stored_a = _create_section(sections, disposable, parent, en100, "01", "100", True, title_ar=ar100)
        assert stored_a["title"] == en100 and stored_a["title_ar"] == ar100 and stored_a["active"] == "true"

    title_b = _title("143377", "B-INACTIVE")
    title_c = _title("143377", "C")
    with allure.step("Section B (Active=false) and Section C (Active) — valid titles"):
        _, stored_b = _create_section(sections, disposable, parent, title_b, "02", "200", False, title_ar="قسم ب")
        assert stored_b["active"] == "false", f"Section B's stored Active Status is {stored_b['active']!r}"
        _create_section(sections, disposable, parent, title_c, "03", "300", True, title_ar="قسم ج")

    with allure.step("Public detail EN/AR, desktop 1920 and mobile ~390: Section B hidden; 100-char title renders"):
        for locale, a_label in (("en", en100), ("ar", ar100)):
            view, rows = _public_detail(anon_pages, parent.code, locale, expect_rows=2)
            allure.attach(repr(rows), name=f"nav rows ({locale})")
            labels = [r["label"].strip() for r in rows]
            body = view.body_text()
            if title_b in body or "قسم ب" in labels:
                problems.append(f"{locale}: the inactive Section B is visible on the public page")
            if len(rows) != 2:
                problems.append(f"{locale}: nav shows {len(rows)} rows, expected 2 (A and C): {labels}")
            _evidence(view, f"143377 {locale} nav")
        for locale, a_label in (("en", en100), ("ar", ar100)):
            _mobile_and_desktop_checks(anon_pages, parent.code, locale, a_label, problems, "143377 100-char",
                                       expect_rows=2)
    assert not problems, "PRODUCT: " + "; ".join(problems)


# ===========================================================================
# 143390 — Sort Order controls the display position on the public listing
# ===========================================================================
@pytest.mark.control_panel
@pytest.mark.invest
@pytest.mark.functional_low
@pytest.mark.pbi_130697
@pytest.mark.tc_143390
@D_GROUP
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Listing Sort Order")
@allure.title("Sort Order controls the display position of Published/Active opportunities on the listing (143390)")
def test_sort_order_controls_listing_position(page, anon_pages, disposable):
    # Azure TC 143390 | Site Content Editor | Sort Order 1/2/3 -> 100/200/300 (100-grid).
    admin, _ = _login(page)
    today = date.today()
    plan = [  # (suffix, display order, publish-date offset): conflicting on purpose
        ("A", "100", -30), ("B", "200", -20), ("C", "300", -10),
    ]
    records: dict[str, DEntry] = {}
    with allure.step("Step 1: three Published/Active QCTEST records with Display Order 100/200/300"):
        for suffix, order, offset in plan:
            records[suffix] = _create_parent(
                admin, disposable, _title("143390", suffix), order,
                **{K_PUBLISH_DATE: ddmmyyyy(today + timedelta(days=offset)),
                   K_ARCHIVE_DATE: ddmmyyyy(today + timedelta(days=365))})
        rows = {r["entry_id"]: r["status"] for r in admin.open_list_all().list_rows()}
        allure.attach(repr({k: rows.get(v.entry_id) for k, v in records.items()}), name="row statuses")
        assert all(rows.get(e.entry_id) == "PUBLISHED" for e in records.values()), f"statuses: {rows}"
    titles = {k: v.title for k, v in records.items()}

    with allure.step("Step 2-3: public listing (default sort, Active tab), Load More expanded"):
        started = monotonic()
        holder = {}

        def _all_present() -> bool:
            view = BizOppListingPublicD(anon_pages())
            view.open_expanded("en")
            holder["view"], holder["titles"] = view, view.card_titles()
            return all(t in holder["titles"] for t in titles.values())

        try:
            wait_until(_all_present, timeout=PUBLIC_REFLECT_TIMEOUT, poll=2.0)
        except WaitTimeoutError:
            pass
        view, cards = holder["view"], holder["titles"]
        allure.attach(f"{monotonic() - started:.1f}s", name="public listing latency")
        allure.attach("\n".join(f"{i + 1}. {t}" for i, t in enumerate(cards)), name="listing order (default sort)")
        allure.attach(f"sort dropdown: {view.default_sort()!r}; tab Active: {view.is_tab_active('active')}",
                      name="listing state")
        _evidence(view, "143390 listing default sort")
        missing = [t for t in titles.values() if t not in cards]
        assert not missing, f"PRODUCT: published QCTEST records are missing from the Active listing: {missing}"
        assert view.is_tab_active("active"), "the Active tab is not the default"
        position = {k: cards.index(t) for k, t in titles.items()}
        mine = sorted(position, key=position.get)
        allure.attach(f"positions: {position}; shown order of the three: {mine}", name="relative order")
        assert mine == ["A", "B", "C"], (
            f"PRODUCT: the listing does not order by Sort Order (Display Order 100/200/300). Under the default "
            f"'{view.default_sort()}' sort the three records appear as {mine} (A=100/oldest date, B=200, C=300/"
            f"newest date); the order follows Publish Date (newest first), not Sort Order. Full order: {cards}")
