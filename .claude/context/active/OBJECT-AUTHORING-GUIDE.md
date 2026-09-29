# Object Authoring — Content Editor Guide

> **SOURCE OF TRUTH — supplied by the project team 2026-09-08.**
> This file is the authoritative description of the **Object Authoring** staff
> surface (`/web/qatar-chamber/object-authoring`) — its URLs, buttons, statuses,
> bilingual field shapes, attachment behaviour, preview panel and error
> messages. It was provided as `OBJECT-AUTHORING-GUIDE.md` +
> `QC-Object-Authoring-Guide.pdf` and is reproduced here verbatim (the original
> `.md` had a broken text encoding; the Arabic and arrow characters below are
> restored from the PDF).
>
> **Precedence:** where this guide and any other repo document disagree about
> *how the tool behaves*, **this guide wins** — file a note in
> `standards.md` and fix the other document. `standards.md` still wins on *QA
> policy* (what we are allowed to do to `qcdev`, e.g. the never-delete-by-
> position rule and the mandatory logged-out visibility check), because policy
> is deliberately stricter than the tool.
>
> Referenced from: `standards.md` → *Object Authoring Is the Only Path for
> Content Operations*, and `cms/liferay-context.md` §2.

**Start here:** `/web/qatar-chamber/object-authoring`

Object Authoring is the staff-facing screen for editing website content. Every
piece of text, image and link on the site lives in a **Liferay Object**, and this
tool gives each Object a plain page where you can list its entries, add one, edit
one, see how it will look on the real website, and publish it — without opening
the Control Panel and without touching a page or a fragment.

It is the same content the Control Panel edits. Use whichever you prefer; this
tool adds three things the Control Panel does not have: the **Arabic boxes beside
the English ones**, a **live preview of the actual website page**, and **draft →
publish** in one place.

> Looking for what a particular field means? See `CONTENT-ADMIN-GUIDE.md` — it
> walks the website page by page and names the Object and fields behind every
> section. This guide is about the *tool*, not the fields. (In this repo the
> equivalent is `cms/Content-Admin-Guide.docx`, cross-referenced in
> `cms/liferay-context.md` §13.)

---

## 1. Getting in

1. **Sign in first.** The authoring pages are staff-only: a visitor who is not
   signed in gets a 404, not a login prompt. If the URL "does not exist", you are
   signed out.
2. Open **`/web/qatar-chamber/object-authoring`**.
3. You get **Object Authoring Forms** — one link per Object you can author, e.g.
   *News Article*, *Hero Banner Slide*, *Useful Link*.
4. **Filter objects** — type in the box (`law`, `banner`, `newsletter`…) to
   narrow the list instead of scrolling it. The count on the right follows the
   filter (e.g. `2 of 193 Objects`).

If you can see the page but the form area is empty, your account can *view* the
page but has no **Add** permission on that Object. Ask a developer or a site
administrator to grant it.

### What is not here, on purpose

Objects that are filled in by **visitors** — form submissions, registrations and
subscriptions — have no authoring page, because nobody hand-writes them:

`AddCompanyRequest`, `B2BCompanyRegistration`, `B2BContactRequest`,
`CircularSubscriber`, `ConsultationRequest`, `EOISubmission`,
`EOISubmissionDocument`, `EventCoverageRequestSubmission`,
`EventMediaPRSupportRequest`, `EventRegistration`, `HallBookingRequest`,
`Inquiry`, `InterviewRequestSubmission`, `MediaInquirySubmission`,
`MediationRequest`, `NewsletterSubscriber`, `OpportunityInquiry`,
`OpportunitySubmission`.

Read those in the Control Panel (**Global Menu ▦ → Control Panel → Objects**).
They hold people's names, e-mail addresses and phone numbers — treat them
accordingly.

---

## 2. The manage page

Clicking an Object opens its own page, `/web/qatar-chamber/manage-<object>` — for
example `/web/qatar-chamber/manage-news-article`. Four parts, top to bottom:

| Part | What it is |
|---|---|
| **Left navigation** | Every Object, with the current one highlighted, plus its own **Filter** box and an **Objects Home** link back to the index. |
| **Entry list** | The existing entries: *Entry*, *Status*, *Last modified*, and the row actions. The heading shows a count, e.g. `12 total · 2 drafts`. |
| **Form** | The fields of the Object, then the two buttons **Save as Draft** and **Submit for Publishing**. |
| **Preview** | *"Preview — how this record renders on the site"* — a live frame of the real page. See §6. |

### Row actions

| Action | What it does |
|---|---|
| **Edit** | Loads that record into the form on the same page (the URL gains `?editEntry=…`). |
| **Preview** | Switches the preview frame to that record. Ctrl/Cmd-click or middle-click opens it in a new tab instead. |
| **Control panel** | Opens the same record in Liferay's own Objects admin, in a new tab. Useful for a field this form does not show. |
| **Delete** | Asks to confirm, then deletes. **There is no undo and no recycle bin.** To take something off the site without losing it, un-tick its `activeStatus` field, or unpublish it (§4). |

An Object with no entries yet says *"No entries yet. Use the form below to add
one."*

Status badges on each row are `APPROVED` (published) or `DRAFT`.

---

## 3. Adding an entry

1. Open the Object's manage page. The form is already in "add" mode — if it is
   not (a blue bar says *Editing …*), click **Cancel and add a new entry
   instead** in that bar.
2. Fill the fields. Required ones are marked with `*`; the save is refused until
   they are filled.
3. Fill **both languages** — see §5.
4. Choose a button:
   - **Save as Draft** — saved, visible to staff, **invisible to visitors**.
   - **Submit for Publishing** — live on the website.
5. The page comes back with **"Draft saved."** or **"Saved and submitted for
   publishing."**, and the preview frame opens on the record you just saved.

**If the save is refused,** a red bar lists the reasons in plain words (e.g.
*"Another department already uses this English name."*). Fix those fields and save
again — nothing was created.

> **Ordering:** any `displayOrder` / `homeDisplayOrder` field is numbered in
> multiples of 100 — `100, 200, 300 …`, lowest shows first. Never use an
> in-between value like `150`; the gaps exist so a later insert does not force
> you to renumber the whole list.

---

## 4. Editing an existing entry

1. Click **Edit** on the row. The record's values load into the form and a blue
   bar names what you are editing and its current status.
2. Change what you need, then **Save as Draft** or **Submit for Publishing** —
   both now *update* this record instead of creating a new one.

Anything the form does not show is preserved. An attachment you do not re-pick
keeps its current file.

### A published record cannot be turned back into a draft directly

On a published (approved) record, **Save as Draft** is greyed out. The blue bar
carries an **Unpublish to edit as draft** button instead:

1. Click it and confirm. The record **comes off the live site immediately** and
   becomes an ordinary draft.
2. Keep editing and saving drafts as long as you like.
3. **Submit for Publishing** when it is ready to go back up.

If one field could not be filled in automatically, a red bar names that field and
says everything else loaded — check it before saving.

The bar reads, for example:
*"Editing QCDEMO-129395-VMO-VISION (approved). It is published, so Save as Draft
is unavailable until you unpublish it. Cancel and add a new entry instead
[Unpublish to edit as draft]"*

---

## 5. English and Arabic

The site is bilingual, and there are two shapes of field. Both must be filled.

**Localized fields** get a **second box beside the English one**, labelled with
the field name plus **— العربية**, typed right-to-left. A rich-text field gets a
second, right-to-left editor. Type the Arabic there.

**Suffix pairs** are two ordinary fields whose names end in `…En` and `…Ar`
(e.g. `bannerTitleEn` / `bannerTitleAr`). Fill both.

Worth knowing:

- **An empty Arabic box is not the same as empty text.** Leaving it blank removes
  the Arabic translation, and the Arabic site then falls back to the English.
  That is deliberate — better than rendering a blank space.
- **Editing only the English never wipes an existing Arabic translation.**
- **On a brand-new record the Arabic is saved a moment after the record itself.**
  Wait for the **"Arabic content saved for this record."** message before
  navigating away. If you instead see *"the record was saved but its Arabic
  content was not"*, open **Edit** on the new record and enter the Arabic again.

---

## 6. Previewing before you publish

The preview panel sits under the entry list and shows the **real website page**
rendering the record you are working on — including a **draft**, which is what
makes it worth using. Visitors still see nothing until you publish.

| Control | What it does |
|---|---|
| **Page tabs** | One tab per page that renders this Object (e.g. *Home*, *News Article (detail)*). An Object that no public page renders shows *Field view* — a plain list of the stored values. |
| **EN / AR** | Renders the frame in that language, whatever your own account language is. Use **AR** to check the Arabic you just typed. |
| **Show all drafts** | Renders every unpublished entry of this Object at once, as the page would show them. |
| **Refresh** | Reloads the frame after a save. |
| **open in a new tab** | The same preview, full width. |

The frame carries a maroon banner, e.g. *"PREVIEW — showing an unpublished
(draft) vmosections record. Visitors do not see this."*, or with **Show all
drafts** ticked, *"PREVIEW — showing 1 unpublished vmosections record(s).
Visitors do not see these."* A published record previewed in field view reads
*"PREVIEW — published record, shown as stored."*

There is also a generic **`/web/qatar-chamber/object-preview`** page: the
*Preview* link of an Object with no public page of its own lands there and lists
the record's fields, with a **← Back to Object Authoring** link.

---

## 7. Images and files (attachment fields)

- An attachment field shows the file already on the record: a **thumbnail** for
  images, the **file name and size**, and **Preview · Download** links.
- **Leaving the field alone keeps the current file.** Use **Select File** only to
  *replace* it.
- **Remove file** clears the attachment and **Undo remove** puts it back; neither
  takes effect until you save. A required field refuses to be cleared.
- Prefer file names **without spaces**. Each field accepts certain types, usually
  `jpg, png, svg` — the field's help line says which (e.g. *"Upload a
  .jpg,.png,.svg no larger than 2 MB."*).
- If a field says *"The stored file content is missing, so it cannot be previewed
  or downloaded"*, the file's content is genuinely gone from the server. Pick a
  file to replace it.

The block on a record that already has a file reads:
*"Current file: vmo-vision.jpg (94 KB) / Preview · Download / Use "Select File"
only if you want to REPLACE it — leaving it alone keeps this file. / Remove
file"*

---

## 8. Quick reference

| I want to… | Do this |
|---|---|
| Find the Object behind a page section | `CONTENT-ADMIN-GUIDE.md` §2, the website map |
| Add content | Manage page → fill the form → **Submit for Publishing** |
| Work on something unfinished | **Save as Draft** — staff see it, visitors do not |
| Take something off the site but keep it | Un-tick `activeStatus`, or **Unpublish to edit as draft** |
| Put a draft live | **Edit** → **Submit for Publishing** |
| Edit a published record | **Unpublish to edit as draft**, edit, publish again |
| Check the Arabic | Preview panel → **AR** |
| See all unpublished work | Preview panel → **Show all drafts** |
| Reorder items | `displayOrder` in multiples of 100, lowest first |
| Remove permanently | **Delete** — no undo |

## 9. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| The URL 404s | You are signed out. Sign in and reopen it. |
| Page loads, no form | Your account has no **Add** permission on that Object. Ask an administrator. |
| *"Could not load entries (…)"* | The Object's data call failed, usually a permission on the Object. Report the message as shown. |
| Red bar on save, listing reasons | Validation. Fix those fields and save again; nothing was saved. |
| **Save as Draft** greyed out | The record is published. Use **Unpublish to edit as draft** first. |
| Saved, but visitors do not see it | It is a draft (check the *Status* column), or its `activeStatus` is off. |
| Arabic site shows English | The Arabic box for that field is empty. |
| An Object has no link on the index | Either it is a visitor-submission Object (§1), or it is new and a developer still has to generate its page. |

---

*Deploying or repairing this tool is a developer task — see
`build-resources/pages/object-authoring/README.md`.*
