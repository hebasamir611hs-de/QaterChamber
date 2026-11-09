"""
cms/tests/visas_immigration/test_visas_section_fields_control_panel.py —
Control_Panel section-field cases of PBI 130701 "Visas & Immigration" (plan
137724 / suite 140362) on the BG Info Section object (`manage-bg-info-section`):
Section Eyebrow 140416-140419, Section Title 140420-140423, Section Body
140424-140426, section Active Status 140477 (dup 140529) / 140530 and the
page-foot Disclaimer 140533-140536.

Every case runs on OWN `QCTEST-130701-B-` sections (pageKey visas-immigration,
own sectionKey, Display Order 600) — the real sections 01-04 are never opened
for edit (bg_rules.md ADDENDUM a). Teardown deletes only the captured ids.

Substitutions disclosed (case literal -> what runs):
  - "Section 01 / 02 / 03 / 04" -> this case's own QCTEST section (order 600,
    rendered as its own row after the real rows). Titles carry the B prefix,
    e.g. "QCTEST-130701-B-140420-<stamp> Arriving at Hamad International Airport".
  - Valid-value cases create the section with the case value directly (one
    Publish); reject cases first create a valid section, then edit it.
  - 140421 "Section 04 title ... 18px": that style belongs to the NESTED
    official-sources block; an own section renders as a row (h2), so only the
    text persistence is asserted.
  - 140477: own section with two own link items; the disclaimer is stored but
    cannot render at order 600 (only the FIRST section with a disclaimer feeds
    the page foot — the real Official sources one at 400).
  - 140530: own section with two own sub-topic blocks (not eight).
  - Disclaimer render (140533, 140535 public step): the user allows briefly
    replacing the real disclaimer (ADDENDUM c) — under real_page_109104.lock the
    own section is published at Display Order 200 (stable sort: after the real
    "arrivals" 200, before "departures" 300, so Official sources stays nested
    in Departures), checked publicly, deleted, and the real disclaimer verified
    back. 140535 runs its 501-character CMS attempt at order 600 BEFORE the
    locked public step, to keep the lock short.
  - 140534 / 140536 (reject cases) run at order 600 without the lock; their
    public step checks the real disclaimer is unchanged.
"""

from __future__ import annotations

import pytest
import allure

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.visas_immigration.bg_admin_page import (
    SLUG_LINK,
    SLUG_SECTION,
    SLUG_SUBTOPIC,
    STATUS_INACTIVE,
    bg_data,
    real_page_lock,
)
from cms.tests.visas_immigration.b_fields_support import (  # noqa: F401 — fixtures imported for use
    AGENT,
    DISCLAIMER_RENDER_ORDER,
    EVIDENCE_DIR,
    MAXLEN_RE,
    PUBLIC_BUDGET_S,
    REAL_DISCLAIMER_EN,
    REAL_ROW_TITLES,
    REQUIRED_RE,
    STAMP,
    anon_pages,
    attach,
    b_disposable,
    create_ok,
    create_section,
    driver_for,
    edit_own,
    editor_session,
    frontend_limit_check,
    halted,
    name,
    record_finding,
    required_message_for,
    rtl_aligned_right,
    stored,
    style_mismatches,
    sync_identity,
    teardown_entries,
)

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130701,
              pytest.mark.functional_low, pytest.mark.xdist_group("visas_b_sections")]

AUTH_FREE_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
SEC_EYEBROW = ".qc-visas-sec-eyebrow"
SEC_TITLE = ".qc-visas-sec-title"
PROSE = ".qc-visas-prose"
DISCLAIMER = "[data-qc-visas-disclaimer]"
REAL_DISCLAIMER_AR = "قد تتغير متطلبات التأشيرة والدخول والمغادرة. تحقق من المتطلبات الحالية لدى الجهة المختصة قبل السفر."


def _ar_title(tc: str) -> str:
    return f"قسم اختبار {tc}-{STAMP}"


def _row_poll(view, title: str, predicate=lambda r: True, locale: str = "en") -> dict:
    return view.b_poll(lambda m: any(r["title"] == title and predicate(r) for r in m["rows"]), PUBLIC_BUDGET_S,
                       locale=locale)


def _row(view, title: str) -> dict | None:
    return view.row_by_title(title)


def _ar_max(n: int) -> str:
    base = ("اختبار الحد الأقصى لطول النص " * 30)[: n - 1].rstrip()
    return base + "ب" * (n - len(base))


def _refusal_problems(result: dict, what: str) -> list[str]:
    if result["went_through"]:
        return [f"PRODUCT: Publish went through with {what} — the value was SAVED (editbar {result.get('editbar')})"]
    problems = []
    if not result["refused"]:
        problems.append(f"Publish was neither refused with validation evidence nor saved: {result['evidence']}")
    if result.get("success_message_shown"):
        problems.append("a success message was shown although the save was refused")
    return problems


def _wording(tc: str, key: str, result: dict, pattern, expected: str) -> None:
    shown = required_message_for(result, key)
    if not result["went_through"] and not pattern.search(shown):
        record_finding(tc, "wording (block works)", field=key, expected=expected, shown=shown)


def _new_section(page, registry, tc: str, **overrides) -> dict:
    driver = editor_session(page)
    overrides.setdefault("sectionTitle_ar", _ar_title(tc))
    return create_section(driver, registry, tc, **overrides)


def _real_disclaimer_intact(anon_pages) -> list[str]:
    view = anon_pages()
    view.open_page("en")
    model = view.model() or {}
    problems = []
    if " ".join(model.get("disclaimer", "").split()) != REAL_DISCLAIMER_EN:
        problems.append(f"public disclaimer now reads {model.get('disclaimer')!r}")
    return problems


# ===========================================================================
# Section Eyebrow
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Eyebrow")
@allure.title("Section Eyebrow accepts a valid bilingual value and renders it on the public page")
@pytest.mark.bilingual
@pytest.mark.tc_140416
def test_140416_section_eyebrow_valid_bilingual(page, b_disposable, anon_pages):
    en, ar = "QCTEST-130701 Travel guidance", "إرشادات السفر"
    sec = _new_section(page, b_disposable, "140416", sectionEyebrow=en, sectionEyebrow_ar=ar)
    view = anon_pages()
    poll = _row_poll(view, sec["title"], lambda r: r["eyebrow"] == en)
    style = view.b_el(SEC_EYEBROW, sec["title"])
    view_ar = anon_pages()
    poll_ar = _row_poll(view_ar, sec["title_ar"], lambda r: r["eyebrow"] == ar, "ar")
    style_ar = view_ar.b_el(SEC_EYEBROW, sec["title_ar"])
    shot = view_ar.b_evidence(EVIDENCE_DIR, "140416_public_ar")
    attach({"poll": poll, "style": style, "poll_ar": poll_ar, "style_ar": style_ar}, "140416 facts")
    assert poll["ok"], "the EN section eyebrow never rendered the new value"
    assert poll["within_budget"], f"EN eyebrow appeared after {poll['seen_at']} s"
    assert poll_ar["ok"], f"the AR section eyebrow never rendered {ar!r} ({shot})"
    problems = style_mismatches(style, "14px", "400", "#911731", width=760)
    problems += [f"AR {p}" for p in style_mismatches(style_ar, "14px", "400", "#911731")]
    if not rtl_aligned_right(style_ar):
        problems.append(f"AR eyebrow not right-aligned: {style_ar and (style_ar['direction'], style_ar['text_align'])}")
    assert not problems, f"style differs from the case: {problems}"


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Eyebrow")
@allure.title("Section Eyebrow rejects an empty mandatory value")
@pytest.mark.tc_140417
def test_140417_section_eyebrow_empty_rejected(page, b_disposable, anon_pages):
    _section_reject_text(page, b_disposable, anon_pages, "140417", "sectionEyebrow", "QCTEST-130701 Travel guidance",
                         "", "eyebrow", "an empty Section Eyebrow EN")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Eyebrow")
@allure.title("Section Eyebrow rejects a whitespace-only value")
@pytest.mark.tc_140419
def test_140419_section_eyebrow_whitespace_rejected(page, b_disposable, anon_pages):
    _section_reject_text(page, b_disposable, anon_pages, "140419", "sectionEyebrow", "Departures", "   ", "eyebrow",
                         "a whitespace-only Section Eyebrow EN")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Eyebrow")
@allure.title("Section Eyebrow enforces its 100-character maximum at the boundary")
@pytest.mark.tc_140418
def test_140418_section_eyebrow_100_boundary(page, b_disposable, anon_pages):
    value = "QCTEST-130701-SECEYEBROW-100-" + "A" * 71
    _section_boundary(page, b_disposable, anon_pages, "140418", "sectionEyebrow", value, 100, SEC_EYEBROW, "eyebrow")


# ===========================================================================
# Section Title
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Title")
@allure.title("Section Title accepts a valid bilingual value and renders it on the public page")
@pytest.mark.bilingual
@pytest.mark.tc_140420
def test_140420_section_title_valid_bilingual(page, b_disposable, anon_pages):
    driver = editor_session(page)
    title, ar = name("140420", "Arriving at Hamad International Airport"), "الوصول إلى مطار حمد الدولي"
    sec = create_section(driver, b_disposable, "140420", "Arriving at Hamad International Airport",
                         sectionTitle_ar=f"{ar} {STAMP}")
    view = anon_pages()
    poll = _row_poll(view, title)
    style = view.b_el(SEC_TITLE, title)
    view_ar = anon_pages()
    poll_ar = _row_poll(view_ar, sec["title_ar"], locale="ar")
    style_ar = view_ar.b_el(SEC_TITLE, sec["title_ar"])
    view_ar.b_evidence(EVIDENCE_DIR, "140420_public_ar")
    attach({"poll": poll, "style": style, "poll_ar": poll_ar, "style_ar": style_ar}, "140420 facts")
    assert sec["title"] == title
    assert poll["ok"] and poll["within_budget"], f"EN title: {poll}"
    assert poll_ar["ok"], f"the AR section title {sec['title_ar']!r} never rendered"
    problems = style_mismatches(style, "36px", "700", "#1D1D1B", width=760)
    problems += [f"AR {p}" for p in style_mismatches(style_ar, "36px", "700", "#1D1D1B")]
    if not rtl_aligned_right(style_ar):
        problems.append("AR title not right-aligned")
    assert not problems, f"style differs from the case: {problems}"


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Title")
@allure.title("Section Title rejects an empty mandatory value")
@pytest.mark.tc_140421
def test_140421_section_title_empty_rejected(page, b_disposable, anon_pages):
    _section_reject_title(page, b_disposable, anon_pages, "140421", "", "an empty Section Title EN", "Official sources")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Title")
@allure.title("Section Title rejects a whitespace-only value")
@pytest.mark.tc_140423
def test_140423_section_title_whitespace_rejected(page, b_disposable, anon_pages):
    _section_reject_title(page, b_disposable, anon_pages, "140423", "   ", "a whitespace-only Section Title EN",
                          "Departing from Hamad International Airport")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Title")
@allure.title("Section Title enforces its 120-character maximum at the boundary")
@pytest.mark.tc_140422
def test_140422_section_title_120_boundary(page, b_disposable, anon_pages):
    head = f"QCTEST-130701-B-140422-{STAMP}-SECTITLE-120-"
    value = head + "A" * (120 - len(head))
    ar_value = _ar_max(120)
    driver = editor_session(page)
    sec = driver_for(driver, SLUG_SECTION)
    data = bg_data(SLUG_SECTION, value, f"qctest-130701-b-140422-{STAMP}", displayOrder=600, sectionTitle_ar=ar_value,
                   highlightCardEyebrow="QCTEST card", highlightCardHeading="QCTEST card 140422")
    entry = create_ok(sec, b_disposable, data, "140422", "section")
    facts = {"stored_max": stored(sec, entry)["sectionTitle"]}
    view = anon_pages()
    facts["poll"] = _row_poll(view, value)
    facts["el"] = view.b_el(SEC_TITLE, value)
    facts["frontend"] = frontend_limit_check(anon_pages, "140422", SEC_TITLE, {"en": value, "ar": ar_value},
                                             {"en": value, "ar": ar_value})
    facts["over"] = edit_own(sec, entry, "140422", "121", typed={"sectionTitle": value + "A"},
                             before_save=lambda d: {"value_len": len(d.value_of("sectionTitle")),
                                                    "counter": d.counter_reading("sectionTitle")})
    entry = sync_identity(sec, b_disposable, entry)
    facts["stored_after"] = stored(sec, entry)["sectionTitle"]
    attach(facts, "140422 facts")
    assert facts["stored_max"] == value, f"stored {facts['stored_max']!r}"
    assert facts["poll"]["ok"] and facts["poll"]["within_budget"], f"public 120-character title: {facts['poll']}"
    problems = []
    el = facts["el"] or {}
    if el and el["scroll_width"] > el["client_width"] + 1:
        problems.append(f"the 120-character title does not wrap inside its {el['width']}px box "
                        f"(content {el['scroll_width']}px)")
    if el and abs(el["width"] - 760) > 2:
        problems.append(f"title box {el['width']}px (expected 760px)")
    problems += [f"public {r['locale'].upper()} @{r['viewport']}: {r['problems']} ({r['screenshot']})"
                 for r in facts["frontend"] if r["problems"]]
    if len(facts["stored_after"]) > 120:
        problems.append(f"PRODUCT: {len(facts['stored_after'])} characters were STORED (limit 120)")
    elif facts["stored_after"] != value:
        problems.append(f"stored value after the 121-character attempt is {facts['stored_after']!r}")
    if facts["over"]["went_through"] and facts["over"]["before_save"]["value_len"] > 120:
        problems.append("PRODUCT: Publish with 121 characters went through")
    _wording("140422", "sectionTitle", facts["over"], MAXLEN_RE, "a maximum-length error")
    assert not problems, f"120-character boundary: {problems}"


# ===========================================================================
# Section Body
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Body")
@allure.title("Section Body accepts two rich-text paragraphs and renders both on the public page")
@pytest.mark.tc_140424
def test_140424_section_body_two_paragraphs(page, b_disposable, anon_pages):
    p1, p2 = "QCTEST-130701 reference intro paragraph", "QCTEST-130701 requirements vary by nationality and residency"
    sec = _new_section(page, b_disposable, "140424", sectionBody=f"{p1}\n{p2}",
                       sectionBody_ar="فقرة تمهيدية مرجعية\nتختلف المتطلبات حسب الجنسية والإقامة")
    stored_html = stored(sec["driver"], sec["entry"])["sectionBody_html"]
    view = anon_pages()
    poll = _row_poll(view, sec["title"], lambda r: p2 in r["body"])
    markup = view.b_markup(PROSE, sec["title"])
    style = view.b_el(PROSE, sec["title"])
    attach({"stored_html": stored_html, "poll": poll, "markup": markup, "style": style}, "140424 facts")
    assert stored_html.count("<p>") == 2, f"the editor stored {stored_html!r}"
    assert poll["ok"] and poll["within_budget"], f"public body: {poll}"
    problems = style_mismatches(style, "16px", "400", "#6C6C6B", width=760)
    if (markup or {}).get("paragraphs") != [p1, p2]:
        problems.append(f"paragraphs rendered: {(markup or {}).get('paragraphs')}")
    if "<p" in (markup or {}).get("text", ""):
        problems.append("raw HTML tags are shown as visible text")
    assert not problems, f"public body differs from the case: {problems}"


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Body")
@allure.title("Section Body rejects an empty mandatory value")
@pytest.mark.tc_140425
def test_140425_section_body_empty_rejected(page, b_disposable, anon_pages):
    _section_reject_rich(page, b_disposable, anon_pages, "140425", "sectionBody", "", "an empty Section Body EN")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Body")
@allure.title("Section Body rejects a whitespace-only value")
@pytest.mark.tc_140426
def test_140426_section_body_whitespace_rejected(page, b_disposable, anon_pages):
    _section_reject_rich(page, b_disposable, anon_pages, "140426", "sectionBody", "   ", "a whitespace-only Section Body EN")


# ===========================================================================
# Section Active Status
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Active Status")
@allure.title("Setting a section Active Status to Active makes the section appear on the public page")
@pytest.mark.tc_140477
@pytest.mark.tc_140529
def test_140477_section_activate_shows_section(page, browser, b_disposable, anon_pages):
    # User decision 2026-10-06: own section at Display Order 200 under real_page_109104.lock so its
    # disclaimer feeds the page foot (first section with a disclaimer wins). Created INACTIVE before
    # the lock (invisible to visitors); activation -> public check -> guarded delete -> real disclaimer
    # and real row order verified back, all inside the lock.
    disclaimer = "QCTEST-130701 disclaimer 140477"
    _halt_guard()
    driver = editor_session(page)
    sec = create_section(driver, b_disposable, "140477", "Official sources", activeStatus=False,
                         displayOrder=DISCLAIMER_RENDER_ORDER, sectionTitle_ar=_ar_title("140477"),
                         disclaimerBody=disclaimer, disclaimerBody_ar="إخلاء مسؤولية تجريبي",
                         expect_status=(STATUS_PUBLISHED, STATUS_INACTIVE), check_active=False)
    links = driver_for(driver, SLUG_LINK)
    for i in (1, 2):
        create_ok(links, b_disposable, bg_data(SLUG_LINK, name("140477", f"link {i}"), sec["key"],
                                               displayOrder=100 * i), "140477", f"link{i}")
    sec["driver"].open_list_all()
    facts = {"status_inactive": sec["driver"].row_status_of(sec["entry"])}
    view = anon_pages()
    view.open_page("en")
    model = view.model() or {}
    facts["absent_before"] = _row(view, sec["title"]) is None and sec["title"] not in view.page.content()
    facts["rows_before"] = [r["title"] for r in model.get("rows", [])][:3]
    facts["stored_before"] = stored(sec["driver"], sec["entry"])["activeStatus"]
    with real_page_lock(AGENT):
        try:
            facts["edit"] = edit_own(sec["driver"], sec["entry"], "140477", "activate", data={"activeStatus": True})
            facts["status_after"] = sec["driver"].wait_row_status(sec["entry"], (STATUS_PUBLISHED,))
            facts["stored_after"] = stored(sec["driver"], sec["entry"])["activeStatus"]
            view2 = anon_pages()
            facts["poll"] = _row_poll(view2, sec["title"], lambda r: len(r["links"]) == 2)
            m2 = view2.model() or {}
            row = _row(view2, sec["title"]) or {}
            facts["links"] = row.get("links")
            facts["disclaimer"] = m2.get("disclaimer")
            facts["rows_live"] = [r["title"] for r in m2.get("rows", [])]
            facts["title_style"] = view2.b_el(SEC_TITLE, sec["title"])
            facts["shot"] = view2.b_evidence(EVIDENCE_DIR, "140477_public_en_order200")
        finally:
            facts["restore"] = _remove_and_verify_real_disclaimer(browser, b_disposable, anon_pages, "140477")
    attach(facts, "140477 facts")
    assert not facts["restore"], f"REAL DISCLAIMER / ROW ORDER NOT RESTORED: {facts['restore']}"
    assert facts["stored_before"] == "false", f"precondition: stored Active Status {facts['stored_before']!r}"
    assert facts["absent_before"], "the inactive section is visible on the public page"
    assert facts["rows_before"] == REAL_ROW_TITLES, f"real rows before: {facts['rows_before']}"
    assert facts["edit"]["went_through"] and facts["edit"]["success_message_shown"], facts["edit"]
    assert facts["stored_after"] == "true", f"Active Status did not persist: {facts['stored_after']!r}"
    assert facts["status_after"] == STATUS_PUBLISHED, f"status after activation {facts['status_after']!r}"
    assert facts["poll"]["ok"], f"the activated section never appeared with both links ({facts['shot']})"
    assert facts["poll"]["within_budget"], f"the activated section appeared after {facts['poll']['seen_at']} s"
    assert sorted(link["title"] for link in facts["links"]) == [name("140477", "link 1"), name("140477", "link 2")]
    assert " ".join((facts["disclaimer"] or "").split()) == disclaimer, (
        f"the page-foot disclaimer reads {facts['disclaimer']!r}, not the activated section's")
    problems = style_mismatches(facts["title_style"], weight="700", color_hex="#1D1D1B")
    if facts["title_style"] and facts["title_style"]["font_size"] != "18px":
        problems.append(f"section title {facts['title_style']['font_size']} (case: 18px — that size belongs to the "
                        f"NESTED Official sources block; an own section renders as a row h2)")
    if problems:
        record_finding("140477", "style note", problems=problems)


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Section Active Status")
@allure.title("A section Active Status toggle persists both states and re-activating restores the section")
@pytest.mark.tc_140530
def test_140530_section_toggle_persists(page, b_disposable, anon_pages):
    driver = editor_session(page)
    sec = create_section(driver, b_disposable, "140530", "Arriving at Hamad International Airport",
                         sectionTitle_ar=_ar_title("140530"))
    blocks = driver_for(driver, SLUG_SUBTOPIC)
    heads = [name("140530", f"block {i}") for i in (1, 2)]
    for i, head in enumerate(heads, 1):
        create_ok(blocks, b_disposable, bg_data(SLUG_SUBTOPIC, head, sec["key"], displayOrder=100 * i),
                  "140530", f"block{i}")
    facts = {}
    facts["off"] = edit_own(sec["driver"], sec["entry"], "140530", "deactivate", data={"activeStatus": False})
    facts["stored_off"] = stored(sec["driver"], sec["entry"])["activeStatus"]
    view = anon_pages()
    # the page must be RENDERED (real rows present — another agent may briefly unpublish the real page
    # under the lock) and the own section absent
    facts["poll_off"] = view.b_poll(lambda m: [r["title"] for r in m["rows"]][:3] == REAL_ROW_TITLES
                                    and all(r["title"] != sec["title"] for r in m["rows"]), PUBLIC_BUDGET_S)
    facts["real_off"] = [r["title"] for r in (view.model() or {}).get("rows", [])][:3]
    facts["on"] = edit_own(sec["driver"], sec["entry"], "140530", "reactivate", data={"activeStatus": True})
    facts["stored_on"] = stored(sec["driver"], sec["entry"])["activeStatus"]
    view2 = anon_pages()
    facts["poll_on"] = _row_poll(view2, sec["title"], lambda r: [b["heading"] for b in r["blocks"]] == heads)
    titles = [r["title"] for r in (view2.model() or {}).get("rows", [])]
    facts["titles_on"] = titles
    attach(facts, "140530 facts")
    assert facts["off"]["went_through"] and facts["off"]["success_message_shown"], facts["off"]
    assert facts["stored_off"] == "false", f"Inactive did not persist: {facts['stored_off']!r}"
    assert facts["poll_off"]["ok"] and facts["poll_off"]["within_budget"], f"section still visible: {facts['poll_off']}"
    assert facts["real_off"] == REAL_ROW_TITLES, f"real rows while inactive: {facts['real_off']}"
    assert facts["on"]["went_through"] and facts["on"]["success_message_shown"], facts["on"]
    assert facts["stored_on"] == "true", f"Active did not persist: {facts['stored_on']!r}"
    assert facts["poll_on"]["ok"] and facts["poll_on"]["within_budget"], f"section not restored: {facts['poll_on']}"
    assert titles[:3] == REAL_ROW_TITLES and sec["title"] in titles[3:], f"row order after re-activation: {titles}"


# ===========================================================================
# Disclaimer
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Disclaimer")
@allure.title("Disclaimer accepts a valid bilingual rich-text value and renders it on the public page")
@pytest.mark.bilingual
@pytest.mark.tc_140533
def test_140533_disclaimer_valid_bilingual(page, browser, b_disposable, anon_pages):
    en = ("QCTEST-130701 visa, entry and departure requirements can change. Verify current requirements with the "
          "competent authority before travelling.")
    ar = "قد تتغير متطلبات التأشيرة والدخول والمغادرة. تحقق من المتطلبات الحالية لدى الجهة المختصة قبل السفر."
    _halt_guard()
    driver = editor_session(page)
    facts: dict = {}
    with real_page_lock(AGENT):
        try:
            sec = create_section(driver, b_disposable, "140533", "disclaimer", displayOrder=DISCLAIMER_RENDER_ORDER,
                                 sectionTitle_ar=_ar_title("140533"), disclaimerBody=en, disclaimerBody_ar=ar)
            view = anon_pages()
            facts["poll"] = view.b_poll(lambda m: " ".join(m["disclaimer"].split()) == en, PUBLIC_BUDGET_S)
            facts["style"] = view.b_el(DISCLAIMER)
            facts["links_bottom"] = view.b_source_links_bottom()
            facts["headings"] = view.headings_in_order()
            facts["shot_en"] = view.b_evidence(EVIDENCE_DIR, "140533_public_en")
            view_ar = anon_pages()
            facts["poll_ar"] = view_ar.b_poll(lambda m: " ".join(m["disclaimer"].split()) == ar, PUBLIC_BUDGET_S,
                                              locale="ar")
            facts["style_ar"] = view_ar.b_el(DISCLAIMER)
            facts["ar_rows"] = [r["title"] for r in (view_ar.model() or {}).get("rows", [])]
            facts["shot_ar"] = view_ar.b_evidence(EVIDENCE_DIR, "140533_public_ar")
        finally:
            facts["restore"] = _remove_and_verify_real_disclaimer(browser, b_disposable, anon_pages, "140533")
    attach(facts, "140533 facts")
    assert not facts["restore"], f"REAL DISCLAIMER NOT RESTORED: {facts['restore']}"
    assert facts["poll"]["ok"], f"the EN disclaimer never rendered the new value ({facts.get('shot_en')})"
    assert facts["poll"]["within_budget"], f"EN disclaimer appeared after {facts['poll']['seen_at']} s"
    assert facts["poll_ar"]["ok"], f"the AR disclaimer never rendered the new value ({facts.get('shot_ar')})"
    # the case's AR text equals the real AR disclaimer word for word: prove the own section (order 200,
    # the first with a disclaimer) is the one live on the AR page
    assert _ar_title("140533") in facts["ar_rows"], f"own section not live on the AR page: {facts['ar_rows']}"
    problems = style_mismatches(facts["style"], "14px", "400", "#6C6C6B", width=1297)
    if facts["style"] and facts["style"]["top"] < facts["links_bottom"]:
        problems.append(f"the disclaimer (top {facts['style']['top']}) is not below the source links "
                        f"(bottom {facts['links_bottom']})")
    if not rtl_aligned_right(facts["style_ar"]):
        problems.append("AR disclaimer not right-aligned")
    assert not problems, f"disclaimer differs from the case: {problems}"


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Disclaimer")
@allure.title("Disclaimer rejects an empty mandatory value")
@pytest.mark.tc_140534
def test_140534_disclaimer_empty_rejected(page, b_disposable, anon_pages):
    _disclaimer_reject(page, b_disposable, anon_pages, "140534", "", "an empty Disclaimer Body EN")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Disclaimer")
@allure.title("Disclaimer rejects a whitespace-only value")
@pytest.mark.tc_140536
def test_140536_disclaimer_whitespace_rejected(page, b_disposable, anon_pages):
    _disclaimer_reject(page, b_disposable, anon_pages, "140536", "   ", "a whitespace-only Disclaimer Body EN")


@AUTH_FREE_PAGE
@allure.epic("Business Gateway")
@allure.feature("Visas & Immigration — Control Panel")
@allure.story("Disclaimer")
@allure.title("Disclaimer enforces its 500-character maximum at the boundary")
@pytest.mark.tc_140535
def test_140535_disclaimer_500_boundary(page, browser, b_disposable, anon_pages):
    value = "QCTEST-130701-DISCLAIMER-500-" + "A" * 471
    ar_value = _ar_max(500)
    assert len(value) == 500 and len(ar_value) == 500
    over_value = value + "A"   # the case's 501-character value
    _halt_guard()
    driver = editor_session(page)
    facts: dict = {}
    # A REFUSED create on this form once wrote its Arabic values onto ANOTHER agent's record (live
    # 2026-10-06, see report) — so the section is created with a short disclaimer and every length
    # attempt is an EDIT of this own record (a refused edit only ever touches its own entry id).
    sec = create_section(driver, b_disposable, "140535", "disclaimer", sectionTitle_ar=_ar_title("140535"),
                         disclaimerBody="QCTEST-130701 baseline disclaimer 140535", disclaimerBody_ar="إخلاء مسؤولية")
    d = sec["driver"]
    full, full_ar = value, ar_value
    facts["attempts"] = []
    for n in (500, 491, 490, 480, 450):
        value, ar_value = full[:n], full_ar[:n]
        res = edit_own(d, sec["entry"], "140535", f"len{n}", rich_typed={"disclaimerBody": value,
                                                                        "disclaimerBody_ar": ar_value})
        facts["attempts"].append({"n": n, "went_through": res["went_through"],
                                  "errors": res["evidence"].get("field_errors"), "screenshot": res["screenshot"]})
        if res["went_through"]:
            break
    assert facts["attempts"][-1]["went_through"], f"no disclaimer length up to 450 was accepted: {facts['attempts']}"
    facts["stored_500"] = stored(d, sec["entry"])
    facts["block_500"] = d.rich_block_text("disclaimerBody")
    facts["over"] = edit_own(d, sec["entry"], "140535", "501", rich_typed={"disclaimerBody": over_value},
                             before_save=lambda drv: {"block": drv.rich_block_text("disclaimerBody")})
    facts["stored_after_over"] = stored(d, sec["entry"])
    over_len = len(" ".join(facts["stored_after_over"]["disclaimerBody"].split()))
    if over_len != len(value):   # put the max accepted value back for the public step
        facts["reset"] = edit_own(d, sec["entry"], "140535", "reset500", rich_typed={"disclaimerBody": value})
    with real_page_lock(AGENT):
        try:
            facts["move"] = edit_own(d, sec["entry"], "140535", "order200",
                                     data={"displayOrder": DISCLAIMER_RENDER_ORDER})
            view = anon_pages()
            facts["poll"] = view.b_poll(lambda m: " ".join(m["disclaimer"].split()) == value, PUBLIC_BUDGET_S)
            facts["el"] = view.b_el(DISCLAIMER)
            facts["frontend"] = frontend_limit_check(anon_pages, "140535", DISCLAIMER, {"en": value, "ar": ar_value})
        finally:
            facts["restore"] = _remove_and_verify_real_disclaimer(browser, b_disposable, anon_pages, "140535")
    attach(facts, "140535 facts")
    assert not facts["restore"], f"REAL DISCLAIMER NOT RESTORED: {facts['restore']}"
    stored_500 = " ".join(facts["stored_500"]["disclaimerBody"].split())
    assert stored_500 == value, f"the {len(value)}-character disclaimer was stored as {len(stored_500)} characters"
    assert facts["move"]["went_through"], facts["move"]
    assert facts["poll"]["ok"] and facts["poll"]["within_budget"], f"public 500-character disclaimer: {facts['poll']}"
    problems = []
    el = facts["el"] or {}
    if el and el["scroll_width"] > el["client_width"] + 1:
        problems.append(f"the disclaimer does not wrap inside its box (content {el['scroll_width']}px > {el['client_width']}px)")
    if el and abs(el["width"] - 1297) > 2:
        problems.append(f"disclaimer box {el['width']}px (expected 1297px)")
    problems += [f"public {r['locale'].upper()} @{r['viewport']}: {r['problems']} ({r['screenshot']})"
                 for r in facts["frontend"] if r["problems"]]
    if len(value) < 500:
        problems.insert(0, f"PRODUCT: exactly 500 visible characters were REFUSED on Publish "
                           f"({facts['attempts'][0]['errors']}); the longest accepted value was {len(value)} characters "
                           f"(attempts {[(a['n'], a['went_through']) for a in facts['attempts']]}) -> the limit counts "
                           f"stored HTML markup, not visible text; the public check used {len(value)} characters")
    if over_len > 500:
        problems.append(f"PRODUCT: {over_len} characters were STORED in Disclaimer Body EN (limit 500); "
                        f"Publish went_through={facts['over']['went_through']}, no counter on the field "
                        f"(block: {facts['over']['before_save']['block'][:120]!r})")
    _wording("140535", "disclaimerBody", facts["over"], MAXLEN_RE, "a maximum-length error")
    assert not problems, f"500-character boundary: {problems}"


# ===========================================================================
# shared case bodies
# ===========================================================================
def _halt_guard() -> None:
    reason = halted()
    if reason:
        pytest.fail(f"B real-page work is HALTED (restore problem earlier): {reason}")


def _remove_and_verify_real_disclaimer(browser, registry, anon_pages, tc: str) -> list[str]:
    """Inside the lock: guarded delete of this test's own records, then the real disclaimer must be back."""
    problems = []
    try:
        teardown_entries(browser, registry, f"{tc} (inside real_page_109104.lock)")
    except AssertionError as exc:
        problems.append(str(exc))
    own_titles = {_ar_title(tc), }
    for locale, want in (("en", REAL_DISCLAIMER_EN), ("ar", REAL_DISCLAIMER_AR)):
        view = anon_pages()
        ok = view.b_poll(lambda m: " ".join(m["disclaimer"].split()) == want
                         and not any(r["title"] in own_titles or r["title"].startswith(f"QCTEST-130701-B-{tc}")
                                     for r in m["rows"]), 5.0, locale=locale)
        if not ok["ok"]:
            problems.append(f"{locale.upper()} public disclaimer is not the real one: {(view.model() or {}).get('disclaimer')!r}")
        view.b_evidence(EVIDENCE_DIR, f"{tc}_real_disclaimer_back_{locale}")
        rows = [r["title"] for r in (view.model() or {}).get("rows", [])][:3]
        if locale == "en" and rows != REAL_ROW_TITLES:
            problems.append(f"real rows after the delete: {rows}")
    if problems:
        record_finding(tc, "REAL DISCLAIMER RESTORE PROBLEM", problems=problems)
    return problems


def _section_reject_text(page, registry, anon_pages, tc, key, baseline, bad, model_key, what) -> None:
    sec = _new_section(page, registry, tc, **{key: baseline})
    d = sec["driver"]
    flags = {}

    def _before(drv):
        flags.update(drv.field_flags(key))
        return {"value": drv.value_of(key)}

    result = edit_own(d, sec["entry"], tc, "reject", typed={key: bad}, before_save=_before)
    after = stored(d, sec["entry"])[key]
    view = anon_pages()
    view.open_page("en")
    row = _row(view, sec["title"]) or {}
    attach({"flags": flags, "result": result, "stored": after, "public_row": row}, f"{tc} facts")
    problems = _refusal_problems(result, what)
    if bad == "" and not (flags.get("required_attr") or flags.get("aria_required") or flags.get("label_star")):
        problems.append(f"the field is not marked mandatory (label {flags.get('label')!r}, required="
                        f"{flags.get('required_attr')})")
    if after != baseline:
        problems.append(f"stored value is now {after!r}")
    if row.get(model_key) != baseline:
        problems.append(f"public {model_key} now {row.get(model_key)!r} (expected {baseline!r})")
    _wording(tc, key, result, REQUIRED_RE, "the field is required")
    assert not problems, f"{what}: {problems} (screenshot {result['screenshot']})"


def _section_reject_title(page, registry, anon_pages, tc, bad, what, case_title) -> None:
    driver = editor_session(page)
    sec = create_section(driver, registry, tc, case_title, sectionTitle_ar=_ar_title(tc))
    d = sec["driver"]
    flags = {}

    def _before(drv):
        flags.update(drv.field_flags("sectionTitle"))
        return {"value": drv.value_of("sectionTitle")}

    result = edit_own(d, sec["entry"], tc, "reject", typed={"sectionTitle": bad}, before_save=_before)
    entry = sync_identity(d, registry, sec["entry"])
    after = stored(d, entry)["sectionTitle"]
    view = anon_pages()
    view.open_page("en")
    present = _row(view, sec["title"]) is not None
    blank_heads = [r for r in (view.model() or {}).get("rows", []) if not r["title"].strip()]
    attach({"flags": flags, "result": result, "stored": after, "public_present": present}, f"{tc} facts")
    problems = _refusal_problems(result, what)
    if bad == "" and not (flags.get("required_attr") or flags.get("aria_required") or flags.get("label_star")):
        problems.append(f"Section Title EN not marked mandatory: {flags}")
    if after != sec["title"]:
        problems.append(f"stored title is now {after!r}")
    if not present:
        problems.append("the public row no longer shows the original title")
    if blank_heads:
        problems.append(f"{len(blank_heads)} row(s) render a blank heading")
    _wording(tc, "sectionTitle", result, REQUIRED_RE, "the field is required")
    assert not problems, f"{what}: {problems} (screenshot {result['screenshot']})"


def _section_reject_rich(page, registry, anon_pages, tc, key, bad, what) -> None:
    p1, p2 = f"QCTEST-130701 baseline paragraph one {tc}", f"QCTEST-130701 baseline paragraph two {tc}"
    sec = _new_section(page, registry, tc, **{key: f"{p1}\n{p2}"})
    d = sec["driver"]
    result = edit_own(d, sec["entry"], tc, "reject", rich_typed={key: bad},
                      before_save=lambda drv: {"html": drv.rich_data(key), "block": drv.rich_block_text(key)})
    after = stored(d, sec["entry"])[f"{key}_html"]
    view = anon_pages()
    view.open_page("en")
    markup = view.b_markup(PROSE, sec["title"]) or {}
    attach({"result": result, "stored_html": after, "markup": markup}, f"{tc} facts")
    problems = _refusal_problems(result, what)
    if bad == "" and "*" not in result["before_save"]["block"] and "Required" not in result["before_save"]["block"]:
        problems.append(f"the field is not marked mandatory (block {result['before_save']['block'][:80]!r})")
    if markup.get("paragraphs") != [p1, p2]:
        problems.append(f"public body now renders {markup.get('paragraphs')}")
    _wording(tc, key, result, REQUIRED_RE, "the field is required")
    assert not problems, f"{what}: {problems} (stored {after!r}; screenshot {result['screenshot']})"


def _disclaimer_reject(page, registry, anon_pages, tc, bad, what) -> None:
    sec = _new_section(page, registry, tc, disclaimerBody=f"QCTEST-130701 baseline disclaimer {tc}",
                       disclaimerBody_ar="إخلاء مسؤولية أساسي")
    d = sec["driver"]
    result = edit_own(d, sec["entry"], tc, "reject", rich_typed={"disclaimerBody": bad},
                      before_save=lambda drv: {"html": drv.rich_data("disclaimerBody"),
                                               "block": drv.rich_block_text("disclaimerBody")})
    after = stored(d, sec["entry"])["disclaimerBody_html"]
    public = _real_disclaimer_intact(anon_pages)
    attach({"result": result, "stored_html": after, "public": public}, f"{tc} facts")
    problems = _refusal_problems(result, what)
    if bad == "" and "*" not in result["before_save"]["block"] and "Required" not in result["before_save"]["block"]:
        problems.append(f"Disclaimer Body EN is not marked mandatory (block {result['before_save']['block'][:80]!r})")
    problems += public
    _wording(tc, "disclaimerBody", result, REQUIRED_RE, "the field is required")
    assert not problems, f"{what}: {problems} (stored {after!r}; screenshot {result['screenshot']})"


def _section_boundary(page, registry, anon_pages, tc, key, value, limit, selector, model_key) -> None:
    assert len(value) == limit
    ar_value = _ar_max(limit)
    sec = _new_section(page, registry, tc, **{key: value, f"{key}_ar": ar_value})
    d = sec["driver"]
    facts = {"stored_max": stored(d, sec["entry"])[key]}
    view = anon_pages()
    facts["poll"] = _row_poll(view, sec["title"], lambda r: r[model_key] == value)
    facts["frontend"] = frontend_limit_check(anon_pages, tc, selector, {"en": value, "ar": ar_value},
                                             {"en": sec["title"], "ar": sec["title_ar"]})
    facts["over"] = edit_own(d, sec["entry"], tc, f"{limit + 1}", typed={key: value + "A"},
                             before_save=lambda drv: {"value_len": len(drv.value_of(key)),
                                                      "counter": drv.counter_reading(key)})
    facts["stored_after"] = stored(d, sec["entry"])[key]
    attach(facts, f"{tc} facts")
    assert facts["stored_max"] == value, f"stored {facts['stored_max']!r}"
    assert facts["poll"]["ok"] and facts["poll"]["within_budget"], f"public {limit}-character {model_key}: {facts['poll']}"
    problems = [f"public {r['locale'].upper()} @{r['viewport']}: {r['problems']} ({r['screenshot']})"
                for r in facts["frontend"] if r["problems"]]
    if len(facts["stored_after"]) > limit:
        problems.append(f"PRODUCT: {len(facts['stored_after'])} characters were STORED (limit {limit})")
    elif facts["stored_after"] != value:
        problems.append(f"stored value after the over-limit attempt is {facts['stored_after']!r}")
    if facts["over"]["went_through"] and facts["over"]["before_save"]["value_len"] > limit:
        problems.append(f"PRODUCT: Publish with {limit + 1} characters went through")
    _wording(tc, key, facts["over"], MAXLEN_RE, "a maximum-length error")
    assert not problems, f"{limit}-character boundary: {problems}"
