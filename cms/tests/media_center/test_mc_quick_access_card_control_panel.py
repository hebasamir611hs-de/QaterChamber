"""
cms/tests/media_center/test_mc_quick_access_card_control_panel.py — QAC agent.

Field / validation / visibility cases of PBI 130709 (Azure plan 137724, suite
140368) on `manage-media-center-quick-access-card`, asserted against the
logged-out public hub /web/qatar-chamber/media-center ("Explore the hub").

Disclosed substitutions (case wording -> what runs):
  - "Submit for Review" as the Site Content Editor -> the Editor's form button
    reads "Publish" (live 2026-10-07); same submit control.
  - "Main Menu -> Insights & Media -> Media Center" -> direct URL to the hub in
    a fresh logged-out context (the menu itself is not this object's subject).
  - "QCTEST-130709-QAC-NN" -> a disposable card with the case's exact titles,
    identified by captured entry id + server code (the form has no ERC field).
  - Display Order 900 on cards that need no position -> 1000 (rules: QCTEST
    >= 1000 unless a position is asserted); 700/800/900 kept where the case
    asserts a slot after the six real cards (orders read live: 100..600).
  - Icon fixtures generated locally: qctest-qac-icon.svg ~10 KB, .png 64x64
    ~9 KB, .jpg 64x64 ~5 KB; uploaded under a unique "qctest-qac-icon-<hex>"
    name so Documents & Media never dedupes onto another run's file.
  - USER DECISION 2026-10-12: the six quick-access cards are FIXED by design
    (hub fragment maxCards=6), so a QCTEST card never renders publicly. Cases
    that edit "QCTEST-130709-QAC-01" now run on the real card Photo Gallery
    (QCDEMO-130709-CARD-01; order case: CARD-01 <-> CARD-02 100/200 swap) under
    snapshot -> edit (UI, Editor) -> logged-out check -> exact PUT restore ->
    empty diff, with the rule-4b concurrency guard (fixture `real_guard`).
    Expected public slot "7th" -> the real card's own slot (#1).
"""

from __future__ import annotations

from time import monotonic

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.media_center.mc_quick_access_card_admin_page import ROLE_EDITOR, K_ICON  # noqa: F401
from cms.tests.media_center.qac_support import (  # noqa: F401 — fixtures
    ICON_JPG,
    ICON_PNG,
    QAC01,
    VIDEO_LIBRARY,
    attach,
    card_data,
    create,
    create_ok,
    edit,
    expected_index,
    find,
    message_check,
    overflow_outside,
    public_until,
    qac,
    real_cards,
    record_finding,
    require_active,
    stored,
    sync_identity,
    text_intact,
    real_guard,
    real_session,
    guarded_edit,
    save,
)

pytestmark = [pytest.mark.control_panel, pytest.mark.media, pytest.mark.pbi_130709,
              pytest.mark.xdist_group("mc_qac_130709")]

EPIC = "Media Center"
FEATURE = "Quick Access Card — Control Panel (fields)"

T100_EN = "QCTEST-ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNO"
T101_EN = T100_EN + "P"
T100_AR = "ق" * 100
D150_EN = ("QCTEST-ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ"
           "ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLM")
D151_EN = D150_EN + "N"
D150_AR = "ق" * 150


def _labels(tc: str, qa: str, title: str):
    allure.dynamic.epic(EPIC)
    allure.dynamic.feature(FEATURE)
    allure.dynamic.title(title)
    allure.dynamic.label("testcase", tc)
    allure.dynamic.label("pbi", "130709")
    allure.dynamic.label("qa_id", qa)


def _late(late: list, fn, *args, **kwargs):
    """Runs a public step whose failure is kept and re-raised at the end of the
    test (so the CMS steps after it still run); never swallowed."""
    try:
        return fn(*args, **kwargs)
    except AssertionError as exc:
        late.append(str(exc).splitlines()[0])
        return None


def _assert_loaded(result: dict, entry_title: str):
    assert entry_title in result["banner"] and "(Published)" in result["banner"], \
        f"the blue bar does not name {entry_title!r} as Published: {result['banner']!r}"


def _refused(result: dict, what: str):
    assert not result["went_through"], f"{what} was SAVED (expected refused): {result.get('editbar')}"


# ===========================================================================
CARD01 = "QCDEMO-130709-CARD-01"
CARD02 = "QCDEMO-130709-CARD-02"


def _hub(sessions):
    return sessions.visitor()


@pytest.mark.tc_149197
@pytest.mark.functional_low
@pytest.mark.bilingual
def test_card_title_edit_reaches_public_en_and_ar(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-143 — valid Card Title EN/AR reaches the public card (real card under snapshot/restore)."""
    _labels("149197", "MEDIA-MCHUB-TC-143", "Card Title EN/AR reaches the public card")
    sessions, admin, ref = real_session(qac, real_guard)
    admin.open_list_all()
    modified_before = admin.row_modified_text(ref)
    result = guarded_edit(real_guard, admin, ref, {"cardTitle": "QCTEST Press Kit", "cardTitle_ar": "QCTEST الملف الصحفي"},
                          "149197")
    _assert_loaded(result, ref.title)
    assert admin.ar_direction("cardTitle") == "rtl", "the Arabic Card Title box is not right-to-left"
    assert result["went_through"], f"the edit was refused: {result['evidence']}"
    started = monotonic()
    admin.open_list_all()
    assert admin.row_status_of(ref) == STATUS_PUBLISHED
    assert admin.row_modified_text(ref) != modified_before, "Last modified did not change"
    visitor = _hub(sessions)
    public_until(visitor, lambda c: find(c, ref.code).get("title") == "QCTEST Press Kit",
                 "card title = 'QCTEST Press Kit'", "149197", "en", started)
    cards = public_until(visitor, lambda c: find(c, ref.code).get("title") == "QCTEST الملف الصحفي",
                         "card title = 'QCTEST الملف الصحفي'", "149197", "ar", budget=False)
    assert find(cards, ref.code)["title_box"]["direction"] == "rtl", "the AR card title is not rendered RTL"


@pytest.mark.tc_149198
@pytest.mark.functional_low
def test_empty_english_card_title_is_refused(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-144 — empty EN Card Title refused; public unchanged."""
    _labels("149198", "MEDIA-MCHUB-TC-144", "Empty English Card Title is refused")
    sessions, admin, ref = real_session(qac, real_guard)
    admin.open_list_all()
    modified_before = admin.row_modified_text(ref)
    title_ar = real_guard.snapshots[ref.code]["cardTitle_i18n"]["ar_SA"]
    result = guarded_edit(real_guard, admin, ref, {"cardTitle": ""}, "149198")
    _assert_loaded(result, ref.title)
    assert result["filled"]["cardTitle"] == "" and result["filled"]["cardTitle_ar"] == title_ar
    _refused(result, "an empty English Card Title")
    assert stored(admin, ref)["cardTitle"] == ref.title
    admin.open_list_all()
    assert admin.row_status_of(ref) == STATUS_PUBLISHED
    assert admin.row_modified_text(ref) == modified_before, "Last modified changed although nothing was saved"
    blob = result["messages"] + result.get("page_text", "")
    if not ("Card Title" in blob and "required" in blob.lower()):
        record_finding("149198", "WORDING", expected="'Card Title' named as required", shown=result["evidence"])
    public_until(_hub(sessions), lambda c: find(c, ref.code).get("title") == ref.title,
                 f"card still '{ref.title}'", "149198", budget=False)


def _limit_case(qac, guard, tc: str, key: str, us_limit: int, v_en: str, v_en_over: str, v_ar: str, box: str):
    sessions, admin, ref = real_session(qac, guard)
    admin.open_entry(ref.code)
    limits = {"counter_en": admin.counter_limit(key), "counter_ar": admin.counter_limit(key, True),
              "maxlength_en": admin.native_max_length(key), "maxlength_ar": admin.native_max_length(key, True)}
    attach("implemented limit evidence", limits)
    assert limits["counter_en"] is None or limits["counter_en"] >= us_limit, \
        f"implemented limit {limits['counter_en']} < {us_limit} (Rule 5.3)"
    result = guarded_edit(guard, admin, ref, {key: v_en, f"{key}_ar": v_ar}, tc)
    assert result["went_through"], f"PRODUCT: {us_limit}-character values were refused: {result['evidence']}"
    values = stored(admin, ref)
    assert values[key] == v_en and values[f"{key}_ar"] == v_ar, "stored values differ from the input"
    problems = {}
    for locale, value in (("en", v_en), ("ar", v_ar)):
        visitor = _hub(sessions)
        cards = public_until(visitor, lambda c, v=value: find(c, ref.code).get(box) == v,
                             f"{us_limit}-char {key} {locale}", tc, locale, budget=False)
        card = find(cards, ref.code)
        issues = text_intact(card[f"{box}_box"]) + overflow_outside(card)
        if visitor.page_layout()["hscroll"]:
            issues.append("page scrolls horizontally")
        if locale == "ar" and card[f"{box}_box"]["direction"] != "rtl":
            issues.append("not rendered RTL")
        problems[locale] = {"issues": issues, "screenshot": visitor.evidence(f"{tc}_limit_{locale}")}
    over = guarded_edit(guard, admin, ref, {key: v_en_over}, tc + "_over")
    stored_over = stored(admin, ref)[key]
    attach("over-limit outcome", {"typed_len": len(over["filled"][key]), "went_through": over["went_through"],
                                  "stored_len": len(stored_over), "messages": over["messages"]})
    assert len(stored_over) <= us_limit, f"the {us_limit + 1}-character value was stored ({len(stored_over)})"
    bad = {k: v for k, v in problems.items() if v["issues"]}
    if bad:
        record_finding(tc, "LOW char-limit frontend render problem", details=bad)
    assert not bad, f"the long {key} breaks the public card: {bad}"


@pytest.mark.tc_149199
@pytest.mark.functional_low
def test_card_title_100_char_limit(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-145 — Card Title 100 chars accepted, 101st per Rule 5, renders intact."""
    _labels("149199", "MEDIA-MCHUB-TC-145", "Card Title character limit (100)")
    _limit_case(qac, real_guard, "149199", "cardTitle", 100, T100_EN, T101_EN, T100_AR, "title")


@pytest.mark.tc_149200
@pytest.mark.functional_low
@pytest.mark.bilingual
def test_card_description_edit_reaches_public_en_and_ar(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-146 — valid Card Description EN/AR reaches the public card."""
    _labels("149200", "MEDIA-MCHUB-TC-146", "Card Description EN/AR reaches the public card")
    sessions, admin, ref = real_session(qac, real_guard)
    admin.open_list_all()
    modified_before = admin.row_modified_text(ref)
    en, ar = "QCTEST Logos, fact sheets and brand assets.", "QCTEST الشعارات والنشرات التعريفية وهوية العلامة."
    result = guarded_edit(real_guard, admin, ref, {"cardDescription": en, "cardDescription_ar": ar}, "149200")
    _assert_loaded(result, ref.title)
    assert admin.ar_direction("cardDescription") == "rtl"
    assert result["went_through"], f"the edit was refused: {result['evidence']}"
    started = monotonic()
    admin.open_list_all()
    assert admin.row_status_of(ref) == STATUS_PUBLISHED
    assert admin.row_modified_text(ref) != modified_before, "Last modified did not change"
    visitor = _hub(sessions)
    public_until(visitor, lambda c: find(c, ref.code).get("desc") == en, "description EN", "149200", "en", started)
    cards = public_until(visitor, lambda c: find(c, ref.code).get("desc") == ar, "description AR", "149200", "ar",
                         budget=False)
    assert find(cards, ref.code)["desc_box"]["direction"] == "rtl"


@pytest.mark.tc_149201
@pytest.mark.functional_low
def test_empty_english_card_description_is_refused(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-147 — empty EN Card Description refused; public unchanged."""
    _labels("149201", "MEDIA-MCHUB-TC-147", "Empty English Card Description is refused")
    sessions, admin, ref = real_session(qac, real_guard)
    snap = real_guard.snapshots[ref.code]
    admin.open_list_all()
    modified_before = admin.row_modified_text(ref)
    result = guarded_edit(real_guard, admin, ref, {"cardDescription": ""}, "149201")
    _assert_loaded(result, ref.title)
    assert result["filled"]["cardDescription"] == ""
    _refused(result, "an empty English Card Description")
    assert stored(admin, ref)["cardDescription"] == snap["cardDescription"]
    admin.open_list_all()
    assert admin.row_status_of(ref) == STATUS_PUBLISHED
    assert admin.row_modified_text(ref) == modified_before
    blob = result["messages"] + result.get("page_text", "")
    if not ("Card Description" in blob and "required" in blob.lower()):
        record_finding("149201", "WORDING", expected="'Card Description' named as required", shown=result["evidence"])
    public_until(_hub(sessions), lambda c: find(c, ref.code).get("desc") == snap["cardDescription"],
                 "description unchanged", "149201", budget=False)


@pytest.mark.tc_149202
@pytest.mark.functional_low
def test_card_description_150_char_limit(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-148 — Card Description 150 chars accepted, 151st per Rule 5, renders intact."""
    _labels("149202", "MEDIA-MCHUB-TC-148", "Card Description character limit (150)")
    _limit_case(qac, real_guard, "149202", "cardDescription", 150, D150_EN, D151_EN, D150_AR, "desc")


@pytest.mark.tc_149230
@pytest.mark.functional_low
def test_png_icon_is_shown_on_public_card(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-176 — valid PNG icon stored and rendered in the icon tile."""
    _labels("149230", "MEDIA-MCHUB-TC-176", "PNG icon reaches the public card")
    sessions, admin, ref = real_session(qac, real_guard)
    pending = {}
    result = guarded_edit(real_guard, admin, ref, {"icon_file": ICON_PNG, "icon_stem": "qctest-qac-icon"}, "149230",
                          prepare=lambda a: pending.update(block=a.upload_block_text(K_ICON)))
    uploaded = admin.last_uploaded_name
    assert uploaded.split(".")[0] in pending["block"], f"the PNG is not shown as pending: {pending['block']!r}"
    assert result["went_through"], f"the PNG edit was refused: {result['evidence']}"
    icon = stored(admin, ref)["icon"]
    assert icon.startswith("qctest-qac-icon") and icon.endswith(".png"), f"Current file reads {icon!r}"
    visitor = _hub(sessions)
    cards = public_until(visitor, lambda c: uploaded.split(".")[0] in find(c, ref.code).get("icon_url", ""),
                         "card icon = PNG", "149230", budget=False)
    url = find(cards, ref.code)["icon_url"]
    status = visitor.head_status(url if url.startswith("http") else visitor.page.url.split("/web/")[0] + url)
    assert status == 200, f"the public icon URL answers {status}"


@pytest.mark.tc_149232
@pytest.mark.functional_low
def test_jpg_icon_is_blocked(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-178 — JPG icon blocked with 'Unsupported file type or size.'"""
    _labels("149232", "MEDIA-MCHUB-TC-178", "JPG icon is blocked")
    sessions, admin, ref = real_session(qac, real_guard)
    svg_before = real_guard.snapshots[ref.code]["icon"]["name"]
    real_guard.check_before_edit(ref.code)
    try:
        admin.open_entry(ref.code)
        upload = admin.attempt_upload(K_ICON, ICON_JPG, "qctest-qac-icon")
        attach("JPG upload attempt", upload)
        save_result = save(admin, ROLE_EDITOR, True) if upload.get("attached") else None
    finally:
        real_guard.record_written(ref.code)
    shot = admin.evidence("149232_after_jpg")
    blob = " ".join([str(upload.get("errors")), upload.get("picker_text", ""), upload.get("field_text", ""),
                     (save_result or {}).get("messages", "")])
    icon_after = stored(admin, ref)["icon"]
    assert icon_after == svg_before, f"PRODUCT: the JPG replaced the icon ({svg_before!r} -> {icon_after!r})"
    if "Unsupported file type or size." not in blob:
        record_finding("149232", "WORDING", expected="Unsupported file type or size.", shown=blob[:400], screenshot=shot)
    public_until(_hub(sessions), lambda c: svg_before.split(".")[0] in find(c, ref.code).get("icon_url", ""),
                 "card still shows its SVG", "149232", budget=False)


def _position_unchanged(sessions, ref, tc):
    cards = public_until(_hub(sessions), lambda c: bool(find(c, ref.code)), "card present", tc, budget=False)
    assert find(cards, ref.code)["index"] == 0, f"{ref.title!r} is card #{find(cards, ref.code)['index'] + 1}, not #1"


@pytest.mark.tc_149248
@pytest.mark.functional_low
def test_empty_display_order_is_refused(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-194 — empty Display Order refused; public position unchanged."""
    _labels("149248", "MEDIA-MCHUB-TC-194", "Empty Display Order is refused")
    sessions, admin, ref = real_session(qac, real_guard)
    result = guarded_edit(real_guard, admin, ref, {}, "149248", prepare=lambda a: a.clear_number("displayOrder"))
    assert result["filled"]["displayOrder"] == ""
    _refused(result, "an empty Display Order")
    assert stored(admin, ref)["displayOrder"] == "100"
    _position_unchanged(sessions, ref, "149248")


@pytest.mark.tc_149249
@pytest.mark.functional_low
def test_zero_and_negative_display_order_are_refused(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-195 — Display Order 0 and -100 refused (positive integer)."""
    _labels("149249", "MEDIA-MCHUB-TC-195", "Display Order 0 / -100 refused")
    sessions, admin, ref = real_session(qac, real_guard)
    outcomes = {}
    for value in ("0", "-100"):
        result = guarded_edit(real_guard, admin, ref, {"displayOrder": value}, f"149249_{value}")
        outcomes[value] = {"went_through": result["went_through"], "stored": stored(admin, ref)["displayOrder"],
                           "messages": result["messages"]}
    attach("outcomes", outcomes)
    accepted = {v: o for v, o in outcomes.items() if o["went_through"]}
    assert not accepted, f"PRODUCT: Display Order accepted non-positive values: {accepted}"
    _position_unchanged(sessions, ref, "149249")


@pytest.mark.tc_149260
@pytest.mark.functional_high
def test_display_order_change_reorders_public_cards(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-206 — swapping Display Orders (100 <-> 200) reorders the hub (real cards, restored)."""
    _labels("149260", "MEDIA-MCHUB-TC-206", "Display Order reorders the public hub")
    sessions, admin, first = real_session(qac, real_guard, CARD01)
    second = real_guard.take(CARD02)
    visitor = _hub(sessions)
    public_until(visitor, lambda c: find(c, CARD01).get("index") == 0 and find(c, CARD02).get("index") == 1,
                 "Photo Gallery before Video Gallery", "149260", budget=False)
    r1 = guarded_edit(real_guard, admin, first, {"displayOrder": 200}, "149260_a")
    r2 = guarded_edit(real_guard, admin, second, {"displayOrder": 100}, "149260_b")
    assert r1["went_through"] and r2["went_through"], f"the order change was refused: {r1['evidence']} {r2['evidence']}"
    started = monotonic()
    admin.open_list_all()
    assert admin.row_status_of(first) == STATUS_PUBLISHED
    public_until(visitor, lambda c: find(c, CARD02).get("index") == 0 and find(c, CARD01).get("index") == 1,
                 "Video Gallery before Photo Gallery", "149260", started=started)


@pytest.mark.tc_149261
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
def test_inactive_card_is_hidden_and_grid_reflows(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-207 — unticking Active Status hides the card; re-ticking restores it (real card, restored)."""
    _labels("149261", "MEDIA-MCHUB-TC-207", "Active Status hides / restores the public card")
    sessions, admin, ref = real_session(qac, real_guard)
    visitor = _hub(sessions)
    before = public_until(visitor, lambda c: find(c, ref.code).get("index") == 0, "card shown", "149261", budget=False)
    result = guarded_edit(real_guard, admin, ref, {"activeStatus": False}, "149261_untick")
    assert result["went_through"], f"unticking Active Status was refused: {result['evidence']}"
    started = monotonic()
    admin.open_list_all()
    badge = admin.row_status_of(ref)
    after = public_until(visitor, lambda c: not find(c, ref.code), "card hidden", "149261", started=started)
    assert [c["erc"] for c in after] == [c["erc"] for c in before if c["erc"] != ref.code], "remaining cards changed"
    assert all(c["card"]["w"] > 0 and c["card"]["h"] > 0 for c in after), "an empty slot is rendered"
    result = guarded_edit(real_guard, admin, ref, {"activeStatus": True}, "149261_retick")
    assert result["went_through"], f"re-ticking Active Status was refused: {result['evidence']}"
    started = monotonic()
    public_until(visitor, lambda c: find(c, ref.code).get("index") == 0, "card back in its slot", "149261",
                 started=started)
    # User decision 2026-10-13: an unticked (inactive) published card shows the INACTIVE badge.
    assert badge.strip().upper() == "INACTIVE", f"after unticking Active Status the badge reads {badge!r}, not INACTIVE"


@pytest.mark.tc_149264
@pytest.mark.functional_low
def test_external_destination_link_navigates(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-210 — external Destination Link https://www.qcb.gov.qa."""
    _labels("149264", "MEDIA-MCHUB-TC-210", "External Destination Link navigates")
    sessions, admin, ref = real_session(qac, real_guard)
    result = guarded_edit(real_guard, admin, ref, {"destinationLink": "https://www.qcb.gov.qa"}, "149264")
    assert result["went_through"], f"the external link was refused: {result['evidence']}"
    admin.open_list_all()
    assert admin.row_status_of(ref) == STATUS_PUBLISHED
    visitor = _hub(sessions)
    public_until(visitor, lambda c: find(c, ref.code).get("href") == "https://www.qcb.gov.qa",
                 "href = https://www.qcb.gov.qa", "149264", budget=False)
    landed = visitor.follow_card(ref.code)
    attach("navigation", landed)
    assert "qcb.gov.qa" in landed["url"], f"the card opened {landed['url']!r}"


@pytest.mark.tc_149231
@pytest.mark.functional_low
def test_new_card_without_icon_is_refused(qac, real_cards):
    """MEDIA-MCHUB-TC-177 — a new card cannot be submitted without an icon."""
    _labels("149231", "MEDIA-MCHUB-TC-177", "New card without icon is refused")
    sessions, registry = qac
    admin = sessions.admin(ROLE_EDITOR)
    data = card_data("QCTEST No Icon", "QCTEST بلا أيقونة", "QCTEST card without icon.", "QCTEST بطاقة بلا أيقونة.",
                     1000, icon_file=None)
    entry, result = create(admin, registry, data, "149231")
    new_rows = [r for r in result.get("new_rows", []) if r["title"].strip() == "QCTEST No Icon"]
    assert not result["went_through"] and not new_rows, \
        f"PRODUCT: a card without an icon was created: {new_rows or result.get('editbar')}"
    blob = result["messages"] + result.get("page_text", "")
    if not ("Icon" in blob and "required" in blob.lower()):
        record_finding("149231", "WORDING", expected="'Icon' reported as required", shown=result["evidence"],
                       screenshot=result.get("screenshot"))
    visitor = sessions.visitor().open_hub()
    assert not [c for c in visitor.cards() if c["title"] == "QCTEST No Icon"]



@pytest.mark.tc_149265
@pytest.mark.functional_low
@pytest.mark.regression
def test_new_card_without_destination_link_is_blocked(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-211 — 'A destination link is required.'

    Healed 2026-10-13 (bug 149913): Add New was removed from this fixed-block
    Object, so a card can no longer be created. The same rule is exercised by
    clearing Destination Link on a real card (snapshot -> edit -> restore)."""
    _labels("149265", "MEDIA-MCHUB-TC-211", "Card without Destination Link is blocked")
    sessions, admin, ref = real_session(qac, real_guard)
    link = real_guard.snapshots[ref.code]["destinationLink"]
    result = guarded_edit(real_guard, admin, ref, {"destinationLink": ""}, "149265")
    assert result["filled"]["destinationLink"] == "", f"Destination Link was not cleared: {result['filled']}"
    _refused(result, "an empty Destination Link")
    assert stored(admin, ref)["destinationLink"] == link, "the stored Destination Link changed"
    assert message_check("149265", "A destination link is required.", result, "edit without link"), \
        f"PRODUCT: 'A destination link is required.' not shown: {result.get('messages')!r}"
    public_until(_hub(sessions), lambda c: find(c, ref.code).get("href") == link,
                 "href unchanged", "149265", budget=False)



@pytest.mark.tc_149266
@pytest.mark.functional_low
def test_whitespace_destination_link_is_blocked(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-212 — whitespace-only link treated as missing."""
    _labels("149266", "MEDIA-MCHUB-TC-212", "Whitespace Destination Link is blocked")
    sessions, admin, ref = real_session(qac, real_guard)
    link = real_guard.snapshots[ref.code]["destinationLink"]
    result = guarded_edit(real_guard, admin, ref, {"destinationLink": "   "}, "149266")
    assert result["filled"]["destinationLink"] == "   "
    _refused(result, "a whitespace-only Destination Link")
    assert stored(admin, ref)["destinationLink"] == link
    message_check("149266", "A destination link is required.", result, "whitespace link")
    public_until(_hub(sessions), lambda c: find(c, ref.code).get("href") == link,
                 "href unchanged", "149266", budget=False)


@pytest.mark.tc_149267
@pytest.mark.functional_low
def test_malformed_destination_link_is_rejected(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-213 — malformed 'htp:/qctest bad link' refused."""
    _labels("149267", "MEDIA-MCHUB-TC-213", "Malformed Destination Link is rejected")
    sessions, admin, ref = real_session(qac, real_guard)
    link = real_guard.snapshots[ref.code]["destinationLink"]
    result = guarded_edit(real_guard, admin, ref, {"destinationLink": "htp:/qctest bad link"}, "149267")
    _refused(result, "a malformed Destination Link")
    assert stored(admin, ref)["destinationLink"] == link
    visitor = _hub(sessions)
    public_until(visitor, lambda c: find(c, ref.code).get("href") == link, "href unchanged", "149267", budget=False)
    landed = visitor.follow_card(ref.code)
    assert landed["url"].split("?")[0].rstrip("/").endswith(link), f"the card navigates to {landed['url']!r}"


@pytest.mark.tc_149274
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.regression
def test_card_without_arabic_is_blocked(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-220 — 'Arabic content is required.'

    Healed 2026-10-13: Add New is removed (fixed set of six), so the rule is
    exercised by clearing the Arabic title + description of a real card under
    snapshot -> edit -> restore -> diff (real_guard)."""
    _labels("149274", "MEDIA-MCHUB-TC-220", "Card without Arabic content is blocked")
    sessions, admin, ref = real_session(qac, real_guard)
    snap = real_guard.snapshots[ref.code]
    result = guarded_edit(real_guard, admin, ref, {"cardTitle_ar": "", "cardDescription_ar": ""}, "149274")
    assert result["filled"]["cardTitle_ar"] == "", f"the Arabic title was not cleared: {result['filled']}"
    _refused(result, "a card without Arabic content")
    values = stored(admin, ref)
    assert values["cardTitle_ar"] == snap.get("cardTitle_i18n", {}).get("ar_SA", values["cardTitle_ar"])         and values["cardTitle_ar"], f"the stored Arabic title changed: {values}"
    message_check("149274", "Arabic content is required.", result, "edit without Arabic")


def _ar_ui_case(qac, tc: str, data: dict, expected: str, title: str):
    sessions, registry = qac
    admin = sessions.admin(ROLE_EDITOR)
    ids_before = admin.snapshot_ids()
    admin.open_create_form("ar")
    button = admin.submit_button_text_any()
    assert button not in ("Publish", "Submit for Review"), f"the interface is not Arabic (button {button!r})"
    admin.fill_card(dict(data, icon_any_locale=True))
    admin.click_submit_any_locale()
    result = {"went_through": admin.save_went_through(), "evidence": admin.refusal_evidence(),
              "messages": admin.all_messages_text()}
    result["page_text"] = admin.wait_body_contains((expected,), 5.0)[:3000]
    result["screenshot"] = admin.evidence(f"{tc}_ar_ui")
    new_rows = [r for r in admin.new_rows_since(ids_before) if r["title"].strip() == title]
    for row in new_rows:
        from cms.pages.media_center.mc_quick_access_card_admin_page import QacEntry  # noqa: PLC0415
        registry.track(admin.adopt(QacEntry(row["title"].strip(), row["entry_id"], row["code"])))
    attach("AR UI attempt", result)
    assert not result["went_through"] and not new_rows, f"PRODUCT: the card was created: {new_rows}"
    return result


@pytest.mark.tc_149277
@pytest.mark.functional_low
@pytest.mark.bilingual
def test_arabic_required_message_in_arabic_ui(qac, real_cards):
    """MEDIA-MCHUB-TC-223 — 'المحتوى بالعربية مطلوب.' in the AR interface."""
    _labels("149277", "MEDIA-MCHUB-TC-223", "Arabic-required message in the AR UI")
    data = card_data("QCTEST AR UI", "", "QCTEST AR UI card.", "", 1000)
    result = _ar_ui_case(qac, "149277", data, "المحتوى بالعربية مطلوب.", "QCTEST AR UI")
    message_check("149277", "المحتوى بالعربية مطلوب.", result, "AR UI, Arabic missing")


@pytest.mark.tc_149278
@pytest.mark.functional_low
@pytest.mark.bilingual
def test_destination_link_message_in_arabic_ui(qac, real_cards, real_guard):
    """MEDIA-MCHUB-TC-224 — 'رابط الوجهة مطلوب.' in the AR interface.

    Healed 2026-10-13 (bug 149913): no Add New any more; the real card is
    opened in the AR interface, its link cleared and the submit refused
    (snapshot -> edit -> restore)."""
    _labels("149278", "MEDIA-MCHUB-TC-224", "Destination-link message in the AR UI")
    sessions, admin, ref = real_session(qac, real_guard)
    link = real_guard.snapshots[ref.code]["destinationLink"]
    real_guard.check_before_edit(ref.code)
    try:
        admin.open_entry(ref.code, "ar")
        button = admin.submit_button_text_any()
        assert button not in ("Publish", "Submit for Review"), f"the interface is not Arabic (button {button!r})"
        admin.fill_card({"destinationLink": ""})
        admin.click_submit_any_locale()
        result = {"went_through": admin.save_went_through(), "evidence": admin.refusal_evidence(),
                  "messages": admin.all_messages_text()}
        result["page_text"] = admin.wait_body_contains(("رابط الوجهة مطلوب.",), 5.0)[:3000]
        result["screenshot"] = admin.evidence("149278_ar_ui")
        result["form"] = admin.form_labels_and_errors()
        attach("AR UI attempt", result)
        attach("AR red bar (verbatim)", " || ".join(result["form"]["bar"]))
    finally:
        real_guard.record_written(ref.code)
    _refused(result, "an empty Destination Link (AR UI)")
    placeholders = [t for t in result["form"]["labels"] + result["form"]["field_errors"] if "(AR)" in t]
    assert not placeholders, f"PRODUCT: AR form labels/messages still carry '(AR)': {placeholders}"
    bar = " || ".join(result["form"]["bar"])
    if "رابط الوجهة مطلوب." not in bar:
        record_finding("149278", "WORDING", context="AR red bar", expected="رابط الوجهة مطلوب.", shown=bar)
    assert message_check("149278", "رابط الوجهة مطلوب.", result, "AR UI, link missing"), \
        f"PRODUCT: 'رابط الوجهة مطلوب.' not shown: {result.get('messages')!r}"
    admin.open_entry(ref.code)
    assert stored(admin, ref)["destinationLink"] == link, "the stored Destination Link changed"


@pytest.mark.tc_149283
@pytest.mark.edge
def test_card_hidden_when_destination_page_unpublished():
    """MEDIA-MCHUB-TC-229 — card hidden while its destination page is unpublished."""
    _labels("149283", "MEDIA-MCHUB-TC-229", "Card hidden while destination page is unpublished")
    pytest.skip("BLOCKED: no disposable destination PAGE can be made through Object Authoring — pages are "
                "Liferay layouts (off-limits to automation), news articles render on the shared "
                "/web/qatar-chamber/news-detail?id=N page (no /news/<slug> page exists to unpublish), and "
                "unpublishing a real page is forbidden.")
