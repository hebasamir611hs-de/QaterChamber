"""
cms/tests/media_center/test_mc_band_control_panel.py — PBI 130709 Media Center
Home Page: Subscription Band cases (previously blocked by bug 149354).

Since the bug 149354 fix (live 2026-10-19) the band's fields live on the hero
singleton QCDEMO-130709-HERO-MAIN (`manage-media-center-hero`):
Subscription Icon (.svg/.png <= 2 MB), Subscription Heading (150),
Subscription Description (300), Email Field Placeholder (60), Subscribe
Button Label (30), each with a required "— العربية" twin. The public band is
`section.qc-mc-sub` on /web/qatar-chamber/media-center, reading
/o/c/mediacenterheros by ERC QCDEMO-130709-HERO-MAIN.

The cases' disposable QCTEST-130709-BAND-01 cannot exist (singleton), so every
case edits the live hero inside `hero_session()` (user-approved lock +
snapshot + edit + exact restore + empty diff, plus the rules-4b concurrency
guard). The cases' QCTEST precondition values are read as "the band's current
stored values" (the snapshot).

Run serially: python -m pytest cms/tests/media_center/test_mc_band_control_panel.py -n 1
"""

from __future__ import annotations

import os

import pytest

from cms.pages.media_center.mc_hero_admin_page import (
    K_SUB_BUTTON,
    K_SUB_DESC,
    K_SUB_EMAIL,
    K_SUB_HEADING,
    K_SUB_ICON,
    MSG_ARABIC_REQUIRED,
    MCHeroAdminPage,
    record_diff,
)
from cms.tests.media_center.hero_support import (
    FIXTURES,
    attach,
    editbar_names_published,
    hero_session,
    layout_problems,
    public_flat,
    public_read,
    record_finding,
    refusal_names,
)

pytestmark = [pytest.mark.pbi_130709, pytest.mark.media, pytest.mark.xdist_group(name="mc_hero_130709")]

LABELS = {K_SUB_HEADING: "Subscription Heading", K_SUB_DESC: "Subscription Description",
          K_SUB_EMAIL: "Email Field Placeholder", K_SUB_BUTTON: "Subscribe Button Label"}
FLAT = {K_SUB_HEADING: "band_heading", K_SUB_DESC: "band_desc", K_SUB_EMAIL: "band_placeholder",
        K_SUB_BUTTON: "band_button"}
NODE = {K_SUB_HEADING: "heading", K_SUB_DESC: "desc", K_SUB_BUTTON: "button"}


def _api_text(record: dict, key: str, locale: str) -> str:
    return (record.get(f"{key}_i18n") or {}).get("en_US" if locale == "en" else "ar_SA", "")


def _band_value(state: dict, key: str):
    return public_flat(state).get(FLAT[key])


def _band_problems(state: dict, key: str, want: str) -> list[str]:
    """Clipping / truncation of one band element (Rule 1 / Rule 5.2)."""
    band = state.get("band") or {}
    if not band:
        return ["subscription band not rendered"]
    if key == K_SUB_EMAIL:
        problems = []
        if band.get("placeholder") != want:
            problems.append(f"placeholder differs: {band.get('placeholder')!r}")
        node = band.get("input") or {}
        if node and band.get("placeholder_text_width") and band["placeholder_text_width"] > node["client_width"]:
            problems.append(f"placeholder text ({band['placeholder_text_width']:.0f}px) wider than the input "
                            f"({node['client_width']}px) - cut off")
        if state["doc_scroll_width"] > state["doc_client_width"] + 1:
            problems.append("page scrolls horizontally")
        return problems
    pseudo = {"x": band.get(NODE[key]), "viewport": state["viewport"],
              "doc_scroll_width": state["doc_scroll_width"], "doc_client_width": state["doc_client_width"]}
    problems = layout_problems(pseudo, "x", want)
    if key == K_SUB_BUTTON:
        box, label = band.get("button_box") or {}, band.get("button") or {}
        if box and label and (label["right"] > box["right"] + 1 or label["left"] < box["left"] - 1):
            problems.append(f"button label overflows its button ({label['left']:.0f}..{label['right']:.0f} vs "
                            f"{box['left']:.0f}..{box['right']:.0f})")
        if box and box["scroll_width"] > box["client_width"] + 1:
            problems.append(f"button clips its label (scrollWidth {box['scroll_width']} > {box['client_width']})")
    return [p.replace("x ", f"{NODE[key]} ", 1) for p in problems]


# ===========================================================================
# Case shapes
# ===========================================================================
def _positive_text(browser, tc: str, key: str, en: str, ar: str):
    with hero_session(browser, tc) as s:
        d = s.driver
        assert editbar_names_published(d), f"edit bar does not name the entry + PUBLISHED: {d.editing_bar_text()!r}"
        d.set_text(key, en)
        d.set_text(key, ar, arabic=True)
        assert d.value_of(key) == en and d.value_of(key, arabic=True) == ar
        assert d.text_direction(key, arabic=True) == "rtl", "the Arabic box does not type right-to-left"
        result = d.publish()
        result["screenshot"] = d.evidence(f"{tc}_after_publish")
        attach(result, f"{tc} publish")
        assert result["went_through"], f"Publish did not go through: {result['messages']}"
        assert d.shows_publish_success(result["editbar"]), f"no success message: {result['editbar']}"
        stored = d.api_get()
        assert _api_text(stored, key, "en") == en and _api_text(stored, key, "ar") == ar, \
            f"stored values differ: {stored.get(f'{key}_i18n')}"
        assert stored["dateModified"] != s.snapshot["dateModified"], "Last modified did not change"
        d.open_list()
        assert d.row_status() == "Published", f"row badge {d.row_status()!r}"
        out = {}
        for locale, want in (("en", en), ("ar", ar)):
            res = public_read(browser, locale, lambda st, w=want: _band_value(st, key) == w,
                              shot=f"{tc}_public_{locale}", band=True)
            out[locale] = {"value": _band_value(res["state"], key), "seconds": res["seconds"], "ok": res["ok"],
                           "dir": res["flat"]["band_dir"], "screenshot": res["screenshot"]}
        attach(out, f"{tc} public band EN/AR")
        assert out["en"]["ok"], f"EN band shows {out['en']['value']!r}, expected {en!r}"
        assert out["ar"]["ok"], f"AR band shows {out['ar']['value']!r}, expected {ar!r}"
        assert out["ar"]["dir"] == "rtl", f"AR band direction {out['ar']['dir']!r}"


def _refused_publish(browser, tc: str, key: str, prepare, expect_label: str | None = None,
                     message: str | None = None) -> dict:
    with hero_session(browser, tc) as s:
        d = s.driver
        before_public = s.public["en"]
        prepared = prepare(d)
        attach(prepared or {}, f"{tc} form before publish")
        result = d.publish()
        result["screenshot"] = d.evidence(f"{tc}_after_publish")
        attach(result, f"{tc} publish attempt")
        changed = record_diff(s.snapshot, d.api_get())
        pub = public_read(browser, "en", shot=f"{tc}_public_en", band=True)
        attach({"stored_changes": changed, "public": pub["flat"], "public_before": before_public}, f"{tc} outcome")
        assert not result["went_through"] and not changed, \
            f"Publish was ACCEPTED (expected a refusal); stored changes: {changed}"
        if expect_label:
            assert refusal_names(result, d, key, expect_label), \
                f"the refusal does not name {expect_label!r}: {result['messages']!r}"
        if message:
            shown = result["messages"] + " " + d.body_text()
            assert message in shown, f"expected message {message!r}; shown: {result['messages']!r}"
        assert pub["flat"] == before_public, f"public page changed: {pub['flat']} vs {before_public}"
        return {"public_en": pub, "result": result}


def _empty_en(browser, tc: str, key: str):
    def prepare(d: MCHeroAdminPage):
        d.set_text(key, "")
        return {"en": d.value_of(key), "ar": d.value_of(key, arabic=True)}
    _refused_publish(browser, tc, key, prepare, expect_label=LABELS[key])


def _limit_case(browser, tc: str, key: str, en_max: str, en_over: str, ar_max: str, us_limit: int):
    with hero_session(browser, tc) as s:
        d = s.driver
        facts = {"counter_en": d.counter_reading(key), "counter_ar": d.counter_reading(key, arabic=True),
                 "maxlength_en": d.native_max_length(key), "maxlength_ar": d.native_max_length(key, arabic=True)}
        counter = facts["counter_en"][1] if facts["counter_en"] else None
        d.type_text(key, en_max)
        d.type_text(key, ar_max, arabic=True)
        facts["typed_len_en"], facts["typed_len_ar"] = len(d.value_of(key)), len(d.value_of(key, arabic=True))
        result = d.publish()
        facts["publish_max"] = {k: result[k] for k in ("went_through", "messages", "editbar")}
        facts["publish_max_shot"] = d.evidence(f"{tc}_publish_max")
        assert counter is not None, "no character counter / limit readable on the field"
        if counter < us_limit:
            attach(facts, f"{tc} limit facts")
            pytest.fail(f"implemented limit L={counter} < US limit {us_limit} (Rule 5.3)")
        assert facts["typed_len_en"] == us_limit and facts["typed_len_ar"] == us_limit, f"typed lengths {facts}"
        assert result["went_through"], f"the {us_limit}-character values were refused: {result['messages']}"
        stored = d.api_get()
        assert _api_text(stored, key, "en") == en_max and _api_text(stored, key, "ar") == ar_max
        problems = {}
        for locale, want in (("en", en_max), ("ar", ar_max)):
            res = public_read(browser, locale, lambda st, w=want: _band_value(st, key) == w,
                              shot=f"{tc}_public_{locale}_max", band=True)
            problems[locale] = _band_problems(res["state"], key, want)
            if not res["ok"]:
                problems[locale].insert(0, f"public value never became the {us_limit}-char value")
            facts[f"public_{locale}"] = {"shot": res["screenshot"], "problems": problems[locale],
                                         "seconds": res["seconds"]}
        d.open_hero()
        d.type_text(key, en_over)
        facts["typed_len_over"] = len(d.value_of(key))
        over = d.publish()
        facts["publish_over"] = {k: over[k] for k in ("went_through", "messages", "editbar")}
        facts["publish_over_shot"] = d.evidence(f"{tc}_publish_over")
        stored_over = _api_text(d.api_get(), key, "en")
        facts["stored_len_after_over"] = len(stored_over)
        if len(stored_over) > us_limit:
            res = public_read(browser, "en", lambda st, w=stored_over: _band_value(st, key) == w,
                              shot=f"{tc}_public_en_over", band=True)
            problems["en_over"] = _band_problems(res["state"], key, stored_over)
            record_finding(tc, "over-limit value accepted", key=key, counter=counter, stored_len=len(stored_over))
        attach(facts, f"{tc} limit facts")
        bad = {k: v for k, v in problems.items() if v}
        if bad:
            record_finding(tc, "char-limit frontend", problems=bad)
        assert not bad, f"long text breaks the public subscription band UI: {bad}"


# ===========================================================================
# Heading / Description / Placeholder / Button
# ===========================================================================
@pytest.mark.tc_149210
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149210_band_heading_reaches_public_en_ar(browser):
    """MEDIA-MCHUB-TC-156 — valid Subscription Heading reaches the band heading (EN + AR)."""
    _positive_text(browser, "149210", K_SUB_HEADING, "QCTEST Stay close to Qatar business news",
                   "QCTEST ابقَ قريبًا من أخبار الأعمال في قطر")


@pytest.mark.tc_149211
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149211_empty_en_band_heading_refused(browser):
    """MEDIA-MCHUB-TC-157 — empty English Subscription Heading is refused; public value unchanged."""
    _empty_en(browser, "149211", K_SUB_HEADING)


@pytest.mark.tc_149212
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149212_band_description_reaches_public_en_ar(browser):
    """MEDIA-MCHUB-TC-158 — valid Subscription Description reaches the band description (EN + AR)."""
    _positive_text(browser, "149212", K_SUB_DESC, "QCTEST Get selected news and reports from Qatar Chamber.",
                   "QCTEST احصل على أخبار وتقارير مختارة من غرفة قطر.")


@pytest.mark.tc_149213
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149213_empty_en_band_description_refused(browser):
    """MEDIA-MCHUB-TC-159 — empty English Subscription Description is refused; public value unchanged."""
    _empty_en(browser, "149213", K_SUB_DESC)


@pytest.mark.tc_149214
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149214_band_email_placeholder_reaches_public_en_ar(browser):
    """MEDIA-MCHUB-TC-160 — valid Email Field Placeholder reaches the band email field (EN + AR)."""
    _positive_text(browser, "149214", K_SUB_EMAIL, "QCTEST Your work e-mail", "QCTEST بريدك الإلكتروني للعمل")


@pytest.mark.tc_149215
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149215_empty_en_band_email_placeholder_refused(browser):
    """MEDIA-MCHUB-TC-161 — empty English Email Field Placeholder is refused; public value unchanged."""
    _empty_en(browser, "149215", K_SUB_EMAIL)


EMAIL_60 = "QCTEST-ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZA"
EMAIL_61 = "QCTEST-ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZAB"


@pytest.mark.tc_149216
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149216_band_email_placeholder_60_char_limit(browser):
    """MEDIA-MCHUB-TC-162 — Email Field Placeholder accepts 60 chars, 61st per Rule 5, renders intact EN + AR."""
    assert len(EMAIL_60) == 60 and len(EMAIL_61) == 61
    _limit_case(browser, "149216", K_SUB_EMAIL, EMAIL_60, EMAIL_61, "ق" * 60, 60)


@pytest.mark.tc_149217
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149217_band_button_label_reaches_public_en_ar(browser):
    """MEDIA-MCHUB-TC-163 — valid Subscribe Button Label reaches the band Subscribe button (EN + AR)."""
    _positive_text(browser, "149217", K_SUB_BUTTON, "QCTEST Join", "QCTEST انضم")


@pytest.mark.tc_149218
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149218_empty_en_band_button_label_refused(browser):
    """MEDIA-MCHUB-TC-164 — empty English Subscribe Button Label is refused; public value unchanged."""
    _empty_en(browser, "149218", K_SUB_BUTTON)


BUTTON_30 = "QCTEST-ABCDEFGHIJKLMNOPQRSTUVW"
BUTTON_31 = "QCTEST-ABCDEFGHIJKLMNOPQRSTUVWX"


@pytest.mark.tc_149219
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149219_band_button_label_30_char_limit(browser):
    """MEDIA-MCHUB-TC-165 — Subscribe Button Label accepts 30 chars, 31st per Rule 5, renders intact EN + AR."""
    assert len(BUTTON_30) == 30 and len(BUTTON_31) == 31
    _limit_case(browser, "149219", K_SUB_BUTTON, BUTTON_30, BUTTON_31, "ق" * 30, 30)


# ===========================================================================
# Subscription Icon
# ===========================================================================
ICON_FIXTURE = os.path.join(FIXTURES, "qctest-envelope.svg")
ICON_MARKER = "qctest-envelope-130709"


@pytest.mark.tc_149233
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149233_valid_svg_icon_shown_in_public_band(browser):
    """MEDIA-MCHUB-TC-179 — a valid SVG Subscription Icon is saved and shown in the public band."""
    with hero_session(browser, "149233") as s:
        d = s.driver
        name_before = s.snapshot["subscriptionIcon"]["name"]
        assert name_before in d.upload_block_text(K_SUB_ICON), "icon block does not show the current file"
        attempt = d.try_upload(K_SUB_ICON, ICON_FIXTURE, "qctest-envelope")
        attempt["shot"] = d.evidence("149233_after_pick")
        attach(attempt, "149233 upload attempt")
        assert attempt["attached"], f"qctest-envelope.svg was not taken as the pending file: {attempt}"
        result = d.publish()
        result["screenshot"] = d.evidence("149233_after_publish")
        attach(result, "149233 publish")
        assert result["went_through"], f"Publish did not go through: {result['messages']}"
        stored = d.api_get()["subscriptionIcon"]["name"]
        d.open_hero()
        block = d.upload_block_text(K_SUB_ICON)
        d.open_list()
        badge = d.row_status()
        assert stored.startswith("qctest-envelope"), f"stored icon {stored!r}"
        assert f"Current file: {stored}" in block, f"icon block after save: {block[:200]!r}"
        assert badge == "Published", f"row badge {badge!r}"
        # The band renders an uploaded icon as <img src="/documents/.../<file name>/..."> (live 2026-10-19).
        res = public_read(browser, "en", lambda st: f"/{stored}/" in ((st.get("band") or {}).get("icon_html") or "")
                          or ICON_MARKER in ((st.get("band") or {}).get("icon_html") or ""),
                          shot="149233_public_en", band=True)
        icon_html = (res["state"].get("band") or {}).get("icon_html") or ""
        attach({"stored": stored, "icon_html_head": icon_html[:300], "seconds": res["seconds"]}, "149233 public")
        assert res["ok"], f"the public band icon is not qctest-envelope.svg (badge html {icon_html[:160]!r})"


@pytest.mark.tc_149234
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149234_required_icon_cannot_be_removed(browser):
    """MEDIA-MCHUB-TC-180 — the required Subscription Icon cannot be removed and saved empty."""
    with hero_session(browser, "149234") as s:
        d = s.driver
        name_before = s.snapshot["subscriptionIcon"]["name"]
        block_before = d.upload_block_text(K_SUB_ICON)
        removed = d.remove_image(K_SUB_ICON)
        removed["shot"] = d.evidence("149234_after_remove")
        result = d.publish()
        result["screenshot"] = d.evidence("149234_after_publish")
        stored = d.api_get().get("subscriptionIcon") or {}
        pub = public_read(browser, "en", shot="149234_public_en", band=True)
        attach({"block_before": block_before, "remove": removed, "publish": result, "stored": stored.get("name"),
                "public_icon_sha": pub["flat"]["band_icon_sha"]}, "149234 facts")
        assert name_before in block_before
        assert stored.get("id") == s.snapshot["subscriptionIcon"]["id"], \
            f"the band was SAVED WITHOUT its Subscription Icon (stored {stored!r})"
        assert not result["went_through"], "Publish went through although the icon was removed"
        assert refusal_names(result, d, K_SUB_ICON, "Subscription Icon"), \
            f"the refusal does not report 'Subscription Icon' as required: {result['messages']!r}"
        assert pub["flat"]["band_icon_sha"] == s.public["en"]["band_icon_sha"], "public band icon changed"


# ===========================================================================
# Bilingual
# ===========================================================================
@pytest.mark.tc_149276
@pytest.mark.functional_low
@pytest.mark.control_panel
def test_149276_band_publish_without_arabic_blocked(browser):
    """MEDIA-MCHUB-TC-222 — publishing the band without Arabic is blocked with 'Arabic content is required.'"""
    en_only = "QCTEST EN only heading"

    def prepare(d: MCHeroAdminPage):
        d.set_text(K_SUB_HEADING, en_only)
        d.set_text(K_SUB_HEADING, "", arabic=True)
        return {"en": d.value_of(K_SUB_HEADING), "ar": d.value_of(K_SUB_HEADING, arabic=True)}

    out = _refused_publish(browser, "149276", K_SUB_HEADING, prepare, message=MSG_ARABIC_REQUIRED)
    assert en_only not in str(out["public_en"]["flat"]), "English-only QCTEST heading shows on the EN page"
    ar = public_read(browser, "ar", shot="149276_public_ar", band=True)
    attach(ar["flat"], "149276 public AR")
    assert en_only not in str(ar["flat"]), "English-only QCTEST content shows on the Arabic page"


@pytest.mark.tc_149179
@pytest.mark.edge
@pytest.mark.web
def test_149179_band_arabic_fallback(browser):
    """MEDIA-MCHUB-TC-125 — the band falls back when its Arabic content is missing (AR page).

    The precondition (band published with EN heading 'QCTEST Stay connected' and
    EMPTY Arabic heading/description) is attempted through Object Authoring as
    the Editor. If the CMS refuses it (Arabic required), the state cannot occur
    and the case is reported BLOCKED with that evidence — it is never forced
    through another path."""
    with hero_session(browser, "149179") as s:
        d = s.driver
        d.set_text(K_SUB_HEADING, "QCTEST Stay connected")
        d.set_text(K_SUB_HEADING, "", arabic=True)
        d.set_text(K_SUB_DESC, "", arabic=True)
        result = d.publish()
        result["screenshot"] = d.evidence("149179_precondition_publish")
        attach(result, "149179 precondition publish")
        if not result["went_through"]:
            pytest.skip("BLOCKED: the precondition cannot be created — Object Authoring refuses to publish the "
                        f"band with empty Arabic heading/description ({result['messages'][:200]!r}); see 149276")
        res = public_read(browser, "ar", lambda st: (st.get("band") or {}).get("ready") == "true",
                          shot="149179_public_ar", band=True)
        band = res["state"].get("band") or {}
        flat = res["flat"]
        attach({"flat": flat, "input_enabled": band.get("input_enabled"),
                "button_enabled": band.get("button_enabled")}, "149179 public AR band")
        assert band, "the band does not render on the AR page"
        assert flat["band_heading"] == "QCTEST Stay connected", f"AR heading {flat['band_heading']!r} (expected EN fallback)"
        assert flat["band_desc"], "AR description is empty (no fallback)"
        assert band.get("input_enabled") and band.get("button_enabled"), "email field / Subscribe button not usable"
