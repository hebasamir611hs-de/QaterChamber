"""
cms/tests/home_services/test_our_services_p34_control_panel.py — PBI 129371
(QC-HOME-003 — Our Services), suite 134449: the P3/P4 cases classed High /
Medium for the 2026-10-15 Phase 3 run (PBI running rules, rule 2). Low and
character-limit cases are not scripted. The View All label/URL cases
(135380-135391) are not scripted either: no such field exists live (see
test_our_services_p12_control_panel.py::test_view_all_url_field_present).

Records and rules as in the P1/P2 module:
  - Section field cases write to the ONE live section record
    (QCDEMO-129371-OSS-DEFAULT): snapshot first, every write logged, snapshot
    restored and the record left Published in `finally`. The Published record's
    fields are edited in place (no unpublish), so the section stays on the
    live Home Page throughout.
  - Card and empty/whitespace tab cases use disposable QCTEST records; a card
    that reached Published is unpublished in `finally`; nothing is deleted.
  - 135392 / 135396 name the real Membership tab (QCDEMO-129371-FILTER_TAB-02):
    its label is changed, checked on the live tab bar, and restored.
  - 135404: Display Order 50 (the case says 1) — below the real cards' 100+,
    so the QCTEST card sorts first, as the case expects, and is unpublished
    right after.
  - 135378: 3.5 MB — up to 3 MB accepted is the project's tolerance.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import allure
import pytest

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.home_services.our_services_admin_page import (
    OSS_ENTRY_CODE,
    FilterTabAdminPage as Tab,
    OurServicesSectionAdminPage as Section,
    ServiceCardAdminPage as Card,
    default_png,
)
from cms.tests import authoring_checks as ac
from config.settings import control_panel_url
from cms.tests.home_services.test_our_services_p12_control_panel import (
    OSS,
    _cards,
    _edit_section,
    _poll,
    _publish_card,
    _retire_card,
    _section_restore,
)
from cms.tests.live_write_guard import LiveRecord, log_live_write
from web.pages.home_services.home_services_page import HomeServicesPage

pytestmark = [pytest.mark.control_panel, pytest.mark.pbi_129371]

MEMBERSHIP_TAB = "QCDEMO-129371-FILTER_TAB-02"
MEMBERSHIP_REC = LiveRecord("filter-tab", MEMBERSHIP_TAB, "Filter Tab 'Membership' (real)")


def _big_png(tag: str) -> str:
    from PIL import Image

    path = Path(tempfile.gettempdir()) / f"QCTEST-{tag}.png"
    Image.frombytes("RGB", (1100, 1100), os.urandom(1100 * 1100 * 3)).save(path, "PNG")
    assert path.stat().st_size > 3 * 1024 * 1024
    return str(path)


def _bad_file(tag: str) -> str:
    path = Path(tempfile.gettempdir()) / f"QCTEST-{tag}.exe"
    path.write_bytes(b"MZ" + os.urandom(2048))
    return str(path)


# ---------------------------------------------------------------------------
# section preview + field cases (the ONE live record)
# ---------------------------------------------------------------------------
@allure.title("Preview shows the section as it will appear, without affecting the live page")
@pytest.mark.functional_high
@pytest.mark.tc_135347
def test_section_preview(page):
    """Account: Editor. Opens the section row's Preview (a staff surface) and
    reads Tag / Heading back from it. Nothing is saved."""
    section = Section(page)
    section.sign_in(ROLE_EDITOR)
    section.open_entry_by_code(OSS_ENTRY_CODE)
    snap = section.snapshot()
    section.open_entries_list()
    url = section.row_preview_url_by_code(OSS_ENTRY_CODE)
    assert url, "the section row offers no Preview link"
    section.open(url)
    page.wait_for_load_state("domcontentloaded")
    body = page.locator("body").inner_text()
    for key in ("section_tag:en", "section_heading:en"):
        assert snap[key] and snap[key] in body, f"Preview does not render {key} {snap[key]!r}"
    assert section.list_status() == STATUS_PUBLISHED, "Preview changed the live record's status"


def _section_value(page, tc: int, key: str, loc: str, value: str, expect_saved: bool) -> None:
    section = Section(page).open_record(ROLE_EDITOR)
    snap = section.snapshot()
    try:
        _edit_section(section)
        section.fill(key, value, locale=loc)
        log_live_write(OSS, f"{key}:{loc}", value, tc, action="publish" if expect_saved else "attempt",
                       note=f"snapshot {snap}")
        section.submit_for_review()
        if expect_saved:
            assert not section.refusal_visible(2000), f"valid {key} ({loc}) was refused: {section.refusal_text()}"
            assert section.list_status() == STATUS_PUBLISHED, "the section is not Published after the save"
            section.open_entry_by_code(OSS_ENTRY_CODE)
            assert section.value(key, loc) == value, f"{key} ({loc}) stored {section.value(key, loc)!r}"
        else:
            refused = section.refusal_visible()
            section.open_entry_by_code(OSS_ENTRY_CODE)
            stored = section.value(key, loc)
            assert refused and stored == snap[f"{key}:{loc}"], (
                f"{key} ({loc}) = {value!r} was not refused (refusal seen: {refused}; stored {stored!r})"
            )
    finally:
        _section_restore(section, snap, tc)


SECTION_VALID = [
    pytest.param("section_tag", "en", "QCTEST Services", id="135354", marks=pytest.mark.tc_135354),
    pytest.param("section_tag", "ar", "خدمات QCTEST", id="135358", marks=pytest.mark.tc_135358),
    pytest.param("section_heading", "en", "QCTEST Services We Provide", id="135362", marks=pytest.mark.tc_135362),
    pytest.param("section_heading", "ar", "الخدمات التي نقدمها QCTEST", id="135366", marks=pytest.mark.tc_135366),
    pytest.param("section_description", "en", "QCTEST description of the services the Chamber offers.",
                 id="135370", marks=pytest.mark.tc_135370),
    pytest.param("section_description", "ar", "وصف QCTEST للخدمات التي تقدمها الغرفة.",
                 id="135373", marks=pytest.mark.tc_135373),
]


@allure.title("Valid section field value saves and persists")
@pytest.mark.xdist_group("our_services_section")
@pytest.mark.parametrize("key,loc,value", SECTION_VALID)
def test_section_valid_value_saved(page, request, key, loc, value):
    _section_value(page, int(request.node.callspec.id), key, loc, value, expect_saved=True)


SECTION_REFUSED = [
    pytest.param("section_tag", "en", "", id="135355", marks=pytest.mark.tc_135355),
    pytest.param("section_tag", "en", "    ", id="135357", marks=pytest.mark.tc_135357),
    pytest.param("section_tag", "ar", "", id="135359", marks=pytest.mark.tc_135359),
    pytest.param("section_tag", "ar", "    ", id="135361", marks=pytest.mark.tc_135361),
    pytest.param("section_heading", "en", "", id="135363", marks=pytest.mark.tc_135363),
    pytest.param("section_heading", "en", "    ", id="135365", marks=pytest.mark.tc_135365),
    pytest.param("section_heading", "ar", "", id="135367", marks=pytest.mark.tc_135367),
    pytest.param("section_heading", "ar", "    ", id="135369", marks=pytest.mark.tc_135369),
]


@allure.title("Empty or whitespace-only mandatory section field is refused")
@pytest.mark.xdist_group("our_services_section")
@pytest.mark.parametrize("key,loc,value", SECTION_REFUSED)
def test_section_empty_value_refused(page, request, key, loc, value):
    _section_value(page, int(request.node.callspec.id), key, loc, value, expect_saved=False)


# ---------------------------------------------------------------------------
# service cards (disposable)
# ---------------------------------------------------------------------------
@allure.title("Unsupported image format is refused for the thumbnail")
@pytest.mark.tc_135377
def test_thumbnail_unsupported_format_refused(page):
    ac.check_file_refused(page, Card, 135377, "thumbnail", _bad_file("135377-thumb"))


@allure.title("Thumbnail over the size limit is refused")
@pytest.mark.tc_135378
def test_thumbnail_over_size_refused(page):
    ac.check_file_refused(page, Card, 135378, "thumbnail", _big_png("135378-thumb-big"))


@allure.title("Card without a thumbnail is refused")
@pytest.mark.tc_135379
def test_card_without_thumbnail_refused(page):
    ac.check_empty_refused(page, Card, 135379, "thumbnail")


@allure.title("Invalid Service Card Redirect URL is refused")
@pytest.mark.tc_135401
def test_invalid_redirect_url_refused(page):
    """PBI running rules, rule 17: an accepted malformed link is not a bug on
    this project — a failure here is reviewed, not filed."""
    ac.check_value_refused(page, Card, 135401, "redirect_url", "not-a-url", short="badurl")


@allure.title("Empty Service Card Redirect URL is refused")
@pytest.mark.tc_135403
def test_empty_redirect_url_refused(page):
    ac.check_empty_refused(page, Card, 135403, "redirect_url")


@allure.title("Valid positive Display Order saves and controls card sort position")
@pytest.mark.tc_135404
def test_display_order_controls_sort(page, browser):
    admin = Card(page)
    title = ac.run_title(135404, "order-first")
    ctx, anon = ac._anon_page(browser)
    try:
        _publish_card(admin, title, extra={"display_order": "50", "assigned_tab": "Information"})
        home = HomeServicesPage(anon)

        def _first() -> bool:
            home.open_home()
            home.open_tab("Information")
            cards = [c for c in _cards(home) if c]
            return bool(cards) and cards[0] == title

        assert _poll(_first), f"{title!r} (Display Order 50) is not first under Information"
    finally:
        ac._close(ctx)
        _retire_card(admin, title, 135404)


DISPLAY_BAD = [
    pytest.param("-1", id="135405", marks=pytest.mark.tc_135405),
    pytest.param("0", id="135406", marks=pytest.mark.tc_135406),
    pytest.param("abc", id="135407", marks=pytest.mark.tc_135407),
]


@allure.title("Invalid card Display Order is refused")
@pytest.mark.parametrize("bad", DISPLAY_BAD)
def test_invalid_display_order_refused(page, request, bad):
    ac.check_value_refused(page, Card, int(request.node.callspec.id), "display_order", bad, short="order")


@allure.title("Valid card icon uploads and displays on the live card")
@pytest.mark.tc_135410
def test_card_icon_displays(page, browser):
    admin = Card(page)
    title = ac.run_title(135410, "icon")
    icon = default_png("QCTEST-135410icon.png", size=(64, 64))
    ctx, anon = ac._anon_page(browser)
    try:
        _publish_card(admin, title, files={"icon": icon})
        home = HomeServicesPage(anon)
        assert _poll(lambda: (home.open_home(), title in _cards(home))[1]), f"{title!r} never reached the Home Page"
        card = anon.locator(f"{home.CARD}:has({home.CARD_TITLE}:text-is('{title}'))").first
        srcs = [i.get_attribute("src") or "" for i in card.locator("img").all()]
        # Healed 2026-10-15: every upload of this card is named after its
        # QCTEST title, so the thumbnail AND the icon both carry "135410";
        # the card must render both, and each must serve an image.
        hit = [s for s in srcs if "QCTEST-135410" in s]
        assert len(hit) >= 2, f"the card does not render both uploads (thumbnail + icon): {srcs}"
        for src in hit:
            resp = anon.request.get(src if src.startswith("http") else control_panel_url(src))
            assert resp.ok and resp.headers.get("content-type", "").startswith("image/"), f"{src} serves no image"
    finally:
        ac._close(ctx)
        _retire_card(admin, title, 135410)


@allure.title("Card without an icon is refused")
@pytest.mark.tc_135411
def test_card_without_icon_refused(page):
    ac.check_empty_refused(page, Card, 135411, "icon")


# ---------------------------------------------------------------------------
# filter tabs
# ---------------------------------------------------------------------------
def _tab_status(tab: Tab) -> str:
    """Status of the Membership row, found by its Edit link's entry code —
    the Entry column shows the (changing) label, not the code (healed
    2026-10-15: a code-text lookup read "" and the restore tried to
    re-publish a Published row)."""
    from cms.pages.components.object_authoring_page import normalize_status

    tab.open_entries_list()
    row = tab.page.locator(f"{tab.ENTRIES_TABLE_ROW}:has(a[href*='editEntry={MEMBERSHIP_TAB}'])").first
    return normalize_status(row.locator("td").nth(1).inner_text()) if row.count() else ""


def _tab_label_live(page, browser, tc: int, loc: str) -> None:
    """Change the real Membership tab's label, see it on the live tab bar,
    put it back (logged; left Published)."""
    tab = Tab(page)
    tab.sign_in(ROLE_EDITOR)
    tab.open_entry_by_code(MEMBERSHIP_TAB)
    before = {"en": tab.value("tab_label", "en"), "ar": tab.value("tab_label", "ar")}
    new = f"{before[loc]} QCTEST"
    ctx, anon = ac._anon_page(browser)
    try:
        tab.fill("tab_label", new, locale=loc)
        log_live_write(MEMBERSHIP_REC, f"Tab Label:{loc}", new, tc, action="publish", note=f"was {before}")
        tab.submit_for_review()
        assert _tab_status(tab) == STATUS_PUBLISHED, "tab not Published after save"
        home = HomeServicesPage(anon)

        def _shown() -> bool:
            home.open_home_arabic() if loc == "ar" else home.open_home()
            return any(t.strip() == new for t in home.tab_texts())

        assert _poll(_shown), f"the live tab bar never showed {new!r}"
    finally:
        ac._close(ctx)
        tab.open_entry_by_code(MEMBERSHIP_TAB)
        if tab.value("tab_label", loc) != before[loc]:
            tab.fill("tab_label", before[loc], locale=loc)
            log_live_write(MEMBERSHIP_REC, f"Tab Label:{loc}", before[loc], tc, action="publish", note="restore")
            tab.submit_for_review()
        final = _tab_status(tab)
        if final != STATUS_PUBLISHED:
            log_live_write(MEMBERSHIP_REC, "<workflow>", STATUS_PUBLISHED, tc, action="publish", note="restore")
            row_label = before["en"]
            tab.publish_entry(row_label)


@allure.title("Valid Tab Label (EN) saves and shows on the live tab bar")
@pytest.mark.xdist_group("filter_tab_membership")
@pytest.mark.tc_135392
def test_tab_label_en_shows_live(page, browser):
    _tab_label_live(page, browser, 135392, "en")


@allure.title("Valid Tab Label (AR) saves and shows on the live tab bar")
@pytest.mark.xdist_group("filter_tab_membership")
@pytest.mark.tc_135396
def test_tab_label_ar_shows_live(page, browser):
    _tab_label_live(page, browser, 135396, "ar")


TAB_REFUSED = [
    pytest.param("en", "", id="135393", marks=pytest.mark.tc_135393),
    pytest.param("en", "    ", id="135395", marks=pytest.mark.tc_135395),
    pytest.param("ar", "", id="135397", marks=pytest.mark.tc_135397),
    pytest.param("ar", "    ", id="135399", marks=pytest.mark.tc_135399),
]


@allure.title("Empty or whitespace-only Tab Label is refused")
@pytest.mark.parametrize("loc,value", TAB_REFUSED)
def test_tab_label_refused(page, request, loc, value):
    """A disposable QCTEST tab: EN carries the QCTEST name unless EN is the
    side under test (then the record has no findable title and the refusal
    alone is the signal)."""
    tc = int(request.node.callspec.id)
    admin = Tab(page)
    title = ac.run_title(tc, "tab")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill("display_order", "9900")
        if loc == "en":
            admin.fill("tab_label", value)
            admin.fill("tab_label", f"{title} AR", locale="ar")
            log_live_write(LiveRecord("filter-tab", title, "disposable QCTEST record"), "Tab Label:en",
                           repr(value), tc, action="attempt")
            admin.submit_for_review()
            assert admin.refusal_visible(), f"Tab Label (EN) = {value!r}: Submit raised no refusal"
            title = None
        else:
            admin.fill("tab_label", title)
            admin.fill("tab_label", value, locale="ar")
            log_live_write(LiveRecord("filter-tab", title, "disposable QCTEST record"), "Tab Label:ar",
                           repr(value), tc, action="attempt")
            ac._submit_and_expect_refusal(admin, title, f"Tab Label (AR) = {value!r}")
    finally:
        if title:
            ac.dispose(admin, title, tc)


# ---------------------------------------------------------------------------
# remaining Low cases (QA lead, 2026-10-15: run every CMS case still Not Executed)
# ---------------------------------------------------------------------------
OPTIONAL_EMPTY = [
    pytest.param("en", id="135371", marks=pytest.mark.tc_135371),
    pytest.param("ar", id="135374", marks=pytest.mark.tc_135374),
]


@allure.title("Section Description can be saved empty (optional)")
@pytest.mark.xdist_group("our_services_section")
@pytest.mark.parametrize("loc", OPTIONAL_EMPTY)
def test_section_description_optional_empty(page, request, loc):
    """Writes the ONE live section record (Description emptied on one side),
    restores the snapshot and leaves it Published in finally."""
    tc = int(request.node.callspec.id)
    section = Section(page).open_record(ROLE_EDITOR)
    snap = section.snapshot()
    try:
        _edit_section(section)
        section.fill("section_description", "", locale=loc)
        log_live_write(OSS, f"section_description:{loc}", "", tc, action="publish", note=f"snapshot {snap}")
        section.submit_for_review()
        assert not section.refusal_visible(3000), f"empty optional Description ({loc}) was refused: {section.refusal_text()}"
        assert section.list_status() == STATUS_PUBLISHED, "section not Published after saving an empty Description"
        section.open_entry_by_code(OSS_ENTRY_CODE)
        assert section.value("section_description", loc) == "", "the empty Description was not stored"
    finally:
        _section_restore(section, snap, tc)


@allure.title("Discarding unsaved section changes keeps the last saved values")
@pytest.mark.tc_135412
def test_section_discard_unsaved_changes(page):
    """Nothing is saved: edit the Tag, leave the page without saving, reopen."""
    section = Section(page).open_record(ROLE_EDITOR)
    before = section.value("section_tag", "en")
    page.once("dialog", lambda d: d.accept())
    section.fill("section_tag", "QCTEST-135412 unsaved")
    section.open_entries_list()
    section.open_entry_by_code(OSS_ENTRY_CODE)
    assert section.value("section_tag", "en") == before, "an unsaved change was kept"
    assert section.list_status() == STATUS_PUBLISHED
