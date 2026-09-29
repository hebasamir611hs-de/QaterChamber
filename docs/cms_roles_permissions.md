# CMS (Liferay) Roles & Permissions

Mapping of legacy WordPress roles to the Liferay roles used in this CMS, their as-designed
permission summary, and the actual behaviour verified through manual/automated testing.

## Role Definitions (As-Designed)

| WordPress Role | Liferay Role | Permissions (As-Is Summary) | Permission Summary | Description |
|---|---|---|---|---|
| Administrator | Administrator (Regular Role) | Full access to users, roles, content, plugins, settings | Full system control | Super Administrator with complete control configuration and user management |
| Editor | Site Content Editor (Site Role) | Manage Gravity Views, form entries, SEO metadata, redirects, publish content | Manage & publish all content | Responsible for full content lifecycle including publishing and advanced configurations |
| Author | Site Content Author (Site Role) | Create/edit/publish own content, manage tables, upload files | Create & publish own content | Creates and manages own content with publishing rights |
| Contributor | Content Contributor (Site Role) | Create/edit content, no publishing rights | Create content (no publish) | Can draft content but requires approval before publishing |
| Subscriber | Site Member (Regular Role) | Read, limited view access | View-only access | Basic authenticated user with access to view content |
| SEO Manager | SEO Manager (Regular Role) | Manage SEO metadata, redirects, options, site health checks | Full SEO management | Handles SEO configuration, optimization, and monitoring |
| SEO Editor | SEO Editor (Regular Role) | Edit SEO metadata, manage redirects (limited) | SEO content updates | Supports SEO updates and metadata management |
| Gravity Forms Role | Forms Manager (Site Role) | Manage form entries, edit/export/view submissions, moderate entries | Manage forms & submissions | Responsible for managing forms and processing submissions |
| Organizer | Event Organizer (Site Role) | Read (limited role) | Event access role | Handles event-related coordination (expandable role) |

## Verified Behaviour (QA-Confirmed)

| Role | Type | Verified Behaviour |
|---|---|---|
| Site Content Editor | Site | Add / view / update / delete on all editorial Objects |
| Site Content Author | Site | Add + view only — edits to own records come from Liferay's implicit Owner role |
| Content Contributor | Site | Add + view, no document uploads |
| SEO Manager | Regular | Add redirects and delete them, page SEO options |
| SEO Editor | Regular | Add redirects, cannot delete ("limited") |
| Forms Manager | Site | View + update form submissions |
| Event Organizer | Site | View only |

### Notes

- "Verified Behaviour" reflects what QA has actually observed in the CMS, and takes precedence
  over the as-designed summary where the two disagree (e.g. Site Content Author is add+view only
  in practice, with per-record edit rights coming from Liferay's Owner role rather than the
  Author role itself).
- Administrator, Site Member (Subscriber), and Event Organizer's broader description have not yet
  been independently re-verified against the live CMS.
