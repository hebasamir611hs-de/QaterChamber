# QATAR CHAMBER — Project Background

> Context for all QA analysis. Read this before analyzing any feature. Derived from
> BRD "Qatar Chamber Website V2.2" (iHorizons, sign-off 09/06/2026). Items marked
> *(confirm)* are assumptions or open items in the BRD itself — verify as the system
> matures.

## Company / Domain
Qatar Chamber (QC) is Qatar's chamber of commerce. This project rebuilds the public
Qatar Chamber website on **Liferay DXP**, replacing the current WordPress site. The
site is a **content-governance-driven bilingual (Arabic/English) public portal** —
informational pages, membership/legal/e-services gateways, committee and B2B
workflows, a media center, an "Invest in Qatar" hub, and an AI chatbot — built and
managed almost entirely inside Liferay CMS with a defined content workflow
(Draft → Pending Review → Approved → Published → Unpublished/Rejected/Archived).

**Important framing for QA:** most "services" on this site are **informational
gateways or lead-capture forms**, not transactional systems. E-Services (Certificate
of Origin, ATA Carnet, TIR Carnet) explicitly do **not** implement the underlying
transaction — they redirect to external platforms. Tenders capture an Expression of
Interest only, no payment. Advertisements explicitly state "online payment... is out
of scope." **There is effectively no real payment flow in this project** — do not
apply money/payment-heavy edge case emphasis by default; only Halls Reservation,
Tender EOI, Membership, Committee/B2B registration, and Advertisement requests
involve business-critical submission + approval workflows.

## Platforms (Surfaces)
- **Public Website** — bilingual (Arabic RTL / English LTR), responsive
  (desktop/tablet/mobile), built on Liferay DXP. This is the only public-facing
  surface — **no mobile app** in this BRD.
- **Liferay CMS / Admin Backend (Control Panel)** — internal content management,
  workflow, form/submission review, lookup/master-data management, chatbot
  administration (via GCP), integration configuration.
- **AI Chatbot widget** — embedded on all public website pages; separately
  administered via the Google Conversational Agents Platform (Gemini models) /
  Google Cloud Platform (GCP) console, not inside Liferay.

There is **no separate mobile platform tag** for this project — all Platform tags
should resolve to `Web` (public site) or `Control_Panel` (CMS/admin), unless a future
phase adds native apps.

## Content Governance Model
Every content type (pages, news, events, publications, circulars, etc.) follows the
same Liferay workflow lifecycle:
`Draft → Pending Review → Approved → Published → Unpublish / Rejected / Archived`.
- **Site Content Author** — creates/edits own content, submits for review; cannot
  publish directly (except where explicitly noted as having Editor-equivalent rights,
  e.g., Chairman's Message, GM's Message).
- **Site Content Editor** — full content lifecycle: create, edit, preview, publish,
  unpublish, delete, manage global components, classify workflow.
- **Form Manager** — manages submitted webforms/submissions specifically (separate
  Site Role layered on top of Editor/Author for form-heavy features).
- **Administrator** — full system control: users, roles, integrations, lookup
  master data, chatbot config, audit logs.
- **Public Visitor** — unauthenticated; views published content, submits public
  forms, subscribes/unsubscribes, uses chatbot.
- **QC Admin Reviewer** — reviews and approves/rejects specific submission types
  (e.g., Advertisement requests, Global Business Opportunity inquiries).

## Services / Products (Website Structure)
1. **About Us** — Qatar Chamber overview, Chairman's Message, Chamber's Laws,
   Vision/Mission/Objective (tabbed), General Manager's Message, Board of Directors &
   General Director (listing + profile pages), Organization Structure (dynamic tree).
2. **Our Services** — Membership Services (New Membership, Renewal, and a tabbed
   Membership Services block: Attestation on Signature, Signatory Cancellation,
   Update Key Contact — all consolidated on one page, redirect-only CTAs to external
   systems), Legal Service (Legal Consulting webform, Mediation webform — both with
   admin Approve/Reject and email notifications), Information (Economic Consultancy,
   Economic Research w/ downloadable reports, Proposal for Research, Circulars — full
   listing/subscription/read+download-count module), Training Platform (redirect-only
   menu + Food Handlers Certification accordion page), Halls Reservation (gallery +
   webform, QC-reviewed offline, acknowledgement email only, **no real booking
   engine** — BRD explicitly flags a fuller booking workflow as Out of Scope).
3. **E-Services** (global rule: **informational gateway only, no real transaction
   processing**) — Certificate of Origin Online, ATA Carnet (User Guide, Apply
   Online), TIR Carnet. All are accordion content + redirect links to external
   platforms.
4. **Committees** — Committee and Business Councils (info + links to join-request
   pages), QAFL Membership Registration (heavy webform, Approve/Reject + email),
   Committee Joining Request (webform), Business Council Joining Request (multicountry webform), Suggestions and Complaints (webform).
5. **Events** — Chamber Events (unified upcoming/ongoing/previous listing, event
   detail page, registration webform — **data capture only, not attendance
   enforcement unless a registration limit is configured**, Add-to-Calendar
   export), Global Events (calendar + grid browsing, **no internal registration** —
   redirects to external organizer/registration site, referral channel only),
   Partners (offers/discounts directory, category-filtered, no inquiry form).
6. **Exhibitions** — Made in Qatar Expo, Made in China Expo — both **redirection-only
   menu items**, no listing/detail pages.
7. **Media Center** — Event Media/PR & Communications Support Request (**internal
   Liferay service**, not public — 7-step stepper form for QC departments, admin
   Approve/Reject), Media Center Homepage (hub with summary counts, quick links,
   news/photo/video previews, newsletter subscribe box), News (listing + detail,
   search/filter/sort, view/share counts), Photo Archive (**two-stage Flickr → Liferay
   Documents & Media import, then album/category creation entirely in Liferay** —
   Flickr is asset-import only, never the content-management layer), Video Library
   (category filter + playback, upload or embed link), Podcasts (episode records with
   **either** an uploaded media file **or** a third-party embed link — at least one
   mandatory), Al-Moltaqa Magazine (issue listing + PDF), Advertisements (rate cards +
   Book Now external redirect + request webform, QC Approve/Reject, **no payment
   processing**), Annual Reports (listing + PDF), Publications (multi-type: Research
   Papers/Guides/Reports/White Papers/Manuals/Brochures, single structure, filterable,
   view/download counts), Private Sector Export Reports (sub-listing under
   Publications), Commercial and Industrial Directory (**read-only nightly cron-synced
   external API data**, plus an internal "Add Your Company Details" review queue that
   never writes back to the external system), For Media Professionals (Press Kit
   download + 3 separate webforms: Interview Request, Event Coverage Request, Media
   Inquiry — acknowledgement email only, no approval workflow).
8. **Invest in Qatar** — Qatar at a Glance (accordion + company/GDP tables), Economic
   Laws, Visas & Immigration, Investment in Qatar (all three: banner + redirect
   links), Business Opportunities (**Global Business Opportunities** — searchable/
   filterable listing, tabbed detail page (Overview/Investment Details/Gallery &
   Docs/Contact & Inquire), inquiry webform, full admin lifecycle incl. archive),
   Business Owners Platform (info page), Tenders (**E-Tender** listing + detail +
   Expression-of-Interest webform — **captures interest only, no payment/award
   processing**; heavy field set incl. Commercial Registration Number as mandatory,
   Establishment/CR Numbers conditional).
9. **B2B** — B2B Platform (directory of QC-approved companies, search + contact
   webform per company), B2B Registration (heavy company webform, admin
   Approve/Reject — approved records **automatically** populate the B2B Platform
   directory, no duplicate entry).
10. **Contact Us** — hero + map + inquiry webform (category dropdown, attachment,
    CAPTCHA).
11. **Useful Links** — collapsible sections of logo-based external redirect links
    (State of Qatar Ministries, Arab Chambers, etc.) — admin-managed, no forms.
12. **FAQ Knowledge Base** — searchable accordion FAQ list.
13. **AI-Powered Chatbot** — Google Conversational Agents Platform (Gemini),
    bilingual, grounded strictly on QC-approved datasets, guided flows + free Q&A,
    speech-to-text, rich content (buttons/cards), webhook/API integration, GCP-side
    logging/analytics. Administered entirely outside Liferay (GCP console).
14. **Global/Cross-cutting features** — 3-level site navigation, global header/
    footer/homepage widgets (incl. live Weather widget via external API), bilingual
    content engine, friendly URLs + SEO metadata, Global Announcement/Alert popup
    (site-wide or page-targeted), AI Text-to-Speech (selected public pages),
    Newsletter Subscription (consent-based, unsubscribe-in-every-email), Configurable
    Lookup Master Data (admin-managed dropdown values across all modules — sector,
    country, currency, tender category, etc.), sitemap.xml (multi-language,
    auto-updated on publish/unpublish), keyboard navigation accessibility, Global
    Advanced Search (cross-module: pages/news/events/publications/services/B2B/
    opportunities).

## Core Business Objects
- **Content Item / Page** — bilingual (EN/AR), Draft→Published lifecycle, per-page
  SEO metadata.
- **Webform Submission** — the generic pattern behind nearly every feature (Legal
  Consultation, Mediation, QAFL, Committee/Business Council Joining, Suggestions &
  Complaints, Halls Reservation, Advertisement Request, Business Opportunity
  Inquiry, Tender EOI, B2B Registration/Contact, Contact Us, For Media forms, Event
  Media internal service): captures applicant data, stores with a status (commonly
  Pending/Submitted → Approved/Rejected), triggers acknowledgement email on
  submission, and — **only on Approval** — triggers a second confirmation email.
  **Rejection generally does not notify the user** except where explicitly stated
  otherwise (e.g., For Media forms send ack only, no approve/reject step at all).
- **Event** — Chamber Event (internal, registration-capable) vs. Global Event
  (external referral, no internal registration) are **distinct object types** with
  different rules — do not conflate them in test design.
- **Publication / Media Asset** — News, Publications, Circulars, Annual Reports,
  Al-Moltaqa issues, Podcast episodes, Video, Photo Album — each with bilingual
  metadata, view/download/read counters, category/type taxonomy, and a PDF or
  media-file/embed-link payload.
- **Directory Company Record** — Commercial Directory (external API, read-only,
  cron-synced) vs. B2B Company Profile (internally created via B2B Registration,
  admin-approved) — **two different data sources feeding conceptually similar
  listings**; do not assume they share a backing table.
- **Lookup / Master Data value** — Sector, Country, Currency, Tender Category,
  Inquiry Type, etc. — all admin-managed via the CMS Lookup Management module, never
  hardcoded. New lookup categories can appear at any time without a code deploy.
- **Subscriber** — Newsletter and Podcast subscriptions are **separate subscription
  objects** (Media Center homepage newsletter vs. Podcast page subscribe box), each
  with their own Active/Unsubscribed lifecycle and unsubscribe-link mechanism.

## User Roles
- **Public Visitor** — unauthenticated browsing, form submission, subscribe/
  unsubscribe, chatbot use.
- **Site Content Author (Site Role)** — creates/edits own content; author-level
  publish rights vary by feature (mostly submit-for-review, a few exceptions have
  direct publish).
- **Site Content Editor (Site Role)** — full content lifecycle across assigned
  features; the default "can do everything content-wise" role in this BRD.
- **Form Manager** — manages webform submissions specifically (layered with Editor/
  Author on form-heavy features: Legal Consultation, Mediation, QAFL, B2B, Contact
  Us, Commercial Directory).
- **QC Admin Reviewer** — approves/rejects Advertisement requests and Business
  Opportunity inquiries specifically.
- **Administrator** — full system control: AD SSO user sync, RBAC/permission
  configuration, User Groups, Lookup Master Data, integration credentials (Flickr,
  chatbot, CAPTCHA), audit logs, sitemap/SEO defaults.
- *(WordPress-legacy roles carried over as Liferay role mappings, mostly not
  QA-relevant beyond permission checks)*: SEO Manager, SEO Editor, Forms Manager
  (Site Role — distinct from "Form Manager" actor label used loosely in some FRs,
  confirm if these are the same role), Event Organizer (Site Role).

## Integrations *(confirm live endpoints/credentials per environment)*
- **AD SSO (ADFS)** — internal/admin user authentication only; passwords not
  managed in Liferay for SSO users.
- **Flickr Pro API** — one-way **asset import** (albums/photos → Liferay Documents &
  Media) via a configurable cron job; never a content-management source of truth.
- **Commercial Directory external API** — read-only nightly sync into Liferay;
  Liferay is display-only for this data, "Add Your Company" submissions go to an
  internal review queue that does **not** write back to the source system.
- **Weather Widget API** — live current-weather + 5-day forecast for Doha, homepage.
- **Google reCAPTCHA** — on all public-facing forms.
- **Email/SMS notification system** — SMTP/API-based, drives every webform's
  acknowledgement/approval email pattern.
- **AI Chatbot — Google Conversational Agents Platform / Gemini / GCP** — webhook/API
  integration for live data lookups, separate GCP-hosted logging & analytics.
- **Google Analytics GA4** — site traffic/behavior tracking via Measurement ID.
- **External redirect-only integrations** (no data exchange, just links, all
  CMS-configurable): Marhaba Guide, Membership System, Food Handling Certificate
  Platform, Training Platform (e.g., ARLO), E-Services Platform, ICC Qatar, QIIC,
  Exhibitions sites, ATA Carnet verification (API), Directory Card redirect (QNB).

## Environments *(confirm)*
Dev / QA / UAT / Prod — not detailed in the BRD; confirm with the client/iHorizons.

## Compatibility & Localization
- **Web:** responsive across desktop/tablet/mobile; standard modern browsers
  *(confirm exact browser/version matrix — not specified in BRD)*.
- **Languages:** Arabic (RTL) and English (LTR) — mandated site-wide, including
  chatbot, TTS, sitemap, and search. Bilingual fields are the default for nearly
  every content type in this BRD — treat a missing Arabic field as a real defect,
  not an edge case.
- **Accessibility:** keyboard navigation, header contrast toggle, zoom in/out are
  explicit BRD requirements (not just nice-to-have).

## Scope Boundaries — Critical for Analysis
The BRD includes an explicit **"Approved Out of Scope" list** (iHorizons will build
these for free, but they are officially out of scope) and a separate **"Out of
Scope"** list (cost/timeline impact, only via Change Request). Before deep-analyzing
any feature, check whether it appears in either list in the BRD's closing sections —
notably: Advanced/AI-powered search, dynamic org structure, Legal Consulting/
Mediation status-revision workflows, Circulars WhatsApp/mobile-API preview, full
end-to-end Hall Reservation booking engine, Event Media custom dashboards, most
"Global Events" advanced features (AI search, maps, delegation tracking, SSO,
SLA/analytics dashboards), and most "Business Opportunity" advanced features (AI
search/recommendations, map view, SEO schema, saved searches). **Do not write test
cases beyond what a section's core FR describes if the enhancement is explicitly
listed as out of scope** — flag it as N/A with the BRD reference instead.

## Notes / To Confirm
- Whether "Form Manager" (actor label) and "Forms Manager (Site Role)" are the same
  role or two distinct role names carried from different sections of the BRD.
- Exact non-production environment names/URLs.
- Browser/OS support matrix (not specified).
- Whether a mobile app is planned for a future phase (none in this BRD).
