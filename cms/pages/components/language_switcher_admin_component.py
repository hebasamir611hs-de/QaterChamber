"""
cms/pages/components/language_switcher_admin_component.py — HeaderConfigurationLanguageSwitcherPage.

PBI 129365 (QC-GBL-002 Language Switcher), CMS side. Backs ADO 134429: "the
language switcher does not appear in the header when disabled in the CMS".

The guide (cms/Content-Admin-Guide.docx §3) gives the header ONE
`HeaderConfiguration` entry, with these fields: logoImage, logoAltTextEn/Ar,
logoRedirectUrl, workflowStatus. It lists no language-switcher setting.
eng-header's live read on 2026-09-30 of the edit form
(QCDEMO-129363-HEADER-CONFIG-DEFAULT, entryId 44788) agrees. It found
Workflow Status, Logo Image, Logo Alt Text (EN), Logo Alt Text (AR), Logo
Redirect URL and Active Status, and nothing else.

READ-ONLY. This Page Object only opens the live entry and lists the labels of
its form controls. The test decides from that list whether an enable/disable
control exists. Nothing here saves; the live entry is the real header.
"""

import re

from cms.pages.components.object_authoring_page import ObjectAuthoringPage

HEADER_CONFIG_SLUG = "header-configuration"
LIVE_HEADER_CONFIG_TITLE = "QCDEMO-129363-HEADER-CONFIG-DEFAULT"
# English-only, matched against the form's own label texts (not used as a locator).
LANGUAGE_SWITCHER_LABEL_PATTERN = re.compile(r"language|switcher|locale", re.I)


class HeaderConfigurationLanguageSwitcherPage(ObjectAuthoringPage):
    ENTRY_LINK = f'a[data-qc-oel-label="{LIVE_HEADER_CONFIG_TITLE}"]'

    def __init__(self, page):
        super().__init__(page, HEADER_CONFIG_SLUG)

    def open_live_entry(self) -> "HeaderConfigurationLanguageSwitcherPage":
        """Opens the one live entry via its own row's Edit link, matched by
        exact title. Waits on the row's label link, not the Delete link."""
        self.open(self._manage_url(locale="en"))
        self.wait_for(self.ENTRY_LINK, first=True, timeout=35000)
        rows = self.page.locator(f"{self.ENTRIES_TABLE_ROW}:has({self.ENTRY_LINK})")
        if rows.count() != 1:
            raise AssertionError(
                f"expected exactly one {LIVE_HEADER_CONFIG_TITLE!r} row on manage-{self.slug}, "
                f"found {rows.count()}"
            )
        self.open_entry_by_edit_link(LIVE_HEADER_CONFIG_TITLE)
        return self

    def form_control_labels(self) -> list[str]:
        """Label text of every visible input/select/textarea/switch on the page's
        authoring form (the form holding the Logo Redirect URL field)."""
        return self.page.evaluate(
            """() => {
              const form = Array.from(document.querySelectorAll('form'))
                .find(f => f.querySelector('[name^="ObjectField_"]')) || document;
              return Array.from(form.querySelectorAll('input, select, textarea, [role="switch"]'))
                .filter(e => e.type !== 'hidden' && (e.offsetWidth || e.offsetHeight))
                .map(e => ((e.labels && e.labels[0]) ? e.labels[0].innerText
                           : (e.getAttribute('aria-label') || e.name || '')).trim())
                .filter(t => t);
            }"""
        )

    def language_switcher_controls(self) -> list[str]:
        return [lbl for lbl in self.form_control_labels() if LANGUAGE_SWITCHER_LABEL_PATTERN.search(lbl)]

    def screenshot_png(self) -> bytes:
        return self.page.screenshot(full_page=True)
