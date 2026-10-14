"""
cms/pages/home_featured_event/home_featured_event_admin_page.py —
HomeFeaturedEventAdminPage.

Control_Panel Page Object for PBI 129382 (Home Page "Upcoming Featured
Event"). Rewritten 2026-10-07 (phase 3) to the Object Authoring surface.

CONTENT MODEL (cms/Content-Admin-Guide.docx §10): object `UpcomingEventPin`
— fields `pinnedEvent` (which BusinessEvent to feature) and `activeStatus`.
Nothing else. The PBI's Section Tag / Section Heading / Section Description
fields are NOT part of this object (requirements-vs-implementation conflict,
escalated in the phase-3 report — never satisfied by inventing an object).

LIVE FACTS (read-only recon 2026-10-07, as Site Content Editor / Author /
Site Member / logged out):
  - Sidebar label "Upcoming Event Pin" -> `/web/qatar-chamber/manage-upcoming-event-pin`.
    The page carries the normal 7-state workflow (PUBLISHED / DRAFT badges,
    Unpublish + History row actions), so the old "Content & Data, not an
    Object-Definition record" exemption in standards.md is stale for it.
  - Live singleton: entry code `QCDEMO-129382-PIN-001`, id 49205, PUBLISHED.
    A second row, `76e1088e-b6c9-0f7a-5559-a4f415b6b57b` (id 149262), is a
    DRAFT of unknown origin — not QCTEST, never touched by automation.
  - Form fields: `ObjectField_pinnedEvent` (plain text input) and
    `ObjectField_activeStatus` (checkbox). Editor's submit button reads
    "Publish"; Author's reads "Submit for Review".
  - Editor row actions on 49205: Edit / Preview / Unpublish / History / Delete.
    Author row actions on 49205: View / Preview / History (no edit).
  - Site Member and logged-out visitors get the public "Coming Soon" page
    (HTTP-404 style) on the manage URL — no form, no rows.

SAFETY: record 49205 is a real shared singleton. Every write helper below
(`set_*`, `publish`, `restore`) is used only by tests carrying
`xdist_group("pin_event_49205")`, and those tests need the user's ID-named
approval before they are run. Read helpers never save.
"""

from __future__ import annotations

import os

import pytest

from cms.pages.components.object_authoring_page import (
    ObjectAuthoringPage,
    normalize_status,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url
from core.web.base_page import BasePage


# ---- Write gate for the live pin 49205 -------------------------------------
# 49205 is the REAL Home Page pin. Every test that writes it requests the
# `approved_49205_write` fixture, which FAILS (never skips: skips are
# forbidden on this project) during setup, before any browser step, unless
# the user has given ID-named approval and the run sets QC_ALLOW_49205_WRITE=1.
# So `pytest -m control_panel`, `-m pbi_129382` or CI still collect these
# tests but cannot write 49205 by accident.
ALLOW_49205_WRITE_ENV = "QC_ALLOW_49205_WRITE"
GATE_MESSAGE = (
    "NEEDS USER: writes real record 49205 — requires ID-named approval; "
    f"set {ALLOW_49205_WRITE_ENV}=1"
)


@pytest.fixture
def approved_49205_write():
    if os.environ.get(ALLOW_49205_WRITE_ENV) != "1":
        pytest.fail(GATE_MESSAGE, pytrace=False)


class HomeFeaturedEventAdminPage(BasePage):
    SLUG = "upcoming-event-pin"
    SIDEBAR_LABEL = "Upcoming Event Pin"
    OBJECT_AUTHORING_INDEX = "/en/object-authoring"
    LIVE_PIN_CODE = "QCDEMO-129382-PIN-001"
    LIVE_PIN_ID = "49205"

    PINNED_EVENT_INPUT = 'input[name$="ObjectField_pinnedEvent"]'
    ACTIVE_STATUS_CHECKBOX = 'input[name$="ObjectField_activeStatus"]'
    OBJECT_FIELD_INPUTS = '[name*="ObjectField_"]'
    # A selector "list" would surface as one of these once the field is focused.
    SELECTOR_LIST = '[role="listbox"]:visible, [role="option"]:visible, datalist, .dropdown-menu.show'

    def __init__(self, page):
        super().__init__(page)
        self.authoring = ObjectAuthoringPage(page, self.SLUG)

    # ---- Session ----------------------------------------------------------
    def sign_in_as(self, role: str) -> "HomeFeaturedEventAdminPage":
        email, password = cms_role_credentials(role)
        CmsLoginPage(self.page).ensure_signed_in_as(email, password)
        return self

    # ---- Navigation -------------------------------------------------------
    def open_manage_page_raw(self) -> "HomeFeaturedEventAdminPage":
        """Navigate to the manage URL without waiting for the form — used by
        the denial cases, where the form must NOT appear.

        Uses a bare page.goto(), NOT BasePage.open(): open() runs
        core/web/session_guard.reauthenticate(), which treats a manage-<slug>
        URL rendered without `body.signed-in` as a dead session and silently
        signs in as TEST_USER — turning the logged-out case (135663) into an
        admin session (seen in run 20261007-2025)."""
        self.page.goto(
            control_panel_url(f"/en/web/qatar-chamber/manage-{self.SLUG}"),
            wait_until="domcontentloaded",
        )
        return self

    def open_entries_list(self) -> "HomeFeaturedEventAdminPage":
        self.authoring.open_entries_list(locale="en")
        return self

    def open_live_pin_read_only(self) -> "HomeFeaturedEventAdminPage":
        """Opens 49205's form by its own entry code. Callers never save."""
        self.authoring.open_entry_by_code(self.LIVE_PIN_CODE, locale="en")
        self.wait_for(self.PINNED_EVENT_INPUT, state="attached", timeout=20000, first=True)
        return self

    def open_object_authoring_index(self) -> "HomeFeaturedEventAdminPage":
        self.open(control_panel_url(self.OBJECT_AUTHORING_INDEX))
        self.page.get_by_text(self.SIDEBAR_LABEL, exact=True).first.wait_for(timeout=35000)
        return self

    def open_from_sidebar(self) -> "HomeFeaturedEventAdminPage":
        self.page.get_by_text(self.SIDEBAR_LABEL, exact=True).first.click()
        self.page.wait_for_url(f"**/manage-{self.SLUG}**", timeout=35000)
        self.wait_for(self.PINNED_EVENT_INPUT, state="attached", timeout=35000, first=True)
        return self

    # ---- Reads ------------------------------------------------------------
    def sidebar_has_entry(self) -> bool:
        return self.page.get_by_text(self.SIDEBAR_LABEL, exact=True).count() > 0

    def pin_form_present(self) -> bool:
        return (
            self.page.locator(self.PINNED_EVENT_INPUT).count() > 0
            and self.page.locator(self.ACTIVE_STATUS_CHECKBOX).count() > 0
        )

    def pin_form_editable(self) -> bool:
        pe = self.page.locator(self.PINNED_EVENT_INPUT).first
        ac = self.page.locator(self.ACTIVE_STATUS_CHECKBOX).first
        return pe.is_editable() and ac.is_enabled()

    def object_field_names(self) -> set:
        names = self.page.locator(self.OBJECT_FIELD_INPUTS).evaluate_all(
            "els => els.map(e => e.getAttribute('name') || '')"
        )
        return {n.split("ObjectField_", 1)[1].split("_")[0] for n in names if "ObjectField_" in n}

    def pinned_event_value(self) -> str:
        return self.page.locator(self.PINNED_EVENT_INPUT).first.input_value()

    def is_active(self) -> bool:
        return self.page.locator(self.ACTIVE_STATUS_CHECKBOX).first.is_checked()

    def pinned_event_input_type(self) -> str:
        return self.page.locator(self.PINNED_EVENT_INPUT).first.get_attribute("type") or ""

    def open_pinned_event_selector(self) -> bool:
        """Focus the Pinned Event control the way an editor would to pick an
        event, and report whether any selectable list appears. Types nothing
        and never saves."""
        self.page.locator(self.PINNED_EVENT_INPUT).first.click()
        try:
            self.page.locator(self.SELECTOR_LIST).first.wait_for(state="attached", timeout=5000)
            return True
        except Exception:  # noqa: BLE001 — absence of a list is the answer
            return False

    def selector_option_texts(self) -> list:
        return [t.strip() for t in self.page.locator('[role="option"]').all_inner_texts() if t.strip()]

    def live_pin_row_actions(self) -> set:
        """Workflow/edit actions the signed-in role is offered on 49205's row.
        `data-qc-oel-*` attributes, plus the row's own Edit/View link text."""
        row = self.page.locator("table tbody tr", has_text=self.LIVE_PIN_CODE).first
        attrs = row.locator("a, button").evaluate_all(
            "els => els.flatMap(e => [...e.attributes].map(a => a.name)"
            ".filter(n => n.startsWith('data-qc-oel-')).map(n => n.slice(12))"
            ".concat([(e.innerText || '').trim().toLowerCase()]))"
        )
        return {a for a in attrs if a}

    def live_pin_status(self) -> str:
        return normalize_status(self.authoring.row_status_text_by_code(self.LIVE_PIN_CODE))

    def manage_page_rendered(self) -> bool:
        return self.page.title().startswith("Manage:") or self.pin_form_present()

    def login_form_visible(self) -> bool:
        return CmsLoginPage(self.page).login_form_visible()

    def body_text(self) -> str:
        return self.page.locator("body").inner_text()

    # ---- Writes (49205 — approval-gated tests only) -------------------------
    def snapshot(self) -> dict:
        return {"pinnedEvent": self.pinned_event_value(), "activeStatus": self.is_active()}

    def set_pinned_event(self, value: str) -> "HomeFeaturedEventAdminPage":
        self.page.locator(self.PINNED_EVENT_INPUT).first.fill(value)
        return self

    def set_active(self, active: bool) -> "HomeFeaturedEventAdminPage":
        self.page.locator(self.ACTIVE_STATUS_CHECKBOX).first.set_checked(active)
        return self

    def publish(self) -> "HomeFeaturedEventAdminPage":
        """Editor's submit ("Publish"; SUBMIT_FOR_REVIEW_BUTTON matches both labels)."""
        self.authoring.submit_for_review()
        return self

    def open_for_edit(self) -> "HomeFeaturedEventAdminPage":
        """Open 49205 for a WRITE. A published record is edited by
        "Unpublish to edit as draft" first (OBJECT-AUTHORING-GUIDE: "Edit a
        published record — Unpublish to edit as draft, edit, publish again"),
        then reopened so the form reflects the draft. Approval-gated callers only."""
        self.open_live_pin_read_only()
        if self.page.locator(ObjectAuthoringPage.UNPUBLISH_BUTTON).count():
            self.authoring.unpublish_to_edit_as_draft()
            self.open_live_pin_read_only()
        return self

    def restore(self, snap: dict) -> None:
        """Write the snapshot back to 49205, publish, then reopen and verify."""
        self.open_for_edit()
        self.set_pinned_event(snap["pinnedEvent"]).set_active(snap["activeStatus"]).publish()
        self.open_live_pin_read_only()
        assert self.snapshot() == snap, f"49205 restore did not persist: {self.snapshot()} != {snap}"
