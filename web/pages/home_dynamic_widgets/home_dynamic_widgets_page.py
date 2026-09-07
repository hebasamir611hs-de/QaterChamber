"""
web/pages/home_dynamic_widgets/home_dynamic_widgets_page.py —
HomeDynamicWidgetsPage.

Public-frontend Page Object for PBI 129384 (Home Page "Dynamic Widgets" —
Marhaba Guide / B2B Platform / Weather). See
home_dynamic_widgets_admin_page.py for the authoring-surface counterpart
and the full live-exploration docstring this Page Object's locators are
drawn from.

REAL, LIVE-VERIFIED FACTS (this session, 2026-08-31, against qcdev
`/en/home`):

  - The whole feature renders inside `section.qc-home-dynamic-widgets` >
    `.qc-dw-inner` > `.qc-dw-row[data-qc-dw-row]`.
  - Each "content" widget (Marhaba/B2B) renders as an `<a class="qc-dw-card"
    href="<redirect url>" target="_blank" rel="noopener noreferrer">`
    (confirmed live: `target="_blank"` was present on both currently-Active,
    Open-in-New-Tab-enabled rows this session — this attribute is the
    delivery-surface signal for the admin "Open in New Tab" toggle) wrapping
    a single `img.qc-dw-card-img` whose `src` embeds the record's own
    `objectEntryExternalReferenceCode` query param — confirmed live, e.g.
    `...objectEntryExternalReferenceCode=QCDEMO-129384-b2b-verified` — this
    is the SAME identifying ERC seen in the admin edit-form URL, so a test
    can use it to confirm "this specific admin record propagated to
    delivery" without depending on card ORDER or exact filename text.
  - Cards render in DOM order matching the object entries' Display Order
    (both rows had orders 100/200 this session; the 100-order "directory"
    card rendered first, the 200-order "b2b-verified" card second) —
    consistent with the case text's expectation that Display Order controls
    card position.
  - The Weather widget is a SEPARATE mount point,
    `.qc-dw-weather[data-qc-weather-widget][data-qc-weather-init="1"]`,
    inside the SAME `.qc-dw-row` as the content cards — confirmed live via
    an inline HTML comment on the rendered page: "Weather widget (PBI
    129384 / T45): the maroon Doha weather card is rendered by the
    qc-weather-widget Client Extension ... calls the Weather API for Doha,
    and shows the bilingual 'Weather data unavailable.' fallback on
    failure." Its title renders as `.qc-dw-weather .the-subtitle` with text
    exactly "Weather" (a trailing decorative icon span is a sibling, not
    part of the text). Live city text was "Doha" — case says assert
    presence/position only, not live weather VALUES (correct per the case's
    own instruction: those are non-deterministic).
  - No live "before Active/Display-Order write" or "after write" comparison
    was performed this session (see the admin Page Object's own
    SAVE_COMMIT_GRACE_MS disclosure — no live Save was exercised to avoid
    mutating the shared qcdev rows before a restore path existed). The
    locators above are read-only-confirmed against the CURRENT baseline
    state only.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeDynamicWidgetsPage(BasePage):
    WIDGETS_SECTION = "section.qc-home-dynamic-widgets"
    WIDGETS_ROW = f"{WIDGETS_SECTION} [data-qc-dw-row]"
    CARD = f"{WIDGETS_SECTION} .qc-dw-card"
    CARD_IMG = ".qc-dw-card-img"

    WEATHER_WIDGET = f"{WIDGETS_SECTION} .qc-dw-weather[data-qc-weather-widget]"
    WEATHER_TITLE = f"{WEATHER_WIDGET} .the-subtitle"

    def open_home(self, locale: str = "en") -> "HomeDynamicWidgetsPage":
        self.open(web_url("/home", locale=locale))
        return self

    # ---- Content widgets (Marhaba / B2B) -----------------------------------
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_by_entry_erc(self, erc: str):
        """The `.qc-dw-card` whose image `src` embeds the given
        `objectEntryExternalReferenceCode` — the stable, record-level
        identity signal confirmed live (see module docstring), independent
        of card position/order."""
        return self.page.locator(f'{self.CARD} img[src*="objectEntryExternalReferenceCode={erc}"]').locator(
            "xpath=ancestor::a[1]"
        )

    def is_card_visible_for_erc(self, erc: str) -> bool:
        return self.card_by_entry_erc(erc).count() > 0 and self.card_by_entry_erc(erc).first.is_visible()

    def card_href_for_erc(self, erc: str) -> str:
        return self.card_by_entry_erc(erc).first.get_attribute("href") or ""

    def card_opens_new_tab_for_erc(self, erc: str) -> bool:
        return self.card_by_entry_erc(erc).first.get_attribute("target") == "_blank"

    # ---- Weather widget -----------------------------------------------------
    def is_weather_widget_visible(self) -> bool:
        return self.page.locator(self.WEATHER_WIDGET).count() > 0 and self.page.locator(
            self.WEATHER_WIDGET
        ).first.is_visible()

    def weather_title_text(self) -> str:
        return self.text(self.WEATHER_TITLE).strip()

    def is_weather_first_in_row(self) -> bool:
        """True when the Weather mount is the FIRST child of
        `.qc-dw-row` — the delivery-surface signal for "Display Order = 1"
        per the case text (assert position, not the live weather VALUES,
        which are non-deterministic — see module docstring)."""
        return self.page.locator(self.WIDGETS_ROW).evaluate(
            "row => row.firstElementChild && row.firstElementChild.matches('.qc-dw-weather, [data-qc-weather-widget]')"
        )
