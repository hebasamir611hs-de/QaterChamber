"""
web/tests/announcement_popup/test_announcement_popup_web.py

Web-platform cases for PBI 131032 ("Global Announcement Popup"), suite 140386 —
11 approved Automation cases: 141403-141408, 141410, 141415-141418 (141409 is
Manual, not here).

These run against the REAL live component (no API mocking). The popup is not
published on qcdev today (GET /o/qc-newsletter/announcement-popups ->
{"items": [], "status": "ok"}), so every test first reads the feed and skips
with "No published announcement on qcdev (API items: [])" — recorded as
Blocked on Azure. The moment an announcement is published, the tests run
unchanged.

Navigation deliberately bypasses BasePage.open()'s global overlay dismissal
(AnnouncementPopupPage.open_in_scope uses page.goto) — BasePage is unchanged.

Case-specific seeded values (Title 'Ramadan Working Hours Notice', CTA 'Learn
More', the Arabic title, the bold/link description) are TEST DATA: when the
live item carries different content the difference is reported as a note and
the product behaviour (the popup renders what is configured) is asserted
against the live item's own fields.
"""

import re

import allure
import pytest

from web.pages.announcement_popup.announcement_popup_page import AnnouncementPopupPage

PBI = "131032"
ARABIC = re.compile(r"[؀-ۿ]")
TAP = 44.0
SKIP_REASON = "No published announcement on qcdev (API items: [])"

pytestmark = [pytest.mark.web, pytest.mark.pbi_131032, pytest.mark.global_]


class _Check:
    def __init__(self, title):
        self.title, self.deviations, self.notes = title, [], []

    def truthy(self, label, condition, expected, actual):
        if not condition:
            self.deviations.append(f"{label}: expected {expected!r}, got {actual!r}")

    def equals(self, label, actual, expected):
        self.truthy(label, actual == expected, expected, actual)

    def test_data(self, label, expected, actual):
        if expected != actual:
            self.notes.append(f"TEST DATA — {label}: expected {expected!r}, got {actual!r}")

    def assert_clean(self):
        if self.notes:
            allure.attach("\n".join(self.notes), "notes (test data)", allure.attachment_type.TEXT)
        assert not self.deviations, f"{self.title}: {len(self.deviations)} deviation(s):\n  - " + "\n  - ".join(self.deviations)


def _live_item(page) -> tuple:
    ann = AnnouncementPopupPage(page)
    items = ann.published_items()
    if not items:
        pytest.skip(SKIP_REASON)
    return ann, items[0]


def _meta(tc, title, story, severity=allure.severity_level.NORMAL):
    def deco(fn):
        for d in (allure.label("testcase", tc), allure.label("pbi", PBI), allure.title(title),
                  allure.severity(severity), allure.story(story), allure.feature("Global Announcement Popup"),
                  allure.epic("Global")):
            fn = d(fn)
        return fn
    return deco


C = allure.severity_level.CRITICAL


def _renders_config(check: _Check, ann: AnnouncementPopupPage, item: dict, ar: bool = False):
    title = (item.get("titleAr") if ar else None) or item.get("titleEn") or ""
    check.equals("title renders the configured value", ann.text_of(ann.TITLE), title.strip())
    check.truthy("description rendered", bool(ann.text_of(ann.DESC)), "non-empty", ann.text_of(ann.DESC))
    label = ((item.get("ctaLabelAr") if ar else None) or item.get("ctaLabelEn") or "").strip()
    if label and item.get("ctaUrl"):
        check.equals("CTA label", ann.text_of(ann.CTA), label)
        check.equals("CTA URL", ann.attribute(ann.CTA, "href"), item["ctaUrl"])
    check.truthy("Close (×) control visible", ann.count(ann.CLOSE) == 1 and ann.box(ann.CLOSE) is not None, "visible", None)


def _layout(check: _Check, ann: AnnouncementPopupPage):
    vp = ann.viewport()
    card = ann.box(ann.CARD)
    check.truthy("popup inside the viewport", card and card["x"] >= 0 and card["x"] + card["width"] <= vp["w"] + 1,
                 f"0..{vp['w']}px", card)
    check.truthy("no horizontal overflow", ann.horizontal_overflow_px() <= 0, "0px", ann.horizontal_overflow_px())
    check.equals("no clipped popup text", ann.clipped_in_popup(), [])
    return card, vp


def _dismiss(check: _Check, ann: AnnouncementPopupPage):
    ann.close_popup()
    check.equals("popup removed after Close", ann.count(ann.ROOT), 0)


# ---------------------------------------------------------------------------
@_meta("141403", "Popup renders Title, Description, CTA and Close on page load (EN, desktop)", "Content", C)
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.uat
@pytest.mark.tc_141403
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_popup_renders_elements_en(page):
    """Azure TC 141403 | PBI 131032 — EN 1920x1080: centred popup with title, rich description, CTA, Close."""
    ann, item = _live_item(page)
    check = _Check("TC 141403")
    ann.open_in_scope(item)
    check.test_data("seeded title", "Ramadan Working Hours Notice", (item.get("titleEn") or "").strip())
    check.test_data("seeded CTA label", "Learn More", (item.get("ctaLabelEn") or "").strip())
    _renders_config(check, ann, item)
    card, vp = _layout(check, ann)
    if card:
        cx = card["x"] + card["width"] / 2
        check.truthy("popup horizontally centred", abs(cx - vp["w"] / 2) <= 2, vp["w"] / 2, cx)
    check.assert_clean()


@_meta("141404", "Popup renders correctly in Arabic with RTL layout", "Bilingual", C)
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.uat
@pytest.mark.tc_141404
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_popup_arabic_rtl(page):
    """Azure TC 141404 | PBI 131032 — /ar: Arabic title/description, right-aligned RTL, Close/CTA mirrored."""
    ann, item = _live_item(page)
    check = _Check("TC 141404")
    ann.open_in_scope(item, locale="ar")
    check.test_data("seeded Arabic title", "إشعار ساعات عمل رمضان", (item.get("titleAr") or "").strip())
    check.equals("overlay dir", ann.attribute(ann.ROOT, "dir"), "rtl")
    check.truthy("Arabic title", bool(ARABIC.search(ann.text_of(ann.TITLE))), "Arabic", ann.text_of(ann.TITLE))
    check.truthy("Arabic description", bool(ARABIC.search(ann.text_of(ann.DESC))), "Arabic", ann.text_of(ann.DESC)[:60])
    st = ann.style(ann.TITLE, ("direction", "text-align"))
    check.truthy("title right-aligned RTL", st["direction"] == "rtl" and st["text-align"] in ("start", "right"),
                 "rtl/right", st)
    card, close = ann.box(ann.CARD), ann.box(ann.CLOSE)
    if card and close:
        check.truthy("Close mirrored to the left side", close["x"] + close["width"] / 2 < card["x"] + card["width"] / 2,
                     "left half of the card", close)
    check.equals("no clipped Arabic text", ann.clipped_in_popup(), [])
    check.assert_clean()


@_meta("141405", "Popup is responsive and dismissible on a mobile viewport", "Responsive")
@pytest.mark.ui
@pytest.mark.tc_141405
@pytest.mark.parametrize("page", [{"viewport": (375, 667), "auth": False}], indirect=True)
def test_popup_mobile_responsive(page):
    """Azure TC 141405 | PBI 131032 — 375x667: no overflow/clipping, Close >= 44x44, dismisses on tap, page usable."""
    ann, item = _live_item(page)
    check = _Check("TC 141405")
    ann.open_in_scope(item)
    _layout(check, ann)
    close = ann.box(ann.CLOSE)
    check.truthy("Close tap target >= 44x44", close and close["width"] >= TAP and close["height"] >= TAP, ">= 44x44", close)
    _dismiss(check, ann)
    check.truthy("page not scroll-locked after close", not ann.page_is_scroll_locked(), "unlocked", "locked")
    check.assert_clean()


@_meta("141406", "Popup is responsive on a tablet viewport", "Responsive")
@pytest.mark.ui
@pytest.mark.tc_141406
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_popup_tablet_responsive(page):
    """Azure TC 141406 | PBI 131032 — 768x1024: proportioned layout, no overlap, CTA label not truncated."""
    ann, item = _live_item(page)
    check = _Check("TC 141406")
    ann.open_in_scope(item)
    _layout(check, ann)
    parts = [ann.box(l) for l in (ann.TITLE, ann.DESC, ann.ACTIONS) if ann.count(l)]
    for i in range(len(parts) - 1):
        check.truthy(f"popup block {i + 1}/{i + 2} no overlap", parts[i]["y"] + parts[i]["height"] <= parts[i + 1]["y"] + 1,
                     "stacked", (parts[i], parts[i + 1]))
    check.assert_clean()


@_meta("141407", "Popup renders without a CTA button when no CTA is configured", "Content")
@pytest.mark.ui
@pytest.mark.tc_141407
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_popup_without_cta(page):
    """Azure TC 141407 | PBI 131032 — needs a published item with NO CTA label/URL; skips otherwise."""
    ann, item = _live_item(page)
    if item.get("ctaLabelEn") and item.get("ctaUrl"):
        pytest.skip("Live announcement has a CTA configured; this case needs a no-CTA configuration (CMS)")
    check = _Check("TC 141407")
    ann.open_in_scope(item)
    check.equals("no CTA button", ann.count(ann.CTA), 0)
    check.equals("no empty CTA slot", ann.count(ann.ACTIONS), 0)
    check.truthy("title, description and Close shown", bool(ann.text_of(ann.TITLE)) and bool(ann.text_of(ann.DESC))
                 and ann.count(ann.CLOSE) == 1, True, False)
    check.assert_clean()


@_meta("141408", "Close control shows hover and focus states and is keyboard-dismissible", "Interaction")
@pytest.mark.ui
@pytest.mark.tc_141408
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_close_hover_focus_escape(page):
    """Azure TC 141408 | PBI 131032 — hover style change, visible :focus-visible ring after Tab, Escape dismisses."""
    ann, item = _live_item(page)
    check = _Check("TC 141408")
    ann.open_in_scope(item)
    props = ("background-color", "color", "border-color", "box-shadow", "opacity", "transform")
    before = ann.style(ann.CLOSE, props)
    ann.hover(ann.CLOSE)
    after = ann.style(ann.CLOSE, props)
    check.truthy("hover style change", before != after, "a style change on hover", before)
    check.truthy("Tab reaches the Close control", ann.tab_to_close(), True, False)
    focus = ann.style(ann.CLOSE, ("outline-style", "outline-width", "box-shadow"))
    check.truthy("visible focus outline/ring", ann.focus_visible(ann.CLOSE) and (
        focus["outline-style"] != "none" or focus["box-shadow"] != "none"), "outline or ring", focus)
    ann.press("Escape")
    check.truthy("Escape dismisses the popup", ann.wait_detached(), "removed", "still present")
    check.assert_clean()


@_meta("141410", "Closing the popup does not block scrolling or interaction with the page", "Interaction", C)
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.tc_141410
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_close_does_not_block_page(page):
    """Azure TC 141410 | PBI 131032 — after Close: no overlay in DOM, page scrolls, a page link responds."""
    ann, item = _live_item(page)
    check = _Check("TC 141410")
    ann.open_in_scope(item)
    _dismiss(check, ann)
    check.truthy("page scrolls after close", ann.scroll_by(600) > 0, "scrollY changed", 0)
    before = ann.current_url()
    check.truthy("a page link responds to click", ann.click_first_page_link() != before, "navigated", before)
    check.assert_clean()


@_meta("141415", "Rich-text description formatting (bold, link) renders on the live popup", "Content")
@pytest.mark.ui
@pytest.mark.tc_141415
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_rich_text_description(page):
    """Azure TC 141415 | PBI 131032 — bold text rendered bold and the link a real hyperlink, no raw markup."""
    ann, item = _live_item(page)
    check = _Check("TC 141415")
    ann.open_in_scope(item)
    text = ann.text_of(ann.DESC)
    check.truthy("no raw HTML/markdown in the description", not re.search(r"<\/?\w+|\*\*", text), "rendered text", text[:80])
    check.truthy("bold text rendered", ann.count(ann.DESC_BOLD) > 0, "<strong>/<b> element", ann.html_of(ann.DESC)[:120])
    check.truthy("embedded hyperlink rendered", ann.count(ann.DESC_LINK) > 0, "<a href>", ann.html_of(ann.DESC)[:120])
    if ann.count(ann.DESC_LINK):
        check.test_data("seeded link target", "https://www.qcci.org/about", ann.attribute(ann.DESC_LINK, "href"))
    check.assert_clean()


def _compat(page, tc: str):
    ann, item = _live_item(page)
    check = _Check(f"TC {tc}")
    ann.open_in_scope(item)
    _renders_config(check, ann, item)
    _layout(check, ann)
    _dismiss(check, ann)
    check.assert_clean()


@_meta("141416", "Popup displays and is dismissible on a 1920x1080 desktop viewport", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_141416
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_popup_desktop(page):
    """Azure TC 141416 | PBI 131032 — 1920x1080 display + Close."""
    _compat(page, "141416")


@_meta("141417", "Popup displays and is dismissible on a 768x1024 tablet viewport", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_141417
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_popup_tablet(page):
    """Azure TC 141417 | PBI 131032 — 768x1024 display + Close."""
    _compat(page, "141417")


@_meta("141418", "Popup displays and is dismissible on a 375x667 mobile viewport", "Compatibility")
@pytest.mark.compatibility
@pytest.mark.tc_141418
@pytest.mark.parametrize("page", [{"viewport": (375, 667), "auth": False}], indirect=True)
def test_popup_mobile(page):
    """Azure TC 141418 | PBI 131032 — 375x667 display + tap Close."""
    _compat(page, "141418")
