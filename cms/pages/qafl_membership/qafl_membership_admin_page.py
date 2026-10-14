"""
cms/pages/qafl_membership/qafl_membership_admin_page.py — Control_Panel Page
Objects for PBI 130718 (QAFL Membership Registration).

Live sidebar objects (2026-10-04): "QAFL Page Content" (page-level singleton;
its one entry id 208073 "QAFL Membership Registration" IS the live page at
/web/qatar-chamber/qafl-membership) and "QAFL Membership Submission" (the
submissions). Field refs and file rules read from the form: Hero Background
Image .jpg/.jpeg/.png/.svg/.webp up to 5 MB (optional), Card Icon
.jpg/.jpeg/.png/.svg up to 2 MB (required, a file upload, not an icon picker),
Template File .pdf/.doc/.docx up to 10 MB (required). Section Body is a
rich-text editor; Card Description is a plain textarea. Drafts are off for the
Editor's record type (Save as Draft hidden + disabled; Submit button reads
"Publish").
"""

from cms.pages.components.disposable_object_admin import FieldSpec as F
from cms.pages.join_committee.council_base import SubmissionAdminPage, _Council, _DraftsOff

LIVE_PAGE_ID = "208073"
LIVE_PAGE_TITLE = "QAFL Membership Registration"
PUBLIC_PATH = "/web/qatar-chamber/qafl-membership"


class QaflPageContentAdminPage(_DraftsOff, _Council):
    SIDEBAR_LABEL = "QAFL Page Content"
    SLUG = "qafl-page-content"
    PLURAL = "qaflpagecontents"
    SINGLETON = True
    LIVE_IDS = (LIVE_PAGE_ID,)
    TITLE_FIELD = "hero_title"
    ACTIVE_FIELD = "page_active"
    FIELDS = {
        "breadcrumb": F("Breadcrumb Label", bilingual=True, required=True, default="QCTEST Crumb",
                        default_ar="مسار اختبار", confirmed_live=True),
        "hero_title": F("Hero Title", bilingual=True, required=True, max_len=100, confirmed_live=True),
        "hero_subtitle": F("Hero Subtitle", bilingual=True, required=True, default="QCTEST subtitle",
                           default_ar="عنوان فرعي اختبار", confirmed_live=True),
        "hero_bg": F("Hero Background Image", kind="file", confirmed_live=True),
        "page_active": F("Page Active Status", kind="checkbox", confirmed_live=True),
        "section_eyebrow": F("Section Eyebrow", bilingual=True, required=True, default="QCTEST eyebrow",
                             default_ar="عنوان صغير اختبار", confirmed_live=True),
        "section_heading": F("Section Heading", bilingual=True, required=True, default="QCTEST heading",
                             default_ar="عنوان اختبار", confirmed_live=True),
        "section_body": F("Section Body", kind="rich", bilingual=True, required=True, ref="sectionBody",
                          default="QCTEST section body.", default_ar="نص قسم اختبار.", confirmed_live=True),
        "card_icon": F("Card Icon", kind="file", required=True, confirmed_live=True),
        "card_eyebrow": F("Card Eyebrow", bilingual=True, required=True, default="QCTEST card eyebrow",
                          default_ar="بطاقة اختبار", confirmed_live=True),
        "card_title": F("Card Title", bilingual=True, required=True, default="QCTEST card title",
                        default_ar="عنوان بطاقة اختبار", confirmed_live=True),
        "card_description": F("Card Description", bilingual=True, required=True, default="QCTEST card description",
                              default_ar="وصف بطاقة اختبار", confirmed_live=True),
        "download_label": F("Download Button Label", bilingual=True, required=True, default="QCTEST Download",
                            default_ar="تنزيل اختبار", confirmed_live=True),
        "template_file": F("Template File", kind="file", required=True, confirmed_live=True),
    }


class QaflMembershipSubmissionAdminPage(SubmissionAdminPage):
    SIDEBAR_LABEL = "QAFL Membership Submission"
    SLUG = "qafl-membership-submission"
    PLURAL = "qaflmembershipsubmissions"
