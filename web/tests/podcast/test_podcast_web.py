"""
web/tests/podcast/test_podcast_web.py — Web-tagged cases for PBI 130713
("QC - Insights & Media - 005 - Podcast"), sourced verbatim from the 59
approved, already-injected Azure Test Cases handed to this batch
(TC 143521-143823, Web platform only — Control_Panel/CMS-tagged cases for
this PBI were deliberately excluded from this batch per explicit user
instruction and are not touched here).

Live page confirmed 2026-09-21: https://qcdev.ihorizons.com/web/qatar-chamber/podcast
(AR: /ar/web/qatar-chamber/podcast). See podcast_page.py's module docstring
for the full DOM extraction log this batch is built from.

Live data set confirmed 2026-09-21 (qcdev, 5 published episodes total,
newest-first order — the environment already renders in this order with NO
seeding needed):
    Episode 24 "Qatar Chamber Podcast" — May 10, 2026, 42 MIN, 19 plays,
        HAS AI Highlights (2 points)
    Episode 23 "Financing Growth: SME Access to Capital" — May 3, 2026,
        38 MIN, 8 plays, HAS AI Highlights (2 points — CONFIRMED LIVE
        IDENTICAL TEXT to Episode 24's own points, see below)
    Episode 21 "Trade Talks: Forum 2026 Special" — Apr 19, 2026, 42 MIN,
        3 plays, NO AI Highlights control
    Episode 20 "Digital Economy Roundtable" — Apr 12, 2026, 38 MIN,
        2 plays, NO AI Highlights control
    Episode 19 "Women in Business Leadership" — Apr 5, 2026, 45 MIN,
        1 plays, NO AI Highlights control
All 5 episodes are Option-A (uploaded file): every row renders a Download
link, none uses the Option-B embed slot (`.qc-ppl-embed` stays `hidden`
regardless of which episode is played) — CONFIRMED LIVE, not assumed.
All 5 episodes' real playable audio resolves to the SAME ~19-second
placeholder file, independent of the row's own stated "NN MIN" duration
badge.

*** REAL, CONFIRMED LIVE CANDIDATE BUG (flagged back, not filed) ***
TC 143593 ("AI Highlights popup shows only the selected episode's
highlights, not another episode's"): Episode 24's and Episode 23's popups
render the EXACT SAME two highlight strings verbatim (confirmed via two
separate live reads). test_ai_highlights_popup_shows_per_episode_highlights
below asserts real per-episode distinctness and is EXPECTED TO FAIL when
run — this is the correct, honest representation of an observed product
defect (automation-standards.md's Result-integrity section: a test that
catches a real defect must fail, never be weakened/skipped to stay green).
Per this project's own bug-filing convention ("confirm independently before
filing"), this is reported back to the QA Manager/user for triage, not
filed as a bug by this batch.

Data adaptations disclosed per test (also inline at the specific assertion):
  143596/143597 (subscribe success message) — the real live success message
    text ("You are subscribed! We will email you when a new episode is
    published." EN / "تم اشتراكك! سنرسل لك بريدًا إلكترونيًا عند نشر حلقة
    جديدة." AR) differs from each case's own literal wording; asserted
    against the REAL observed text, not narrowed to match the case's words.
  143599 (duplicate message) / 143679 (AR duplicate message) — the real
    live text ("This email address is already subscribed." / "هذا البريد
    الإلكتروني مشترك بالفعل") is used as the exact assertion — this one
    DOES match each case's own stated wording.
  143624 (newest-first order) — the case's own precondition asks to "seed 3
    published episodes with distinct dates"; this environment's real 5 live
    episodes are ALREADY published with distinct dates in descending order
    by default — verified against the real live order instead of seeding.
  143625 (Duration format) — only the front-end display half is verified
    ("NN MIN" on the row); the case's own second step (reopen the admin
    record, confirm HH:MM:SS precision is retained) needs Control_Panel
    access, out of scope for this Web-only batch — see its own inline note.
  143820/143823 (lowercase / trim on submit) — only front-end ACCEPTANCE is
    verified (the form submits successfully with no validation error for a
    mixed-case or padded address); confirming the value was actually stored
    lowercased/trimmed needs Control_Panel access to the subscriber record,
    out of scope for this Web-only batch — see each test's own inline note.

SKIPPED this batch (17 of 59), each carrying full traceability markers:
  143524 (zero published episodes site-wide) — destructive: would require
    unpublishing all 5 real, shared qcdev episodes, no confirmed teardown path.
  143525 (inactive platform button reflow) — requires a CMS write (set
    Spotify's own Active Status field to false), out of scope this batch.
  143529 (single-highlight-populated episode) — no live episode has exactly
    one of its two highlight fields populated (both live AI-enabled episodes
    carry both fields); no CMS write to author one.
  143531 (missing-translation fallback) — every live episode's AR title AND
    description are fully translated (confirmed live, both EN and AR reads);
    no CMS write to author a blank-AR/filled-EN episode.
  143542 (Public Visitor denied admin URL) — no Podcast Control_Panel/admin
    management URL is known or confirmed reachable this batch; three
    plausible `manage-<slug>` guesses all 404 to a generic "Coming Soon"
    fallback rather than a real admin surface or a login redirect — see
    podcast_page.py's module docstring.
  143560 (Download hidden for Option-B episode) — no Option-B/embed-only
    episode exists live; all 5 are Option-A with a Download link.
  143585 (Option-B embed playback) — same gap as 143560.
  143602 (reactivate a previously-Unsubscribed address) — reaching the
    Unsubscribed precondition requires clicking a real unsubscribe link
    delivered by email; no mailbox/API access is wired into this framework
    (checked conftest.py/existing fixtures — none exists).
  143606 (unsubscribe-link click sets Unsubscribed + sends confirmation) —
    same mailbox-access gap as 143602.
  143607 (unsubscribed address receives no further emails) — same gap.
  143609 (every Podcast email contains a working unsubscribe link) — same
    gap; there is no mailbox to inspect delivered emails from.
  143622 (badge excludes Drafts) — requires a CMS write (create a Draft
    episode), out of scope this batch.
  143623 (badge increments on publish) — requires a CMS write (publish a new
    episode), out of scope this batch.
  143626 (play-count abbreviation >1000, e.g. "12.4K plays") — no live
    episode's play count exceeds 20; no CMS write to set one to 12400.
  143627 (play-count boundary 1000/1001) — same gap as 143626.
  143628 (unpublished episode denied via direct file URL) — requires a CMS
    write (unpublish a known episode) with no confirmed teardown path.
  143633 (Featured episode shown on Home page) — requires a CMS write (set
    an episode's Featured flag), out of scope this batch.

2026-09-22 re-evaluation under the destructive-precondition rule
(standards.md): 10 of the 17 skips above (143525, 143529, 143542, 143560,
143585, 143622, 143623, 143626, 143627, 143628) were unblocked using ONE
disposable QCTEST Podcast Episode + ONE disposable QCTEST Podcast Platform
Link, both created via Object Authoring (never any of the 5 real, shared
QCDEMO episodes / 3 real platform links). See the QCTEST_EPISODE_* module
constants for the episode's erc/title. Its Status was cycled Draft ->
Published -> Unpublished, and its Play Count edited (12400 -> 1000) across
this batch's tests — see each test's own comment for the state it needs.
Both disposable records were torn down (deleted) at the end of this batch.

Two things worth flagging from this pass:
  - TC 143627: at Play Count exactly 1000 the live product abbreviates to
    "1K plays" — the case's original literal wording ("1000 does not
    abbreviate") did not hold; the real abbreviation boundary is >=1000,
    not >1000. QA Manager reviewed and confirmed (2026-09-22) this is the
    live product's real behaviour, not a bug — the test's own hardcoded
    expectation was corrected to assert the >=1000 boundary. VERIFIED
    GREEN 2026-09-22: re-authored a fresh disposable QCTEST record
    (QCTEST-143627-PlayCount-1000, erc 76f3962c-e66f-2c1c-4bbe-d21832b8de31,
    entryId 176461, Published, Play Count = 1000 exactly) via Object
    Authoring after the original combined-episode record (used by
    143529/143560/143585/143622/143623/143626 above) had already been torn
    down at the end of the batch that created it. Confirmed live on the
    public Podcast page: the card's meta line reads "1K plays". Ran solo
    (`pytest web/tests/podcast/test_podcast_web.py::
    test_podcast_play_count_boundary_1000_1001`) — PASSED. This new record
    was ALSO torn down (deleted) immediately after the run, per this
    project's standing disposable-test-data rule — see the updated
    QCTEST_EPISODE_TITLE/QCTEST_EPISODE_ERC constants below, which now
    describe THIS record and serve TC 143627 only. The other six tests
    above that share these same constants (143529, 143560, 143585, 143622,
    143623, 143626) need a record with a DIFFERENT state (Option-B-only-
    highlight-field / Draft / Unpublished cycling / Play Count 12400) that
    this Published, Play-Count-1000, both-fields-populated record does not
    provide — they are not re-verified by this pass and will need their
    own fresh disposable record re-authored before their next run.
  - 143531 (missing-AR-translation fallback) stays skipped for a NEW,
    corrected reason: 'Episode Title (AR)' and 'Description (AR)' are
    independently required fields on this object (confirmed via a real
    save attempt) — a blank-AR episode cannot be authored at all, a
    schema fact rather than a CMS-access gap.
  - 143524 (zero episodes site-wide) and 143633 (Featured on Home Page) are
    re-evaluated with corrected reasons — see their own skip blocks.
  - 143602/143606/143607/143609 (mailbox/email-delivery cases) are
    unrelated to the destructive-precondition rule and unchanged.

Caveat for re-running without fresh disposable data: 143525/143529/143560/
143585/143622/143626/143627/143628 assert against the disposable records'
specific state and will behave differently (or fail) once those records
are deleted — expected/honest on re-run without re-authoring, not a
regression.
"""

import re
import time
from datetime import datetime

import allure
import pytest

from web.pages.components.header_component import HeaderComponent
from web.pages.podcast.podcast_page import PodcastPage

# Real, live episode titles/badges confirmed 2026-09-21 (see module docstring).
TITLE_24 = "Qatar Chamber Podcast"
TITLE_23 = "Financing Growth: SME Access to Capital"
TITLE_21 = "Trade Talks: Forum 2026 Special"
TITLE_20 = "Digital Economy Roundtable"
TITLE_19 = "Women in Business Leadership"

# Disposable QCTEST Podcast Episode — RE-AUTHORED 2026-09-22 via Object
# Authoring for TC 143627 ONLY (the original combined-episode record these
# constants used to describe — Audio Source Type = External Embed Link,
# only AI Episode Highlight 1 populated, Status cycled Draft -> Published ->
# Unpublished across 143529/143560/143585/143622/143623/143626/143627 — was
# already torn down at the end of the batch that created it; see those
# tests' own comments and the module docstring's caveat). THIS record:
# Published, Audio Source Type = External Embed Link (Option B), Play Count
# = exactly 1000, entryId 176461. Confirmed live "1K plays" on the public
# Podcast page. Torn down (deleted) again immediately after TC 143627's
# solo re-verification run — never one of the 5 real, shared QCDEMO
# episodes. The other six tests sharing these constants (143529, 143560,
# 143585, 143622, 143623, 143626) need a record in a different state and
# are NOT re-verified by this record — see module docstring.
QCTEST_EPISODE_ERC = "76f3962c-e66f-2c1c-4bbe-d21832b8de31"
QCTEST_EPISODE_TITLE = "QCTEST-143627-PlayCount-1000"


def _unique_email(tag: str) -> str:
    """A synthetic, disposable test address — never a real person's inbox,
    and never destructive to any existing shared qcdev content (the real
    public subscription endpoint is the actual feature under test, same
    class of "genuine use of a public feature" as prior batches' newsletter
    forms). Timestamp-suffixed so every test run is independent/idempotent
    rather than colliding with a fixed literal address from a prior run."""
    return f"qa.podcast.{tag}.{int(time.time() * 1000)}@example.com"


# ---------------------------------------------------------------------------
# 143521 — Podcast page renders correctly in English (LTR)
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Bilingual / LTR")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Podcast page renders correctly in English (LTR)")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.pbi_130713
@pytest.mark.tc_143521
def test_podcast_page_renders_ltr_english(page):
    podcast = PodcastPage(page)

    with allure.step("Open the Podcast page (EN)"):
        podcast.open_podcast()

    dir_attr = page.evaluate("() => document.documentElement.getAttribute('dir')")

    # Assert: breadcrumb + hero LTR
    assert dir_attr == "ltr"
    assert podcast.is_breadcrumb_visible()
    assert podcast.breadcrumb_texts() == ["Home", "Insights & Media", "Podcast"]
    assert podcast.breadcrumb_current_text() == "Podcast"
    assert podcast.is_hero_visible()
    assert podcast.hero_title_text() == "Qatar Chamber Podcast"
    assert podcast.badge_texts() == ["5 Episodes", "Weekly"]
    assert podcast.is_host_visible()
    assert podcast.platform_labels() == [
        "Listen on Apple Music", "RSS Feed", "Listen on Spotify",
    ]

    with allure.step("Scroll to the episode list"):
        podcast.load_all_episodes()

    # Assert: episode rows render title/description/meta/Play/Download
    assert podcast.card_count() == 5
    assert podcast.is_download_visible(0)
    meta = podcast.card_meta_texts(0)
    assert any("2026" in m for m in meta)

    with allure.step("Scroll to the subscription band"):
        pass  # already in the DOM; no separate navigation needed

    # Assert: subscription band LTR
    assert podcast.is_subscribe_band_visible()
    assert podcast.subscribe_heading_text() == "Never miss a new episode"
    assert podcast.subscribe_placeholder() == "Enter your email"


# ---------------------------------------------------------------------------
# 143522 — Podcast page renders correctly in Arabic (RTL)
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Podcast page renders correctly in Arabic (RTL)")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.rtl
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143522
def test_podcast_page_renders_rtl_arabic(page):
    podcast = PodcastPage(page)

    with allure.step("Open the Podcast page (AR)"):
        podcast.open_podcast(locale="ar")

    dir_attr = page.evaluate("() => document.documentElement.getAttribute('dir')")

    # Assert: RTL hero
    assert dir_attr == "rtl"
    assert podcast.hero_title_text() == "بودكاست غرفة قطر"
    assert set(podcast.badge_texts()) == {"اسبوعية", "5 حلقة"}

    with allure.step("Episode rows"):
        podcast.load_all_episodes()

    assert podcast.card_count() == 5

    with allure.step("Subscription band"):
        pass

    # Assert: subscription band mirrors, Arabic copy renders
    assert podcast.is_subscribe_band_visible()
    assert podcast.subscribe_heading_text() == "لا تفوّت أي حلقة جديدة"
    assert podcast.subscribe_placeholder() == "ادخل البريد الالكتروني"


# ---------------------------------------------------------------------------
# 143524 — SKIPPED — "No episodes are currently available." on zero episodes
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Empty state")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('"No episodes are currently available." displays when zero episodes are published')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143524
@pytest.mark.skip(
    reason="Re-evaluated 2026-09-22 under the destructive-precondition rule: "
    "reaching a genuine zero-published-episodes state requires unpublishing "
    "all 5 REAL, shared QCDEMO episodes (a disposable QCTEST episode added "
    "alongside them would still leave the badge/grid non-empty). A "
    "reversible-in-principle mutation of real shared content, forbidden "
    "without its own explicit, ID-named user exception (same class as "
    "photo_albums' 143180 / video_library's 143075) — BLOCKED pending that "
    "exception, not attempted."
)
def test_podcast_empty_state_when_zero_episodes(page):
    ...


# ---------------------------------------------------------------------------
# 143525 — SKIPPED — inactive platform button hidden, remaining reflow
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Platform buttons")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An inactive platform follow button does not display and remaining buttons reflow")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143525
def test_podcast_inactive_platform_button_hidden(page):
    # Disposable QCTEST Podcast Platform Link (Active Status = false)
    # created via Object Authoring per the 2026-09-22 destructive-
    # precondition rule — never the real, shared Spotify/Apple Music/RSS
    # platform link records the case's own wording names.
    podcast = PodcastPage(page)
    podcast.open_podcast()

    labels = podcast.platform_labels()

    # Assert: the inactive platform never renders; the 3 real active ones
    # are unaffected (reflow intent — no gap/placeholder left behind)
    assert not any("QCTEST" in (label or "") for label in labels)
    assert len(labels) == 3


# ---------------------------------------------------------------------------
# 143526 — AI Highlights popup dismissed via close (X)
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("AI Highlights popup")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("AI Highlights popup can be dismissed via its close (X) action")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.pbi_130713
@pytest.mark.tc_143526
def test_ai_highlights_popup_close_via_x(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    index = podcast.card_index_by_title(TITLE_24)

    with allure.step("Start playback, then open a DIFFERENT episode's AI Highlights popup"):
        podcast.click_play(index)
        assert podcast.is_player_playing()
        other_index = podcast.card_index_by_title(TITLE_23)
        podcast.click_ai_highlights(other_index)

    with allure.step("Close the popup via its X"):
        podcast.close_popup_via_close_button()

    # Assert
    assert not podcast.is_popup_visible()
    assert podcast.is_player_visible()
    assert podcast.is_player_playing()


# ---------------------------------------------------------------------------
# 143527 — AI Highlights popup dismissed by clicking the overlay
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("AI Highlights popup")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("AI Highlights popup can be dismissed by clicking the dimmed overlay")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130713
@pytest.mark.tc_143527
def test_ai_highlights_popup_close_via_overlay(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    index = podcast.card_index_by_title(TITLE_24)

    with allure.step("Open the AI Highlights popup"):
        podcast.click_ai_highlights(index)

    with allure.step("Click outside the popup, on the dimmed overlay"):
        podcast.close_popup_via_overlay()

    # Assert
    assert not podcast.is_popup_visible()


# ---------------------------------------------------------------------------
# 143528 — AI Highlights popup dismissed via the Esc key
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("AI Highlights popup")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("AI Highlights popup can be dismissed via the Esc key")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130713
@pytest.mark.tc_143528
def test_ai_highlights_popup_close_via_escape(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    index = podcast.card_index_by_title(TITLE_24)

    with allure.step("Open the AI Highlights popup"):
        podcast.click_ai_highlights(index)

    with allure.step("Press Esc"):
        podcast.close_popup_via_escape()

    # Assert
    assert not podcast.is_popup_visible()


# ---------------------------------------------------------------------------
# 143529 — SKIPPED — one-highlight-field-only episode shows no placeholder
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("AI Highlights popup")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An episode with only one highlight field populated shows no empty placeholder")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143529
def test_ai_highlights_popup_single_populated_field_no_placeholder(page):
    # Disposable QCTEST episode (see module constants): AI Episode
    # Highlight 1 populated, Highlight 2 deliberately left blank — created
    # via Object Authoring per the 2026-09-22 destructive-precondition
    # rule, never one of the 5 real, shared QCDEMO episodes.
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.load_all_episodes()
    index = podcast.card_index_by_title(QCTEST_EPISODE_TITLE)

    with allure.step("Open the AI Highlights popup"):
        podcast.click_ai_highlights(index)

    # Assert: exactly one highlight shown, no empty placeholder for the
    # unpopulated second field
    highlights = podcast.popup_highlight_texts()
    assert len(highlights) == 1
    assert highlights[0]


# ---------------------------------------------------------------------------
# 143530 — AI Highlights action hidden when no highlights configured
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("AI Highlights popup")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("AI Highlights action is hidden when no highlights are configured for an episode")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.pbi_130713
@pytest.mark.tc_143530
def test_ai_highlights_hidden_when_unconfigured(page):
    # Episode 21 ("Trade Talks: Forum 2026 Special") has NO AI Highlights
    # button live (confirmed) — used as the real subject.
    podcast = PodcastPage(page)
    podcast.open_podcast()
    index = podcast.card_index_by_title(TITLE_21)

    # Assert: no AI Highlights control, other meta-line elements unaffected
    assert not podcast.is_ai_highlights_visible(index)
    meta = podcast.card_meta_texts(index)
    assert any("2026" in m for m in meta)  # date
    assert any("MIN" in m for m in meta)  # duration
    assert any("play" in m for m in meta)  # plays


# ---------------------------------------------------------------------------
# 143531 — SKIPPED — missing-translation content falls back to active language
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Bilingual fallback")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Missing-translation content falls back to the active language")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.pbi_130713
@pytest.mark.tc_143531
@pytest.mark.skip(
    reason="Re-evaluated 2026-09-22: confirmed live via a real Object "
    "Authoring save attempt that 'Episode Title (AR)' and 'Description "
    "(AR)' are separate, independently REQUIRED fields on the Podcast "
    "Episodes object (not a single translatable field with an optional "
    "AR locale, unlike Photo Albums/Video Records/Advertisement Rate "
    "Cards) — the form rejects submission with both AR fields blank. A "
    "genuinely blank-AR episode cannot be authored at all, disposable or "
    "otherwise — this is a schema fact, not a CMS-access gap."
)
def test_podcast_missing_translation_falls_back(page):
    ...


# ---------------------------------------------------------------------------
# 143532 — Desktop viewport (1920x1080)
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Responsive / Desktop")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Podcast page renders responsively on desktop viewport (1920x1080)")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143532
def test_podcast_desktop_viewport(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.click_play(podcast.card_index_by_title(TITLE_24))

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert: hero, episode rows, sticky player, subscription band all render
    assert podcast.is_hero_visible()
    assert podcast.card_count() >= 1
    assert podcast.is_player_visible()
    assert podcast.is_subscribe_band_visible()
    assert scroll_width <= client_width + 1


# ---------------------------------------------------------------------------
# 143533 — Tablet viewport (768x1024)
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Responsive / Tablet")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Podcast page renders responsively on tablet viewport (768x1024)")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.pbi_130713
@pytest.mark.tc_143533
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_podcast_tablet_viewport(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.click_play(podcast.card_index_by_title(TITLE_24))

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")
    player_box = page.locator(podcast.PLAYER).bounding_box()

    # Assert: readable list, no horizontal scroll, player docks full-width
    assert scroll_width <= client_width + 1
    assert player_box is not None
    assert player_box["width"] >= client_width - 4


# ---------------------------------------------------------------------------
# 143534 — Mobile viewport (375x812)
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Responsive / Mobile")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Podcast page renders responsively on mobile viewport (375x812)")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143534
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_podcast_mobile_viewport(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    index = podcast.card_index_by_title(TITLE_24)
    meta_before = podcast.card_meta_texts(index)
    podcast.click_play(index)

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert: hero stacks, meta line not truncated, controls tappable, no overflow
    assert scroll_width <= client_width + 1
    assert any("Episode" in m for m in meta_before)
    assert any("MIN" in m for m in meta_before)
    assert podcast.is_visible(podcast.PLAYER_PLAY)
    assert podcast.is_visible(podcast.PLAYER_FWD)
    assert podcast.is_visible(podcast.PLAYER_BACK)

    with allure.step("Subscription band stacks vertically"):
        sub_input_box = page.locator(podcast.SUB_INPUT).bounding_box()
        sub_btn_box = page.locator(podcast.SUB_SUBMIT).bounding_box()
    assert sub_input_box is not None and sub_btn_box is not None
    assert sub_btn_box["y"] >= sub_input_box["y"] + sub_input_box["height"] - 2


# ---------------------------------------------------------------------------
# 143542 — SKIPPED — Public Visitor denied direct access to the admin area
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Access control")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Public Visitor cannot access the Podcast Control Panel/admin area")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130713
@pytest.mark.tc_143542
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_podcast_public_visitor_denied_admin_access(page):
    # Re-evaluated 2026-09-22: the earlier "no known admin URL" reason no
    # longer holds — the real Object Authoring admin URL for Podcast
    # Episodes (objectDefinitionId=50342) was confirmed live this batch
    # while authoring disposable QCTEST episodes for the other unblocked
    # cases below. As a fresh, logged-out Public Visitor, this same URL
    # must NOT render the entries grid.
    podcast = PodcastPage(page)
    podcast.open_episodes_admin_as_visitor()

    # Assert: redirected away from the admin entries grid (no admin table
    # reachable while logged out)
    assert "login" in page.url.lower() or not podcast.is_admin_entries_table_visible()


# ---------------------------------------------------------------------------
# 143543 — "Listen on Spotify" opens a new tab to the configured URL
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Platform buttons")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Clicking "Listen on Spotify" opens the configured Spotify URL in a new tab')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143543
def test_podcast_spotify_link_opens_new_tab(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    original_url = page.url
    expected_href = podcast.platform_href("Listen on Spotify")

    with allure.step("Click 'Listen on Spotify'"):
        new_page = podcast.click_platform("Listen on Spotify")

    # Assert: new tab, original unchanged
    assert new_page.url == expected_href or expected_href.startswith(new_page.url.split("?")[0])
    assert page.url == original_url
    assert len(page.context.pages) == 2


# ---------------------------------------------------------------------------
# 143544 — "Listen on Apple Music" opens the configured URL in a new tab
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Platform buttons")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Clicking "Listen on Apple Music" opens the configured URL in a new tab')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143544
def test_podcast_apple_music_link_opens_new_tab(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    expected_href = podcast.platform_href("Listen on Apple Music")

    with allure.step("Click 'Listen on Apple Music'"):
        new_page = podcast.click_platform("Listen on Apple Music")

    # Assert
    assert new_page.url.startswith(expected_href.split("?")[0])
    assert len(page.context.pages) == 2


# ---------------------------------------------------------------------------
# 143545 — "RSS Feed" opens the configured RSS URL in a new tab
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Platform buttons")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Clicking "RSS Feed" opens the configured RSS URL in a new tab')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143545
def test_podcast_rss_feed_link_opens_new_tab(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    expected_href = podcast.platform_href("RSS Feed")

    with allure.step("Click 'RSS Feed'"):
        new_page = podcast.click_platform("RSS Feed")

    # Assert
    assert new_page.url.startswith(expected_href.split("?")[0])
    assert len(page.context.pages) == 2


# ---------------------------------------------------------------------------
# 143546 — "Load More" reveals additional episodes
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Load More")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Clicking "Load More" reveals additional episodes')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143546
def test_podcast_load_more_reveals_additional_episodes(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    before = podcast.card_titles()
    assert len(before) == 4

    with allure.step("Click Load More"):
        podcast.click_load_more()

    after = podcast.card_titles()

    # Assert: appended without duplicating existing rows
    assert len(after) == 5
    assert after[:4] == before
    assert len(set(after)) == len(after)


# ---------------------------------------------------------------------------
# 143547 — "Load More" hidden/disabled once no further episodes remain
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Load More")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('"Load More" is hidden or disabled once no further episodes remain')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143547
def test_podcast_load_more_hidden_when_exhausted(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()

    with allure.step("Click Load More until exhausted"):
        podcast.load_all_episodes()

    # Assert
    assert not podcast.is_load_more_visible()
    assert podcast.card_count() == 5


# ---------------------------------------------------------------------------
# 143548 — Play opens the sticky player and starts playback
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Sticky player")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking Play on an episode row opens the sticky player and starts playback")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143548
def test_podcast_play_opens_sticky_player(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    index = podcast.card_index_by_title(TITLE_24)

    with allure.step("Click Play on Episode 24"):
        podcast.click_play(index)

    # Assert: player docked, shows artwork/title/eyebrow, elapsed time advances
    assert podcast.is_player_visible()
    assert podcast.player_title_text() == TITLE_24
    assert podcast.player_eyebrow_text() == "Episode 24"
    page.wait_for_timeout(2000)
    assert podcast.player_time_text() != "0:00 / 0:00"


# ---------------------------------------------------------------------------
# 143549 — Playing a different episode switches the sticky player
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Sticky player")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking Play on a different episode switches the sticky player rather than opening a second one")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143549
def test_podcast_play_different_episode_switches_player(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()

    with allure.step("Play Episode 24"):
        podcast.click_play(podcast.card_index_by_title(TITLE_24))
        assert podcast.player_eyebrow_text() == "Episode 24"

    with allure.step("While playing, click Play on Episode 23"):
        podcast.click_play(podcast.card_index_by_title(TITLE_23))

    # Assert: single player instance, now showing Episode 23
    assert page.locator(podcast.PLAYER).count() == 1
    assert podcast.player_eyebrow_text() == "Episode 23"
    assert podcast.player_title_text() == TITLE_23


# ---------------------------------------------------------------------------
# 143550 — Download works for an Option-A episode
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Download")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Download action downloads the audio file for an Option-A (uploaded file) episode")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143550
def test_podcast_download_option_a_episode(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    index = podcast.card_index_by_title(TITLE_24)
    assert podcast.is_download_visible(index)

    with allure.step("Click Download"):
        with page.expect_download() as download_info:
            page.locator(podcast.CARD).nth(index).locator(podcast.CARD_DOWNLOAD).click()
        download = download_info.value

    # Assert: a real download started, with an audio file extension
    assert download.suggested_filename
    assert any(download.suggested_filename.lower().endswith(ext) for ext in (".mp3", ".wav", ".m4a"))


# ---------------------------------------------------------------------------
# 143551 — Closing the sticky player stops playback and dismisses it
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Sticky player")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Closing the sticky player stops playback and dismisses it")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143551
def test_podcast_close_player_stops_playback(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.click_play(podcast.card_index_by_title(TITLE_24))
    assert podcast.is_player_visible()

    with allure.step("Click the sticky player's close action"):
        podcast.close_player()

    # Assert: playback element removed from the viewport
    assert not podcast.is_player_visible()


# ---------------------------------------------------------------------------
# 143552 — Play/pause control toggles playback
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Sticky player controls")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Sticky player play/pause control toggles playback")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143552
def test_podcast_player_play_pause_toggle(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.click_play(podcast.card_index_by_title(TITLE_24))
    assert podcast.is_player_playing()

    with allure.step("Click Pause"):
        podcast.click_player_play_pause()
    assert not podcast.is_player_playing()
    frozen_time = podcast.player_time_text()
    page.wait_for_timeout(1200)
    assert podcast.player_time_text() == frozen_time

    with allure.step("Click Play"):
        podcast.click_player_play_pause()

    # Assert: resumes from the paused position
    assert podcast.is_player_playing()


# ---------------------------------------------------------------------------
# 143553 — Seek/progress bar jumps playback position
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Sticky player controls")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Sticky player's seek/progress bar jumps playback position")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143553
def test_podcast_player_seek_bar_jumps_position(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.click_play(podcast.card_index_by_title(TITLE_24))
    page.wait_for_timeout(1000)

    with allure.step("Drag the progress bar to the 50% mark"):
        podcast.seek_to_fraction(0.5)
        page.wait_for_timeout(500)

    # Assert: elapsed time reflects the jump, playback continues from there
    fill_width = page.locator(f"{podcast.PLAYER_BAR} .qc-ppl-bar-fill").evaluate(
        "el => parseFloat(el.style.width)"
    )
    assert fill_width > 0


# ---------------------------------------------------------------------------
# 143554 — Skip-forward control advances playback
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Sticky player controls")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Sticky player's skip-forward control advances playback")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143554
def test_podcast_player_skip_forward(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.click_play(podcast.card_index_by_title(TITLE_24))
    page.wait_for_timeout(500)
    before = page.locator(podcast.PLAYER_AUDIO).evaluate("el => el.currentTime")

    with allure.step("Click skip-forward"):
        podcast.click_skip_forward()
        page.wait_for_timeout(300)

    after = page.locator(podcast.PLAYER_AUDIO).evaluate("el => el.currentTime")

    # Assert: elapsed advances by the control's configured interval (~15s)
    assert after > before


# ---------------------------------------------------------------------------
# 143555 — Skip-back control rewinds playback
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Sticky player controls")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Sticky player's skip-back control rewinds playback")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143555
def test_podcast_player_skip_back(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.click_play(podcast.card_index_by_title(TITLE_24))
    page.wait_for_timeout(500)
    podcast.click_skip_forward()
    page.wait_for_timeout(300)
    before = page.locator(podcast.PLAYER_AUDIO).evaluate("el => el.currentTime")

    with allure.step("Click skip-back"):
        podcast.click_skip_back()
        page.wait_for_timeout(300)

    after = page.locator(podcast.PLAYER_AUDIO).evaluate("el => el.currentTime")

    # Assert: elapsed decreases
    assert after < before


# ---------------------------------------------------------------------------
# 143556 — Volume control adjusts playback volume
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Sticky player controls")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Sticky player's volume control adjusts playback volume")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143556
def test_podcast_player_volume_control(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.click_play(podcast.card_index_by_title(TITLE_24))

    with allure.step("Drag the volume control to 50%"):
        podcast.set_volume(0.5)

    # Assert: control reflects the new level, audio element volume matches
    assert podcast.volume_value() == "0.5"
    audio_volume = page.locator(podcast.PLAYER_AUDIO).evaluate("el => el.volume")
    assert round(audio_volume, 1) == 0.5


# ---------------------------------------------------------------------------
# 143557 — Muting the sticky player volume silences playback
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Sticky player controls")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Muting the sticky player volume silences playback")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143557
def test_podcast_player_mute(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.click_play(podcast.card_index_by_title(TITLE_24))
    assert not podcast.is_muted()

    with allure.step("Click mute"):
        podcast.click_mute()

    # Assert: no audible output, icon reflects muted state
    is_muted_prop = page.locator(podcast.PLAYER_AUDIO).evaluate("el => el.muted")
    assert is_muted_prop is True
    assert podcast.is_muted()


# ---------------------------------------------------------------------------
# 143558 — Sticky player remains docked while scrolling the page
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Sticky player")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Sticky player remains docked and playback continues while scrolling the page")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143558
def test_podcast_player_persists_while_scrolling(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.click_play(podcast.card_index_by_title(TITLE_24))

    with allure.step("Scroll to the bottom of the page"):
        page.keyboard.press("End")
        page.wait_for_timeout(1500)

    # Assert: player still visible, elapsed time still advancing
    assert podcast.is_player_visible()
    t1 = page.locator(podcast.PLAYER_AUDIO).evaluate("el => el.currentTime")
    page.wait_for_timeout(1500)
    t2 = page.locator(podcast.PLAYER_AUDIO).evaluate("el => el.currentTime")
    assert t2 >= t1


# ---------------------------------------------------------------------------
# 143559 — Sticky player persists after navigating to another page
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Sticky player")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Sticky player remains docked and playback continues after navigating to another page")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143559
def test_podcast_player_persists_across_navigation(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.click_play(podcast.card_index_by_title(TITLE_24))
    # Wait for playback to actually start before navigating away — mirrors
    # sibling tc_143591's own click_play() + wait_for_timeout(1000) pattern
    # (HEALED 2026-09-23). Without it, navigation can fire before the player
    # has genuinely entered a playing state.
    page.wait_for_timeout(1000)

    with allure.step("Navigate to the Home page via the main menu"):
        header = HeaderComponent(page)
        header.open_home()

    # Assert: player still visible and playing on the new page
    assert podcast.is_player_visible()
    assert podcast.is_player_playing()


# ---------------------------------------------------------------------------
# 143560 — SKIPPED — Download hidden for an Option-B (external embed) episode
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Download")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Download action is hidden for an Option-B (external embed) episode")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143560
def test_podcast_download_hidden_for_option_b_episode(page):
    # Disposable QCTEST episode (see module constants): Audio Source Type
    # = External Embed Link (Option B) — created via Object Authoring per
    # the 2026-09-22 destructive-precondition rule, never one of the 5
    # real, shared QCDEMO episodes (all Option A).
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.load_all_episodes()
    index = podcast.card_index_by_title(QCTEST_EPISODE_TITLE)

    # Assert: no Download link for an Option-B (embed-only) episode
    assert not podcast.is_download_visible(index)


# ---------------------------------------------------------------------------
# 143585 — SKIPPED — Play on an Option-B episode renders the external embed
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Playback")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking Play on an Option-B episode renders the configured external embed player")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143585
def test_podcast_play_option_b_renders_embed(page):
    # Same disposable QCTEST episode as 143560 (Option B / External Embed
    # Link) — created via Object Authoring per the 2026-09-22
    # destructive-precondition rule.
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.load_all_episodes()
    index = podcast.card_index_by_title(QCTEST_EPISODE_TITLE)

    with allure.step("Click Play on the Option-B episode"):
        podcast.click_play(index)

    # Assert: the external-embed iframe slot renders, not an <audio> element
    assert podcast.is_embed_visible()
    assert "spotify" in podcast.embed_frame_src()


# ---------------------------------------------------------------------------
# 143587 — Playing an episode increments its play count once per session
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Play count")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Playing an episode increments its play count once per visitor session")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143587
def test_podcast_play_count_increments_once_per_session(page):
    # Episode 19 ("Women in Business Leadership") carries the lowest live
    # play count (1) — used as the subject so an increment is unambiguous.
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.load_all_episodes()
    index = podcast.card_index_by_title(TITLE_19)

    with allure.step("Note the current play count, then play the episode"):
        before = podcast.card_meta_texts(index)[-1]
        podcast.click_play(index)
        page.wait_for_timeout(2000)

    with allure.step("Reload and read the updated count"):
        podcast.open_podcast()
        podcast.load_all_episodes()
        after_first_play = podcast.card_meta_texts(index)[-1]

    with allure.step("Play the SAME episode again in the SAME browser session"):
        podcast.click_play(index)
        page.wait_for_timeout(2000)
        podcast.open_podcast()
        podcast.load_all_episodes()
        after_second_play = podcast.card_meta_texts(index)[-1]

    # Assert: incremented once after the first play, unchanged after the second
    assert after_first_play != before
    assert after_second_play == after_first_play


# ---------------------------------------------------------------------------
# 143589 — Unavailable/failed audio source shows the error message, recovers
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Playback error handling")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Unavailable/failed audio source shows the unavailable message instead of a broken player, with recovery")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.edge
@pytest.mark.pbi_130713
@pytest.mark.tc_143589
def test_podcast_broken_audio_shows_error_and_recovers(page):
    # A genuine network-level simulation (mirrors
    # accessibility_tools_component.py's real-bundle-abort precedent): aborts
    # every real episode audio-file request so the player's own real error
    # handling fires — not an invented/faked failure.
    podcast = PodcastPage(page)
    podcast.simulate_broken_audio()
    podcast.open_podcast()

    with allure.step("Click Play with the audio source broken"):
        podcast.click_play(podcast.card_index_by_title(TITLE_24))
        page.wait_for_timeout(2000)

    # Assert: unavailable message shown, no broken/blank player
    assert podcast.is_player_error_visible()
    assert podcast.player_error_text() == (
        "This episode is currently unavailable. Please try again later."
    )

    with allure.step("Recovery: reload (clearing the simulated break) and play a healthy episode"):
        page.unroute(podcast.AUDIO_REQUEST_PATTERN)
        podcast.open_podcast()
        podcast.click_play(podcast.card_index_by_title(TITLE_23))
        page.wait_for_timeout(2000)

    # Assert: playback starts normally
    assert podcast.is_player_playing()
    assert not podcast.is_player_error_visible()


# ---------------------------------------------------------------------------
# 143591 — Opening/closing AI Highlights does not interrupt playback
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("AI Highlights popup")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Opening and closing the AI Highlights popup does not interrupt sticky player playback")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143591
def test_podcast_ai_highlights_does_not_interrupt_playback(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()

    with allure.step("Start playback of Episode 24"):
        podcast.click_play(podcast.card_index_by_title(TITLE_24))
        page.wait_for_timeout(1000)

    with allure.step("Open AI Highlights for a different episode, then close it"):
        podcast.click_ai_highlights(podcast.card_index_by_title(TITLE_23))
        podcast.close_popup_via_close_button()

    # Assert: original episode's playback continues uninterrupted
    assert podcast.is_player_playing()
    assert podcast.player_eyebrow_text() == "Episode 24"


# ---------------------------------------------------------------------------
# 143593 — AI Highlights popup shows only the selected episode's highlights
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("AI Highlights popup")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("AI Highlights popup shows only the selected episode's highlights, not another episode's")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143593
def test_ai_highlights_popup_shows_per_episode_highlights(page):
    # *** REAL, CONFIRMED LIVE CANDIDATE BUG (see module docstring): this
    # test is EXPECTED TO FAIL — Episode 24's and Episode 23's popups render
    # the exact same two highlight strings verbatim on this environment.
    # Scripted per the case's real, intended expected result (never
    # weakened to force green — automation-standards.md's Result-integrity
    # section). ***
    podcast = PodcastPage(page)
    podcast.open_podcast()

    with allure.step("Open AI Highlights for Episode 24"):
        podcast.click_ai_highlights(podcast.card_index_by_title(TITLE_24))
        highlights_24 = podcast.popup_highlight_texts()
        podcast.close_popup_via_close_button()

    with allure.step("Close, then open AI Highlights for Episode 23"):
        podcast.click_ai_highlights(podcast.card_index_by_title(TITLE_23))
        highlights_23 = podcast.popup_highlight_texts()

    # Assert: each episode's own highlights, never the other episode's
    assert highlights_24 != highlights_23


# ---------------------------------------------------------------------------
# 143596 — Subscribe with a valid, new email address
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A visitor can subscribe with a valid, new email address")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143596
def test_podcast_subscribe_with_valid_new_email(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    email = _unique_email("new")

    with allure.step(f"Subscribe with {email}"):
        podcast.subscribe(email)

    # Assert: confirmation message shown — the REAL observed text, not the
    # case's own literal wording (see module docstring's "Data adaptations").
    # Verifying the record was stored with status Active, and the
    # Subscription Confirmation email's unsubscribe link/merge fields,
    # needs Control_Panel/mailbox access neither available this batch.
    assert not podcast.is_subscribe_error_visible()
    assert podcast.subscribe_status_text() == (
        "You are subscribed! We will email you when a new episode is published."
    )


# ---------------------------------------------------------------------------
# 143597 — Arabic confirmation message on subscribe
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Subscribing on the Arabic locale shows the correct Arabic confirmation message")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143597
def test_podcast_subscribe_arabic_confirmation_message(page):
    podcast = PodcastPage(page)
    podcast.open_podcast(locale="ar")
    email = _unique_email("ar")

    with allure.step(f"Subscribe with {email} on the AR locale"):
        podcast.subscribe(email)

    # Assert: real observed Arabic confirmation text (see module docstring)
    assert podcast.subscribe_status_text() == (
        "تم اشتراكك! سنرسل لك بريدًا إلكترونيًا عند نشر حلقة جديدة."
    )


# ---------------------------------------------------------------------------
# 143599 — Duplicate active subscription blocked, incl. rapid double-submit
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An already-actively-subscribed address is blocked with no duplicate record, including a rapid double-submit")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.edge
@pytest.mark.pbi_130713
@pytest.mark.tc_143599
def test_podcast_subscribe_duplicate_blocked_and_race_safe(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    dup_email = _unique_email("dup")

    with allure.step(f"Subscribe {dup_email} the first time"):
        podcast.subscribe(dup_email)
        assert podcast.subscribe_status_text() == (
            "You are subscribed! We will email you when a new episode is published."
        )

    with allure.step("Attempt to subscribe the same address again"):
        podcast.subscribe(dup_email)

    # Assert: blocked with the duplicate message
    assert podcast.subscribe_status_text() == "This email address is already subscribed."

    with allure.step("Rapidly double-click Subscribe with a brand-new address"):
        race_email = _unique_email("race")
        podcast.double_click_subscribe(race_email)

    # Assert: the second, back-to-back click did not produce a second
    # distinct "new subscription" confirmation — either the duplicate
    # message (server-side de-duped the race) or the same success message
    # rendered idempotently; this batch has no Control_Panel access to
    # directly count the resulting subscriber records.
    final_status = podcast.subscribe_status_text()
    assert final_status in (
        "You are subscribed! We will email you when a new episode is published.",
        "This email address is already subscribed.",
    )


# ---------------------------------------------------------------------------
# 143602 — SKIPPED — re-subscribing a previously-Unsubscribed address
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Re-subscribing a previously-unsubscribed address reactivates the same record")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143602
@pytest.mark.skip(
    reason="Reaching the Unsubscribed precondition requires clicking a real "
    "unsubscribe link delivered by email — no mailbox/API access is wired "
    "into this framework (checked conftest.py and existing fixtures; none "
    "exists)."
)
def test_podcast_resubscribe_reactivates_unsubscribed_record(page):
    ...


# ---------------------------------------------------------------------------
# 143606 — SKIPPED — unsubscribe-link click sets Unsubscribed
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Following the unsubscribe link in an email sets the subscriber to Unsubscribed")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143606
@pytest.mark.skip(
    reason="Requires clicking a real link delivered inside a received "
    "Podcast email — no mailbox/API access wired into this framework."
)
def test_podcast_unsubscribe_link_sets_unsubscribed(page):
    ...


# ---------------------------------------------------------------------------
# 143607 — SKIPPED — unsubscribed address receives no further emails
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An unsubscribed address receives no further Podcast emails")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143607
@pytest.mark.skip(
    reason="Requires a mailbox/API to confirm an email was NOT delivered — "
    "no such capability is wired into this framework, and it also depends "
    "on the Unsubscribed precondition (see TC 143602's skip reason)."
)
def test_podcast_unsubscribed_receives_no_further_emails(page):
    ...


# ---------------------------------------------------------------------------
# 143609 — SKIPPED — every Podcast email has a working unsubscribe link
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Every Podcast email contains a working unsubscribe link")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143609
@pytest.mark.skip(
    reason="Requires a mailbox/API to inspect delivered email content — no "
    "such capability is wired into this framework (checked conftest.py and "
    "existing fixtures; none exists)."
)
def test_podcast_every_email_has_unsubscribe_link(page):
    ...


# ---------------------------------------------------------------------------
# 143611 — Subscriber email addresses never displayed publicly
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Data privacy")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Subscriber email addresses are never displayed publicly anywhere on the Podcast page")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.auth
@pytest.mark.pbi_130713
@pytest.mark.tc_143611
def test_podcast_subscriber_emails_never_public(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.load_all_episodes()

    # Subscribe with a known address first, so a leak would be observable.
    email = _unique_email("privacy")
    podcast.subscribe(email)

    with allure.step("Reload and inspect the full rendered HTML"):
        podcast.open_podcast()
        html = page.content()

    # Assert: no subscriber email address anywhere in the rendered HTML
    assert email not in html
    assert "@example.com" not in html


# ---------------------------------------------------------------------------
# 143622 — SKIPPED — episode badge count excludes Drafts
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Episode count badge")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Episode count badge reflects only Published episodes, excluding Drafts")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143622
def test_podcast_episode_badge_excludes_drafts(page):
    # Disposable QCTEST episode (see module constants), Status = Draft,
    # created via Object Authoring per the 2026-09-22 destructive-
    # precondition rule — never one of the 5 real, shared QCDEMO episodes.
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.load_all_episodes()

    # Assert: badge still reads the real 5 published episodes, excluding
    # this disposable Draft one
    assert "5" in podcast.badge_texts()[0]
    assert QCTEST_EPISODE_TITLE not in podcast.card_titles()


# ---------------------------------------------------------------------------
# 143623 — SKIPPED — episode badge increments on publish
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Episode count badge")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Episode count badge increments when a new episode is published")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143623
def test_podcast_episode_badge_increments_on_publish(page):
    # Same disposable QCTEST episode as 143622, flipped to Status =
    # Published via Object Authoring (2026-09-22) — never one of the 5
    # real, shared QCDEMO episodes.
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.load_all_episodes()

    # Assert: badge increments to include the newly-published episode
    assert "6" in podcast.badge_texts()[0]
    assert QCTEST_EPISODE_TITLE in podcast.card_titles()


# ---------------------------------------------------------------------------
# 143624 — Episodes listed newest-first by Published Date
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Ordering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Episodes are listed newest-first by Published Date")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143624
def test_podcast_episodes_ordered_newest_first(page):
    # This environment's real 5 live episodes are already published with
    # distinct dates in descending order — verified against the real live
    # order instead of seeding 3 new ones (see module docstring).
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.load_all_episodes()

    dates = []
    for i in range(podcast.card_count()):
        meta = podcast.card_meta_texts(i)
        date_item = next(m for m in meta if "2026" in m)
        dates.append(date_item)

    parsed = [datetime.strptime(d, "%b %d, %Y") for d in dates]

    # Assert: most-recent Published Date first, descending thereafter
    assert parsed == sorted(parsed, reverse=True)
    assert podcast.card_titles() == [TITLE_24, TITLE_23, TITLE_21, TITLE_20, TITLE_19]


# ---------------------------------------------------------------------------
# 143625 — Duration displays as "{n} MIN" (front-end display only)
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Duration formatting")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Duration displays as "{n} MIN" on the episode row')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143625
def test_podcast_duration_displays_as_n_min(page):
    # Only the front-end display half is verified — the case's own second
    # step (reopen the admin record, confirm HH:MM:SS precision is
    # retained) needs Control_Panel access, out of scope this Web-only
    # batch (see module docstring).
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.load_all_episodes()

    for i in range(podcast.card_count()):
        meta = podcast.card_meta_texts(i)
        duration_item = next(m for m in meta if "MIN" in m)
        # Assert: whole-minute integer + " MIN", never HH:MM:SS
        assert re.fullmatch(r"\d+ MIN", duration_item), duration_item


# ---------------------------------------------------------------------------
# 143626 — SKIPPED — play count >1000 abbreviates (e.g. "12.4K plays")
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Play count formatting")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('A play count over 1000 displays abbreviated (e.g. "12.4K plays")')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143626
def test_podcast_play_count_abbreviates_over_1000(page):
    # Disposable QCTEST episode (see module constants), Play Count = 12400
    # — created via Object Authoring per the 2026-09-22 destructive-
    # precondition rule, never one of the 5 real, shared QCDEMO episodes.
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.load_all_episodes()
    index = podcast.card_index_by_title(QCTEST_EPISODE_TITLE)

    meta = podcast.card_meta_texts(index)
    plays_item = next(m for m in meta if "play" in m.lower())

    # Assert: abbreviated form, e.g. "12.4K plays", not the raw "12400"
    assert "12400" not in plays_item
    assert "K" in plays_item.upper()


# ---------------------------------------------------------------------------
# 143627 — SKIPPED — play count boundary 1000/1001
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Play count formatting")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A play count of exactly 1000 abbreviates to \"1K plays\"")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130713
@pytest.mark.tc_143627
def test_podcast_play_count_boundary_1000_1001(page):
    # Same disposable QCTEST episode as 143626, Play Count set to EXACTLY
    # 1000 via Object Authoring (2026-09-22) — the >1000 abbreviation side
    # of this boundary is already confirmed by 143626 (12400 -> "12.4K
    # plays"). Confirmed real behaviour (QA Manager, 2026-09-22): the
    # abbreviation boundary sits AT 1000 inclusive — 1000 itself abbreviates
    # to "1K plays", it does not wait until 1001.
    podcast = PodcastPage(page)
    podcast.open_podcast()
    podcast.load_all_episodes()
    index = podcast.card_index_by_title(QCTEST_EPISODE_TITLE)

    meta = podcast.card_meta_texts(index)
    plays_item = next(m for m in meta if "play" in m.lower())

    # Assert: exactly 1000 renders abbreviated ("1K plays"), not the raw
    # "1000"/"1,000"
    assert "1000" not in plays_item.replace(",", "")
    assert "1K" in plays_item.upper()


# ---------------------------------------------------------------------------
# 143628 — SKIPPED — unpublished episode denied via direct file URL
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Draft/Unpublished visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An unpublished episode cannot be played or downloaded even via a direct file URL")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130713
@pytest.mark.tc_143628
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_podcast_unpublished_episode_denied_direct_url(page):
    # Same disposable QCTEST episode as 143622-143627, flipped to Status =
    # Unpublished via Object Authoring (2026-09-22) — never one of the 5
    # real, shared QCDEMO episodes. Fresh logged-out context per the
    # Draft/Unpublish public-visibility rule.
    podcast = PodcastPage(page)
    status = podcast.fetch_episode_audio_status("176283")

    # Assert: the direct audio-asset URL is denied, not served, once
    # Unpublished
    assert status in (401, 403, 404)


# ---------------------------------------------------------------------------
# 143633 — SKIPPED — Featured episode shown in the Home Page Podcast section
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Home page integration")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Featured episode is the one displayed in the Home Page Podcast section")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143633
@pytest.mark.skip(
    reason="Re-evaluated 2026-09-22: the 'Featured on Home Page' flag IS "
    "settable via Object Authoring on a disposable QCTEST episode (see "
    "this batch's other unblocked cases) — the remaining blocker is that "
    "the Home Page's own Podcast section Page Object is not yet "
    "implemented (web/pages/home_podcast/home_podcast_page.py is a stub); "
    "building that surface is out of scope for this destructive-"
    "precondition re-evaluation pass. Not a CMS-access or rule gap."
)
def test_podcast_featured_episode_shown_on_home_page(page):
    ...


# ---------------------------------------------------------------------------
# 143678 — Whitespace-only subscription email rejected on trim
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A whitespace-only subscription email is trimmed to empty and rejected")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130713
@pytest.mark.tc_143678
def test_podcast_subscribe_whitespace_only_rejected(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()

    with allure.step('Enter "   " (spaces only) and click Subscribe'):
        podcast.subscribe("   ")

    # Assert: trimmed to empty, MSG-5 shown, no record created
    assert podcast.subscribe_error_text() == "This field is required."
    assert not podcast.is_subscribe_status_visible()


# ---------------------------------------------------------------------------
# 143679 — Already-registered address on AR locale shows Arabic message
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Subscribing with an already-registered address on the AR locale shows the correct Arabic "already subscribed" message')
@pytest.mark.web
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.pbi_130713
@pytest.mark.tc_143679
def test_podcast_subscribe_ar_already_subscribed_message(page):
    # Self-contained/idempotent: subscribes a fresh AR-locale address once
    # (making it Active), then immediately re-submits the SAME address to
    # observe the duplicate message — rather than depending on a fixed
    # pre-existing record from a prior run.
    podcast = PodcastPage(page)
    podcast.open_podcast(locale="ar")
    email = _unique_email("ar-dup")

    with allure.step("Subscribe once to make the address Active"):
        podcast.subscribe(email)
        assert podcast.subscribe_status_text() == (
            "تم اشتراكك! سنرسل لك بريدًا إلكترونيًا عند نشر حلقة جديدة."
        )

    with allure.step("Attempt to subscribe the same address again"):
        podcast.subscribe(email)

    # Assert
    assert podcast.subscribe_status_text() == "هذا البريد الإلكتروني مشترك بالفعل"


# ---------------------------------------------------------------------------
# 143820 — Valid email accepted (front-end acceptance only)
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid mixed-case email address is accepted")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.pbi_130713
@pytest.mark.tc_143820
def test_podcast_subscribe_mixed_case_email_accepted(page):
    # Only front-end ACCEPTANCE is verified — confirming the value was
    # actually stored lowercased needs Control_Panel access to the
    # subscriber record, out of scope this Web-only batch.
    podcast = PodcastPage(page)
    podcast.open_podcast()
    ts = int(time.time() * 1000)
    email = f"QA.Podcast.Mixed.{ts}@Example.COM"

    with allure.step(f"Enter {email} and click Subscribe"):
        podcast.subscribe(email)

    # Assert: accepted, confirmation message shown, no validation error
    assert not podcast.is_subscribe_error_visible()
    assert podcast.subscribe_status_text() == (
        "You are subscribed! We will email you when a new episode is published."
    )


# ---------------------------------------------------------------------------
# 143821 — Invalid email format rejected
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An invalid email format is rejected")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.edge
@pytest.mark.pbi_130713
@pytest.mark.tc_143821
def test_podcast_subscribe_invalid_format_rejected(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()

    with allure.step('Enter "not-an-email" and click Subscribe'):
        podcast.subscribe("not-an-email")

    # Assert: MSG-4 shown, blocked
    assert podcast.subscribe_error_text() == "Please enter a valid email address."
    assert not podcast.is_subscribe_status_visible()


# ---------------------------------------------------------------------------
# 143822 — Empty email field rejected
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An empty email field is rejected")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.edge
@pytest.mark.pbi_130713
@pytest.mark.tc_143822
def test_podcast_subscribe_empty_field_rejected(page):
    podcast = PodcastPage(page)
    podcast.open_podcast()

    with allure.step("Leave the email field blank and click Subscribe"):
        podcast.click(podcast.SUB_SUBMIT)
        page.wait_for_timeout(800)

    # Assert: MSG-5 shown, blocked
    assert podcast.subscribe_error_text() == "This field is required."
    assert not podcast.is_subscribe_status_visible()


# ---------------------------------------------------------------------------
# 143823 — Leading/trailing whitespace trimmed before validation (accepted)
# ---------------------------------------------------------------------------
@allure.epic("Insights & Media")
@allure.feature("Podcast")
@allure.story("Subscription validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Leading/trailing whitespace in the email address is trimmed before validation")
@pytest.mark.web
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130713
@pytest.mark.tc_143823
def test_podcast_subscribe_padded_email_trimmed_and_accepted(page):
    # Only front-end ACCEPTANCE is verified — confirming the value was
    # actually stored trimmed needs Control_Panel access, out of scope this
    # Web-only batch.
    podcast = PodcastPage(page)
    podcast.open_podcast()
    ts = int(time.time() * 1000)
    padded_email = f"  qa.podcast.padded.{ts}@example.com  "

    with allure.step("Enter the padded email and click Subscribe"):
        podcast.subscribe(padded_email)

    # Assert: trimmed and accepted without a formatting error
    assert not podcast.is_subscribe_error_visible()
    assert podcast.subscribe_status_text() == (
        "You are subscribed! We will email you when a new episode is published."
    )
