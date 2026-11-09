"""
cms/tests/visas_immigration/test_visas_items_control_panel.py — Control_Panel
cases for PBI 130701 "QC - Business Gateway - Visas & Immigration" (Azure plan
137724, suite 140362), Agent C: BG Checklist Items, BG Highlight Items and BG
Sub-topic Blocks on Object Authoring (`manage-bg-checklist-item`,
`manage-bg-highlight-item`, `manage-bg-sub-topic-block`), verified on the
public `/web/qatar-chamber/visas-immigration` page (EN + AR).
The Highlight Card Eyebrow / Heading cases live in
test_visas_items_card_control_panel.py.

How the cases are run (disclosed substitutions):
  - "Open the Visas & Immigration record and expand Section 0N" — there is no
    nested section editor: items are separate Objects joined by a plain-text
    sectionKey (bg_recon.md §2). The equivalent is the item Object's own
    manage page; records are located by their captured id / exact text.
  - "Section 01/02/03" — the REAL sections are never edited (user decision).
    Every case runs on Agent C's OWN QCTEST section on the same page key
    (pageKey visas-immigration, sectionKey qctest-130701-c-items-<stamp>,
    Display Order 700, highlight card eyebrow + heading set, no supporting
    image so the card renders). Case pre-conditions ("an item X is Active with
    text Y") are created by the test itself.
  - Display Order "1 / 4 / 6 / 9" in the cases -> 100 / 400 / 600 / 900
    (100-grid rule; same relative order).
  - ENTRY-column values must carry the QCTEST-130701-C- prefix (guarded delete
    namespace). Highlight Item Text and Block Heading literals therefore become
    "QCTEST-130701-C-<tc>-<stamp> <case literal without QCTEST-130701>"; the
    120-char boundary literals keep their exact length with the prefix
    "QCTEST-130701-C-HLITEM-120-" / "QCTEST-130701-C-BLKHEAD-120-".
  - "Liferay generic success toast" -> the Object Authoring edit-bar message
    "Saved and published." (the only success feedback this surface has).
  - Public checks: only after the list shows Published AND the re-opened record
    stores Active Status ticked; fresh logged-out context; the 5 s budget is
    measured from the first page open and reported, polling continues up to
    40 s to separate "slow" from "absent".
  - Rich-text limits (Checklist 300, Block Body 500) have no counter: the
    N / N+1 behaviour is tested as written, and the N value is also checked on
    the public page EN + AR at 1920 and 390 (bg_rules.md rule 6).

Every finding is appended to reports/evidence/130701_C/findings.jsonl.
"""

from __future__ import annotations

import pytest

from cms.pages.visas_immigration.bg_admin_page import (
    OPT_BLOCK_STYLE_CHECKLIST,
    OPT_BLOCK_STYLE_PARAGRAPH,
    SLUG_CHECKLIST,
    SLUG_HIGHLIGHT,
    SLUG_SUBTOPIC,
    bg_data,
)
from cms.tests.visas_immigration.c_items_support import (  # noqa: F401 — fixtures imported for pytest
    AUTH_FREE_PAGE,
    MAXLEN_RE,
    PUBLIC_BUDGET_S,
    REQUIRED_RE,
    CRegistry,
    anon_pages,
    ar_text,
    c_disposable,
    create,
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
    teardown_entries,
    wait_published,
)
from core.web.browser import new_context

pytestmark = [pytest.mark.control_panel, pytest.mark.invest, pytest.mark.pbi_130701,
              pytest.mark.functional_low, pytest.mark.xdist_group("visas_130701_c")]

CHECK_LABELS = ".qc-visas-article > .qc-visas-checks .qc-visas-check-label"
PILL_LABELS = ".qc-visas-card .qc-visas-pill-label"
BLOCK_HEADS = ".qc-visas-article > .qc-visas-block > .qc-visas-block-head"
BLOCK_PROSE = ".qc-visas-article > .qc-visas-block > .qc-visas-prose"
BLOCK_CHECK_LABELS = ".qc-visas-article > .qc-visas-block .qc-visas-check-label"


# ===========================================================================
# Shared own section (module scope): QCTEST-130701-C-ITEMS-<stamp> section
# ===========================================================================
@pytest.fixture(scope="module")
def c_items_section(browser):
    registry = CRegistry()
    ctx = new_context(browser, use_auth_state=False)
    try:
        driver = editor_session(ctx.new_page())
        info = create_section(driver, registry, "ITEMS",
                              highlightCardEyebrow="QCTEST-130701-C items card eyebrow",
                              highlightCardEyebrow_ar="عنوان تمهيدي للبطاقة",
                              highlightCardHeading="QCTEST-130701-C items card heading",
                              highlightCardHeading_ar="عنوان بطاقة العناصر")
    except BaseException:
        ctx.close()
        teardown_entries(browser, registry.entries, "module section (setup failed)")
        raise
    ctx.close()
    yield info
    teardown_entries(browser, registry.entries, "module section")


def _admin(page, slug):
    return driver_for(editor_session(page), slug)


def _norm(text: str) -> str:
    return " ".join((text or "").split())


def _design(tc: str, where: str, mismatches: list[str], bucket: list[str]) -> None:
    if mismatches:
        bucket.append(f"{where}: " + "; ".join(mismatches))


def _budget_note(tc: str, where: str, seconds: float) -> None:
    if seconds > PUBLIC_BUDGET_S:
        record_finding(tc, "publish-to-public budget exceeded (info)", where=where, seconds=round(seconds, 1),
                       budget=PUBLIC_BUDGET_S)


def _assert_created_cleanly(result: dict, what: str) -> None:
    assert result.get("went_through"), f"saving {what} did not go through: {result}"
    assert not result["evidence"].get("field_errors"), f"{what}: validation messages shown {result['evidence']}"
    assert result.get("success_message_shown"), (
        f"{what}: no 'Saved and published.' success message; edit bar {result.get('editbar')}")


def _rejection_outcome(tc: str, result: dict, field_key: str, field_label: str, what: str,
                       stored_now: str, public_ok: bool, public_desc: str, public_png: str) -> None:
    """Shared verdict for 'empty / whitespace must be rejected' cases."""
    if result["went_through"]:
        record_finding(tc, f"LOW validation: {what} accepted on Publish", field=field_key,
                       stored_after=repr(stored_now), public=public_desc, cms_screenshot=result["screenshot"],
                       public_screenshot=public_png, messages=result["messages"])
        pytest.fail(f"PRODUCT: Publish with {what} was NOT blocked — saved ('Saved and published.' "
                    f"shown: {result.get('success_message_shown')}), stored value now {stored_now!r}; "
                    f"public: {public_desc}; screenshots {result['screenshot']} / {public_png}")
    assert result["refused"], f"Publish with {what} was neither refused with validation evidence nor saved: {result}"
    points = refusal_points_at(result, field_key) or field_label.lower() in result["messages"].lower()
    assert points, f"Publish was refused, but the evidence does not point at {field_label}: {result['evidence']}"
    if not REQUIRED_RE.search(result["messages"]):
        record_finding(tc, "LOW wording: refusal message does not say the field is required",
                       field=field_label, shown=result["messages"], screenshot=result["screenshot"])
    assert public_ok, f"after the refused publish the public page no longer shows {public_desc}; {public_png}"


# ===========================================================================
# Checklist Items
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.bilingual
@pytest.mark.tc_140428
@pytest.mark.tc_140480
def test_140428_checklist_item_valid_bilingual_renders(page, c_items_section, c_disposable, anon_pages):
    """140428 (dup 140480): a 4th checklist item with a valid EN + AR Item Text is
    accepted, published and rendered 4th (EN 16/400/#6C6C6B in 730px; AR right-aligned)."""
    tc, sec = "140428", c_items_section
    en = "QCTEST-130701 check visa and entry requirements before starting your journey."
    ar = "تحقق من متطلبات التأشيرة والدخول قبل بدء رحلتك."
    chk = _admin(page, SLUG_CHECKLIST)
    # Arrange — the case pre-condition: three active items already in the section.
    for i in (1, 2, 3):
        create_ok(chk, c_disposable, bg_data(SLUG_CHECKLIST, sec["key"], itemText=f"QCTEST-130701-C baseline check {i}",
                                             itemText_ar=f"بند أساسي {i}", displayOrder=i * 100), tc, f"baseline{i}")
    chk.open_list_all()
    listed = [r for r in chk.list_rows() if r["title"] == sec["key"]]
    assert len(listed) == 3, f"step 1: the section's checklist lists {len(listed)} items, expected 3: {listed}"
    # Act
    entry, result = create(chk, c_disposable, bg_data(SLUG_CHECKLIST, sec["key"], itemText=en, itemText_ar=ar,
                                                       displayOrder=400), tc, "new_item")
    _assert_created_cleanly(result, "the new checklist item")
    assert entry is not None, "the new checklist item is not identifiable as exactly one NEW record"
    wait_published(chk, entry)
    require_active(chk, entry)
    # Assert — public EN / AR
    design: list[str] = []
    view, row, secs, held = public_row(anon_pages, sec["title"], lambda r: len(r["checklist"]) >= 4)
    png = view.c_evidence(shot_path(f"{tc}_public_en"))
    assert held, f"EN: the section never rendered 4 checklist items; got {row and row['checklist']}; {png}"
    _budget_note(tc, "EN", secs)
    assert len(row["checklist"]) == 4 and _norm(row["checklist"][3]) == _norm(en), (
        f"EN: 4th item reads {row['checklist']}, expected {en!r} 4th of 4; {png}")
    style = view.c_styles(sec["title"], CHECK_LABELS)[3]
    _design(tc, "EN item", style_mismatches(style, "16px", "400", "#6C6C6B", 730), design)
    view, row, secs, held = public_row(anon_pages, sec["title_ar"], lambda r: len(r["checklist"]) >= 4, "ar")
    png_ar = view.c_evidence(shot_path(f"{tc}_public_ar"))
    assert held and _norm(row["checklist"][3]) == _norm(ar), (
        f"AR: 4th item reads {row and row['checklist']}, expected {ar!r}; {png_ar}")
    style_ar = view.c_styles(sec["title_ar"], CHECK_LABELS)[3]
    assert rtl_aligned_right(style_ar), f"AR item is not right-aligned: {style_ar}"
    if design:
        record_finding(tc, "design token mismatch", details=design, screenshot=png)
    assert not design, f"design mismatches: {design}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140429
@pytest.mark.tc_140481
def test_140429_checklist_item_rejects_empty_text(page, c_items_section, c_disposable, anon_pages):
    """140429 (dup 140481): clearing a published item's Item Text EN and publishing is
    blocked with a required-field error; the public item keeps its text."""
    tc, sec = "140429", c_items_section
    original = "QCTEST-130701 placeholder checklist text"
    chk = _admin(page, SLUG_CHECKLIST)
    entry = create_ok(chk, c_disposable, bg_data(SLUG_CHECKLIST, sec["key"], itemText=original, displayOrder=100),
                      tc, "item")
    require_active(chk, entry)
    view, row, _, held = public_row(anon_pages, sec["title"], lambda r: original in map(_norm, r["checklist"]))
    assert held, f"PRECONDITION: the item never rendered publicly: {row}"
    # Act — located by its captured id + code (exact identity), Item Text EN emptied
    chk.open_entry_en(entry.code)
    assert _norm(chk.rich_text("itemText")) == original, "the captured record does not hold the case text"
    result = edit(chk, entry, tc, "empty_text", rich_raw={"itemText": ""})
    now = stored(chk, entry).get("itemText", "")
    view, row, _, still = public_row(anon_pages, sec["title"], lambda r: original in map(_norm, r["checklist"]),
                                     timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    _rejection_outcome(tc, result, "itemText", "Item Text", "an empty Item Text EN", now, still,
                       f"checklist {row and row['checklist']}", png)


@AUTH_FREE_PAGE
@pytest.mark.tc_140430
@pytest.mark.tc_140482
def test_140430_checklist_item_300_char_boundary(page, c_items_section, c_disposable, anon_pages):
    """140430 (dup 140482): 300 chars accepted and rendered in full; 301 never stored."""
    tc, sec = "140430", c_items_section
    v300 = "QCTEST-130701-CHECKLIST-300-" + "A" * 272
    v301 = v300 + "A"
    assert len(v300) == 300 and len(v301) == 301
    a300 = ar_text(300)
    chk = _admin(page, SLUG_CHECKLIST)
    # The case value first (EN 300 + an AR 300 for the rule-6 render check). When it is
    # refused, two diagnostic attempts locate the effective limit: EN 300 with a short
    # AR, then EN 293 (= 300 minus the 7 characters of the "<p></p>" wrapper the rich
    # editor stores). Only the first attempt decides the case.
    v293 = v300[:293]
    attempts = [("300_en_ar", v300, a300), ("300_en_only", v300, "بند"), ("293_en_only", v293, "بند")]
    entry, accepted, outcomes = None, None, {}
    for label, en_value, ar_value in attempts:
        entry, result = create(chk, c_disposable, bg_data(SLUG_CHECKLIST, sec["key"], itemText=en_value,
                                                          itemText_ar=ar_value, displayOrder=100), tc, label)
        outcomes[label] = {"went_through": result.get("went_through"), "messages": result.get("messages"),
                           "screenshot": result.get("screenshot"), "created": entry is not None}
        if result.get("went_through") and entry is not None:
            accepted = (label, en_value, ar_value)
            break
    first = outcomes["300_en_ar"]
    if not first["went_through"]:
        record_finding(tc, "LOW validation: a 300-character Checklist Item Text is REJECTED as over the limit",
                       attempts=outcomes, note="Item Text is rich text with no counter; the server answers 400 "
                       "with the message below although the visible text is exactly 300 characters")
    assert accepted is not None, f"no checklist value up to 293 characters was accepted: {outcomes}"
    label, v_ok, a_ok = accepted
    wait_published(chk, entry)
    data = stored(chk, entry)
    require_active(chk, entry)
    view, row, secs, held = public_row(anon_pages, sec["title"], lambda r: v_ok in map(_norm, r["checklist"]))
    png = view.c_evidence(shot_path(f"{tc}_public_en_{label}"))
    assert held, f"EN: the {len(v_ok)}-character item never rendered (rendered {row and row['checklist']}); {png}"
    _budget_note(tc, "EN", secs)
    limit = frontend_limit_check(anon_pages, tc, sec["title"], sec["title_ar"], CHECK_LABELS, v_ok,
                                 a_ok, lambda r: len(r["checklist"]) >= 1)
    assert first["went_through"], (
        f"PRODUCT: the exact 300-character boundary value was refused ({first['messages']!r}); accepted only "
        f"{label} ({len(v_ok)} chars, stored {len(data['itemText'])}); attempts {outcomes}; {first['screenshot']}")
    # 301
    chk.open_entry_en(entry.code)
    chk.type_rich("itemText", v301)
    typed = len(chk.rich_text("itemText"))
    result = edit(chk, entry, tc, "301", rich_raw={"itemText": v301})
    after = stored(chk, entry)["itemText"]
    if len(after) == 301:
        record_finding(tc, "LOW validation: Checklist Item Text 300-character limit not enforced",
                       typed_len=typed, stored_len=len(after), messages=result["messages"],
                       screenshot=result["screenshot"], frontend=limit)
    assert len(after) != 301, (
        f"PRODUCT: a 301-character Item Text was accepted and stored (field kept {typed} chars, Publish "
        f"went through: {result['went_through']}); screenshot {result['screenshot']}")
    assert len(after) == 300, f"after the 301 attempt the stored value is {len(after)} chars, expected the 300 string"
    if result["went_through"] is False and not MAXLEN_RE.search(result["messages"]):
        record_finding(tc, "LOW wording: refusal message does not name the maximum length",
                       shown=result["messages"], screenshot=result["screenshot"])


@AUTH_FREE_PAGE
@pytest.mark.tc_140431
@pytest.mark.tc_140483
def test_140431_checklist_item_rejects_whitespace(page, c_items_section, c_disposable, anon_pages):
    """140431 (dup 140483): Item Text EN of three spaces is blocked; no empty bullet renders."""
    tc, sec = "140431", c_items_section
    original = "QCTEST-130701 whitespace probe item"
    chk = _admin(page, SLUG_CHECKLIST)
    entry = create_ok(chk, c_disposable, bg_data(SLUG_CHECKLIST, sec["key"], itemText=original, displayOrder=100),
                      tc, "item")
    require_active(chk, entry)
    _, row, _, held = public_row(anon_pages, sec["title"], lambda r: original in map(_norm, r["checklist"]))
    assert held, f"PRECONDITION: the item never rendered publicly: {row}"
    result = edit(chk, entry, tc, "whitespace", rich_raw={"itemText": "   "})
    now = stored(chk, entry).get("itemText", "")
    view, row, _, still = public_row(anon_pages, sec["title"], lambda r: original in map(_norm, r["checklist"]),
                                     timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    markup = view.c_markup(sec["title"]) or {}
    empty_bullets = [c for c in markup.get("checklist_rows", []) if not c["text"]]
    _rejection_outcome(tc, result, "itemText", "Item Text", "a whitespace-only Item Text EN", now, still,
                       f"checklist {row and row['checklist']}, empty bullets {len(empty_bullets)}", png)
    assert not empty_bullets, f"an empty bullet is rendered: {empty_bullets}; {png}"


# ===========================================================================
# Highlight Items (card pills)
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.bilingual
@pytest.mark.tc_140440
@pytest.mark.tc_140492
def test_140440_highlight_item_valid_bilingual_renders_chip(page, c_items_section, c_disposable, anon_pages):
    """140440 (dup 140492): a 4th highlight item renders as the 4th chip (14/400/#343432
    on #EDEDED, 332px); AR chip right-aligned."""
    tc, sec = "140440", c_items_section
    en = name(tc, "Arrivals")
    ar = "الوصول"
    hl = _admin(page, SLUG_HIGHLIGHT)
    for i in (1, 2, 3):
        create_ok(hl, c_disposable, bg_data(SLUG_HIGHLIGHT, name(tc, f"baseline {i}"), sec["key"],
                                            itemText_ar=f"عنصر أساسي {i}", displayOrder=i * 100), tc, f"baseline{i}")
    entry, result = create(hl, c_disposable, bg_data(SLUG_HIGHLIGHT, en, sec["key"], itemText_ar=ar, displayOrder=400),
                           tc, "new_item")
    _assert_created_cleanly(result, "the new highlight item")
    assert entry is not None
    wait_published(hl, entry)
    require_active(hl, entry)
    design: list[str] = []
    view, row, secs, held = public_row(anon_pages, sec["title"], lambda r: bool(r["card"]) and len(r["card"]["pills"]) >= 4)
    png = view.c_evidence(shot_path(f"{tc}_public_en"))
    assert held, f"EN: the card never rendered 4 chips; card {row and row['card']}; {png}"
    _budget_note(tc, "EN", secs)
    pills = row["card"]["pills"]
    assert len(pills) == 4 and _norm(pills[3]) == en, f"EN chips {pills}, expected {en!r} 4th of 4; {png}"
    style = view.c_styles(sec["title"], PILL_LABELS)[3]
    _design(tc, "EN chip label", style_mismatches(style, "14px", "400", "#343432", 332), design)
    chain = view.c_chip_chain(sec["title"], en) or []
    fills = [c["background_color"] for c in chain] + [c["background_image"] for c in chain]
    if not any("237, 237, 237" in f for f in fills):
        design.append(f"chip fill: no #EDEDED (rgb(237, 237, 237)) on the label or its chip; seen {chain}")
    view, row, _, held = public_row(anon_pages, sec["title_ar"],
                                    lambda r: bool(r["card"]) and len(r["card"]["pills"]) >= 4, "ar")
    png_ar = view.c_evidence(shot_path(f"{tc}_public_ar"))
    assert held and _norm(row["card"]["pills"][3]) == ar, f"AR chips {row and row['card']}, expected {ar!r}; {png_ar}"
    assert rtl_aligned_right(view.c_styles(sec["title_ar"], PILL_LABELS)[3]), "AR chip is not right-aligned"
    if design:
        record_finding(tc, "design token mismatch", details=design, screenshot=png)
    assert not design, f"design mismatches: {design}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140441
@pytest.mark.tc_140493
def test_140441_highlight_item_rejects_empty_text(page, c_items_section, c_disposable, anon_pages):
    """140441 (dup 140493): clearing a published highlight Item Text EN is blocked."""
    tc, sec = "140441", c_items_section
    original = name(tc, "placeholder highlight")
    hl = _admin(page, SLUG_HIGHLIGHT)
    entry = create_ok(hl, c_disposable, bg_data(SLUG_HIGHLIGHT, original, sec["key"], displayOrder=100), tc, "item")
    require_active(hl, entry)
    _, row, _, held = public_row(anon_pages, sec["title"], lambda r: bool(r["card"]) and original in r["card"]["pills"])
    assert held, f"PRECONDITION: the chip never rendered publicly: {row and row['card']}"
    result = edit(hl, entry, tc, "empty_text", data={"itemText": ""})
    now = stored(hl, entry).get("itemText", "")
    view, row, _, still = public_row(anon_pages, sec["title"],
                                     lambda r: bool(r["card"]) and original in r["card"]["pills"], timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    _rejection_outcome(tc, result, "itemText", "Item Text", "an empty Item Text EN", now, still,
                       f"chips {row and row['card'] and row['card']['pills']}", png)


@AUTH_FREE_PAGE
@pytest.mark.tc_140442
@pytest.mark.tc_140494
def test_140442_highlight_item_120_char_boundary(page, c_items_section, c_disposable, anon_pages):
    """140442 (dup 140494): 120 chars accepted and rendered in full in the chip; 121 never stored."""
    tc, sec = "140442", c_items_section
    head = "QCTEST-130701-C-HLITEM-120-"
    v120 = head + "A" * (120 - len(head))
    v121 = v120 + "A"
    a120 = ar_text(120)
    hl = _admin(page, SLUG_HIGHLIGHT)
    entry, result = create(hl, c_disposable, bg_data(SLUG_HIGHLIGHT, v120, sec["key"], itemText_ar=a120,
                                                     displayOrder=100), tc, "120")
    _assert_created_cleanly(result, "the 120-character Item Text")
    assert entry is not None
    wait_published(hl, entry)
    data = stored(hl, entry)
    counter = hl.counter_limit("itemText")
    assert data["itemText"] == v120, f"stored EN Item Text is {len(data['itemText'])} chars, expected the 120 string"
    require_active(hl, entry)
    view, row, secs, held = public_row(anon_pages, sec["title"], lambda r: bool(r["card"]) and v120 in r["card"]["pills"])
    assert held, f"EN: the full 120-character chip never rendered: {row and row['card']}"
    _budget_note(tc, "EN", secs)
    limit = frontend_limit_check(anon_pages, tc, sec["title"], sec["title_ar"], PILL_LABELS, v120, a120,
                                 lambda r: bool(r["card"]) and len(r["card"]["pills"]) >= 1)
    hl.open_entry_en(entry.code)
    hl.fill_en("itemText", v121)
    kept = len(hl.text_value("itemText"))
    result = edit(hl, entry, tc, "121", data={"itemText": v121})
    after = stored(hl, entry)["itemText"]
    record_finding(tc, "boundary observation (info)", counter=counter, typed_121_kept=kept, stored_after=len(after),
                   publish_went_through=result["went_through"], messages=result["messages"],
                   frontend={k: v["problems"] for k, v in limit.items()})
    if len(after) == 121:
        record_finding(tc, "LOW validation: Highlight Item Text 120-character limit not enforced",
                       stored_len=121, screenshot=result["screenshot"])
    assert len(after) != 121, f"PRODUCT: a 121-character Item Text was stored; {result['screenshot']}"
    assert after == v120, f"after the 121 attempt the stored value is {len(after)} chars, not the 120 string"
    # Case expects the max-length value to fit its box on the public page (Fable review 2026-10-06; bug 148926).
    overflow = {k: v["problems"] for k, v in limit.items() if v["problems"]}
    assert not overflow, f"PRODUCT (LOW): max-length value overflows publicly: {overflow}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140443
@pytest.mark.tc_140495
def test_140443_highlight_item_rejects_whitespace(page, c_items_section, c_disposable, anon_pages):
    """140443 (dup 140495): Item Text EN of three spaces is blocked; no empty chip renders."""
    tc, sec = "140443", c_items_section
    original = name(tc, "whitespace highlight")
    hl = _admin(page, SLUG_HIGHLIGHT)
    entry = create_ok(hl, c_disposable, bg_data(SLUG_HIGHLIGHT, original, sec["key"], displayOrder=100), tc, "item")
    require_active(hl, entry)
    _, row, _, held = public_row(anon_pages, sec["title"], lambda r: bool(r["card"]) and original in r["card"]["pills"])
    assert held, f"PRECONDITION: the chip never rendered publicly: {row and row['card']}"
    result = edit(hl, entry, tc, "whitespace", data={"itemText": "   "})
    now = stored(hl, entry).get("itemText", "")
    view, row, _, still = public_row(anon_pages, sec["title"],
                                     lambda r: bool(r["card"]) and original in r["card"]["pills"], timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    markup = view.c_markup(sec["title"]) or {}
    empty_chips = [p for p in ((markup.get("card") or {}).get("pill_nodes") or []) if not p.strip()]
    _rejection_outcome(tc, result, "itemText", "Item Text", "a whitespace-only Item Text EN", now, still,
                       f"chips {row and row['card'] and row['card']['pills']}, empty chips {len(empty_chips)}", png)
    assert not empty_chips, f"an empty chip is rendered; {png}"


# ===========================================================================
# Sub-topic Blocks
# ===========================================================================
def _block(heading: str, key: str, **overrides) -> dict:
    return bg_data(SLUG_SUBTOPIC, heading, key, **overrides)


def _block_of(view, title: str, heading: str) -> dict | None:
    markup = view.c_markup(title) or {}
    for block in markup.get("blocks", []):
        if _norm(block["heading"]) == _norm(heading):
            return block
    return None


def _has_block(heading: str):
    return lambda r: any(_norm(b["heading"]) == _norm(heading) for b in r["blocks"])


@AUTH_FREE_PAGE
@pytest.mark.bilingual
@pytest.mark.tc_140444
@pytest.mark.tc_140496
def test_140444_block_heading_valid_bilingual_renders(page, c_items_section, c_disposable, anon_pages):
    """140444 (dup 140496): a valid EN + AR Block Heading renders (18/700/#1D1D1B, 760px; AR right)."""
    tc, sec = "140444", c_items_section
    en = name(tc, "Using your e-gate card")
    ar = "استخدام بطاقة البوابة الإلكترونية"
    blk = _admin(page, SLUG_SUBTOPIC)
    entry, result = create(blk, c_disposable, _block(en, sec["key"], blockHeading_ar=ar, displayOrder=100,
                                                     blockStyle=OPT_BLOCK_STYLE_PARAGRAPH), tc, "block")
    _assert_created_cleanly(result, "the sub-topic block")
    assert entry is not None
    wait_published(blk, entry)
    require_active(blk, entry)
    design: list[str] = []
    view, row, secs, held = public_row(anon_pages, sec["title"], _has_block(en))
    png = view.c_evidence(shot_path(f"{tc}_public_en"))
    assert held, f"EN: block heading {en!r} never rendered; blocks {row and row['blocks']}; {png}"
    _budget_note(tc, "EN", secs)
    style = [s for s in view.c_styles(sec["title"], BLOCK_HEADS) if _norm(s["text"]) == en][0]
    _design(tc, "EN block heading", style_mismatches(style, "18px", "700", "#1D1D1B", 760), design)
    view, row, _, held = public_row(anon_pages, sec["title_ar"], _has_block(ar), "ar")
    png_ar = view.c_evidence(shot_path(f"{tc}_public_ar"))
    assert held, f"AR: block heading {ar!r} never rendered; {row and row['blocks']}; {png_ar}"
    style_ar = [s for s in view.c_styles(sec["title_ar"], BLOCK_HEADS) if _norm(s["text"]) == ar][0]
    _design(tc, "AR block heading", style_mismatches(style_ar, "18px", "700", "#1D1D1B"), design)
    assert rtl_aligned_right(style_ar), f"AR heading is not right-aligned: {style_ar}"
    if design:
        record_finding(tc, "design token mismatch", details=design, screenshot=png)
    assert not design, f"design mismatches: {design}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140445
@pytest.mark.tc_140497
def test_140445_block_heading_rejects_empty(page, c_items_section, c_disposable, anon_pages):
    """140445 (dup 140497): clearing Block Heading EN of a published block is blocked."""
    tc, sec = "140445", c_items_section
    original = name(tc, "Exit permits")
    blk = _admin(page, SLUG_SUBTOPIC)
    entry = create_ok(blk, c_disposable, _block(original, sec["key"], displayOrder=100), tc, "block")
    require_active(blk, entry)
    _, row, _, held = public_row(anon_pages, sec["title"], _has_block(original))
    assert held, f"PRECONDITION: block never rendered publicly: {row and row['blocks']}"
    result = edit(blk, entry, tc, "empty_heading", data={"blockHeading": ""})
    now = stored(blk, entry).get("blockHeading", "")
    view, row, _, still = public_row(anon_pages, sec["title"], _has_block(original), timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    _rejection_outcome(tc, result, "blockHeading", "Block Heading", "an empty Block Heading EN", now, still,
                       f"block headings {row and [b['heading'] for b in row['blocks']]}", png)


@AUTH_FREE_PAGE
@pytest.mark.tc_140446
@pytest.mark.tc_140498
def test_140446_block_heading_120_char_boundary(page, c_items_section, c_disposable, anon_pages):
    """140446 (dup 140498): 120 chars accepted and rendered in full (760px box); 121 never stored."""
    tc, sec = "140446", c_items_section
    head = "QCTEST-130701-C-BLKHEAD-120-"
    v120 = head + "A" * (120 - len(head))
    v121 = v120 + "A"
    a120 = ar_text(120)
    blk = _admin(page, SLUG_SUBTOPIC)
    entry, result = create(blk, c_disposable, _block(v120, sec["key"], blockHeading_ar=a120, displayOrder=100),
                           tc, "120")
    _assert_created_cleanly(result, "the 120-character Block Heading")
    assert entry is not None
    wait_published(blk, entry)
    data = stored(blk, entry)
    counter = blk.counter_limit("blockHeading")
    assert data["blockHeading"] == v120, f"stored Block Heading is {len(data['blockHeading'])} chars"
    require_active(blk, entry)
    _, row, secs, held = public_row(anon_pages, sec["title"], _has_block(v120))
    assert held, f"EN: the full 120-character heading never rendered: {row and row['blocks']}"
    _budget_note(tc, "EN", secs)
    limit = frontend_limit_check(anon_pages, tc, sec["title"], sec["title_ar"], BLOCK_HEADS, v120, a120,
                                 lambda r: len(r["blocks"]) >= 1)
    blk.open_entry_en(entry.code)
    blk.fill_en("blockHeading", v121)
    kept = len(blk.text_value("blockHeading"))
    result = edit(blk, entry, tc, "121", data={"blockHeading": v121})
    after = stored(blk, entry)["blockHeading"]
    record_finding(tc, "boundary observation (info)", counter=counter, typed_121_kept=kept, stored_after=len(after),
                   publish_went_through=result["went_through"], messages=result["messages"],
                   frontend={k: v["problems"] for k, v in limit.items()})
    if len(after) == 121:
        record_finding(tc, "LOW validation: Block Heading 120-character limit not enforced",
                       screenshot=result["screenshot"])
    assert len(after) != 121, f"PRODUCT: a 121-character Block Heading was stored; {result['screenshot']}"
    assert after == v120, f"after the 121 attempt the stored value is {len(after)} chars, not the 120 string"
    # Case expects the max-length value to fit its box on the public page (Fable review 2026-10-06; bug 148926).
    overflow = {k: v["problems"] for k, v in limit.items() if v["problems"]}
    assert not overflow, f"PRODUCT (LOW): max-length value overflows publicly: {overflow}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140447
@pytest.mark.tc_140499
def test_140447_block_heading_rejects_whitespace(page, c_items_section, c_disposable, anon_pages):
    """140447 (dup 140499): Block Heading EN of three spaces is blocked; no blank heading renders."""
    tc, sec = "140447", c_items_section
    original = name(tc, "Paying your visa fee")
    blk = _admin(page, SLUG_SUBTOPIC)
    entry = create_ok(blk, c_disposable, _block(original, sec["key"], displayOrder=100), tc, "block")
    require_active(blk, entry)
    _, row, _, held = public_row(anon_pages, sec["title"], _has_block(original))
    assert held, f"PRECONDITION: block never rendered publicly: {row and row['blocks']}"
    result = edit(blk, entry, tc, "whitespace", data={"blockHeading": "   "})
    now = stored(blk, entry).get("blockHeading", "")
    view, row, _, still = public_row(anon_pages, sec["title"], _has_block(original), timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    markup = view.c_markup(sec["title"]) or {}
    blank = [b for b in markup.get("blocks", []) if b["heading_raw"] is not None and not b["heading"]]
    _rejection_outcome(tc, result, "blockHeading", "Block Heading", "a whitespace-only Block Heading EN", now,
                       still, f"block headings {row and [b['heading'] for b in row['blocks']]}, blank {len(blank)}",
                       png)
    assert not blank, f"a blank heading element is rendered; {png}"


@AUTH_FREE_PAGE
@pytest.mark.bilingual
@pytest.mark.tc_140448
@pytest.mark.tc_140500
def test_140448_block_body_valid_bilingual_renders(page, c_items_section, c_disposable, anon_pages):
    """140448 (dup 140500): a valid EN + AR Block Body renders (16/400/#6C6C6B, 760px; AR right)."""
    tc, sec = "140448", c_items_section
    heading = name(tc, "e-gate body probe")
    en = "QCTEST-130701 if you hold a valid e-gate card, proceed to the e-gate area near passport control."
    ar = "إذا كنت تحمل بطاقة بوابة إلكترونية صالحة، توجه إلى منطقة البوابات الإلكترونية بالقرب من مراقبة الجوازات."
    blk = _admin(page, SLUG_SUBTOPIC)
    entry = create_ok(blk, c_disposable, _block(heading, sec["key"], displayOrder=100), tc, "block")
    # Act — enter the case's EN / AR body on the published block and publish
    result = edit(blk, entry, tc, "body", rich_raw={"blockBody": en, "blockBody_ar": ar})
    _assert_created_cleanly(result, "the Block Body EN/AR")
    wait_published(blk, entry)
    require_active(blk, entry)
    design: list[str] = []
    view, row, secs, held = public_row(anon_pages, sec["title"],
                                       lambda r: any(_norm(b["prose"]) == _norm(en) for b in r["blocks"]))
    png = view.c_evidence(shot_path(f"{tc}_public_en"))
    assert held, f"EN: block body never rendered {en!r}; blocks {row and row['blocks']}; {png}"
    _budget_note(tc, "EN", secs)
    style = [s for s in view.c_styles(sec["title"], BLOCK_PROSE) if _norm(s["text"]) == _norm(en)][0]
    _design(tc, "EN block body", style_mismatches(style, "16px", "400", "#6C6C6B", 760), design)
    view, row, _, held = public_row(anon_pages, sec["title_ar"],
                                    lambda r: any(_norm(b["prose"]) == _norm(ar) for b in r["blocks"]), "ar")
    png_ar = view.c_evidence(shot_path(f"{tc}_public_ar"))
    assert held, f"AR: block body never rendered {ar!r}; {row and row['blocks']}; {png_ar}"
    style_ar = [s for s in view.c_styles(sec["title_ar"], BLOCK_PROSE) if _norm(s["text"]) == _norm(ar)][0]
    assert rtl_aligned_right(style_ar), f"AR body is not right-aligned: {style_ar}"
    if design:
        record_finding(tc, "design token mismatch", details=design, screenshot=png)
    assert not design, f"design mismatches: {design}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140449
@pytest.mark.tc_140501
def test_140449_block_body_rejects_empty(page, c_items_section, c_disposable, anon_pages):
    """140449 (dup 140501): clearing all Block Body EN content of a published block is blocked."""
    tc, sec = "140449", c_items_section
    heading = name(tc, "BLK-PRIORITY")
    body = "QCTEST-130701 priority processing body."
    blk = _admin(page, SLUG_SUBTOPIC)
    entry = create_ok(blk, c_disposable, _block(heading, sec["key"], blockBody=body, displayOrder=100), tc, "block")
    require_active(blk, entry)
    has_body = lambda r: any(_norm(b["heading"]) == heading and _norm(b["prose"]) == body for b in r["blocks"])  # noqa: E731
    _, row, _, held = public_row(anon_pages, sec["title"], has_body)
    assert held, f"PRECONDITION: block body never rendered publicly: {row and row['blocks']}"
    result = edit(blk, entry, tc, "empty_body", rich_raw={"blockBody": ""})
    now = stored(blk, entry).get("blockBody", "")
    view, row, _, still = public_row(anon_pages, sec["title"], has_body, timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    _rejection_outcome(tc, result, "blockBody", "Block Body", "an empty Block Body EN", now, still,
                       f"block {_block_of(view, sec['title'], heading)}", png)


@AUTH_FREE_PAGE
@pytest.mark.tc_140450
@pytest.mark.tc_140502
def test_140450_block_body_500_char_boundary(page, c_items_section, c_disposable, anon_pages):
    """140450 (dup 140502): 500 chars accepted and rendered in full (760px box); 501 never stored."""
    tc, sec = "140450", c_items_section
    heading = name(tc, "body 500 probe")
    v500 = "QCTEST-130701-BLKBODY-500-" + "A" * 474
    v501 = v500 + "A"
    assert len(v500) == 500
    a500 = ar_text(500)
    blk = _admin(page, SLUG_SUBTOPIC)
    entry, result = create(blk, c_disposable, _block(heading, sec["key"], blockBody=v500, blockBody_ar=a500,
                                                     displayOrder=100), tc, "500")
    _assert_created_cleanly(result, "the 500-character Block Body")
    assert entry is not None
    wait_published(blk, entry)
    data = stored(blk, entry)
    assert len(data["blockBody"]) == 500, f"stored Block Body is {len(data['blockBody'])} chars, expected 500"
    require_active(blk, entry)
    _, row, secs, held = public_row(anon_pages, sec["title"],
                                    lambda r: any(_norm(b["prose"]) == v500 for b in r["blocks"]))
    assert held, f"EN: the full 500-character body never rendered: {row and row['blocks']}"
    _budget_note(tc, "EN", secs)
    limit = frontend_limit_check(anon_pages, tc, sec["title"], sec["title_ar"], BLOCK_PROSE, v500, a500,
                                 lambda r: len(r["blocks"]) >= 1)
    blk.open_entry_en(entry.code)
    blk.type_rich("blockBody", v501)
    typed = len(blk.rich_text("blockBody"))
    result = edit(blk, entry, tc, "501", rich_raw={"blockBody": v501})
    after = stored(blk, entry)["blockBody"]
    if len(after) == 501:
        record_finding(tc, "LOW validation: Block Body 500-character limit not enforced", typed_len=typed,
                       stored_len=501, messages=result["messages"], screenshot=result["screenshot"],
                       frontend={k: v["problems"] for k, v in limit.items()})
    assert len(after) != 501, (
        f"PRODUCT: a 501-character Block Body was accepted and stored (editor kept {typed} chars, Publish went "
        f"through: {result['went_through']}); screenshot {result['screenshot']}")
    assert len(after) == 500, f"after the 501 attempt the stored value is {len(after)} chars, expected 500"


@AUTH_FREE_PAGE
@pytest.mark.tc_140451
@pytest.mark.tc_140503
def test_140451_block_body_rejects_whitespace(page, c_items_section, c_disposable, anon_pages):
    """140451 (dup 140503): Block Body EN of three spaces is blocked; no empty paragraph is added."""
    tc, sec = "140451", c_items_section
    heading = name(tc, "BLK-SOLVE")
    body = "QCTEST-130701 problem solving body."
    blk = _admin(page, SLUG_SUBTOPIC)
    entry = create_ok(blk, c_disposable, _block(heading, sec["key"], blockBody=body, displayOrder=100), tc, "block")
    require_active(blk, entry)
    has_body = lambda r: any(_norm(b["heading"]) == heading and _norm(b["prose"]) == body for b in r["blocks"])  # noqa: E731
    _, row, _, held = public_row(anon_pages, sec["title"], has_body)
    assert held, f"PRECONDITION: block body never rendered publicly: {row and row['blocks']}"
    result = edit(blk, entry, tc, "whitespace_body", rich_raw={"blockBody": "   "})
    now = stored(blk, entry).get("blockBody", "")
    view, row, _, still = public_row(anon_pages, sec["title"], has_body, timeout=15)
    png = view.c_evidence(shot_path(f"{tc}_public_after"))
    block = _block_of(view, sec["title"], heading) or {}
    empty_paras = [p for p in block.get("prose", []) if not p["text"]]
    _rejection_outcome(tc, result, "blockBody", "Block Body", "a whitespace-only Block Body EN", now, still,
                       f"block {block}", png)
    assert not empty_paras, f"an empty paragraph block is rendered: {block}; {png}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140452
@pytest.mark.tc_140504
def test_140452_block_style_paragraph_renders_prose(page, c_items_section, c_disposable, anon_pages):
    """140452 (dup 140504): Block Style offers exactly Paragraph / Checklist (no free text);
    Paragraph renders the body as prose (16/400/#6C6C6B, 760px), no list, no bullets."""
    tc, sec = "140452", c_items_section
    heading = name(tc, "style probe")
    body = "QCTEST-130701 first sentence. QCTEST-130701 second sentence."
    blk = _admin(page, SLUG_SUBTOPIC)
    entry = create_ok(blk, c_disposable, _block(heading, sec["key"], blockBody=body, displayOrder=900,
                                                blockStyle=OPT_BLOCK_STYLE_CHECKLIST), tc, "block")
    # Step 2 — the dropdown's options
    blk.open_entry_en(entry.code)
    options = blk.picklist_options("blockStyle")
    labels = [o for o in options["labels"] if o.strip()]
    assert labels == [OPT_BLOCK_STYLE_PARAGRAPH, OPT_BLOCK_STYLE_CHECKLIST], f"Block Style offers {options}"
    assert not options["free_text_accepted"], f"Block Style accepts free text: {options}"
    # Step 3-4 — set Paragraph and publish
    result = edit(blk, entry, tc, "paragraph", data={"blockStyle": OPT_BLOCK_STYLE_PARAGRAPH})
    _assert_created_cleanly(result, "Block Style Paragraph")
    wait_published(blk, entry)
    assert stored(blk, entry)["blockStyle"] == OPT_BLOCK_STYLE_PARAGRAPH
    require_active(blk, entry)
    view, row, secs, held = public_row(
        anon_pages, sec["title"],
        lambda r: any(_norm(b["heading"]) == heading and b["style"] == "paragraph" for b in r["blocks"]))
    png = view.c_evidence(shot_path(f"{tc}_public_en"))
    assert held, f"the block never rendered as a paragraph; {row and row['blocks']}; {png}"
    _budget_note(tc, "EN", secs)
    block = _block_of(view, sec["title"], heading)
    assert block["ul"] == 0 and block["li"] == 0, f"paragraph block contains a list: {block['html']}"
    assert not block["check_rows"] and block["check_disc"] == 0, f"paragraph block shows bullet/tick markers: {block}"
    assert [_norm(p["text"]) for p in block["prose"]] == [body], f"paragraph text {block['prose']}"
    style = [s for s in view.c_styles(sec["title"], BLOCK_PROSE) if _norm(s["text"]) == body][0]
    design = style_mismatches(style, "16px", "400", "#6C6C6B", 760)
    if design:
        record_finding(tc, "design token mismatch", details=design, screenshot=png)
    assert not design, f"design mismatches: {design}"


@AUTH_FREE_PAGE
@pytest.mark.tc_140453
@pytest.mark.tc_140505
def test_140453_block_style_checklist_renders_list(page, c_items_section, c_disposable, anon_pages):
    """140453 (dup 140505): switching Paragraph -> Checklist renders two list items
    (16/400/#6C6C6B, 730px, bullet marker); the paragraph presentation is gone."""
    tc, sec = "140453", c_items_section
    heading = name(tc, "BLK-STYLE")
    lines = ["QCTEST-130701 first check", "QCTEST-130701 second check"]
    blk = _admin(page, SLUG_SUBTOPIC)
    entry = create_ok(blk, c_disposable, _block(heading, sec["key"], blockBody="\n".join(lines), displayOrder=900,
                                                blockStyle=OPT_BLOCK_STYLE_PARAGRAPH), tc, "block")
    require_active(blk, entry)
    _, row, _, held = public_row(
        anon_pages, sec["title"],
        lambda r: any(_norm(b["heading"]) == heading and b["style"] == "paragraph" for b in r["blocks"]))
    assert held, f"PRECONDITION: the block never rendered as Paragraph: {row and row['blocks']}"
    result = edit(blk, entry, tc, "checklist", data={"blockStyle": OPT_BLOCK_STYLE_CHECKLIST})
    _assert_created_cleanly(result, "Block Style Checklist")
    wait_published(blk, entry)
    assert stored(blk, entry)["blockStyle"] == OPT_BLOCK_STYLE_CHECKLIST
    view, row, secs, held = public_row(
        anon_pages, sec["title"],
        lambda r: any(_norm(b["heading"]) == heading and b["style"] == "checklist" for b in r["blocks"]))
    png = view.c_evidence(shot_path(f"{tc}_public_en"))
    assert held, f"the block never rendered as a checklist; {row and row['blocks']}; {png}"
    _budget_note(tc, "EN", secs)
    block = _block_of(view, sec["title"], heading)
    assert [_norm(t) for t in block["check_rows"]] == lines, f"checklist rows {block['check_rows']}, expected {lines}"
    assert block["check_disc"] == 2, f"expected a bullet/tick marker per row, found {block['check_disc']}"
    assert not block["prose"], f"the paragraph presentation is still rendered: {block['prose']}"
    styles = [s for s in view.c_styles(sec["title"], BLOCK_CHECK_LABELS) if _norm(s["text"]) in lines]
    design = [m for s in styles for m in style_mismatches(s, "16px", "400", "#6C6C6B", 730)]
    if block["ul"] != 1 or block["li"] != 2:
        record_finding(tc, "LOW markup: checklist block is not an unordered list",
                       expected="<ul> with exactly two <li>", actual=f"{block['ul']} <ul>, {block['li']} <li>; "
                       "rows are <div class=qc-visas-check> with a tick disc", html=block["html"][:600], screenshot=png)
    if design:
        record_finding(tc, "design token mismatch", details=design, screenshot=png)
    assert not design, f"design mismatches: {design}"
    assert block["ul"] == 1 and block["li"] == 2, (
        f"PRODUCT: the checklist renders {len(block['check_rows'])} tick rows but the markup has "
        f"{block['ul']} <ul> / {block['li']} <li> (case expects an unordered list with exactly two list items); {png}")


@AUTH_FREE_PAGE
@pytest.mark.tc_140454
@pytest.mark.tc_140506
def test_140454_block_without_style_saves_and_publishes(page, c_items_section, c_disposable, anon_pages):
    """140454 (dup 140506): Block Style left empty is not mandatory: Save, then Publish,
    and the block renders in the default (prose) presentation."""
    tc, sec = "140454", c_items_section
    heading = name(tc, "no style probe")
    body = "QCTEST-130701 no style body text."
    blk = _admin(page, SLUG_SUBTOPIC)
    data = _block(heading, sec["key"], blockBody=body, displayOrder=600)
    data.pop("blockStyle")

    def _confirm_empty(driver):
        assert driver.clear_picklist_is_empty("blockStyle"), "Block Style is not empty on the new form"
        flag = driver.field_marked_required("blockStyle")
        assert not (flag["required_attr"] or flag["aria_required"] or flag["label_star"]), (
            f"Block Style is flagged mandatory: {flag}")

    entry, result = create(blk, c_disposable, data, tc, "save", publish=False, before_save=_confirm_empty)
    assert result.get("went_through"), f"Save as Draft with an empty Block Style did not go through: {result}"
    assert result.get("success_message_shown"), f"no 'Draft saved.' message: {result.get('editbar')}"
    assert not result["evidence"].get("field_errors"), f"validation shown: {result['evidence']}"
    assert entry is not None
    assert stored(blk, entry)["blockStyle"] == "", "the saved block does not have an empty Block Style"
    result = edit(blk, entry, tc, "publish")
    _assert_created_cleanly(result, "publishing the no-style block")
    wait_published(blk, entry)
    require_active(blk, entry)
    view, row, secs, held = public_row(anon_pages, sec["title"], _has_block(heading))
    png = view.c_evidence(shot_path(f"{tc}_public_en"))
    assert held, f"the block never rendered; {row and row['blocks']}; {png}"
    _budget_note(tc, "EN", secs)
    block = _block_of(view, sec["title"], heading)
    assert [_norm(p["text"]) for p in block["prose"]] == [body], f"default presentation is not prose: {block}"
    design = []
    head_style = [s for s in view.c_styles(sec["title"], BLOCK_HEADS) if _norm(s["text"]) == heading][0]
    _design(tc, "heading", style_mismatches(head_style, "18px", "700", "#1D1D1B"), design)
    body_style = [s for s in view.c_styles(sec["title"], BLOCK_PROSE) if _norm(s["text"]) == body][0]
    _design(tc, "body", style_mismatches(body_style, "16px", "400", "#6C6C6B"), design)
    if design:
        record_finding(tc, "design token mismatch", details=design, screenshot=png)
    assert not design, f"design mismatches: {design}"
