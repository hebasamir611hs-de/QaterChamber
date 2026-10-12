"""
web/pages/business_opportunities/detail_page.py — BusinessOpportunityDetailPage.

Public-frontend Page Object for PBI 130697 (INVEST — Business Opportunities):
the Opportunity Detail page (header, sticky section index, 01 Overview,
02 Investment Details, 03 Gallery & Supporting Documents) plus the
"Express Your Interest" inquiry modal that opens from its "Submit Inquiry" CTA.

Ownership: W4 owns the core (header / index / sections / CTA state). The
inquiry-modal locators and methods live in the `# --- W2 ---` sections and
belong to W2.

LOCATORS — verified LIVE on qcdev 2026-10-12 (unauthenticated context) against
real Published records QC-BIZOPP-130697-01..04 (Active) and -05 (Archived):
  route        /web/qatar-chamber/business-opportunity?opportunity=<ERC>
               (AR: /ar/web/...); the ERC (e.g. QC-BIZOPP-130697-01) is the key.
  widget root  div.qc-bod ; hero section.qc-bod-hero ; body div.qc-bod-body
  breadcrumb   nav.qc-bod-crumbs > a.qc-bod-crumb (current: .is-current,
               aria-current=page) — "Home › Business Gateway" (PBI + Figma).
  index        aside.qc-bod-index (position: sticky; top: 96px) >
               nav.qc-bod-index-card > a.qc-bod-index-row
               (.qc-bod-index-num / .qc-bod-index-label), hrefs
               #qc-bod-overview | #qc-bod-investment | #qc-bod-gallery.
               Hidden (display:none) below the desktop breakpoint — matches the
               Figma mobile frame 4964:223038, which has no index at all.
               No active-row state exists in the DOM (no class/aria change on
               scroll or click) — see the 143254 test.
  sections     section.qc-bod-sec#qc-bod-overview / #qc-bod-investment /
               #qc-bod-gallery / #qc-bod-docs (docs is a 4th section that the
               index's 03 entry does not link to separately).
  CTA          button.qc-bod-cta ("Submit Inquiry"); on an Archived record it is
               [hidden] (display:none) and p.qc-bod-archived shows instead.
  files        div.qc-bod-file (.qc-bod-file-badge, .qc-bod-file-title,
               .qc-bod-file-meta span x2 = type / size, a.qc-bod-file-btn[download]
               -> /o/qc-business-opportunities-api/attachment?id=<n>).
"""

import re

from config.settings import web_url
from core.web.base_page import BasePage

PATH_TEMPLATE = "/web/qatar-chamber/business-opportunity?opportunity={slug}"

INQUIRY_FIELD_KEYS = ("your_name", "email", "mobile", "company", "inquiry_type", "message")

# Real Published qcdev records used read-only by the web tests.
ACTIVE_ERC = "QC-BIZOPP-130697-01"          # "Qatar Smart City Infrastructure Fund"
ACTIVE_TITLE = "Qatar Smart City Infrastructure Fund"
ARCHIVED_ERC = "QC-BIZOPP-130697-05"        # "Agricultural Technology Hub"


class BusinessOpportunityDetailPage(BasePage):
    # ---- Header / breadcrumb ------------------------------------------------
    ROOT = "div.qc-bod"
    HERO = "section.qc-bod-hero"
    BREADCRUMB = "nav.qc-bod-crumbs"
    BREADCRUMB_LINK = "a.qc-bod-crumb"
    BREADCRUMB_CURRENT = "a.qc-bod-crumb.is-current"
    CHIP = ".qc-bod-chip"
    HEADER_TITLE = "h1.qc-bod-title"
    HEADER_SUMMARY = ".qc-bod-hero-desc"
    HERO_IMAGE = "img.qc-bod-hero-img"
    MISSING_STATE = ".qc-bod-missing"

    # ---- Sticky section index ------------------------------------------------
    SECTION_INDEX = "aside.qc-bod-index"
    SECTION_INDEX_CARD = "nav.qc-bod-index-card"
    SECTION_INDEX_ITEM = "a.qc-bod-index-row"
    SECTION_INDEX_NUM = ".qc-bod-index-num"
    SECTION_INDEX_LABEL = ".qc-bod-index-label"

    SECTION = "section.qc-bod-sec"
    SECTION_OVERVIEW = "#qc-bod-overview"
    SECTION_INVESTMENT_DETAILS = "#qc-bod-investment"
    SECTION_GALLERY = "#qc-bod-gallery"
    SECTION_DOCS = "#qc-bod-docs"
    SECTION_EYEBROW = ".qc-bod-eyebrow"
    SECTION_TITLE = "h2.qc-bod-sectitle"
    SECTION_ICON_TILE = ".qc-bod-sectile"
    DIVIDER = "hr.qc-bod-divider"

    # ---- 01 Overview ----------------------------------------------------------
    OVERVIEW_PROSE = "#qc-bod-overview > .qc-bod-prose"
    STAT = ".qc-bod-stat"
    STAT_LABEL = ".qc-bod-stat-label"
    STAT_VALUE = ".qc-bod-stat-value"
    SUBHEAD = "h3.qc-bod-subhead"
    KEY_HIGHLIGHTS = ".qc-bod-highlights"
    KEY_HIGHLIGHT_ITEM = "li.qc-bod-highlight"
    SUBMITTER = ".qc-bod-submitter"
    SUBMITTED_BY_NAME = ".qc-bod-submitter-name"
    SUBMITTED_BY_META_ITEM = ".qc-bod-submitter-meta > span:not(.qc-bod-submitter-sep)"
    SUBMITTED_BY_LOGO = ".qc-bod-submitter-logo img"

    # ---- 02 Investment Details ------------------------------------------------
    DEFS = "dl.qc-bod-defs"
    DEF = ".qc-bod-def"
    DEF_TERM = "dt.qc-bod-def-term"
    DEF_VALUE = "dd.qc-bod-def-value"

    # ---- 03 Gallery & Supporting Documents -------------------------------
    GALLERY_IMAGE = "#qc-bod-gallery .qc-bod-shot img"
    RESOURCE_ROW = ".qc-bod-file"
    RESOURCE_BADGE = ".qc-bod-file-badge"
    RESOURCE_TITLE = ".qc-bod-file-title"
    RESOURCE_META_ITEM = ".qc-bod-file-meta > span:not(.qc-bod-file-dot)"
    RESOURCE_DOWNLOAD_BUTTON = "a.qc-bod-file-btn"

    # ---- Submit Inquiry CTA -------------------------------------------------
    SUBMIT_INQUIRY_CTA = "button.qc-bod-cta"
    ARCHIVED_NOTE = "p.qc-bod-archived"
    MODAL_PANEL = ".qc-bod-modal-panel"

    # --- W2 --- (inquiry modal locators; owned by W2)
    # ---- Express Your Interest modal ----------------------------------------
    # Verified LIVE on qcdev 2026-10-12 (unauthenticated, EN + AR, 1920/1440/390,
    # light + dark) on QC-BIZOPP-130697-04. The modal markup is server-rendered
    # inside the detail fragment; main.js builds the six fields. reCAPTCHA is
    # switched off on qcdev, so [data-qc-recaptcha] stays [hidden] and empty.
    INQUIRY_DIALOG = "[data-qc-bod-modal-panel]"          # div.qc-bod-modal-panel[role=dialog][aria-modal=true]
    INQUIRY_MODAL = INQUIRY_DIALOG
    INQUIRY_EYEBROW = "[data-qc-bod-modal-panel] .qc-bod-modal-eyebrow"
    INQUIRY_TITLE = "[data-qc-bod-modal-panel] h2.qc-bod-modal-title"
    INQUIRY_LEAD = "[data-qc-bod-modal-panel] p.qc-bod-modal-lead"
    INQUIRY_HEAD = "[data-qc-bod-modal-panel] .qc-bod-modal-head"
    INQUIRY_CLOSE_BUTTON = "[data-qc-bod-modal-panel] button.qc-bod-modal-close"
    INQUIRY_CANCEL_BUTTON = "[data-qc-bod-modal-panel] button.qc-bod-form-cancel"
    INQUIRY_SUBMIT_BUTTON = "[data-qc-bod-modal-panel] button.qc-bod-form-submit"
    INQUIRY_FORM = "[data-qc-bod-modal-panel] form.qc-bod-form"
    INQUIRY_FIELD_WRAP = "[data-qc-bod-modal-panel] .qc-bod-fld"
    INQUIRY_FIELD_LABEL = ".qc-bod-fld-label > span:first-child"
    INQUIRY_REQUIRED_MARK = "[data-qc-bod-modal-panel] .qc-bod-req"
    INQUIRY_OPTIONAL_MARK = "[data-qc-bod-modal-panel] .qc-bod-opt"
    INQUIRY_CAPTCHA_FIELD = "[data-qc-bod-modal-panel] [data-qc-bod-captcha-field]"
    INQUIRY_CAPTCHA_MOUNT = "[data-qc-bod-modal-panel] [data-qc-recaptcha]"
    INQUIRY_GENERIC_ERROR = "[data-qc-bod-modal-panel] [data-qc-bod-form-error]"
    INQUIRY_SUCCESS = "[data-qc-bod-modal-panel] [data-qc-bod-done]"
    INQUIRY_SUCCESS_MESSAGE = INQUIRY_SUCCESS
    INQUIRY_SUCCESS_TITLE = "[data-qc-bod-modal-panel] h3.qc-bod-done-title"
    INQUIRY_SUCCESS_BODY = "[data-qc-bod-modal-panel] p.qc-bod-done-body"
    INQUIRY_SUCCESS_REF = "[data-qc-bod-modal-panel] [data-qc-bod-done-ref]"
    INQUIRY_SUCCESS_CLOSE = "[data-qc-bod-modal-panel] button.qc-bod-done-close"
    INQUIRY_API_PATH = "/o/qc-business-opportunities-api/inquiries"

    INQUIRY_FIELD_NAMES = {
        "your_name": "yourName", "email": "emailAddress", "mobile": "mobileNumber",
        "company": "company", "inquiry_type": "inquiryType", "message": "message",
    }
    INQUIRY_FIELD_LOCATORS = {
        key: f"[data-qc-bod-modal-panel] [name='{name}']" for key, name in INQUIRY_FIELD_NAMES.items()
    }
    # The inline error is the .qc-bod-fld-error sibling inside the same .qc-bod-fld.
    INQUIRY_FIELD_ERROR_LOCATORS = {
        key: f"[data-qc-bod-modal-panel] .qc-bod-fld:has([name='{name}']) .qc-bod-fld-error"
        for key, name in INQUIRY_FIELD_NAMES.items()
    }

    # ---- Navigation -----------------------------------------------------------
    def open_detail(self, slug: str, locale: str = "en") -> "BusinessOpportunityDetailPage":
        """`slug` is the record's ERC (e.g. QC-BIZOPP-130697-01)."""
        self.open(web_url(PATH_TEMPLATE.format(slug=slug), locale=locale))
        self.wait_for(self.HEADER_TITLE, state="visible", timeout=60000)
        return self

    def wait_loaded(self, timeout: int = 60000) -> "BusinessOpportunityDetailPage":
        """For arrivals by click (View Details) rather than open_detail()."""
        self.page.wait_for_url("**/business-opportunity?opportunity=*", timeout=timeout)
        self.wait_for(self.HEADER_TITLE, state="visible", timeout=timeout)
        return self

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def has_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
        )

    def overflowing_elements(self) -> list:
        """Class names of `.qc-bod` descendants poking out of the viewport."""
        return self.page.evaluate(
            "() => [...document.querySelectorAll('.qc-bod *')].filter(e => { const r = e.getBoundingClientRect();"
            " return r.width > 0 && (r.right > window.innerWidth + 1 || r.left < -1); })"
            ".map(e => e.className.toString()).slice(0, 10)"
        )

    def box(self, locator: str, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).bounding_box()

    def style(self, locator: str, *props: str, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).evaluate(
            "(el, props) => { const s = getComputedStyle(el); const o = {}; props.forEach(p => o[p] = s[p]); return o; }",
            list(props),
        )

    # ---- Header / breadcrumb ------------------------------------------------
    def title_text(self) -> str:
        return self.text(self.HEADER_TITLE).strip()

    def summary_text(self) -> str:
        return self.text(self.HEADER_SUMMARY).strip()

    def chip_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.CHIP).all_inner_texts()]

    def breadcrumb_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.BREADCRUMB_LINK).all_inner_texts()]

    def breadcrumb_hrefs(self) -> list:
        return [a.get_attribute("href") for a in self.page.locator(self.BREADCRUMB_LINK).all()]

    def click_breadcrumb(self, label: str) -> None:
        self.click(f"{self.BREADCRUMB_LINK}:has-text('{label}')")

    def is_hero_image_loaded(self) -> bool:
        return self.page.locator(self.HERO_IMAGE).evaluate("i => i.complete && i.naturalWidth > 0")

    # ---- Section index -----------------------------------------------------
    def is_section_index_visible(self) -> bool:
        return self.is_visible(self.SECTION_INDEX_CARD)

    def section_index_entries(self) -> list:
        """[(num, label, href), ...] in DOM order."""
        rows = self.page.locator(self.SECTION_INDEX_ITEM)
        return [
            (
                rows.nth(i).locator(self.SECTION_INDEX_NUM).inner_text().strip(),
                rows.nth(i).locator(self.SECTION_INDEX_LABEL).inner_text().strip(),
                rows.nth(i).get_attribute("href"),
            )
            for i in range(rows.count())
        ]

    def section_index_labels(self) -> list:
        return [label for _, label, _ in self.section_index_entries()]

    def click_section_index_item(self, label: str) -> None:
        self.click(f"{self.SECTION_INDEX_ITEM}:has({self.SECTION_INDEX_LABEL}:text-is('{label}'))")
        self.page.wait_for_timeout(1200)  # let any smooth scroll settle before measuring

    def active_section_index_label(self):
        """Label of the row the page marks as current, or None when no row is
        marked. A row counts as marked when it carries an active/current class
        or aria-current, or when its background+label colour differs from
        every other row. Live 2026-10-12: always None (no row state change on
        scroll or click)."""
        # Neutral pointer/focus first, so hover or focus styling is not read as "active".
        self.page.mouse.move(1900, 5)
        self.page.evaluate("() => document.activeElement && document.activeElement.blur()")
        self.page.wait_for_timeout(300)
        return self.page.evaluate(
            """() => { const rows = [...document.querySelectorAll('a.qc-bod-index-row')];
                 const sig = rows.map(r => getComputedStyle(r).backgroundColor + '|' +
                     getComputedStyle(r.querySelector('.qc-bod-index-label')).color + '|' +
                     getComputedStyle(r.querySelector('.qc-bod-index-num')).backgroundColor);
                 const marked = rows.filter((r, i) => /(^|\\s)(is-active|active|is-current|current)(\\s|$)/.test(r.className)
                     || r.getAttribute('aria-current')
                     || (rows.length > 2 && sig.filter(s => s === sig[i]).length === 1));
                 return marked.length === 1 ? marked[0].querySelector('.qc-bod-index-label').innerText.trim() : null; }"""
        )

    def section_index_viewport_top(self) -> float:
        return self.page.locator(self.SECTION_INDEX_CARD).evaluate("e => e.getBoundingClientRect().top")

    def section_viewport_top(self, section_locator: str) -> float:
        return self.page.locator(section_locator).evaluate("e => e.getBoundingClientRect().top")

    def section_ids(self) -> list:
        return self.page.evaluate("() => [...document.querySelectorAll('section.qc-bod-sec')].map(s => s.id)")

    def scroll_to_y(self, y: int) -> None:
        self.page.evaluate(f"window.scrollTo(0, {int(y)})")
        self.page.wait_for_timeout(800)

    # ---- 01 Overview ----------------------------------------------------------
    def section_title_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.SECTION_TITLE).all_inner_texts()]

    def overview_prose_texts(self) -> list:
        """The Overview's rich-text blocks in order: [overview body, investment brief]."""
        return [t.strip() for t in self.page.locator(self.OVERVIEW_PROSE).all_inner_texts()]

    def overview_body_text(self) -> str:
        texts = self.overview_prose_texts()
        return texts[0] if texts else ""

    def investment_brief_text(self) -> str:
        texts = self.overview_prose_texts()
        return texts[1] if len(texts) > 1 else ""

    def stats(self) -> dict:
        stats = self.page.locator(self.STAT)
        return {
            stats.nth(i).locator(self.STAT_LABEL).inner_text().strip():
                stats.nth(i).locator(self.STAT_VALUE).inner_text().strip()
            for i in range(stats.count())
        }

    def subhead_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.SUBHEAD).all_inner_texts()]

    def key_highlight_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.KEY_HIGHLIGHT_ITEM).all_inner_texts()]

    def submitted_by(self) -> dict:
        meta = [t.strip() for t in self.page.locator(self.SUBMITTED_BY_META_ITEM).all_inner_texts()]
        logo = self.page.locator(self.SUBMITTED_BY_LOGO)
        return {
            "name": self.text(self.SUBMITTED_BY_NAME).strip(),
            "entity_type": meta[0] if meta else "",
            "location": meta[1] if len(meta) > 1 else "",
            "logo_loaded": logo.count() > 0 and logo.first.evaluate("i => i.complete && i.naturalWidth > 0"),
        }

    # ---- 02 Investment Details ------------------------------------------------
    def investment_structure(self) -> dict:
        defs = self.page.locator(self.DEF)
        return {
            defs.nth(i).locator(self.DEF_TERM).inner_text().strip():
                defs.nth(i).locator(self.DEF_VALUE).inner_text().strip()
            for i in range(defs.count())
        }

    # ---- 03 Gallery & Supporting Documents -------------------------------
    def gallery_image_count(self) -> int:
        return self.page.locator(self.GALLERY_IMAGE).count()

    def broken_gallery_images(self) -> list:
        self.page.locator(self.SECTION_GALLERY).scroll_into_view_if_needed()
        self.page.wait_for_timeout(1000)
        return self.page.locator(self.GALLERY_IMAGE).evaluate_all(
            "imgs => imgs.filter(i => !(i.complete && i.naturalWidth > 0)).map(i => i.src)"
        )

    def resources(self) -> list:
        rows = self.page.locator(self.RESOURCE_ROW)
        out = []
        for i in range(rows.count()):
            row = rows.nth(i)
            meta = [t.strip() for t in row.locator(self.RESOURCE_META_ITEM).all_inner_texts()]
            out.append({
                "badge": row.locator(self.RESOURCE_BADGE).inner_text().strip(),
                "title": row.locator(self.RESOURCE_TITLE).inner_text().strip(),
                "type": meta[0] if meta else "",
                "size": meta[1] if len(meta) > 1 else "",
                "button": row.locator(self.RESOURCE_DOWNLOAD_BUTTON).inner_text().strip(),
                "href": row.locator(self.RESOURCE_DOWNLOAD_BUTTON).get_attribute("href"),
            })
        return out

    def resource_title_text(self, index: int = 0) -> str:
        return self.page.locator(self.RESOURCE_TITLE).nth(index).inner_text().strip()

    def click_download_resource(self, index: int = 0):
        """Returns the Playwright Download for the file the click triggers."""
        with self.page.expect_download(timeout=30000) as download_info:
            self.page.locator(self.RESOURCE_DOWNLOAD_BUTTON).nth(index).click()
        return download_info.value

    def is_submit_inquiry_cta_keyboard_reachable(self, max_presses: int = 25) -> bool:
        return self.press_tab_until_focused(self.SUBMIT_INQUIRY_CTA, max_presses=max_presses)

    # ---- Submit Inquiry CTA -------------------------------------------------
    def is_submit_inquiry_cta_visible(self) -> bool:
        return self.is_visible(self.SUBMIT_INQUIRY_CTA)

    def is_submit_inquiry_cta_enabled(self) -> bool:
        cta = self.page.locator(self.SUBMIT_INQUIRY_CTA)
        return cta.count() > 0 and cta.first.is_visible() and cta.first.is_enabled()

    def archived_note_text(self) -> str:
        note = self.page.locator(self.ARCHIVED_NOTE)
        return note.inner_text().strip() if note.count() and note.first.is_visible() else ""

    def click_submit_inquiry(self) -> "BusinessOpportunityDetailPage":
        self.click(self.SUBMIT_INQUIRY_CTA)
        self.wait_for(self.MODAL_PANEL, state="visible", timeout=15000)
        return self

    def is_modal_panel_visible(self) -> bool:
        return self.is_visible(self.MODAL_PANEL)

    # --- W2 --- (inquiry modal methods; owned by W2)
    # ---- Express Your Interest modal ----------------------------------------
    def open_inquiry_modal(self) -> "BusinessOpportunityDetailPage":
        """Clicks the real CTA and waits until main.js has built the fields."""
        self.page.locator(self.SUBMIT_INQUIRY_CTA).first.click()
        self.page.locator(self.INQUIRY_FIELD_LOCATORS["your_name"]).wait_for(state="visible", timeout=30000)
        self.page.wait_for_function(
            "() => document.getAnimations().every((a) => a.playState !== 'running')", timeout=10000)
        return self

    def force_open_inquiry_modal_via_script(self) -> None:
        """Fires the (possibly [hidden]) CTA's click handler from script: the
        "any exposed client-side trigger" step of the archived-opportunity case."""
        self.page.evaluate("(sel) => { const b = document.querySelector(sel); if (b) b.click(); }",
                           self.SUBMIT_INQUIRY_CTA)
        self.page.wait_for_timeout(1000)

    def is_inquiry_modal_open(self) -> bool:
        return self.page.locator(self.INQUIRY_DIALOG).is_visible()

    def inquiry_dialog_attrs(self) -> dict:
        loc = self.page.locator(self.INQUIRY_DIALOG)
        return {"role": loc.get_attribute("role"), "aria_modal": loc.get_attribute("aria-modal")}

    def close_inquiry_modal(self) -> None:
        self.page.locator(self.INQUIRY_CLOSE_BUTTON).click()

    def inquiry_header_texts(self) -> dict:
        p = self.page
        return {"eyebrow": p.locator(self.INQUIRY_EYEBROW).inner_text().strip(),
                "eyebrow_source": p.locator(self.INQUIRY_EYEBROW).text_content().strip(),
                "title": p.locator(self.INQUIRY_TITLE).inner_text().strip(),
                "lead": p.locator(self.INQUIRY_LEAD).inner_text().strip()}

    def inquiry_field_labels(self) -> dict:
        """{field_key: label text}."""
        out = {}
        for key, name in self.INQUIRY_FIELD_NAMES.items():
            wrap = self.page.locator(f"{self.INQUIRY_FIELD_WRAP}:has([name='{name}'])")
            out[key] = wrap.locator(self.INQUIRY_FIELD_LABEL).inner_text().strip() if wrap.count() else None
        return out

    def visible_inquiry_field_keys(self) -> list:
        return [k for k in INQUIRY_FIELD_KEYS if self.page.locator(self.INQUIRY_FIELD_LOCATORS[k]).is_visible()]

    def inquiry_field_meta(self, field_key: str) -> dict:
        loc = self.page.locator(self.INQUIRY_FIELD_LOCATORS[field_key])
        return loc.evaluate("""(e) => ({tag: e.tagName.toLowerCase(), type: e.type, maxlength: e.maxLength,
            placeholder: e.placeholder || '', required: e.getAttribute('aria-required'),
            dir: getComputedStyle(e).direction, value: e.value,
            options: e.options ? [...e.options].map(o => [o.value, o.text.trim()]) : null})""")

    def inquiry_mobile_prefix(self) -> dict:
        """What the Mobile Number control shows besides the bare input (Figma:
        Qatar flag + '+974' country-code block inside the input)."""
        wrap = self.page.locator(f"{self.INQUIRY_FIELD_WRAP}:has([name='mobileNumber'])")
        return wrap.evaluate("""(w) => ({text: w.innerText.replace(/\\s+/g, ' ').trim(),
            graphics: w.querySelectorAll('img, svg').length, has974: /\\+974/.test(w.innerText),
            value: w.querySelector('input').value})""")

    def fill_inquiry_field(self, field_key: str, value: str) -> None:
        loc = self.page.locator(self.INQUIRY_FIELD_LOCATORS[field_key])
        if field_key == "inquiry_type":
            if value:
                loc.select_option(label=value)
            else:
                loc.select_option(value="")
        else:
            loc.fill(value)

    def type_inquiry_field(self, field_key: str, value: str) -> None:
        """Real key-by-key typing (honours maxlength like a visitor's keyboard)."""
        loc = self.page.locator(self.INQUIRY_FIELD_LOCATORS[field_key])
        loc.fill("")
        loc.press_sequentially(value, delay=0)

    def fill_inquiry_form(self, values: dict) -> "BusinessOpportunityDetailPage":
        for key, value in values.items():
            self.fill_inquiry_field(key, value)
        return self

    def inquiry_field_value(self, field_key: str) -> str:
        return self.page.locator(self.INQUIRY_FIELD_LOCATORS[field_key]).input_value()

    def selected_inquiry_type_label(self) -> str:
        return self.page.locator(self.INQUIRY_FIELD_LOCATORS["inquiry_type"]).evaluate(
            "(s) => s.options[s.selectedIndex].text.trim()")

    def inquiry_field_error_text(self, field_key: str) -> str:
        loc = self.page.locator(self.INQUIRY_FIELD_ERROR_LOCATORS[field_key])
        return loc.inner_text().strip() if loc.count() else ""

    def inquiry_field_errors(self) -> dict:
        return {k: self.inquiry_field_error_text(k) for k in INQUIRY_FIELD_KEYS}

    def is_inquiry_field_error_visible(self, field_key: str) -> bool:
        return bool(self.inquiry_field_error_text(field_key))

    def is_inquiry_field_invalid(self, field_key: str) -> bool:
        return self.page.locator(self.INQUIRY_FIELD_LOCATORS[field_key]).get_attribute("aria-invalid") == "true"

    def inquiry_captcha_state(self) -> dict:
        mount = self.page.locator(self.INQUIRY_CAPTCHA_MOUNT)
        present = mount.count() > 0
        return {"present": present, "visible": present and mount.first.is_visible(),
                "iframes": self.page.locator(f"{self.INQUIRY_CAPTCHA_MOUNT} iframe").count()}

    def is_inquiry_captcha_present(self) -> bool:
        return self.inquiry_captcha_state()["visible"]

    def click_submit_inquiry_button(self) -> None:
        self.page.locator(self.INQUIRY_SUBMIT_BUTTON).click()

    def submit_inquiry_and_capture(self, double_click: bool = False, hold_ms: int = 0) -> dict:
        """Clicks Submit once (or double-clicks it) and records every POST to the
        inquiry endpoint, the button state while the request is in flight, and
        the outcome. `hold_ms` holds the request in the browser (test side) so the
        in-flight button state can be read reliably before it is sent."""
        posts, during = [], {}

        def _route(route):
            posts.append(route.request.url)
            if hold_ms and not during:
                btn = self.page.locator(self.INQUIRY_SUBMIT_BUTTON)
                during.update({"disabled": btn.is_disabled(), "text": btn.inner_text().strip()})
            route.continue_()

        pattern = f"**{self.INQUIRY_API_PATH}*"
        self.page.route(pattern, _route)
        btn = self.page.locator(self.INQUIRY_SUBMIT_BUTTON)
        with self.page.expect_response(
            lambda r: self.INQUIRY_API_PATH in r.url and r.request.method == "POST", timeout=60000
        ) as info:
            if double_click:
                btn.dblclick()
            else:
                btn.click()
        response = info.value
        try:
            body = response.json()
        except Exception:  # noqa: BLE001 - the body is informational
            body = {}
        try:
            self.page.locator(f"{self.INQUIRY_SUCCESS}:visible, {self.INQUIRY_GENERIC_ERROR}:visible").first.wait_for(
                timeout=30000)
        except Exception:  # noqa: BLE001 - outcome read below
            pass
        self.page.wait_for_timeout(1500)  # a second (duplicate) POST would have fired by now
        self.page.unroute(pattern)
        return {"http": response.status, "body": body, "posts": len(posts), "during": during,
                "success": self.is_inquiry_success_visible(), "error": self.inquiry_generic_error_text()}

    def is_inquiry_submit_button_disabled(self) -> bool:
        return self.page.locator(self.INQUIRY_SUBMIT_BUTTON).is_disabled()

    def inquiry_success_texts(self) -> dict:
        p = self.page
        return {"title": p.locator(self.INQUIRY_SUCCESS_TITLE).inner_text().strip(),
                "body": p.locator(self.INQUIRY_SUCCESS_BODY).inner_text().strip(),
                "ref": p.locator(self.INQUIRY_SUCCESS_REF).inner_text().strip(),
                "all": re.sub(r"\s+", " ", p.locator(self.INQUIRY_SUCCESS).inner_text()).strip()}

    def inquiry_success_message_text(self) -> str:
        return self.inquiry_success_texts()["all"]

    def is_inquiry_success_visible(self) -> bool:
        return self.page.locator(self.INQUIRY_SUCCESS).is_visible()

    def inquiry_generic_error_text(self) -> str:
        loc = self.page.locator(self.INQUIRY_GENERIC_ERROR)
        return loc.inner_text().strip() if loc.count() and loc.is_visible() else ""

    def inquiry_layout(self) -> dict:
        """Computed styles and boxes of the modal parts, for the Figma comparison."""
        return self.page.evaluate("""() => {
          const P = document.querySelector('[data-qc-bod-modal-panel]');
          const m = (e) => { if (!e) return null; const s = getComputedStyle(e), r = e.getBoundingClientRect();
            return {ff: s.fontFamily.split(',')[0].replace(/["']/g, '').trim(), fs: s.fontSize, fw: s.fontWeight,
              lh: s.lineHeight, color: s.color, bg: s.backgroundColor, radius: s.borderTopLeftRadius,
              padding: s.padding, transform: s.textTransform, shadow: s.boxShadow, align: s.textAlign,
              dir: s.direction, x: r.x, y: r.y, w: r.width, h: r.height}; };
          const q = (s) => P.querySelector(s);
          const inputs = {}; P.querySelectorAll('.qc-bod-input').forEach(i => { inputs[i.name] = m(i); });
          return {panel: m(P), eyebrow: m(q('.qc-bod-modal-eyebrow')), title: m(q('.qc-bod-modal-title')),
            lead: m(q('.qc-bod-modal-lead')), close: m(q('.qc-bod-modal-close')),
            label: m(q('.qc-bod-fld-label > span')), req: m(q('.qc-bod-req')), inputs,
            cancel: m(q('.qc-bod-form-cancel')), submit: m(q('.qc-bod-form-submit')),
            submit_icon: !!q('.qc-bod-form-submit svg'), head_icons: P.querySelectorAll('.qc-bod-modal-head svg').length,
            viewport: [innerWidth, innerHeight], theme: document.documentElement.getAttribute('data-theme')};
        }""")

    def inquiry_panel_screenshot(self, path: str) -> str:
        self.page.locator(self.INQUIRY_DIALOG).screenshot(path=path)
        return path
