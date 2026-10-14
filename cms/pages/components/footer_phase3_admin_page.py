"""
cms/pages/components/footer_phase3_admin_page.py -- Object Authoring forms for
PBI 129366 (QC-GBL-004, Site Footer) as read live 2026-10-14
(reports/probe-footer-20261014.json, reports/probe-footer-config-20261014.json).

* `footer-configuration` -- ONE real record `QC_FOOTER_CONFIG_DEFAULT` (row
  shows the code). Its form submits with "Submit for Publishing" (not the
  workflow "Publish"); Save as Draft is disabled on the Published record.
  Logo Image accepts .gif/.jpeg/.jpg/.png/.svg/.webp <= 10 MB; no field label
  carries a "*". A Site Content Author sees the SAME editable form with the
  submit enabled (no Access Denied note), EN and AR interface.
* `footer-navigation-column` -- multi-record (About Qatar Chamber, Services).
  Fields: Column Heading (+ AR *), Column Number, Display Order, Active Status.
  Buttons: Save as Draft, Publish.
"""

from cms.pages.components.disposable_object_admin import DisposableObjectAdminPage, FieldSpec

FOOTER_CONFIG_CODE = "QC_FOOTER_CONFIG_DEFAULT"


class FooterConfigForm(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Footer Configuration"
    SLUG = "footer-configuration"
    SLUG_CONFIRMED_LIVE = True
    SINGLETON = True
    STATUS_SUBMIT = 'button[type="submit"][name="status"][value="0"]'
    FIELDS = {
        "logo": FieldSpec("Logo Image", kind="file", confirmed_live=True),
        "about_title": FieldSpec("About Column Title", bilingual=True, confirmed_live=True),
        "logo_alt": FieldSpec("Logo Alt Text", bilingual=True, confirmed_live=True),
        "active": FieldSpec("Active Status", kind="checkbox", confirmed_live=True),
    }


class FooterNavColumnForm(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Footer Navigation Column"
    SLUG = "footer-navigation-column"
    SLUG_CONFIRMED_LIVE = True
    STATUS_SUBMIT = 'button[type="submit"][name="status"][value="0"]'
    FIELDS = {
        "heading": FieldSpec("Column Heading", bilingual=True, confirmed_live=True),
        "number": FieldSpec("Column Number", kind="number", confirmed_live=True),
        "order": FieldSpec("Display Order", kind="number", confirmed_live=True),
        "active": FieldSpec("Active Status", kind="checkbox", confirmed_live=True),
    }
