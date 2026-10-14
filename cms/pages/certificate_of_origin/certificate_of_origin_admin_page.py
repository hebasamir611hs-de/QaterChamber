"""
cms/pages/certificate_of_origin/certificate_of_origin_admin_page.py — Control_Panel
Page Objects for PBI 130947 (Certificate of Origin Online).

Object names, slugs and field labels were read LIVE from the Object Authoring
sidebar and each create-new form on 2026-10-01 as QC Site Content Editor
(engineer brief "Object-name source"; the Content-Admin-Guide.docx has no COO
entry). Field refs come from the `qc-ar-<ref>` ids on the live form and match
cms/liferay-context.md. No field carries a `maxlength` attribute, so length
limits are only observable through save/read-back.

`COO Page Content` is the page-level singleton (one QCDEMO entry renders the
page): tests create only QCTEST drafts / refused submits on it. `COO Call To
Action` is keyed (CTA Key) and is treated the same way for publish cases.
Every other object is a list object: QCTEST entries are created, published
where a case needs the public half, and deleted by exact title every run.
Pre-existing QCDEMO-* entries are real shared content: read only.
"""

from cms.pages.certificate_of_origin.fragment_form_mixin import FragmentFormMixin
from cms.pages.components.disposable_object_admin import DisposableObjectAdminPage, FieldSpec as F


class _Coo(FragmentFormMixin, DisposableObjectAdminPage):
    SLUG_CONFIRMED_LIVE = True  # read live 2026-10-01 (Object Authoring sidebar)


class CooPageContentAdminPage(_Coo):
    SIDEBAR_LABEL = "COO Page Content"
    SLUG = "coo-page-content"
    SINGLETON = True
    TITLE_FIELD = "page_title"
    FIELDS = {
        "eyebrow": F("Eyebrow Label", bilingual=True, required=True, max_len=60,
                     default="QCTEST Eyebrow", default_ar="عنوان اختبار", confirmed_live=True),
        "page_title": F("Page Title", bilingual=True, required=True, max_len=100, confirmed_live=True),
        "hero_description": F("Hero Description", kind="rich", bilingual=True, required=True,
                              ref="heroDescription", default="QCTEST hero description.",
                              default_ar="وصف اختبار.", confirmed_live=True),
        "hero_image": F("Hero Image", kind="file", confirmed_live=True),
        "banner_eyebrow": F("Banner Eyebrow", bilingual=True, max_len=60, confirmed_live=True),
        "banner_heading": F("Banner Heading", bilingual=True, max_len=150, confirmed_live=True),
        "banner_body": F("Banner Body", kind="rich", bilingual=True, ref="bannerBody", confirmed_live=True),
        "banner_active": F("Banner Active Status", kind="checkbox", confirmed_live=True),
        "page_status": F("Status", kind="select", required=True, confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class CooCtaAdminPage(_Coo):
    SIDEBAR_LABEL = "COO Call To Action"
    SLUG = "coo-cta"
    SINGLETON = True  # keyed: a published QCTEST CTA would reuse a live key
    TITLE_FIELD = "cta_label"
    FIELDS = {
        "cta_key": F("CTA Key", required=True, default="qctest-cta", confirmed_live=True),
        "cta_label": F("CTA Label", bilingual=True, required=True, max_len=100, confirmed_live=True),
        "redirect_url": F("Redirect URL", kind="url", default="https://example.com/qctest", confirmed_live=True),
        "open_behavior": F("Open Behavior", kind="select", required=True, confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class CooQuickFactAdminPage(_Coo):
    SIDEBAR_LABEL = "COO Quick Fact"
    SLUG = "coo-quick-fact"
    TITLE_FIELD = "fact_value"  # liferay-context titleField = factValue
    FIELDS = {
        "icon": F("Icon", kind="file", confirmed_live=True),
        "fact_label": F("Label", bilingual=True, required=True, max_len=60,
                        default="QCTEST Fact", default_ar="معلومة اختبار", confirmed_live=True),
        "fact_value": F("Value", bilingual=True, required=True, max_len=120, confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class CooSectionAdminPage(_Coo):
    SIDEBAR_LABEL = "COO Section"
    SLUG = "coo-section"
    TITLE_FIELD = "section_title"
    FIELDS = {
        "section_key": F("Section Key", required=True, default="qctest-section", confirmed_live=True),
        "section_number": F("Section Number", default="09", confirmed_live=True),
        "index_label": F("Index Label", bilingual=True, required=True,
                         default="QCTEST Index", default_ar="فهرس اختبار", confirmed_live=True),
        "section_badge": F("Section Badge", bilingual=True, max_len=100, confirmed_live=True),
        "section_title": F("Section Title", bilingual=True, required=True, max_len=100, confirmed_live=True),
        "section_intro": F("Section Intro", kind="rich", bilingual=True, ref="sectionIntro", confirmed_live=True),
        "section_body": F("Section Body", kind="rich", bilingual=True, ref="sectionBody", confirmed_live=True),
        "section_icon": F("Section Icon", kind="file", confirmed_live=True),
        "pdf_button_label": F("Action Button Label", bilingual=True, max_len=80, confirmed_live=True),
        "pdf_button_file": F("Action Button File", kind="file", confirmed_live=True),
        "pdf_button_url": F("Action Button URL", kind="url", confirmed_live=True),
        "pdf_button_behavior": F("Action Button Behavior", kind="select", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class CooInfoCardAdminPage(_Coo):
    SIDEBAR_LABEL = "COO Info Card"
    SLUG = "coo-info-card"
    TITLE_FIELD = "card_title"
    FIELDS = {
        "card_icon": F("Card Icon", kind="file", confirmed_live=True),
        "card_title": F("Card Title", bilingual=True, required=True, max_len=100, confirmed_live=True),
        "card_description": F("Card Description", kind="rich", bilingual=True, ref="cardDescription",
                              confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class CooDocumentRequirementAdminPage(_Coo):
    SIDEBAR_LABEL = "COO Document Requirement"
    SLUG = "coo-document-requirement"
    TITLE_FIELD = "item_title"
    FIELDS = {
        "item_title": F("Item Title", bilingual=True, required=True, max_len=200, confirmed_live=True),
        "item_subtitle": F("Item Subtitle", bilingual=True, max_len=200, confirmed_live=True),
        "item_content": F("Item Content", kind="rich", bilingual=True, required=True, ref="itemContent",
                          default="QCTEST content block.", default_ar="محتوى اختبار.", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class CooProcessStepAdminPage(_Coo):
    SIDEBAR_LABEL = "COO Process Step"
    SLUG = "coo-process-step"
    TITLE_FIELD = "step_title"
    FIELDS = {
        "step_number": F("Step Number", required=True, default="99", confirmed_live=True),
        "step_title": F("Step Title", bilingual=True, required=True, max_len=150, confirmed_live=True),
        "step_description": F("Step Description", kind="rich", bilingual=True, required=True,
                              ref="stepDescription", default="QCTEST step description.",
                              default_ar="وصف خطوة اختبار.", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class CooDownloadCardAdminPage(_Coo):
    SIDEBAR_LABEL = "COO Download Card"
    SLUG = "coo-download-card"
    TITLE_FIELD = "card_title"
    FIELDS = {
        "card_title": F("Card Title", bilingual=True, required=True, max_len=100, confirmed_live=True),
        "card_subtitle": F("Card Subtitle", bilingual=True, max_len=200, confirmed_live=True),
        "application_form_file": F("Application Form File", kind="file", confirmed_live=True),
        "download_label": F("Download Label", bilingual=True, max_len=40, confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }
