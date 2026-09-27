"""
web/pages/org_structure/org_structure_page.py — OrgStructurePage.

Public-frontend Page Object for PBI 129399 (QC-ABOUT-007 — Organizational
Structure), `/web/qatar-chamber/about-us/organizational-structure`.

Locators extracted CLI-first via tools/extract_locators.py against the live
page (WEB_BASE_URL=https://qcdev.ihorizons.com/) at the framework default
viewport, plus a disclosed Playwright-MCP fallback for the org-chart node
cards themselves — the CLI harvester only walks a,button,input,select,
textarea,[role],[data-testid],[data-test],[aria-label],[contenteditable], and
the chart's node cards are `<div role="button">`, not `<button>`, so an
MCP accessibility snapshot + a scoped `page.evaluate` DOM probe were used to
confirm the real, stable custom class names below (qc-org-*) before writing
them in as constants:

    python tools/extract_locators.py \
      --url https://qcdev.ihorizons.com/web/qatar-chamber/about-us/organizational-structure

    -> role=heading[name="Organizational Structure"]  uniq=1
    -> role=button[name="Expand All"] / "Collapse All" / "Zoom out" / "Zoom in"
       / "Reset View" / "Toggle fullscreen"  all uniq=1
    -> role=searchbox[name="Search departments, leaders or titles"]

DOM probe (MCP `browser_evaluate`) confirmed the node-card structure:
    div.qc-org-node[role=button][tabindex=0]
      div.qc-org-node-head > span.qc-org-node-dept
      hr.qc-org-node-divider
      div.qc-org-node-person
        span.qc-org-avatar-wrap > span.qc-org-avatar > svg.qc-org-avatar-default (no photo)
        span.qc-org-node-person-text
          span.qc-org-node-name
          span.qc-org-node-title
    button.qc-org-btn.qc-org-btn-icon-only[aria-label="Toggle branch"]  (nested toggle, present only on parents with children)
    ul/li tree nesting: a node's children live in a <ul> nested INSIDE its own
    <li> — this IS the parent/child relationship encoded structurally (used by
    connector-line case 133260/133365 instead of asserting on SVG paint).
    Search: matched <li> gets class "qc-org-item is-match"; empty state is
    div.qc-org-empty ("No departments match your search.").
    Toolbar container: div.qc-org-toolbar; zoom % text: span.qc-org-zoom.
"""

from config.settings import web_url
from core.web.base_page import BasePage

ORG_STRUCTURE_PATH = "/web/qatar-chamber/about-us/organizational-structure"

# Borrowed from cms-profile.md's ONLY measured propagation budget (~0s /
# 5s-timeout / 0.5s-interval, Board Members JAX-RS endpoint) and reused
# project-wide as the safety-margin default pending a per-endpoint
# re-measure (same disclosed-not-independently-confirmed precedent as
# HomePromoBannersPage.RELOAD_POLL_TIMEOUT_MS / HomeHeroBannerPage's own
# PROPAGATION_POLL_TIMEOUT_MS) — used by reload_until_node_matches() below,
# ADDED 2026-09-14 (Group A/tc_133294 triage: a single cold post-deactivation
# read raced cache propagation with no retry; sibling tests in this same
# suite, e.g. Hero Banner's reload_until_title_in_carousel(), already carry
# this exact poll pattern for the identical class of publish-then-verify
# check).
PROPAGATION_POLL_TIMEOUT_MS = 5000
PROPAGATION_POLL_INTERVAL_MS = 500


class OrgStructurePage(BasePage):
    # ---- Page chrome -------------------------------------------------
    PAGE_TITLE = 'role=heading[name="Organizational Structure"]'
    BREADCRUMB_NAV = 'role=navigation[name="Breadcrumb"]'
    BREADCRUMB_HOME_LINK = 'role=navigation[name="Breadcrumb"] >> role=link[name="Home"]'

    # ---- Toolbar -------------------------------------------------------
    TOOLBAR = ".qc-org-toolbar"
    SEARCH_INPUT = 'role=searchbox[name="Search departments, leaders or titles"]'
    SEARCH_EMPTY_STATE = ".qc-org-empty"
    EXPAND_ALL_BTN = 'role=button[name="Expand All"]'
    COLLAPSE_ALL_BTN = 'role=button[name="Collapse All"]'
    ZOOM_OUT_BTN = 'role=button[name="Zoom out"]'
    ZOOM_IN_BTN = 'role=button[name="Zoom in"]'
    ZOOM_INDICATOR = ".qc-org-zoom"
    RESET_VIEW_BTN = 'role=button[name="Reset View"]'
    FULLSCREEN_TOGGLE_BTN = 'role=button[name="Toggle fullscreen"]'

    # ---- Node card (per-department, resolved by department name) ------
    NODE_DEPT = ".qc-org-node-dept"
    NODE_PERSON_NAME = ".qc-org-node-name"
    NODE_PERSON_TITLE = ".qc-org-node-title"
    NODE_AVATAR_DEFAULT = ".qc-org-avatar-default"
    NODE_DIVIDER = ".qc-org-node-divider"
    MATCHED_ITEM = ".qc-org-item.is-match"

    # ---- Navigation -----------------------------------------------------
    def open_org_structure(self, locale: str = "en") -> "OrgStructurePage":
        self.open(web_url(ORG_STRUCTURE_PATH, locale=locale))
        return self

    def open_broken_url(self) -> "OrgStructurePage":
        """Deliberately-invalid path under the same section, for the
        standard-error-page case (133287) — the environment has no toggle to
        make the real page's *content* unavailable, so an unknown child path
        is used to exercise the site's standard not-found handling instead."""
        self.open(web_url(ORG_STRUCTURE_PATH + "-unavailable-content-check"))
        return self

    # ---- Page chrome ----------------------------------------------------
    def page_title_text(self) -> str:
        return self.text(self.PAGE_TITLE)

    def is_page_title_visible(self) -> bool:
        return self.is_visible(self.PAGE_TITLE)

    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.BREADCRUMB_NAV)

    def breadcrumb_home_text(self) -> str:
        return self.text(self.BREADCRUMB_HOME_LINK)

    def is_toolbar_visible(self) -> bool:
        return self.is_visible(self.TOOLBAR)

    def is_chart_visible(self) -> bool:
        # CONFIRMED LIVE, 2026-08-25: the rendered chart has 8 top-level
        # `.qc-org-node` cards, so the bare locator triggers a Playwright
        # strict-mode violation ("resolved to 8 elements") on is_visible().
        # BasePage.is_visible()'s blanket except-and-return-False swallowed
        # that exception silently, reporting an actually-rendered chart as
        # invisible. `>> nth=0` scopes to a single element without needing
        # a bespoke locator.
        return self.is_visible(".qc-org-node >> nth=0")

    # ---- Node locators / queries ----------------------------------------
    def _node(self, department_name: str):
        """The `.qc-org-node` card whose department span's text equals
        `department_name` exactly (avoids partial-match collisions with the
        footer's duplicate 'About Qatar Chamber' nav links)."""
        return self.page.locator(
            f'.qc-org-node:has(.qc-org-node-dept:text-is("{department_name}"))'
        ).first

    def is_node_visible(self, department_name: str) -> bool:
        try:
            return self._node(department_name).is_visible()
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible's contract
            return False

    def reload_until_node_matches(
        self,
        department_name: str,
        expected_visible: bool,
        timeout_ms: int = PROPAGATION_POLL_TIMEOUT_MS,
        interval_ms: int = PROPAGATION_POLL_INTERVAL_MS,
    ) -> bool:
        """Poll (reload + is_node_visible check), never a single cold read
        — ADDED 2026-09-14 (Group A/tc_133294 triage). Mirrors
        HomeHeroBannerPage.reload_until_title_in_carousel()'s own already-
        established pattern in this same test suite for the identical
        class of check (admin deactivates/reactivates -> the frontend read
        needs a real retry window for cache propagation, not an immediate
        single reload)."""
        import time

        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_org_structure()
            if self.is_node_visible(department_name) == expected_visible:
                return True
            if time.monotonic() >= deadline:
                return self.is_node_visible(department_name) == expected_visible
            self.page.wait_for_timeout(interval_ms)

    def reload_until_default_avatar_matches(
        self,
        department_name: str,
        expected_default: bool,
        timeout_ms: int = PROPAGATION_POLL_TIMEOUT_MS,
        interval_ms: int = PROPAGATION_POLL_INTERVAL_MS,
    ) -> bool:
        """Poll (reload + node_has_default_avatar check), never a single cold
        read — ADDED 2026-09-15 (tc_133345/tc_133346 healing re-investigation).
        Mirrors reload_until_node_matches()'s own already-established pattern
        exactly (same class of publish-then-verify propagation gap: a single
        open_org_structure() immediately after admin.save() can race delivery-
        surface propagation for a brand-new department entry, the same way it
        already does for a plain node-visibility read)."""
        import time

        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_org_structure()
            if self.node_has_default_avatar(department_name) == expected_default:
                return True
            if time.monotonic() >= deadline:
                return self.node_has_default_avatar(department_name) == expected_default
            self.page.wait_for_timeout(interval_ms)

    def node_person_name(self, department_name: str) -> str:
        return self._node(department_name).locator(self.NODE_PERSON_NAME).inner_text()

    def node_person_title(self, department_name: str) -> str:
        return self._node(department_name).locator(self.NODE_PERSON_TITLE).inner_text()

    def node_has_default_avatar(self, department_name: str) -> bool:
        return self._node(department_name).locator(self.NODE_AVATAR_DEFAULT).count() > 0

    def node_computed_style(self, locator, props: list) -> dict:
        """Generic Figma-token probe: computed CSS of the first match of a
        BasePage-style string locator, restricted to the requested props."""
        handle = self.page.locator(locator).first
        return handle.evaluate(
            """
            (el, props) => {
                const s = getComputedStyle(el);
                const out = {};
                for (const p of props) out[p] = s[p];
                return out;
            }
            """,
            props,
        )

    def node_dept_locator(self, department_name: str) -> str:
        return f'.qc-org-node:has(.qc-org-node-dept:text-is("{department_name}")) .qc-org-node-dept'

    def node_person_name_locator(self, department_name: str) -> str:
        return f'.qc-org-node:has(.qc-org-node-dept:text-is("{department_name}")) .qc-org-node-name'

    def node_person_title_locator(self, department_name: str) -> str:
        return f'.qc-org-node:has(.qc-org-node-dept:text-is("{department_name}")) .qc-org-node-title'

    def child_department_order(self, parent_name: str) -> list:
        """Ordered (DOM-rendered) list of `parent_name`'s DIRECT children
        department names — CONFIRMED LIVE 2026-09-07 (tc_133295): a
        parent's children render as a `<ul>` nested directly inside that
        parent's own `<li>` (same structural fact `is_child_nested_under_
        parent()` already relies on for membership), and that `<ul>`'s own
        `<li>` order is confirmed live to follow each child's own admin-set
        Display Order value ascending (lower value first) — used here to
        assert a Display Order change actually reorders the rendered
        sibling sequence, not just the raw field value. `:scope > ul > li`
        scopes to DIRECT children only (never grandchildren) relative to
        the parent's own `<li>`."""
        parent_li = self.page.locator(
            f'li:has(> .qc-org-node .qc-org-node-dept:text-is("{parent_name}"))'
        ).first
        return parent_li.locator(
            ':scope > ul > li > .qc-org-node .qc-org-node-dept'
        ).all_inner_texts()

    def is_child_nested_under_parent(self, parent_name: str, child_name: str) -> bool:
        """Structural parent/child check (case 133260/133365): the org chart
        renders each node's children as a <ul> nested INSIDE that node's own
        <li>, so "a connector visually links child to parent" is equivalent
        to, and verified here as, "child_name's card is a DOM descendant of
        parent_name's <li>" — cheaper and more deterministic than asserting
        on SVG paint of a connector line."""
        parent_li = self.page.locator(
            f'li:has(> .qc-org-node .qc-org-node-dept:text-is("{parent_name}"))'
        ).first
        return parent_li.locator(
            f'.qc-org-node-dept:text-is("{child_name}")'
        ).count() > 0

    def reload_until_child_nested(
        self,
        parent_name: str,
        child_name: str,
        expected_nested: bool = True,
        timeout_ms: int = PROPAGATION_POLL_TIMEOUT_MS,
        interval_ms: int = PROPAGATION_POLL_INTERVAL_MS,
    ) -> bool:
        """Poll (reload + is_child_nested_under_parent check), never a
        single cold read — HEALED 2026-09-15 (tc_133326 healing session):
        CONFIRMED LIVE a single `open_org_structure()` + immediate
        `is_child_nested_under_parent()` read can race delivery-surface
        propagation for a brand-new department entry the same way
        `reload_until_node_matches()` above already documents for a plain
        visibility check (same class of gap, same fix shape) — a fresh
        admin-side read confirmed the entry was genuinely Approved with the
        correct Parent Department value, yet the immediately-following
        single frontend read still reported no nesting. Mirrors
        `reload_until_node_matches()`'s own already-established pattern
        exactly."""
        import time

        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_org_structure()
            if self.is_child_nested_under_parent(parent_name, child_name) == expected_nested:
                return True
            if time.monotonic() >= deadline:
                return self.is_child_nested_under_parent(parent_name, child_name) == expected_nested
            self.page.wait_for_timeout(interval_ms)

    # ---- Expand / collapse ----------------------------------------------
    def _toggle_branch_button(self, department_name: str):
        return self._node(department_name).locator(
            'role=button[name="Toggle branch"]'
        )

    def toggle_branch(self, department_name: str) -> "OrgStructurePage":
        # CONFIRMED LIVE, 2026-08-25: string-concatenating plain CSS with a
        # bare-space "role=..." engine prefix is not valid Playwright
        # selector syntax outside of explicit ">>" chaining — Playwright
        # parses the whole string as CSS and throws
        # `Unexpected token "=" while parsing selector`. Reuse the
        # correctly-written `_toggle_branch_button()` helper (chained
        # `.locator().locator()` calls) instead of re-deriving a broken
        # selector string here.
        self._toggle_branch_button(department_name).click()
        return self

    def is_branch_expanded(self, department_name: str) -> bool:
        return self._toggle_branch_button(department_name).get_attribute("aria-expanded") == "true"

    def is_descendant_visible(self, department_name: str) -> bool:
        return self.is_node_visible(department_name)

    def expand_all(self) -> "OrgStructurePage":
        self.click(self.EXPAND_ALL_BTN)
        return self

    def collapse_all(self) -> "OrgStructurePage":
        self.click(self.COLLAPSE_ALL_BTN)
        return self

    # ---- Search -----------------------------------------------------------
    def search(self, term: str) -> "OrgStructurePage":
        self.type(self.SEARCH_INPUT, term)
        return self

    def matched_department_texts(self) -> list:
        return self.page.locator(self.MATCHED_ITEM).all_inner_texts()

    def is_empty_state_visible(self) -> bool:
        return self.is_visible(self.SEARCH_EMPTY_STATE)

    def empty_state_text(self) -> str:
        return self.text(self.SEARCH_EMPTY_STATE)

    # ---- Zoom / view controls ----------------------------------------------
    def zoom_percentage(self) -> int:
        raw = self.text(self.ZOOM_INDICATOR).strip().rstrip("%")
        return int(raw)

    def click_zoom_in(self, times: int = 1) -> "OrgStructurePage":
        for _ in range(times):
            self.click(self.ZOOM_IN_BTN)
        return self

    def click_zoom_out(self, times: int = 1) -> "OrgStructurePage":
        for _ in range(times):
            self.click(self.ZOOM_OUT_BTN)
        return self

    def reset_view(self) -> "OrgStructurePage":
        self.click(self.RESET_VIEW_BTN)
        return self

    def toggle_fullscreen(self) -> "OrgStructurePage":
        self.click(self.FULLSCREEN_TOGGLE_BTN)
        return self

    def is_fullscreen_active(self) -> bool:
        return bool(self.page.evaluate("() => !!document.fullscreenElement"))
