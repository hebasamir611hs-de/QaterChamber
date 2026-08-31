# Qatar Chamber — Liferay DXP Technical Context

Purpose: a single technical reference on how this Liferay DXP instance is actually
built and wired, for writing test-automation / API scripts against it. Combines
(a) the project's existing Claude Code skill docs (`CMS/skills.zip`), (b) the
non-technical `Content-Admin-Guide.docx`, and (c) a live, read-only exploration
of the real instance performed 2026-08-13. Where live findings differ from the
skill docs, the live findings win and are marked **[LIVE]**; anything not
independently re-verified live is marked **[FROM SKILLS]**.

This is a living document — re-verify anything load-bearing before a first
write against a *different* instance/version, per the skills' own
"Verification duty" convention.

---

## 1. Environment & Connectivity

- **Instance explored**: `https://qcdev.ihorizons.com` (dev, actively being
  worked on by other people/pipelines — expect data to change between runs).
- **Auth**: HTTP Basic, `Authorization: Basic base64(email:password)`. Demo
  credentials used for read-only exploration: `test@liferay.com` / `test`.
  Never print credentials in logs/reports. **[LIVE — confirmed working]**
- **Canonical site "Qatar Chamber"**: groupId **37246**, externalReferenceCode
  `QCDEMO-SITE-qatar-chamber`, friendlyUrlPath `/qatar-chamber`,
  defaultLanguageId `en_US` / `en-US`, availableLanguageIds `en_US, ar_SA`
  (Arabic is RTL). Two other sites exist on the instance: `Guest` (id 20127,
  `/guest`) and the instance's `Global` group (id 20121) — neither holds QC
  content. **[LIVE — confirmed]**
- **Headless API bases** (all under `https://qcdev.ihorizons.com`):
  - `/o/headless-admin-content/v1.0` — structured-contents templates,
    display-page-templates, page-definitions. **No content-structures
    mutation route exists here** (GET-only elsewhere, see §5).
  - `/o/headless-delivery/v1.0` — sites, content-structures (GET-only),
    document-folders/documents, site-pages, structured-contents.
  - `/o/headless-admin-site/v1.0` — sites (create/update).
  - `/o/headless-admin-user/v1.0` — user-accounts.
  - `/o/object-admin/v1.0` — object-definitions, object-fields,
    object-actions, object-layouts, object-relationships (full CRUD).
  - `/o/headless-admin-list-type/v1.0` — list-type-definitions (backs
    Picklist option sets).
  - `/o/c/{restContextPath}` — auto-generated CRUD for each Object
    Definition's entries (the actual content-editing surface).
  - `/o/mcp` — Liferay's own MCP server, gated behind
    `feature.flag.LPD-63311`. **Not used this session** — direct REST GETs
    were sufficient and avoid a restart/local Node bridge dependency.
    **[FROM SKILLS, connector setup documented in `liferay-mcp-connector`
    skill if ever needed]**
- **Pagination envelope** (all list endpoints): `{ items, page, pageSize,
  totalCount, lastPage }`. `page` is 1-based. **See §5 for pageSize/pagination
  bugs — do not assume this is reliable at face value.**

---

## 2. Content Model — How This Site Is Actually Built

Three layers, and only the third is what content editors (and most
automation) ever touches:

1. **Pages** — layout only (`/o/headless-delivery/v1.0/sites/{siteId}/site-pages`,
   35 pages on this site — home, about-us and its 8 subpages, our-services and
   its 9 subpages, contact-us, news, podcast, plus several `*-detail` /
   `*-listing` template pages consumed by fragments). Off-limits to editors.
2. **Fragments** — the HTML/CSS/JS design blocks dropped onto pages, built via
   Fragment Collections in the Liferay Admin UI (from Figma, per the
   `qatar-chamber-header-footer-master` / `qatar-chamber-deploy-fragment`
   skills). **[LIVE] Confirmed NOT exposed via headless REST on this
   instance/version** — searched all paths in the `headless-delivery`,
   `headless-admin-content`, and `object-admin` OpenAPI specs, zero
   fragment-related routes. Fragment automation must go through the Admin UI
   or Playwright (see `qatar-chamber-playwright-fragment-import` skill),
   never REST.
3. **Objects / Content Structures** — the actual editable data. This project
   uses **two distinct mechanisms** side by side:
   - **Liferay Objects** (`/o/object-admin/v1.0/object-definitions`,
     entries at `/o/c/{restContextPath}`) — the dominant pattern here. **[LIVE]
     111 site-scoped, Qatar-Chamber-specific Object Definitions exist**,
     essentially one small object (or object family) per page section (see
     §6 for the full catalog). Used for anything with ordering, an
     active/inactive flag, or a draft/publish status — i.e. almost
     everything on this site.
   - **Journal/Web Content Structures**
     (`/o/headless-delivery/v1.0/content-structures`, GET-only via REST) —
     used sparingly. **[LIVE] Only 6 exist**: Home Page Section, Business
     Events Section, Publications Section, Contact Us Section, Board
     Directory Page, Organization Structure Page (full fields in §9).

Every editable field is bilingual (`en_US` + `ar_SA`) by convention, though
**live data shows this is inconsistently honored** — see §10 (Data Quality).

### ERC (External Reference Code) scheme **[FROM SKILLS, pattern confirmed live]**
Every resource is addressed by ERC, never a raw numeric ID, for idempotent
GET/PUT:
- Object Definition: `QCDEMO-{storyId}-{OBJECT_NAME}` (upper-snake or
  kebab-case observed for both — live data is NOT perfectly consistent, e.g.
  `QCDEMO-129382-upcoming-event-pin` vs `QCDEMO-129363-NAV_ITEM`; don't
  hardcode a casing assumption, read the ERC as stored).
  Exceptions seen live: a handful of fixed, non-story-scoped ERCs like
  `QC_FOOTER_CONFIGURATION`, `QC_COMMUNITY_PARTNER`,
  `QCDEMO-ABOUT-HERO-BANNER` (shared across all About-Us subpages).
- Site: fixed exception `QCDEMO-SITE-qatar-chamber` (not story-scoped).
- List Type Definition: `{OBJECT_ERC}-{FIELD}-OPTIONS` (also inconsistent
  casing live — see §8).

---

## 3. Headless Write Protocol **[FROM SKILLS — `liferay-headless-skill`, not exercised live this session since this pass was read-only]**

Golden rule: **never POST directly**; every mutation is an idempotent PUT by
ERC, preceded by a GET that captures prior state for rollback.

1. `GET .../by-external-reference-code/{erc}` → 404 means create, 200 means
   update (capture the full body as priorState).
2. `PUT .../by-external-reference-code/{erc}` with the desired body.
3. Log `{resourceType, erc, id, action, priorState, endpoint, at}` for
   rollback before/after every mutation.
4. `DELETE .../by-external-reference-code/{erc}` for rollback only; 404 on
   delete = already gone = success.

Endpoint-specific confirmed behavior (dated, from prior verification passes —
re-confirm before first live write against a new instance/version):
- **Object Definition**: full by-ERC PUT route confirmed working; a new/updated
  definition is inactive until `POST .../object-definitions/{id}/publish`.
- **List Type Definition**: full by-ERC PUT route confirmed working; embed
  `listTypeEntries[]` directly in the PUT body.
- **Structure (DDM/legacy)**: **no mutation route exists at all** on this
  instance — GET-only. Use `content-structures` for read/existence-check only;
  never attempt a write. If a plan entity needs a writable structure, model it
  as an Object Definition instead.
- **Document Folder**: no by-ERC route; idempotency substitute is GET the
  parent's folder listing and match by `name` client-side, then POST only if
  absent.
- **Document upload/move**: requires `multipart/form-data`, not JSON — a
  plain JSON body 415s.
- A `required: true` Boolean object field cannot be explicitly PUT/PATCHed
  back to `false` on this instance (400) — model an "unsubscribe/deactivate"
  action as a DELETE of the entry instead, or design the field as
  `required: false` from the start if an explicit false must be settable.
- Attachment field uploads: `objectFieldSettings.acceptedFileExtensions` must
  be bare extensions with **no leading dot** (`"jpg, png"`, not `".jpg,.png"`)
  or every upload 400s with "invalid extension" even though the field itself
  looks fine in the Admin UI.

---

## 4. Localization & RTL **[FROM SKILLS]**
- `defaultLanguageId: en_US`, `availableLanguageIds: [en_US, ar_SA]`.
- Locale key format is **not consistent across APIs** — see §5, item 5.
- A missing Arabic translation is conventionally marked with an
  English-text-plus-`(AR)` suffix and `needsTranslation=true` — never
  machine-translate ad hoc; this marker is the contract for a human
  translation pass. **[LIVE] This convention is real and pervasive in
  current data — see §10.**
- Templates/fragments must use logical CSS properties (`margin-inline-start`,
  not `margin-left`) to render correctly under `dir="rtl"`.

---

## 5. Platform Gotchas & Known Issues (merged: prior + newly found)

1. **Percent-encode every `?filter=...` query value.** Liferay's URI parser
   throws `URISyntaxException` on raw spaces/quotes (e.g.
   `filter=name eq 'Navigation Item'`). Prefer fetching unfiltered/paginated
   and matching client-side over filtering — sidesteps this entirely.
   **[FROM SKILLS]**
2. **A site-scoped Object's entry collection must be addressed via
   `/o/c/{restContextPath}/scopes/{groupId}`**, never the bare
   `/o/c/{restContextPath}` — the bare form 409s ("Conflict with
   getObjectEntriesPage"), not 404. Applies to any site-scoped Object, not
   just the ones first discovered this way. **[FROM SKILLS]**
3. **`GET /o/object-admin/v1.0/object-definitions?pageSize=N` returns a bogus
   `404 {"status":"NOT_FOUND"}` when N >= 99.** Stay at pageSize <= 50 for
   this endpoint. **[LIVE — newly confirmed 2026-08-13]**
4. **Two specific Object Definitions are permanently un-listable** — they
   404 on every single-item page regardless of pageSize/page/sort
   combination, yet fetch fine individually via
   `GET .../by-external-reference-code/{erc}`:
   - `QCDEMO-129405-MEDIATION_PAGE` (id 90039) — ERC known.
   - One more, alphabetically between `L_POSTAL_ADDRESS` and
     `QCDEMO-129402-APPLY_ONLINE_CTA` under `sort=name:asc` — likely a
     company-scope system object, ERC unrecoverable via listing (never
     surfaces). If you need the complete Object Definition list, iterate
     known ERCs from this document rather than trusting the listing
     endpoint to be exhaustive. **[LIVE — newly found 2026-08-13]**
5. **`sort=id:asc` / `sort=id:desc` return HTTP 400** on both
   `/o/object-admin/v1.0/object-definitions` and
   `/o/headless-admin-list-type/v1.0/list-type-definitions` — `id` isn't a
   whitelisted sort field on either. Use `name:asc`, `dateCreated:asc`, or
   omit `sort`. **[LIVE — newly found]**
6. **`/o/headless-admin-list-type/v1.0/list-type-definitions` listing
   silently omits healthy, individually-fetchable records** — beyond the 2
   that hard-404, at least 5 more referenced-and-working list types never
   appear in any listing page/position, for reasons unrelated to the hard-404
   pattern. **For this endpoint specifically, resolve ERCs from the Object
   fields that reference them (`listTypeDefinitionExternalReferenceCode`)
   rather than trusting the list endpoint's completeness.** **[LIVE — newly
   found]**
7. **Locale key format differs by API.** `list-type-entries[].name_i18n` uses
   hyphenated keys (`en-US`, `ar-SA`); `objectFields[].label` and
   `objectValidationRules[].errorLabel` on `/o/object-admin` use underscored
   keys (`en_US`, `ar_SA`). Normalize before comparing/merging across APIs.
   **[LIVE — newly found]**
8. **Object field `localized` flag is immutable after creation** — flipping
   it requires delete + recreate the field, so get it right in the create
   payload. **[FROM SKILLS]**
9. Object Definition create is POST + a separate `/publish` call; delete is
   by numeric id only (`by-external-reference-code` DELETE returns 405).
   **[FROM SKILLS]**
10. Formal `objectRelationships[]` are rare: only 3 exist across all 111
    site objects (NavItem self-reference for nav hierarchy,
    FooterNavigationColumn → FooterNavigationLink, ServiceInformationGroup →
    ServiceInformationGroupItem). **Objects sharing a `QCDEMO-{storyId}-`
    prefix are usually siblings, not linked by any API-visible relationship**
    — there is no single call to fetch "all children of X" for most feature
    groups (e.g. the 9 Mediation objects, 10 TIR Carnet objects, 10 COO
    objects are each independently addressable). Any hierarchy visible on
    the page is assembled by fragment/page composition, not an object
    relationship. **[LIVE — newly found]**
11. Export/seed scripts must use `node fetch`, never `curl` piped through a
    shell — curl mangles inline Arabic UTF-8 in this environment.
    **[FROM SKILLS]**

---

## 6. Live Object Definitions Catalog (111 site-scoped objects, 37 feature groups)

**[LIVE — captured 2026-08-13, one row per object, full field tables below each]**

This is the full inventory referenced above. Feature groups are keyed by the
numeric story-id embedded in the ERC (e.g. `QCDEMO-129405-*` = the Mediation
service page); a handful use fixed non-story ERCs (`QC_FOOTER_*`,
`QC_COMMUNITY_PARTNER`, `QCDEMO-ABOUT-HERO-BANNER`) because they're shared
global elements rather than single-page features.

### QCDEMO-129363

Objects: `HeaderConfiguration`, `NavItem`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| HeaderConfiguration | QCDEMO-129363-HEADER_CONFIGURATION | 44720 | Header Configuration | Header Configuration (AR) | Header Configurations | externalReferenceCode | 5 |  |  |
| NavItem | QCDEMO-129363-NAV_ITEM | 44631 | Navigation Item | Navigation Item (AR) | Navigation Items | navItemLabelEn | 6 |  | 1 |

**HeaderConfiguration** (`QCDEMO-129363-HEADER_CONFIGURATION`, id 44720) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| workflowStatus | Workflow Status | Workflow Status (AR) | Picklist | String | true | false | QCDEMO-129363-HEADER_CONFIGURATION-WORKFLOW_STATUS-OPTIONS |  |
| logoImage | Logo Image | ???? ?????? | Attachment | Long | true | false |  | acceptedFileExtensions=png, svg; fileSource=documentsAndMedia |
| logoAltTextEn | Logo Alt Text (EN) | ???? ?????? ?????? (???????) | Text | String | true | false |  |  |
| logoAltTextAr | Logo Alt Text (AR) | ???? ?????? ?????? (????) | Text | String | true | false |  |  |
| logoRedirectUrl | Logo Redirect URL | ???? ????? ????? ?????? | LongText | Clob | true | false |  |  |

**NavItem** (`QCDEMO-129363-NAV_ITEM`, id 44631) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| navItemLabelEn | Nav Item Label EN | Nav Item Label EN (AR) | Text | String | true | false |  | indexed |
| navItemLabelAr | Nav Item Label AR | Nav Item Label AR (AR) | Text | String | true | false |  |  |
| navItemUrl | Nav Item URL | Nav Item URL (AR) | Text | String | false | false |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  |  |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |
| r_navItemParent_c_navItemId | Parent Item | العنصر الأصل | Relationship | Long | false | false |  | indexed |

### QCDEMO-129364

Objects: `AccessibilityHeaderConfiguration`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| AccessibilityHeaderConfiguration | QCDEMO-129364-accessibility-header-configuration | 45327 | Accessibility Header Configuration | إعدادات إمكانية الوصول في الرأس (بانتظار المراجعة اللغوية) | Accessibility Header Configurations | externalReferenceCode | 1 |  |  |

**AccessibilityHeaderConfiguration** (`QCDEMO-129364-accessibility-header-configuration`, id 45327) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| accessibilityToolsEnabled | Accessibility Tools Enabled | تفعيل أدوات إمكانية الوصول (بانتظار المراجعة اللغوية) | Boolean | Boolean | false | false |  |  |

### QCDEMO-129366

Objects: `BottomBarLink`, `CopyrightBar`, `FooterNavigationColumn`, `FooterNavigationLink`, `QuickLink`, `SocialMediaIcon`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| BottomBarLink | QCDEMO-129366-BOTTOM_BAR_LINK | 46541 | Bottom Bar Link | Bottom Bar Link (AR) | Bottom Bar Links | externalReferenceCode | 5 |  |  |
| CopyrightBar | QCDEMO-129366-COPYRIGHT_BAR | 46493 | Copyright Bar | Copyright Bar (AR) | Copyright Bars | externalReferenceCode | 2 |  |  |
| FooterNavigationColumn | QCDEMO-129366-FOOTER_NAVIGATION_COLUMN | 46203 | Footer Navigation Column | Footer Navigation Column (AR) | Footer Navigation Columns | heading | 4 |  | 1 |
| FooterNavigationLink | QCDEMO-129366-FOOTER_NAVIGATION_LINK | 46257 | Footer Navigation Link | Footer Navigation Link (AR) | Footer Navigation Links | externalReferenceCode | 7 |  |  |
| QuickLink | QCDEMO-129366-QUICK_LINK | 46421 | Quick Link | Quick Link (AR) | Quick Links | externalReferenceCode | 6 |  |  |
| SocialMediaIcon | QCDEMO-129366-SOCIAL_MEDIA_ICON | 45866 | Social Media Icon | Social Media Icon (AR) | Social Media Icons | externalReferenceCode | 10 |  |  |

**BottomBarLink** (`QCDEMO-129366-BOTTOM_BAR_LINK`, id 46541) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| title | Bottom Link Title | Bottom Link Title (AR) | Text | String | true | true |  | indexed |
| openInNewTab | Open in New Tab | Open in New Tab (AR) | Boolean | Boolean | false | false |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| active | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |
| url | Bottom Link URL | Bottom Link URL (AR) | Text | String | false | true |  |  |

**CopyrightBar** (`QCDEMO-129366-COPYRIGHT_BAR`, id 46493) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| copyrightText | Copyright Text | Copyright Text (AR) | LongText | Clob | true | true |  | indexed |
| active | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |

**FooterNavigationColumn** (`QCDEMO-129366-FOOTER_NAVIGATION_COLUMN`, id 46203) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| heading | Column Heading | Column Heading (AR) | Text | String | true | true |  | indexed |
| columnNumber | Column Number | Column Number (AR) | Integer | Integer | true | false |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| active | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |

**FooterNavigationLink** (`QCDEMO-129366-FOOTER_NAVIGATION_LINK`, id 46257) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| title | Link Title | Link Title (AR) | Text | String | true | true |  | indexed |
| url | Link URL | Link URL (AR) | Text | String | true | true |  |  |
| openInNewTab | Open in New Tab | Open in New Tab (AR) | Boolean | Boolean | false | false |  |  |
| columnNumber | Parent Column Number | Parent Column Number (AR) | Integer | Integer | false | false |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| active | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |
| r_footerNavColumnLinks_c_footerNavigationColumnId | Footer Navigation Column | عمود تنقل التذييل | Relationship | Long | false | false |  | indexed |

**QuickLink** (`QCDEMO-129366-QUICK_LINK`, id 46421) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| columnHeading | Quick Links Column Heading | Quick Links Column Heading (AR) | Text | String | true | true |  | indexed |
| title | Quick Link Title | Quick Link Title (AR) | Text | String | true | true |  |  |
| url | Quick Link URL | Quick Link URL (AR) | Text | String | true | true |  |  |
| openInNewTab | Open in New Tab | Open in New Tab (AR) | Boolean | Boolean | false | false |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| active | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |

**SocialMediaIcon** (`QCDEMO-129366-SOCIAL_MEDIA_ICON`, id 45866) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| platform | Platform | Platform (AR) | Picklist | String | true | false | QCDEMO-129366-SOCIAL_MEDIA_ICON-PLATFORM-OPTIONS | indexed |
| image | Social Icon Image | Social Icon Image (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, gif, webp; fileSource=documentsAndMedia |
| altText | Icon Alt Text | Icon Alt Text (AR) | Text | String | true | true |  |  |
| redirectUrl | Social Redirect URL | Social Redirect URL (AR) | Text | String | true | true |  |  |
| openInNewTab | Open in New Tab | Open in New Tab (AR) | Boolean | Boolean | false | false |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| active | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |
| showOnHome | Show on Home | Show on Home (AR) | Boolean | Boolean | false | false |  | indexed |
| homeIconImage | Home Icon Image | Home Icon Image (AR) | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, gif, webp; fileSource=documentsAndMedia |
| homeDisplayOrder | Home Display Order | Home Display Order (AR) | Integer | Integer | false | false |  | indexed |

### QCDEMO-129367

Objects: `AchievementCounter`, `HeroBannerSlide`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| AchievementCounter | QCDEMO-129367-ACHIEVEMENT_COUNTER | 45566 | Achievement Counter | Achievement Counter (AR) | Achievement Counters | externalReferenceCode | 6 |  |  |
| HeroBannerSlide | QCDEMO-129367-HERO_BANNER_SLIDE | 45374 | Hero Banner Slide | Hero Banner Slide (AR) | Hero Banner Slides | externalReferenceCode | 14 |  |  |

**AchievementCounter** (`QCDEMO-129367-ACHIEVEMENT_COUNTER`, id 45566) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| counterTitleEn | Counter Title (EN) | Counter Title (EN) (AR) | Text | String | false | false |  | indexed |
| counterTitleAr | Counter Title (AR) | Counter Title (AR) (AR) | Text | String | false | false |  |  |
| counterValue | Counter Value | Counter Value (AR) | Text | String | false | false |  |  |
| counterIcon | Counter Icon | Counter Icon (AR) | Attachment | Long | false | false |  | acceptedFileExtensions=png, svg; fileSource=documentsAndMedia |
| counterDisplayOrder | Counter Display Order | Counter Display Order (AR) | Integer | Integer | false | false |  |  |
| counterActiveStatus | Counter Active Status | Counter Active Status (AR) | Boolean | Boolean | false | false |  |  |

**HeroBannerSlide** (`QCDEMO-129367-HERO_BANNER_SLIDE`, id 45374) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| bannerImage | Banner Image | Banner Image (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=gif, jpeg, jpg, mp4, png, webm, webp; fileSource=documentsAndMedia |
| bannerTitleEn | Banner Title (EN) | Banner Title (EN) (AR) | Text | String | true | false |  | indexed |
| bannerTitleAr | Banner Title (AR) | Banner Title (AR) (AR) | Text | String | true | false |  |  |
| bannerSubtitleDescriptionEn | Banner Subtitle (Description) (EN) | Banner Subtitle (Description) (EN) (AR) | LongText | Clob | false | false |  |  |
| bannerSubtitleDescriptionAr | Banner Subtitle (Description) (AR) | Banner Subtitle (Description) (AR) (AR) | LongText | Clob | false | false |  |  |
| button1LabelEn | Button 1 Label (EN) | Button 1 Label (EN) (AR) | Text | String | true | false |  |  |
| button1LabelAr | Button 1 Label (AR) | Button 1 Label (AR) (AR) | Text | String | true | false |  |  |
| button1Link | Button 1 Link | Button 1 Link (AR) | Text | String | true | false |  |  |
| button2LabelEn | Button 2 Label (EN) | Button 2 Label (EN) (AR) | Text | String | true | false |  |  |
| button2LabelAr | Button 2 Label (AR) | Button 2 Label (AR) (AR) | Text | String | true | false |  |  |
| button2Link | Button 2 Link | Button 2 Link (AR) | Text | String | true | false |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  |  |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |
| counterActiveStatus | Counters Active Status |  | Boolean | Boolean | false | false |  | indexed |

### QCDEMO-129368

Objects: `PromotionalBanner`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| PromotionalBanner | QCDEMO-129368-PROMOTIONAL_BANNER | 47506 | Promotional Banner | لافتة ترويجية | Promotional Banners | bannerAltTextEN | 12 | 2 |  |

**PromotionalBanner** (`QCDEMO-129368-PROMOTIONAL_BANNER`, id 47506) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| bannerImageEN | Banner Image (EN) | Banner Image (EN) (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| bannerImageAR | Banner Image (AR) | Banner Image (AR) (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| bannerAltTextEN | Banner Alt Text (EN) | Banner Alt Text (EN) (AR) | Text | String | true | false |  | indexed |
| bannerAltTextAR | Banner Alt Text (AR) | Banner Alt Text (AR) (AR) | Text | String | true | false |  | indexed |
| redirectUrl | Redirect URL | Redirect URL (AR) | Text | String | false | true |  |  |
| openInNewTab | Open in New Tab | Open in New Tab (AR) | Boolean | Boolean | false | false |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |
| startDate | Start Date | تاريخ البدء | Date | Date | false | false |  |  |
| endDate | End Date | تاريخ الانتهاء | Date | Date | false | false |  |  |
| bannerImageMobileEN | Banner Image Mobile (EN) | صورة البانر للجوال (إنجليزي) | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| bannerImageMobileAR | Banner Image Mobile (AR) | صورة البانر للجوال (عربي) | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |

Validation rules on **PromotionalBanner**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Display Order Positive | `displayOrder >= 1` | Positive number required. | يجب إدخال رقم موجب. |
| Redirect URL Valid | `equals(redirectUrl, "") \|\| isURL(redirectUrl)` | Please enter a valid URL. | يرجى إدخال رابط صالح. |

### QCDEMO-129371

Objects: `FilterTab`, `ServiceCard`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| FilterTab | QCDEMO-129371-FILTER_TAB | 48032 | Filter Tab | Filter Tab (AR) | Filter Tabs | tabLabel | 3 | 1 |  |
| ServiceCard | QCDEMO-129371-SERVICE_CARD | 47976 | Service Card | Service Card (AR) | Service Cards | title | 8 | 2 |  |

**FilterTab** (`QCDEMO-129371-FILTER_TAB`, id 48032) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| tabLabel | Tab Label | Tab Label (AR) | Text | String | true | true |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |

Validation rules on **FilterTab**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Display Order Positive | `displayOrder >= 1` | Positive number required. | يجب إدخال رقم موجب. |

**ServiceCard** (`QCDEMO-129371-SERVICE_CARD`, id 47976) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| imageThumbnail | Image Thumbnail | Image Thumbnail (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, gif, webp; fileSource=documentsAndMedia |
| icon | Icon | Icon (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| title | Title | العنوان | Text | String | true | true |  | indexed |
| shortDescription | Short Description | Short Description (AR) | LongText | Clob | false | true |  | indexed |
| redirectUrl | Redirect URL | Redirect URL (AR) | Text | String | true | false |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |
| assignedTab | Assigned Tab | Assigned Tab (AR) | Picklist | String | true | false | QCDEMO-129371-SERVICE_CARD-ASSIGNED_TAB-OPTIONS | indexed |

Validation rules on **ServiceCard**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Display Order Positive | `displayOrder >= 1` | Positive number required. | يجب إدخال رقم موجب. |
| Redirect URL Valid | `equals(redirectUrl, "") \|\| isURL(redirectUrl)` | Please enter a valid URL. | يرجى إدخال رابط صالح. |

### QCDEMO-129372

Objects: `NewsArticle`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| NewsArticle | QCDEMO-129372-NEWS_ARTICLE | 48649 | News Article | مقال إخباري | News Articles | title | 5 |  |  |

**NewsArticle** (`QCDEMO-129372-NEWS_ARTICLE`, id 48649) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| title | Title | العنوان | Text | String | true | true |  | indexed |
| thumbnailImage | Thumbnail Image | Thumbnail Image (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| publicationDate | Publication Date | Publication Date (AR) | Date | Date | true | false |  | indexed |
| viewCount | View Count | View Count (AR) | Integer | Integer | false | false |  | indexed |
| activeStatus | Active/Published Status | Active/Published Status (AR) | Boolean | Boolean | false | false |  | indexed |

### QCDEMO-129381

Objects: `StrategicPillarCard`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| StrategicPillarCard | QCDEMO-129381-STRATEGIC_PILLAR_CARD | 48938 | Strategic Pillar Card | Strategic Pillar Card (AR) | Strategic Pillar Cards | externalReferenceCode | 5 | 3 |  |

**StrategicPillarCard** (`QCDEMO-129381-STRATEGIC_PILLAR_CARD`, id 48938) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| pillarTitle | Pillar Title | Pillar Title (AR) | Text | String | true | true |  | indexed |
| pillarDescription | Pillar Description | Pillar Description (AR) | RichText | Clob | true | true |  |  |
| pillarIcon | Pillar Icon | Pillar Icon (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=png, svg; fileSource=documentsAndMedia |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |

Validation rules on **StrategicPillarCard**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Pillar Title Max Length | `length(pillarTitle) <= 100` | Pillar Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان الركيزة 100 حرف. |
| Pillar Description Max Length | `length(pillarDescription) <= 1000` | Pillar Description must not exceed 1000 characters. | يجب ألا يتجاوز وصف الركيزة 1000 حرف. |
| Display Order Minimum | `displayOrder >= 1` | Display Order must be a positive number (1 or greater). | يجب أن يكون ترتيب العرض رقمًا موجبًا (1 أو أكثر). |

### QCDEMO-129382

Objects: `UpcomingEventPin`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| UpcomingEventPin | QCDEMO-129382-upcoming-event-pin | 49124 | Upcoming Event Pin | تثبيت الفعالية القادمة | Upcoming Event Pins | externalReferenceCode | 2 |  |  |

**UpcomingEventPin** (`QCDEMO-129382-upcoming-event-pin`, id 49124) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| pinnedEvent | Pinned Event | الفعالية المثبتة | Text | String | false | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  | indexed |

### QCDEMO-129383

Objects: `BusinessEvent`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| BusinessEvent | QCDEMO-129383-business-event | 49263 | Business Event | فعالية تجارية | Business Events | eventTitle | 8 | 3 |  |

**BusinessEvent** (`QCDEMO-129383-business-event`, id 49263) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| eventTitle | Event Title | عنوان الفعالية | Text | String | true | true |  | indexed |
| eventSector | Event Sector | قطاع الفعالية | Text | String | true | true |  | indexed |
| eventCategory | Event Category | فئة الفعالية | Picklist | String | true | false | QCDEMO-129383-BUSINESS_EVENT-eventCategory-OPTIONS | indexed |
| eventDateTime | Event Date & Time | تاريخ ووقت الفعالية | DateTime | DateTime | true | false |  | indexed |
| location | Location | الموقع | Text | String | true | true |  |  |
| eventImage | Event Image | صورة الفعالية | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| description | Description | الوصف | RichText | Clob | false | true |  |  |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  | indexed |

Validation rules on **BusinessEvent**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Event Title Max Length | `length(eventTitle) <= 200` | Event Title must not exceed 200 characters. | يجب ألا يتجاوز عنوان الفعالية 200 حرف. |
| Location Max Length | `length(location) <= 200` | Location must not exceed 200 characters. | يجب ألا يتجاوز الموقع 200 حرف. |
| Description Max Length | `equals(description, "") \|\| length(description) <= 2000` | Description must not exceed 2000 characters. | يجب ألا يتجاوز الوصف 2000 حرف. |

### QCDEMO-129384

Objects: `DynamicWidget`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| DynamicWidget | QCDEMO-129384-dynamic-widget | 49566 | Dynamic Widget | أداة ديناميكية (AR) | Dynamic Widgets | externalReferenceCode | 6 | 3 |  |

**DynamicWidget** (`QCDEMO-129384-dynamic-widget`, id 49566) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| widgetImageEn | Widget Image (EN) | Widget Image (EN) (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png, svg; fileSource=documentsAndMedia |
| widgetImageAr | Widget Image (AR) | Widget Image (AR) (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png, svg; fileSource=documentsAndMedia |
| redirectUrl | Redirect URL | Redirect URL (AR) | Text | String | true | false |  |  |
| openInNewTab | Open in New Tab | Open in New Tab (AR) | Boolean | Boolean | false | false |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |

Validation rules on **DynamicWidget**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Redirect URL Format | `match(redirectUrl, "^https?://.*")` | Please enter a valid URL. | يرجى إدخال رابط صالح. |
| Redirect URL Max Length | `length(redirectUrl) <= 500` | Redirect URL must not exceed 500 characters. | يجب ألا يتجاوز رابط إعادة التوجيه 500 حرف. |
| Display Order Minimum | `displayOrder >= 1` | Display Order must be a positive number (1 or greater). | يجب أن يكون ترتيب العرض رقمًا موجبًا (1 أو أكثر). |

### QCDEMO-129386

Objects: `Publication`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| Publication | QCDEMO-129386-publication | 49925 | Publication | منشور | Publications | publicationTitle | 9 |  |  |

**Publication** (`QCDEMO-129386-publication`, id 49925) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| publicationTitle | Publication Title | عنوان المنشور | Text | String | true | true |  | indexed |
| publicationDescription | Publication Description | وصف المنشور | LongText | Clob | false | true |  |  |
| publicationType | Publication Type | نوع المنشور | Picklist | String | true | false | QCDEMO-129386-PUBLICATION-PUBLICATIONTYPE-OPTIONS | indexed |
| publicationDate | Publication Date | تاريخ النشر | Date | Date | true | false |  | indexed |
| coverImage | Cover Image | صورة الغلاف | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| fileAttachment | File Attachment | الملف المرفق | Attachment | Long | true | false |  | acceptedFileExtensions=pdf; fileSource=documentsAndMedia |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  | indexed |
| downloadCount | Download Count | عدد التنزيلات | Integer | Integer | false | false |  | indexed |
| viewCount | View Count | عدد المشاهدات | Integer | Integer | false | false |  | indexed |

### QCDEMO-129387

Objects: `PodcastEpisode`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| PodcastEpisode | QCDEMO-129387-podcast-episode | 50342 | Podcast Episode | حلقة البودكاست | Podcast Episodes | episodeTitleEn | 16 | 11 |  |

**PodcastEpisode** (`QCDEMO-129387-podcast-episode`, id 50342) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| episodeTitleEn | Episode Title (EN) | Episode Title (EN) (AR) | Text | String | true | false |  | indexed |
| episodeTitleAr | Episode Title (AR) | Episode Title (AR) (AR) | Text | String | true | false |  | indexed |
| episodeNumber | Episode Number | Episode Number (AR) | Integer | Integer | true | false |  | indexed |
| descriptionEn | Description (EN) | Description (EN) (AR) | LongText | Clob | true | false |  | indexed |
| descriptionAr | Description (AR) | Description (AR) (AR) | LongText | Clob | true | false |  |  |
| thumbnailImage | Thumbnail Image | Thumbnail Image (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| audioFile | Audio File | Audio File (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=mp3, aac; fileSource=documentsAndMedia |
| duration | Duration | Duration (AR) | Text | String | true | false |  |  |
| publishDate | Publish Date | Publish Date (AR) | Date | Date | true | false |  | indexed |
| episodeCountLabelEn | Episode Count Label (EN) | Episode Count Label (EN) (AR) | Text | String | false | false |  |  |
| episodeCountLabelAr | Episode Count Label (AR) | Episode Count Label (AR) (AR) | Text | String | false | false |  |  |
| frequencyLabelEn | Frequency Label (EN) | Frequency Label (EN) (AR) | Text | String | false | false |  |  |
| frequencyLabelAr | Frequency Label (AR) | Frequency Label (AR) (AR) | Text | String | false | false |  |  |
| featuredOnHomePage | Featured on Home Page | Featured on Home Page (AR) | Boolean | Boolean | false | false |  | indexed |
| exploreMoreUrl | Explore More URL | Explore More URL (AR) | Text | String | true | false |  |  |
| episodeStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129387-PODCAST_EPISODE-status-OPTIONS | indexed |

Validation rules on **PodcastEpisode**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Episode Title (EN) Max Length | `length(episodeTitleEn) <= 250` | Episode Title (EN) must not exceed 250 characters. | يجب ألا يتجاوز عنوان الحلقة (بالإنجليزية) 250 حرفًا. |
| Episode Title (AR) Max Length | `length(episodeTitleAr) <= 250` | Episode Title (AR) must not exceed 250 characters. | يجب ألا يتجاوز عنوان الحلقة (بالعربية) 250 حرفًا. |
| Episode Number Positive | `episodeNumber >= 1` | Episode Number must be a positive number. | يجب أن يكون رقم الحلقة رقمًا موجبًا. |
| Description (EN) Max Length | `equals(descriptionEn, "") \|\| length(descriptionEn) <= 500` | Description (EN) must not exceed 500 characters. | يجب ألا يتجاوز الوصف (بالإنجليزية) 500 حرف. |
| Description (AR) Max Length | `equals(descriptionAr, "") \|\| length(descriptionAr) <= 500` | Description (AR) must not exceed 500 characters. | يجب ألا يتجاوز الوصف (بالعربية) 500 حرف. |
| Duration Max Length | `length(duration) <= 10` | Duration must not exceed 10 characters. | يجب ألا تتجاوز المدة 10 أحرف. |
| Episode Count Label (EN) Max Length | `equals(episodeCountLabelEn, "") \|\| length(episodeCountLabelEn) <= 50` | Episode Count Label (EN) must not exceed 50 characters. | يجب ألا تتجاوز تسمية عدد الحلقات (بالإنجليزية) 50 حرفًا. |
| Episode Count Label (AR) Max Length | `equals(episodeCountLabelAr, "") \|\| length(episodeCountLabelAr) <= 50` | Episode Count Label (AR) must not exceed 50 characters. | يجب ألا تتجاوز تسمية عدد الحلقات (بالعربية) 50 حرفًا. |
| Frequency Label (EN) Max Length | `equals(frequencyLabelEn, "") \|\| length(frequencyLabelEn) <= 50` | Frequency Label (EN) must not exceed 50 characters. | يجب ألا تتجاوز تسمية التكرار (بالإنجليزية) 50 حرفًا. |
| Frequency Label (AR) Max Length | `equals(frequencyLabelAr, "") \|\| length(frequencyLabelAr) <= 50` | Frequency Label (AR) must not exceed 50 characters. | يجب ألا تتجاوز تسمية التكرار (بالعربية) 50 حرفًا. |
| Explore More URL Max Length | `length(exploreMoreUrl) <= 500` | Explore More URL must not exceed 500 characters. | يجب ألا يتجاوز رابط استكشاف المزيد 500 حرف. |

### QCDEMO-129388

Objects: `MediaItem`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| MediaItem | QCDEMO-129388-media-item | 50743 | Media Item | عنصر وسائط | Media Items | mediaTitleEn | 6 | 3 |  |

**MediaItem** (`QCDEMO-129388-media-item`, id 50743) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| mediaTitleEn | Media Title (EN) | عنوان الوسائط (بالإنجليزية) | Text | String | true | false |  | indexed |
| mediaTitleAr | Media Title (AR) | عنوان الوسائط (بالعربية) | Text | String | true | false |  | indexed |
| thumbnailImage | Thumbnail Image | الصورة المصغّرة | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| videoFileEmbedUrl | Video File / Embed URL | ملف الفيديو / رابط التضمين | Text | String | false | false |  |  |
| publicationDate | Publication Date | تاريخ النشر | Date | Date | true | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  | indexed |

Validation rules on **MediaItem**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Media Title (EN) Max Length | `length(mediaTitleEn) <= 200` | Media Title (EN) must not exceed 200 characters. | يجب ألا يتجاوز عنوان الوسائط (بالإنجليزية) 200 حرف. |
| Media Title (AR) Max Length | `length(mediaTitleAr) <= 200` | Media Title (AR) must not exceed 200 characters. | يجب ألا يتجاوز عنوان الوسائط (بالعربية) 200 حرف. |
| Video File / Embed URL Max Length | `equals(videoFileEmbedUrl, "") \|\| length(videoFileEmbedUrl) <= 500` | Video File / Embed URL must not exceed 500 characters. | يجب ألا يتجاوز رابط ملف الفيديو / التضمين 500 حرف. |

### QCDEMO-129389

Objects: `AboutUsCounter`, `AboutUsSection`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| AboutUsCounter | QCDEMO-129389-about-us-counter | 52004 | About Us Counter | عداد إنجازات من نحن | About Us Counters | externalReferenceCode | 6 | 1 |  |
| AboutUsSection | QCDEMO-129389-about-us-section | 51812 | About Us Section | قسم من نحن | About Us Sections | externalReferenceCode | 14 | 1 |  |

**AboutUsCounter** (`QCDEMO-129389-about-us-counter`, id 52004) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| counterTitleEn | Counter Title (EN) | عنوان العداد (بالإنجليزية) | Text | String | true | false |  | indexed |
| counterTitleAr | Counter Title (AR) | عنوان العداد (بالعربية) | Text | String | true | false |  |  |
| counterValue | Counter Value | قيمة العداد | Text | String | true | false |  |  |
| counterIcon | Counter Icon | أيقونة العداد | Attachment | Long | false | false |  | acceptedFileExtensions=png, svg; fileSource=documentsAndMedia |
| counterDisplayOrder | Counter Display Order | ترتيب عرض العداد | Integer | Integer | true | false |  | indexed |
| counterActiveStatus | Counter Active Status | حالة تفعيل العداد | Boolean | Boolean | false | false |  | indexed |

Validation rules on **AboutUsCounter**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Counter Display Order positive | `counterDisplayOrder >= 1` | Counter Display Order must be a positive number. | يجب أن يكون ترتيب عرض العداد رقمًا موجبًا. |

**AboutUsSection** (`QCDEMO-129389-about-us-section`, id 51812) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionTagEn | Section Tag (EN) | وسم القسم (بالإنجليزية) | Text | String | false | false |  |  |
| sectionTagAr | Section Tag (AR) | وسم القسم (بالعربية) | Text | String | false | false |  |  |
| sectionHeadingEn | Section Heading (EN) | عنوان القسم (بالإنجليزية) | Text | String | true | false |  | indexed |
| sectionHeadingAr | Section Heading (AR) | عنوان القسم (بالعربية) | Text | String | true | false |  | indexed |
| sectionDescriptionEn | Section Description (EN) | وصف القسم (بالإنجليزية) | RichText | Clob | true | false |  |  |
| sectionDescriptionAr | Section Description (AR) | وصف القسم (بالعربية) | RichText | Clob | true | false |  |  |
| buildingImagePrimary | Building Image (Primary) | صورة المبنى (الأساسية) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| buildingImageSecondary | Building Image (Secondary) | صورة المبنى (الثانوية) | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| buildingImageTertiary | Building Image (Tertiary) | صورة المبنى (الثالثة) | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| yearsOfExperienceBadgeEn | Years of Experience Badge (EN) | شارة سنوات الخبرة (بالإنجليزية) | Text | String | false | false |  |  |
| yearsOfExperienceBadgeAr | Years of Experience Badge (AR) | شارة سنوات الخبرة (بالعربية) | Text | String | false | false |  |  |
| readMoreLabelEn | Read More Label (EN) | نص زر اقرأ المزيد (بالإنجليزية) | Text | String | true | false |  |  |
| readMoreLabelAr | Read More Label (AR) | نص زر اقرأ المزيد (بالعربية) | Text | String | true | false |  |  |
| readMoreUrl | Read More URL | رابط اقرأ المزيد | Text | String | true | false |  |  |

Validation rules on **AboutUsSection**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Read More URL format | `isURL(readMoreUrl)` | Please enter a valid URL. | يرجى إدخال رابط صالح. |

### QCDEMO-129390

Objects: `InquiryCategory`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| InquiryCategory | QCDEMO-129390-INQUIRY_CATEGORY | 52436 | Inquiry Category | Inquiry Category (AR) | Inquiry Categories | externalReferenceCode | 3 | 2 |  |

**InquiryCategory** (`QCDEMO-129390-INQUIRY_CATEGORY`, id 52436) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| label | Category Label | Category Label (AR) | Text | String | true | true |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |

Validation rules on **InquiryCategory**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Display Order Positive | `displayOrder >= 1` | Positive number required. | يجب إدخال رقم موجب. |
| Category Label Max Length | `length(label) <= 100` | Category Label must not exceed 100 characters. | يجب ألا يتجاوز اسم الفئة 100 حرف. |

### QCDEMO-129391

Objects: `StrategicPartner`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| StrategicPartner | QCDEMO-129391-STRATEGIC_PARTNER | 53108 | Strategic Partner | شريك استراتيجي | Strategic Partners | partnerName | 7 |  |  |

**StrategicPartner** (`QCDEMO-129391-STRATEGIC_PARTNER`, id 53108) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| partnerName | Partner Name | Partner Name (AR) | Text | String | true | true |  | indexed |
| logoImage | Logo Image | Logo Image (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| logoAltText | Logo Alt Text | Logo Alt Text (AR) | Text | String | true | true |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  | indexed |
| startDate | Start Date | تاريخ البدء | Date | Date | false | false |  |  |
| endDate | End Date | تاريخ الانتهاء | Date | Date | false | false |  |  |

### QCDEMO-129392

Objects: `AboutQatarChamberPage`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| AboutQatarChamberPage | QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE | 77427 | About Qatar Chamber Page | صفحة غرفة قطر | About Qatar Chamber Pages | externalReferenceCode | 9 | 7 |  |

**AboutQatarChamberPage** (`QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE`, id 77427) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| pageTitle | Page Title | عنوان الصفحة | Text | String | true | true |  | indexed |
| heroBannerImage | Hero Banner Image | صورة البانر الرئيسي | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png, svg; fileSource=documentsAndMedia |
| heroBannerAltText | Hero Banner Alt Text | النص البديل للبانر الرئيسي | Text | String | true | true |  |  |
| contentImage | Content Image | صورة المحتوى | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png, svg; fileSource=documentsAndMedia |
| contentImageAltText | Content Image Alt Text | النص البديل لصورة المحتوى | Text | String | true | true |  |  |
| pageContent | Page Content | محتوى الصفحة | RichText | Clob | true | true |  | indexed |
| hyperlinkTitle | Hyperlink Title | عنوان الرابط | Text | String | false | true |  |  |
| hyperlinkUrl | Hyperlink URL | رابط URL | Text | String | false | true |  |  |
| pageStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-STATUS-OPTIONS | indexed |

Validation rules on **AboutQatarChamberPage**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Page Title max length | `pageTitle == null \|\| length(pageTitle) <= 100` | Arabic title is required. | العنوان العربي مطلوب. |
| Hero Banner Alt Text max length | `heroBannerAltText == null \|\| length(heroBannerAltText) <= 150` | Hero Banner Alt Text must not exceed 150 characters. | يجب ألا يتجاوز النص البديل للبانر الرئيسي 150 حرفًا. |
| Content Image Alt Text max length | `contentImageAltText == null \|\| length(contentImageAltText) <= 150` | Content Image Alt Text must not exceed 150 characters. | يجب ألا يتجاوز النص البديل لصورة المحتوى 150 حرفًا. |
| Page Content max length | `pageContent == null \|\| length(pageContent) <= 5000` | Page Content must not exceed 5000 characters. | يجب ألا يتجاوز محتوى الصفحة 5000 حرف. |
| Hyperlink Title max length | `hyperlinkTitle == null \|\| length(hyperlinkTitle) <= 100` | Hyperlink Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان الرابط 100 حرف. |
| Hyperlink URL max length | `hyperlinkUrl == null \|\| length(hyperlinkUrl) <= 500` | Hyperlink URL must not exceed 500 characters. | يجب ألا يتجاوز رابط URL 500 حرف. |
| Hyperlink URL format | `hyperlinkUrl == null \|\| equals(hyperlinkUrl, "") \|\| match(hyperlinkUrl, "^https?://.*")` | A valid URL is required. | يجب إدخال رابط صحيح. |

### QCDEMO-129393

Objects: `ChairmanMessagePage`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| ChairmanMessagePage | QCDEMO-129393-CHAIRMAN_MESSAGE_PAGE | 78084 | Chairman Message Page | Chairman Message Page (AR) | Chairman Message Pages | externalReferenceCode | 11 | 1 |  |

**ChairmanMessagePage** (`QCDEMO-129393-CHAIRMAN_MESSAGE_PAGE`, id 78084) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| pageTitle | Page Title | Page Title (AR) | Text | String | true | true |  | indexed |
| heroBannerImage | Hero Banner Image | Hero Banner Image (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png; fileSource=documentsAndMedia |
| heroBannerAltText | Hero Banner Alt Text | Hero Banner Alt Text (AR) | Text | String | true | true |  |  |
| chairmanPortrait | Chairman Portrait | Chairman Portrait (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png; fileSource=documentsAndMedia |
| chairmanPortraitAltText | Chairman Portrait Alt Text | Chairman Portrait Alt Text (AR) | Text | String | true | true |  |  |
| chairmanName | Chairman Name | Chairman Name (AR) | Text | String | true | true |  | indexed |
| chairmanDesignation | Chairman Designation | Chairman Designation (AR) | Text | String | true | true |  |  |
| messageContent | Message Content | Message Content (AR) | RichText | Clob | true | true |  |  |
| hyperlinkTitle | Hyperlink Title | Hyperlink Title (AR) | Text | String | false | true |  |  |
| hyperlinkUrl | Hyperlink URL | Hyperlink URL (AR) | LongText | Clob | false | true |  |  |
| publishStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129393-CHAIRMAN_MESSAGE_PAGE-STATUS-OPTIONS |  |

Validation rules on **ChairmanMessagePage**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Hyperlink URL Format | `equals(hyperlinkUrl, "") \|\| match(hyperlinkUrl, "^https?://.*")` | Please enter a valid URL starting with http:// or https:// | الرجاء إدخال رابط صالح يبدأ بـ http:// أو https:// |

### QCDEMO-129394

Objects: `LawEntry`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| LawEntry | QCDEMO-129394-LAW_ENTRY | 78508 | Law Entry | سجل قانوني | Law Entries | lawTitle | 7 | 5 |  |

**LawEntry** (`QCDEMO-129394-LAW_ENTRY`, id 78508) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| lawNumber | Law Number | Law Number (AR) | Text | String | true | true |  | indexed |
| lawTitle | Law Title | Law Title (AR) | Text | String | true | true |  | indexed |
| lawDescription | Law Description | Law Description (AR) | LongText | Clob | true | true |  |  |
| externalLinkUrl | External Link URL | رابط النص القانوني الخارجي | Text | String | false | false |  |  |
| lawIcon | Law Icon | أيقونة القانون | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png, svg; fileSource=documentsAndMedia |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  | indexed |

Validation rules on **LawEntry**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| External Link URL format | `isEmpty(externalLinkUrl) \|\| match(externalLinkUrl, "^https?://.*")` | External Link URL must start with http:// or https:// | يجب أن يبدأ الرابط الخارجي بـ http:// أو https:// |
| Display Order minimum | `displayOrder >= 1` | Display Order must be 1 or greater | يجب أن يكون ترتيب العرض 1 أو أكبر |
| Law Number length | `match(lawNumber, "(?s)^.{0,100}$")` | Law Number must not exceed 100 characters | يجب ألا يتجاوز رقم القانون 100 حرف |
| Law Title length | `match(lawTitle, "(?s)^.{0,200}$")` | Law Title must not exceed 200 characters | يجب ألا يتجاوز عنوان القانون 200 حرف |
| Law Description length | `match(lawDescription, "(?s)^.{0,500}$")` | Law Description must not exceed 500 characters | يجب ألا يتجاوز وصف القانون 500 حرف |

### QCDEMO-129395

Objects: `VmoSection`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| VmoSection | QCDEMO-129395-VMO_SECTION | 78736 | VMO Section | VMO Section (AR) | VMO Sections | externalReferenceCode | 8 |  |  |

**VmoSection** (`QCDEMO-129395-VMO_SECTION`, id 78736) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionLabel | Section Label | Section Label (AR) | Text | String | true | true |  | indexed |
| headline | Headline | Headline (AR) | Text | String | true | true |  | indexed |
| subheading | Subheading | Subheading (AR) | Text | String | false | true |  |  |
| bodyContent | Body Content | Body Content (AR) | RichText | Clob | false | true |  |  |
| sectionImage | Section Image | صورة القسم | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png, svg; fileSource=documentsAndMedia |
| imageBadgeLabel | Image Badge Label | Image Badge Label (AR) | Text | String | false | true |  |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| active | Active | الحالة النشطة | Boolean | Boolean | false | false |  | indexed |

### QCDEMO-129397

Objects: `GeneralManagerMessage`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| GeneralManagerMessage | QCDEMO-129397-GENERAL_MANAGER_MESSAGE | 79727 | General Manager Message | رسالة المدير العام | General Manager Messages | externalReferenceCode | 11 |  |  |

**GeneralManagerMessage** (`QCDEMO-129397-GENERAL_MANAGER_MESSAGE`, id 79727) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| pageTitle | Page Title | Page Title (AR) | Text | String | true | true |  | indexed |
| heroBanner | Hero Banner | صورة البانر الرئيسي | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png, svg; fileSource=documentsAndMedia |
| heroBannerAltText | Image Alt Text | Image Alt Text (AR) | Text | String | true | true |  |  |
| gmPortrait | GM Portrait Image | صورة المدير العام | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| gmName | GM Name | GM Name (AR) | Text | String | true | true |  | indexed |
| gmDesignation | GM Designation | GM Designation (AR) | Text | String | true | true |  |  |
| salutationHeading | Salutation Heading | Salutation Heading (AR) | Text | String | true | true |  |  |
| pageContent | Page Content | Page Content (AR) | RichText | Clob | true | true |  | indexed |
| signatureClosingText | Signature Closing Text | Signature Closing Text (AR) | Text | String | true | true |  |  |
| signatureAvatar | Signature Avatar | الصورة الرمزية للتوقيع | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| publicationStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129397-GENERAL_MANAGER_MESSAGE-STATUS-OPTIONS | indexed |

### QCDEMO-129398

Objects: `BoardMember`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| BoardMember | QCDEMO-129398-board-member | 80051 | Board Member | عضو مجلس الإدارة | Board Members | fullName | 12 | 5 |  |

**BoardMember** (`QCDEMO-129398-board-member`, id 80051) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| memberCategory | Member Category | فئة العضو | Picklist | String | true | false | QCDEMO-129398-BOARD_MEMBER-memberCategory-OPTIONS | indexed |
| fullName | Full Name | الاسم الكامل | Text | String | true | true |  | indexed |
| positionLabel | Position Label | المسمى الوظيفي | Text | String | true | true |  |  |
| roleBadgeLabel | Role Badge Label | نص شارة الدور | Text | String | false | true |  |  |
| memberPhoto | Member Photo | صورة العضو | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| photoAltText | Photo Alt Text | النص البديل للصورة | Text | String | false | true |  |  |
| shortBio | Short Bio | نبذة مختصرة | LongText | Clob | true | true |  |  |
| detailedBiography | Detailed Biography | السيرة الذاتية التفصيلية | RichText | Clob | false | true |  |  |
| professionalExperienceEntries | Professional Experience Entries | الخبرات المهنية | LongText | Clob | false | true |  |  |
| enableShareIcons | Enable Share Icons | تفعيل أيقونات المشاركة | Boolean | Boolean | false | false |  |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | false | false |  |  |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

Validation rules on **BoardMember**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Full Name Max Length | `length(fullName) <= 150` | Full Name must not exceed 150 characters. | يجب ألا يتجاوز الاسم الكامل 150 حرفًا. |
| Position Label Max Length | `length(positionLabel) <= 100` | Position Label must not exceed 100 characters. | يجب ألا يتجاوز المسمى الوظيفي 100 حرف. |
| Role Badge Label Max Length | `equals(roleBadgeLabel, "") \|\| length(roleBadgeLabel) <= 100` | Role Badge Label must not exceed 100 characters. | يجب ألا يتجاوز نص شارة الدور 100 حرف. |
| Photo Alt Text Max Length | `equals(photoAltText, "") \|\| length(photoAltText) <= 150` | Photo Alt Text must not exceed 150 characters. | يجب ألا يتجاوز النص البديل للصورة 150 حرفًا. |
| Short Bio Max Length | `length(shortBio) <= 400` | Short Bio must not exceed 400 characters. | يجب ألا تتجاوز النبذة المختصرة 400 حرف. |

### QCDEMO-129399

Objects: `Department`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| Department | QCDEMO-129399-department | 80610 | Department | قسم | Departments | departmentNameEn | 12 | 9 |  |

**Department** (`QCDEMO-129399-department`, id 80610) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| departmentNameEn | Department Name (EN) | اسم القسم (إنجليزي) | Text | String | true | false |  | indexed |
| departmentNameAr | Department Name (AR) | اسم القسم (عربي) | Text | String | true | false |  | indexed |
| parentDepartment | Parent Department | القسم الأصل | LongInteger | Long | false | false |  |  |
| personNameEn | Person Name (EN) | اسم الشخص (إنجليزي) | Text | String | true | false |  | indexed |
| personNameAr | Person Name (AR) | اسم الشخص (عربي) | Text | String | true | false |  | indexed |
| personTitleEn | Person Title (EN) | المسمى الوظيفي (إنجليزي) | Text | String | true | false |  |  |
| personTitleAr | Person Title (AR) | المسمى الوظيفي (عربي) | Text | String | true | false |  |  |
| personPhoto | Person Photo | صورة الشخص | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| departmentDescriptionEn | Department Description (EN) | وصف القسم (إنجليزي) | LongText | Clob | false | false |  |  |
| departmentDescriptionAr | Department Description (AR) | وصف القسم (عربي) | LongText | Clob | false | false |  |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  |  |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

Validation rules on **Department**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Department Name (EN) Max Length | `length(departmentNameEn) <= 150` | Department Name (EN) must not exceed 150 characters. | يجب ألا يتجاوز اسم القسم (إنجليزي) 150 حرفًا. |
| Department Name (AR) Max Length | `length(departmentNameAr) <= 150` | Department Name (AR) must not exceed 150 characters. | يجب ألا يتجاوز اسم القسم (عربي) 150 حرفًا. |
| Person Name (EN) Max Length | `length(personNameEn) <= 150` | Person Name (EN) must not exceed 150 characters. | يجب ألا يتجاوز اسم الشخص (إنجليزي) 150 حرفًا. |
| Person Name (AR) Max Length | `length(personNameAr) <= 150` | Person Name (AR) must not exceed 150 characters. | يجب ألا يتجاوز اسم الشخص (عربي) 150 حرفًا. |
| Person Title (EN) Max Length | `length(personTitleEn) <= 150` | Person Title (EN) must not exceed 150 characters. | يجب ألا يتجاوز المسمى الوظيفي (إنجليزي) 150 حرفًا. |
| Person Title (AR) Max Length | `length(personTitleAr) <= 150` | Person Title (AR) must not exceed 150 characters. | يجب ألا يتجاوز المسمى الوظيفي (عربي) 150 حرفًا. |
| Department Description (EN) Max Length | `equals(departmentDescriptionEn, "") \|\| length(departmentDescriptionEn) <= 1000` | Department Description (EN) must not exceed 1000 characters. | يجب ألا يتجاوز وصف القسم (إنجليزي) 1000 حرف. |
| Department Description (AR) Max Length | `equals(departmentDescriptionAr, "") \|\| length(departmentDescriptionAr) <= 1000` | Department Description (AR) must not exceed 1000 characters. | يجب ألا يتجاوز وصف القسم (عربي) 1000 حرف. |
| Display Order Minimum | `displayOrder >= 1` | Display Order must be at least 1. | يجب أن يكون ترتيب العرض 1 على الأقل. |

### QCDEMO-129400

Objects: `MemberService`, `MemberServicesPage`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| MemberService | QCDEMO-129400-MEMBER_SERVICE | 81019 | Member Service | خدمة الأعضاء | Member Services | name | 13 |  |  |
| MemberServicesPage | QCDEMO-129400-MEMBER_SERVICES_PAGE | 81165 | Member Services Page | صفحة خدمات الأعضاء | Member Services Pages | pageTitle | 6 |  |  |

**MemberService** (`QCDEMO-129400-MEMBER_SERVICE`, id 81019) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| name | Service Name | اسم الخدمة | Text | String | true | true |  | indexed |
| shortDescription | Short Description | الوصف المختصر | LongText | Clob | false | true |  | indexed |
| icon | Service Icon | أيقونة الخدمة | Attachment | Long | false | false |  | acceptedFileExtensions=svg, png; fileSource=documentsAndMedia |
| detailIntro | Detail Intro | مقدمة التفاصيل | RichText | Clob | false | true |  | indexed |
| whoThisServiceIsFor | Who This Service Is For | لمن هذه الخدمة | RichText | Clob | false | true |  |  |
| requiredDocuments | Required Documents | المستندات المطلوبة | RichText | Clob | false | true |  |  |
| howToApply | How to Apply | كيفية التقديم | RichText | Clob | false | true |  |  |
| supportingImage | Supporting Image (Detail) | الصورة المساندة (التفاصيل) | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| ctaLabel | CTA Button Label | نص زر الإجراء | Text | String | false | true |  |  |
| ctaRedirectUrl | CTA Redirect URL | رابط تحويل زر الإجراء | Text | String | false | true |  |  |
| ctaOpenBehavior | CTA Open Behavior | سلوك فتح زر الإجراء | Picklist | String | false | false | QCDEMO-129400-MEMBER_SERVICE-CTAOPENBEHAVIOR-OPTIONS |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | false | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  | indexed |

**MemberServicesPage** (`QCDEMO-129400-MEMBER_SERVICES_PAGE`, id 81165) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| pageTitle | Page Title | عنوان الصفحة | Text | String | true | true |  | indexed |
| heroBanner | Hero Banner | البانر الرئيسي | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, png, svg; fileSource=documentsAndMedia |
| sectionHeading | Section Heading | عنوان القسم | Text | String | false | true |  |  |
| introContent | Intro Content | المحتوى التمهيدي | RichText | Clob | false | true |  | indexed |
| supportingImage | Supporting Image (List) | الصورة المساندة (القائمة) | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| publishedStatus | Published | منشور | Boolean | Boolean | false | false |  | indexed |

### QCDEMO-129402

Objects: `ApplyOnlineCTA`, `ATACarnetCTA`, `ATACarnetPage`, `ATAChecklistItem`, `ATACoveredCategory`, `ATAEligibleTile`, `ATAFeeRow`, `ATAMemberCountry`, `ATAOperatingHour`, `ATAQuickFact`, `ATASection`, `CollapsibleSection`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| ApplyOnlineCTA | QCDEMO-129402-APPLY_ONLINE_CTA | 81803 | Apply Online CTA | زر التقديم عبر الإنترنت | Apply Online CTAs | label | 4 | 1 |  |
| ATACarnetCTA | QCDEMO-129402-ATA_CARNET_CTA | 88557 | ATA Carnet CTA | زر إجراء | ATA Carnet CTAs | ctaLabel | 6 |  |  |
| ATACarnetPage | QCDEMO-129402-ATA_CARNET_PAGE | 81663 | ATA Carnet Page | صفحة بطاقة الـ ATA | ATA Carnet Pages | pageTitle | 10 |  |  |
| ATAChecklistItem | QCDEMO-129402-ATA_CHECKLIST_ITEM | 88314 | ATA Checklist Item | عنصر قائمة التحقق | ATA Checklist Items | checklistLabel | 4 |  |  |
| ATACoveredCategory | QCDEMO-129402-ATA_COVERED_CATEGORY | 88263 | ATA Covered Category | فئة البضائع المشمولة | ATA Covered Categories | cardTitle | 6 |  |  |
| ATAEligibleTile | QCDEMO-129402-ATA_ELIGIBLE_TILE | 88360 | ATA Eligible Tile | فئة المستفيدين | ATA Eligible Tiles | tileLabel | 4 |  |  |
| ATAFeeRow | QCDEMO-129402-ATA_FEE_ROW | 88460 | ATA Fee Row | بند رسوم | ATA Fee Rows | feeItem | 6 |  |  |
| ATAMemberCountry | QCDEMO-129402-ATA_MEMBER_COUNTRY | 88409 | ATA Member Country | دولة عضو | ATA Member Countries | countryName | 5 |  |  |
| ATAOperatingHour | QCDEMO-129402-ATA_OPERATING_HOUR | 88509 | ATA Operating Hour | ساعات العمل | ATA Operating Hours | activityTitle | 6 |  |  |
| ATAQuickFact | QCDEMO-129402-ATA_QUICK_FACT | 88159 | ATA Quick Fact | معلومة سريعة | ATA Quick Facts | factLabel | 5 |  |  |
| ATASection | QCDEMO-129402-ATA_SECTION | 88209 | ATA Section | قسم الصفحة | ATA Sections | sectionTitle | 9 |  |  |
| CollapsibleSection | QCDEMO-129402-COLLAPSIBLE_SECTION | 81753 | Collapsible Section | القسم القابل للطي | Collapsible Sections | sectionTitle | 7 | 2 |  |

**ApplyOnlineCTA** (`QCDEMO-129402-APPLY_ONLINE_CTA`, id 81803) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| label | Label | التسمية | Text | String | true | true |  |  |
| externalRedirectUrl | External Redirect URL | رابط التحويل الخارجي | Text | String | true | false |  |  |
| openBehavior | Open Behavior | سلوك الفتح | Picklist | String | true | false | QCDEMO-129402-APPLY_ONLINE_CTA-OPENBEHAVIOR-OPTIONS |  |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

Validation rules on **ApplyOnlineCTA**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| External Redirect URL Format | `match(externalRedirectUrl, "^(https?)://.+")` | Please enter a valid URL. | يرجى إدخال رابط صالح. |

**ATACarnetCTA** (`QCDEMO-129402-ATA_CARNET_CTA`, id 88557) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| ctaKey | CTA Key | مفتاح الزر | Text | String | true | false |  | indexed |
| ctaLabel | Label | التسمية | Text | String | true | true |  | indexed |
| externalRedirectUrl | External Redirect URL | رابط التحويل الخارجي | Text | String | false | false |  |  |
| openBehavior | Open Behavior | سلوك الفتح | Picklist | String | true | false | QCDEMO-129402-APPLY_ONLINE_CTA-OPENBEHAVIOR-OPTIONS |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

**ATACarnetPage** (`QCDEMO-129402-ATA_CARNET_PAGE`, id 81663) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| pageTitle | Page Title | عنوان الصفحة | Text | String | true | true |  | indexed |
| heroBanner | Hero Banner | البانر الرئيسي | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| serviceDescription | Service Description | وصف الخدمة | RichText | Clob | false | true |  | indexed |
| pageStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129402-ATA_CARNET_PAGE-STATUS-OPTIONS |  |
| eyebrowLabel | Eyebrow Label | التسمية العلوية | Text | String | true | true |  | indexed |
| heroDescription | Hero Description | وصف الخدمة | RichText | Clob | true | true |  | indexed |
| heroImage | Hero Image | صورة الغلاف | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| bannerEyebrow | Banner Eyebrow | التسمية العلوية للبانر | Text | String | false | true |  | indexed |
| bannerHeading | Banner Heading | عنوان البانر | Text | String | true | true |  | indexed |
| bannerBody | Banner Body | نص البانر | RichText | Clob | false | true |  | indexed |

**ATAChecklistItem** (`QCDEMO-129402-ATA_CHECKLIST_ITEM`, id 88314) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| cardKey | Card Key | مفتاح البطاقة | Text | String | true | false |  | indexed |
| checklistLabel | Checklist Label | نص العنصر | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

**ATACoveredCategory** (`QCDEMO-129402-ATA_COVERED_CATEGORY`, id 88263) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| cardKey | Card Key | مفتاح البطاقة | Text | String | true | false |  | indexed |
| cardIcon | Card Icon | أيقونة البطاقة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| cardTitle | Card Title | عنوان البطاقة | Text | String | true | true |  | indexed |
| cardDescription | Card Description | وصف البطاقة | RichText | Clob | false | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

**ATAEligibleTile** (`QCDEMO-129402-ATA_ELIGIBLE_TILE`, id 88360) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| tileIcon | Tile Icon | أيقونة الفئة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| tileLabel | Tile Label | اسم الفئة | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

**ATAFeeRow** (`QCDEMO-129402-ATA_FEE_ROW`, id 88460) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| feeItem | Fee Item | بند الرسوم | Text | String | true | true |  | indexed |
| memberAmount | Member Amount | رسوم الأعضاء | Integer | Integer | true | false |  |  |
| nonMemberAmount | Non-Member Amount | رسوم غير الأعضاء | Integer | Integer | true | false |  |  |
| currency | Currency | العملة | Picklist | String | true | false | QCDEMO-129402-ATA_FEE_ROW-CURRENCY-OPTIONS |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

**ATAMemberCountry** (`QCDEMO-129402-ATA_MEMBER_COUNTRY`, id 88409) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| countryFlag | Country Flag | علم الدولة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| countryName | Country Name | اسم الدولة | Text | String | true | true |  | indexed |
| countryNote | Country Note | ملاحظة | Text | String | false | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

**ATAOperatingHour** (`QCDEMO-129402-ATA_OPERATING_HOUR`, id 88509) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| dayRange | Day Range | نطاق الأيام | Text | String | true | true |  | indexed |
| activityTitle | Activity Title | النشاط | Text | String | true | true |  | indexed |
| timeRange | Time | التوقيت | Text | String | true | true |  | indexed |
| hoursStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129402-ATA_OPERATING_HOUR-STATUS-OPTIONS |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

**ATAQuickFact** (`QCDEMO-129402-ATA_QUICK_FACT`, id 88159) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| icon | Icon | الأيقونة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| factLabel | Label | التسمية | Text | String | true | true |  | indexed |
| factValue | Value | القيمة | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

**ATASection** (`QCDEMO-129402-ATA_SECTION`, id 88209) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionKey | Section Key | مفتاح القسم | Text | String | true | false |  | indexed |
| anchorLabel | Anchor Label | تسمية الفهرس | Text | String | true | true |  | indexed |
| sectionBadge | Section Badge | شارة القسم | Text | String | false | true |  | indexed |
| sectionTitle | Title | العنوان | Text | String | true | true |  | indexed |
| sectionIntro | Section Intro | مقدمة القسم | RichText | Clob | false | true |  | indexed |
| sectionBody | Section Body | محتوى القسم | RichText | Clob | false | true |  | indexed |
| sectionIcon | Section Icon | أيقونة القسم | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |

**CollapsibleSection** (`QCDEMO-129402-COLLAPSIBLE_SECTION`, id 81753) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionTitle | Section Title | عنوان القسم | Text | String | true | true |  | indexed |
| sectionContent | Section Content | محتوى القسم | RichText | Clob | true | true |  | indexed |
| downloadableDocument | Downloadable Document | مستند قابل للتنزيل | Attachment | Long | false | false |  | acceptedFileExtensions=pdf, doc, docx, xls, xlsx; fileSource=documentsAndMedia |
| redirectUrl | Redirect URL | رابط التحويل | Text | String | false | false |  |  |
| openBehaviour | Open Behaviour | سلوك الفتح | Picklist | String | false | false | QCDEMO-129402-COLLAPSIBLE_SECTION-OPENBEHAVIOUR-OPTIONS |  |
| activeStatus | Active Status | الحالة النشطة | Boolean | Boolean | false | false |  |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | false | false |  |  |

Validation rules on **CollapsibleSection**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Redirect URL Format | `isEmpty(redirectUrl) \|\| match(redirectUrl, "^(https?)://.+")` | Please enter a valid URL. | يرجى إدخال رابط صالح. |
| Display Order Positive | `isEmpty(displayOrder) \|\| (displayOrder >= 1)` | Display order must be a positive number. | يجب أن يكون ترتيب العرض رقماً موجباً. |

### QCDEMO-129403

Objects: `TIRBenefitCard`, `TIRCarnetPage`, `TIRCriteria`, `TIRFaqItem`, `TIRPrepareItem`, `TIRProcessStep`, `TIRQuickFact`, `TIRResource`, `TIRSection`, `TIRStatistic`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| TIRBenefitCard | QCDEMO-129403-TIR_BENEFIT_CARD | 88768 | TIR Benefit Card | بطاقة ميزة | TIR Benefit Cards | cardTitle | 5 | 1 |  |
| TIRCarnetPage | QCDEMO-129403-TIR_CARNET_PAGE | 82292 | TIR Carnet Page | صفحة بطاقة TIR | TIR Carnet Pages | pageTitle | 7 | 3 |  |
| TIRCriteria | QCDEMO-129403-TIR_CRITERIA | 88819 | TIR Eligibility Criteria | معيار أهلية | TIR Eligibility Criteria | criteriaLabel | 3 | 1 |  |
| TIRFaqItem | QCDEMO-129403-TIR_FAQ_ITEM | 89398 | TIR FAQ Item | سؤال شائع | TIR FAQ Items | question | 4 | 1 |  |
| TIRPrepareItem | QCDEMO-129403-TIR_PREPARE_ITEM | 89304 | TIR Prepare Item | مستند مطلوب | TIR Prepare Items | itemLabel | 3 | 1 |  |
| TIRProcessStep | QCDEMO-129403-TIR_PROCESS_STEP | 89350 | TIR Process Step | خطوة | TIR Process Steps | stepTitle | 5 | 1 |  |
| TIRQuickFact | QCDEMO-129403-TIR_QUICK_FACT | 88607 | TIR Quick Fact | معلومة سريعة | TIR Quick Facts | factValue | 5 | 2 |  |
| TIRResource | QCDEMO-129403-TIR_RESOURCE | 89445 | TIR Downloadable Resource | مورد قابل للتنزيل | TIR Downloadable Resources | resourceTitle | 7 | 2 |  |
| TIRSection | QCDEMO-129403-TIR_SECTION | 88660 | TIR Section | قسم الصفحة | TIR Sections | sectionTitle | 13 | 2 |  |
| TIRStatistic | QCDEMO-129403-TIR_STATISTIC | 88720 | TIR Statistic | إحصائية | TIR Statistics | statLabel | 4 | 2 |  |

**TIRBenefitCard** (`QCDEMO-129403-TIR_BENEFIT_CARD`, id 88768) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| cardIcon | Card Icon | أيقونة البطاقة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| cardTitle | Card Title | عنوان البطاقة | Text | String | true | true |  | indexed |
| cardDescription | Card Description | وصف البطاقة | RichText | Clob | false | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **TIRBenefitCard**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Card Title Maximum Length | `length(cardTitle) <= 100` | Card Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان البطاقة 100 حرفًا. |

**TIRCarnetPage** (`QCDEMO-129403-TIR_CARNET_PAGE`, id 82292) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| pageTitle | Page Title | عنوان الصفحة | Text | String | true | true |  | indexed |
| heroBanner | Hero Banner | البانر الرئيسي | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| serviceDescription | Service Description | وصف الخدمة | RichText | Clob | false | true |  | indexed |
| pageStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129403-TIR_CARNET_PAGE-STATUS-OPTIONS |  |
| eyebrowLabel | Eyebrow Label | التسمية العلوية | Text | String | true | true |  | indexed |
| heroDescription | Hero Description | وصف الخدمة | RichText | Clob | true | true |  | indexed |
| heroImage | Hero Image | صورة الخدمة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |

Validation rules on **TIRCarnetPage**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Page Title Max Length | `isEmpty(pageTitle) \|\| (length(pageTitle) <= 100)` | Page title must not exceed 100 characters. | يجب ألا يتجاوز عنوان الصفحة 100 حرف. |
| Page Title Maximum Length | `length(pageTitle) <= 100` | Page Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان الصفحة 100 حرفًا. |
| Eyebrow Label Maximum Length | `length(eyebrowLabel) <= 60` | Eyebrow Label must not exceed 60 characters. | يجب ألا يتجاوز التسمية العلوية 60 حرفًا. |

**TIRCriteria** (`QCDEMO-129403-TIR_CRITERIA`, id 88819) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| criteriaLabel | Criteria Label | نص المعيار | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **TIRCriteria**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Criteria Label Maximum Length | `length(criteriaLabel) <= 250` | Criteria Label must not exceed 250 characters. | يجب ألا يتجاوز نص المعيار 250 حرفًا. |

**TIRFaqItem** (`QCDEMO-129403-TIR_FAQ_ITEM`, id 89398) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| question | Question | السؤال | Text | String | true | true |  | indexed |
| answer | Answer | الإجابة | RichText | Clob | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **TIRFaqItem**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Question Maximum Length | `length(question) <= 250` | Question must not exceed 250 characters. | يجب ألا يتجاوز السؤال 250 حرفًا. |

**TIRPrepareItem** (`QCDEMO-129403-TIR_PREPARE_ITEM`, id 89304) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| itemLabel | Item Label | نص العنصر | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **TIRPrepareItem**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Item Label Maximum Length | `length(itemLabel) <= 250` | Item Label must not exceed 250 characters. | يجب ألا يتجاوز نص العنصر 250 حرفًا. |

**TIRProcessStep** (`QCDEMO-129403-TIR_PROCESS_STEP`, id 89350) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| stepNumber | Step Number | رقم الخطوة | Text | String | true | false |  |  |
| stepTitle | Step Title | عنوان الخطوة | Text | String | true | true |  | indexed |
| stepDescription | Step Description | وصف الخطوة | RichText | Clob | false | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **TIRProcessStep**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Step Title Maximum Length | `length(stepTitle) <= 100` | Step Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان الخطوة 100 حرفًا. |

**TIRQuickFact** (`QCDEMO-129403-TIR_QUICK_FACT`, id 88607) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| icon | Icon | الأيقونة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| factLabel | Label | التسمية | Text | String | true | true |  | indexed |
| factValue | Value | القيمة | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **TIRQuickFact**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Label Maximum Length | `length(factLabel) <= 60` | Label must not exceed 60 characters. | يجب ألا يتجاوز التسمية 60 حرفًا. |
| Value Maximum Length | `length(factValue) <= 120` | Value must not exceed 120 characters. | يجب ألا يتجاوز القيمة 120 حرفًا. |

**TIRResource** (`QCDEMO-129403-TIR_RESOURCE`, id 89445) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| resourceTitle | Resource Title | عنوان المورد | Text | String | true | true |  | indexed |
| resourceFile | Resource File | الملف | Attachment | Long | false | false |  | acceptedFileExtensions=pdf; fileSource=documentsAndMedia |
| fileType | File Type | نوع الملف | Text | String | false | false |  |  |
| fileSize | File Size | حجم الملف | Text | String | false | false |  |  |
| downloadLabel | Download Label | تسمية زر التنزيل | Text | String | false | true |  |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **TIRResource**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Resource Title Maximum Length | `length(resourceTitle) <= 150` | Resource Title must not exceed 150 characters. | يجب ألا يتجاوز عنوان المورد 150 حرفًا. |
| Download Label Maximum Length | `length(downloadLabel) <= 40` | Download Label must not exceed 40 characters. | يجب ألا يتجاوز تسمية زر التنزيل 40 حرفًا. |

**TIRSection** (`QCDEMO-129403-TIR_SECTION`, id 88660) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionKey | Section Key | مفتاح القسم | Text | String | true | false |  | indexed |
| sectionNumber | Section Number | رقم القسم | Text | String | false | false |  |  |
| anchorLabel | Index Label | تسمية الفهرس | Text | String | false | true |  | indexed |
| sectionBadge | Section Badge | شارة القسم | Text | String | false | true |  | indexed |
| sectionTitle | Section Title | عنوان القسم | Text | String | true | true |  | indexed |
| sectionIcon | Section Icon | أيقونة القسم | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| sectionBody | Section Body | محتوى القسم | RichText | Clob | false | true |  | indexed |
| videoUrl | Embedded Video URL | رابط الفيديو | Text | String | false | true |  |  |
| boxLabel | Box Label | عنوان الصندوق | Text | String | false | true |  | indexed |
| boxIntro | Box Intro | مقدمة الصندوق | RichText | Clob | false | true |  | indexed |
| openBehaviour | Open Behavior | سلوك الفتح | Picklist | String | false | false | QCDEMO-129403-TIR_SECTION-OPEN-BEHAVIOUR |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **TIRSection**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Section Title Maximum Length | `length(sectionTitle) <= 100` | Section Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان القسم 100 حرفًا. |
| Section Badge Maximum Length | `length(sectionBadge) <= 100` | Section Badge must not exceed 100 characters. | يجب ألا يتجاوز شارة القسم 100 حرفًا. |

**TIRStatistic** (`QCDEMO-129403-TIR_STATISTIC`, id 88720) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| statValue | Value | القيمة | Text | String | true | true |  | indexed |
| statLabel | Label | التسمية | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **TIRStatistic**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Value Maximum Length | `length(statValue) <= 20` | Value must not exceed 20 characters. | يجب ألا يتجاوز القيمة 20 حرفًا. |
| Label Maximum Length | `length(statLabel) <= 80` | Label must not exceed 80 characters. | يجب ألا يتجاوز التسمية 80 حرفًا. |

### QCDEMO-129404

Objects: `ConsultationRequest`, `LegalConsultationPage`, `LegalCriteria`, `LegalFaqItem`, `LegalInfoCard`, `LegalProcessStep`, `LegalQuickFact`, `LegalScopeItem`, `LegalSection`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| ConsultationRequest | QCDEMO-129404-CONSULTATION_REQUEST | 82565 | Consultation Request | طلب استشارة | Consultation Requests | subject | 11 | 5 |  |
| LegalConsultationPage | QCDEMO-129404-LEGAL_PAGE | 89623 | Legal Consultation Page | صفحة الاستشارة القانونية | Legal Consultation Page | pageTitle | 13 | 5 |  |
| LegalCriteria | QCDEMO-129404-LEGAL_CRITERIA | 89848 | Legal Eligibility Criteria | معيار الأهلية | Legal Eligibility Criteria | criteriaLabel | 3 | 1 |  |
| LegalFaqItem | QCDEMO-129404-LEGAL_FAQ_ITEM | 89990 | Legal FAQ Item | سؤال شائع | Legal FAQ Items | question | 4 | 1 |  |
| LegalInfoCard | QCDEMO-129404-LEGAL_INFO_CARD | 89797 | Legal Info Card | بطاقة معلومات | Legal Info Cards | cardTitle | 5 | 1 |  |
| LegalProcessStep | QCDEMO-129404-LEGAL_PROCESS_STEP | 89942 | Legal Process Step | خطوة المعالجة | Legal Process Steps | stepTitle | 5 | 1 |  |
| LegalQuickFact | QCDEMO-129404-LEGAL_QUICK_FACT | 89686 | Legal Quick Fact | معلومة سريعة | Legal Quick Facts | factLabel | 5 | 2 |  |
| LegalScopeItem | QCDEMO-129404-LEGAL_SCOPE_ITEM | 89895 | Legal Scope Item | عنصر النطاق | Legal Scope Items | scopeText | 4 | 1 |  |
| LegalSection | QCDEMO-129404-LEGAL_SECTION | 89739 | Legal Section | قسم الاستشارة القانونية | Legal Sections | sectionTitle | 10 | 3 |  |

**ConsultationRequest** (`QCDEMO-129404-CONSULTATION_REQUEST`, id 82565) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| fullName | Full Name | الاسم الكامل | Text | String | true | false |  |  |
| companyName | Company Name | اسم الشركة | Text | String | true | false |  |  |
| email | Email | البريد الإلكتروني | Text | String | true | false |  |  |
| phone | Phone | رقم الهاتف | Text | String | true | false |  |  |
| legalIssueCategory | Legal Issue Category | فئة القضية القانونية | Picklist | String | true | false | QCDEMO-129404-CONSULTATION_REQUEST-LEGALISSUECATEGORY-OPTIONS |  |
| legalIssueCategoryOther | Legal Issue Category - Other | فئة القضية القانونية - أخرى | Text | String | false | false |  |  |
| subject | Subject | الموضوع | Text | String | true | false |  |  |
| description | Description | الوصف | LongText | Clob | true | false |  |  |
| attachment | Attachment | المرفق | Attachment | Long | false | false |  | acceptedFileExtensions=pdf, docx; fileSource=documentsAndMedia |
| submissionDate | Submission Date | تاريخ التقديم | Date | Date | false | false |  |  |
| requestStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129404-CONSULTATION_REQUEST-STATUS-OPTIONS |  |

Validation rules on **ConsultationRequest**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Full Name Max Length | `isEmpty(fullName) \|\| match(fullName, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Company Name Max Length | `isEmpty(companyName) \|\| match(companyName, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Subject Max Length | `isEmpty(subject) \|\| match(subject, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Description Max Length | `isEmpty(description) \|\| match(description, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Legal Issue Category - Other Max Length | `isEmpty(legalIssueCategoryOther) \|\| match(legalIssueCategoryOther, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |

**LegalConsultationPage** (`QCDEMO-129404-LEGAL_PAGE`, id 89623) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| eyebrowLabel | Eyebrow Label | التسمية العلوية | Text | String | true | true |  | indexed |
| pageTitle | Page Title | عنوان الصفحة | Text | String | true | true |  | indexed |
| heroDescription | Hero Description | وصف الصفحة | RichText | Clob | true | true |  | indexed |
| heroImage | Hero Image | صورة الصفحة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| ctaLabel | CTA Label | نص زر الإجراء | Text | String | true | true |  | indexed |
| ctaRedirectUrl | CTA Redirect URL | رابط زر الإجراء | Text | String | false | false |  |  |
| ctaOpenBehaviour | CTA Open Behaviour | سلوك فتح زر الإجراء | Picklist | String | true | false | QCDEMO-129404-LEGAL_CTA-OPENBEHAVIOUR-OPTIONS |  |
| ctaActiveStatus | CTA Active Status | حالة زر الإجراء | Boolean | Boolean | false | false |  |  |
| bannerEyebrow | Banner Eyebrow | التسمية العلوية للبانر | Text | String | false | true |  | indexed |
| bannerHeading | Banner Heading | عنوان البانر | Text | String | false | true |  | indexed |
| bannerBody | Banner Body | نص البانر | RichText | Clob | false | true |  | indexed |
| bannerActiveStatus | Banner Active Status | حالة البانر | Boolean | Boolean | false | false |  |  |
| pageStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129404-LEGAL_PAGE-STATUS-OPTIONS |  |

Validation rules on **LegalConsultationPage**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Eyebrow Label Maximum Length | `length(eyebrowLabel) <= 60` | Eyebrow Label must not exceed 60 characters. | يجب ألا يتجاوز التسمية العلوية 60 حرفًا. |
| Page Title Maximum Length | `length(pageTitle) <= 100` | Page Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان الصفحة 100 حرفًا. |
| CTA Label Maximum Length | `length(ctaLabel) <= 100` | CTA Label must not exceed 100 characters. | يجب ألا يتجاوز نص زر الإجراء 100 حرفًا. |
| Banner Eyebrow Maximum Length | `length(bannerEyebrow) <= 60` | Banner Eyebrow must not exceed 60 characters. | يجب ألا يتجاوز التسمية العلوية للبانر 60 حرفًا. |
| Banner Heading Maximum Length | `length(bannerHeading) <= 150` | Banner Heading must not exceed 150 characters. | يجب ألا يتجاوز عنوان البانر 150 حرفًا. |

**LegalCriteria** (`QCDEMO-129404-LEGAL_CRITERIA`, id 89848) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| criteriaLabel | Criteria Label | نص المعيار | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **LegalCriteria**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Criteria Label Maximum Length | `length(criteriaLabel) <= 250` | Criteria Label must not exceed 250 characters. | يجب ألا يتجاوز نص المعيار 250 حرفًا. |

**LegalFaqItem** (`QCDEMO-129404-LEGAL_FAQ_ITEM`, id 89990) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| question | Question | السؤال | Text | String | true | true |  | indexed |
| answer | Answer | الإجابة | RichText | Clob | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **LegalFaqItem**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Question Maximum Length | `length(question) <= 250` | Question must not exceed 250 characters. | يجب ألا يتجاوز السؤال 250 حرفًا. |

**LegalInfoCard** (`QCDEMO-129404-LEGAL_INFO_CARD`, id 89797) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| cardIcon | Card Icon | أيقونة البطاقة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| cardTitle | Card Title | عنوان البطاقة | Text | String | true | true |  | indexed |
| cardDescription | Card Description | وصف البطاقة | RichText | Clob | false | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **LegalInfoCard**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Card Title Maximum Length | `length(cardTitle) <= 100` | Card Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان البطاقة 100 حرفًا. |

**LegalProcessStep** (`QCDEMO-129404-LEGAL_PROCESS_STEP`, id 89942) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| stepNumber | Step Number | رقم الخطوة | Text | String | false | false |  |  |
| stepTitle | Step Title | عنوان الخطوة | Text | String | true | true |  | indexed |
| stepDescription | Step Description | وصف الخطوة | RichText | Clob | false | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **LegalProcessStep**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Step Title Maximum Length | `length(stepTitle) <= 100` | Step Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان الخطوة 100 حرفًا. |

**LegalQuickFact** (`QCDEMO-129404-LEGAL_QUICK_FACT`, id 89686) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| icon | Icon | الأيقونة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| factLabel | Label | التسمية | Text | String | true | true |  | indexed |
| factValue | Value | القيمة | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **LegalQuickFact**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Label Maximum Length | `length(factLabel) <= 60` | Label must not exceed 60 characters. | يجب ألا يتجاوز التسمية 60 حرفًا. |
| Value Maximum Length | `length(factValue) <= 120` | Value must not exceed 120 characters. | يجب ألا يتجاوز القيمة 120 حرفًا. |

**LegalScopeItem** (`QCDEMO-129404-LEGAL_SCOPE_ITEM`, id 89895) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| scopeGroup | Scope Group | مجموعة النطاق | Picklist | String | true | false | QCDEMO-129404-LEGAL_SCOPE-GROUP-OPTIONS |  |
| scopeText | Scope Item | نص العنصر | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **LegalScopeItem**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Scope Item Maximum Length | `length(scopeText) <= 300` | Scope Item must not exceed 300 characters. | يجب ألا يتجاوز نص العنصر 300 حرفًا. |

**LegalSection** (`QCDEMO-129404-LEGAL_SECTION`, id 89739) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionKey | Section Key | مفتاح القسم | Text | String | true | false |  |  |
| sectionNumber | Section Number | رقم القسم | Text | String | false | false |  |  |
| anchorLabel | Index Label | تسمية الفهرس | Text | String | true | true |  | indexed |
| sectionBadge | Section Badge | شارة القسم | Text | String | false | true |  | indexed |
| sectionTitle | Section Title | عنوان القسم | Text | String | true | true |  | indexed |
| sectionBody | Section Body | نص القسم | RichText | Clob | false | true |  | indexed |
| sectionIcon | Section Icon | أيقونة القسم | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| openBehaviour | Accordion Open Behaviour | سلوك فتح الأسئلة | Picklist | String | false | false | QCDEMO-129404-LEGAL_FAQ-OPENBEHAVIOUR-OPTIONS |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **LegalSection**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Index Label Maximum Length | `length(anchorLabel) <= 100` | Index Label must not exceed 100 characters. | يجب ألا يتجاوز تسمية الفهرس 100 حرفًا. |
| Section Badge Maximum Length | `length(sectionBadge) <= 100` | Section Badge must not exceed 100 characters. | يجب ألا يتجاوز شارة القسم 100 حرفًا. |
| Section Title Maximum Length | `length(sectionTitle) <= 100` | Section Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان القسم 100 حرفًا. |

### QCDEMO-129405

Objects: `MediationBenefitCard`, `MediationCriteria`, `MediationFaqItem`, `MediationPage`, `MediationPrepareItem`, `MediationProcessStep`, `MediationQuickFact`, `MediationRequest`, `MediationSection`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| MediationBenefitCard | QCDEMO-129405-MEDIATION_BENEFIT_CARD | 90574 | Mediation Benefit Card | بطاقة ميزة الوساطة | Mediation Benefit Cards | cardTitle | 5 | 1 |  |
| MediationCriteria | QCDEMO-129405-MEDIATION_CRITERIA | 90625 | Mediation Eligibility Criterion | معيار أهلية الوساطة | Mediation Eligibility Criteria | criteriaLabel | 3 | 1 |  |
| MediationFaqItem | QCDEMO-129405-MEDIATION_FAQ_ITEM | 90765 | Mediation FAQ Item | سؤال شائع عن الوساطة | Mediation FAQ Items | question | 4 | 1 |  |
| MediationPage | QCDEMO-129405-MEDIATION_PAGE | 90039 | Mediation Page | صفحة الوساطة | Mediation Page | pageTitle | 14 | 6 |  |
| MediationPrepareItem | QCDEMO-129405-MEDIATION_PREPARE_ITEM | 90671 | Mediation Prepare Item | عنصر تحضير للوساطة | Mediation Prepare Items | itemLabel | 3 | 1 |  |
| MediationProcessStep | QCDEMO-129405-MEDIATION_PROCESS_STEP | 90717 | Mediation Process Step | خطوة عملية الوساطة | Mediation Process Steps | stepTitle | 5 | 1 |  |
| MediationQuickFact | QCDEMO-129405-MEDIATION_QUICK_FACT | 90104 | Mediation Quick Fact | معلومة سريعة للوساطة | Mediation Quick Facts | factLabel | 5 | 2 |  |
| MediationRequest | QCDEMO-129405-MEDIATION_REQUEST | 83298 | Mediation Request | طلب الوساطة | Mediation Requests | applicantCompanyName | 33 | 10 |  |
| MediationSection | QCDEMO-129405-MEDIATION_SECTION | 90512 | Mediation Section | قسم الوساطة | Mediation Sections | sectionTitle | 12 | 5 |  |

**MediationBenefitCard** (`QCDEMO-129405-MEDIATION_BENEFIT_CARD`, id 90574) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| cardIcon | Card Icon | أيقونة البطاقة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| cardTitle | Card Title | عنوان البطاقة | Text | String | true | true |  | indexed |
| cardDescription | Card Description | وصف البطاقة | RichText | Clob | false | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **MediationBenefitCard**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Card Title Maximum Length | `length(cardTitle) <= 100` | Card Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان البطاقة 100 حرفًا. |

**MediationCriteria** (`QCDEMO-129405-MEDIATION_CRITERIA`, id 90625) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| criteriaLabel | Criteria Label | نص المعيار | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **MediationCriteria**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Criteria Label Maximum Length | `length(criteriaLabel) <= 500` | Criteria Label must not exceed 500 characters. | يجب ألا يتجاوز نص المعيار 500 حرفًا. |

**MediationFaqItem** (`QCDEMO-129405-MEDIATION_FAQ_ITEM`, id 90765) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| question | Question | السؤال | Text | String | true | true |  | indexed |
| answer | Answer | الإجابة | RichText | Clob | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **MediationFaqItem**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Question Maximum Length | `length(question) <= 250` | Question must not exceed 250 characters. | يجب ألا يتجاوز السؤال 250 حرفًا. |

**MediationPage** (`QCDEMO-129405-MEDIATION_PAGE`, id 90039) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| eyebrowLabel | Eyebrow Label | التسمية العلوية | Text | String | true | true |  | indexed |
| pageTitle | Page Title | عنوان الصفحة | Text | String | true | true |  | indexed |
| heroDescription | Hero Description | وصف الصفحة | RichText | Clob | true | true |  | indexed |
| heroImage | Hero Image | صورة الصفحة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| ctaLabel | CTA Label | نص زر الإجراء | Text | String | true | true |  | indexed |
| ctaRedirectUrl | CTA Redirect URL | رابط زر الإجراء | Text | String | false | false |  |  |
| ctaOpenBehaviour | CTA Open Behaviour | سلوك فتح زر الإجراء | Picklist | String | true | false | QCDEMO-129405-MEDIATION_CTA-OPENBEHAVIOUR-OPTIONS |  |
| ctaActiveStatus | CTA Active Status | حالة زر الإجراء | Boolean | Boolean | false | false |  |  |
| requestPageTitle | Request Page Title | عنوان صفحة الطلب | Text | String | false | true |  | indexed |
| bannerEyebrow | Banner Eyebrow | التسمية العلوية للبانر | Text | String | false | true |  | indexed |
| bannerHeading | Banner Heading | عنوان البانر | Text | String | false | true |  | indexed |
| bannerBody | Banner Body | نص البانر | RichText | Clob | false | true |  | indexed |
| bannerActiveStatus | Banner Active Status | حالة البانر | Boolean | Boolean | false | false |  |  |
| pageStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129405-MEDIATION_PAGE-STATUS-OPTIONS |  |

Validation rules on **MediationPage**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Eyebrow Label Maximum Length | `length(eyebrowLabel) <= 60` | Eyebrow Label must not exceed 60 characters. | يجب ألا يتجاوز التسمية العلوية 60 حرفًا. |
| Page Title Maximum Length | `length(pageTitle) <= 120` | Page Title must not exceed 120 characters. | يجب ألا يتجاوز عنوان الصفحة 120 حرفًا. |
| CTA Label Maximum Length | `length(ctaLabel) <= 100` | CTA Label must not exceed 100 characters. | يجب ألا يتجاوز نص زر الإجراء 100 حرفًا. |
| Request Page Title Maximum Length | `length(requestPageTitle) <= 120` | Request Page Title must not exceed 120 characters. | يجب ألا يتجاوز عنوان صفحة الطلب 120 حرفًا. |
| Banner Eyebrow Maximum Length | `length(bannerEyebrow) <= 60` | Banner Eyebrow must not exceed 60 characters. | يجب ألا يتجاوز التسمية العلوية للبانر 60 حرفًا. |
| Banner Heading Maximum Length | `length(bannerHeading) <= 150` | Banner Heading must not exceed 150 characters. | يجب ألا يتجاوز عنوان البانر 150 حرفًا. |

**MediationPrepareItem** (`QCDEMO-129405-MEDIATION_PREPARE_ITEM`, id 90671) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| itemLabel | Prepare Item | عنصر التحضير | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **MediationPrepareItem**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Prepare Item Maximum Length | `length(itemLabel) <= 500` | Prepare Item must not exceed 500 characters. | يجب ألا يتجاوز عنصر التحضير 500 حرفًا. |

**MediationProcessStep** (`QCDEMO-129405-MEDIATION_PROCESS_STEP`, id 90717) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| stepNumber | Step Number | رقم الخطوة | Text | String | false | false |  |  |
| stepTitle | Step Title | عنوان الخطوة | Text | String | true | true |  | indexed |
| stepDescription | Step Description | وصف الخطوة | RichText | Clob | false | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **MediationProcessStep**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Step Title Maximum Length | `length(stepTitle) <= 100` | Step Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان الخطوة 100 حرفًا. |

**MediationQuickFact** (`QCDEMO-129405-MEDIATION_QUICK_FACT`, id 90104) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| icon | Icon | الأيقونة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| factLabel | Fact Label | تسمية المعلومة | Text | String | true | true |  | indexed |
| factValue | Fact Value | قيمة المعلومة | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **MediationQuickFact**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Fact Label Maximum Length | `length(factLabel) <= 60` | Fact Label must not exceed 60 characters. | يجب ألا يتجاوز تسمية المعلومة 60 حرفًا. |
| Fact Value Maximum Length | `length(factValue) <= 120` | Fact Value must not exceed 120 characters. | يجب ألا يتجاوز قيمة المعلومة 120 حرفًا. |

**MediationRequest** (`QCDEMO-129405-MEDIATION_REQUEST`, id 83298) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| applicantCompanyName | Applicant Company Name | اسم شركة مقدم الطلب | Text | String | true | false |  |  |
| crNumber | CR Number | رقم السجل التجاري | Text | String | true | false |  |  |
| membershipNumber | Membership Number | رقم العضوية | Text | String | true | false |  |  |
| contactPerson | Contact Person | الشخص المسؤول | Text | String | true | false |  |  |
| jobTitle | Job Title | المسمى الوظيفي | Text | String | true | false |  |  |
| email | Email | البريد الإلكتروني | Text | String | true | false |  |  |
| mobile | Mobile Number | رقم الجوال | Text | String | true | false |  |  |
| telephone | Telephone | الهاتف | Text | String | false | false |  |  |
| companyAddress | Company Address | عنوان الشركة | Text | String | true | false |  |  |
| country | Country | الدولة | Text | String | true | false |  |  |
| legalRepresentative | Legal Representative | الممثل القانوني | Text | String | false | false |  |  |
| respondentCompanyName | Respondent Company Name | اسم شركة المدعى عليه | Text | String | true | false |  |  |
| respondentContactPerson | Respondent Contact Person | الشخص المسؤول لدى المدعى عليه | Text | String | true | false |  |  |
| respondentEmail | Respondent Email | البريد الإلكتروني للمدعى عليه | Text | String | true | false |  |  |
| respondentPhone | Respondent Phone | هاتف المدعى عليه | Text | String | true | false |  |  |
| respondentAddress | Respondent Address | عنوان المدعى عليه | Text | String | true | false |  |  |
| respondentCountry | Respondent Country | دولة المدعى عليه | Text | String | true | false |  |  |
| respondentCrLicenseNumber | Respondent CR / License Number | رقم السجل / الترخيص للمدعى عليه | Text | String | false | false |  |  |
| disputeCategory | Dispute Category | فئة النزاع | Text | String | true | false |  |  |
| disputeCategoryOther | Dispute Category - Other | فئة النزاع - أخرى | Text | String | false | false |  |  |
| contractReference | Contract / Agreement Reference | مرجع العقد / الاتفاقية | Text | String | true | false |  |  |
| contractDate | Contract Date | تاريخ العقد | Date | Date | true | false |  |  |
| claimAmount | Claim Amount | قيمة المطالبة | PrecisionDecimal | BigDecimal | true | false |  |  |
| currency | Currency | العملة | Text | String | true | false |  |  |
| natureOfDispute | Nature of Dispute | طبيعة النزاع | Text | String | true | false |  |  |
| detailedDisputeSummary | Detailed Dispute Summary | ملخص تفصيلي للنزاع | LongText | Clob | true | false |  |  |
| requestedResolution | Requested Resolution | الحل المطلوب | LongText | Clob | true | false |  |  |
| priorCommunicationAttempts | Prior Communication Attempts | محاولات التواصل السابقة | Boolean | Boolean | false | false |  |  |
| supportingDocuments | Supporting Documents | المستندات الداعمة | Attachment | Long | false | false |  | acceptedFileExtensions=pdf, docx, jpg, png, xlsx, zip; fileSource=documentsAndMedia |
| declaration | Declaration | الإقرار | Boolean | Boolean | false | false |  |  |
| submissionDate | Submission Date | تاريخ التقديم | Date | Date | false | false |  |  |
| caseReferenceNumber | Case Reference Number | الرقم المرجعي للقضية | Text | String | false | false |  |  |
| requestStatus | Status | الحالة | Picklist | String | false | false | QCDEMO-129405-MEDIATION_REQUEST-STATUS-OPTIONS |  |

Validation rules on **MediationRequest**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Applicant Company Name Max Length | `isEmpty(applicantCompanyName) \|\| match(applicantCompanyName, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Contact Person Max Length | `isEmpty(contactPerson) \|\| match(contactPerson, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Job Title Max Length | `isEmpty(jobTitle) \|\| match(jobTitle, "^[\s\S]{0,200}$")` | Please enter no more than 200 characters. | الرجاء إدخال ما لا يزيد عن 200 حرف. |
| Company Address Max Length | `isEmpty(companyAddress) \|\| match(companyAddress, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Legal Representative Max Length | `isEmpty(legalRepresentative) \|\| match(legalRepresentative, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Respondent Company Name Max Length | `isEmpty(respondentCompanyName) \|\| match(respondentCompanyName, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Respondent Contact Person Max Length | `isEmpty(respondentContactPerson) \|\| match(respondentContactPerson, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Respondent Address Max Length | `isEmpty(respondentAddress) \|\| match(respondentAddress, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Dispute Category - Other Max Length | `isEmpty(disputeCategoryOther) \|\| match(disputeCategoryOther, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |
| Nature of Dispute Max Length | `isEmpty(natureOfDispute) \|\| match(natureOfDispute, "^[\s\S]{0,500}$")` | Please enter no more than 500 characters. | الرجاء إدخال ما لا يزيد عن 500 حرف. |

**MediationSection** (`QCDEMO-129405-MEDIATION_SECTION`, id 90512) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionKey | Section Key | مفتاح القسم | Text | String | true | false |  |  |
| sectionNumber | Section Number | رقم القسم | Text | String | false | false |  |  |
| anchorLabel | Index Label | تسمية الفهرس | Text | String | true | true |  | indexed |
| sectionBadge | Section Badge | شارة القسم | Text | String | false | true |  | indexed |
| sectionTitle | Section Title | عنوان القسم | Text | String | true | true |  | indexed |
| sectionBody | Section Body | نص القسم | RichText | Clob | false | true |  | indexed |
| sectionIcon | Section Icon | أيقونة القسم | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| criteriaBoxLabel | Criteria Box Label | عنوان صندوق المعايير | Text | String | false | true |  | indexed |
| prepareBoxLabel | Prepare Box Label | عنوان صندوق التحضير | Text | String | false | true |  | indexed |
| openBehaviour | Accordion Open Behaviour | سلوك فتح الأسئلة | Picklist | String | false | false | QCDEMO-129405-MEDIATION_FAQ-OPENBEHAVIOUR-OPTIONS |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **MediationSection**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Index Label Maximum Length | `length(anchorLabel) <= 100` | Index Label must not exceed 100 characters. | يجب ألا يتجاوز تسمية الفهرس 100 حرفًا. |
| Section Badge Maximum Length | `length(sectionBadge) <= 100` | Section Badge must not exceed 100 characters. | يجب ألا يتجاوز شارة القسم 100 حرفًا. |
| Section Title Maximum Length | `length(sectionTitle) <= 100` | Section Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان القسم 100 حرفًا. |
| Criteria Box Label Maximum Length | `length(criteriaBoxLabel) <= 100` | Criteria Box Label must not exceed 100 characters. | يجب ألا يتجاوز عنوان صندوق المعايير 100 حرفًا. |
| Prepare Box Label Maximum Length | `length(prepareBoxLabel) <= 100` | Prepare Box Label must not exceed 100 characters. | يجب ألا يتجاوز عنوان صندوق التحضير 100 حرفًا. |

### QCDEMO-129406

Objects: `EconomicConsultancyAreaCard`, `EconomicConsultancyFAQItem`, `EconomicConsultancyHighlightItem`, `EconomicConsultancyInfoCard`, `EconomicConsultancyPage`, `EconomicConsultancyQuickFact`, `EconomicConsultancyScopeItem`, `EconomicConsultancySection`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| EconomicConsultancyAreaCard | QCDEMO-129406-EC_AREA_CARD | 91071 | Economic Consultancy Area Card | Economic Consultancy Area Card (AR) | Economic Consultancy Area Cards | cardTitle | 5 |  |  |
| EconomicConsultancyFAQItem | QCDEMO-129406-EC_FAQ_ITEM | 91542 | Economic Consultancy FAQ Item | Economic Consultancy FAQ Item (AR) | Economic Consultancy FAQ Items | question | 4 |  |  |
| EconomicConsultancyHighlightItem | QCDEMO-129406-EC_HIGHLIGHT_ITEM | 91024 | Economic Consultancy Highlight Item | Economic Consultancy Highlight Item (AR) | Economic Consultancy Highlight Items | highlightItem | 3 |  |  |
| EconomicConsultancyInfoCard | QCDEMO-129406-EC_INFO_CARD | 90972 | Economic Consultancy Info Card | Economic Consultancy Info Card (AR) | Economic Consultancy Info Cards | cardTitle | 5 |  |  |
| EconomicConsultancyPage | QCDEMO-129406-EC_PAGE | 90814 | Economic Consultancy Page | Economic Consultancy Page (AR) | Economic Consultancy Page | pageTitle | 10 |  |  |
| EconomicConsultancyQuickFact | QCDEMO-129406-EC_QUICK_FACT | 90869 | Economic Consultancy Quick Fact | Economic Consultancy Quick Fact (AR) | Economic Consultancy Quick Facts | factLabel | 5 |  |  |
| EconomicConsultancyScopeItem | QCDEMO-129406-EC_SCOPE_ITEM | 91124 | Economic Consultancy Scope Item | Economic Consultancy Scope Item (AR) | Economic Consultancy Scope Items | externalReferenceCode | 4 |  |  |
| EconomicConsultancySection | QCDEMO-129406-EC_SECTION | 90921 | Economic Consultancy Section | Economic Consultancy Section (AR) | Economic Consultancy Sections | sectionTitle | 7 |  |  |

**EconomicConsultancyAreaCard** (`QCDEMO-129406-EC_AREA_CARD`, id 91071) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| cardIcon | Card Icon | Card Icon (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| cardTitle | Card Title | Card Title (AR) | Text | String | true | true |  | indexed |
| cardDescription | Card Description | Card Description (AR) | RichText | Clob | true | true |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

**EconomicConsultancyFAQItem** (`QCDEMO-129406-EC_FAQ_ITEM`, id 91542) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| question | Question | Question (AR) | Text | String | true | true |  | indexed |
| answer | Answer | Answer (AR) | RichText | Clob | true | true |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

**EconomicConsultancyHighlightItem** (`QCDEMO-129406-EC_HIGHLIGHT_ITEM`, id 91024) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| highlightItem | Highlight Item | Highlight Item (AR) | Text | String | true | true |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

**EconomicConsultancyInfoCard** (`QCDEMO-129406-EC_INFO_CARD`, id 90972) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| cardIcon | Card Icon | Card Icon (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| cardTitle | Card Title | Card Title (AR) | Text | String | true | true |  | indexed |
| cardDescription | Card Description | Card Description (AR) | RichText | Clob | true | true |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

**EconomicConsultancyPage** (`QCDEMO-129406-EC_PAGE`, id 90814) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| eyebrowLabel | Eyebrow Label | Eyebrow Label (AR) | Text | String | true | true |  | indexed |
| pageTitle | Page Title | Page Title (AR) | Text | String | true | true |  | indexed |
| heroDescription | Hero Description | Hero Description (AR) | RichText | Clob | true | true |  | indexed |
| heroBanner | Hero Banner | Hero Banner (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| heroBannerAltText | Hero Banner Alt Text | Hero Banner Alt Text (AR) | Text | String | true | true |  |  |
| pageStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129406-EC_PAGE_STATUS | indexed |
| overviewBody | Overview Body | Overview Body (AR) | RichText | Clob | true | true |  | indexed |
| overviewHyperlinkUrl | Hyperlink URL | Hyperlink URL (AR) | Text | String | false | false |  |  |
| overviewHyperlinkTarget | Link Target | Link Target (AR) | Picklist | String | false | false | QCDEMO-129406-EC_LINK_TARGET |  |
| overviewSecondaryParagraph | Secondary Paragraph | Secondary Paragraph (AR) | RichText | Clob | true | true |  | indexed |

**EconomicConsultancyQuickFact** (`QCDEMO-129406-EC_QUICK_FACT`, id 90869) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| icon | Icon | Icon (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| factLabel | Label | Label (AR) | Text | String | true | true |  | indexed |
| factValue | Value | Value (AR) | Text | String | true | true |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

**EconomicConsultancyScopeItem** (`QCDEMO-129406-EC_SCOPE_ITEM`, id 91124) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| scopeGroup | Scope Group | Scope Group (AR) | Picklist | String | true | false | QCDEMO-129406-EC_SCOPE_GROUP | indexed |
| scopeText | Scope Item | Scope Item (AR) | RichText | Clob | true | true |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

**EconomicConsultancySection** (`QCDEMO-129406-EC_SECTION`, id 90921) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionKey | Section Key | Section Key (AR) | Text | String | true | false |  |  |
| sectionNumber | Section Number | Section Number (AR) | Text | String | true | false |  |  |
| sectionBadge | Section Badge | Section Badge (AR) | Text | String | false | true |  | indexed |
| sectionTitle | Section Title | Section Title (AR) | Text | String | true | true |  | indexed |
| sectionIntro | Section Intro | Section Intro (AR) | RichText | Clob | false | true |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

### QCDEMO-129407

Objects: `EconomicResearchListingPage`, `EconomicResearchReport`, `QuickFactsTile`, `SectionIndexEntry`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| EconomicResearchListingPage | QCDEMO-129407-ECONOMIC_RESEARCH_LISTING_PAGE | 94225 | Economic Research Listing Page | صفحة قائمة البحوث الاقتصادية | Economic Research Listing Pages | pageTitle | 6 |  |  |
| EconomicResearchReport | QCDEMO-129407-ECONOMIC_RESEARCH_REPORT | 94375 | Economic Research Report | تقرير بحث اقتصادي | Economic Research Reports | reportTitle | 7 |  |  |
| QuickFactsTile | QCDEMO-129407-QUICK_FACTS_TILE | 94276 | Quick Facts Tile | بطاقة حقائق سريعة | Quick Facts Tiles | factLabel | 5 |  |  |
| SectionIndexEntry | QCDEMO-129407-SECTION_INDEX_ENTRY | 94328 | Section Index Entry | عنصر فهرس الأقسام | Section Index Entries | sectionTitle | 3 |  |  |

**EconomicResearchListingPage** (`QCDEMO-129407-ECONOMIC_RESEARCH_LISTING_PAGE`, id 94225) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| eyebrowLabel | Eyebrow Label | النص التمهيدي | Text | String | true | true |  |  |
| pageTitle | Page Title | عنوان الصفحة | Text | String | true | true |  | indexed |
| heroDescription | Hero Description | وصف القسم الرئيسي | RichText | Clob | true | true |  | indexed |
| heroBanner | Hero Banner | لافتة القسم الرئيسي | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| pageIntroContent | Page Intro Content | محتوى مقدمة الصفحة | RichText | Clob | true | true |  | indexed |
| pageStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129407-LT-CONTENT_STATUS | indexed |

**EconomicResearchReport** (`QCDEMO-129407-ECONOMIC_RESEARCH_REPORT`, id 94375) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| reportTitle | Report Title | عنوان التقرير | Text | String | true | true |  | indexed |
| shortDescription | Short Description | وصف مختصر | LongText | Clob | true | true |  | indexed |
| thumbnailImage | Thumbnail Image | الصورة المصغرة | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| pdfAttachment | PDF Attachment | ملف PDF المرفق | Attachment | Long | true | false |  | acceptedFileExtensions=pdf, docx; fileSource=documentsAndMedia |
| publishDate | Publish Date | تاريخ النشر | Date | Date | true | false |  | indexed |
| reportContent | Report Content | محتوى التقرير | RichText | Clob | false | true |  | indexed |
| reportStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129407-LT-CONTENT_STATUS | indexed |

**QuickFactsTile** (`QCDEMO-129407-QUICK_FACTS_TILE`, id 94276) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| icon | Icon | الأيقونة | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| factLabel | Label | التسمية | Text | String | true | true |  | indexed |
| factValue | Value | القيمة | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | حالة التفعيل | Boolean | Boolean | false | false |  |  |

**SectionIndexEntry** (`QCDEMO-129407-SECTION_INDEX_ENTRY`, id 94328) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionTitle | Section Title | عنوان القسم | Text | String | true | true |  | indexed |
| sectionNumbering | Section Numbering | ترقيم القسم | Text | String | true | false |  | indexed |
| activeStatus | Active Status | حالة التفعيل | Boolean | Boolean | false | false |  |  |

### QCDEMO-129566

Objects: `Newsletter`, `NewsletterSubscriber`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| Newsletter | QCDEMO-129566-NEWSLETTER | 46653 | Newsletter | النشرة الإخبارية | Newsletters | title | 11 |  |  |
| NewsletterSubscriber | QCDEMO-129566-NEWSLETTER_SUBSCRIBER | 46600 | Newsletter Subscriber | مشترك النشرة الإخبارية | Newsletter Subscribers | externalReferenceCode | 5 |  |  |

**Newsletter** (`QCDEMO-129566-NEWSLETTER`, id 46653) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| newsletterId | Newsletter ID | معرّف النشرة الإخبارية | Text | String | true | false |  | indexed |
| title | Title | العنوان | Text | String | true | true |  | indexed |
| subjectLine | Subject Line | سطر الموضوع | Text | String | true | true |  | indexed |
| shortDescription | Short Description | وصف مختصر | LongText | Clob | false | true |  |  |
| content | Content | المحتوى | RichText | Clob | true | true |  |  |
| bannerImage | Banner Image | صورة البانر | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, png; fileSource=documentsAndMedia |
| attachments | Attachments | المرفقات | Attachment | Long | false | false |  | acceptedFileExtensions=pdf, doc, docx; fileSource=documentsAndMedia |
| language | Language | اللغة | Picklist | String | true | false | QCDEMO-129566-NEWSLETTER-LANGUAGE-OPTIONS | indexed |
| newsletterStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-129566-NEWSLETTER-STATUS-OPTIONS | indexed |
| publishDate | Publish Date | تاريخ النشر | DateTime | DateTime | false | false |  | indexed |
| expiryDate | Expiry Date | تاريخ الانتهاء | DateTime | DateTime | false | false |  |  |

**NewsletterSubscriber** (`QCDEMO-129566-NEWSLETTER_SUBSCRIBER`, id 46600) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| email | Email | البريد الإلكتروني | Text | String | true | false |  | indexed |
| unsubscribeToken | Unsubscribe Token | رمز إلغاء الاشتراك | Text | String | true | false |  | indexed |
| active | Active Subscription | اشتراك نشط | Boolean | Boolean | false | false |  | indexed |
| lastSubscribedOn | Last Subscribed On | ??? ?????? | DateTime | DateTime | false | false |  | indexed |
| lastUnsubscribedOn | Last Unsubscribed On | ??? ????? ?????? | DateTime | DateTime | false | false |  | indexed |

### QCDEMO-130947

Objects: `COOCta`, `COODocumentRequirement`, `COODownloadCard`, `COOFinderDocument`, `COOFinderOption`, `COOInfoCard`, `COOPageContent`, `COOProcessStep`, `COOQuickFact`, `COOSection`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| COOCta | QCDEMO-130947-COO_CTA | 86720 | COO Call To Action | زر إجراء شهادة المنشأ | COO Calls To Action | ctaLabel | 6 | 2 |  |
| COODocumentRequirement | QCDEMO-130947-COO_DOCUMENT_REQUIREMENT | 86938 | COO Document Requirement | متطلب مستندات | COO Document Requirements | itemTitle | 5 | 2 |  |
| COODownloadCard | QCDEMO-130947-COO_DOWNLOAD_CARD | 87035 | COO Download Card | بطاقة تنزيل | COO Download Cards | cardTitle | 6 | 3 |  |
| COOFinderDocument | QCDEMO-130947-COO_FINDER_DOCUMENT | 87457 | COO Finder Document | مستند الباحث | COO Finder Documents | docTitle | 8 | 2 |  |
| COOFinderOption | QCDEMO-130947-COO_FINDER_OPTION | 87089 | COO Finder Option | خيار الباحث عن المستندات | COO Finder Options | optionLabel | 5 | 1 |  |
| COOInfoCard | QCDEMO-130947-COO_INFO_CARD | 86887 | COO Info Card | بطاقة معلومات | COO Info Cards | cardTitle | 5 | 1 |  |
| COOPageContent | QCDEMO-130947-COO_PAGE_CONTENT | 86628 | COO Page Content | محتوى صفحة شهادة المنشأ | COO Page Content | pageTitle | 9 | 4 |  |
| COOProcessStep | QCDEMO-130947-COO_PROCESS_STEP | 86987 | COO Process Step | خطوة تقديم | COO Process Steps | stepTitle | 5 | 1 |  |
| COOQuickFact | QCDEMO-130947-COO_QUICK_FACT | 86770 | COO Quick Fact | معلومة سريعة | COO Quick Facts | factValue | 5 | 2 |  |
| COOSection | QCDEMO-130947-COO_SECTION | 86822 | COO Section | قسم الصفحة | COO Sections | sectionTitle | 14 | 3 |  |

**COOCta** (`QCDEMO-130947-COO_CTA`, id 86720) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| ctaKey | CTA Key | مُعرّف الزر | Text | String | true | false |  |  |
| ctaLabel | CTA Label | نص الزر | Text | String | true | true |  | indexed |
| redirectUrl | Redirect URL | رابط التحويل | Text | String | false | false |  |  |
| openBehaviour | Open Behavior | سلوك الفتح | Picklist | String | true | false | QCDEMO-130947-COO_CTA-OPENBEHAVIOUR-OPTIONS |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **COOCta**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| CTA Label Maximum Length | `length(ctaLabel) <= 100` | CTA Label must not exceed 100 characters. | يجب ألا يتجاوز نص الزر 100 حرفًا. |
| Redirect URL Format | `contains(redirectUrl, "http")` | Redirect URL must be a valid http(s) address. | يجب أن يكون رابط التحويل عنوانًا صحيحًا يبدأ بـ http. |

**COODocumentRequirement** (`QCDEMO-130947-COO_DOCUMENT_REQUIREMENT`, id 86938) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| itemTitle | Item Title | عنوان العنصر | Text | String | true | true |  | indexed |
| itemSubtitle | Item Subtitle | العنوان الفرعي | Text | String | false | true |  | indexed |
| itemContent | Item Content | محتوى العنصر | RichText | Clob | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **COODocumentRequirement**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Item Title Maximum Length | `length(itemTitle) <= 200` | Item Title must not exceed 200 characters. | يجب ألا يتجاوز عنوان العنصر 200 حرفًا. |
| Item Subtitle Maximum Length | `length(itemSubtitle) <= 200` | Item Subtitle must not exceed 200 characters. | يجب ألا يتجاوز العنوان الفرعي 200 حرفًا. |

**COODownloadCard** (`QCDEMO-130947-COO_DOWNLOAD_CARD`, id 87035) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| cardTitle | Card Title | عنوان البطاقة | Text | String | true | true |  | indexed |
| cardSubtitle | Card Subtitle | العنوان الفرعي للبطاقة | Text | String | false | true |  | indexed |
| applicationFormFile | Application Form File | ملف نموذج الطلب | Attachment | Long | false | false |  | acceptedFileExtensions=pdf, docx; fileSource=documentsAndMedia |
| downloadLabel | Download Label | نص زر التنزيل | Text | String | false | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **COODownloadCard**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Card Title Maximum Length | `length(cardTitle) <= 100` | Card Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان البطاقة 100 حرفًا. |
| Card Subtitle Maximum Length | `length(cardSubtitle) <= 200` | Card Subtitle must not exceed 200 characters. | يجب ألا يتجاوز العنوان الفرعي للبطاقة 200 حرفًا. |
| Download Label Maximum Length | `length(downloadLabel) <= 40` | Download Label must not exceed 40 characters. | يجب ألا يتجاوز نص زر التنزيل 40 حرفًا. |

**COOFinderDocument** (`QCDEMO-130947-COO_FINDER_DOCUMENT`, id 87457) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| docTitle | Document Title | عنوان المستند | Text | String | true | true |  | indexed |
| docDescription | Document Description | وصف المستند | RichText | Clob | false | true |  | indexed |
| badgeLabel | Badge Label | نص الشارة | Text | String | false | true |  | indexed |
| certificateTypeKeys | Certificate Type Keys | مفاتيح نوع الشهادة | Text | String | false | false |  |  |
| productTypeKeys | Product Type Keys | مفاتيح نوع المنتج | Text | String | false | false |  |  |
| exportDestinationKeys | Export Destination Keys | مفاتيح وجهة التصدير | Text | String | false | false |  |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **COOFinderDocument**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Document Title Maximum Length | `length(docTitle) <= 200` | Document Title must not exceed 200 characters. | يجب ألا يتجاوز عنوان المستند 200 حرفًا. |
| Badge Label Maximum Length | `length(badgeLabel) <= 40` | Badge Label must not exceed 40 characters. | يجب ألا يتجاوز نص الشارة 40 حرفًا. |

**COOFinderOption** (`QCDEMO-130947-COO_FINDER_OPTION`, id 87089) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| optionGroup | Dropdown | القائمة المنسدلة | Picklist | String | true | false | QCDEMO-130947-COO_FINDER-OPTION-GROUP-OPTIONS |  |
| optionKey | Option Key | مُعرّف الخيار | Text | String | true | false |  |  |
| optionLabel | Option Label | نص الخيار | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **COOFinderOption**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Option Label Maximum Length | `length(optionLabel) <= 100` | Option Label must not exceed 100 characters. | يجب ألا يتجاوز نص الخيار 100 حرفًا. |

**COOInfoCard** (`QCDEMO-130947-COO_INFO_CARD`, id 86887) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| cardIcon | Card Icon | أيقونة البطاقة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| cardTitle | Card Title | عنوان البطاقة | Text | String | true | true |  | indexed |
| cardDescription | Card Description | وصف البطاقة | RichText | Clob | false | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **COOInfoCard**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Card Title Maximum Length | `length(cardTitle) <= 100` | Card Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان البطاقة 100 حرفًا. |

**COOPageContent** (`QCDEMO-130947-COO_PAGE_CONTENT`, id 86628) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| eyebrowLabel | Eyebrow Label | التسمية العلوية | Text | String | true | true |  | indexed |
| pageTitle | Page Title | عنوان الصفحة | Text | String | true | true |  | indexed |
| heroDescription | Hero Description | وصف الصفحة | RichText | Clob | true | true |  | indexed |
| heroImage | Hero Image | صورة الصفحة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| bannerEyebrow | Banner Eyebrow | التسمية العلوية للبانر | Text | String | false | true |  | indexed |
| bannerHeading | Banner Heading | عنوان البانر | Text | String | false | true |  | indexed |
| bannerBody | Banner Body | نص البانر | RichText | Clob | false | true |  | indexed |
| bannerActiveStatus | Banner Active Status | حالة البانر | Boolean | Boolean | false | false |  |  |
| pageStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-130947-COO_PAGE_CONTENT-STATUS-OPTIONS |  |

Validation rules on **COOPageContent**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Eyebrow Label Maximum Length | `length(eyebrowLabel) <= 60` | Eyebrow Label must not exceed 60 characters. | يجب ألا يتجاوز التسمية العلوية 60 حرفًا. |
| Page Title Maximum Length | `length(pageTitle) <= 100` | Page Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان الصفحة 100 حرفًا. |
| Banner Eyebrow Maximum Length | `length(bannerEyebrow) <= 60` | Banner Eyebrow must not exceed 60 characters. | يجب ألا يتجاوز التسمية العلوية للبانر 60 حرفًا. |
| Banner Heading Maximum Length | `length(bannerHeading) <= 150` | Banner Heading must not exceed 150 characters. | يجب ألا يتجاوز عنوان البانر 150 حرفًا. |

**COOProcessStep** (`QCDEMO-130947-COO_PROCESS_STEP`, id 86987) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| stepNumber | Step Number | رقم الخطوة | Text | String | true | false |  |  |
| stepTitle | Step Title | عنوان الخطوة | Text | String | true | true |  | indexed |
| stepDescription | Step Description | وصف الخطوة | RichText | Clob | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **COOProcessStep**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Step Title Maximum Length | `length(stepTitle) <= 150` | Step Title must not exceed 150 characters. | يجب ألا يتجاوز عنوان الخطوة 150 حرفًا. |

**COOQuickFact** (`QCDEMO-130947-COO_QUICK_FACT`, id 86770) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| icon | Icon | الأيقونة | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| factLabel | Label | التسمية | Text | String | true | true |  | indexed |
| factValue | Value | القيمة | Text | String | true | true |  | indexed |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **COOQuickFact**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Label Maximum Length | `length(factLabel) <= 60` | Label must not exceed 60 characters. | يجب ألا يتجاوز التسمية 60 حرفًا. |
| Value Maximum Length | `length(factValue) <= 120` | Value must not exceed 120 characters. | يجب ألا يتجاوز القيمة 120 حرفًا. |

**COOSection** (`QCDEMO-130947-COO_SECTION`, id 86822) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionKey | Section Key | مُعرّف القسم | Text | String | true | false |  |  |
| sectionNumber | Section Number | رقم القسم | Text | String | false | false |  |  |
| anchorLabel | Index Label | تسمية الفهرس | Text | String | true | true |  | indexed |
| sectionBadge | Section Badge | شارة القسم | Text | String | false | true |  | indexed |
| sectionTitle | Section Title | عنوان القسم | Text | String | true | true |  | indexed |
| sectionIntro | Section Intro | مقدمة القسم | RichText | Clob | false | true |  | indexed |
| sectionBody | Section Body | محتوى القسم | RichText | Clob | false | true |  | indexed |
| sectionIcon | Section Icon | أيقونة القسم | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg, webp; fileSource=documentsAndMedia |
| pdfButtonLabel | Action Button Label | نص زر الإجراء | Text | String | false | true |  | indexed |
| pdfButtonFile | Action Button File | ملف زر الإجراء | Attachment | Long | false | false |  | acceptedFileExtensions=pdf, docx; fileSource=documentsAndMedia |
| pdfButtonUrl | Action Button URL | رابط زر الإجراء | Text | String | false | false |  |  |
| pdfButtonBehaviour | Action Button Behavior | سلوك زر الإجراء | Picklist | String | false | false | QCDEMO-130947-COO_BUTTON-BEHAVIOUR-OPTIONS |  |
| displayOrder | Display Order | ترتيب العرض | Integer | Integer | true | false |  | indexed |
| activeStatus | Active Status | الحالة | Boolean | Boolean | false | false |  |  |

Validation rules on **COOSection**:

| Rule name (en) | Script | Error label (en) | Error label (ar) |
|---|---|---|---|
| Section Title Maximum Length | `length(sectionTitle) <= 100` | Section Title must not exceed 100 characters. | يجب ألا يتجاوز عنوان القسم 100 حرفًا. |
| Section Badge Maximum Length | `length(sectionBadge) <= 100` | Section Badge must not exceed 100 characters. | يجب ألا يتجاوز شارة القسم 100 حرفًا. |
| Action Button Label Maximum Length | `length(pdfButtonLabel) <= 80` | Action Button Label must not exceed 80 characters. | يجب ألا يتجاوز نص زر الإجراء 80 حرفًا. |

### QCDEMO-130949

Objects: `DownloadableResourceItem`, `OverviewSectionAndInfoCard`, `ProposalForResearchPage`, `ProposalResearchQuickFactsTile`, `ProposalResearchSectionIndexEntry`, `ServiceInformationGroup`, `ServiceInformationGroupItem`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| DownloadableResourceItem | QCDEMO-130949-DOWNLOADABLE_RESOURCE_ITEM | 94688 | Downloadable Resources - Resource Item | Downloadable Resources - Resource Item (AR) | Downloadable Resource Items | resourceTitle | 10 |  |  |
| OverviewSectionAndInfoCard | QCDEMO-130949-OVERVIEW_SECTION_AND_INFO_CARD | 94583 | Overview - Body + Info Card | Overview - Body + Info Card (AR) | Overview Sections and Info Cards | cardTitle | 8 |  |  |
| ProposalForResearchPage | QCDEMO-130949-PROPOSAL_FOR_RESEARCH_PAGE | 94431 | Proposal for Research Page / Hero | Proposal for Research Page / Hero (AR) | Proposal for Research Pages | pageTitle | 7 |  |  |
| ProposalResearchQuickFactsTile | QCDEMO-130949-QUICK_FACTS_TILE | 94483 | Quick-Facts Tile | Quick-Facts Tile (AR) | Quick-Facts Tiles | label | 5 |  |  |
| ProposalResearchSectionIndexEntry | QCDEMO-130949-SECTION_INDEX_ENTRY | 94535 | Section Index / Section | Section Index / Section (AR) | Section Index Entries | sectionTitle | 4 |  |  |
| ServiceInformationGroup | QCDEMO-130949-SERVICE_INFORMATION_GROUP | 94638 | Service Information - Information Group | Service Information - Information Group (AR) | Service Information Groups | groupLabel | 6 |  | 1 |
| ServiceInformationGroupItem | QCDEMO-130949-SERVICE_INFORMATION_GROUP_ITEM | 95186 | Group Item (bullet inside an Information Group) | Group Item (bullet inside an Information Group) (AR) | Service Information Group Items | externalReferenceCode | 4 |  |  |

**DownloadableResourceItem** (`QCDEMO-130949-DOWNLOADABLE_RESOURCE_ITEM`, id 94688) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionBadge | Section Badge | Section Badge (AR) | Text | String | true | true |  | indexed |
| sectionTitle | Section Title | Section Title (AR) | Text | String | true | true |  |  |
| sectionIntro | Section Intro | Section Intro (AR) | RichText | Clob | true | true |  |  |
| resourceTitle | Resource Title | Resource Title (AR) | Text | String | true | true |  |  |
| resourceFile | Resource File | Resource File (AR) | Attachment | Long | false | false |  | acceptedFileExtensions=pdf; fileSource=documentsAndMedia |
| fileType | File Type | File Type (AR) | Text | String | true | false |  |  |
| fileSize | File Size | File Size (AR) | Text | String | true | false |  |  |
| downloadLabel | Download Label | Download Label (AR) | Text | String | true | true |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  |  |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

**OverviewSectionAndInfoCard** (`QCDEMO-130949-OVERVIEW_SECTION_AND_INFO_CARD`, id 94583) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionBadge | Section Badge | Section Badge (AR) | Text | String | true | true |  | indexed |
| sectionTitle | Section Title | Section Title (AR) | Text | String | true | true |  |  |
| overviewBody | Overview Body | Overview Body (AR) | RichText | Clob | true | true |  |  |
| cardIcon | Card Icon | Card Icon (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| cardTitle | Card Title | Card Title (AR) | Text | String | true | true |  |  |
| cardDescription | Card Description | Card Description (AR) | RichText | Clob | true | true |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  |  |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

**ProposalForResearchPage** (`QCDEMO-130949-PROPOSAL_FOR_RESEARCH_PAGE`, id 94431) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| eyebrowLabel | Eyebrow Label | Eyebrow Label (AR) | Text | String | true | true |  | indexed |
| pageTitle | Page Title | Page Title (AR) | Text | String | true | true |  |  |
| heroDescription | Hero Description | Hero Description (AR) | RichText | Clob | true | true |  |  |
| heroBanner | Hero Banner | Hero Banner (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, png, svg; fileSource=documentsAndMedia |
| pageStatus | Status | الحالة | Picklist | String | true | false | QCDEMO-130949-PROPOSAL_FOR_RESEARCH_PAGE-STATUS-OPTIONS |  |
| createdDate | Created Date | Created Date (AR) | Date | Date | true | false |  |  |
| lastModifiedDate | Last Modified Date | Last Modified Date (AR) | Date | Date | true | false |  |  |

**ProposalResearchQuickFactsTile** (`QCDEMO-130949-QUICK_FACTS_TILE`, id 94483) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| icon | Icon | Icon (AR) | Attachment | Long | true | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| label | Label | Label (AR) | Text | String | true | true |  | indexed |
| value | Value | Value (AR) | Text | String | true | true |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  |  |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

**ProposalResearchSectionIndexEntry** (`QCDEMO-130949-SECTION_INDEX_ENTRY`, id 94535) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionTitle | Section Title | Section Title (AR) | Text | String | true | true |  | indexed |
| sectionNumbering | Section Numbering | Section Numbering (AR) | Text | String | true | true |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  |  |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

**ServiceInformationGroup** (`QCDEMO-130949-SERVICE_INFORMATION_GROUP`, id 94638) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| sectionBadge | Section Badge | Section Badge (AR) | Text | String | true | true |  | indexed |
| sectionTitle | Section Title | Section Title (AR) | Text | String | true | true |  |  |
| groupLabel | Group Label | Group Label (AR) | Text | String | true | true |  |  |
| groupIntro | Group Intro | Group Intro (AR) | RichText | Clob | false | true |  |  |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  |  |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |

**ServiceInformationGroupItem** (`QCDEMO-130949-SERVICE_INFORMATION_GROUP_ITEM`, id 95186) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| itemLabel | Item Label | Item Label (AR) | RichText | Clob | true | true |  | indexed |
| displayOrder | Display Order | Display Order (AR) | Integer | Integer | true | false |  |  |
| activeStatus | Active Status | Active Status (AR) | Boolean | Boolean | false | false |  |  |
| r_serviceInformationGroupItems_c_serviceInformationGroupId | Service Information Group | مجموعة معلومات الخدمة | Relationship | Long | false | false |  | indexed |

### QCDEMO-ABOUT-HERO-BANNER

Objects: `AboutHeroBanner`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| AboutHeroBanner | QCDEMO-ABOUT-HERO-BANNER | 79334 | About Hero Banner | About Hero Banner (AR) | About Hero Banners | pageKey | 3 |  |  |

**AboutHeroBanner** (`QCDEMO-ABOUT-HERO-BANNER`, id 79334) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| pageKey | Page Key | Page Key (AR) | Text | String | true | false |  | indexed |
| bannerImage | Banner Image | Banner Image (AR) | Attachment | Long | false | false |  | acceptedFileExtensions=jpg, jpeg, png, svg; fileSource=documentsAndMedia |
| bannerImageAltText | Banner Image Alt Text | Banner Image Alt Text (AR) | Text | String | false | true |  |  |

### QC_COMMUNITY_PARTNER

Objects: `CommunityPartner`, `CommunityPartnersConfiguration`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| CommunityPartner | QC_COMMUNITY_PARTNER | 45665 | Community Partner | شريك مجتمعي | Community Partners | partnerNameEn | 6 |  |  |
| CommunityPartnersConfiguration | QC_COMMUNITY_PARTNERS_CONFIGURATION | 45816 | Community Partners Configuration | إعدادات الشركاء المجتمعيين | Community Partners Configurations | externalReferenceCode | 4 |  |  |

**CommunityPartner** (`QC_COMMUNITY_PARTNER`, id 45665) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| partnerNameEn | Partner Name (EN) |  | Text | String | true | false |  | indexed |
| partnerNameAr | Partner Name (AR) |  | Text | String | false | false |  | indexed |
| partnerUrl | Partner URL |  | Text | String | false | false |  | indexed |
| displayOrder | Display Order |  | Integer | Integer | false | false |  | indexed |
| activeStatus | Active |  | Boolean | Boolean | false | false |  | indexed |
| partnerLogoColor | Partner Logo (Color, hover state) |  | Attachment | Long | false | false |  | acceptedFileExtensions=[gif, jpeg, jpg, png, svg, webp]; fileSource=documentsAndMedia |

**CommunityPartnersConfiguration** (`QC_COMMUNITY_PARTNERS_CONFIGURATION`, id 45816) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| titleEn | Title (EN) |  | Text | String | false | false |  | indexed |
| titleAr | Title (AR) |  | Text | String | false | false |  | indexed |
| subtitleEn | Subtitle (EN) |  | Text | String | false | false |  | indexed |
| subtitleAr | Subtitle (AR) |  | Text | String | false | false |  | indexed |

### QC_FOOTER

Objects: `FooterConfiguration`, `FooterLink`

| Object (name) | ERC | id | Label (en) | Label (ar) | Plural Label (en) | Title Field | # custom fields | Validation rules | Relationships |
|---|---|---|---|---|---|---|---|---|---|
| FooterConfiguration | QC_FOOTER_CONFIGURATION | 44794 | Footer Configuration | إعدادات التذييل | Footer Configurations | externalReferenceCode | 13 |  |  |
| FooterLink | QC_FOOTER_LINK | 45195 | Footer Link | رابط التذييل | Footer Links | footerLinkLabelEn | 6 |  |  |

**FooterConfiguration** (`QC_FOOTER_CONFIGURATION`, id 44794) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| logoImage | Logo Image |  | Attachment | Long | false | false |  | acceptedFileExtensions=[gif, jpeg, jpg, png, svg, webp]; fileSource=documentsAndMedia |
| logoRedirectUrl | Logo Redirect URL |  | Text | String | false | true |  | indexed |
| aboutColumnTitle | About Column Title |  | Text | String | false | true |  | indexed |
| servicesColumnTitle | Services Column Title |  | Text | String | false | true |  | indexed |
| quickLinksColumnTitle | Quick Links Column Title |  | Text | String | false | true |  | indexed |
| socialTitle | Social Title |  | Text | String | false | true |  | indexed |
| aboutText | About Text |  | LongText | Clob | false | true |  |  |
| newsletterTitle | Newsletter Title |  | Text | String | false | true |  | indexed |
| newsletterText | Newsletter Text |  | LongText | Clob | false | true |  |  |
| subscribeLabel | Subscribe Label |  | Text | String | false | true |  | indexed |
| copyright | Copyright |  | Text | String | false | true |  | indexed |
| logoAltText | Logo Alt Text |  | Text | String | false | true |  | indexed |
| emailPlaceholder | Email Placeholder |  | Text | String | false | true |  | indexed |

**FooterLink** (`QC_FOOTER_LINK`, id 45195) — fields:

| Field | Label (en) | Label (ar) | businessType | DBType | required | localized | Picklist ERC | Notes |
|---|---|---|---|---|---|---|---|---|
| footerLinkLabelEn | Label (EN) |  | Text | String | true | false |  | indexed |
| footerLinkLabelAr | Label (AR) |  | Text | String | false | false |  | indexed |
| footerLinkUrl | URL |  | Text | String | false | false |  | indexed |
| footerColumn | Column |  | Picklist | String | true | false | QC_FOOTER_COLUMNS | indexed |
| displayOrder | Display Order |  | Integer | Integer | false | false |  | indexed |
| activeStatus | Active |  | Boolean | Boolean | false | false |  | indexed |

---

## 7. Object Relationships

**[LIVE]**

Only **3** formal `objectRelationships` entries exist across all 111 site-scoped object definitions, despite many objects sharing a feature-group naming convention (e.g. all the `QCDEMO-129405-MEDIATION_*` objects are siblings, not linked via a formal DB relationship/foreign key — automation should not assume a parent/child API link exists just because two objects share a story-id prefix).

| Parent object (side 1) | Relationship field name | Type | Child object (side 2) | Deletion type |
|---|---|---|---|---|
| NavItem (`QCDEMO-129363-NAV_ITEM`) | navItemParent | oneToMany | NavItem (`QCDEMO-129363-NAV_ITEM`) | disassociate |
| FooterNavigationColumn (`QCDEMO-129366-FOOTER_NAVIGATION_COLUMN`) | footerNavColumnLinks | oneToMany | FooterNavigationLink (`QCDEMO-129366-FOOTER_NAVIGATION_LINK`) | disassociate |
| ServiceInformationGroup (`QCDEMO-130949-SERVICE_INFORMATION_GROUP`) | serviceInformationGroupItems | oneToMany | ServiceInformationGroupItem (`QCDEMO-130949-SERVICE_INFORMATION_GROUP_ITEM`) | cascade |

No `objectFields[].businessType === "Relationship"` entries were found beyond these same 3 (cross-checked across all 111 objects' full field lists) — i.e. there is no hidden/undocumented relationship wiring beyond what `objectRelationships[]` reports.

---

## 8. List Type Definitions

**[LIVE]** Note quirk #6 above (§5) — this listing endpoint under-reports; the table below was reconstructed by cross-referencing every Object Picklist field's `listTypeDefinitionExternalReferenceCode`, not by trusting the list endpoint alone.

### Referenced list types (used by at least one Object Picklist field)

| ERC | Name | id | Used by (object.field) | Entries (key: en / ar) |
|---|---|---|---|---|
| QC_FOOTER_COLUMNS | Footer Columns | 38443 | FooterLink.footerColumn | about: About Qatar Chamber / عن غرفة قطر; services: Services / خدماتنا; quickLinks: Quick Links / روابط سريعة; legal: Legal / قانوني |
| QCDEMO-129363-HEADER_CONFIGURATION-WORKFLOW_STATUS-OPTIONS | Workflow Status Options | 37358 | HeaderConfiguration.workflowStatus | draft: Draft / Draft (AR); submittedforreview: Submitted for Review / Submitted for Review (AR); published: Published / Published (AR); unpublished: Unpublished / Unpublished (AR) |
| QCDEMO-129366-SOCIAL_MEDIA_ICON-PLATFORM-OPTIONS | Social Media Platform | 41871 | SocialMediaIcon.platform | facebook: Facebook / Facebook (AR); x: X / X (AR); linkedin: LinkedIn / LinkedIn (AR); instagram: Instagram / Instagram (AR); youtube: YouTube / YouTube (AR); whatsapp: WhatsApp / WhatsApp (AR); telegram: Telegram / Telegram (AR); snapchat: Snapchat / Snapchat (AR) |
| QCDEMO-129371-SERVICE_CARD-ASSIGNED_TAB-OPTIONS | Service Card Assigned Tab Options | 47916 | ServiceCard.assignedTab | allServices: All Services / All Services (AR); membership: Membership / Membership (AR); legal: Legal / Legal (AR); eServices: E-Services / E-Services (AR); information: Information / Information (AR) |
| QCDEMO-129383-BUSINESS_EVENT-eventCategory-OPTIONS | Business Event Category Options | 49260 | BusinessEvent.eventCategory | chamberEvents: Chamber Events / فعاليات الغرفة; globalEvents: Global Events / الفعاليات العالمية |
| QCDEMO-129386-PUBLICATION-PUBLICATIONTYPE-OPTIONS | Publication Type Options | 49805 | Publication.publicationType | report: Report / تقرير; bulletin: Bulletin / نشرة; study: Study / دراسة; researchPaper: Research Paper / ورقة بحثية; guides: Guides / أدلة; whitePaper: White Paper / ورقة بيضاء; manuals: Manuals / كتيبات; brochure: Brochure / كتيب تعريفي |
| QCDEMO-129387-PODCAST_EPISODE-status-OPTIONS | Podcast Episode Status | 50214 | PodcastEpisode.episodeStatus | draft: Draft / مسودة; published: Published / منشور; archived: Archived / مؤرشف |
| QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-STATUS-OPTIONS | About Qatar Chamber Page Status | 77371 | AboutQatarChamberPage.pageStatus | draft: Draft / مسودة; published: Published / منشور |
| QCDEMO-129393-CHAIRMAN_MESSAGE_PAGE-STATUS-OPTIONS | Chairman Message Page Status Options | 77825 | ChairmanMessagePage.publishStatus | draft: Draft / Draft (AR); published: Published / Published (AR) |
| QCDEMO-129397-GENERAL_MANAGER_MESSAGE-STATUS-OPTIONS | GM Message Status | 79634 | GeneralManagerMessage.publicationStatus | draft: Draft / مسودة; published: Published / منشور |
| QCDEMO-129398-BOARD_MEMBER-memberCategory-OPTIONS | Board Member — Member Category Options | 79984 | BoardMember.memberCategory | chairman: Chairman / رئيس مجلس الإدارة; viceChairman: Vice Chairman / نائب رئيس مجلس الإدارة; boardMember: Board Member / عضو مجلس الإدارة; generalManager: General Manager / المدير العام |
| QCDEMO-129400-MEMBER_SERVICE-CTAOPENBEHAVIOR-OPTIONS | Member Service CTA Open Behavior | 81016 | MemberService.ctaOpenBehavior | sameTab: Same tab / نفس التبويب; newTab: New tab / تبويب جديد |
| QCDEMO-129402-APPLY_ONLINE_CTA-OPENBEHAVIOR-OPTIONS | Apply Online CTA Open Behavior Options | 81660 | ApplyOnlineCTA.openBehavior, ATACarnetCTA.openBehavior | sameTab: Same Tab / نفس التبويب; newTab: New Tab / تبويب جديد |
| QCDEMO-129402-ATA_CARNET_PAGE-STATUS-OPTIONS | ATA Carnet Page Status Options | 81653 | ATACarnetPage.pageStatus | draft: Draft / مسودة; published: Published / منشور; unpublished: Unpublished / غير منشور |
| QCDEMO-129402-ATA_FEE_ROW-CURRENCY-OPTIONS | QCDEMO-129402-ATA_FEE_ROW-CURRENCY-OPTIONS | 88459 | ATAFeeRow.currency | qar: QAR / QAR |
| QCDEMO-129402-ATA_OPERATING_HOUR-STATUS-OPTIONS | QCDEMO-129402-ATA_OPERATING_HOUR-STATUS-OPTIONS | 88508 | ATAOperatingHour.hoursStatus | open: Open / مفتوح; closed: Closed / مغلق |
| QCDEMO-129402-COLLAPSIBLE_SECTION-OPENBEHAVIOUR-OPTIONS | Collapsible Section Open Behaviour Options | 81657 | CollapsibleSection.openBehaviour | sameTab: Same Tab / نفس التبويب; newTab: New Tab / تبويب جديد |
| QCDEMO-129403-TIR_CARNET_PAGE-STATUS-OPTIONS | TIR Carnet Page Status Options | 82288 | TIRCarnetPage.pageStatus | draft: Draft / مسودة; published: Published / منشور; unpublished: Unpublished / غير منشور |
| QCDEMO-129403-TIR_SECTION-OPEN-BEHAVIOUR | QCDEMO-129403-TIR_SECTION-OPEN-BEHAVIOUR | 88659 | TIRSection.openBehaviour | singleOpen: Single-open / فتح عنصر واحد; multiOpen: Multi-open / فتح عدة عناصر |
| QCDEMO-129404-CONSULTATION_REQUEST-LEGALISSUECATEGORY-OPTIONS | Consultation Request - Legal Issue Category | 82481 | ConsultationRequest.legalIssueCategory | commercialCorporateLaw: Commercial / Corporate Law / القانون التجاري / قانون الشركات; laborEmployment: Labor & Employment / قانون العمل والتوظيف; contracts: Contracts / العقود; intellectualProperty: Intellectual Property / الملكية الفكرية; realEstate: Real Estate / العقارات; disputeResolution: Dispute Resolution / تسوية المنازعات; taxation: Taxation / الضرائب; other: Other / أخرى |
| QCDEMO-129404-CONSULTATION_REQUEST-STATUS-OPTIONS | Consultation Request - Status | 82483 | ConsultationRequest.requestStatus | pending: Pending / قيد الانتظار; approved: Approved / مقبول; rejected: Rejected / مرفوض |
| QCDEMO-129404-LEGAL_CTA-OPENBEHAVIOUR-OPTIONS | QCDEMO-129404-LEGAL_CTA-OPENBEHAVIOUR-OPTIONS | 89621 | LegalConsultationPage.ctaOpenBehaviour | sameTab: Same Tab / في نفس التبويب; newTab: New Tab / في تبويب جديد |
| QCDEMO-129404-LEGAL_FAQ-OPENBEHAVIOUR-OPTIONS | QCDEMO-129404-LEGAL_FAQ-OPENBEHAVIOUR-OPTIONS | 89738 | LegalSection.openBehaviour | single: Single-open / سؤال واحد مفتوح; multi: Multi-open / أسئلة متعددة مفتوحة |
| QCDEMO-129404-LEGAL_PAGE-STATUS-OPTIONS | QCDEMO-129404-LEGAL_PAGE-STATUS-OPTIONS | 89622 | LegalConsultationPage.pageStatus | draft: Draft / مسودة; published: Published / منشورة; unpublished: Unpublished / غير منشورة |
| QCDEMO-129404-LEGAL_SCOPE-GROUP-OPTIONS | QCDEMO-129404-LEGAL_SCOPE-GROUP-OPTIONS | 89894 | LegalScopeItem.scopeGroup | included: Included Scope / النطاق المشمول; excluded: Excluded Scope / النطاق غير المشمول |
| QCDEMO-129405-MEDIATION_CTA-OPENBEHAVIOUR-OPTIONS | QCDEMO-129405-MEDIATION_CTA-OPENBEHAVIOUR-OPTIONS | 90037 | MediationPage.ctaOpenBehaviour | sameTab: Same Tab / في نفس التبويب; newTab: New Tab / في تبويب جديد |
| QCDEMO-129405-MEDIATION_FAQ-OPENBEHAVIOUR-OPTIONS | QCDEMO-129405-MEDIATION_FAQ-OPENBEHAVIOUR-OPTIONS | 90511 | MediationSection.openBehaviour | single: Single-open / سؤال واحد مفتوح; multi: Multi-open / أسئلة متعددة مفتوحة |
| QCDEMO-129405-MEDIATION_PAGE-STATUS-OPTIONS | QCDEMO-129405-MEDIATION_PAGE-STATUS-OPTIONS | 90038 | MediationPage.pageStatus | draft: Draft / مسودة; published: Published / منشورة; unpublished: Unpublished / غير منشورة |
| QCDEMO-129405-MEDIATION_REQUEST-STATUS-OPTIONS | Mediation Request Status | 83194 | MediationRequest.requestStatus | pending: Pending / قيد الانتظار; approved: Approved / مقبول; rejected: Rejected / مرفوض |
| QCDEMO-129406-EC_LINK_TARGET | QCDEMO-129406-EC_LINK_TARGET | 90813 | EconomicConsultancyPage.overviewHyperlinkTarget | sameTab: Same Tab / في نفس التبويب; newTab: New Tab / في تبويب جديد |
| QCDEMO-129406-EC_PAGE_STATUS | QCDEMO-129406-EC_PAGE_STATUS | 90812 | EconomicConsultancyPage.pageStatus | draft: Draft / مسودة; published: Published / منشورة; unpublished: Unpublished / غير منشورة |
| QCDEMO-129406-EC_SCOPE_GROUP | QCDEMO-129406-EC_SCOPE_GROUP | 91123 | EconomicConsultancyScopeItem.scopeGroup | included: Included Scope / النطاق المشمول; excluded: Excluded Scope / النطاق غير المشمول |
| QCDEMO-129407-LT-CONTENT_STATUS | Content Status | 94221 | EconomicResearchListingPage.pageStatus, EconomicResearchReport.reportStatus | draft: Draft / مسودة; published: Published / منشور; unpublished: Unpublished / غير منشور |
| QCDEMO-129566-NEWSLETTER-LANGUAGE-OPTIONS | Newsletter Language | 43192 | Newsletter.language | en: EN / الإنجليزية; ar: AR / العربية; both: Both / كلاهما |
| QCDEMO-129566-NEWSLETTER-STATUS-OPTIONS | Newsletter Status | 43196 | Newsletter.newsletterStatus | draft: Draft / مسودة; approved: Approved / معتمد; published: Published / منشور; archived: Archived / مؤرشف |
| QCDEMO-130947-COO_BUTTON-BEHAVIOUR-OPTIONS | COO Action Button Behaviour Options | 86617 | COOSection.pdfButtonBehaviour | sameTab: Same Tab / في نفس التبويب; newTab: New Tab / في تبويب جديد; download: Download / تنزيل |
| QCDEMO-130947-COO_CTA-OPENBEHAVIOUR-OPTIONS | COO CTA Open Behaviour Options | 86621 | COOCta.openBehaviour | sameTab: Same Tab / في نفس التبويب; newTab: New Tab / في تبويب جديد |
| QCDEMO-130947-COO_FINDER-OPTION-GROUP-OPTIONS | COO Finder Option Group | 86624 | COOFinderOption.optionGroup | certificateType: Certificate Type / نوع شهادة المنشأ; productType: Product Type / نوع المنتج; exportDestination: Export Destination / وجهة التصدير |
| QCDEMO-130947-COO_PAGE_CONTENT-STATUS-OPTIONS | COO Page Content Status Options | 82821 | COOPageContent.pageStatus | draft: Draft / Draft (AR); published: Published / Published (AR); unpublished: Unpublished / Unpublished (AR) |
| QCDEMO-130949-PROPOSAL_FOR_RESEARCH_PAGE-STATUS-OPTIONS | Proposal For Research Page Status Options | 94430 | ProposalForResearchPage.pageStatus | published: Published / منشور; draft: Draft / مسودة; unpublished: Unpublished / غير منشور |

### Unreferenced list types (present on instance, no current object field points to them)

| ERC | Name | id |
|---|---|---|
| QCDEMO-129405-MEDIATION_REQUEST-PRIORCOMMUNICATION-OPTIONS | Mediation Prior Communication Options | 92916 |
| QCDEMO-129363-NAV_ITEM-NAV_ITEM_LEVEL-OPTIONS | Nav Item Level Options | 37385 |
| QCDEMO-129566-NEWSLETTER_ISSUE-LANGUAGE-OPTIONS | Newsletter Issue Language Options | 39152 |
| QCDEMO-129566-NEWSLETTER_ISSUE-STATUS-OPTIONS | Newsletter Issue Status Options | 39156 |

---

## 9. Document Folder Tree

**[LIVE]**

All 3 root folders were checked recursively (root -> children -> grandchildren). No third-level (grandchild) folders exist anywhere in the tree — every child folder found is a leaf.

- **qatar-chamber-website** (id 40090)
  - hero-banner (id 40092)
  - community-partners (id 40591)
  - promotional-banners (id 47655)
  - our-services (id 48165)
  - latest-news (id 48733)
  - strategic-direction (id 49034)
  - upcoming-event (id 49191)
  - business-events (id 49357)
  - dynamic-widgets (id 49653)
  - publications-section (id 50050)
  - podcast (id 50467)
  - media-gallery (id 50845)
  - about-us (id 52001)
  - strategic-partners (id 53208)
  - about-qatar-chamber (id 77606)
  - chairman-message (id 78211)
  - chamber-laws (id 78596)
  - vision-mission-objectives (id 78818)
  - general-manager-message (id 79828)
  - board-directory (id 80177)
  - member-services (id 81283)
  - ata-carnet (id 81928)
- **QC Footer Social Icons** (id 42742)
  - (no children)
- **Flickr** (id 52219)
  - Third_Test_Album_QChamber (id 52221)
  - First_Test_Album_QChamber (id 52245)
  - Second_test_Album_QChamber (id 52306)
  - Videos (id 52355)

---

## 10. Content Structures (Journal / Web Content — GET-only via REST)

**[LIVE]**

### Home Page Section (id 49186)

Description: (none) | Available languages: ar-SA, en-US

| Field | Label | dataType | required | repeatable | localizable |
|---|---|---|---|---|---|
| sectionTag | Section Tag | string | false | false | true |
| sectionHeading | Section Heading | string | true | false | true |
| sectionDescription | Section Description | html | true | false | true |

### Business Events Section (id 49321)

Description: (none) | Available languages: ar-SA, en-US

| Field | Label | dataType | required | repeatable | localizable |
|---|---|---|---|---|---|
| sectionTag | Section Tag | string | false | false | true |
| sectionHeading | Section Heading | string | true | false | true |
| sectionDescription | Section Description | html | true | false | true |

### Publications Section (id 50040)

Description: (none) | Available languages: ar-SA, en-US

| Field | Label | dataType | required | repeatable | localizable |
|---|---|---|---|---|---|
| sectionTag | Section Tag | string | false | false | true |
| sectionHeading | Section Heading | string | true | false | true |
| sectionDescription | Section Description | html | true | false | true |

### Contact Us Section (id 52431)

Description: (none) | Available languages: ar-SA, en-US

| Field | Label | dataType | required | repeatable | localizable |
|---|---|---|---|---|---|
| sectionTag | Section Tag | string | true | false | true |
| sectionHeading | Section Heading | string | true | false | true |
| sectionDescription | Section Description | string | false | false | true |
| emailSupportAddress | Email Support Address | string | true | false | true |
| telephoneNumber | Telephone Number | string | true | false | true |
| locationAddress | Location Address | string | true | false | true |
| mapEmbedUrl | Map Embed URL | string | false | false | false |
| formRecipientEmail | Form Recipient Email(s) | string | true | false | false |
| sendMessageButtonLabel | Send Message Button Label | string | true | false | true |

### Board Directory Page (id 80168)

Description: (none) | Available languages: ar-SA, en-US

| Field | Label | dataType | required | repeatable | localizable |
|---|---|---|---|---|---|
| pageTitle | Page Title | string | true | false | true |
| heroBanner | Hero Banner | image | false | false | false |
| sectionEyebrowLabel | Section Eyebrow Label | string | false | false | true |
| sectionHeading | Section Heading | string | false | false | true |

### Organization Structure Page (id 80717)

Description: (none) | Available languages: ar-SA, en-US

| Field | Label | dataType | required | repeatable | localizable |
|---|---|---|---|---|---|
| pageTitle | Page Title | string | true | false | true |
| heroBanner | Hero Banner | image | true | false | false |
| status | Status | string | true | false | false |

---

## 11. Fragments — REST Availability

**[LIVE]**

No fragment-related REST resources are exposed on this instance. Searched full `paths` list of:
- `GET /o/headless-delivery/v1.0/openapi.json` (296 total paths) — zero paths matching `/fragment/i`.
- `GET /o/headless-admin-content/v1.0/openapi.json` (8 total paths: display-page-templates, page-definitions/preview, structured-contents/*) — zero fragment paths.
- `GET /o/object-admin/v1.0/openapi.json` — zero fragment paths.

Previously-tried `/o/headless-delivery/v1.0/sites/{siteId}/site-fragment-collections` also 404s (per prior session). `GET /o/headless-delivery/v1.0/sites/37246/page-definitions/preview` (a GET against a path that exists in the admin-content openapi) returned a plain 404 — that path is likely POST-only (preview submission), not a fragment listing endpoint. Conclusion: fragment collections/entries are not exposed via headless REST on this Liferay version/instance; no further attempts made per task guidance.

Practical implication for automation: fragment-level testing (does the header
render, does a hero banner slide show up correctly) must be done via
**Playwright driving the actual rendered page**, not via REST assertions —
REST can only verify the underlying Object/Content-Structure data is correct,
not that the fragment renders it properly. This matches the existing
`qatar-chamber-playwright-fragment-import` skill's approach.

---

## 12. Data Quality Notes (matters for writing assertions)

**[LIVE]** Of ~989 localizable label values checked across all 111 site
objects (object labels + field labels + validation-rule error labels):

- ~724 contain proper Arabic script.
- ~259 are literal English placeholder text with an appended `(AR)` suffix
  (e.g. `"Header Configuration (AR)"`) instead of a real translation — this
  is the project's documented "pending translation" marker, not a bug.
- **6 fields contain a literal ASCII `?` character as their entire `ar_SA`
  value** (confirmed via raw response bytes, `0x3f` repeated — genuinely
  stored that way, not a mojibake/transport artifact):
  `HeaderConfiguration.logoImage`, `HeaderConfiguration.logoAltTextEn`,
  `HeaderConfiguration.logoAltTextAr`, `HeaderConfiguration.logoRedirectUrl`,
  `NewsletterSubscriber.lastSubscribedOn`, `NewsletterSubscriber.lastUnsubscribedOn`.

**Implication**: do not write an automation assertion that assumes every
field has a real, non-placeholder Arabic string. If a test needs to verify
Arabic content specifically, pick a field confirmed to have real Arabic text
(most field tables above show the actual live `ar_SA` value — anything that
isn't `"<English> (AR)"` or a bare `?` is real).

---

## 13. Cross-Reference to Content-Admin-Guide.docx

`CMS/Content-Admin-Guide.docx` is the non-technical counterpart to this file
— written for content editors, no API details, organized by page/section
(§3–§26) with a sitemap (§2) mapping each page section to its backing
Object(s). Use it to answer "which page does this Object back, and what do
the field labels mean to a human editor" — this file answers "what's the
exact API shape". A few mappings confirmed to match between the two:

- Header/Footer → `HeaderConfiguration`, `NavItem`, `FooterConfiguration`,
  `FooterLink`, `FooterNavigationColumn/Link`, `QuickLink`, `BottomBarLink`,
  `CopyrightBar`, `SocialMediaIcon`.
- Hero Banner → `HeroBannerSlide`, `AchievementCounter`.
- About Us + its subpages → all share `AboutHeroBanner`
  (`QCDEMO-ABOUT-HERO-BANNER`) for the banner, plus a dedicated `*Page`
  object per subpage (`AboutQatarChamberPage`, `ChairmanMessagePage`,
  `GeneralManagerMessage`, `BoardMember`, `Department`, `VmoSection`,
  `LawEntry`).
- Services → `ServiceCard`, `FilterTab`, plus a large dedicated object family
  per individual service page (ATA Carnet, TIR Carnet, Legal Consultation,
  Mediation, Economic Consultancy, Economic Research, Proposal for Research,
  Certificate of Origin ("COO"), Member Services) — each service page is its
  own feature group in §6 above, not a shared structure.
- Business Events / News / Publications / Podcast / Media Gallery → one
  object per section per the guide (`BusinessEvent`, `NewsArticle`,
  `Publication`, `PodcastEpisode`, `MediaItem`).
- Newsletter → `Newsletter` + `NewsletterSubscriber`.
- Contact inquiries → `InquiryCategory` (Object) + Contact Us Section
  (Content Structure, §10 above) for the page copy.

If the docx and this file ever disagree on which Object backs a given page
(e.g. after a future feature is added), re-verify live rather than trusting
either document blindly — both are snapshots.

---

## 14. Checklist Before Writing Automation Against This Instance

1. Confirm base URL, site groupId, and credentials for the target environment
   — they will differ between `qcdev` and any staging/prod instance.
2. For any resource type, verify its by-ERC route actually exists on *that*
   instance/version before assuming this doc's endpoint table still holds
   (see §3 and the skills' "Verification duty" convention) — Structure has
   none, Object Definition/List Type Definition do.
3. Always address site-scoped Object entries via
   `/o/c/{restContextPath}/scopes/{groupId}`, never the bare path.
4. Cap `pageSize` at 50 on `/o/object-admin/v1.0/object-definitions`; treat
   any listing endpoint's `totalCount` as a hint, not a guarantee of
   retrievability — fall back to fetching by known ERC when a listing 404s.
5. Percent-encode filter values, or avoid `?filter=` entirely.
6. Never assume an Object relationship exists between same-prefix objects
   unless it's listed in §7 — fetch/seed each object independently.
7. Never assert on Arabic label text without checking §12 first.
8. Fragment/page-render verification needs Playwright, not REST.
9. Never POST directly to a resource with a by-ERC route; never DELETE
   outside a documented rollback flow.
