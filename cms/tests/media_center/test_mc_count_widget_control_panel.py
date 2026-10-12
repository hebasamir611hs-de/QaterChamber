"""
cms/tests/media_center/test_mc_count_widget_control_panel.py — Control_Panel
cases for PBI 130709 Media Center Home Page (suite 140368), COUNT agent:
`manage-media-center-count-widget` (MediaCenterCountWidget) verified on the
public summary counts strip of /web/qatar-chamber/media-center.

Notes applied to every case (see count_support.py for the data rules):
  - The cases' "Submit for Review" is the Author label; the signed-in QC Site
    Content Editor's privileged submit button reads "Publish" (-> PUBLISHED).
  - "Main Menu -> Insights & Media -> Media Center" is opened by its URL; the
    live header shows "Media Center" as a top-level item.
  - Draft-save case (TC-200) runs as QC Site Content Author per the Phase-3
    rule (drafts show there); every other case as QC Site Content Editor.
  - The public counts strip is FIXED at the five real widgets by design, so a
    QCTEST widget never renders there. Each case's CMS steps run on its own
    disposable QCTEST-130709-CW-0n record; its PUBLIC steps are verified on the
    REAL Videos widget (QCDEMO-130709-COUNT-03, same content type as CW-01)
    inside a guarded window — lock, API snapshot, concurrency re-check before
    every edit and before restore, exact PUT restore, empty diff required
    (user approval 2026-10-12, rules 4b). Never unpublished, never deleted.
  - Soft checks: a step that fails is collected and the case keeps going, so
    one run records every step; the test fails at the end with all of them.
"""

from __future__ import annotations

import re

import pytest

from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED
from cms.pages.media_center.mc_count_widget_admin_page import (
    CONTENT_TYPES,
    K_ACTIVE,
    K_NAME,
    K_ORDER,
    K_TYPE,
    K_UNIT,
    MANAGE_PATH,
    MSG_ARABIC_REQUIRED,
    MSG_DRAFT_SAVED,
    SUBSCRIBER_PATH,
    is_current_time,
    parse_row_modified,
    real_widget_window,
)
from cms.tests.media_center.count_support import (  # noqa: F401 — fixtures imported for pytest
    AUTH_FREE_PAGE,
    ICON_1,
    ICON_2,
    REAL_VIDEOS,
    REQUIRED_RE,
    ROLE_AUTHOR,
    anon_view,
    card_index,
    create,
    create_cw01,
    cw_disposable,
    edit,
    public_absent,
    public_card,
    real_edit,
    record_finding,
    reflow_gaps,
    refusal_points_at,
    role_session,
    save,
    stored,
)

pytestmark = [pytest.mark.control_panel, pytest.mark.media, pytest.mark.pbi_130709,
              pytest.mark.xdist_group("mc_count_130709")]


def _norm(text) -> str:
    return " ".join(str(text or "").split())


def _ar(snapshot: dict, key: str) -> str:
    return (snapshot.get(f"{key}_i18n") or {}).get("ar_SA", "")


def _public_expect(fails: list, anon_view, tc: str, label: str, locale: str = "en", predicate=None,
                   what: str = "") -> dict:
    pub = public_card(anon_view, tc, label, locale, predicate)
    if not pub["held"]:
        fails.append(f"[{locale}] {what}: card {label!r} not shown as expected; strip {pub['state_cards']}; "
                     f"{pub['shot']}")
    return pub


def _saved_ok(fails: list, result: dict, what: str) -> None:
    if not result["went_through"]:
        fails.append(f"{what}: save did not go through: {result['messages']} {result['evidence']}")
    elif not result.get("success_message_shown"):
        fails.append(f"{what}: no 'Saved and published.' message: {result.get('editbar')}")


def _refused(fails: list, tc: str, result: dict, key: str, label: str, what: str) -> None:
    if result["went_through"]:
        record_finding(tc, f"LOW validation: {what} accepted", messages=result["messages"],
                       screenshot=result["screenshot"])
        fails.append(f"PRODUCT: {what} was NOT refused — saved; messages {result['messages']}; {result['screenshot']}")
        return
    if not result["refused"]:
        fails.append(f"{what}: neither refused nor saved: {result['evidence']}")
        return
    if not refusal_points_at(result, key, label):
        fails.append(f"{what}: refused, but nothing names {label!r}: {result['evidence']}")
    elif not REQUIRED_RE.search(result["messages"] or ""):
        record_finding(tc, "LOW wording: refusal does not say the field is required", shown=result["messages"])


def _row_unchanged(fails: list, result: dict) -> None:
    before, after = result["before_row"], result["after_row"]
    if (before.get("status"), before.get("modified")) != (after.get("status"), after.get("modified")):
        fails.append(f"row badge / Last modified changed after a refused save: {before} -> {after}")


def _row_published_now(fails: list, result: dict) -> None:
    after = result["after_row"]
    if _norm(after.get("status")).upper() != "PUBLISHED":
        fails.append(f"row badge reads {after.get('status')!r}, not PUBLISHED")
    stamp = parse_row_modified(after.get("modified", ""))
    if not is_current_time(stamp) or after.get("modified") == result["before_row"].get("modified"):
        fails.append(f"Last modified {after.get('modified')!r} is not the current time (before "
                     f"{result['before_row'].get('modified')!r})")


def _intact(card: dict) -> list[str]:
    problems = []
    for part in ("label_box", "value_box"):
        box = card.get(part) or {}
        if box.get("scroll_width", 0) > box.get("client_width", 0) + 1:
            problems.append(f"{part} content wider than its box ({box.get('scroll_width')} > {box.get('client_width')})")
        if box.get("text_overflow") == "ellipsis":
            problems.append(f"{part} text-overflow ellipsis")
    card_box = card.get("card_box") or {}
    for part in ("label_box", "value_box"):
        box = card.get(part) or {}
        if box and card_box and (box.get("right", 0) > card_box.get("right", 0) + 2
                                 or box.get("left", 0) < card_box.get("left", 0) - 2):
            problems.append(f"{part} overflows its card")
    return problems


def _render_intact(fails: list, anon_view, tc: str, label: str, locale: str, predicate, what: str) -> None:
    pub = _public_expect(fails, anon_view, tc, label, locale, predicate, what=what)
    if pub["held"]:
        problems = _intact(pub["card"])
        if locale == "ar" and pub["card"]["label_box"].get("direction") != "rtl":
            problems.append("AR card not RTL")
        if problems:
            record_finding(tc, "LOW char-limit frontend render problem", locale=locale, problems=problems,
                           screenshot=pub["shot"])
            fails.append(f"[{locale}] {what}: not intact: {problems}; {pub['shot']}")


def _videos_count(anon_view) -> int:
    view = anon_view()
    view.open_hub()
    return int(view.counts().get("videos", 0))


def _position_unchanged(fails: list, anon_view, tc: str, label: str, expected_index: int, what: str) -> None:
    pub = _public_expect(fails, anon_view, tc, label, "en", what=what)
    if pub["held"] and pub["card"]["index"] != expected_index:
        fails.append(f"{what}: {label} is card #{pub['card']['index'] + 1}, expected #{expected_index + 1}; "
                     f"{pub['state_cards']}")


def _finish(fails: list) -> None:
    assert not fails, "\n".join(fails)


# ===========================================================================
# Display Name
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_149191
def test_149191_display_name_valid_reaches_public_en_ar(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-137: valid Display Name EN/AR reaches the widget label on the EN and AR hub."""
    tc, fails = "149191", []
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    drv.open_entry_en(entry.code)
    if not drv.editbar_names("QCTEST Clips", STATUS_PUBLISHED):
        fails.append(f"blue bar does not name the entry + PUBLISHED: {drv.editing_bar_text()!r}")
    if drv.field_dir(K_NAME, arabic=True) != "rtl":
        fails.append("Display Name — العربية does not type right-to-left")
    result = edit(drv, entry, tc, "name", data={K_NAME: "QCTEST Reels", f"{K_NAME}_ar": "QCTEST مقاطع قصيرة"})
    _saved_ok(fails, result, "Publish")
    _row_published_now(fails, result)
    now = stored(drv, entry)
    if (now[K_NAME], now[f"{K_NAME}_ar"]) != ("QCTEST Reels", "QCTEST مقاطع قصيرة"):
        fails.append(f"stored values {now[K_NAME]!r}/{now[f'{K_NAME}_ar']!r}")
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        real = real_edit(w, tc, "name", data={K_NAME: "QCTEST Reels", f"{K_NAME}_ar": "QCTEST مقاطع قصيرة"})
        _saved_ok(fails, real, "REAL Publish")
        _public_expect(fails, anon_view, tc, "QCTEST Reels", "en", what="step 5")
        pub = _public_expect(fails, anon_view, tc, "QCTEST مقاطع قصيرة", "ar", what="step 6")
        if pub["held"] and pub["card"]["label_box"].get("direction") != "rtl":
            fails.append(f"AR label not rendered RTL: {pub['card']['label_box']}")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149192
def test_149192_empty_display_name_refused(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-138: an empty EN Display Name is refused; the public label is unchanged."""
    tc, fails = "149192", []
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    result = edit(drv, entry, tc, "empty_name", data={K_NAME: ""})
    if (result["filled"][K_NAME], result["filled"][f"{K_NAME}_ar"]) != ("", "QCTEST مقاطع"):
        fails.append(f"step 3 form state {result['filled']}")
    _refused(fails, tc, result, "ObjectField_displayName", "Display Name", "Publish with an empty EN Display Name")
    _row_unchanged(fails, result)
    if stored(drv, entry)[K_NAME] != "QCTEST Clips":
        fails.append("stored Display Name is no longer 'QCTEST Clips'")
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        original = w.snapshot[K_NAME]
        real = real_edit(w, tc, "empty_name", data={K_NAME: ""})
        _refused(fails, tc, real, "ObjectField_displayName", "Display Name", "REAL Publish with an empty Display Name")
        _public_expect(fails, anon_view, tc, original, "en", what="step 5 (label unchanged)")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149193
def test_149193_display_name_60_char_limit(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-139: Display Name accepts 60, handles the 61st per Rule 5, renders 60 intact EN/AR."""
    tc, fails = "149193", []
    v60 = "QCTEST-ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZA"
    v61 = v60 + "B"
    a60 = "ق" * 60
    assert (len(v60), len(v61), len(a60)) == (60, 61, 60)
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    drv.open_entry_en(entry.code)
    counter, maxlen = drv.counter_reading(K_NAME), drv.native_max_length(K_NAME)
    limit = counter[1] if counter else (maxlen if maxlen > 0 else None)
    record_finding(tc, "implemented limit (info)", counter=counter, maxlength=maxlen, L=limit)
    if limit is not None and limit < 60:
        fails.append(f"Rule 5.3: implemented limit L={limit} < 60")
    result = edit(drv, entry, tc, "60", typed={K_NAME: v60, f"{K_NAME}_ar": a60})
    _saved_ok(fails, result, "60-character Publish")
    if _norm(result["after_row"].get("status")).upper() != "PUBLISHED":
        fails.append(f"row badge {result['after_row'].get('status')!r}")
    now = stored(drv, entry)
    if (now[K_NAME], now[f"{K_NAME}_ar"]) != (v60, a60):
        fails.append(f"60-char values not stored: {len(now[K_NAME])}/{len(now[f'{K_NAME}_ar'])}")
    drv.open_entry_en(entry.code)
    drv.type_text(K_NAME, v61)
    typed_kept = len(drv.text_value(K_NAME))
    block = drv.field_block_text(K_NAME)
    result61 = save(drv)
    shot61 = drv.evidence(f"{tc}_61_after_save")
    after = stored(drv, entry)[K_NAME]
    record_finding(tc, "61st character (info)", typed_kept=typed_kept, block=block, went_through=result61["went_through"],
                   messages=result61["messages"], stored_len=len(after), screenshot=shot61)
    if limit == 60 and len(after) != 60:
        fails.append(f"L=60 but the 61-character value was stored ({len(after)} chars); {shot61}")
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        real = real_edit(w, tc, "name60", typed={K_NAME: v60, f"{K_NAME}_ar": a60})
        _saved_ok(fails, real, "REAL 60-character Publish")
        _render_intact(fails, anon_view, tc, v60, "en", None, "60-char EN render")
        _render_intact(fails, anon_view, tc, a60, "ar", None, "60-char AR render")
    _finish(fails)


# ===========================================================================
# Unit Label
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_149194
def test_149194_unit_label_valid_reaches_public_en_ar(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-140: valid Unit Label EN/AR shows right after the widget's live count on EN and AR."""
    tc, fails = "149194", []
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    drv.open_entry_en(entry.code)
    if not drv.editbar_names("QCTEST Clips", STATUS_PUBLISHED):
        fails.append(f"blue bar does not name the entry + PUBLISHED: {drv.editing_bar_text()!r}")
    if drv.field_dir(K_UNIT, arabic=True) != "rtl":
        fails.append("Unit Label — العربية does not type right-to-left")
    result = edit(drv, entry, tc, "unit", data={K_UNIT: "QCTEST reels", f"{K_UNIT}_ar": "QCTEST مقطع قصير"})
    _saved_ok(fails, result, "Publish")
    _row_published_now(fails, result)
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        label_en, label_ar = w.snapshot[K_NAME], _ar(w.snapshot, K_NAME)
        real = real_edit(w, tc, "unit", data={K_UNIT: "QCTEST reels", f"{K_UNIT}_ar": "QCTEST مقطع قصير"})
        _saved_ok(fails, real, "REAL Publish")
        videos = _videos_count(anon_view)
        _public_expect(fails, anon_view, tc, label_en, "en",
                       predicate=lambda c: _norm(c["value"]) == f"{videos:,} QCTEST reels", what="step 5")
        pub = _public_expect(fails, anon_view, tc, label_ar, "ar",
                             predicate=lambda c: _norm(c["value"]) == f"{videos:,} QCTEST مقطع قصير", what="step 6")
        if pub["held"] and pub["card"]["value_box"].get("direction") != "rtl":
            fails.append("AR value not RTL")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149195
def test_149195_empty_unit_label_refused(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-141: an empty EN Unit Label is refused; the public unit label is unchanged."""
    tc, fails = "149195", []
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    result = edit(drv, entry, tc, "empty_unit", data={K_UNIT: ""})
    if (result["filled"][K_UNIT], result["filled"][f"{K_UNIT}_ar"]) != ("", "QCTEST مقطع"):
        fails.append(f"step 3 form state {result['filled']}")
    _refused(fails, tc, result, "ObjectField_unitLabel", "Unit Label", "Publish with an empty EN Unit Label")
    _row_unchanged(fails, result)
    if stored(drv, entry)[K_UNIT] != "QCTEST clips":
        fails.append("stored Unit Label is no longer 'QCTEST clips'")
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        label, unit = w.snapshot[K_NAME], w.snapshot[K_UNIT]
        real = real_edit(w, tc, "empty_unit", data={K_UNIT: ""})
        _refused(fails, tc, real, "ObjectField_unitLabel", "Unit Label", "REAL Publish with an empty Unit Label")
        _public_expect(fails, anon_view, tc, label, "en",
                       predicate=lambda c: _norm(c["value"]).endswith(f" {unit}"), what="step 5 (unit unchanged)")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149196
def test_149196_unit_label_30_char_limit(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-142: Unit Label accepts 30, handles the 31st per Rule 5, renders 30 intact EN/AR."""
    tc, fails = "149196", []
    v30 = "QCTEST-ABCDEFGHIJKLMNOPQRSTUVW"
    v31 = v30 + "X"
    a30 = "ق" * 30
    assert (len(v30), len(v31), len(a30)) == (30, 31, 30)
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    drv.open_entry_en(entry.code)
    counter, maxlen = drv.counter_reading(K_UNIT), drv.native_max_length(K_UNIT)
    limit = counter[1] if counter else (maxlen if maxlen > 0 else None)
    record_finding(tc, "implemented limit (info)", counter=counter, maxlength=maxlen, L=limit)
    if limit is not None and limit < 30:
        fails.append(f"Rule 5.3: implemented limit L={limit} < 30")
    result = edit(drv, entry, tc, "30", typed={K_UNIT: v30, f"{K_UNIT}_ar": a30})
    _saved_ok(fails, result, "30-character Publish")
    now = stored(drv, entry)
    if (now[K_UNIT], now[f"{K_UNIT}_ar"]) != (v30, a30):
        fails.append(f"30-char values not stored: {len(now[K_UNIT])}/{len(now[f'{K_UNIT}_ar'])}")
    drv.open_entry_en(entry.code)
    drv.type_text(K_UNIT, v31)
    typed_kept = len(drv.text_value(K_UNIT))
    block = drv.field_block_text(K_UNIT)
    result31 = save(drv)
    shot31 = drv.evidence(f"{tc}_31_after_save")
    after = stored(drv, entry)[K_UNIT]
    record_finding(tc, "31st character (info)", typed_kept=typed_kept, block=block, went_through=result31["went_through"],
                   messages=result31["messages"], stored_len=len(after), screenshot=shot31)
    if limit == 30 and len(after) != 30:
        fails.append(f"L=30 but the 31-character value was stored ({len(after)} chars); {shot31}")
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        label_en, label_ar = w.snapshot[K_NAME], _ar(w.snapshot, K_NAME)
        real = real_edit(w, tc, "unit30", typed={K_UNIT: v30, f"{K_UNIT}_ar": a30})
        _saved_ok(fails, real, "REAL 30-character Publish")
        _render_intact(fails, anon_view, tc, label_en, "en", lambda c: _norm(c["value"]).endswith(v30),
                       "30-char EN render")
        _render_intact(fails, anon_view, tc, label_ar, "ar", lambda c: _norm(c["value"]).endswith(a30),
                       "30-char AR render")
    _finish(fails)


# ===========================================================================
# Icon
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149228
def test_149228_svg_icon_shown_on_public_widget(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-174: a new SVG icon is stored and rendered above the widget label."""
    tc, fails = "149228", []
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    drv.open_entry_en(entry.code)
    drv.fill_widget({"icon_file": ICON_2})
    pending = drv.upload_block_text("icon")
    if "qctest-cw-icon-2" not in pending:
        fails.append(f"step 3: qctest-cw-icon-2.svg not shown as pending: {pending!r}")
    result = save(drv)
    drv.evidence(f"{tc}_after_save")
    _saved_ok(fails, result, "Publish")
    current = stored(drv, entry)["icon_current"]
    # Liferay de-duplicates a re-uploaded name ("qctest-cw-icon-2 (1).svg") — test-data artefact of re-runs.
    if not re.fullmatch(r"qctest-cw-icon-2( \(\d+\))?\.svg", current):
        fails.append(f"step 4: current file is {current!r}, not qctest-cw-icon-2.svg")
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        label = w.snapshot[K_NAME]
        real = real_edit(w, tc, "icon", data={"icon_file": ICON_2})
        _saved_ok(fails, real, "REAL Publish")
        _public_expect(fails, anon_view, tc, label, "en",
                       predicate=lambda c: "qctest-cw-icon-2" in c["icon_url"], what="step 5 icon")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149229
def test_149229_new_widget_without_icon_refused(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-175: a new Count Widget cannot be submitted without an icon."""
    tc, fails = "149229", []
    drv = role_session(page)
    data = {K_TYPE: "Publications", K_NAME: "QCTEST Docs", f"{K_NAME}_ar": "QCTEST وثائق", K_UNIT: "QCTEST docs",
            f"{K_UNIT}_ar": "QCTEST وثيقة", K_ORDER: 700, K_ACTIVE: True}
    entry, result = create(drv, cw_disposable, "QCTEST-130709-CW-02", data, tc)
    _refused(fails, tc, result, "ObjectField_icon", "Icon", "Publish without an Icon")
    if result.get("new_rows"):
        fails.append(f"a new entry was created: {result['new_rows']}")
    absent = public_absent(anon_view, tc, "QCTEST Docs")
    if absent["shown"] or absent["guest_delivered"]:
        fails.append(f"public strip / feed carries 'QCTEST Docs': {absent}")
    _finish(fails)


# ===========================================================================
# Content Type / Count
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149235
def test_149235_content_type_drives_public_total(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-181: changing Content Type to Publications makes the widget show the Publications total."""
    tc, fails = "149235", []
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    first = public_card(anon_view, tc, "Publications", "en")
    assert first["held"], f"step 1: the real Publications widget is not shown: {first['state_cards']}"
    n = _norm(first["card"]["value"]).split(" ")[0]
    drv.open_entry_en(entry.code)
    if drv.picklist_value(K_TYPE) != "Videos":
        fails.append(f"step 3: form Content Type {drv.picklist_value(K_TYPE)!r}, not Videos")
    result = edit(drv, entry, tc, "ctype", data={K_TYPE: "Publications"})
    if result["filled"][K_TYPE] != "Publications":
        fails.append(f"step 4: selected {result['filled'][K_TYPE]!r}")
    _saved_ok(fails, result, "Publish")
    if _norm(result["after_row"].get("status")).upper() != "PUBLISHED":
        fails.append(f"row badge {result['after_row'].get('status')!r}")
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        label, unit = w.snapshot[K_NAME], w.snapshot[K_UNIT]
        before = public_card(anon_view, tc, label, "en")
        real = real_edit(w, tc, "ctype", data={K_TYPE: "Publications"})
        _saved_ok(fails, real, "REAL Publish")
        _public_expect(fails, anon_view, tc, label, "en", predicate=lambda c: _norm(c["value"]) == f"{n} {unit}",
                       what=f"step 6 (was {before['card'] and before['card']['value']!r})")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149236
def test_149236_new_widget_without_content_type_refused(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-182: a new Count Widget cannot be submitted without a Content Type."""
    tc, fails = "149236", []
    drv = role_session(page)
    data = {K_NAME: "QCTEST None", f"{K_NAME}_ar": "QCTEST لا شيء", K_UNIT: "QCTEST items",
            f"{K_UNIT}_ar": "QCTEST عنصر", "icon_file": ICON_1, K_ORDER: 800, K_ACTIVE: True}
    entry, result = create(drv, cw_disposable, "QCTEST-130709-CW-03", data, tc)
    if result.get("filled", {}).get(K_TYPE):
        fails.append(f"step 2: Content Type shows {result['filled'][K_TYPE]!r}")
    _refused(fails, tc, result, "contentType", "Content Type", "Publish without a Content Type")
    if result.get("new_rows"):
        fails.append(f"a new entry was created: {result['new_rows']}")
    absent = public_absent(anon_view, tc, "QCTEST None")
    if absent["shown"] or absent["guest_delivered"]:
        fails.append(f"public strip / feed carries 'QCTEST None': {absent}")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.ui
@pytest.mark.tc_149237
def test_149237_content_type_dropdown_five_options(page):
    """MEDIA-MCHUB-TC-183: Content Type offers exactly Articles, Photo Albums, Videos, Podcast, Publications."""
    drv = role_session(page)
    drv.open_create_form_en()
    options = drv.content_type_options()
    drv.evidence("149237_content_type_options")
    assert options == list(CONTENT_TYPES), f"dropdown offers {options}"


@AUTH_FREE_PAGE
@pytest.mark.ui
@pytest.mark.tc_149238
def test_149238_no_editable_count_field(page, cw_disposable):
    """MEDIA-MCHUB-TC-184: the form has the eight authorable inputs and no Count input."""
    tc = "149238"
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    drv.open_entry_en(entry.code)
    controls = drv.form_controls()
    drv.evidence(f"{tc}_form")
    labels = {_norm(c["label"]).rstrip(" *") for c in controls}
    expected = {"Content Type", "Display Name", "Display Name — العربية", "Icon", "Unit Label",
                "Unit Label — العربية", "Display Order", "Active Status"}
    missing = expected - labels
    count_like = [c for c in controls if "count" in (c["label"] + c["name"]).lower()]
    assert not missing, f"form lacks {missing}; controls {controls}"
    assert not count_like, f"form offers a count input: {count_like}"


# ===========================================================================
# Display Order
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149244
def test_149244_display_order_places_widget(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-190: Display Order 900 (100-grid, after every other widget) makes the widget last."""
    tc, fails = "149244", []
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    drv.open_entry_en(entry.code)
    if drv.text_value(K_ORDER) != "600":
        fails.append(f"step 2: form shows Display Order {drv.text_value(K_ORDER)!r}")
    result = edit(drv, entry, tc, "order900", data={K_ORDER: 900})
    _saved_ok(fails, result, "Publish")
    if _norm(result["after_row"].get("status")).upper() != "PUBLISHED":
        fails.append(f"row badge {result['after_row'].get('status')!r}")
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        label = w.snapshot[K_NAME]
        real = real_edit(w, tc, "order900", data={K_ORDER: 900})
        _saved_ok(fails, real, "REAL Publish")
        view = anon_view()
        state, _, held = view.poll(lambda s: s.get("cards") and card_index(s, label) == len(s["cards"]) - 1,
                                   timeout=30.0)
        shot = view.strip_evidence(f"{tc}_public_order900")
        if not held:
            fails.append(f"{label} with Display Order 900 is card #{card_index(state, label) + 1} of "
                         f"{len(state.get('cards', []))}, not last: "
                         f"{[(c['label'], c['value']) for c in state.get('cards', [])]}; {shot}")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149246
def test_149246_empty_display_order_refused(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-192: an empty Display Order is refused; the public position is unchanged."""
    tc, fails = "149246", []
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    result = edit(drv, entry, tc, "empty_order", data={K_ORDER: ""})
    if result["filled"][K_ORDER] != "":
        fails.append(f"step 3: Display Order shows {result['filled'][K_ORDER]!r}")
    _refused(fails, tc, result, "ObjectField_displayOrder", "Display Order", "Publish with an empty Display Order")
    if stored(drv, entry)[K_ORDER] != "600":
        fails.append("stored Display Order is no longer 600")
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        label = w.snapshot[K_NAME]
        idx = card_index(public_card(anon_view, tc, label, "en")["full_state"], label)
        real = real_edit(w, tc, "empty_order", data={K_ORDER: ""})
        _refused(fails, tc, real, "ObjectField_displayOrder", "Display Order", "REAL Publish with an empty Display Order")
        _position_unchanged(fails, anon_view, tc, label, idx, "step 5")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.tc_149247
def test_149247_zero_and_negative_display_order_refused(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-193: Display Order 0 and -100 are refused (positive integers only)."""
    tc, fails = "149247", []
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    for value in ("0", "-100"):
        result = edit(drv, entry, tc, f"order_{value}", data={K_ORDER: value})
        _refused(fails, tc, result, "ObjectField_displayOrder", "Display Order", f"Publish with Display Order {value}")
        now = stored(drv, entry)[K_ORDER]
        if now != "600":
            fails.append(f"Display Order {value}: stored value is now {now!r}")
            if result["went_through"]:
                edit(drv, entry, tc, f"order_restore_after_{value}", data={K_ORDER: 600})
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        label = w.snapshot[K_NAME]
        idx = card_index(public_card(anon_view, tc, label, "en")["full_state"], label)
        for value in ("0", "-100"):
            real = real_edit(w, tc, f"order_{value}", data={K_ORDER: value})
            _refused(fails, tc, real, "ObjectField_displayOrder", "Display Order",
                     f"REAL Publish with Display Order {value}")
        _position_unchanged(fails, anon_view, tc, label, idx, "step 5")
    _finish(fails)


# ===========================================================================
# Workflow / visibility
# ===========================================================================
@AUTH_FREE_PAGE
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.tc_149254
def test_149254_draft_widget_hidden_publicly(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-200: a Draft Count Widget (Active ticked) is stored for staff and not shown publicly.
    Runs as QC Site Content Author (Phase-3 rule: draft cases on the Author account)."""
    tc, fails = "149254", []
    drv = role_session(page, ROLE_AUTHOR)
    data = {K_TYPE: "Podcast", K_NAME: "QCTEST Draft Widget", f"{K_NAME}_ar": "QCTEST عنصر مسودة",
            K_UNIT: "QCTEST eps", f"{K_UNIT}_ar": "QCTEST حلقة", "icon_file": ICON_1, K_ORDER: 700, K_ACTIVE: True}
    entry, result = create(drv, cw_disposable, "QCTEST-130709-CW-02", data, tc, publish=False, role=ROLE_AUTHOR)
    assert result.get("went_through"), f"Save as Draft did not go through: {result}"
    assert entry is not None, "draft saved but not identifiable"
    if not any(MSG_DRAFT_SAVED in t for t in result.get("editbar", [])):
        fails.append(f"no 'Draft saved.' message: {result.get('editbar')}")
    drv.open_list_all()
    status = drv.row_status_of(entry)
    if status != STATUS_DRAFT:
        fails.append(f"row badge {status!r}, not DRAFT")
    absent = public_absent(anon_view, tc, "QCTEST Draft Widget")
    if absent["shown"] or absent["guest_delivered"]:
        fails.append(f"PRODUCT: draft visible to a visitor: {absent}")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.uat
@pytest.mark.tc_149259
def test_149259_unit_label_after_live_count(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-205: a published widget shows 'V QCTEST clips' (live Videos total) in EN and AR."""
    tc, fails = "149259", []
    pre = public_card(anon_view, tc, "Videos", "en")
    assert pre["held"], f"PRECONDITION: the real Videos widget is not shown: {pre['state_cards']}"
    v = _norm(pre["card"]["value"]).split(" ")[0]
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    drv.open_list_all()
    row = drv.row_of(entry)
    if not (row.get("entry_id") and row.get("code")) or _norm(row.get("status")).upper() != "PUBLISHED":
        fails.append(f"new row lacks identifier / PUBLISHED: {row}")
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        real = real_edit(w, tc, "clips", data={K_NAME: "QCTEST Clips", f"{K_NAME}_ar": "QCTEST مقاطع",
                                               K_UNIT: "QCTEST clips", f"{K_UNIT}_ar": "QCTEST مقطع"})
        _saved_ok(fails, real, "REAL Publish")
        _public_expect(fails, anon_view, tc, "QCTEST Clips", "en",
                       predicate=lambda c: _norm(c["value"]) == f"{v} QCTEST clips", what="step 4")
        pub = _public_expect(fails, anon_view, tc, "QCTEST مقاطع", "ar",
                             predicate=lambda c: _norm(c["value"]) == f"{v} QCTEST مقطع", what="step 5")
        if pub["held"] and pub["card"]["value_box"].get("direction") != "rtl":
            fails.append("AR widget not RTL")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_high
@pytest.mark.tc_149262
def test_149262_active_status_hides_and_restores(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-208: unticking Active Status hides the widget (strip reflows); ticking restores it."""
    tc, fails = "149262", []
    drv = role_session(page)
    entry = create_cw01(drv, cw_disposable, tc)
    off = edit(drv, entry, tc, "inactive", data={K_ACTIVE: False})
    _saved_ok(fails, off, "Publish (inactive)")
    if _norm(off["after_row"].get("status")).upper() != "PUBLISHED":
        fails.append(f"step 3: badge {off['after_row'].get('status')!r}, not PUBLISHED")
    on = edit(drv, entry, tc, "active", data={K_ACTIVE: True})
    _saved_ok(fails, on, "Publish (active)")
    with real_widget_window(drv, REAL_VIDEOS, tc) as w:
        label = w.snapshot[K_NAME]
        before = _public_expect(fails, anon_view, tc, label, "en", what="step 2 (shown before)")
        idx = before["card"]["index"] if before["held"] else -1
        gaps_before = reflow_gaps(before["full_state"])
        real_off = real_edit(w, tc, "inactive", data={K_ACTIVE: False})
        _saved_ok(fails, real_off, "REAL Publish (inactive)")
        drv.open_list_all()
        badge = _norm(next((r["status"] for r in drv.rows_full() if r["code"] == REAL_VIDEOS), ""))
        if badge.upper() != "PUBLISHED":
            fails.append(f"step 3: real row badge {badge!r}, not PUBLISHED")
        view = anon_view()
        state, _, gone = view.poll(lambda s: card_index(s, label) == -1, timeout=30.0)
        shot = view.strip_evidence(f"{tc}_public_inactive")
        if not gone:
            fails.append(f"PRODUCT: inactive widget {label!r} still shown; {shot}")
        gaps = reflow_gaps(state)
        if gaps and (max(gaps) - min(gaps) > 2 or (gaps_before and abs(max(gaps) - max(gaps_before)) > 2)):
            fails.append(f"remaining cards do not close up: gaps {gaps} (before {gaps_before}); {shot}")
        record_finding(tc, "inactive state (info)", strip=[(c["label"], c["value"]) for c in state.get("cards", [])],
                       gaps=gaps, gaps_before=gaps_before, screenshot=shot)
        real_on = real_edit(w, tc, "active", data={K_ACTIVE: True})
        _saved_ok(fails, real_on, "REAL Publish (active)")
        _position_unchanged(fails, anon_view, tc, label, idx, "step 6 (shown again in its position)")
    _finish(fails)


@AUTH_FREE_PAGE
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_149273
def test_149273_publish_without_arabic_blocked(page, cw_disposable, anon_view):
    """MEDIA-MCHUB-TC-219: publishing without Arabic content is blocked with 'Arabic content is required.'"""
    tc, fails = "149273", []
    drv = role_session(page)
    data = {K_TYPE: "Articles", K_NAME: "QCTEST EN only", f"{K_NAME}_ar": "", K_UNIT: "QCTEST stories",
            f"{K_UNIT}_ar": "", "icon_file": ICON_1, K_ORDER: 900, K_ACTIVE: True}
    entry, result = create(drv, cw_disposable, "QCTEST-130709-CW-04", data, tc)
    if result["went_through"]:
        fails.append(f"PRODUCT: published without Arabic; {result['screenshot']}")
    elif MSG_ARABIC_REQUIRED not in (result["messages"] or ""):
        record_finding(tc, "LOW wording: Arabic-required message differs", expected=MSG_ARABIC_REQUIRED,
                       shown=result["messages"], evidence=result["evidence"], screenshot=result["screenshot"])
        if not result["refused"]:
            fails.append(f"neither refused nor saved: {result['evidence']}")
    if result.get("new_rows"):
        fails.append(f"a new row was created: {result['new_rows']}")
    for locale in ("en", "ar"):
        absent = public_absent(anon_view, tc, "QCTEST EN only", locale)
        if absent["shown"]:
            fails.append(f"[{locale}] English-only QCTEST widget shown: {absent['cards']}")
    _finish(fails)


@pytest.mark.auth
@pytest.mark.workflow
@pytest.mark.tc_149338
def test_149338_visitor_cannot_reach_authoring_or_subscribers(anon_view):
    """MEDIA-MCHUB-TC-284: a logged-out visitor sees no authoring form/entries and no subscriber data."""
    view = anon_view()
    fails = []
    for tc_step, path in (("1", MANAGE_PATH), ("2", SUBSCRIBER_PATH)):
        probe = view.anonymous_probe(path)
        shot = view.evidence(f"149338_step{tc_step}_anonymous")
        record_finding("149338", f"anonymous probe step {tc_step} (info)", probe=probe, screenshot=shot)
        if probe["signed_in"] or probe["object_fields"] or probe["entry_rows"] or probe["emails"]:
            fails.append(f"step {tc_step}: {path} exposes staff data to a visitor: {probe}; {shot}")
    _finish(fails)
