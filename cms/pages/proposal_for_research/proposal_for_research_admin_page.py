"""
cms/pages/proposal_for_research/proposal_for_research_admin_page.py — Control_Panel
Page Objects for PBI 130949 (Proposal for Research).

Object names, slugs and field labels were read LIVE from the Object Authoring
sidebar and each create-new form on 2026-10-01 as QC Site Content Editor
(engineer brief "Object-name source"). Field refs come from the live
`qc-ar-<ref>` ids and match cms/liferay-context.md. No field carries a
`maxlength` attribute, so length limits are only observable through
save/read-back.

`Proposal for Research Page / Hero` is the page-level singleton: tests create
only QCTEST drafts / refused submits on it. The other six are list objects:
QCTEST entries are created, published where a case needs the public half, and
deleted by exact title every run. Pre-existing QCDEMO-* entries are real
shared content: read only.

Group Item's "Item Label" is a RICH-TEXT field on the live form (not plain
text), which puts its character-limit cases under the 2026-10-01 rich-text NA
rule.
"""

from cms.pages.certificate_of_origin.fragment_form_mixin import FragmentFormMixin
from cms.pages.components.disposable_object_admin import DisposableObjectAdminPage, FieldSpec as F


class _Pfr(FragmentFormMixin, DisposableObjectAdminPage):
    SLUG_CONFIRMED_LIVE = True  # read live 2026-10-01 (Object Authoring sidebar)


class ProposalPageAdminPage(_Pfr):
    SIDEBAR_LABEL = "Proposal for Research Page / Hero"
    SLUG = "proposal-for-research-page"
    SINGLETON = True
    TITLE_FIELD = "page_title"
    FIELDS = {
        "eyebrow": F("Eyebrow Label", bilingual=True, required=True, max_len=60,
                     default="QCTEST Eyebrow", default_ar="عنوان اختبار", confirmed_live=True),
        "page_title": F("Page Title", bilingual=True, required=True, max_len=100, confirmed_live=True),
        "hero_description": F("Hero Description", kind="rich", bilingual=True, required=True,
                              ref="heroDescription", default="QCTEST hero description.",
                              default_ar="وصف اختبار.", confirmed_live=True),
        "hero_banner": F("Hero Banner", kind="file", required=True, confirmed_live=True),
        "page_status": F("Status", kind="select", required=True, confirmed_live=True),
        "created_date": F("Created Date", kind="date", ref="createdDate", confirmed_live=True),
        "last_modified": F("Last Modified Date", kind="date", ref="lastModifiedDate", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class QuickFactsTileAdminPage(_Pfr):
    SIDEBAR_LABEL = "Quick-Facts Tile"
    SLUG = "proposal-research-quick-facts-tile"
    TITLE_FIELD = "label"
    FIELDS = {
        "icon": F("Icon", kind="file", required=True, confirmed_live=True),
        "label": F("Label", bilingual=True, required=True, max_len=60, confirmed_live=True),
        "value": F("Value", bilingual=True, required=True, max_len=120,
                   default="QCTEST value", default_ar="قيمة اختبار", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class SectionIndexEntryAdminPage(_Pfr):
    SIDEBAR_LABEL = "Section Index / Section"
    SLUG = "proposal-research-section-index-entry"
    TITLE_FIELD = "section_title"
    FIELDS = {
        "section_title": F("Section Title", bilingual=True, required=True, max_len=100, confirmed_live=True),
        "section_numbering": F("Section Numbering", bilingual=True, required=True,
                               default="09", default_ar="09", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class OverviewInfoCardAdminPage(_Pfr):
    SIDEBAR_LABEL = "Overview - Body + Info Card"
    SLUG = "overview-section-and-info-card"
    TITLE_FIELD = "card_title"
    FIELDS = {
        "section_badge": F("Section Badge", bilingual=True, required=True, max_len=100,
                           default="QCTEST Badge", default_ar="شارة اختبار", confirmed_live=True),
        "section_title": F("Section Title", bilingual=True, required=True, max_len=100,
                           default="QCTEST Overview", default_ar="نظرة اختبار", confirmed_live=True),
        "overview_body": F("Overview Body", kind="rich", bilingual=True, required=True, ref="overviewBody",
                           default="QCTEST overview body.", default_ar="نص اختبار.", confirmed_live=True),
        "card_icon": F("Card Icon", kind="file", required=True, confirmed_live=True),
        "card_title": F("Card Title", bilingual=True, required=True, max_len=100, confirmed_live=True),
        "card_description": F("Card Description", kind="rich", bilingual=True, required=True,
                              ref="cardDescription", default="QCTEST card description.",
                              default_ar="وصف بطاقة اختبار.", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class InformationGroupAdminPage(_Pfr):
    SIDEBAR_LABEL = "Service Information - Information Group"
    SLUG = "service-information-group"
    TITLE_FIELD = "group_label"
    FIELDS = {
        "section_badge": F("Section Badge", bilingual=True, required=True, max_len=100,
                           default="QCTEST Badge", default_ar="شارة اختبار", confirmed_live=True),
        "section_title": F("Section Title", bilingual=True, required=True, max_len=100,
                           default="QCTEST Service info", default_ar="معلومات اختبار", confirmed_live=True),
        "group_label": F("Group Label", bilingual=True, required=True, max_len=120, confirmed_live=True),
        "group_intro": F("Group Intro", kind="rich", bilingual=True, ref="groupIntro", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class GroupItemAdminPage(_Pfr):
    SIDEBAR_LABEL = "Group Item (bullet inside an Information Group)"
    SLUG = "service-information-group-item"
    TITLE_FIELD = "item_label"
    FIELDS = {
        # RICH TEXT on the live form; fill_required() fills the title field
        # through fill(), which routes rich kinds to the CKEditor iframe.
        "item_label": F("Item Label", kind="rich", bilingual=True, required=True, ref="itemLabel",
                        max_len=300, confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
        "group": F("Group Items", kind="text", confirmed_live=True),  # relationship picker (label as rendered)
    }


class ResourceItemAdminPage(_Pfr):
    SIDEBAR_LABEL = "Downloadable Resources - Resource Item"
    SLUG = "downloadable-resource-item"
    TITLE_FIELD = "resource_title"
    FIELDS = {
        "section_badge": F("Section Badge", bilingual=True, required=True, max_len=100,
                           default="QCTEST Badge", default_ar="شارة اختبار", confirmed_live=True),
        "section_title": F("Section Title", bilingual=True, required=True, max_len=100,
                           default="QCTEST Resources", default_ar="موارد اختبار", confirmed_live=True),
        "section_intro": F("Section Intro", kind="rich", bilingual=True, required=True, ref="sectionIntro",
                           default="QCTEST resources intro.", default_ar="مقدمة اختبار.", confirmed_live=True),
        "resource_title": F("Resource Title", bilingual=True, required=True, max_len=200, confirmed_live=True),
        "resource_file": F("Resource File", kind="file", confirmed_live=True),
        "file_type": F("File Type", required=True, default="PDF", confirmed_live=True),
        "file_size": F("File Size", required=True, default="1 MB", confirmed_live=True),
        "download_label": F("Download Label", bilingual=True, required=True, max_len=40,
                            default="Download", default_ar="تنزيل", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }
