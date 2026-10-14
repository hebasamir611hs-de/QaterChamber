"""
cms/pages/business_council_membership/business_council_membership_admin_page.py
— Control_Panel Page Objects for PBI 130719 (Business Council Membership Request).

Live sidebar objects (2026-10-04): "Business Council Request Page" (page-level
singleton; its one entry id 183176 "Business Council Joining Request" IS the
live page), "Business Council Country" (the country dropdown values) and
"Business Council Membership Request" (the submissions). Field refs read from
the forms (qc-ar-<ref>). Hero Description / Overview Body / Card Description
are rich-text editors (textarea anchor + editor iframe). The page and country
record types have drafts turned off: Submit is the save.
"""

from cms.pages.components.disposable_object_admin import FieldSpec as F
from cms.pages.join_committee.council_base import SubmissionAdminPage, _Council, _DraftsOff

LIVE_PAGE_ID = "183176"
LIVE_PAGE_TITLE = "Business Council Joining Request"


class BusinessCouncilRequestPageAdminPage(_DraftsOff, _Council):
    SIDEBAR_LABEL = "Business Council Request Page"
    SLUG = "business-council-request-page"
    PLURAL = "businesscouncilrequestpages"
    SINGLETON = True
    LIVE_IDS = (LIVE_PAGE_ID,)
    TITLE_FIELD = "page_title"
    ACTIVE_FIELD = "page_visible"
    FIELDS = {
        "page_title": F("Page Title", bilingual=True, required=True, max_len=100, confirmed_live=True),
        "hero_description": F("Hero Description", kind="rich", bilingual=True, required=True, ref="heroDescription",
                              default="QCTEST hero description.", default_ar="وصف اختبار.", confirmed_live=True),
        "hero_image": F("Hero Image", kind="file", confirmed_live=True),
        "section_badge": F("Section Badge", bilingual=True, required=True, default="QCTEST Badge",
                           default_ar="شارة اختبار", confirmed_live=True),
        "section_title": F("Section Title", bilingual=True, required=True, default="QCTEST Section",
                           default_ar="قسم اختبار", confirmed_live=True),
        "overview_body": F("Overview Body", kind="rich", bilingual=True, required=True, ref="overviewBody",
                           default="QCTEST overview body.", default_ar="نص نظرة عامة اختبار.", confirmed_live=True),
        "card_icon": F("Card Icon", kind="file", confirmed_live=True),
        "card_title": F("Card Title", bilingual=True, required=True, default="QCTEST Card",
                        default_ar="بطاقة اختبار", confirmed_live=True),
        "card_description": F("Card Description", kind="rich", bilingual=True, required=True, ref="cardDescription",
                              default="QCTEST card description.", default_ar="وصف بطاقة اختبار.", confirmed_live=True),
        "page_visible": F("Page Visible", kind="checkbox", confirmed_live=True),
    }


class BusinessCouncilCountryAdminPage(_DraftsOff, _Council):
    SIDEBAR_LABEL = "Business Council Country"
    SLUG = "business-council-country"
    PLURAL = "businesscouncilcountries"
    TITLE_FIELD = "country_name"
    ACTIVE_FIELD = "active"
    FIELDS = {
        "country_name": F("Country Name", bilingual=True, required=True, confirmed_live=True),
        "country_code": F("Country Code", required=True, default="XQ", confirmed_live=True),
        "display_order": F("Display Order", kind="number", default="99900", confirmed_live=True),
        "active": F("Active", kind="checkbox", confirmed_live=True),
    }


class BusinessCouncilMembershipRequestAdminPage(SubmissionAdminPage):
    SIDEBAR_LABEL = "Business Council Membership Request"
    SLUG = "business-council-membership-request"
    PLURAL = "businesscouncilmembershiprequests"
