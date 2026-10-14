"""
cms/pages/advertisements/advertisements_admin_page.py — Control_Panel Page
Objects for PBI 131062 (QC - Media Center - Advertisements).

Objects from the live Object Authoring sidebar (2026-10-01 brief): the page
hero + section header (SINGLETON), the rate card, its checklist items, and
the Booking Requests. Sidebar labels and slugs are read live before the run;
until then `SLUG` is empty and navigation is refused. If an object is absent
from the sidebar, its cases are BLOCKED (coordinator ruling).

Booking Requests are real visitor records: read only. Several cases name a
"QC Admin Reviewer" account, which is not one of the eight provisioned roles
(standards.md, Named CMS User Roles) — those are `conditional`.
"""

from cms.pages.components.disposable_object_admin import DisposableObjectAdminPage, FieldSpec as F


class AdvertisementsPageAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = ""  # TODO(live)
    SLUG = ""
    SINGLETON = True
    TITLE_FIELD = "page_title"
    FIELDS = {
        "hero_eyebrow": F("Hero Eyebrow", bilingual=True, required=True, max_len=60,
                          default="QCTEST Ads", default_ar="إعلانات اختبار"),
        "page_title": F("Page Title", bilingual=True, required=True, max_len=100),
        "hero_description": F("Hero Description", bilingual=True, required=True, max_len=200,
                              default="QCTEST hero.", default_ar="وصف اختبار."),
        "hero_image": F("Hero Image", kind="file", required=True),
        "section_eyebrow": F("Section Eyebrow", bilingual=True, required=True, max_len=60,
                             default="Rates", default_ar="الأسعار"),
        "section_title": F("Section Title", bilingual=True, required=True, max_len=150,
                           default="QCTEST rates", default_ar="أسعار اختبار"),
        "section_description": F("Section Description", bilingual=True, required=True, max_len=300,
                                 default="QCTEST section.", default_ar="قسم اختبار."),
        "active_status": F("Active Status", kind="checkbox"),
    }


class AdvertisementRateCardAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = ""  # TODO(live)
    SLUG = ""
    TITLE_FIELD = "ad_title"
    FIELDS = {
        "card_icon": F("Card Icon", kind="file", required=True),
        "category_label": F("Category/Eyebrow Label", bilingual=True, required=True, max_len=60,
                            default="QCTEST Digital", default_ar="رقمي اختبار"),
        "ad_title": F("Advertisement Title", bilingual=True, required=True, max_len=200),
        "price": F("Price", kind="number", required=True, default="5000.00"),
        "currency": F("Currency", kind="select", required=True, default="QAR"),
        "pricing_unit": F("Pricing Unit", bilingual=True, required=True, max_len=30,
                          default="/month", default_ar="/شهر"),
        "short_description": F("Short Description", bilingual=True, required=True, max_len=500,
                               default="QCTEST rate card.", default_ar="بطاقة اختبار."),
        "featured": F("Featured", kind="checkbox"),
        "book_now_label": F("Book Now Button Label", bilingual=True, max_len=50),
        "mapped_ads_type": F("Mapped Ads Type", kind="select", required=True),
        "display_order": F("Display Order", kind="number", required=True, default="9900"),
        "active_status": F("Active Status", kind="checkbox"),
    }
    DEFAULT_CURRENCY = "QAR"


class AdvertisementChecklistItemAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = ""  # TODO(live): own object, or a repeater inside the rate card
    SLUG = ""
    TITLE_FIELD = "item_text"
    FIELDS = {
        "item_text": F("Checklist Item Text", bilingual=True, required=True, max_len=100),
        "item_display_order": F("Display Order", kind="number", required=True, default="100"),
        "rate_card": F("Rate Card", kind="select", required=True),
        "active_status": F("Active Status", kind="checkbox"),
    }


class AdvertisementBookingRequestAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = ""  # TODO(live): Booking Requests surface
    SLUG = ""
    TITLE_FIELD = "booking_reference"
    ACTIVE_FIELD = None
    FIELDS = {
        "booking_reference": F("Booking Reference"),
        "status": F("Status", kind="select"),
        "ads_type": F("Ads Type", kind="select"),
        "internal_notes": F("Internal Notes", max_len=1000),
    }
