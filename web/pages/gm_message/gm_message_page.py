"""
web/pages/gm_message/gm_message_page.py — GmMessagePage.

Public-frontend Page Object for PBI 129397 (QC-ABOUT-005 — General
Manager's Message), `/web/qatar-chamber/about-us/general-managers-message`.

The real URL is NOT the naively-guessed slug — it was resolved from the live
homepage's About Us submenu link (`a:has-text("General Manager's Message")`)
because the extractor's role-based nav discovery times out on this site's
hover-only submenu; the anchor exists in the DOM regardless (confirmed via
`page.eval_on_selector_all('a', ...)`), so its `href` was read directly
instead of guessing a slug.

Locators extracted CLI-first via `tools/extract_locators.py` for the
site-header/footer chrome (all uniq=1 role-based); the page's OWN structural
elements are not `<a>/<button>/<input>` so the CLI harvester (which only
walks interactive elements) returns nothing for them — mirroring
`org_structure_page.py`'s and `board_of_directors_page.py`'s precedent, a
DOM class probe (`page.eval_on_selector_all('[class]', ...)`) against the
live page confirmed the real, stable `qc-gm-*` custom classes below (no MCP
fallback was needed — the probe is a scripted Playwright call, still
CLI-first per the tooling-priority rule, just not through the extractor
script itself, exactly as org_structure_page.py's DOM-probe precedent):

    .qc-gm-hero > .qc-gm-hero-media[role=img][aria-label=...]   (background-image hero, alt via aria-label)
                > .qc-gm-hero-overlay
                > .qc-gm-hero-inner > h1.qc-gm-hero-title
                                     > nav.qc-gm-breadcrumb[aria-label="Breadcrumb"]
                                         a.qc-gm-crumb.qc-gm-crumb-home (svg.qc-gm-crumb-home-icon + span)
                                         svg.qc-gm-crumb-sep (mirrored via CSS transform:scaleX(-1) in RTL)
                                         span.qc-gm-crumb.qc-gm-crumb-current
    .qc-gm-content > .qc-gm-grid (CSS grid, 424px/696px columns; mirrors
        automatically under dir=rtl — same DOM order, no reordering needed)
        .qc-gm-card
            .qc-gm-portrait-wrap > .qc-gm-portrait-deco (maroon offset rect)
                                  > img.qc-gm-portrait-img (alt = "<name>, <designation>")
            .qc-gm-namecard > p.qc-gm-name, p.qc-gm-designation
        .qc-gm-message
            p.qc-gm-salutation
            div.qc-gm-body (rich-text container — plain <p> paragraphs on
                the currently-published EN/AR content; no heading/list/link
                markup is present in the live content as of this session)
            div.qc-gm-signature
                span.qc-gm-sig-avatar > span.qc-gm-sig-icon > svg (default
                    placeholder icon — no custom avatar image uploaded)
                div.qc-gm-sig-text > p.qc-gm-sig-regards, p.qc-gm-sig-name,
                    p.qc-gm-sig-desig

Confirmed live values (EN): name "Mr. Ali Saeed Busherbak Al Mansoori",
designation "Acting General Manager". AR mirrors dir=rtl automatically via
CSS grid + a `transform: scaleX(-1)` on the breadcrumb separator SVG — the
DOM order of the breadcrumb/grid children does NOT change between EN/AR.
"""

from config.settings import web_url
from core.web.base_page import BasePage

GM_MESSAGE_PATH = "/web/qatar-chamber/about-us/general-managers-message"


class GmMessagePage(BasePage):
    # ---- Hero -------------------------------------------------------------
    HERO_MEDIA = ".qc-gm-hero-media"
    HERO_TITLE = ".qc-gm-hero-title"

    # ---- Breadcrumb ---------------------------------------------------------
    BREADCRUMB_NAV = 'nav.qc-gm-breadcrumb[aria-label="Breadcrumb"]'
    BREADCRUMB_HOME_LINK = ".qc-gm-crumb-home"
    BREADCRUMB_CURRENT = ".qc-gm-crumb-current"
    BREADCRUMB_SEP = ".qc-gm-crumb-sep"

    # ---- Two-column layout --------------------------------------------------
    GRID = ".qc-gm-grid"
    CARD = ".qc-gm-card"
    PORTRAIT_WRAP = ".qc-gm-portrait-wrap"
    PORTRAIT_DECO = ".qc-gm-portrait-deco"
    PORTRAIT_IMG = ".qc-gm-portrait-img"
    NAME_CARD = ".qc-gm-namecard"
    PORTRAIT_NAME = ".qc-gm-name"
    PORTRAIT_DESIGNATION = ".qc-gm-designation"
    MESSAGE_COL = ".qc-gm-message"

    # ---- Message body -------------------------------------------------------
    SALUTATION = ".qc-gm-salutation"
    BODY = ".qc-gm-body"

    # ---- Signature block ------------------------------------------------------
    SIGNATURE = ".qc-gm-signature"
    SIG_AVATAR = ".qc-gm-sig-avatar"
    SIG_AVATAR_ICON = ".qc-gm-sig-icon"
    SIG_REGARDS = ".qc-gm-sig-regards"
    SIG_NAME = ".qc-gm-sig-name"
    SIG_DESIGNATION = ".qc-gm-sig-desig"

    # ---- Navigation -----------------------------------------------------
    def open_gm_message(self, locale: str = "en", cache_bust: bool = False) -> "GmMessagePage":
        """`cache_bust=True` appends a unique `?cb=<ns>` query so a cached
        copy older than a just-published change cannot be served."""
        url = web_url(GM_MESSAGE_PATH, locale=locale)
        if cache_bust:
            import time

            url += f"?cb={time.time_ns()}"
        self.open(url)
        return self

    def open_broken_url(self) -> "GmMessagePage":
        """Deliberately-invalid path under the same section, for the
        standard-error-page cases (135455/136387) — mirrors
        org_structure_page.py's open_broken_url precedent (the environment
        has no toggle to make the real page's content unavailable)."""
        self.open(web_url(GM_MESSAGE_PATH + "-unavailable-content-check"))
        return self

    # ---- Hero / title / breadcrumb queries -------------------------------
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO_MEDIA)

    def hero_alt_text(self) -> str:
        return self.page.locator(self.HERO_MEDIA).first.get_attribute("aria-label") or ""

    def is_title_visible(self) -> bool:
        return self.is_visible(self.HERO_TITLE)

    def title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.BREADCRUMB_NAV)

    def breadcrumb_home_text(self) -> str:
        return self.text(self.BREADCRUMB_HOME_LINK)

    def breadcrumb_current_text(self) -> str:
        return self.text(self.BREADCRUMB_CURRENT)

    def click_breadcrumb_home(self) -> None:
        self.click(self.BREADCRUMB_HOME_LINK)
        # Mirrors BoardOfDirectorsPage.click_breadcrumb_home's pattern
        # (board_of_directors_page.py ~113-121): the bare self.click() with
        # no post-click wait was a race condition — the caller's own
        # assertions could run against the pre-navigation URL/DOM. The
        # confirmed live href is "/web/qatar-chamber" (DOM probe,
        # 2026-08-25).
        try:
            self.page.wait_for_url(lambda url: "general-managers-message" not in url, timeout=15000)
        except Exception:
            pass  # surfaced by the caller's own URL assertion, not swallowed
        self.page.wait_for_load_state("domcontentloaded")

    def breadcrumb_sep_transform(self) -> str:
        return self.page.locator(self.BREADCRUMB_SEP).first.evaluate(
            "el => getComputedStyle(el).transform"
        )

    # ---- Two-column layout queries ----------------------------------------
    def grid_template_columns(self) -> str:
        return self.page.locator(self.GRID).first.evaluate(
            "el => getComputedStyle(el).gridTemplateColumns"
        )

    def grid_child_classes(self) -> list:
        return self.page.locator(self.GRID).first.evaluate(
            "el => [...el.children].map(c => c.className)"
        )

    def is_portrait_card_visible(self) -> bool:
        return self.is_visible(self.CARD)

    def is_message_column_visible(self) -> bool:
        return self.is_visible(self.MESSAGE_COL)

    def portrait_alt_text(self) -> str:
        return self.page.locator(self.PORTRAIT_IMG).first.get_attribute("alt") or ""

    def portrait_name_text(self) -> str:
        return self.text(self.PORTRAIT_NAME)

    def portrait_designation_text(self) -> str:
        return self.text(self.PORTRAIT_DESIGNATION)

    # ---- Salutation / body ------------------------------------------------
    def salutation_text(self) -> str:
        return self.text(self.SALUTATION)

    def body_text(self) -> str:
        return self.text(self.BODY)

    def body_html(self) -> str:
        return self.page.locator(self.BODY).first.inner_html()

    # ---- Signature block queries --------------------------------------------
    def is_signature_visible(self) -> bool:
        return self.is_visible(self.SIGNATURE)

    def signature_regards_text(self) -> str:
        return self.text(self.SIG_REGARDS)

    def signature_name_text(self) -> str:
        return self.text(self.SIG_NAME)

    def signature_designation_text(self) -> str:
        return self.text(self.SIG_DESIGNATION)

    def is_signature_avatar_visible(self) -> bool:
        return self.is_visible(self.SIG_AVATAR)

    def signature_avatar_has_default_icon(self) -> bool:
        """True when the signature avatar shows the built-in placeholder
        icon rather than a custom uploaded image — the live content has
        never had a custom avatar uploaded, so this is always the state
        observed for case 136364."""
        return self.page.locator(self.SIG_AVATAR).locator("img").count() == 0 and (
            self.page.locator(self.SIG_AVATAR).locator(self.SIG_AVATAR_ICON).count() > 0
        )

    # ---- Generic Figma-token probe (mirrors org_structure_page.py) --------
    def node_computed_style(self, locator: str, props: list) -> dict:
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

    def bounding_box(self, locator: str) -> dict:
        return self.page.locator(locator).first.bounding_box()

    # ---- Added 2026-10-12 (PBI 129397 CMS-to-public checks) ---------------
    def document_direction(self) -> str:
        return (self.page.locator("html").get_attribute("dir") or "").lower()

    def page_text(self) -> str:
        return self.page.locator("body").inner_text()

    def hero_image_src(self) -> str:
        """`src` of the hero <img>, or the hero's CSS background-image."""
        img = self.page.locator(f"{self.HERO_MEDIA} img").first
        if img.count():
            return img.get_attribute("src") or ""
        return self.page.locator(self.HERO_MEDIA).first.evaluate(
            "el => getComputedStyle(el).backgroundImage || ''"
        )

    def portrait_image_src(self) -> str:
        return self.page.locator(self.PORTRAIT_IMG).first.get_attribute("src") or ""

    # ---- Added 2026-10-13 (PBI 129397 P3/P4 batch, OFFLINE) ---------------
    # Text nodes a CMS field renders into, by field. VERIFY-LIVE: the
    # signature regards node carries Signature Closing Text.
    FIELD_NODES = {
        "salutation": SALUTATION,
        "name": f"{PORTRAIT_NAME}, {SIG_NAME}",
        "designation": f"{PORTRAIT_DESIGNATION}, {SIG_DESIGNATION}",
        "closing": SIG_REGARDS,
    }

    def field_nodes_html(self, key: str) -> list:
        """innerHTML of every node field `key` renders into (both places
        for the name / designation)."""
        return self.page.locator(self.FIELD_NODES[key]).evaluate_all("els => els.map(e => e.innerHTML)")

    def field_nodes_text(self, key: str) -> list:
        return [t.strip() for t in self.page.locator(self.FIELD_NODES[key]).all_inner_texts()]

    def field_nodes_have_markup(self, key: str, tags=("b", "strong", "img", "script")) -> bool:
        """True when a real element (`<b>`, `<img>`, ...) was rendered INSIDE
        the field's nodes -- i.e. the markup was interpreted, not escaped."""
        selector = ", ".join(f"{node} {tag}" for node in self.FIELD_NODES[key].split(", ") for tag in tags)
        return self.page.locator(selector).count() > 0

    def onerror_node_count(self) -> int:
        """Elements anywhere in the document carrying an `onerror` handler
        attribute -- an injected `<img onerror>` that was rendered as markup."""
        return self.page.evaluate("() => document.querySelectorAll('[onerror]').length")

    def signature_avatar_src(self) -> str:
        """`src` of an uploaded signature avatar <img>, else the avatar's CSS
        background-image, else "" (the default placeholder icon)."""
        img = self.page.locator(f"{self.SIG_AVATAR} img").first
        if img.count():
            return img.get_attribute("src") or ""
        avatar = self.page.locator(self.SIG_AVATAR).first
        if not avatar.count():
            return ""
        bg = avatar.evaluate("el => getComputedStyle(el).backgroundImage || ''")
        return "" if bg in ("", "none") else bg

    def signature_avatar_image(self, timeout: int = 15000) -> dict:
        """The uploaded signature avatar as the visitor's browser loaded it:
        {"present", "src" (absolute), "complete", "natural_width",
        "natural_height"}. Added 2026-10-14 (fix pass 7): the avatar is served
        by a FIELD-keyed endpoint (`/o/qc-newsletter/gm-asset?field=
        signatureAvatar`, read live 2026-10-13), so the file name never
        appears in `src`; whether the image actually decoded is the evidence.
        Waits (bounded) for the <img> to finish loading."""
        img = self.page.locator(f"{self.SIG_AVATAR} img").first
        if not img.count():
            return {"present": False, "src": "", "complete": False, "natural_width": 0, "natural_height": 0}
        try:
            img.evaluate(
                "(el, ms) => el.complete ? true : new Promise(r => { el.addEventListener('load', () => r(true));"
                " el.addEventListener('error', () => r(false)); setTimeout(() => r(false), ms); })",
                timeout,
            )
        except Exception:  # noqa: BLE001 -- reported through `complete` below
            pass
        return img.evaluate(
            "el => ({present: true, src: el.currentSrc || el.src, complete: el.complete,"
            " natural_width: el.naturalWidth, natural_height: el.naturalHeight})"
        )

    def body_link(self, href_prefix: str) -> dict:
        """{href, target, text, count} of the message-body anchors whose href
        starts with `href_prefix` (first match). count == 0 when absent."""
        links = self.page.locator(f'{self.BODY} a[href^="{href_prefix}"]')
        n = links.count()
        if not n:
            return {"href": "", "target": "", "text": "", "count": 0}
        first = links.first
        return {
            "href": first.get_attribute("href") or "",
            "target": first.get_attribute("target") or "",
            "text": first.inner_text().strip(),
            "count": n,
        }

    def follow_body_link(self, href_prefix: str, timeout: int = 15000) -> dict:
        """Clicks the first body anchor whose href starts with `href_prefix`
        and reports where it went: {"url": <first navigated URL>,
        "new_tab": bool}. Only the navigation REQUEST is waited for (an
        external site's full load is not this site's behaviour)."""
        link = self.page.locator(f'{self.BODY} a[href^="{href_prefix}"]').first
        try:
            with self.page.context.expect_page(timeout=4000) as popup_info:
                link.click()
            popup = popup_info.value
            try:
                popup.wait_for_load_state("commit", timeout=timeout)
            except Exception:  # noqa: BLE001 -- the URL is still known
                pass
            url = popup.url
            popup.close()
            return {"url": url, "new_tab": True}
        except Exception:  # noqa: BLE001 -- no new tab: same-tab navigation
            try:
                self.page.wait_for_url(f"{href_prefix}**", timeout=timeout, wait_until="commit")
            except Exception:  # noqa: BLE001 -- reported through the URL
                pass
            return {"url": self.page.url, "new_tab": False}

    def watch_dialogs(self) -> list:
        """Starts recording every native dialog (e.g. an injected alert())."""
        seen: list = []

        def _on(dialog):
            seen.append(dialog.message)
            try:
                dialog.dismiss()
            except Exception:  # noqa: BLE001
                pass

        self.page.on("dialog", _on)
        return seen
