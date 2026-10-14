"""
cms/pages/made_in_qatar_expo/made_in_qatar_expo_admin_page.py — Control_Panel
Page Objects for PBI 130708 (QC - Events - Made in Qatar Expo).

Three Object Authoring objects back the page (Hero, About section, side CTA
card), all on the 7-state editorial workflow. Object names and slugs come
from the live Object Authoring sidebar (engineer brief 2026-10-01,
"Object-name source"); `SLUG_CONFIRMED_LIVE` stays False on each class until
its sidebar label and slug have been read live, and DisposableObjectAdminPage
refuses to navigate before that.

Field labels below are the wording of the approved test cases. Each is
re-read on the live form before the run (FieldSpec.confirmed_live).

All three objects are page-level configuration (SINGLETON = True): the page
renders their one published entry. Tests only ever create QCTEST drafts or
refused submits on them; lifecycle cases that would publish a second entry
are dispositioned `conditional` in .claude/qa-runs/phase3_130708_cp_batch.json.
Pre-existing QCDEMO-* entries are real shared content: read only.
"""

from cms.pages.components.disposable_object_admin import DisposableObjectAdminPage, FieldSpec as F


class MadeInQatarExpoHeroAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Made in Qatar Expo Hero"
    SLUG = "made-in-qatar-expo-hero"  # named in the 2026-10-01 brief; confirm on the sidebar
    SINGLETON = True
    TITLE_FIELD = "page_title"
    FIELDS = {
        "eyebrow": F("Eyebrow Label", bilingual=True, required=True, max_len=60,
                     default="QCTEST Expo", default_ar="معرض اختبار"),
        "page_title": F("Page Title", bilingual=True, required=True, max_len=120),
        "hero_description": F("Hero Description", kind="rich", bilingual=True, required=True,
                              ref="heroDescription", max_len=200,
                              default="QCTEST hero description.", default_ar="وصف اختبار."),
        "hero_banner": F("Hero Banner", kind="file", required=True),
        "hero_banner_alt": F("Hero Banner Alt Text", bilingual=True, required=True,
                             default="QCTEST banner", default_ar="صورة اختبار"),
        "button_label": F("Button Label", bilingual=True, required=True, max_len=60,
                          default="Visit Expo", default_ar="زيارة المعرض"),
        "redirect_url": F("Redirect URL", kind="url", required=True, default="https://example.com/qctest"),
        "open_behavior": F("Open Behavior", kind="select"),
        "display_order": F("Display Order", kind="number", required=True, default="100"),
        "active_status": F("Active Status", kind="checkbox"),
    }


class MadeInQatarExpoAboutAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Made in Qatar Expo About Section"  # TODO(live): exact sidebar text
    SLUG = ""
    SINGLETON = True
    TITLE_FIELD = "section_title"
    FIELDS = {
        "section_eyebrow": F("Section Eyebrow", bilingual=True, required=True, max_len=100,
                             default="QCTEST About", default_ar="حول اختبار"),
        "section_title": F("Section Title", bilingual=True, required=True, max_len=120),
        "section_body": F("Section Body", kind="rich", bilingual=True, required=True,
                          ref="sectionBody", max_len=10000,
                          default="QCTEST about body.", default_ar="نص اختبار."),
        "active_status": F("Active Status", kind="checkbox"),
    }


class MadeInQatarExpoCtaCardAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Explore Made in Qatar CTA Card"  # TODO(live): exact sidebar text
    SLUG = ""
    SINGLETON = True
    TITLE_FIELD = "heading"
    FIELDS = {
        "logo": F("Logo", kind="file", required=True),
        "logo_alt": F("Logo Alt Text", bilingual=True, required=True,
                      default="QCTEST logo", default_ar="شعار اختبار"),
        "eyebrow": F("Eyebrow", bilingual=True, required=True, max_len=100,
                     default="QCTEST card", default_ar="بطاقة اختبار"),
        "heading": F("Heading", bilingual=True, required=True, max_len=120),
        "description": F("Description", kind="rich", bilingual=True, required=True, ref="description",
                         max_len=200, default="QCTEST card text.", default_ar="نص البطاقة."),
        "button_label": F("Button Label", bilingual=True, required=True, max_len=60,
                          default="Explore", default_ar="استكشف"),
        "redirect_url": F("Redirect URL", kind="url", required=True, default="https://example.com/qctest"),
        "open_behavior": F("Open Behavior", kind="select"),
        "active_status": F("Active Status", kind="checkbox"),
    }
