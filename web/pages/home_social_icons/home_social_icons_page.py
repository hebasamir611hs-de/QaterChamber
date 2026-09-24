"""
web/pages/home_social_icons/home_social_icons_page.py — HomeSocialIconsPage.

Web/public Page Object for PBI 129373 (QC-HOME-004B — Social Media Icons) —
the dedicated Home Page "Find us on social media" section. Built as a
dependency of this PBI's Control_Panel batch (see
cms/tests/home_social_icons/test_home_social_icons_control_panel.py, which
must verify the live public effect of a CMS publish/edit/unpublish action,
never just the authoring UI — cms-testing.md's dual-surface rule).

CONFIRMED LIVE 2026-09-07 (anonymous/logged-out Playwright session against
`https://qcdev.ihorizons.com/en/home`, 1920x1080 viewport — deliberately NO
storageState, mirroring standards.md's "Draft/Unpublish Public-Visibility
Checks — Mandatory Logged-Out Context" rule even for this read-only Page
Object, since every caller of it in the CMS test module is checking public
visibility of a CMS-authored entry):

  - The section is `div.qc-home-social` (`data-qc-social-root` attribute,
    confirmed unique) — CONFIRMED DISTINCT from the Footer's own social
    icons block (`div.qc-footer-social-wrap`), which independently renders
    the SAME 8 seeded entries via `ul.qc-footer-social` — see the sibling
    admin Page Object's module docstring for the full "one object, two
    sections" finding. This Page Object only ever queries the HOME section
    (`SECTION` below), never the footer's.
  - Icons render as `ul.qc-social-list > li > a.qc-social-link`, one `<a>`
    per entry, in DOM order (this project's only observable notion of an
    icon's "position" — there is no separate numbered slot UI). Each
    anchor carries `href` (= the entry's own "Social Redirect URL" field,
    confirmed live to round-trip verbatim), `aria-label`/`title` (both =
    the entry's "Platform" enum value, e.g. "YouTube"), and
    `target="_blank" rel="noopener noreferrer"` (confirmed live present
    together, matching "Open in New Tab" = True on every seeded entry).
  - **CONFIRMED LIVE, LOAD-BEARING FINDING**: each anchor's icon glyph is
    an INLINE, per-platform-hardcoded `<svg class="qc-social-glyph">` —
    there is NO `<img>` element anywhere in this section. The "Social Icon
    Image" / "Home Icon Image" upload fields on the admin form do **not**
    appear to drive this section's rendered glyph at all (a real, disclosed
    product-behavior finding, not a locator gap — see the admin Page
    Object's own module docstring and the Control_Panel test module's own
    account of how ADO 131160's "uses the new image" assertion is scripted
    against this fact rather than silently dropped). `icon_uses_uploaded_image()`
    below checks for an `<img>` at all (there confirmed-live is none for
    the 8 seeded platforms) so a future finding here is asserted on
    honestly rather than assumed either way.
  - Since the "Platform" field is a small CLOSED enum already fully seeded
    (see admin Page Object), a test's own new/edited entry can share its
    Platform label with a pre-existing seeded row. `href` (built from the
    entry's own, test-unique "Social Redirect URL") is therefore the ONLY
    reliable way to identify "this test's own icon" among possibly
    same-labelled icons — every lookup method below is href-keyed, never
    label-keyed alone.
  - No propagation-latency measurement exists yet for this specific object
    in cms-profile.md (only the Board Members JAX-RS endpoint was probed).
    `reload_until()` mirrors the same bounded-poll shape (never a bare
    `sleep()`) other Home Page sections in this project already use
    (see HomeBusinessEventsPage.reload_until()), with a conservative
    default budget until a real measurement is recorded here.

ROOT-CAUSE INVESTIGATION (2026-09-07, triggered by a QA-Manager-vs-
automation discrepancy report on TC 131159/131160 — the QA Manager
manually tested both scenarios and observed a PASS where the automated
suite FAILED on the "position" assertion). This session went through TWO
rounds of live experiments before landing on the CONFIRMED, twice-
independently-verified answer below — the first round's conclusion was
itself wrong and is documented here (not silently deleted) as a caution
against the same mistake: a controlled experiment whose two data points
happen to TIE on one of the two candidate fields cannot distinguish
between them, and this session initially treated such a tie as proof.

  ROUND 1 (WRONG — superseded by ROUND 2 below): a brand-new entry was
  created with Display Order=6, Home Display Order left completely
  untouched (confirmed via its own raw JAX-RS record: `"homeDisplayOrder":
  0`, the untouched default). It rendered before all 8 seeded platforms,
  matching ascending Display Order. A second live artifact already present
  (`altText: "Test Icon"`, Display Order=2, Home Display Order=0 — TIED
  with the new entry on Home Display Order) rendered before it. This was
  read as proof Display Order drives position — but it is NOT proof: both
  compared entries were TIED at Home Display Order=0, so the observed
  order is equally explained by "Home Display Order ascending, tie broken
  by creation order" (the older "Test Icon" entry was created first) as by
  "Display Order ascending". The experiment could not distinguish the two
  hypotheses because it never varied Home Display Order independently of
  Display Order across a NON-tied pair.

  ROUND 2 (CONFIRMED, disambiguating): TC 131160 was replicated live —
  `QC-SMI-x`'s "Display Order" field (ONLY) was changed from 200 to 1,
  its "Home Display Order" field was NOT touched and stayed at its own
  real value, 200 (confirmed via its own JAX-RS record immediately after
  publish: `"displayOrder": 1, "homeDisplayOrder": 200` — these two DO
  diverge here, unlike Round 1's tied pair). The live Home page rendered
  this entry at position 3, NOT position 1. Sorting the full live catalog
  ascending by `displayOrder` predicts position 1 (WRONG — does not
  match). Sorting the SAME catalog ascending by `homeDisplayOrder`
  predicts position 3 (Test Icon@0, Facebook@100, X@200, ...) — EXACT
  MATCH. This is the clean, unambiguous, twice-checked (raw JAX-RS diff
  AND live DOM read, same session, both restored to baseline immediately
  after) proof: **"Home Display Order" is the field that actually drives
  the Home section's sort order. "Display Order" drives the Footer's own
  sort order (confirmed via its own separate, explicitly-sorted query —
  see below) and has NO effect on the Home section.** The object genuinely
  has TWO INDEPENDENT order fields, one per section — the ORIGINAL
  pre-investigation understanding of this object (documented in
  HomeSocialIconsAdminPage before this session's Round 1 mis-correction)
  was right all along.

  Network capture (Playwright MCP, both requests reproducible via a bare
  unauthenticated `curl`, both 200 with no cookies): the Home page's own
  script fetches `GET /o/c/socialmediaicons/scopes/<scopeId>?filter=active
  eq true and showOnHome eq true&pageSize=200` (no `sort=` param — raw
  payload is plain ascending internal id/creation order) and re-sorts it
  client-side; the DERIVED sort key, confirmed by the Round 2
  disambiguating diff above, is `homeDisplayOrder` ascending, NOT
  `displayOrder`. The Footer's own separate query,
  `GET .../scopes/<scopeId>?filter=active eq true&sort=displayOrder:asc
  &pageSize=200`, sorts server-side by `displayOrder` — confirming the two
  sections really do key off two different fields, each consistent with
  its own field's name.

  REAL SEEDED BASELINE (also corrected this session —
  HomeSocialIconsAdminPage's original "every entry ties at Display
  Order=500" claim was itself wrong, apparently read off only the YouTube
  row and over-generalized): Facebook=100, X=200, LinkedIn=300,
  Instagram=400, YouTube=500, WhatsApp=600, Telegram=700, Snapchat=800 —
  BOTH `displayOrder` AND `homeDisplayOrder` carry this same per-row value
  on every one of the 8 seeded rows (confirmed live via each row's own
  JAX-RS record) — a coincidence of how the seed data was authored (both
  fields set to the same per-platform value), not evidence the two fields
  are actually linked; Round 2's edit (changing ONLY `displayOrder` on one
  row) is what proves they are not.

WHY TC 131159/131160's LITERAL "position 6" / "position 1" ASSERTIONS
FAILED LIVE: both cases' own literal steps name only "Display Order" —
the FOOTER section's own field — never "Home Display Order", the field
that actually drives what these cases are asserting on (the HOME page's
own section). Per automation-standards.md's "no reinterpreting the case"
rule, the Control_Panel test module fills exactly the field the case's
steps literally name (Display Order) and does NOT invent setting "Home
Display Order" to make the literal number true — instead it asserts the
REAL, live-computed expected position derived from `homeDisplayOrder`
(via `expected_position_by_home_display_order()` below), which for TC
131159 (a field the case never touches, so it sits at its own schema
default) and TC 131160 (a field the case's own steps never change, so it
stays at its pre-edit baseline value) is NOT literally "6" or "1" — this
is disclosed as a real, case-vs-schema mismatch finding (see the
Control_Panel test module's own docstring/inline notes), not silently
adapted to make the case's literal wording appear to pass. QA Manager's
manual PASS on both scenarios is consistent with a human visually
confirming "the icon's position looks different/plausible after my edit"
without cross-checking the literal absolute index against the live
catalog — precisely the looseness an automated literal-equality assertion
does not have.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeSocialIconsPage(BasePage):
    HOME_PATH = "/en/home"

    SECTION = "div.qc-home-social"
    ICON_LIST = f"{SECTION} ul.qc-social-list"
    ICON_LINK = f"{ICON_LIST} li a.qc-social-link"

    # No project-specific propagation measurement exists yet for this
    # object (see module docstring) — this budget is a conservative
    # multiple over every OTHER Object-Authoring-backed section's own
    # measured figure on this project (all under ~3s), never a blind
    # guess, and is still a real, condition-based POLL, never a sleep.
    RELOAD_POLL_TIMEOUT_MS = 15000
    RELOAD_POLL_INTERVAL_MS = 1000

    def open_home(self) -> "HomeSocialIconsPage":
        self.open(web_url(self.HOME_PATH))
        self.wait_for(self.SECTION)
        return self

    def icon_hrefs(self) -> list[str]:
        """All icon hrefs in the Home section, in rendered (DOM) order —
        this project's only observable notion of icon "position"."""
        links = self.page.locator(self.ICON_LINK)
        return [links.nth(i).get_attribute("href") or "" for i in range(links.count())]

    def has_icon_with_href(self, href: str) -> bool:
        return href in self.icon_hrefs()

    def position_of_href(self, href: str) -> int:
        """1-indexed DOM position of the icon whose href matches exactly,
        or 0 if not present — mirrors the QA case's own "position N"
        wording (there is no other numbered-slot concept on this live
        page; see module docstring)."""
        hrefs = self.icon_hrefs()
        try:
            return hrefs.index(href) + 1
        except ValueError:
            return 0

    def platform_label_for_href(self, href: str) -> str:
        link = self.page.locator(f'{self.ICON_LINK}[href="{href}"]').first
        return link.get_attribute("aria-label") or ""

    def icon_uses_uploaded_image(self, href: str) -> bool:
        """True only if the icon for `href` renders as a real `<img>`
        (i.e. actually reflects an uploaded file) rather than this
        section's confirmed-live default inline SVG glyph — see module
        docstring's LOAD-BEARING FINDING. Never assumed either way."""
        link = self.page.locator(f'{self.ICON_LINK}[href="{href}"]').first
        return link.locator("img").count() > 0

    def icon_count(self) -> int:
        return self.page.locator(self.ICON_LINK).count()

    # ---- Expected-position ground truth (see module docstring's
    # ROOT-CAUSE INVESTIGATION, Round 2) — reads the SAME public,
    # unauthenticated JAX-RS endpoint the Home page's own front-end script
    # itself queries (confirmed live via network capture + a bare
    # cookie-less `curl`, both 200), used ONLY to compute what position an
    # entry's OWN Home Display Order value should rank at among whatever is
    # really live right now — never as the pass/fail signal itself (that
    # remains position_of_href(), read off the actual rendered DOM, per
    # cms-testing.md's public-surface rule). This replaces a hardcoded
    # literal-index expectation (e.g. "must be exactly position 6") that
    # only holds if the case's own steps had touched "Home Display Order"
    # — the field CONFIRMED LIVE (Round 2) to actually drive this section's
    # order — which neither TC 131159 nor TC 131160's literal steps do.
    JAXRS_SCOPE_ID = "37246"  # confirmed live 2026-09-07 — same scopeId every capture on this environment used
    JAXRS_ENTRIES_PATH = f"/o/c/socialmediaicons/scopes/{JAXRS_SCOPE_ID}"
    JAXRS_HOME_ORDER_FIELD = "homeDisplayOrder"

    def _live_home_display_orders_by_redirect_url(self) -> dict[str, int]:
        """`{redirectUrl: homeDisplayOrder}` for every entry CURRENTLY
        matching the exact filter the Home section's own front-end applies
        (`active eq true and showOnHome eq true`) — confirmed live
        2026-09-07 via network capture of the real /en/home page load. No
        `sort=` param: matches the real endpoint's own confirmed-live
        behavior (raw creation-order payload; the Home page's script does
        its own client-side sort by `homeDisplayOrder` ascending — see
        module docstring's Round 2 disambiguating evidence — which this
        method reproduces in expected_position_by_home_display_order()
        below)."""
        response = self.page.request.get(
            web_url(self.JAXRS_ENTRIES_PATH)
            + "?filter=active%20eq%20true%20and%20showOnHome%20eq%20true&pageSize=200"
        )
        items = response.json().get("items", [])
        return {item.get("redirectUrl", ""): item.get(self.JAXRS_HOME_ORDER_FIELD, 0) for item in items}

    def expected_position_by_home_display_order(self, own_redirect_url: str, own_home_display_order: int) -> int:
        """1-indexed rank `own_redirect_url` SHOULD occupy on the Home page
        right now, given `own_home_display_order` and every OTHER currently
        active+shown entry's own real, live Home Display Order value —
        i.e. "how many entries currently rank ahead of this Home Display
        Order value, plus one". Ties broken by redirect URL string order
        (arbitrary but deterministic) since the real UI's own tie-break was
        never confirmed live and is not this method's concern — callers
        should avoid asserting against a value known to tie with another
        live entry's Home Display Order.

        This is ground truth computed from the SAME data source (confirmed
        live) the Home section itself renders from — not a hardcoded
        absolute index assumed from the ADO case's own wording, and keyed
        on the field CONFIRMED LIVE (module docstring's Round 2) to
        actually drive this section's order — "Home Display Order", not
        "Display Order" (the Footer's own field, and this session's own
        Round 1 mistake)."""
        orders = self._live_home_display_orders_by_redirect_url()
        orders[own_redirect_url] = own_home_display_order
        ranked = sorted(orders.items(), key=lambda kv: (kv[1], kv[0]))
        hrefs_in_order = [href for href, _ in ranked]
        return hrefs_in_order.index(own_redirect_url) + 1

    def reload_until(self, predicate, timeout_ms: int | None = None, interval_ms: int | None = None) -> bool:
        """Poll `open_home()` + `predicate(self)` until True or the
        timeout elapses — the propagation-check shape mandated by
        cms-profile.md (poll, never a bare `sleep()`). See module
        docstring's budget note."""
        import time

        timeout_ms = timeout_ms if timeout_ms is not None else self.RELOAD_POLL_TIMEOUT_MS
        interval_ms = interval_ms if interval_ms is not None else self.RELOAD_POLL_INTERVAL_MS
        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_home()
            if predicate(self):
                return True
            if time.monotonic() >= deadline:
                return False
            self.page.wait_for_timeout(interval_ms)
