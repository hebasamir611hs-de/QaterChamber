"""
cms/pages/podcast/podcast_admin_page.py — Control_Panel Page Objects for
PBI 130713 (QC - Media Center - Podcast).

Objects (names from the live Object Authoring sidebar per the 2026-10-01
brief): Podcast Show Configuration (page-level, SINGLETON), Podcast Platform
Link, Podcast Episode, Podcast Subscriber. `SLUG_CONFIRMED_LIVE` stays False
until each slug is read on the sidebar; DisposableObjectAdminPage refuses to
navigate before that. Field labels are the test cases' wording until read live.

Podcast Subscriber rows are real visitor subscriptions: open and read only,
except a QCTEST subscriber this suite created itself.
"""

from cms.pages.components.disposable_object_admin import DisposableObjectAdminPage, FieldSpec as F


class PodcastShowConfigurationAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Podcast Show Configuration"
    SLUG = ""
    SINGLETON = True
    TITLE_FIELD = "show_title"
    FIELDS = {
        "show_title": F("Show Title", bilingual=True, required=True, max_len=150),
        "show_description": F("Show Description", kind="rich", bilingual=True, required=True,
                              ref="showDescription", max_len=1000,
                              default="QCTEST show description.", default_ar="وصف البرنامج."),
        "hero_background_image": F("Hero Background Image", kind="file", required=True),
        "hero_illustration": F("Hero Illustration", kind="file", required=True),
        "cadence_badge_label": F("Cadence Badge Label", bilingual=True, required=True, max_len=30,
                                 default="Weekly", default_ar="أسبوعي"),
        "host_name": F("Host Name", bilingual=True, required=True, max_len=150,
                       default="QCTEST Host", default_ar="مقدم اختبار"),
        "host_title": F("Host Title", bilingual=True, required=True, max_len=150,
                        default="QCTEST Presenter", default_ar="مذيع اختبار"),
        "host_image": F("Host Image", kind="file", required=True),
        "subscription_heading": F("Subscription Heading", bilingual=True, required=True, max_len=150,
                                  default="Subscribe", default_ar="اشترك"),
        "subscription_description": F("Subscription Description", bilingual=True, required=True,
                                      max_len=300, default="QCTEST updates.", default_ar="تحديثات."),
        "email_placeholder": F("Email Field Placeholder", bilingual=True, required=True,
                               default="Email", default_ar="البريد"),
        "subscribe_button_label": F("Subscribe Button Label", bilingual=True, required=True,
                                    default="Subscribe", default_ar="اشترك"),
        "active_status": F("Active Status", kind="checkbox"),
    }


class PodcastPlatformLinkAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Podcast Platform Link"
    SLUG = ""
    TITLE_FIELD = "platform_name"
    FIELDS = {
        "platform_name": F("Platform Name", bilingual=True, required=True, max_len=60),
        "platform_icon": F("Platform Icon", kind="file", required=True),
        "platform_url": F("Platform URL", kind="url", required=True,
                          default="https://example.com/qctest-podcast"),
        # Multiples of 100 (OBJECT-AUTHORING-GUIDE); 9900 keeps a QCTEST row last.
        "display_order": F("Display Order", kind="number", required=True, default="9900"),
        "active_status": F("Active Status", kind="checkbox"),
    }


class PodcastEpisodeAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Podcast Episode"
    SLUG = ""
    TITLE_FIELD = "episode_title"
    FIELDS = {
        "episode_title": F("Episode Title", bilingual=True, required=True, max_len=200),
        "episode_number": F("Episode Number", kind="number", required=True, default="9901"),
        "episode_artwork": F("Episode Artwork", kind="file", required=True),
        "brief_description": F("Brief Description", bilingual=True, required=True, max_len=300,
                               default="QCTEST episode.", default_ar="حلقة اختبار."),
        # Default variant plays from an embed link (Option B), so a QCTEST
        # episode needs no audio upload; PodcastEpisodeAudioAdminPage is the
        # uploaded-file variant (Option A).
        "audio_source_type": F("Audio Source Type", kind="select", required=True, default="Option B"),
        "audio_file": F("Episode Audio File", kind="file"),
        "embed_link": F("Episode Embed Link", kind="url", required=True,
                        default="https://example.com/qctest-embed"),
        "published_date": F("Published Date", kind="date", required=True, ref="publishedDate",
                            default="01/06/2027"),
        "duration": F("Duration", required=True, default="00:42:15"),
        "featured": F("Featured on Home Page", kind="checkbox"),
        "active_status": F("Active Status", kind="checkbox"),
    }
    OPTION_AUDIO_FILE = "Option A"  # TODO(live): exact option labels
    OPTION_EMBED = "Option B"


class PodcastSubscriberAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Podcast Subscriber"
    SLUG = ""
    TITLE_FIELD = "email"
    ACTIVE_FIELD = None
    FIELDS = {
        "email": F("Email", required=True),
        "status": F("Status", kind="select"),
    }


class PodcastEpisodeAudioAdminPage(PodcastEpisodeAdminPage):
    """Same object, uploaded-audio variant (Audio Source Type = Option A)."""

    FIELDS = dict(
        PodcastEpisodeAdminPage.FIELDS,
        audio_source_type=F("Audio Source Type", kind="select", required=True, default="Option A"),
        audio_file=F("Episode Audio File", kind="file", required=True),
        embed_link=F("Episode Embed Link", kind="url"),
    )
