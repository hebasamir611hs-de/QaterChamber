"""
cms/pages/sectoral_committees/sectoral_committees_admin_page.py — Control_Panel
Page Objects for PBI 130716 (Sectoral Committees & Business Councils).

Live sidebar objects (2026-10-04), all read as QC Site Content Editor:
  * "Sectoral Committees Page" — page-level singleton; its one entry id 181385
    "Sectoral Committees and Business Councils" IS the live page. Drafts on.
  * "Committee Item" (directory rows), "Committee Leader Card" (Head of
    Sectoral committees grid), "Committee Mandate Item" (a committee's
    checklist; linked to a committee through the "Committee" picker),
    "Committee CTA Card" (Continue with Qatar Chamber panel).
Display orders of the live records are multiples of 100; QCTEST defaults use
9900 so they sort after real content unless a case needs otherwise.
"""

from cms.pages.components.disposable_object_admin import FieldSpec as F
from cms.pages.join_committee.council_base import _Council

LIVE_PAGE_ID = "181385"
LIVE_PAGE_TITLE = "Sectoral Committees and Business Councils"


class SectoralCommitteesPageAdminPage(_Council):
    SIDEBAR_LABEL = "Sectoral Committees Page"
    SLUG = "sectoral-committees-page"
    PLURAL = "sectoralcommitteespages"
    SINGLETON = True
    LIVE_IDS = (LIVE_PAGE_ID,)
    TITLE_FIELD = "hero_title"
    ACTIVE_FIELD = "page_active"

    def open_entry_by_edit_link(self, title: str):
        """Run 2026-10-04 (tc_146851, as the Author): this list's row carries TWO
        'Edit' links for the same entry, so the shared row-scoped locator hit a
        strict-mode violation. Fallback only on that error: both links must
        point at the same href (same entry) before the first is clicked."""
        try:
            return super().open_entry_by_edit_link(title)
        except Exception as exc:  # noqa: BLE001
            if "strict mode violation" not in str(exc):
                raise
        assert title.startswith("QCTEST-"), f"refusing to open non-QCTEST row {title!r}"
        links = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")').get_by_role("link", name="Edit")
        hrefs = {links.nth(i).get_attribute("href") for i in range(links.count())}
        if len(hrefs) != 1:
            raise RuntimeError(f"{title!r}: the row's Edit links point at different targets {hrefs!r}")
        links.first.click(force=True)
        self._wait_for_network_settle()
        self.wait_for(self.CANCEL_AND_ADD_NEW_LINK, timeout=30000)
        self._ident()["pending"] = title
        self._ident()["editing"] = self._ident()["ids"].get(title)
        return self
    FIELDS = {
        "breadcrumb": F("Breadcrumb Label", bilingual=True, required=True, default="QCTEST Crumb",
                        default_ar="مسار اختبار", confirmed_live=True),
        "hero_eyebrow": F("Hero Eyebrow", bilingual=True, required=True, default="QCTEST Eyebrow",
                          default_ar="عنوان صغير اختبار", confirmed_live=True),
        "hero_title": F("Hero Title", bilingual=True, required=True, max_len=150, confirmed_live=True),
        "hero_subtitle": F("Hero Subtitle", bilingual=True, required=True, default="QCTEST subtitle",
                           default_ar="عنوان فرعي اختبار", confirmed_live=True),
        "hero_bg": F("Hero Background Image", kind="file", confirmed_live=True),
        "page_active": F("Page Active Status", kind="checkbox", confirmed_live=True),
        "sector_eyebrow": F("Sector Section Eyebrow", bilingual=True, required=True, default="QCTEST sector eyebrow",
                            default_ar="تمثيل اختبار", confirmed_live=True),
        "sector_heading": F("Sector Section Heading", bilingual=True, required=True, default="QCTEST sector heading",
                            default_ar="عنوان قطاع اختبار", confirmed_live=True),
        "sector_body": F("Sector Section Body", kind="rich", bilingual=True, required=True, ref="sectorSectionBody",
                         default="QCTEST sector body.", default_ar="نص قطاع اختبار.", confirmed_live=True),
        "card_eyebrow": F("Sector Card Eyebrow", bilingual=True, required=True, default="QCTEST card eyebrow",
                          default_ar="دليل اختبار", confirmed_live=True),
        "card_title": F("Sector Card Title", bilingual=True, required=True, default="QCTEST card title",
                        default_ar="بطاقة اختبار", confirmed_live=True),
        "card_description": F("Sector Card Description", bilingual=True, required=True,
                              default="QCTEST card description", default_ar="وصف بطاقة اختبار", confirmed_live=True),
        "sector_active": F("Sector Section Active Status", kind="checkbox", confirmed_live=True),
        "dir_eyebrow": F("Directory Section Eyebrow", bilingual=True, required=True, default="QCTEST dir eyebrow",
                         default_ar="دليل اللجان اختبار", confirmed_live=True),
        "dir_heading": F("Directory Section Heading", bilingual=True, required=True, default="QCTEST dir heading",
                         default_ar="عنوان دليل اختبار", confirmed_live=True),
        "dir_body": F("Directory Section Body", bilingual=True, required=True, default="QCTEST dir body",
                      default_ar="نص دليل اختبار", confirmed_live=True),
        "search_placeholder": F("Directory Search Placeholder", bilingual=True, required=True,
                                default="QCTEST search", default_ar="بحث اختبار", confirmed_live=True),
        "dir_active": F("Directory Section Active Status", kind="checkbox", confirmed_live=True),
        "mandate_eyebrow": F("Mandate Panel Eyebrow", bilingual=True, required=True, default="QCTEST mandate eyebrow",
                             default_ar="اختصاصات اختبار", confirmed_live=True),
        "mandate_heading": F("Mandate Panel Heading", bilingual=True, required=True, default="QCTEST mandate heading",
                             default_ar="صلاحيات اختبار", confirmed_live=True),
        "cta_eyebrow": F("CTA Panel Eyebrow", bilingual=True, required=True, default="QCTEST cta eyebrow",
                         default_ar="تواصل اختبار", confirmed_live=True),
        "cta_heading": F("CTA Panel Heading", bilingual=True, required=True, default="QCTEST cta heading",
                         default_ar="عنوان تواصل اختبار", confirmed_live=True),
        "cta_body": F("CTA Panel Body", bilingual=True, required=True, default="QCTEST cta body",
                      default_ar="نص تواصل اختبار", confirmed_live=True),
        "cta_active": F("CTA Panel Active Status", kind="checkbox", confirmed_live=True),
    }


class CommitteeItemAdminPage(_Council):
    SIDEBAR_LABEL = "Committee Item"
    SLUG = "committee-item"
    PLURAL = "committeeitems"
    TITLE_FIELD = "committee_name"
    ACTIVE_FIELD = "item_active"
    FIELDS = {
        "display_order": F("Display Order / Number", kind="number", required=True, default="9900", confirmed_live=True),
        "committee_name": F("Committee Name", bilingual=True, required=True, confirmed_live=True),
        "short_description": F("Short Description", bilingual=True, required=True, default="QCTEST short description",
                               default_ar="وصف قصير اختبار", confirmed_live=True),
        "item_active": F("Item Active Status", kind="checkbox", confirmed_live=True),
    }


class CommitteeLeaderCardAdminPage(_Council):
    SIDEBAR_LABEL = "Committee Leader Card"
    SLUG = "committee-leader-card"
    PLURAL = "committeeleadercards"
    TITLE_FIELD = "leader_name"
    ACTIVE_FIELD = "card_active"
    FIELDS = {
        "display_number": F("Display Number", kind="number", required=True, default="99", confirmed_live=True),
        "leader_name": F("Leader Name", bilingual=True, required=True, confirmed_live=True),
        "sector_name": F("Committee/Sector Name", bilingual=True, required=True, default="QCTEST Committee",
                         default_ar="لجنة اختبار", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9900", confirmed_live=True),
        "card_active": F("Card Active Status", kind="checkbox", confirmed_live=True),
    }


class CommitteeMandateItemAdminPage(_Council):
    SIDEBAR_LABEL = "Committee Mandate Item"
    SLUG = "committee-mandate-item"
    PLURAL = "committeemandateitems"
    TITLE_FIELD = "bullet"
    ACTIVE_FIELD = "active"
    FIELDS = {
        "bullet": F("Mandate Bullet Item", bilingual=True, required=True, confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9900", confirmed_live=True),
        # the relation picker (combobox "Committee"); filled by each test with its own QCTEST committee
        "committee": F("Committee", kind="select", confirmed_live=True),
        "active": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class CommitteeCtaCardAdminPage(_Council):
    SIDEBAR_LABEL = "Committee CTA Card"
    SLUG = "committee-cta-card"
    PLURAL = "committeectacards"
    TITLE_FIELD = "card_title"
    ACTIVE_FIELD = "card_active"
    FIELDS = {
        "card_icon": F("Card Icon", kind="file", required=True, confirmed_live=True),
        "card_title": F("Card Title", bilingual=True, required=True, confirmed_live=True),
        "card_description": F("Card Description", bilingual=True, required=True, default="QCTEST CTA description",
                              default_ar="وصف بطاقة اختبار", confirmed_live=True),
        "target_url": F("Target URL / Link", kind="url", required=True,
                        default="/web/qatar-chamber/request-to-join-a-committee", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9900", confirmed_live=True),
        "card_active": F("Card Active Status", kind="checkbox", confirmed_live=True),
    }
