"""
cms/pages/join_committee/join_committee_admin_page.py — Control_Panel Page
Objects for PBI 130717 (Request to Join a Committee).

Live Object Authoring sidebar, 2026-10-04 (full re-read, all roles): the
feature is backed by exactly two objects,
  * "Committee Joining Request" (manage-committee-joining-request): the
    submissions, reviewed by row actions (council_base.SubmissionAdminPage);
  * "Committee Lookup Status" (manage-committee-lookup-status): the lookup
    values behind the public Sector / Committee dropdown (listKey
    `sectorCommittee`, entryKey = the dropdown option value).
There is NO page-content object for the Request to Join a Committee page
(hero, info section, form header / disclaimer / consent): cases that edit it
cannot be scripted and are reported as an open question.
"""

from cms.pages.components.disposable_object_admin import FieldSpec as F
from cms.pages.join_committee.council_base import SubmissionAdminPage, _Council, _DraftsOff

# The lookup's own picklist values (a Committee Lookup Status field, read live).
LOOKUP_ACTIVE = "Active"
LOOKUP_INACTIVE = "Inactive"
SECTOR_LIST_KEY = "sectorCommittee"


class CommitteeLookupStatusAdminPage(_DraftsOff, _Council):
    """Drafts are off for this record type; Submit is the save."""

    SIDEBAR_LABEL = "Committee Lookup Status"
    SLUG = "committee-lookup-status"
    PLURAL = "committeelookupstatuses"
    TITLE_FIELD = "entry_key"
    ACTIVE_FIELD = None  # the gate is the Active State picklist, not a checkbox
    FIELDS = {
        "list_key": F("Lookup List", required=True, default=SECTOR_LIST_KEY, confirmed_live=True),
        "entry_key": F("Lookup Entry Key", required=True, confirmed_live=True),
        "label_en": F("Label (EN)", confirmed_live=True),
        "label_ar": F("Label (AR)", confirmed_live=True),
        "active_state": F("Active State", kind="select", required=True, default=LOOKUP_ACTIVE, confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9900", confirmed_live=True),
    }


class CommitteeJoiningRequestAdminPage(SubmissionAdminPage):
    SIDEBAR_LABEL = "Committee Joining Request"
    SLUG = "committee-joining-request"
    PLURAL = "committeejoiningrequests"


class RequestToJoinCommitteePageAdminPage(_Council):
    """A9 2026-10-07: "Request to Join a Committee Page" appeared on the live sidebar (Editor, Form
    Manager, Contributor; created 2026-10-05). Its one entry 441112 IS the live page and its manage page
    opens that record's form directly (singleton trap), so 441112 is in LIVE_IDS: the network guard
    blocks any write to it unless one test is running it under reports/live-restore/a9_cycle.py
    (allow_live_write). Drafts are ON (Save as Draft + Publish; a Published record shows
    "Unpublish to edit as draft"). Field refs read live (a9/explore/join_form.json)."""

    SIDEBAR_LABEL = "Request to Join a Committee Page"
    SLUG = "request-to-join-a-committee-page"
    PLURAL = "requesttojoinacommitteepages"
    SINGLETON = True
    LIVE_IDS = ("441112",)
    TITLE_FIELD = "page_title"
    FIELDS = {
        "page_title": F("Page Title", bilingual=True, required=True, confirmed_live=True),
        "hero_description": F("Page Description", kind="rich", bilingual=True, required=True, ref="heroDescription",
                              confirmed_live=True),
        "hero_image": F("Hero Background Image", kind="file", confirmed_live=True),
        "eyebrow": F("Section Eyebrow", bilingual=True, confirmed_live=True),
        "section_title": F("Section Heading", bilingual=True, confirmed_live=True),
        "section_intro": F("Section Body", kind="rich", bilingual=True, required=True, ref="sectionIntro",
                           confirmed_live=True),
        "form_icon": F("Form Icon", kind="file", confirmed_live=True),
        "form_title": F("Form Title", bilingual=True, confirmed_live=True),
        "form_intro": F("Form Disclaimer", bilingual=True, confirmed_live=True),
        "consent": F("Consent Statement", kind="rich", bilingual=True, required=True, ref="consentStatement",
                     confirmed_live=True),
        "privacy_url": F("Privacy Policy Link", kind="url", confirmed_live=True),
        "submit_label": F("Submit Button Label", bilingual=True, confirmed_live=True),
        "success_message": F("Success Message", bilingual=True, confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }
