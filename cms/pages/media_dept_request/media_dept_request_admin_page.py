"""
cms/pages/media_dept_request/media_dept_request_admin_page.py — Control_Panel
Page Objects for PBI 131061 (QC - Media Center - Request to the Media Dept.).

Objects from the live Object Authoring sidebar (2026-10-01 brief): the page
hero (SINGLETON), the Press Kit card (SINGLETON), the standard request cards,
and the webform Submissions. Sidebar labels and slugs are read live before
the run; until then `SLUG` is empty and navigation is refused. If an object
is absent from the sidebar, its cases are BLOCKED (coordinator ruling).

Submissions are real visitor records: read only. Status / Internal Notes
cases need a QCTEST submission and are dispositioned `conditional`.
"""

from cms.pages.components.disposable_object_admin import DisposableObjectAdminPage, FieldSpec as F


class MediaDeptPageHeroAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = ""  # TODO(live)
    SLUG = ""
    SINGLETON = True
    TITLE_FIELD = "page_title"
    FIELDS = {
        "hero_eyebrow": F("Hero Eyebrow Label", bilingual=True, required=True, max_len=60,
                          default="QCTEST Media", default_ar="إعلام اختبار"),
        "page_title": F("Page Title", bilingual=True, required=True, max_len=100),
        "hero_description": F("Hero Description", kind="rich", bilingual=True, required=True,
                              ref="heroDescription", max_len=200,
                              default="QCTEST hero.", default_ar="وصف اختبار."),
        "hero_image": F("Hero Image", kind="file", required=True),
        "active_status": F("Active Status", kind="checkbox"),
    }


class PressKitCardAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = ""  # TODO(live)
    SLUG = ""
    SINGLETON = True
    TITLE_FIELD = "title"
    FIELDS = {
        "icon": F("Icon", kind="file", required=True),
        "eyebrow": F("Eyebrow Label", bilingual=True, required=True, max_len=60,
                     default="Press Kit", default_ar="الملف الصحفي"),
        "title": F("Title", bilingual=True, required=True, max_len=150),
        "description": F("Description", bilingual=True, required=True, max_len=400,
                         default="QCTEST press kit.", default_ar="ملف اختبار."),
        "file_button_label": F("File Button Label", bilingual=True, required=True, max_len=50,
                               default="Download", default_ar="تحميل"),
        "file_en": F("Press Kit File", kind="file", required=True),
        "file_ar": F("Press Kit File — العربية", kind="file", required=True),
        "active_status": F("Active Status", kind="checkbox"),
    }


class MediaStandardCardAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = ""  # TODO(live)
    SLUG = ""
    TITLE_FIELD = "title"
    FIELDS = {
        "icon": F("Icon", kind="file", required=True),
        "eyebrow": F("Eyebrow Label", bilingual=True, required=True, max_len=60,
                     default="QCTEST Request", default_ar="طلب اختبار"),
        "title": F("Title", bilingual=True, required=True, max_len=150),
        "description": F("Description", bilingual=True, required=True, max_len=400,
                         default="QCTEST card.", default_ar="بطاقة اختبار."),
        "button_label": F("Button Label", bilingual=True, required=True, max_len=50,
                          default="Request", default_ar="اطلب"),
        "display_order": F("Display Order", kind="number", default="9900"),
        "active_status": F("Active Status", kind="checkbox"),
    }


class MediaDeptSubmissionAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = ""  # TODO(live): Submissions surface (Form Manager)
    SLUG = ""
    TITLE_FIELD = "reference_no"
    ACTIVE_FIELD = None
    FIELDS = {
        "reference_no": F("Reference No."),
        "form_type": F("Form Type", kind="select"),
        "status": F("Status", kind="select"),
        "internal_notes": F("Internal Notes", max_len=1000),
    }
