"""
cms/pages/partners_offers/partners_offers_admin_page.py — Control_Panel Page
Objects for PBI 130720 (Partners & Offers).

Sidebar labels and slugs read LIVE 2026-10-01 from the Object Authoring
sidebar. Field labels / refs / required flags read LIVE 2026-10-04 as QC Site
Content Editor from each create-new form (read-only probe, Engineer A; the
2026-10-01 "no authoring form" block is lifted).

Form mechanics REUSE Engineer B's proven FragmentFormMixin
(cms/pages/certificate_of_origin/fragment_form_mixin.py) by import, not copy:
the save watch (edit_info_item / `/o/c/` write, ID from the write), the
positive-signal refusal oracle, status / History / delete BY ID, the cached
role session checked against my-user-account, and the Editor
Pending->Published re-read. Neither that file nor the shared
ObjectAuthoringPage / DisposableObjectAdminPage is edited.

Two local overrides (Partners & Offers only):
  * fill_required() also uploads every key passed in `files`, required or
    not, so a test that hands a file always gets it attached (an optional
    file field silently left empty once caused false "not rendered" fails);
  * date fields are filled by their live `input[name="ObjectField_<ref>"]`
    (the shared textbox-role lookup hangs on these inputs, b9 2026-10-04).
"""

from cms.pages.certificate_of_origin.fragment_form_mixin import FragmentFormMixin
from cms.pages.components.disposable_object_admin import DisposableObjectAdminPage, FieldSpec as F


class _Po(FragmentFormMixin, DisposableObjectAdminPage):
    SLUG_CONFIRMED_LIVE = True  # read live 2026-10-01 (Object Authoring sidebar)

    def fill_required(self, title, skip=(), active=False, files=None):
        files = files or {}
        super().fill_required(title, skip=skip, active=active, files=files)
        for key, path in files.items():
            spec = self.FIELDS.get(key)
            if spec is None or key in skip or spec.required:
                continue  # required files were uploaded by the base fill
            self.upload(key, path, tag=title)
        return self

    # Smoke 2026-10-04: a role switch right after a submit hit net::ERR_ABORTED
    # on /c/portal/login (the save's own redirect still in flight; tc_144366),
    # and a cold manage-partner-category render outlived 35 s (tc_144415).
    # One settle-and-retry each, never a loop.
    def _fresh_login(self, email, password):
        try:
            return super()._fresh_login(email, password)
        except Exception as exc:  # noqa: BLE001
            if "ERR_ABORTED" not in str(exc):
                raise
            self.page.wait_for_timeout(3000)
            return super()._fresh_login(email, password)

    ADD_NEW_BUTTON = 'button:has-text("+ Add New"), a:has-text("+ Add New")'
    FORM_READY = 'button:has-text("Save as Draft")'
    PLURAL = ""  # the object's /o/c/<plural> (read live 2026-10-04)

    def _open_manage(self, role, locale, form):
        """Smoke 2026-10-04 (tc_144415 screenshot): manage-<slug> can land on
        a record PREVIEW ("Previewing General (Published)") with the create
        form not shown, until "+ Add New" is clicked. The list is opened
        first; the form is then revealed through "+ Add New" when Save as
        Draft is not already visible."""
        try:
            super()._open_manage(role, locale, form=False)
        except Exception as exc:  # noqa: BLE001
            if "Timeout" not in str(exc) and "ERR_ABORTED" not in str(exc):
                raise
            self.page.wait_for_timeout(2000)
            super()._open_manage(role, locale, form=False)
        if form:
            draft = self.page.locator(self.FORM_READY).first
            try:
                draft.wait_for(state="visible", timeout=5000)
            except Exception:  # noqa: BLE001 - preview shown instead of the form
                self.page.locator(self.ADD_NEW_BUTTON).first.click()
                draft.wait_for(state="visible", timeout=35000)
        return self

    def _row_locator(self, title_or_code: str):
        """Live 2026-10-04: Partner Category / Membership Tier rows carry no
        History control, so the row is matched by id on History OR Delete."""
        eid = self.id_for(title_or_code)
        if eid:
            r = self.ENTRIES_TABLE_ROW
            return self.page.locator(
                f'{r}:has([data-qc-oel-history="{eid}"]), {r}:has([data-qc-oel-delete="{eid}"])').first
        return super()._row_locator(title_or_code)

    def _id_by_title(self, title: str, role: str):
        """(found, id): one bounded search of the entries list by the exact
        QCTEST title prefix; id read from the row's data-qc-oel-delete.
        found=False means no such row exists (nothing was ever stored)."""
        self.open_list(role)
        box = self.page.locator(self.ENTRIES_SEARCH_INPUT)
        needle = self._needle(title)
        if box.count():
            box.fill(needle)
            box.press("Enter")
        rows = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{needle}")')
        try:
            rows.first.wait_for(state="visible", timeout=8000)
        except Exception:  # noqa: BLE001
            return False, None
        if rows.count() != 1:
            return True, None
        link = rows.first.locator("[data-qc-oel-delete]")
        return True, (link.first.get_attribute("data-qc-oel-delete") if link.count() else None)

    def delete_disposable(self, title, role=None):
        """Smoke 2026-10-04 (coordinator: 'LEFTOVER ... id=None'): a record
        whose save never went out has no ID, and the mixin's title fallback
        then reported a leftover for a record that never existed. With no
        known ID the list is searched first: no row = nothing to delete
        (True); one row = delete BY that row's ID."""
        from cms.pages.components.disposable_object_admin import DISPOSABLE_PREFIX, ROLE_EDITOR

        if (title and title.startswith(DISPOSABLE_PREFIX) and not self.id_for(title)
                and title not in self._ident()["absent"]):
            try:
                found, eid = self._id_by_title(title, role or ROLE_EDITOR)
            except Exception:  # noqa: BLE001 - fall through to the mixin's own path
                found, eid = True, None
            if not found:
                self._ident()["absent"].add(title)
                return True
            if eid:
                self._ident()["ids"][title] = (self.PLURAL, eid)
        return super().delete_disposable(title, role)

    def fill(self, key, value, locale="en"):
        """Live 2026-10-04: the visible date control is the site's own
        picker, `input#qc-dtp-<native id>` (placeholder dd/mm/yyyy); the
        native `input[type=date][name=ObjectField_<ref>]` is aria-hidden and
        carries the submitted ISO value. Tests pass ISO dates."""
        spec = self.spec(key)
        if spec.kind != "date" or not spec.ref:
            return super().fill(key, value, locale)
        native = self._date_input(key)
        nid = native.get_attribute("id") or ""
        text = self.page.locator(f'[id="qc-dtp-{nid}"]').first
        text.fill(_iso_to_dmy(value) if value else "")
        text.press("Tab")
        if native.input_value() != value:
            native.evaluate(
                "(e, v) => { e.value = v; e.dispatchEvent(new Event('input', {bubbles: true}));"
                " e.dispatchEvent(new Event('change', {bubbles: true})); }", value)
        return self


def _iso_to_dmy(value: str) -> str:
    y, m, d = value.split("-")
    return f"{d}/{m}/{y}"


class _FormScopedSubmit:
    """Partner Category / Membership Tier (read live 2026-10-04 as Editor):
    the form's submit button still carries the retired label (vocabulary
    drift, CLAUDE.md non-negotiable 2), so the shared
    SUBMIT_FOR_REVIEW_BUTTON (text-is "Submit for Review" | "Publish")
    matches nothing. The submit is located structurally instead: in the
    form holding Save as Draft, its other submit button (never Unpublish)."""

    # Live 2026-10-04: these forms also hold an unlabelled submit button
    # first in DOM order, so the submit is the one whose text holds "Submit".
    SUBMIT_FOR_REVIEW_BUTTON = (
        'form:has(button:has-text("Save as Draft")) button[type="submit"]'
        ':has-text("Submit"):not(:has-text("Save as Draft"))'
    )
    # Drafts are OFF for these record types (live tooltip on the hidden,
    # disabled Save as Draft: "Drafts are turned off for this record type -
    # set the status and use Submit."), so the form is ready when the submit
    # button is visible.
    FORM_READY = SUBMIT_FOR_REVIEW_BUTTON


class PartnerOfferAdminPage(_Po):
    SIDEBAR_LABEL = "Partner Offer"
    SLUG = "partner-offer"
    PLURAL = "partneroffers"
    TITLE_FIELD = "partner_name"
    ACTIVE_FIELD = None  # live 2026-10-04: no Active Status on this object (only the Status picklist)
    FIELDS = {
        "partner_name": F("Partner Name", bilingual=True, required=True, max_len=200, confirmed_live=True),
        "partner_logo": F("Partner Logo", kind="file", required=True, confirmed_live=True),
        # live: a plain Text field holding the category NAME (no picker)
        "partner_category": F("Partner Category", required=True, default="General", confirmed_live=True),
        "partner_location": F("Partner Location", bilingual=True, max_len=200, confirmed_live=True),
        "offer_description": F("Offer Description", kind="rich", bilingual=True, required=True,
                               ref="offerDescription", default="QCTEST offer description.",
                               default_ar="وصف عرض اختبار.", confirmed_live=True),
        "offer_terms": F("Offer Terms", kind="rich", bilingual=True, required=True, ref="offerTerms",
                         default="QCTEST offer terms.", default_ar="شروط عرض اختبار.", confirmed_live=True),
        # the default window holds today (2026-10-04): public cards show in-window offers only
        "validity_start": F("Offer Validity Start Date", kind="date", required=True, ref="validityStartDate",
                            default="2026-09-21", confirmed_live=True),
        "validity_end": F("Offer Validity End Date", kind="date", required=True, ref="validityEndDate",
                          default="2026-12-31", confirmed_live=True),
        # live: a plain Text field holding the tier NAME (no picker)
        "membership_tier": F("Membership Tier", required=True, default="General", confirmed_live=True),
        "contract_file": F("Offer Contract Document", kind="file", confirmed_live=True),
        "contract_url": F("Offer Contract URL", kind="url", confirmed_live=True),
        "offer_status": F("Status", kind="select", required=True, default="Published", confirmed_live=True),
    }


class PartnerCategoryAdminPage(_FormScopedSubmit, _Po):
    SIDEBAR_LABEL = "Partner Category"
    SLUG = "partner-category"
    PLURAL = "partnercategories"
    TITLE_FIELD = "category_name"
    FIELDS = {
        "category_name": F("Category Name", bilingual=True, required=True, max_len=100, confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class MembershipTierAdminPage(_FormScopedSubmit, _Po):
    SIDEBAR_LABEL = "Membership Tier"
    SLUG = "membership-tier"
    PLURAL = "membershiptiers"
    TITLE_FIELD = "tier_name"
    FIELDS = {
        "tier_name": F("Tier Name", bilingual=True, required=True, max_len=50, confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9901", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }


class PartnersOffersPageAdminPage(_Po):
    """Page-level singleton: the one entry QCDEMO-130720-PO-PAGE-01 (id
    167087, "Partners & Offers") IS the live page. Tests only create QCTEST
    entries that must be refused; nothing is published here."""

    SIDEBAR_LABEL = "Partners Offers Page"
    SLUG = "partners-offers-page"
    PLURAL = "partnersofferspages"
    SINGLETON = True
    TITLE_FIELD = "page_title"
    ACTIVE_FIELD = None  # live 2026-10-04: no Active Status on this object
    FIELDS = {
        "eyebrow": F("Eyebrow Label", bilingual=True, required=True, max_len=60,
                     default="QCTEST Eyebrow", default_ar="عنوان اختبار", confirmed_live=True),
        "page_title": F("Page Title", bilingual=True, required=True, max_len=150, confirmed_live=True),
        "page_description": F("Page Description", kind="rich", bilingual=True, required=True,
                              ref="pageDescription", default="QCTEST page description.",
                              default_ar="وصف صفحة اختبار.", confirmed_live=True),
        "hero_illustration": F("Hero Illustration", kind="file", required=True, confirmed_live=True),
        "section_eyebrow": F("Section Eyebrow", bilingual=True, required=True, max_len=60,
                             default="QCTEST Section", default_ar="قسم اختبار", confirmed_live=True),
        "section_heading": F("Section Heading", bilingual=True, required=True, max_len=150,
                             default="QCTEST Heading", default_ar="عنوان قسم اختبار", confirmed_live=True),
        "section_description": F("Section Description", bilingual=True, required=True, max_len=300,
                                 default="QCTEST section description.", default_ar="وصف قسم اختبار.",
                                 confirmed_live=True),
        "find_button_label": F("Find Button Label", bilingual=True, required=True, max_len=30,
                               default="Find", default_ar="بحث", confirmed_live=True),
        # first option, as the COO page singleton: nothing here is meant to go live
        "page_status": F("Status", kind="select", required=True, default="Draft", confirmed_live=True),
    }
