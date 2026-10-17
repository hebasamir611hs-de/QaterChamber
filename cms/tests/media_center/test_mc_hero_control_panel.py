"""
cms/tests/media_center/test_mc_hero_control_panel.py — PBI 130709 Media Center
Home Page: Control_Panel cases on the Media Center Hero
(`manage-media-center-hero`, singleton QCDEMO-130709-HERO-MAIN).

The hero page holds ONE record and cannot create a second one (live
2026-10-07: "This page holds this one record only."), so the cases'
disposable QCTEST-130709-HERO-01 is not creatable. Per the user's decision
(2026-10-07) every case edits the LIVE hero inside `hero_session()` (lock +
snapshot + restore + diff, see hero_support.py). The cases' QCTEST
precondition values ("QCTEST Media Center", "qctest-hero-base.jpg", …) are
therefore read as "the hero's current stored value" — the snapshot.

Run serially: python -m pytest cms/tests/media_center/test_mc_hero_control_panel.py -n 1
"""

from __future__ import annotations

import os

import pytest

from cms.pages.media_center.mc_hero_admin_page import (
    K_DESC,
    K_HEADLINE,
    K_IMAGE,
    K_LABEL,
    K_SEARCH,
    MSG_ACCESS_DENIED,
    MSG_ARABIC_REQUIRED,
    MSG_FILE_INVALID_AR,
    MSG_FILE_INVALID_EN,
    MSG_SAVED_AND_PUBLISHED,
    ROLE_MEMBER,
    MCHeroAdminPage,
)
from cms.tests.media_center.hero_support import (
    DESKTOP,
    FIXTURES,
    attach,
    editbar_names_published,
    hero_session,
    layout_problems,
    placeholder_problems,
    public_read,
    record_finding,
    refusal_names,
)
from core.web.browser import new_context

GROUP = pytest.mark.xdist_group(name="mc_hero_130709")
pytestmark = [pytest.mark.pbi_130709, pytest.mark.control_panel, pytest.mark.media, GROUP]

LABELS = {K_LABEL: "Page Label", K_HEADLINE: "Hero Headline", K_SEARCH: "Search Placeholder",
          K_DESC: "Hero Description"}
PUBLIC_KEY = {K_LABEL: "label", K_HEADLINE: "headline", K_SEARCH: "placeholder", K_DESC: "desc"}


def _api_text(record: dict, key: str, locale: str) -> str:
    return (record.get(f"{key}_i18n") or {}).get("en_US" if locale == "en" else "ar_SA", "")


def _public_value(flat: dict, key: str):
    return flat.get(PUBLIC_KEY[key])


# ===========================================================================
# Shared case shapes
# ===========================================================================
def _positive_text(browser, tc: str, key: str, en: str, ar: str):
    with hero_session(browser, tc) as s:
        d = s.driver
        # Steps 1-2: manage page + the hero loaded with its PUBLISHED bar
        assert editbar_names_published(d), f"edit bar does not name the entry + PUBLISHED: {d.editing_bar_text()!r}"
        # Step 3: both values, Arabic box right-to-left
        d.set_text(key, en)
        d.set_text(key, ar, arabic=True)
        assert d.value_of(key) == en and d.value_of(key, arabic=True) == ar
        assert d.text_direction(key, arabic=True) == "rtl", "the Arabic box does not type right-to-left"
        # Step 4: Publish
        result = d.publish()
        result["screenshot"] = d.evidence(f"{tc}_after_publish")
        attach(result, f"{tc} publish")
        assert result["went_through"], f"Publish did not go through: {result['messages']}"
        assert any(MSG_SAVED_AND_PUBLISHED in t for t in result["editbar"]), f"no success message: {result['editbar']}"
        stored = d.api_get()
        assert _api_text(stored, key, "en") == en and _api_text(stored, key, "ar") == ar, \
            f"stored values differ: {stored.get(f'{key}_i18n')}"
        assert stored["dateModified"] != s.snapshot["dateModified"], "Last modified did not change"
        d.open_list()
        assert d.row_status() == "Published", f"row badge {d.row_status()!r}"
        # Steps 5-6: public EN / AR (fresh logged-out contexts)
        out = {}
        for locale, want in (("en", en), ("ar", ar)):
            res = public_read(browser, locale, lambda st, w=want: _public_value(_flat(st), key) == w,
                              shot=f"{tc}_public_{locale}")
            out[locale] = {"value": _public_value(res["flat"], key), "seconds": res["seconds"], "ok": res["ok"],
                           "dir": res["flat"]["section_dir"], "screenshot": res["screenshot"]}
        attach(out, f"{tc} public EN/AR")
        assert out["en"]["ok"], f"EN hero shows {out['en']['value']!r}, expected {en!r}"
        assert out["ar"]["ok"], f"AR hero shows {out['ar']['value']!r}, expected {ar!r}"
        assert out["ar"]["dir"] == "rtl", f"AR hero direction {out['ar']['dir']!r}"


def _flat(state: dict) -> dict:
    from cms.tests.media_center.hero_support import public_flat  # noqa: PLC0415
    return public_flat(state)


def _refused_publish(browser, tc: str, key: str, prepare, expect_label: str | None = None,
                     message: str | None = None):
    """Prepare the form (callable(driver)), Publish, expect a refusal that names
    the field / shows `message`, nothing stored, public value unchanged."""
    with hero_session(browser, tc) as s:
        d = s.driver
        before_public = s.public["en"]
        prepared = prepare(d)
        attach(prepared or {}, f"{tc} form before publish")
        result = d.publish()
        result["screenshot"] = d.evidence(f"{tc}_after_publish")
        attach(result, f"{tc} publish attempt")
        stored = d.api_get()
        from cms.pages.media_center.mc_hero_admin_page import record_diff  # noqa: PLC0415
        changed = record_diff(s.snapshot, stored)
        pub = public_read(browser, "en", shot=f"{tc}_public_en")
        attach({"stored_changes": changed, "public": pub["flat"], "public_before": before_public}, f"{tc} outcome")
        assert not result["went_through"] and not changed, \
            f"Publish was ACCEPTED (expected a refusal); stored changes: {changed}"
        if expect_label:
            assert refusal_names(result, d, key, expect_label), \
                f"the refusal does not name {expect_label!r}: {result['messages']!r}"
        if message:
            shown = result["messages"] + " " + d.body_text()
            assert message in shown, f"expected message {message!r}; shown: {result['messages']!r}"
        assert pub["flat"] == before_public, f"public hero changed: {pub['flat']} vs {before_public}"
        return result


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
            res = public_read(browser, locale, lambda st, w=want: _public_value(_flat(st), key) == w,
                              shot=f"{tc}_public_{locale}_max")
            st = res["state"]
            problems[locale] = (placeholder_problems(st, want) if key == K_SEARCH
                                else layout_problems(st, PUBLIC_KEY[key], want))
            if not res["ok"]:
                problems[locale].insert(0, f"public value never became the {us_limit}-char value")
            facts[f"public_{locale}"] = {"shot": res["screenshot"], "problems": problems[locale],
                                         "seconds": res["seconds"]}
        # Step 8: the over-limit value
        d.open_hero()
        d.type_text(key, en_over)
        facts["typed_len_over"] = len(d.value_of(key))
        over = d.publish()
        facts["publish_over"] = {k: over[k] for k in ("went_through", "messages", "editbar")}
        facts["publish_over_shot"] = d.evidence(f"{tc}_publish_over")
        stored_over = _api_text(d.api_get(), key, "en")
        facts["stored_len_after_over"] = len(stored_over)
        if len(stored_over) > us_limit:
            for locale in ("en",):
                res = public_read(browser, locale, lambda st, w=stored_over: _public_value(_flat(st), key) == w,
                                  shot=f"{tc}_public_{locale}_over")
                st = res["state"]
                p = (placeholder_problems(st, stored_over) if key == K_SEARCH
                     else layout_problems(st, PUBLIC_KEY[key], stored_over))
                problems[f"{locale}_over"] = p
            record_finding(tc, "over-limit value accepted", key=key, counter=counter,
                           stored_len=len(stored_over))
        attach(facts, f"{tc} limit facts")
        bad = {k: v for k, v in problems.items() if v}
        if bad:
            record_finding(tc, "char-limit frontend", problems=bad)
        assert not bad, f"long text breaks the public hero UI: {bad}"


def _image_reject(browser, tc: str, fixture: str, stem: str, message: str, locale: str = "en"):
    with hero_session(browser, tc, locale=locale) as s:
        d = s.driver
        name_before = s.snapshot["heroBackgroundImage"]["name"]
        block_before = d.upload_block_text()
        attempt = d.try_upload_image(os.path.join(FIXTURES, fixture), stem)
        attempt["shot_after_pick"] = d.evidence(f"{tc}_after_pick")
        result = d.publish()
        result["screenshot"] = d.evidence(f"{tc}_after_publish")
        stored = d.api_get()
        shown = " | ".join([" ".join(attempt.get("errors", [])), attempt.get("picker_text", ""),
                            attempt.get("field_text", ""), " ".join(attempt.get("field_errors", [])),
                            result["messages"]])
        pub = public_read(browser, "en", shot=f"{tc}_public_en")
        facts = {"block_before": block_before, "attempt": attempt, "publish": result,
                 "stored_image": stored["heroBackgroundImage"]["name"], "public_bg": pub["flat"]["bg_file"]}
        attach(facts, f"{tc} upload facts")
        assert name_before in block_before, f"attachment block does not show the current file {name_before!r}"
        assert stored["heroBackgroundImage"]["id"] == s.snapshot["heroBackgroundImage"]["id"], \
            f"the {fixture} was STORED as the hero background ({stored['heroBackgroundImage']['name']})"
        assert pub["flat"]["bg_file"] == s.public["en"]["bg_file"], f"public background changed: {pub['flat']}"
        assert message in shown, f"expected {message!r}; shown: {shown[:400]!r}"


# ===========================================================================
# Page Label
# ===========================================================================
@pytest.mark.tc_149183
@pytest.mark.functional_low
def test_149183_page_label_reaches_public_en_ar(browser):
    """MEDIA-MCHUB-TC-129 — valid Page Label reaches the hero page label (EN + AR)."""
    _positive_text(browser, "149183", K_LABEL, "QCTEST Media Hub", "QCTEST المركز الإعلامي للغرفة")


@pytest.mark.tc_149184
@pytest.mark.functional_low
def test_149184_empty_en_page_label_refused(browser):
    """MEDIA-MCHUB-TC-130 — empty English Page Label is refused; public value unchanged."""
    def prepare(d: MCHeroAdminPage):
        d.set_text(K_LABEL, "")
        return {"en": d.value_of(K_LABEL), "ar": d.value_of(K_LABEL, arabic=True)}
    _refused_publish(browser, "149184", K_LABEL, prepare, expect_label="Page Label")


# ===========================================================================
# Hero Headline
# ===========================================================================
@pytest.mark.tc_149185
@pytest.mark.functional_low
def test_149185_headline_reaches_public_en_ar(browser):
    """MEDIA-MCHUB-TC-131 — valid Hero Headline reaches the centred hero headline (EN + AR)."""
    _positive_text(browser, "149185", K_HEADLINE, "QCTEST-130709 Your gateway to Qatar Chamber's official news",
                   "QCTEST-130709 بوابتك إلى أخبار غرفة قطر الرسمية")


@pytest.mark.tc_149186
@pytest.mark.functional_low
def test_149186_empty_en_headline_refused(browser):
    """MEDIA-MCHUB-TC-132 — empty English Hero Headline is refused; public value unchanged."""
    def prepare(d: MCHeroAdminPage):
        d.set_text(K_HEADLINE, "")
        return {"en": d.value_of(K_HEADLINE), "ar": d.value_of(K_HEADLINE, arabic=True)}
    _refused_publish(browser, "149186", K_HEADLINE, prepare, expect_label="Hero Headline")


HEADLINE_150 = "QCTEST-" + ("ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 6)[:143]
HEADLINE_151 = "QCTEST-" + ("ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 6)[:144]


@pytest.mark.tc_149187
@pytest.mark.functional_low
def test_149187_headline_150_char_limit(browser):
    """MEDIA-MCHUB-TC-133 — Hero Headline accepts 150 chars, 151st per Rule 5, renders intact EN + AR."""
    assert len(HEADLINE_150) == 150 and len(HEADLINE_151) == 151
    _limit_case(browser, "149187", K_HEADLINE, HEADLINE_150, HEADLINE_151, "ق" * 150, 150)


@pytest.mark.tc_149220
@pytest.mark.functional_low
def test_149220_whitespace_headline_refused(browser):
    """MEDIA-MCHUB-TC-166 — whitespace-only Hero Headline is refused; public headline unchanged."""
    def prepare(d: MCHeroAdminPage):
        d.set_text(K_HEADLINE, "     ")
        return {"en": d.value_of(K_HEADLINE)}
    _refused_publish(browser, "149220", K_HEADLINE, prepare, expect_label="Hero Headline")


# ===========================================================================
# Search Placeholder
# ===========================================================================
@pytest.mark.tc_149188
@pytest.mark.functional_low
def test_149188_search_placeholder_reaches_public_en_ar(browser):
    """MEDIA-MCHUB-TC-134 — valid Search Placeholder reaches the hero search field (EN + AR)."""
    _positive_text(browser, "149188", K_SEARCH, "QCTEST Search all media", "QCTEST ابحث في كل الوسائط")


@pytest.mark.tc_149189
@pytest.mark.functional_low
def test_149189_empty_en_search_placeholder_refused(browser):
    """MEDIA-MCHUB-TC-135 — empty English Search Placeholder is refused; public value unchanged."""
    def prepare(d: MCHeroAdminPage):
        d.set_text(K_SEARCH, "")
        return {"en": d.value_of(K_SEARCH), "ar": d.value_of(K_SEARCH, arabic=True)}
    _refused_publish(browser, "149189", K_SEARCH, prepare, expect_label="Search Placeholder")


SEARCH_100 = "QCTEST-" + ("ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 4)[:93]
SEARCH_101 = "QCTEST-" + ("ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 4)[:94]


@pytest.mark.tc_149190
@pytest.mark.functional_low
def test_149190_search_placeholder_100_char_limit(browser):
    """MEDIA-MCHUB-TC-136 — Search Placeholder accepts 100 chars, 101st per Rule 5, renders intact EN + AR."""
    assert len(SEARCH_100) == 100 and len(SEARCH_101) == 101
    _limit_case(browser, "149190", K_SEARCH, SEARCH_100, SEARCH_101, "ق" * 100, 100)


# ===========================================================================
# Hero Description (rich text)
# ===========================================================================
DESC_EN = "QCTEST official news, press releases and media from Qatar Chamber."
DESC_AR = "QCTEST الأخبار الرسمية والبيانات الصحفية من غرفة قطر."


@pytest.mark.tc_149221
@pytest.mark.functional_low
def test_149221_formatted_description_renders_bold(browser):
    """MEDIA-MCHUB-TC-167 — formatted Hero Description renders formatted on the public EN + AR hero."""
    with hero_session(browser, "149221") as s:
        d = s.driver
        d.type_rich(K_DESC, DESC_EN)
        d.bold_phrase(K_DESC, "press releases")
        d.type_rich(K_DESC, DESC_AR, arabic=True)
        d.bold_phrase(K_DESC, "البيانات الصحفية", arabic=True)
        html_en, html_ar = d.rich_data(K_DESC), d.rich_data(K_DESC, arabic=True)
        attach({"en": html_en, "ar": html_ar}, "149221 editor html")
        assert "<strong>press releases</strong>" in html_en, f"EN editor html {html_en!r}"
        assert "<strong>البيانات الصحفية</strong>" in html_ar, f"AR editor html {html_ar!r}"
        result = d.publish()
        result["screenshot"] = d.evidence("149221_after_publish")
        attach(result, "149221 publish")
        assert result["went_through"], f"Publish did not go through: {result['messages']}"
        out = {}
        for locale, text, bold in (("en", DESC_EN, "press releases"), ("ar", DESC_AR, "البيانات الصحفية")):
            res = public_read(browser, locale,
                              lambda st, t=text: " ".join(((st.get("desc") or {}).get("text") or "").split()) == t,
                              shot=f"149221_public_{locale}")
            st = res["state"]
            out[locale] = {"ok": res["ok"], "text": (st.get("desc") or {}).get("text"),
                           "html": (st.get("desc") or {}).get("html"), "bold": st.get("desc_bold"),
                           "dir": res["flat"]["section_dir"], "shot": res["screenshot"]}
        attach(out, "149221 public EN/AR")
        for locale, bold in (("en", "press releases"), ("ar", "البيانات الصحفية")):
            assert out[locale]["ok"], f"{locale} description reads {out[locale]['text']!r}"
            assert "<" not in (out[locale]["text"] or ""), f"{locale} shows raw HTML: {out[locale]['text']!r}"
            assert bold in (out[locale]["bold"] or []), \
                f"{locale}: {bold!r} is not bold on the public hero (bold runs {out[locale]['bold']})"
        assert out["ar"]["dir"] == "rtl"


@pytest.mark.tc_149222
@pytest.mark.functional_low
def test_149222_empty_description_refused(browser):
    """MEDIA-MCHUB-TC-168 — empty English Hero Description is refused."""
    def prepare(d: MCHeroAdminPage):
        d.clear_rich(K_DESC)
        return {"en_html": d.rich_data(K_DESC)}
    _refused_publish(browser, "149222", K_DESC, prepare, expect_label="Hero Description")


@pytest.mark.tc_149223
@pytest.mark.functional_low
def test_149223_whitespace_paragraphs_description_refused(browser):
    """MEDIA-MCHUB-TC-169 — Hero Description of only spaces and empty paragraphs is refused."""
    def prepare(d: MCHeroAdminPage):
        d.type_rich(K_DESC, "    \n\n\n")
        return {"en_html": d.rich_data(K_DESC)}
    _refused_publish(browser, "149223", K_DESC, prepare, expect_label="Hero Description")


# ===========================================================================
# Hero Background Image
# ===========================================================================
@pytest.mark.tc_149224
@pytest.mark.functional_low
def test_149224_valid_jpg_background_saved_and_shown(browser):
    """MEDIA-MCHUB-TC-170 — valid JPG (< 2 MB) Hero Background Image is saved and shown publicly."""
    with hero_session(browser, "149224") as s:
        d = s.driver
        name_before = s.snapshot["heroBackgroundImage"]["name"]
        assert name_before in d.upload_block_text(), "attachment block does not show the current file"
        attempt = d.try_upload_image(os.path.join(FIXTURES, "qctest-hero-bg.jpg"), "qctest-hero-bg")
        attach(attempt, "149224 upload attempt")
        assert attempt["attached"], f"qctest-hero-bg.jpg was not taken as the pending file: {attempt}"
        result = d.publish()
        result["screenshot"] = d.evidence("149224_after_publish")
        attach(result, "149224 publish")
        assert result["went_through"], f"Publish did not go through: {result['messages']}"
        stored = d.api_get()["heroBackgroundImage"]["name"]
        d.open_hero()
        block = d.upload_block_text()
        assert stored.startswith("qctest-hero-bg"), f"stored image {stored!r}"
        assert f"Current file: {stored}" in block, f"attachment block after save: {block[:200]!r}"
        res = public_read(browser, "en", lambda st: (st.get("bg_file") or "").startswith("qctest-hero-bg"),
                          shot="149224_public_en")
        attach({"stored": stored, "public_bg": res["flat"]["bg_file"], "seconds": res["seconds"]}, "149224 public")
        assert res["ok"], f"public hero background is {res['flat']['bg_file']!r}, expected {stored!r}"


@pytest.mark.tc_149225
@pytest.mark.functional_low
def test_149225_required_background_cannot_be_removed(browser):
    """MEDIA-MCHUB-TC-171 — the required Hero Background Image cannot be removed and saved empty."""
    with hero_session(browser, "149225") as s:
        d = s.driver
        name_before = s.snapshot["heroBackgroundImage"]["name"]
        block_before = d.upload_block_text()
        removed = d.remove_image()
        removed["shot"] = d.evidence("149225_after_remove")
        result = d.publish()
        result["screenshot"] = d.evidence("149225_after_publish")
        stored = d.api_get().get("heroBackgroundImage") or {}
        pub = public_read(browser, "en", shot="149225_public_en")
        attach({"block_before": block_before, "remove": removed, "publish": result,
                "stored": stored.get("name"), "public_bg": pub["flat"]["bg_file"]}, "149225 facts")
        assert name_before in block_before
        assert stored.get("id") == s.snapshot["heroBackgroundImage"]["id"], \
            f"the hero was SAVED WITHOUT its background image (stored {stored!r})"
        assert not result["went_through"], "Publish went through although the image was removed"
        assert refusal_names(result, d, K_IMAGE, "Hero Background Image"), \
            f"the refusal does not report 'Hero Background Image' as required: {result['messages']!r}"
        assert pub["flat"]["bg_file"] == s.public["en"]["bg_file"]


@pytest.mark.tc_149226
@pytest.mark.functional_low
def test_149226_gif_background_blocked(browser):
    """MEDIA-MCHUB-TC-172 — GIF Hero Background Image is blocked with 'Unsupported file type or size.'"""
    _image_reject(browser, "149226", "qctest-hero-bg.gif", "qctest-hero-bg", MSG_FILE_INVALID_EN)


@pytest.mark.tc_149227
@pytest.mark.functional_low
def test_149227_oversized_jpg_background_blocked(browser):
    """MEDIA-MCHUB-TC-173 — 2.5 MB JPG Hero Background Image is blocked with 'Unsupported file type or size.'"""
    _image_reject(browser, "149227", "qctest-hero-bg-large.jpg", "qctest-hero-bg-large", MSG_FILE_INVALID_EN)


@pytest.mark.tc_149279
@pytest.mark.functional_low
def test_149279_file_validation_message_in_arabic_ui(browser):
    """MEDIA-MCHUB-TC-225 — file validation reads 'نوع الملف أو حجمه غير مدعوم.' in the Arabic Control Panel UI."""
    _image_reject(browser, "149279", "qctest-hero-bg.gif", "qctest-hero-bg", MSG_FILE_INVALID_AR, locale="ar")


# ===========================================================================
# Bilingual enforcement
# ===========================================================================
@pytest.mark.tc_149272
@pytest.mark.functional_low
def test_149272_publish_without_arabic_blocked(browser):
    """MEDIA-MCHUB-TC-218 — publishing the hero without Arabic is blocked with 'Arabic content is required.'"""
    en_only = "QCTEST-130709 Headline EN only"

    def prepare(d: MCHeroAdminPage):
        d.set_text(K_HEADLINE, en_only)
        d.set_text(K_HEADLINE, "", arabic=True)
        return {"en": d.value_of(K_HEADLINE), "ar": d.value_of(K_HEADLINE, arabic=True)}

    _refused_publish(browser, "149272", K_HEADLINE, prepare, message=MSG_ARABIC_REQUIRED)
    ar = public_read(browser, "ar", shot="149272_public_ar")
    attach(ar["flat"], "149272 public AR")
    assert en_only not in str(ar["flat"]), "English-only QCTEST content shows on the Arabic page"


# ===========================================================================
# Access
# ===========================================================================
@pytest.mark.tc_149335
@pytest.mark.auth
@pytest.mark.regression
def test_149335_site_member_refused_on_hub_authoring(browser):
    """MEDIA-MCHUB-TC-281 — a signed-in site member with no role is refused with 'Access Denied…'."""
    ctx = new_context(browser, viewport=DESKTOP, use_auth_state=False)
    try:
        d = MCHeroAdminPage(ctx.new_page())
        try:
            outcome = d.login_as_role(ROLE_MEMBER)
        except RuntimeError as exc:
            pytest.skip(f"BLOCKED: no site-member (qc.member.test) credentials in .env — {exc}")
        if outcome != "ok":
            pytest.fail(f"login as site member: {outcome}")
        facts = {"user": d.signed_in_user()}
        for slug in ("media-center-hero", "media-center-count-widget"):
            d.slug = slug
            d.open(d._manage_url(locale="en"))
            d.page.wait_for_load_state("load")
            body = d.body_text()
            facts[slug] = {"url": d.page.url, "has_form": d.has_hero_form() if slug == "media-center-hero"
                           else d.page.locator('[name^="ObjectField_"]').count() > 0,
                           "access_denied_shown": MSG_ACCESS_DENIED in body, "body_head": body[:300],
                           "shot": d.evidence(f"149335_{slug}")}
        attach(facts, "149335 facts")
        for slug in ("media-center-hero", "media-center-count-widget"):
            assert not facts[slug]["has_form"], f"site member sees the {slug} form"
        for slug in ("media-center-hero", "media-center-count-widget"):
            assert facts[slug]["access_denied_shown"], \
                f"{slug}: refusal is not 'Access Denied…'; page shows {facts[slug]['body_head'][:160]!r}"
    finally:
        ctx.close()
