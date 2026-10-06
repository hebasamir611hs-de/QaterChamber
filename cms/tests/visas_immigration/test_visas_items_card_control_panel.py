"""
cms/tests/visas_immigration/test_visas_items_card_control_panel.py — Control_Panel
cases for PBI 130701 Visas & Immigration (suite 140362), Agent C: the section
Highlight Card Eyebrow / Heading (BG Info Section fields highlightCardEyebrow
100 / highlightCardHeading 200 on `manage-bg-info-section`), verified on the
public `/web/qatar-chamber/visas-immigration` card (rail of a row with no
supporting photo).

Substitutions (see test_visas_items_control_panel.py for the common ones):
  - "Section 01 / Section 03 highlight card" -> a per-test OWN section
    `QCTEST-130701-C-<tc>-<stamp> section` (pageKey visas-immigration, order
    700, no supporting image, so the card renders — fragment rule: photo wins,
    else the card if eyebrow or heading is set). "Section 01"-style cards get one
    own highlight item (the real Section 01 card has pills, which switches the
    heading to its 20px style); "Section 03"-style cards get none (18px).
  - Current values quoted by the cases ("Before departure", "Reference
    overview", the two headings) are created on the own section prefixed with
    "QCTEST-130701 " so no visitor mistakes them for real copy.
  - Valid-value cases first create the section with a baseline card value and
    then edit it to the case value, so "the record status stays Published" is
    exercised on an edit of a published record.
"""

from __future__ import annotations

import pytest

from cms.pages.visas_immigration.bg_admin_page import SLUG_HIGHLIGHT, SLUG_SECTION, bg_data
from cms.tests.visas_immigration.c_items_support import (  # noqa: F401 — fixtures imported for pytest
    AUTH_FREE_PAGE,
    MAXLEN_RE,
    PUBLIC_BUDGET_S,
    REQUIRED_RE,
    anon_pages,
    ar_text,
    c_disposable,
    create_ok,
    create_section,
    driver_for,
    edit,
    editor_session,
    frontend_limit_check,
    name,
    public_row,
    record_finding,
    refusal_points_at,
    require_active,
    rtl_aligned_right,
    shot_path,
    stored,
    style_mismatches,
    wait_published,
)

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130701,
              pytest.mark.functional_low, pytest.mark.xdist_group("visas_130701_c")]

CARD_EYEBROW = ".qc-visas-card .qc-visas-card-eyebrow"
CARD_TITLE = ".qc-visas-card .qc-visas-card-title"

S01_EYEBROW = "QCTEST-130701 Reference overview"
S01_HEADING = "QCTEST-130701 The page is organized around the passenger journey through arrival and departure."
S03_EYEBROW = "QCTEST-130701 Before departure"
S03_HEADING = ("QCTEST-130701 Keep your passport, boarding pass and any applicable permit ready before "
               "passport control.")


def _norm(text: str) -> str:
    return " ".join((text or "").split())


def _card_section(page, registry, tc: str, eyebrow: str, heading: str, pills: bool, **extra) -> tuple:
    admin = editor_session(page)
    sec = create_section(admin, registry, tc, highlightCardEyebrow=eyebrow, highlightCardEyebrow_ar="عنوان تمهيدي",
                         highlightCardHeading=heading, highlightCardHeading_ar="عنوان البطاقة", **extra)
    if pills:
        hl = driver_for(admin, SLUG_HIGHLIGHT)
        create_ok(hl, registry, bg_data(SLUG_HIGHLIGHT, name(tc, "pill"), sec["key"], displayOrder=100), tc, "pill")
    return driver_for(admin, SLUG_SECTION), sec


def _card(predicate):
    return lambda r: bool(r["card"]) and predicate(r["card"])


def _rejection(tc, result, key, label, what, now, still, public_desc, png):
    if result["went_through"]:
        record_finding(tc, f"LOW validation: {what} accepted on Publish", field=key, stored_after=repr(now),
                       public=public_desc, cms_screenshot=result["screenshot"], public_screenshot=png,
                       messages=result["messages"])
        pytest.fail(f"PRODUCT: Publish with {what} was NOT blocked — saved ('Saved and published.' shown: "
                    f"{result.get('success_message_shown')}), stored now {now!r}; public: {public_desc}; "
                    f"screenshots {result['screenshot']} / {png}")
    assert result["refused"], f"Publish with {what} was neither refused nor saved: {result}"
    assert refusal_points_at(result, key) or label.lower() in result["messages"].lower(), (
        f"refused, but the evidence does not point at {label}: {result['evidence']}")
    if not REQUIRED_RE.search(result["messages"]):
        record_finding(tc, "LOW wording: refusal message does not say the field is required", field=label,
                       shown=result["messages"], screenshot=result["screenshot"])
    assert still, f"after the refused publish the public card no longer shows the previous value; {png}"


def _mandatory_flag(driver, entry, key: str) -> dict:
    driver.open_entry_en(entry.code)
    return driver.field_marked_required(key)


# ===========================================================================
# Card Eyebrow (highlightCardEyebrow, 100)
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.bilingual
@pytest.mark.tc_140432
@pytest.mark.tc_140484
def test_140432_card_eyebrow_valid_bilingual_renders(page, c_disposable, anon_pages):
    """140432 (dup 140484): EN/AR Card Eyebrow accepted and rendered (12/600/#911731, 350px; AR right)."""
    tc = "140432"
    en, ar = "QCTEST-130701 Reference overview", "نظرة عامة مرجعية"
    drv, sec = _card_section(page, c_disposable, tc, "QCTEST-130701-C eyebrow baseline", S01_HEADING, pills=True)
    result = edit(drv, sec["entry"], tc, "eyebrow", data={"highlightCardEyebrow": en, "highlightCardEyebrow_ar": ar})
    assert result["went_through"] and not result["evidence"].get("field_errors"), f"not accepted: {result}"
    assert result.get("success_message_shown"), f"no 'Saved and published.' message: {result.get('editbar')}"
    wait_published(drv, sec["entry"])
    require_active(drv, sec["entry"])
    design = []
    view, row, secs, held = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["eyebrow"]) == en))
    png = view.c_evidence(shot_path(f"{tc}_public_en"))
    assert held, f"EN card eyebrow never read {en!r}: {row and row['card']}; {png}"
    if secs > PUBLIC_BUDGET_S:
        record_finding(tc, "publish-to-public budget exceeded (info)", seconds=round(secs, 1))
    design += style_mismatches(view.c_styles(sec["title"], CARD_EYEBROW)[0], "12px", "600", "#911731", 350)
    view, row, _, held = public_row(anon_pages, sec["title_ar"], _card(lambda c: _norm(c["eyebrow"]) == ar), "ar")
    png_ar = view.c_evidence(shot_path(f"{tc}_public_ar"))
    assert held, f"AR card eyebrow never read {ar!r}: {row and row['card']}; {png_ar}"
    style_ar = view.c_styles(sec["title_ar"], CARD_EYEBROW)[0]
    design += [f"AR {m}" for m in style_mismatches(style_ar, "12px", "600", "#911731")]
    assert rtl_aligned_right(style_ar), f"AR eyebrow not right-aligned: {style_ar}"
    if design:
        record_finding(tc, "design token mismatch", details=design, screenshot=png)
    assert not design, f"design mismatches: {design}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140433
@pytest.mark.tc_140485
def test_140433_card_eyebrow_rejects_empty(page, c_disposable, anon_pages):
    """140433 (dup 140485): Card Eyebrow EN is mandatory — emptying it blocks Publish."""
    tc = "140433"
    drv, sec = _card_section(page, c_disposable, tc, S03_EYEBROW, S03_HEADING, pills=False)
    _, row, _, held = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["eyebrow"]) == S03_EYEBROW))
    assert held, f"PRECONDITION: card eyebrow never rendered: {row and row['card']}"
    flag = _mandatory_flag(drv, sec["entry"], "highlightCardEyebrow")
    marked = flag["required_attr"] or flag["aria_required"] or flag["label_star"]
    if not marked:
        record_finding(tc, "LOW: Card Eyebrow EN is not marked mandatory on the form", flag=flag)
    result = edit(drv, sec["entry"], tc, "empty_eyebrow", data={"highlightCardEyebrow": ""})
    now = stored(drv, sec["entry"]).get("highlightCardEyebrow", "")
    view, row, _, still = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["eyebrow"]) == S03_EYEBROW),
                                     timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    _rejection(tc, result, "highlightCardEyebrow", "Card Eyebrow", "an empty Card Eyebrow EN", now, still,
               f"card {row and row['card']}", png)
    style = view.c_styles(sec["title"], CARD_EYEBROW)[0]
    design = style_mismatches(style, "12px", "600", "#911731")
    assert marked, f"step 2: Card Eyebrow EN is not marked as mandatory: {flag}"
    assert not design, f"design mismatches: {design}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140434
@pytest.mark.tc_140486
def test_140434_card_eyebrow_100_char_boundary(page, c_disposable, anon_pages):
    """140434 (dup 140486): 100 chars accepted and rendered in full in the 350px card; 101 never stored."""
    tc = "140434"
    v100 = "QCTEST-130701-CARDEYEBROW-100-" + "A" * 70
    v101 = v100 + "A"
    assert len(v100) == 100
    a100 = ar_text(100)
    drv, sec = _card_section(page, c_disposable, tc, S01_EYEBROW, S01_HEADING, pills=True)
    counter = None
    drv.open_entry_en(sec["entry"].code)
    counter = drv.counter_limit("highlightCardEyebrow")
    result = edit(drv, sec["entry"], tc, "100", data={"highlightCardEyebrow": v100, "highlightCardEyebrow_ar": a100})
    assert result["went_through"] and not result["evidence"].get("field_errors"), f"100 not accepted: {result}"
    assert result.get("success_message_shown"), f"no 'Saved and published.' message: {result.get('editbar')}"
    wait_published(drv, sec["entry"])
    assert stored(drv, sec["entry"])["highlightCardEyebrow"] == v100
    require_active(drv, sec["entry"])
    _, row, secs, held = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["eyebrow"]) == v100))
    assert held, f"EN: the full 100-character eyebrow never rendered: {row and row['card']}"
    limit = frontend_limit_check(anon_pages, tc, sec["title"], sec["title_ar"], CARD_EYEBROW, v100, a100,
                                 lambda r: bool(r["card"]))
    drv.open_entry_en(sec["entry"].code)
    drv.fill_en("highlightCardEyebrow", v101)
    kept = len(drv.text_value("highlightCardEyebrow"))
    result = edit(drv, sec["entry"], tc, "101", data={"highlightCardEyebrow": v101})
    after = stored(drv, sec["entry"])["highlightCardEyebrow"]
    record_finding(tc, "boundary observation (info)", counter=counter, typed_101_kept=kept, stored_after=len(after),
                   publish_went_through=result["went_through"], messages=result["messages"],
                   frontend={k: v["problems"] for k, v in limit.items()})
    if len(after) == 101:
        record_finding(tc, "LOW validation: Card Eyebrow 100-character limit not enforced",
                       screenshot=result["screenshot"])
    assert len(after) != 101, f"PRODUCT: a 101-character Card Eyebrow was stored; {result['screenshot']}"
    assert after == v100, f"after the 101 attempt the stored value is {len(after)} chars, not the 100 string"
    # Case expects the max-length value to fit its box on the public page (Fable review 2026-10-06; bug 148926).
    overflow = {k: v["problems"] for k, v in limit.items() if v["problems"]}
    assert not overflow, f"PRODUCT (LOW): max-length value overflows publicly: {overflow}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140435
@pytest.mark.tc_140487
def test_140435_card_eyebrow_rejects_whitespace(page, c_disposable, anon_pages):
    """140435 (dup 140487): Card Eyebrow EN of three spaces is blocked; no blank eyebrow renders."""
    tc = "140435"
    drv, sec = _card_section(page, c_disposable, tc, S01_EYEBROW, S01_HEADING, pills=False)
    _, row, _, held = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["eyebrow"]) == S01_EYEBROW))
    assert held, f"PRECONDITION: card eyebrow never rendered: {row and row['card']}"
    result = edit(drv, sec["entry"], tc, "whitespace_eyebrow", data={"highlightCardEyebrow": "   "})
    now = stored(drv, sec["entry"]).get("highlightCardEyebrow", "")
    view, row, _, still = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["eyebrow"]) == S01_EYEBROW),
                                     timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    markup = view.c_markup(sec["title"]) or {}
    blank = [n for n in ((markup.get("card") or {}).get("eyebrow_nodes") or []) if not n.strip()]
    _rejection(tc, result, "highlightCardEyebrow", "Card Eyebrow", "a whitespace-only Card Eyebrow EN", now, still,
               f"card {row and row['card']}, blank eyebrow nodes {len(blank)}", png)
    assert not blank, f"a blank eyebrow element is rendered; {png}"


# ===========================================================================
# Card Heading (highlightCardHeading, 200)
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.bilingual
@pytest.mark.tc_140436
@pytest.mark.tc_140488
def test_140436_card_heading_valid_bilingual_renders(page, c_disposable, anon_pages):
    """140436 (dup 140488): EN/AR Card Heading accepted and rendered (20/700/#1D1D1B; AR right)."""
    tc = "140436"
    en = "QCTEST-130701 the page is organized around the passenger journey through arrival and departure."
    ar = "تم تنظيم الصفحة حول رحلة المسافر عبر الوصول والمغادرة."
    drv, sec = _card_section(page, c_disposable, tc, S01_EYEBROW, "QCTEST-130701-C heading baseline", pills=True)
    result = edit(drv, sec["entry"], tc, "heading", data={"highlightCardHeading": en, "highlightCardHeading_ar": ar})
    assert result["went_through"] and not result["evidence"].get("field_errors"), f"not accepted: {result}"
    assert result.get("success_message_shown"), f"no 'Saved and published.' message: {result.get('editbar')}"
    wait_published(drv, sec["entry"])
    require_active(drv, sec["entry"])
    design = []
    view, row, secs, held = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["heading"]) == en))
    png = view.c_evidence(shot_path(f"{tc}_public_en"))
    assert held, f"EN card heading never read {en!r}: {row and row['card']}; {png}"
    if secs > PUBLIC_BUDGET_S:
        record_finding(tc, "publish-to-public budget exceeded (info)", seconds=round(secs, 1))
    design += style_mismatches(view.c_styles(sec["title"], CARD_TITLE)[0], "20px", "700", "#1D1D1B")
    view, row, _, held = public_row(anon_pages, sec["title_ar"], _card(lambda c: _norm(c["heading"]) == ar), "ar")
    png_ar = view.c_evidence(shot_path(f"{tc}_public_ar"))
    assert held, f"AR card heading never read {ar!r}: {row and row['card']}; {png_ar}"
    style_ar = view.c_styles(sec["title_ar"], CARD_TITLE)[0]
    design += [f"AR {m}" for m in style_mismatches(style_ar, "20px", "700", "#1D1D1B")]
    assert rtl_aligned_right(style_ar), f"AR heading not right-aligned: {style_ar}"
    if design:
        record_finding(tc, "design token mismatch", details=design, screenshot=png)
    assert not design, f"design mismatches: {design}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140437
@pytest.mark.tc_140489
def test_140437_card_heading_rejects_empty(page, c_disposable, anon_pages):
    """140437 (dup 140489): Card Heading EN is mandatory — emptying it blocks Publish."""
    tc = "140437"
    drv, sec = _card_section(page, c_disposable, tc, S03_EYEBROW, S03_HEADING, pills=False)
    _, row, _, held = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["heading"]) == S03_HEADING))
    assert held, f"PRECONDITION: card heading never rendered: {row and row['card']}"
    flag = _mandatory_flag(drv, sec["entry"], "highlightCardHeading")
    marked = flag["required_attr"] or flag["aria_required"] or flag["label_star"]
    if not marked:
        record_finding(tc, "LOW: Card Heading EN is not marked mandatory on the form", flag=flag)
    result = edit(drv, sec["entry"], tc, "empty_heading", data={"highlightCardHeading": ""})
    now = stored(drv, sec["entry"]).get("highlightCardHeading", "")
    view, row, _, still = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["heading"]) == S03_HEADING),
                                     timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    _rejection(tc, result, "highlightCardHeading", "Card Heading", "an empty Card Heading EN", now, still,
               f"card {row and row['card']}", png)
    design = style_mismatches(view.c_styles(sec["title"], CARD_TITLE)[0], "18px", "700", "#1D1D1B")
    assert marked, f"step 2: Card Heading EN is not marked as mandatory: {flag}"
    assert not design, f"design mismatches: {design}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140438
@pytest.mark.tc_140490
def test_140438_card_heading_200_char_boundary(page, c_disposable, anon_pages):
    """140438 (dup 140490): 200 chars accepted and rendered in full in the 350px card; 201 never stored."""
    tc = "140438"
    v200 = "QCTEST-130701-CARDHEADING-200-" + "A" * 170
    v201 = v200 + "A"
    assert len(v200) == 200
    a200 = ar_text(200)
    drv, sec = _card_section(page, c_disposable, tc, S03_EYEBROW, S03_HEADING, pills=False)
    drv.open_entry_en(sec["entry"].code)
    counter = drv.counter_limit("highlightCardHeading")
    result = edit(drv, sec["entry"], tc, "200", data={"highlightCardHeading": v200, "highlightCardHeading_ar": a200})
    assert result["went_through"] and not result["evidence"].get("field_errors"), f"200 not accepted: {result}"
    assert result.get("success_message_shown"), f"no 'Saved and published.' message: {result.get('editbar')}"
    wait_published(drv, sec["entry"])
    assert stored(drv, sec["entry"])["highlightCardHeading"] == v200
    require_active(drv, sec["entry"])
    _, row, secs, held = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["heading"]) == v200))
    assert held, f"EN: the full 200-character heading never rendered: {row and row['card']}"
    limit = frontend_limit_check(anon_pages, tc, sec["title"], sec["title_ar"], CARD_TITLE, v200, a200,
                                 lambda r: bool(r["card"]))
    drv.open_entry_en(sec["entry"].code)
    drv.fill_en("highlightCardHeading", v201)
    kept = len(drv.text_value("highlightCardHeading"))
    result = edit(drv, sec["entry"], tc, "201", data={"highlightCardHeading": v201})
    after = stored(drv, sec["entry"])["highlightCardHeading"]
    record_finding(tc, "boundary observation (info)", counter=counter, typed_201_kept=kept, stored_after=len(after),
                   publish_went_through=result["went_through"], messages=result["messages"],
                   frontend={k: v["problems"] for k, v in limit.items()})
    if len(after) == 201:
        record_finding(tc, "LOW validation: Card Heading 200-character limit not enforced",
                       screenshot=result["screenshot"])
    assert len(after) != 201, f"PRODUCT: a 201-character Card Heading was stored; {result['screenshot']}"
    assert after == v200, f"after the 201 attempt the stored value is {len(after)} chars, not the 200 string"
    # Case expects the max-length value to fit its box on the public page (Fable review 2026-10-06; bug 148926).
    overflow = {k: v["problems"] for k, v in limit.items() if v["problems"]}
    assert not overflow, f"PRODUCT (LOW): max-length value overflows publicly: {overflow}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140439
@pytest.mark.tc_140491
def test_140439_card_heading_rejects_whitespace(page, c_disposable, anon_pages):
    """140439 (dup 140491): Card Heading EN of three spaces is blocked; no blank heading renders."""
    tc = "140439"
    drv, sec = _card_section(page, c_disposable, tc, S01_EYEBROW, S01_HEADING, pills=False)
    _, row, _, held = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["heading"]) == S01_HEADING))
    assert held, f"PRECONDITION: card heading never rendered: {row and row['card']}"
    result = edit(drv, sec["entry"], tc, "whitespace_heading", data={"highlightCardHeading": "   "})
    now = stored(drv, sec["entry"]).get("highlightCardHeading", "")
    view, row, _, still = public_row(anon_pages, sec["title"], _card(lambda c: _norm(c["heading"]) == S01_HEADING),
                                     timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    markup = view.c_markup(sec["title"]) or {}
    blank = [n for n in ((markup.get("card") or {}).get("heading_nodes") or []) if not n.strip()]
    _rejection(tc, result, "highlightCardHeading", "Card Heading", "a whitespace-only Card Heading EN", now, still,
               f"card {row and row['card']}, blank heading nodes {len(blank)}", png)
    assert not blank, f"a blank heading element is rendered; {png}"
