"""
web/pages/home_featured_event/home_featured_event_admin_page.py —
HomeFeaturedEventAdminPage.

Control_Panel Page Object for PBI 129382 (Home Page "Upcoming Event Pins"),
backing the "Upcoming Event Pins" Object Definition (objectDefinitionId
49124) singleton record that drives the public Home Page's
`section.qc-home-upcoming-event` card (home_featured_event_page.py is the
public-frontend counterpart).

REAL, LIVE-VERIFIED FACTS (this session, 2026-08-31, headed Chromium against
qcdev via the Playwright MCP browser, single non-parallel session):

NAVIGATION
  - Same regenerating-portlet-instance-id behavior already documented for
    every other Object Definition on this project (gm_message_admin_page.py,
    home_business_events_admin_page.py, etc.) — reach it ONLY via Product
    Menu > Content & Data > "Upcoming Event Pins", never a cached deep-link
    URL across sessions.
  - There is exactly ONE row on the list screen: id 49205, External Reference
    Code `QCDEMO-129382-PIN-001` — a TEST_OWNED singleton per cms-profile.md
    (reset to a fixed known baseline, not "whatever it was before" in the
    general case; here the fixed baseline IS also literally what was
    observed pre-mutation, confirmed live before any test in this batch
    touched it: `pinnedEvent=/web/qatar-chamber/events/novgorod-delegation`,
    `activeStatus=Yes`).

CONFIRMED LIVE FORM FIELD MAP (exactly 2 fields on this record's edit form)
  - Active Status  -> `activeStatus`  -> native `input[type="checkbox"]`
    under `[data-field-reference="activeStatus"]`.
  - Pinned Event   -> `pinnedEvent`   -> plain `input.ddm-field-text` under
    `[data-field-reference="pinnedEvent"]`, holding a raw path/slug STRING —
    confirmed live NOT a picker/dropdown despite the case text's wording.
  - Save/Cancel only — no separate Publish button (confirmed live: the
    rendered edit form has exactly two buttons).

OPEN QUESTION RESOLVED THIS SESSION — CONFIRMED PRODUCT DEFECT, not a locator
gap: the `pinnedEvent` field does NOT control which event the public
Home Page card renders. Reproduced independently, twice, with two different
real candidate values, live, each followed by a hard navigation + an
11-15s wait (well past this project's only measured propagation budget,
~0s for a different data source, and past the client-render settle time
documented on home_featured_event_page.py):
  1. `pinnedEvent = /web/qatar-chamber/events/event?id=110785` ("Export
     Documentation Workshop", a real, live, Published, future-dated
     [20 Oct 2026] event page) — card did not change.
  2. `pinnedEvent = /web/qatar-chamber/events/event?id=49443` ("Qatar–GCC
     Economic Cooperation Forum", a real event FROM the same Chamber Events
     collection the widget's fallback card is drawn from, ruling out the
     first attempt's "wrong collection" concern) — card still did not
     change.
  In both cases the Home Page kept showing "International Trade & Logistics
  Expo" (id 49485) — the same card shown with the ORIGINAL baseline pin
  value (`/web/qatar-chamber/events/novgorod-delegation`, which itself
  404s as a real page — confirmed live, `Coming Soon` / HTTP 404 — as does
  the OTHER bare-slug format tried, `/web/qatar-chamber/events/
  international-trade-logistics-expo`). No bare-slug URL on this site
  resolves to a real event page at all; the only real, working event URL
  format is the query-string one (`?id=<N>`), which is also the exact
  format the widget's own rendered `[data-qc-ue-media]` href uses. Given
  that even the native `?id=` format the widget speaks itself was ignored
  twice, the field is treated as CONFIRMED NON-FUNCTIONAL, not merely
  "wrong format" — see test_home_featured_event_control_panel.py's
  docstring for the full disclosure and why TC 135669 is left unautomated
  (documented defect) rather than scripted to assert a pass.

  What WAS confirmed to work live: toggling `activeStatus` OFF and Saving
  sets `section.qc-home-upcoming-event`'s inline `style` to `display:none`
  on the next page load (the section itself stays in the DOM — this is a
  CSS visibility toggle, not a DOM removal) — confirmed live, and this is
  the real mechanism TC 135670 automates below.
"""

from core.web.base_page import BasePage
from config.settings import control_panel_url, settings


class HomeFeaturedEventAdminPage(BasePage):
    # ---- Menu navigation (verbatim pattern from gm_message_admin_page.py /
    # home_business_events_admin_page.py) --------------------------------
    PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
    CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
    UPCOMING_EVENT_PINS_MENU_ITEM = '[role="menuitem"]:text-is("Upcoming Event Pins")'
    ADMIN_HOME_EN_URL_PATH = "/en/home"

    # ---- List screen ------------------------------------------------------
    # The one and only singleton row, confirmed live (id 49205).
    PIN_ROW_LINK = 'table tbody tr a:text-is("49205")'

    # ---- Edit form fields (data-field-reference — see module docstring) ---
    ACTIVE_STATUS_CONTAINER = '[data-field-reference="activeStatus"]'
    ACTIVE_STATUS_CHECKBOX = f'{ACTIVE_STATUS_CONTAINER} input[type="checkbox"]'
    PINNED_EVENT_CONTAINER = '[data-field-reference="pinnedEvent"]'
    PINNED_EVENT_INPUT = f'{PINNED_EVENT_CONTAINER} input.ddm-field-text'

    SAVE_BUTTON = 'button:has-text("Save")'
    CANCEL_BUTTON = 'button:has-text("Cancel")'

    # Confirmed-live baseline this session (see module docstring) — the
    # TEST_OWNED fixed reset target per cms-profile.md's Test-Data Policy.
    BASELINE_PINNED_EVENT = "/web/qatar-chamber/events/novgorod-delegation"
    BASELINE_ACTIVE = True

    # ---- Navigation -------------------------------------------------------
    def open_upcoming_event_pins_list(self) -> "HomeFeaturedEventAdminPage":
        """Product Menu > Content & Data > Upcoming Event Pins. Mirrors
        HomeBusinessEventsAdminPage.open_business_events_list()'s
        re-login-if-needed pattern."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(self.CONTENT_DATA_MENU_ITEM) or self.is_visible(self.PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(self.ADMIN_HOME_EN_URL_PATH))

        if not self.is_visible(self.CONTENT_DATA_MENU_ITEM):
            self.click(self.PRODUCT_MENU_TOGGLE)
            self.wait_for(self.CONTENT_DATA_MENU_ITEM)
        self.click(self.CONTENT_DATA_MENU_ITEM)
        self.wait_for(self.UPCOMING_EVENT_PINS_MENU_ITEM)
        self.click(self.UPCOMING_EVENT_PINS_MENU_ITEM)
        self.wait_for(self.PIN_ROW_LINK, timeout=20000)
        return self

    def open_pin_record(self) -> "HomeFeaturedEventAdminPage":
        self.click(self.PIN_ROW_LINK)
        self.wait_for(self.PINNED_EVENT_INPUT, timeout=15000)
        return self

    # ---- Field actions ------------------------------------------------------
    def set_pinned_event(self, value: str) -> "HomeFeaturedEventAdminPage":
        self.type(self.PINNED_EVENT_INPUT, value)
        return self

    def set_active(self, active: bool) -> "HomeFeaturedEventAdminPage":
        self.set_checkbox(self.ACTIVE_STATUS_CHECKBOX, active)
        return self

    def save(self) -> "HomeFeaturedEventAdminPage":
        self.click(self.SAVE_BUTTON)
        # Same disclosed save-commit grace already adopted for every other
        # Object Definition edit form on this project (e.g.
        # HomeBusinessEventsAdminPage.save()) — a real Save was completed
        # and observed live this session (unlike Business Events'), so this
        # is a real, confirmed-safe margin here, not a placeholder.
        self.page.wait_for_timeout(1500)
        return self

    def cancel(self) -> "HomeFeaturedEventAdminPage":
        self.click(self.CANCEL_BUTTON)
        return self

    # ---- State queries --------------------------------------------------------
    def pinned_event_value(self) -> str:
        return self.page.locator(self.PINNED_EVENT_INPUT).input_value()

    def is_active(self) -> bool:
        return self.page.locator(self.ACTIVE_STATUS_CHECKBOX).is_checked()

    def reset_to_baseline(self) -> "HomeFeaturedEventAdminPage":
        """Restore the singleton to its confirmed original baseline and
        SAVE — callers must still reopen the record afterward and assert
        pinned_event_value()/is_active() match BASELINE_* to verify the
        restore actually persisted (the "reopen + assert" hardening used
        elsewhere in this repo), rather than trusting this method's own
        in-form read."""
        self.set_pinned_event(self.BASELINE_PINNED_EVENT)
        self.set_active(self.BASELINE_ACTIVE)
        self.save()
        return self
