"""
cms/tests/made_in_china_expo/test_made_in_china_expo_control_panel.py —
Control_Panel-tagged cases for PBI 130953 ("QC - Events - 006 - Made in
China Expo"), sourced from `.claude/qa-baselines/130953_automation_batch.json`
(113 cases, pre-filtered to `Tag=Automation`).

Holds every case whose `tags` include `Control_Panel` (78 Control_Panel-only
cases) PLUS the Control_Panel-side test for every case that carries BOTH
`Web` and `Control_Panel` (12 cases: 144243, 144244, 144257, 144258, 144288,
144289, 144290, 144306, 144307, 144332, 144333, 144341) — the Web-side test
for those 12 lives in web/tests/made_in_china_expo/
test_made_in_china_expo_web.py under the SAME `tc_<id>` marker.

THIS PBI'S SHAPE — CONFIRMED LIVE 2026-09-22 (authenticated `.auth/
state.json` session, no MCP): unlike the four Insights & Media PBIs
automated earlier this session (single page-level singleton object each),
Made in China Expo is backed by **three separate singleton objects**, each
with its own dedicated Object Authoring page (a real `manage-<slug>`
surface confirmed live for all three, NOT the retired raw Content & Data
grid):

  - Hero        — slug `made-in-china-expo-hero`,
                  entry `QCDEMO-130953-MIC-hero` (see
                  cms/pages/made_in_china_expo/made_in_china_expo_hero_admin_page.py)
  - About Section — slug `made-in-china-expo-about-section`,
                  entry `QCDEMO-130953-MIC-about` (see
                  made_in_china_expo_about_admin_page.py)
  - Side CTA Card — slug `explore-made-in-china-cta-card`,
                  entry `QCDEMO-130953-MIC-cta` (see
                  explore_made_in_china_cta_admin_page.py)

Every one of the three is a genuine singleton ("1 total" in its own entries
list, Status PUBLISHED) — the SAME class of shared, always-live content as
this project's Annual Reports Page / Export Report Page. Per this project's
destructive-ops rule, none of the three Page Objects exposes a
fill_*/save_*/unpublish_* method — every test below either (a) READS an
already-saved value from the live singleton and cross-checks it against the
live public Web page (a genuine, non-invented verification), or (b) is
SKIPPED with that reasoning when the case can only be satisfied by an
actual write. This mirrors cms/tests/annual_reports/
test_annual_reports_control_panel.py's / cms/tests/export_reports/
test_export_reports_control_panel.py's identical page-singleton pattern.

CONFIRMED LIVE PRODUCT DEFECT (shared with the Web module — not repeated
in full here): both the Hero CTA and the Side CTA Card's own rendered
anchor resolve to `https://www.qatarchamber.com/`, not
`https://www.madeinchinaexpo.com`. The CMS-side "Redirect URL saved and
renders" read-verify tests below (tc_144281/144327) assert internal
consistency (the SAVED CMS value matches the PUBLIC rendered href) — which
holds — they do not re-assert the case's assumed literal madeinchinaexpo.com
value, since these two cases' own wording is about the save-and-render
mechanism, not the specific host (that assertion lives in the Web module's
tc_144259/144260/144250, which DO fail honestly on it).

CONFIRMED LIVE, DISCLOSED SCHEMA MISMATCH (tc_144304/144305/144306/144307):
the batch describes a repeatable "Supporting Images" sub-collection with a
PER-IMAGE Display Order/Active Status. The real, live About Section object
exposes exactly ONE "Supporting Image" file field and exactly ONE
section-level Display Order + Active Status pair (see
made_in_china_expo_about_admin_page.py's own docstring) — no such
repeatable list exists on this object at all. SKIPPED as a genuine
case/schema mismatch, not a locator gap.

ESTABLISHED FINDING CARRIED FROM SIBLING PBIs THIS SESSION: the
`CMS_SITE_CONTENT_AUTHOR_EMAIL`/`PASSWORD` credentials are confirmed NOT to
authenticate against this qcdev instance (see e.g.
cms/tests/export_reports/test_export_reports_control_panel.py's
tc_143858/143859 skips, and this project's own memory note). tc_144239/
144240 (Site Content Author role cases) are SKIPPED with that established
reasoning, not re-probed from scratch this batch.

NO ESTABLISHED CMS-UI-LOCALE-SWITCH MECHANISM (tc_144237): unlike
`switch_field_to_arabic()` (which flips ONE bilingual field's own EN/AR
half on an otherwise English-labeled form — an already-established,
different mechanism used project-wide), no prior PBI on this project has
established how to switch the Control Panel's OWN chrome/labels into
Arabic. Not independently discovered this batch — SKIPPED rather than
guessed at.
"""

import allure
import pytest

from cms.pages.made_in_china_expo.made_in_china_expo_hero_admin_page import (
    MadeInChinaExpoHeroAdminPage,
    FIELD_EYEBROW_EN as HERO_EYEBROW_EN,
    FIELD_PAGE_TITLE_EN as HERO_PAGE_TITLE_EN,
    FIELD_HERO_DESCRIPTION_EN,
    FIELD_HERO_BANNER,
    FIELD_HERO_BANNER_ALT_EN,
    FIELD_BUTTON_LABEL_EN as HERO_BUTTON_LABEL_EN,
    FIELD_REDIRECT_URL as HERO_REDIRECT_URL,
    FIELD_STATUS,
    FIELD_DISPLAY_ORDER,
)
from cms.pages.made_in_china_expo.made_in_china_expo_about_admin_page import (
    MadeInChinaExpoAboutAdminPage,
    FIELD_SECTION_EYEBROW_EN,
    FIELD_SECTION_TITLE_EN,
    FIELD_SECTION_BODY_EN,
)
from cms.pages.made_in_china_expo.explore_made_in_china_cta_admin_page import (
    ExploreMadeInChinaCtaAdminPage,
    FIELD_LOGO,
    FIELD_LOGO_ALT_EN,
    FIELD_EYEBROW_EN as CTA_EYEBROW_EN,
    FIELD_HEADING_EN as CTA_HEADING_EN,
    FIELD_SUBTEXT_EN,
    FIELD_BUTTON_LABEL_EN as CTA_BUTTON_LABEL_EN,
    FIELD_REDIRECT_URL as CTA_REDIRECT_URL,
    FIELD_OPEN_BEHAVIOR as CTA_OPEN_BEHAVIOR,
)
from web.pages.made_in_china_expo.made_in_china_expo_page import MadeInChinaExpoPage
from config.settings import control_panel_url


_SINGLETON_WRITE_SKIP = (
    "Requires an authoring WRITE against the real, live-published Made in "
    "China Expo singleton object(s) — not authorized without explicit "
    "ID-based confirmation, per this project's destructive-ops rule. "
    "Mirrors the Annual Reports Page / Export Report Page precedent."
)
_SCHEMA_MISMATCH_REASON = (
    "SCHEMA MISMATCH, DISCLOSED: the real, live About Section object "
    "exposes ONE section-level Supporting Image / Display Order / Active "
    "Status field, not a repeatable per-image sub-collection this case "
    "assumes — see made_in_china_expo_about_admin_page.py's own docstring. "
    "Unreachable by construction, not a locator gap."
)
_AUTHOR_CREDS_SKIP = (
    "CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD confirmed not to authenticate "
    "against qcdev (established on sibling PBIs this session, e.g. "
    "cms/tests/export_reports/test_export_reports_control_panel.py's "
    "tc_143858/143859)."
)


def _make_singleton_skip(tc_id: int, title: str, severity, category_marker, feature: str, reason: str, *extra_markers):
    def _decorator(func):
        func = pytest.mark.skip(reason=reason)(func)
        for m in extra_markers:
            func = m(func)
        func = category_marker(func)
        func = pytest.mark.expo(func)
        func = pytest.mark.control_panel(func)
        func = pytest.mark.pbi_130953(func)
        func = getattr(pytest.mark, f"tc_{tc_id}")(func)
        func = allure.title(title)(func)
        func = allure.severity(severity)(func)
        func = allure.story("Field validation")(func)
        func = allure.feature(feature)(func)
        func = allure.epic("Events")(func)
        return func
    return _decorator


HERO_FEATURE = "Made in China Expo — Hero (Control Panel)"
ABOUT_FEATURE = "Made in China Expo — About Section (Control Panel)"
CTA_FEATURE = "Made in China Expo — Side CTA Card (Control Panel)"


# ===========================================================================
# Auth / RBAC
# ===========================================================================
@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Admin form renders correctly in Arabic with RTL layout")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.bilingual
@pytest.mark.compatibility
@pytest.mark.pbi_130953
@pytest.mark.tc_144237
@pytest.mark.skip(
    reason="No established CMS-UI-locale-switch mechanism on this project "
    "(distinct from switch_field_to_arabic(), which flips one bilingual "
    "field's own EN/AR half, not the CP chrome's own display language) — "
    "not independently discovered this batch; not guessed at."
)
def test_admin_form_arabic_rtl(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Editor can perform the full content lifecycle")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144238
@pytest.mark.skip(reason=_SINGLETON_WRITE_SKIP)
def test_editor_full_content_lifecycle(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Author can view and update assigned page content")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.auth
@pytest.mark.pbi_130953
@pytest.mark.tc_144239
@pytest.mark.skip(reason=_AUTHOR_CREDS_SKIP)
def test_author_can_view_update_assigned_content(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Author is denied direct publish")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144240
@pytest.mark.skip(reason=_AUTHOR_CREDS_SKIP)
def test_author_denied_direct_publish(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Public Visitor is denied access to the Control Panel admin URL")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144242
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_public_visitor_denied_admin_url_access(page):
    # Azure TC 144242 | PBI 130953
    page.goto(control_panel_url("/web/qatar-chamber/manage-made-in-china-expo-hero"))
    page.wait_for_timeout(1500)

    body = page.locator("body").inner_text()

    # Assert: the admin form never renders for an unauthenticated request
    assert "login" in page.url.lower() or "Sign In" in body or "Manage: Made in China Expo Hero" not in body


# ===========================================================================
# Functional-High — lifecycle / propagation (all require a live-singleton write)
# ===========================================================================
@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Editor can configure all fields (EN/AR), preview, and publish successfully")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144243
@pytest.mark.skip(reason=_SINGLETON_WRITE_SKIP)
def test_editor_configures_all_fields_preview_publish_cms(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Editing an already-published Hero Title propagates to the public Web delivery surface")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.pbi_130953
@pytest.mark.tc_144244
@pytest.mark.skip(reason=_SINGLETON_WRITE_SKIP)
def test_hero_title_edit_propagates_cms(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Toast / audit log")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Saving a change displays the Liferay generic success toast and records an audit log entry (English)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.pbi_130953
@pytest.mark.tc_144247
@pytest.mark.skip(reason=_SINGLETON_WRITE_SKIP)
def test_save_shows_toast_and_audit_log_en(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Toast / audit log")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Saving a change displays the Liferay generic success toast and records an audit log entry (Arabic)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.bilingual
@pytest.mark.functional_high
@pytest.mark.pbi_130953
@pytest.mark.tc_144248
@pytest.mark.skip(reason=_SINGLETON_WRITE_SKIP + " Also needs the (unestablished) CMS UI locale switch — see tc_144237.")
def test_save_shows_toast_and_audit_log_ar(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Editor can save the page as Draft")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.pbi_130953
@pytest.mark.tc_144255
@pytest.mark.skip(
    reason=_SINGLETON_WRITE_SKIP + " Additionally requires taking the "
    "real, live-published Hero singleton offline (Draft) — a real, "
    "temporary takedown of the live public page."
)
def test_editor_saves_as_draft(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A Site Content Editor can preview the Draft page before publishing")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.pbi_130953
@pytest.mark.tc_144256
@pytest.mark.skip(reason="Depends on tc_144255's Draft precondition — same skip reasoning.")
def test_editor_previews_draft(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Editor can publish the page")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144257
@pytest.mark.skip(reason=_SINGLETON_WRITE_SKIP)
def test_editor_can_publish_page_cms(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Control Panel")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Editor can unpublish a previously published page")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144258
@pytest.mark.skip(reason=_SINGLETON_WRITE_SKIP)
def test_editor_can_unpublish_page_cms(page):
    ...


# ===========================================================================
# Hero field validation — read-only verify where possible, SKIP where a
# write is unavoidable (mirrors annual_reports_page_admin_page.py /
# export_reports_page_admin_page.py's identical page-singleton pattern)
# ===========================================================================
@allure.epic("Events")
@allure.feature(HERO_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Hero Eyebrow Label saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144262
def test_hero_eyebrow_valid_value_saved(page):
    # Azure TC 144262 | PBI 130953 — read-only: compares the ALREADY-
    # published singleton value to the live public page.
    admin = MadeInChinaExpoHeroAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(HERO_EYEBROW_EN)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value == "Qatari industry. Local ambition."
    assert mic.hero_eyebrow_text() == cms_value


@_make_singleton_skip(144263, "The Hero Eyebrow Label is rejected when left empty",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_eyebrow_empty_rejected(page):
    ...


@_make_singleton_skip(144264, "The Hero Eyebrow Label rejects a value exceeding 60 characters",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_eyebrow_exceeds_60_rejected(page):
    ...


@_make_singleton_skip(144265, "The Hero Eyebrow Label rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_eyebrow_whitespace_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(HERO_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Hero Page Title saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144266
def test_hero_page_title_valid_value_saved(page):
    # Azure TC 144266 | PBI 130953 — read-only.
    admin = MadeInChinaExpoHeroAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(HERO_PAGE_TITLE_EN)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value == "Made in China Expo"
    assert mic.hero_title_text() == cms_value


@_make_singleton_skip(144267, "The Hero Page Title is rejected when left empty",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_page_title_empty_rejected(page):
    ...


@_make_singleton_skip(144268, "The Hero Page Title rejects a value exceeding 120 characters",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_page_title_exceeds_120_rejected(page):
    ...


@_make_singleton_skip(144269, "The Hero Page Title rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_page_title_whitespace_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(HERO_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Hero Description saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144270
def test_hero_description_valid_value_saved(page):
    # Azure TC 144270 | PBI 130953 — read-only. Hero Description is a
    # rich-text CKEditor field (confirmed live) -- read via
    # hero_description_text(), not field_value() (see that method's own
    # docstring for why field_value() times out against it).
    admin = MadeInChinaExpoHeroAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.hero_description_text()

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value
    assert mic.hero_desc_text()


@_make_singleton_skip(144271, "The Hero Description is rejected when left empty",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_description_empty_rejected(page):
    ...


@_make_singleton_skip(144272, "The Hero Description rejects a value exceeding 200 characters",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_description_exceeds_200_rejected(page):
    ...


@_make_singleton_skip(144273, "The Hero Description rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_description_whitespace_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(HERO_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Hero Banner Image uploads and renders with alt text (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144274
def test_hero_banner_valid_uploads_and_displays(page):
    # Azure TC 144274 | PBI 130953 — read-only. CONFIRMED LIVE 2026-09-22:
    # `uploaded_filename(FIELD_HERO_BANNER)` reads back empty
    # (`data-placeholder="No file selected.", value=""`) even though a real
    # file IS attached and rendering live — the public page's own <img>
    # resolves to a real asset (`/documents/.../hero-banner.png`), confirmed
    # via a direct HTML dump. This field's own "Select File" readout widget
    # does not reflect this particular file's attached state the way
    # ObjectAuthoringPage.uploaded_filename() expects on every other object
    # on this project — a real, disclosed rendering quirk of THIS field,
    # not a missing image. Verified instead via the alt-text match plus the
    # public page's own image actually being visible.
    admin = MadeInChinaExpoHeroAdminPage(page)
    admin.open_singleton_for_read()
    alt_cms = admin.field_value(FIELD_HERO_BANNER_ALT_EN)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert alt_cms
    assert mic.hero_image_alt() == alt_cms
    assert mic.get_attribute(mic.HERO_IMG, "src")


@_make_singleton_skip(144275, "The Hero Banner Image rejects an unsupported file format",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_banner_unsupported_format_rejected(page):
    ...


@_make_singleton_skip(144276, "The Hero Banner Image rejects a file exceeding 2 MB",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_banner_oversized_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(HERO_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Hero CTA Button Label saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144277
def test_hero_cta_button_label_valid_saved(page):
    # Azure TC 144277 | PBI 130953 — read-only.
    admin = MadeInChinaExpoHeroAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(HERO_BUTTON_LABEL_EN)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value == "Visit the Official Expo Website"
    assert mic.hero_cta_label() == cms_value


@_make_singleton_skip(144278, "The Hero CTA Button Label is rejected when left empty while the Redirect URL is configured",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_cta_label_empty_rejected(page):
    ...


@_make_singleton_skip(144279, "The Hero CTA Button Label rejects a value exceeding 60 characters",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_cta_label_exceeds_60_rejected(page):
    ...


@_make_singleton_skip(144280, "The Hero CTA Button Label rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_cta_label_whitespace_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(HERO_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Hero CTA Redirect URL saves and renders as the CTA href (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144281
def test_hero_cta_redirect_url_valid_saved(page):
    # Azure TC 144281 | PBI 130953 — read-only: asserts internal consistency
    # (saved CMS value == public rendered href). Does NOT assert the case's
    # assumed madeinchinaexpo.com literal — that assertion lives in the Web
    # module's tc_144259/144250, which fail honestly on the confirmed-live
    # wrong-target defect (see module docstring).
    admin = MadeInChinaExpoHeroAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(HERO_REDIRECT_URL)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value
    assert mic.hero_cta_href() == cms_value


@_make_singleton_skip(144282, "The Hero CTA Redirect URL rejects an invalid/malformed URL and blocks publishing",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_cta_url_invalid_rejected(page):
    ...


@_make_singleton_skip(144283, "The Hero CTA Redirect URL rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_cta_url_whitespace_rejected(page):
    ...


@_make_singleton_skip(144284, 'The Hero CTA Open Behavior dropdown accepts a valid selection ("Same Tab")',
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP + ' The CURRENTLY-live value is "New Tab", not "Same Tab".')
def test_hero_open_behavior_same_tab(page):
    ...


@_make_singleton_skip(144285, "Publish is blocked when the Hero CTA label and URL are configured but Open Behavior is left unselected",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_open_behavior_unselected_blocks_publish(page):
    ...


@allure.epic("Events")
@allure.feature(HERO_FEATURE)
@allure.story("Page status")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Status can be set to Published via the dropdown (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144286
def test_page_status_published_via_dropdown(page):
    # Azure TC 144286 | PBI 130953 — read-only: the singleton's Status
    # field ALREADY reads "Published" live.
    admin = MadeInChinaExpoHeroAdminPage(page)
    admin.open_singleton_for_read()

    status_value = admin.combobox_value(FIELD_STATUS)

    assert status_value == "Published"
    assert admin.row_status_text().upper().startswith("PUBLISHED")


@_make_singleton_skip(144287, "Page Status cannot be left unselected",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_page_status_cannot_be_unselected(page):
    ...


@_make_singleton_skip(144288, "Turning Page Active Status ON makes the page appear in the Events menu",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_active_status_on_shows_in_menu_cms(page):
    ...


@_make_singleton_skip(144289, "Turning Page Active Status OFF removes the page from the Events menu",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_active_status_off_hides_from_menu_cms(page):
    ...


@allure.epic("Events")
@allure.feature(HERO_FEATURE)
@allure.story("Menu ordering")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Page Display Order accepts a valid positive integer (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144290
def test_display_order_valid_positive_integer(page):
    # Azure TC 144290 | PBI 130953 — read-only: reads the ALREADY-saved
    # Display Order value and confirms it parses as a non-negative integer;
    # does not assert an exact live menu position (see the Web module's
    # own tc_144290 skip for that half).
    admin = MadeInChinaExpoHeroAdminPage(page)
    admin.open_singleton_for_read()

    raw_value = admin.display_order_value()

    assert raw_value.strip() != ""
    assert int(raw_value) >= 0


@_make_singleton_skip(144291, "Page Display Order rejects a non-numeric value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_display_order_rejects_non_numeric(page):
    ...


# ===========================================================================
# About Section field validation
# ===========================================================================
@allure.epic("Events")
@allure.feature(ABOUT_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Section Eyebrow saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144292
def test_section_eyebrow_valid_value_saved(page):
    # Azure TC 144292 | PBI 130953 — read-only.
    admin = MadeInChinaExpoAboutAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(FIELD_SECTION_EYEBROW_EN)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value == "About the exhibition"
    assert mic.about_eyebrow_text() == cms_value


@_make_singleton_skip(144293, "The Section Eyebrow is rejected when left empty",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_section_eyebrow_empty_rejected(page):
    ...


@_make_singleton_skip(144294, "The Section Eyebrow rejects a value exceeding 100 characters",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_section_eyebrow_exceeds_100_rejected(page):
    ...


@_make_singleton_skip(144295, "The Section Eyebrow rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_section_eyebrow_whitespace_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(ABOUT_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Section Title saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144296
def test_section_title_valid_value_saved(page):
    # Azure TC 144296 | PBI 130953 — read-only.
    admin = MadeInChinaExpoAboutAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(FIELD_SECTION_TITLE_EN)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value == "Connecting markets and business opportunities"
    assert mic.about_title_text() == cms_value


@_make_singleton_skip(144297, "The Section Title is rejected when left empty",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_section_title_empty_rejected(page):
    ...


@_make_singleton_skip(144298, "The Section Title rejects a value exceeding 120 characters",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_section_title_exceeds_120_rejected(page):
    ...


@_make_singleton_skip(144299, "The Section Title rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_section_title_whitespace_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(ABOUT_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Section Body saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144300
def test_section_body_valid_value_saved(page):
    # Azure TC 144300 | PBI 130953 — read-only. Section Body is a rich-text
    # CKEditor field -- read via section_body_text(), not field_value().
    admin = MadeInChinaExpoAboutAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.section_body_text()

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value
    assert mic.about_body_text()


@_make_singleton_skip(144301, "The Section Body is rejected when left empty",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_section_body_empty_rejected(page):
    ...


@_make_singleton_skip(144302, "The Section Body rejects a value exceeding 10000 characters",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_section_body_exceeds_10000_rejected(page):
    ...


@_make_singleton_skip(144303, "The Section Body rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_section_body_whitespace_rejected(page):
    ...


@_make_singleton_skip(144304, "A Supporting Image's Display Order accepts a valid positive integer",
                       allure.severity_level.MINOR, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SCHEMA_MISMATCH_REASON)
def test_supporting_image_display_order_valid(page):
    ...


@_make_singleton_skip(144305, "A Supporting Image's Display Order rejects a negative value",
                       allure.severity_level.MINOR, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SCHEMA_MISMATCH_REASON)
def test_supporting_image_display_order_negative_rejected(page):
    ...


@_make_singleton_skip(144306, "Turning a Supporting Image's Active Status ON shows it on the delivery surface",
                       allure.severity_level.MINOR, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SCHEMA_MISMATCH_REASON)
def test_supporting_image_active_status_on_cms(page):
    ...


@_make_singleton_skip(144307, "Turning a Supporting Image's Active Status OFF hides it from the delivery surface",
                       allure.severity_level.MINOR, pytest.mark.functional_low, ABOUT_FEATURE,
                       _SCHEMA_MISMATCH_REASON)
def test_supporting_image_active_status_off_cms(page):
    ...


# ===========================================================================
# Side CTA Card field validation
# ===========================================================================
@allure.epic("Events")
@allure.feature(CTA_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid CTA Card Logo uploads and renders with alt text (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144308
def test_cta_logo_valid_uploads_and_displays(page):
    # Azure TC 144308 | PBI 130953 — read-only. Same confirmed-live
    # uploaded_filename() readout quirk as tc_144274 (see that test's own
    # comment) — verified via alt-text match plus the public image actually
    # rendering, not the upload-widget's own (unreliable, on this field)
    # filename readout.
    admin = ExploreMadeInChinaCtaAdminPage(page)
    admin.open_singleton_for_read()
    alt_cms = admin.field_value(FIELD_LOGO_ALT_EN)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert alt_cms
    assert mic.card_logo_alt() == alt_cms
    assert mic.get_attribute(mic.CARD_LOGO, "src")


@_make_singleton_skip(144309, "The CTA Card Logo rejects an unsupported file format",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_logo_unsupported_format_rejected(page):
    ...


@_make_singleton_skip(144310, "The CTA Card Logo rejects a file exceeding 2 MB",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_logo_oversized_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(CTA_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The CTA Card Eyebrow saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144311
def test_cta_eyebrow_valid_value_saved(page):
    # Azure TC 144311 | PBI 130953 — read-only.
    admin = ExploreMadeInChinaCtaAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(CTA_EYEBROW_EN)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value == "Official exhibition website"
    assert mic.card_eyebrow_text() == cms_value


@_make_singleton_skip(144312, "The CTA Card Eyebrow is rejected when left empty",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_eyebrow_empty_rejected(page):
    ...


@_make_singleton_skip(144313, "The CTA Card Eyebrow rejects a value exceeding 100 characters",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_eyebrow_exceeds_100_rejected(page):
    ...


@_make_singleton_skip(144314, "The CTA Card Eyebrow rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_eyebrow_whitespace_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(CTA_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The CTA Card Heading saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144315
def test_cta_heading_valid_value_saved(page):
    # Azure TC 144315 | PBI 130953 — read-only.
    admin = ExploreMadeInChinaCtaAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(CTA_HEADING_EN)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value == "Explore Made in China"
    assert mic.card_heading_text() == cms_value


@_make_singleton_skip(144316, "The CTA Card Heading is rejected when left empty",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_heading_empty_rejected(page):
    ...


@_make_singleton_skip(144317, "The CTA Card Heading rejects a value exceeding 120 characters",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_heading_exceeds_120_rejected(page):
    ...


@_make_singleton_skip(144318, "The CTA Card Heading rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_heading_whitespace_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(CTA_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The CTA Card Subtext saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144319
def test_cta_subtext_valid_value_saved(page):
    # Azure TC 144319 | PBI 130953 — read-only. Subtext is a rich-text
    # CKEditor field -- read via subtext_text(), not field_value().
    admin = ExploreMadeInChinaCtaAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.subtext_text()

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value
    assert mic.card_subtext_text()


@_make_singleton_skip(144320, "The CTA Card Subtext is rejected when left empty",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_subtext_empty_rejected(page):
    ...


@_make_singleton_skip(144321, "The CTA Card Subtext rejects a value exceeding 200 characters",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_subtext_exceeds_200_rejected(page):
    ...


@_make_singleton_skip(144322, "The CTA Card Subtext rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_subtext_whitespace_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(CTA_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The CTA Card Button Label saves with a valid value (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144323
def test_cta_button_label_valid_saved(page):
    # Azure TC 144323 | PBI 130953 — read-only.
    admin = ExploreMadeInChinaCtaAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(CTA_BUTTON_LABEL_EN)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value == "Visit the Official Expo Website"
    assert mic.card_cta_label() == cms_value


@_make_singleton_skip(144324, "The CTA Card Button Label is rejected when left empty while the Redirect URL is configured",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_button_label_empty_rejected(page):
    ...


@_make_singleton_skip(144325, "The CTA Card Button Label rejects a value exceeding 60 characters",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_button_label_exceeds_60_rejected(page):
    ...


@_make_singleton_skip(144326, "The CTA Card Button Label rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_button_label_whitespace_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(CTA_FEATURE)
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The CTA Card Redirect URL saves and renders as the CTA href (read-only verify)")
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144327
def test_cta_redirect_url_valid_saved(page):
    # Azure TC 144327 | PBI 130953 — read-only, internal-consistency check
    # only (see tc_144281's own comment for why this doesn't re-assert the
    # host itself).
    admin = ExploreMadeInChinaCtaAdminPage(page)
    admin.open_singleton_for_read()
    cms_value = admin.field_value(CTA_REDIRECT_URL)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert cms_value
    assert mic.card_cta_href() == cms_value


@_make_singleton_skip(144328, "The CTA Card Redirect URL rejects an invalid/malformed URL and blocks publishing",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_redirect_url_invalid_rejected(page):
    ...


@_make_singleton_skip(144329, "The CTA Card Redirect URL rejects a whitespace-only value",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_redirect_url_whitespace_rejected(page):
    ...


@allure.epic("Events")
@allure.feature(CTA_FEATURE)
@allure.story("Open Behavior")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The CTA Card Open Behavior dropdown accepts a valid selection ("New Tab") (read-only verify)')
@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144330
def test_cta_open_behavior_new_tab(page):
    # Azure TC 144330 | PBI 130953 — read-only: the CURRENTLY-live value
    # already is "New Tab" (confirmed via the rendered anchor's own
    # target="_blank"), so this needs no write.
    admin = ExploreMadeInChinaCtaAdminPage(page)
    admin.open_singleton_for_read()
    value = admin.combobox_value(CTA_OPEN_BEHAVIOR)

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert value == "New Tab"
    assert mic.card_cta_target() == "_blank"


@_make_singleton_skip(144331, "Publish is blocked when the CTA Card Open Behavior is left unselected",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_open_behavior_unselected_blocks_publish(page):
    ...


@_make_singleton_skip(144332, "Turning the CTA Card Active Status ON shows the card on the delivery surface",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_card_active_status_on_cms(page):
    ...


@_make_singleton_skip(144333, "Turning the CTA Card Active Status OFF hides the card from the delivery surface",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, CTA_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_cta_card_active_status_off_cms(page):
    ...


# ===========================================================================
# Bilingual CMS-locale validation-message wording (all require a write, and
# tc_144337 additionally requires the broken Author role)
# ===========================================================================
@_make_singleton_skip(144334, "Required-field validation message displays in Arabic when the CMS locale is Arabic",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, "Made in China Expo — Control Panel",
                       _SINGLETON_WRITE_SKIP + " Also needs the (unestablished) CMS UI locale switch — see tc_144237.",
                       pytest.mark.bilingual)
def test_required_field_message_arabic(page):
    ...


@_make_singleton_skip(144335, "Invalid-URL validation message displays in Arabic when the CMS locale is Arabic",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, "Made in China Expo — Control Panel",
                       _SINGLETON_WRITE_SKIP + " Also needs the (unestablished) CMS UI locale switch — see tc_144237.",
                       pytest.mark.bilingual)
def test_invalid_url_message_arabic(page):
    ...


@_make_singleton_skip(144336, "Image-size validation message displays in Arabic when the CMS locale is Arabic",
                       allure.severity_level.NORMAL, pytest.mark.functional_low, "Made in China Expo — Control Panel",
                       _SINGLETON_WRITE_SKIP + " Also needs the (unestablished) CMS UI locale switch — see tc_144237.",
                       pytest.mark.bilingual)
def test_image_size_message_arabic(page):
    ...


@_make_singleton_skip(144337, "Access-denied message displays in Arabic when the CMS locale is Arabic",
                       allure.severity_level.CRITICAL, pytest.mark.functional_low, "Made in China Expo — Control Panel",
                       _AUTHOR_CREDS_SKIP + " Also needs the (unestablished) CMS UI locale switch — see tc_144237.",
                       pytest.mark.bilingual, pytest.mark.auth)
def test_access_denied_message_arabic(page):
    ...


# ===========================================================================
# Edge — Hero Banner replacement (requires a write to the live singleton)
# ===========================================================================
@_make_singleton_skip(144341, "Replacing the Hero Banner Image on an already-published page propagates with no broken image reference",
                       allure.severity_level.NORMAL, pytest.mark.edge, HERO_FEATURE,
                       _SINGLETON_WRITE_SKIP)
def test_hero_banner_replacement_propagates_cms(page):
    ...
