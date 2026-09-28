"""
core/web/base_page.py — BasePage wrapper. The only place raw Playwright is
touched besides browser.py. Self-waiting, self-logging, self-screenshotting —
per the wrapper API table in automation-standards.md. No time.sleep(), no
bare asserts (Page Objects expose state; tests assert).
"""

import os

from core.utils.logger import get_logger, log_action
from core.utils.reporting import attach_screenshot
from core.web.license_gate import clear_license_gate, is_gate_showing, remember_target
from core.web.overlays import (
    ANNOUNCEMENT_ROOT,
    MOUNT_GRACE_MS,
    dismiss_overlays,
    is_overlay_showing,
)
from core.web.session_guard import is_login_form_showing, reauthenticate
from config.settings import settings

logger = get_logger("base_page")

# Marker for a navigation that is ITSELF the login flow (CmsLoginPage.open_login()
# / the Liferay login portlet's own render/redirect URLs) — same string
# overlays.py's _current_surface() already keys on for the identical reason.
# The login form is expected to be showing on this URL; that is not a dropped
# session, and reauthenticate()'s own login submission must not fire here or
# it races CmsLoginPage.login()'s subsequent type()/click() calls on a page
# that has since navigated away (confirmed live 2026-08-25 — see
# session_guard.py's reentrancy note for the sibling fix in type()).
_LOGIN_FLOW_MARKERS = ("/c/portal/login", "com_liferay_login_web_portlet_LoginPortlet")


def _is_login_flow_url(url: str) -> bool:
    return any(marker in (url or "") for marker in _LOGIN_FLOW_MARKERS)


# Explicit, bounded page-load budget for every navigation this wrapper makes.
# Playwright's own default is 30 000 ms, which is what `page.goto()` silently
# used here. Measured 2026-09-28: ADO-141825 and ADO-141832 both PASS
# standalone (~35 s wall each, homepage load well inside 30 s) but failed the
# parallel suite run with `TimeoutError: Timeout 30000ms exceeded` — qcdev
# serves the homepage more slowly when several xdist workers hit it at once.
# This is genuine slowness, not an unreachable condition, so the one specific
# timeout is raised rather than a sleep added or a wait removed. Still
# bounded, still env-overridable for a slower environment.
NAVIGATION_TIMEOUT_MS = int(os.getenv("NAV_TIMEOUT_MS") or 60000)


class BasePage:
    def __init__(self, page):
        self.page = page

    def open(self, url: str) -> None:
        remember_target(self.page, url)
        self.page.goto(url, timeout=NAVIGATION_TIMEOUT_MS)
        # Site-wide interstitial guard (see core/web/license_gate.py). No-op
        # when the interstitial is absent, which is the normal path.
        clear_license_gate(self.page, url)
        # qcdev's session drops roughly every ~30s under sustained automated
        # traffic (see core/web/session_guard.py) — a reset can land back on
        # the login form. No-op when already authenticated. Skipped when the
        # navigation target IS the login flow itself (see _is_login_flow_url).
        if not _is_login_flow_url(url):
            reauthenticate(self.page, url)
        # Site-wide blocking overlays (see core/web/overlays.py). Client-
        # rendered, so a mount grace is allowed here and only here.
        dismiss_overlays(self.page, grace_ms=MOUNT_GRACE_MS)
        log_action(logger, "open", url)

    def open_anonymous(self, url: str) -> None:
        """Navigate a genuinely anonymous/logged-out context (e.g. a
        `new_context(browser, use_auth_state=False)` public-visibility
        check) without ever calling `reauthenticate()`. `open()` above
        unconditionally reauthenticates on any non-login-flow URL if it
        detects a login form — correct for the normal authenticated flow,
        but on an intentionally anonymous context that would silently log
        the shared TEST_USER/TEST_PASSWORD back in the moment a login form
        rendered, defeating the whole point of an anonymous read and
        producing a false result on a public-visibility/draft/unpublish
        check (see standards.md's "Draft/Unpublish Public-Visibility
        Checks — Mandatory Logged-Out Context"). Only clears the
        credential-free interstitial (license gate) and the site-wide
        announcement overlay — neither of which authenticates anything.
        Callers still do their own post-navigation waits (e.g. for their
        own page's heading) since what to wait for is page-specific."""
        self.page.goto(url, timeout=NAVIGATION_TIMEOUT_MS)
        clear_license_gate(self.page, url)
        dismiss_overlays(self.page, grace_ms=MOUNT_GRACE_MS)
        log_action(logger, "open_anonymous", url)

    def open_anonymous_keeping_overlays(self, url: str, grace_ms: int = MOUNT_GRACE_MS) -> None:
        """Anonymous navigation that deliberately does NOT dismiss the
        site-wide overlay registry — for the handful of cases whose SUBJECT
        is the announcement modal itself (focus trap, close-returns-focus,
        mid-sequence interruption; PBI 131054). Every other test must keep
        using `open()` / `open_anonymous()`, which dismiss it, so an
        unrelated test never has its clicks intercepted.

        Still clears the credential-free license interstitial (it is not an
        overlay under test and would replace the whole page), then waits up
        to `grace_ms` for the client-rendered overlay to mount — the same
        grace `dismiss_overlays()` pays — so the caller's own
        "is the modal showing?" read does not race the mount."""
        self.page.goto(url, timeout=NAVIGATION_TIMEOUT_MS)
        clear_license_gate(self.page, url)
        try:
            self.page.locator(ANNOUNCEMENT_ROOT).first.wait_for(
                state="visible", timeout=grace_ms
            )
        except Exception:  # noqa: BLE001 — absent overlay is a state the caller asserts on
            pass
        log_action(logger, "open_anonymous_keeping_overlays", url)

    def click(self, locator: str, position: dict | None = None) -> None:
        # `position` (e.g. {"x": 10, "y": 10}, viewport-relative to the
        # element's own top-left) is the escape hatch for a large element
        # (e.g. a full-viewport modal overlay) whose default center-click
        # point is itself geometrically covered by a smaller element mounted
        # on top of it (see PodcastPage.close_popup_via_overlay/TC 143527).
        # The session can drop between two calls on this page (open_x() then
        # click(), no wait_for() in between) — check before spending the
        # click's own timeout on a page that's actually the license gate or
        # the login form underneath. Skipped on the login flow's own URL
        # (see _is_login_flow_url) — CmsLoginPage.login() clicking its own
        # submit button while its own form is visible is not a dropped
        # session, and firing reauthenticate() here races login()'s own
        # subsequent calls on a page that has since navigated away
        # (confirmed live 2026-08-25 — same reentrancy bug as type() below).
        on_login_flow = _is_login_flow_url(self.page.url)
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if not on_login_flow and is_login_form_showing(self.page):
            reauthenticate(self.page)
        try:
            self.page.locator(locator).click(position=position)
        except Exception:
            # An overlay that mounted late (or reappeared after a click-driven
            # navigation) intercepts the click, OR the session dropped mid-
            # click. Clear whichever applies and retry once before surfacing
            # this as a real failure.
            recovered = dismiss_overlays(self.page)
            recovered = clear_license_gate(self.page) or recovered
            if not on_login_flow:
                recovered = reauthenticate(self.page) or recovered
            if not recovered:
                raise
            self.page.locator(locator).click(position=position)
        log_action(logger, "click", locator)

    def double_click(self, locator: str) -> None:
        """Two near-simultaneous clicks on one element — the wrapper form of
        Playwright's `dblclick()`. Added 2026-09-23 for the rapid
        double-activation edge cases (a control that must not append its
        payload twice); it exists here, not in a Page Object, so no feature
        object or test ever touches raw Playwright for it. Same gate/session
        pre-check and single overlay-recovery retry as `click()` above."""
        on_login_flow = _is_login_flow_url(self.page.url)
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if not on_login_flow and is_login_form_showing(self.page):
            reauthenticate(self.page)
        try:
            self.page.locator(locator).dblclick()
        except Exception:
            recovered = dismiss_overlays(self.page)
            recovered = clear_license_gate(self.page) or recovered
            if not on_login_flow:
                recovered = reauthenticate(self.page) or recovered
            if not recovered:
                raise
            self.page.locator(locator).dblclick()
        log_action(logger, "double_click", locator)

    def type(self, locator: str, text: str) -> None:
        # Same session-drop window as click() — a multi-field form fills
        # several locators in a row, any of which can outlive one ~30s
        # qcdev session window. Skipped on the login flow's own URL (see
        # click()'s comment and _is_login_flow_url) — filling the login
        # form's own username/password fields must not trigger a redundant
        # background reauthenticate() (confirmed live 2026-08-25: it logged
        # in, navigated to an unrelated page, and left this type() call
        # waiting 30s on a username field that no longer existed there).
        on_login_flow = _is_login_flow_url(self.page.url)
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if not on_login_flow and is_login_form_showing(self.page):
            reauthenticate(self.page)
        loc = self.page.locator(locator)
        try:
            loc.clear()
            loc.fill(text)
        except Exception:
            # Same recovery as click(): a late-mounting overlay (or a
            # session drop) can block a fill() the same way it blocks a
            # click() — confirmed live 2026-08-25 (qcdev), the announcement
            # overlay intercepting the login username field caused a bare
            # 30s TimeoutError here with no recovery attempted, because
            # type() previously had no retry path at all. Mirrors click()'s
            # retry exactly rather than inventing a separate one.
            recovered = dismiss_overlays(self.page)
            recovered = clear_license_gate(self.page) or recovered
            if not on_login_flow:
                recovered = reauthenticate(self.page) or recovered
            if not recovered:
                raise
            loc.clear()
            loc.fill(text)
        log_action(logger, "type", locator, text)

    def text(self, locator: str) -> str:
        return self.page.locator(locator).inner_text()

    def is_visible(self, locator: str) -> bool:
        try:
            # An interstitial or a dropped session would make every locator
            # report "not visible", which silently turns a blocked page into
            # a passing negative assertion. Clear both first, then answer
            # honestly.
            if is_gate_showing(self.page):
                clear_license_gate(self.page)
            if is_login_form_showing(self.page):
                reauthenticate(self.page)
            return self.page.locator(locator).is_visible()
        except Exception:  # noqa: BLE001 — never throws, per the wrapper contract
            return False

    def wait_for(self, locator: str, state: str = "visible", timeout: int = 10000, first: bool = False) -> None:
        # Covers click-driven navigation too (the Page Objects wait on an
        # element after every click), not just the explicit open() above.
        #
        # `first`: pass True when the call is only confirming "at least one
        # match rendered" (e.g. a grid that legitimately has >1 row) rather
        # than targeting one specific element — without it, Playwright's
        # strict mode throws on a locator matching more than one element.
        # Kept inside this wrapper (not a raw `.first` at the call site) so
        # every Page Object call still gets the gate/reauth handling below,
        # including the post-recovery retry and the after-wait overlay
        # check — none of that is optional, per this method's own docstring
        # notes on click-driven navigation re-arming interstitials.
        target = self.page.locator(locator).first if first else self.page.locator(locator)
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if is_login_form_showing(self.page):
            reauthenticate(self.page)
        try:
            target.wait_for(state=state, timeout=timeout)
        except Exception:
            # The interstitial or a dropped session can also arrive
            # mid-wait; clear once and retry before surfacing the timeout as
            # a real failure.
            recovered = clear_license_gate(self.page)
            recovered = reauthenticate(self.page) or recovered
            if not recovered:
                raise
            target.wait_for(state=state, timeout=timeout)
        # Checked AFTER the wait, zero-wait: click-driven navigation re-renders
        # the announcement overlay (it stores no dismissal flag), and by the
        # time the awaited element exists the overlay has normally mounted too.
        # Anything that still slips through is caught by click()'s retry.
        if is_overlay_showing(self.page):
            dismiss_overlays(self.page)

    def wait_for_class_on_nth(self, locator: str, index: int, class_name: str,
                              timeout: int = 10000) -> None:
        """Waits until the nth (0-based) match of `locator` carries
        `class_name`.

        Needed for class states that a page applies ASYNCHRONOUSLY after an
        interaction (smooth-scroll + scroll-spy highlighting, for example):
        click() returns as soon as the click dispatches, several frames
        before the class lands, so reading the state immediately returns the
        PREVIOUS one. Waiting on the class of the specific element under
        test — not on "some element has it" — is what makes that read
        deterministic.
        """
        self.page.wait_for_function(
            """([selector, index, className]) => {
                const nodes = document.querySelectorAll(selector);
                const el = nodes[index];
                return !!el && el.classList.contains(className);
            }""",
            arg=[locator, index, class_name],
            timeout=timeout,
        )
        log_action(logger, "wait_for_class_on_nth", locator, f"[{index}].{class_name}")

    def wait_for_url(self, url_pattern, timeout: int = 15000) -> None:
        """Waits for the page URL to match `url_pattern` (glob/regex/callable,
        per Playwright's page.wait_for_url).

        Use after any click that triggers navigation: click() resolves on
        dispatch, so a page.url read right after it can still return the
        ORIGIN url and make a navigation assertion pass or fail on timing.
        """
        self.page.wait_for_url(url_pattern, timeout=timeout)
        log_action(logger, "wait_for_url", str(url_pattern), self.page.url)

    def get_attribute(self, locator: str, name: str) -> str | None:
        return self.page.locator(locator).get_attribute(name)

    def select_option(self, locator: str, label: str = None, value: str = None) -> None:
        self.page.locator(locator).select_option(label=label, value=value)
        log_action(logger, "select_option", locator, label or value)

    def set_checkbox(self, locator: str, checked: bool) -> None:
        loc = self.page.locator(locator)
        if checked:
            loc.check()
        else:
            loc.uncheck()
        log_action(logger, "set_checkbox", locator, str(checked))

    def upload_file(self, locator: str, file_path: str) -> None:
        self.page.locator(locator).set_input_files(file_path)
        log_action(logger, "upload_file", locator, file_path)

    def press_key(self, key: str) -> None:
        self.page.keyboard.press(key)
        log_action(logger, "press_key", key)

    def is_focused(self, locator: str) -> bool:
        try:
            return self.page.locator(locator).evaluate("el => el === document.activeElement")
        except Exception:  # noqa: BLE001 — never throws, mirrors is_visible's contract
            return False

    def press_tab_until_focused(self, locator: str, max_presses: int = 25) -> bool:
        """Generic keyboard-only reach helper for focus-indicator /
        keyboard-navigation cases: presses Tab up to `max_presses` times,
        returning True as soon as `locator` becomes document.activeElement."""
        for _ in range(max_presses):
            if self.is_focused(locator):
                return True
            self.press_key("Tab")
        return self.is_focused(locator)

    # ── Generic keyboard-navigation / focus machinery ───────────────────
    # Added 2026-09-23 for PBI 131054 ("QC - 001 - Keyboard Navigation").
    # Everything here is selector-free and site-agnostic — no `qc-` class,
    # no page knowledge — so it belongs in core/ next to is_focused() /
    # press_tab_until_focused() rather than in the feature Page Object
    # (automation-standards.md: "core/ is generic").

    # Stable identity string for one element. Defined ONCE as a JS snippet
    # and interpolated into every query below, so the focus-walk list and the
    # clickable list are built by exactly the same function and are directly
    # comparable (ADO-141834). Three hand-copied versions of this expression
    # would be precisely the duplication the redundancy scan exists to catch.
    _ELEMENT_KEY_FN = r"""
      const __key = (el) => el.tagName.toLowerCase()
        + '#' + (el.id || '')
        + '.' + (el.getAttribute('class') || '').trim().replace(/\s+/g, '.')
        + '[' + (el.getAttribute('href') || el.getAttribute('aria-label') || '') + ']'
        + '{' + (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40) + '}';
    """

    # One compact, JSON-safe descriptor of document.activeElement. Used by
    # every tab-order / focus-indicator case, so the shape a test asserts on
    # is defined exactly once.
    _ACTIVE_ELEMENT_JS = r"""() => {
      __KEY_FN__
      const el = document.activeElement;
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const outlineVisible = cs.outlineStyle !== 'none' && cs.outlineStyle !== ''
          && cs.outlineWidth !== '0px'
          && cs.outlineColor !== 'transparent' && cs.outlineColor !== 'rgba(0, 0, 0, 0)';
      const shadowVisible = !!cs.boxShadow && cs.boxShadow !== 'none'
          && !/^rgba\(0, 0, 0, 0\) 0px 0px 0px 0px$/.test(cs.boxShadow);
      const isBody = el === document.body;
      return {
        key: isBody ? null : __key(el),
        tag: el.tagName.toLowerCase(),
        id: el.id || '',
        className: (el.getAttribute('class') || ''),
        role: el.getAttribute('role') || '',
        ariaLabel: el.getAttribute('aria-label') || '',
        href: el.getAttribute('href') || '',
        text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60),
        isBody,
        x: Math.round(rect.x), y: Math.round(rect.y),
        // DOCUMENT coordinates, not viewport ones: a tab walk scrolls the
        // page, so viewport y is meaningless for comparing two stops'
        // reading order, while docX/docY are stable across the whole walk.
        docX: Math.round(rect.left + window.scrollX),
        docY: Math.round(rect.top + window.scrollY),
        width: Math.round(rect.width), height: Math.round(rect.height),
        rendered: rect.width > 0 && rect.height > 0,
        outlineStyle: cs.outlineStyle, outlineWidth: cs.outlineWidth,
        outlineColor: cs.outlineColor, boxShadow: cs.boxShadow,
        borderStyle: cs.borderStyle, borderWidth: cs.borderWidth,
        borderColor: cs.borderColor, backgroundColor: cs.backgroundColor,
        outlineVisible, shadowVisible,
        hasVisibleFocusIndicator: outlineVisible || shadowVisible,
      };
    }""".replace("__KEY_FN__", _ELEMENT_KEY_FN)

    # Every element a MOUSE user can click, in DOCUMENT order, as the same
    # identity strings the focus walk produces.
    _CLICKABLE_SNAPSHOT_JS = r"""() => {
      __KEY_FN__
      const SEL = 'a[href],button,input,select,textarea,summary,'
        + '[role=button],[role=link],[role=tab],[role=menuitem],[onclick]';
      const out = [];
      document.querySelectorAll(SEL).forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return;          // not clickable
        const cs = getComputedStyle(el);
        if (cs.visibility === 'hidden' || cs.display === 'none') return;
        if (el.hasAttribute('disabled') || el.getAttribute('aria-hidden') === 'true') return;
        if (el.getAttribute('tabindex') === '-1') return;      // deliberately skipped
        out.push(__key(el));
      });
      return [...new Set(out)];
    }""".replace("__KEY_FN__", _ELEMENT_KEY_FN)

    def active_element(self) -> dict | None:
        """Descriptor of the currently focused element — identity, geometry
        and the computed styles a focus-indicator assertion needs. `None`
        only when there is no activeElement at all."""
        return self.page.evaluate(self._ACTIVE_ELEMENT_JS)

    def active_element_key(self) -> str | None:
        """Stable identity string for the focused element (`None` when focus
        rests on `<body>`, i.e. nothing is really focused)."""
        descriptor = self.active_element()
        return descriptor.get("key") if descriptor else None

    def blur_active_element(self) -> None:
        """Reset focus to the document start so a tab walk begins from a
        known state — the keyboard-only equivalent of a fresh load, without
        re-navigating (and without re-showing dismissed overlays)."""
        self.page.evaluate(
            "() => { if (document.activeElement && document.activeElement.blur) "
            "document.activeElement.blur(); document.body.focus(); }"
        )
        log_action(logger, "blur_active_element", "document.body")

    def tab_sequence(self, presses: int, key: str = "Tab") -> list:
        """Press `key` `presses` times, returning the active-element
        descriptor after EACH press (index 0 = after the first press)."""
        sequence = []
        for _ in range(presses):
            self.press_key(key)
            sequence.append(self.active_element())
        return sequence

    def focus_walk(self, max_presses: int, key: str = "Tab") -> dict:
        """Walk the whole focus ring: press `key` up to `max_presses` times,
        collecting one descriptor per stop and stopping EARLY once focus
        cycles back to the first element reached (a completed loop). Stops
        where focus rests on `<body>` (the wrap point in Chromium) are
        recorded but do not terminate the walk.

        Returns a REPORT, not a bare list::

            {"stops": [...], "completed": bool,
             "presses": int, "max_presses": int}

        `completed` is True only when the ring actually closed — focus came
        back to the first element the walk reached. When the press budget ran
        out first, `completed` is False and `stops` holds a PARTIAL, prefix-
        only view of the page's focusable set.

        FALSE-GREEN GUARD (added 2026-09-28, ADO-141835). This used to return
        the bare list, so a caller had no way to tell a whole-page walk from a
        truncated one. The homepage grew from 154 to 185 mouse-clickable
        elements, the 200-press budget stopped the walk short of the footer,
        and `test_focus_indicator_never_becomes_invisible_while_tabbing`
        PASSED — certifying a real, filed focus-visibility defect
        (`input.qc-footer-input`, Azure bug #147180) as working, because the
        offending element was simply never reached. Any test that asserts a
        property "across every focusable element" MUST now fail loudly when
        `completed` is False instead of silently judging a partial set.

        Bounded by `max_presses` on purpose — an unbounded walk on a page
        whose focusable set changes underneath it (an auto-rotating carousel)
        would never terminate."""
        stops = []
        first = None
        completed = False
        for _ in range(max_presses):
            self.press_key(key)
            descriptor = self.active_element()
            stops.append(descriptor)
            k = descriptor.get("key") if descriptor else None
            if k is None:
                continue
            if first is None:
                first = k
            elif k == first:
                completed = True
                break
        return {
            "stops": stops,
            "completed": completed,
            "presses": len(stops),
            "max_presses": max_presses,
        }

    def clickable_element_keys(self) -> list:
        """Identity strings of every mouse-clickable element currently
        rendered — the comparison set for "nothing is mouse-only"."""
        return self.page.evaluate(self._CLICKABLE_SNAPSHOT_JS)

    def focus_style(self, locator: str) -> dict:
        """Computed focus-relevant styles of a specific element (whether or
        not it is currently focused)."""
        return self.page.locator(locator).evaluate(
            "el => { const cs = getComputedStyle(el); return {"
            "outlineStyle: cs.outlineStyle, outlineWidth: cs.outlineWidth,"
            "outlineColor: cs.outlineColor, boxShadow: cs.boxShadow,"
            "borderStyle: cs.borderStyle, borderWidth: cs.borderWidth,"
            "borderColor: cs.borderColor, backgroundColor: cs.backgroundColor}; }"
        )

    def wait_for_computed_style(self, locator: str, expected: dict,
                                timeout: int = 5000) -> bool:
        """Wait until every named computed-style property of `locator`
        matches `expected`. Focus rings on this site are CSS-TRANSITIONED, so
        the instant focus moves away the old element still reports a decaying
        box-shadow — a same-tick "is it back to its default rendering?" read
        is a guaranteed flake. Bounded and condition-based (no `sleep`).

        Takes the element as a JSHandle rather than re-querying by selector
        inside the page, because this framework's locators use Playwright's
        `>>` chaining and `:has-text()` pseudo-classes, which
        `document.querySelector` cannot parse.

        Returns True if the styles settled, False on timeout — the caller
        asserts; a Page Object never does."""
        handle = self.page.locator(locator).first.element_handle()
        try:
            self.page.wait_for_function(
                "([el, want]) => { const cs = getComputedStyle(el); "
                "return Object.keys(want).every(k => cs[k] === want[k]); }",
                arg=[handle, expected],
                timeout=timeout,
            )
            settled = True
        except Exception:  # noqa: BLE001 — a timeout is an observation, not an error
            settled = False
        log_action(logger, "wait_for_computed_style", locator, str(settled))
        return settled

    def wait_for_condition(self, js_expression: str, arg=None, timeout: int = 10000) -> None:
        """Condition-based wait on an arbitrary page predicate — the
        no-`sleep()` escape hatch for state with no DOM/network signal of its
        own (e.g. a CSS transition finishing). Wraps Playwright's
        `page.wait_for_function`."""
        self.page.wait_for_function(js_expression, arg=arg, timeout=timeout)
        log_action(logger, "wait_for_condition", js_expression[:60])

    def fill_iframe_editor(self, iframe_locator: str, text: str) -> None:
        """Write into a classic (iframe-based) CKEditor's editable body —
        e.g. `iframe[title="editor"]`. The field's own OUTER wrapper
        (`[role="textbox"][aria-label=...]`) is a non-editable mount point
        only; the real `[contenteditable]` document lives inside this
        iframe and does not exist in the DOM until the wrapper is clicked
        once to force the widget to mount (confirmed live on this project —
        see home_strategic_direction_admin_page.py's PILLAR_DESCRIPTION
        fields for the reproduction). Callers must click the wrapper (or
        otherwise trigger the mount) and wait for the iframe to render
        before calling this. Uses frame_locator (not `.content_frame()` on
        a Locator, which this project's pinned Playwright version does not
        expose) plus a real keyboard select-all + type — never
        `page.evaluate()` into the frame, which would bypass CKEditor's own
        input handling and prove nothing about the real widget."""
        on_login_flow = _is_login_flow_url(self.page.url)
        if is_gate_showing(self.page):
            clear_license_gate(self.page)
        if not on_login_flow and is_login_form_showing(self.page):
            reauthenticate(self.page)
        body = self.page.frame_locator(iframe_locator).locator("body")
        body.wait_for(state="visible")
        body.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.type(text)
        log_action(logger, "fill_iframe_editor", iframe_locator, text)

    def iframe_editor_text(self, iframe_locator: str) -> str:
        """Read the CURRENT (possibly unsaved) editable text out of a
        classic CKEditor iframe's body — the live counterpart to
        `fill_iframe_editor`. For reading a value that's already been
        SAVED and reloaded, prefer a Page Object's own persisted-value
        read (e.g. from the portlet's embedded field-config JSON) where
        one exists — this method reflects only what's currently rendered
        in the iframe on the open form."""
        return self.page.frame_locator(iframe_locator).locator("body").inner_text()

    def screenshot(self, test_case_id: str = "NO-TC") -> bytes:
        png = self.page.screenshot()
        attach_screenshot(png, test_case_id, settings.project_name)
        return png

    def assert_visible(self, locator: str, test_case_id: str = "NO-TC") -> None:
        if not self.is_visible(locator):
            self.screenshot(test_case_id)
            raise AssertionError(f"expected visible: {locator}")

    def assert_text(self, locator: str, expected: str, test_case_id: str = "NO-TC") -> None:
        actual = self.text(locator)
        if actual != expected:
            self.screenshot(test_case_id)
            raise AssertionError(f"expected text {expected!r} at {locator}, got {actual!r}")
