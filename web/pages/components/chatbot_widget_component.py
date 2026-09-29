"""
web/pages/components/chatbot_widget_component.py — ChatbotWidgetComponent.

Cross-page component for PBI 131021 / QC-BOT-001 "Chatbot Widget & Bilingual
Generative Assistance" — the floating launcher + chat window that appears on
EVERY public page (bottom-right corner), same cross-page nature as the
header/footer. Placed under `pages/components/` per this project's component
exception (never duplicated into a page folder) — automation-standards.md's
"Page Object / Screen Object rules" and this project's
`.claude/context/active/standards.md` "Automation Structure" section, which
lists the GLOBAL cross-page components (header/footer/language_switcher/
accessibility_tools/newsletter_subscription) as living here flat, not in
their own page folder. QC-BOT-001 is not yet in that table (it predates this
PBI), but the same rule applies by the identical cross-page rationale — noted
here as the placement judgment call, per the routing instructions for this
batch. Service/Module code for this feature is `CHATBOT` (a project-specific
Axis-2 tag, distinct from `GLOBAL`) — see
`.claude/context/active/standards.md`'s Service/Module Codes table.

FILE-NAMING DEVIATION (disclosed, per the routing instructions' own "follow
the found convention instead" clause): the routing brief for this batch
suggested `chatbot_widget_page.py`. Every existing cross-page component
already living in this exact folder instead uses a `<name>_component.py`
suffix with a `<Name>Component` class (`header_component.py` ->
`HeaderComponent`, `footer_component.py` -> `FooterComponent`,
`accessibility_tools_component.py`, `language_switcher_component.py`,
`newsletter_subscription_component.py`) — a real, consistent, pre-existing
convention for cross-page widgets in this repo. Followed that instead:
`chatbot_widget_component.py` / `ChatbotWidgetComponent`, matching every
sibling in `pages/components/` (test module name/suffix,
`test_chatbot_widget_web.py`, was already consistent with the existing
`test_<component>_web.py` pattern and needed no change).

Composes HeaderComponent (`self.header`) to reuse its already-extracted
LANGUAGE_SWITCHER locator and switch_to_arabic()/switch_to_english() methods
for the language-switch case (ADO-137457) — same reuse pattern
`language_switcher_component.py` already established for its own PBI, not a
new selector declared here for an element another component already owns.

--- CLI-first extraction log ---

`tools/extract_locators.py`'s default 40-row cap and its "only known
interactive/labelled elements" harvest missed the widget entirely on the
first plain pass against https://qcdev.ihorizons.com/home — re-run with
`--max 200 --find chat` surfaced it:

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home \
        --viewport 1920x1080 --max 200
    -> [role] uniq=1  get_by_role("button", name="Open chat")   -> "Open chat"

That single row is the LAUNCHER in its collapsed (idle) state — the harvester
cannot see the tooltip (a non-interactive `role=tooltip` div), the chat
panel's internal elements (only mounted/visible post-click, and several
carry no distinct accessible name — the mic/send icon buttons DO have
aria-labels but the message bubbles/avatars do not), or computed layout
(bounding boxes, gradient background, RTL mirroring) — the documented
"state the script can't reach deterministically" / "needs interactive
reasoning" condition (automation-standards.md's Tooling-priority table).
Resolved the same way every sibling component in this tree resolves it: one
additional disclosed Playwright script (still CLI/shell, never the
Playwright MCP) that reuses BasePage's own license-gate/announcement-overlay
guard sequence before reading/interacting with the live DOM — clicking the
launcher, reading `outerHTML`, sending real messages, and reading computed
styles/bounding boxes across desktop/tablet/mobile viewports and EN/AR
locales.

Real, CLI-verified structure (`#qcChatbot`, dir flips with the page locale):

    div#qcChatbot.qc-chatbot[.is-open when expanded]
      div.qc-panel[role=dialog][aria-label="Qatar Chamber chat"]   (PANEL — always in the DOM; CSS-hidden when collapsed, not removed)
        div.qc-header                                              (HEADER — maroon gradient background-image)
          div.qc-header-brand > img.qc-header-logo[alt="Qatar Chamber"]
          button.qc-minimize[aria-label="Minimize chat"]           (MINIMIZE_BUTTON — the "–" header control)
        div.qc-body                                                (BODY — message thread)
          div.qc-msg.qc-msg-bot > div.qc-avatar > img, div.qc-bubble > p
          div.qc-msg.qc-msg-user > div.qc-bubble > p               (no avatar on user messages — confirmed live)
        form.qc-composer
          button.qc-mic[aria-label="Record a voice message"]
          input.qc-input[placeholder="Ask Something..."][aria-label="Message"]
          button.qc-send[type=submit][aria-label="Send message"]
      div.qc-launcher-wrap
        div.qc-tooltip#qcChatbotTooltip[role=tooltip]              "Can I help you ?"
        button.qc-launcher[aria-describedby=qcChatbotTooltip]      (LAUNCHER — aria-label toggles "Open chat" / "Close chat")

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected — several directly affect how the 18 cases
below had to be scripted):

  - **No separate floating close (×) control exists.** ADO-137465/137469's
    premise of "a separate circular maroon close (×) control below/outside
    the chat panel, distinct from the header's minimize control" does NOT
    match the live implementation: there is exactly ONE launcher button
    (`.qc-launcher`) that toggles between the idle "Open chat" state (shows
    the Qatar Chamber logo icon) and the open "Close chat" state (its
    `svg.qc-close-icon` renders instead, aria-label flips to "Close chat").
    close_chat() below clicks this SAME button — the narrowest reasonable
    reading of "the close control", not an invented separate locator for a
    control that was never observed live.
  - **Minimize and close are functionally identical live.** Clicking
    `.qc-minimize` (the header's "–" control) produces the EXACT same
    result as clicking the launcher to close: `#qcChatbot` loses its
    `is-open` class, `.qc-panel` becomes not-visible, and the launcher
    reverts to its idle "Open chat" aria-label — confirmed by reading
    `#qcChatbot`'s class list and the launcher's aria-label directly before
    and after each action. There is no distinct "minimized indicator" state
    separate from the full-idle state that ADO-137468 describes ("the
    launcher becomes visible again in its (non-idle-tooltip)
    minimized-indicator state, distinct from a full close"). is_chat_open()
    / is_launcher_idle() below read the real, single idle state honestly —
    no separate indicator exists to assert on.
  - **The conversation thread is retained across BOTH minimize→reopen AND
    close→reopen** — confirmed live end-to-end: opened chat, sent a real
    message, read 3 `.qc-msg` elements (greeting + user + bot reply), then
    (separately) minimized-then-reopened and closed-then-reopened — both
    times the reopened panel showed all 3 original messages, none lost or
    duplicated. Because minimize/close are the same CSS-visibility toggle
    (not a state teardown), ADO-137465's "actual thread-history behavior is
    recorded per the observed result" resolves to RETAINED, not reset —
    scripted as an explicit retained-thread assertion, the real observed
    behavior, not an assumption.
  - **Live backend responds in-language and reasonably quickly** (~1-4s,
    well within a bounded `page.wait_for_function` poll): an EN question
    ("What are Qatar Chamber's working hours?") got an English reply
    ("I'm sorry, I couldn't find specific information about Qatar Chamber's
    working hours."); the identical AR question
    ("ما هي رسوم العضوية في غرفة قطر؟") got a full Arabic-script reply. Both
    are canned/ungrounded-sounding fallback answers rather than a grounded
    hit, but that is a content-quality judgment explicitly out of scope for
    automation (see Axis 1b's "chatbot subjective response-quality
    judgment" Manual criterion in this project's tag taxonomy) — these
    cases assert presence/language-detection only, never exact wording.
  - **Empty-send**: clicking `.qc-send` with an untouched (never-focused)
    empty input adds NO message (`.qc-msg` count unchanged) — matches. BUT
    the input does NOT retain focus afterward: `document.activeElement`
    resolves to the send `<button>` itself (a real `type="submit"` button
    receiving focus on click is standard browser behavory), not back to the
    input, contradicting ADO-137470's "input field retains focus" wording.
    Scripted per the case's exact stated expected result regardless (a
    real, honestly-reported mismatch, not silently adjusted — mirrors this
    project's established precedent, e.g. header_component.py's
    box-shadow finding).
  - **Whitespace-only send** ("   "): no new `.qc-msg` added, and the input
    genuinely RETAINS the whitespace value afterward (not cleared) —
    matches one of ADO-137471's two explicitly-allowed outcomes ("cleared
    OR retains the whitespace").
  - **Widget position mirrors under RTL** — a mismatch against ADO-137457's
    stated expectation. EN home: launcher box `x=1830,y=990,w=66,h=66` at a
    1920x1080 viewport (24px inset from the right/bottom edges). AR home
    (`/ar/home`, `#qcChatbot[dir="rtl"]`): launcher box `x=24,y=990,w=66,
    h=66` — the SAME 24px inset, but now measured from the LEFT edge, i.e.
    the widget moved to the bottom-LEFT corner under RTL. ADO-137457
    explicitly expects "no mirroring of the widget's own corner placement";
    the real implementation DOES mirror it. Scripted per the case's exact
    stated expectation (assert bottom-right) regardless — a legitimate,
    honestly-reported failure against the live RTL page, not adjusted here.
  - **Bottom-right inset varies by viewport but stays small and consistent
    per axis**: 24px at both 1920x1080 (desktop) and 768x1024 (tablet),
    12px at 375x667 (mobile) — all comfortably inside a generous tolerance,
    so is_launcher_bottom_right() below checks a bounded edge-gap rather
    than one hardcoded pixel value (the cases never state an exact pixel
    inset, only "bottom-right corner").
  - **Touch target**: the launcher renders 66x66 at ALL three tested
    viewports (desktop/tablet/mobile) — comfortably above the ~44x44
    minimum comfortable/tappable touch-target size ADO-137461/137462 ask
    for.
  - **No horizontal page-level scroll** introduced at any tested viewport,
    open or collapsed (`document.documentElement.scrollWidth` equalled the
    configured viewport width in every case) — matches ADO-137460/61/62.
  - **RTL composer mirrors correctly**: on the AR page the send button's
    bounding box sits to the LEFT of the input's (`x=42` vs `x=96` at a
    1920px viewport) — matches ADO-137459's expected RTL composer layout.
    On the EN page the send button sits to the RIGHT of the input
    (`x=1836` vs `x=1578`) — matches ADO-137458's expected LTR layout.
  - **Bot vs. user bubble alignment/styling**: sending "hello" and reading
    both bubbles' boxes against the panel's own box confirmed the user
    bubble sits near the panel's right edge (`~18px` gap) while the bot
    bubble sits near its left edge (`~55px` gap) — a genuine left/right
    split, not just a color difference. Live computed styles: user bubble
    `background-color: rgb(138, 21, 56)` (maroon) / `color: rgb(255, 255,
    255)` (white); bot bubble `background-color: rgb(242, 242, 242)`
    (light gray). Bot messages render an avatar (`.qc-avatar`, 1 per bot
    message); user messages render none — matches ADO-137463's described
    design exactly.
  - **Header is a real maroon gradient**, not a flat fill: computed
    `background-image` on `.qc-header` reads
    `linear-gradient(100deg, rgb(109, 16, 40) 0%, rgb(138, 21, 56) 45%,
    rgb(163, 43, 70) 100%)` — matches ADO-137458/137459's "maroon gradient
    bar" wording.
  - **Header wordmark is a single embedded logo image**
    (`.qc-header-logo`, `alt="Qatar Chamber"` on BOTH EN and AR pages — not
    a separate bilingual text node like the site header's own logo/wordmark
    handles). The PBI's screenshots describe a separate Arabic wordmark
    "غرفة قطر" rendered alongside "QATAR CHAMBER" — the live widget bakes
    whatever wordmark it shows into one raster `<img>`, so this component
    only asserts the image renders and is visible, never OCRs its pixel
    content to confirm the exact bilingual wordmark text.

--- PBI 131022 (QC-BOT-002 "Controlled & Grounded Responses") batch —
extends this SAME class, no locator/method already present above is
re-declared. Placement follows the routing brief's own recommendation
(flat under pages/components/, same file the PBI 131021 batch already
built) rather than a new `chatbot_page.py` — this file/class is already
the established convention for this cross-page widget in this repo.

--- CLI-first extraction/probe log for this batch (disclosed, one-off
scoped Playwright scripts against https://qcdev.ihorizons.com, reusing the
same license-gate/overlay guard sequence as every prior probe in this file
— never the Playwright MCP) ---

Real, CLI-verified findings that directly change what these 29 cases can
honestly assert (several are genuine mismatches against the case text,
reported here and in the test module, not silently adjusted):

  - **No visually distinct fallback banner/style exists.** Sent a genuinely
    grounded-hitting query, a low-confidence query, and an out-of-domain
    query, then read each reply's computed style: EVERY bot reply — grounded
    or fallback — renders in the IDENTICAL `.qc-bubble` (same
    `background-color: rgb(242, 242, 242)`, same `color: rgb(63, 63, 63)`,
    no extra class such as `.qc-fallback`/`.qc-banner`/`.qc-notice`, no
    icon). ADO-137523's premise of "a visually distinct banner/style" does
    NOT match the live implementation — scripted per the case's exact
    wording regardless (a legitimate, honestly-reported failure against the
    live app, not adjusted to match it).
  - **The only real, verifiable signal for "grounded/sourced from the
    approved dataset" is a literal trailing citation line the live backend
    appends to a genuinely matched reply**: `Source: <Dataset Name>` in
    English (confirmed: "...Source: New Membership" for "What documents do
    I need for membership?"), `المصدر: <Dataset Name>` in Arabic (confirmed:
    "...المصدر: العضوية الجديدة..." for the Arabic equivalent query). No
    other structural marker (class, icon, color) distinguishes a grounded
    reply from a fallback — `is_grounded_reply()` below checks for this
    marker as the narrowest verifiable proxy, not an assumption.
  - **The case's own literal "grounded-trigger" query, "What are Qatar
    Chamber's membership types?", does NOT resolve to a grounded/sourced
    reply live** — it returns the same genuinely-no-match fallback text
    ("I apologize, but I couldn't find information on that topic.") as a
    query with zero dataset relevance. This is a real, disclosed mismatch
    that is MATERIAL to ADO-137534 (English grounded-threshold case), which
    uses this exact query and expects a grounded answer. Scripted per the
    case's literal query text regardless — a legitimate, honestly-reported
    failure, not substituted with a query that happens to pass. By
    contrast, "What documents do I need for membership?" (ADO-137545's own
    literal query) DOES reliably return one single grounded, sourced reply
    live — used as the confirmed-grounded reference query where a case's
    own wording does not require a specific query text.
  - **Two distinct EN fallback strings observed, NEITHER equals ADO-137536's
    stated verbatim "Please contact support"**:
    - "I apologize, but I couldn't find information on that topic." (a
      genuinely no-match query, e.g. "What is Qatar Chamber's phone
      number?", "What are Qatar Chamber's working hours?")
    - "I apologize, but I'm only able to assist with questions related to
      Qatar Chamber and its services." (an out-of-scope/off-topic query,
      e.g. the Halls Reservation date-change query ADO-137536 itself uses,
      and "What is the capital of France?")
    Arabic equivalents confirmed live: "أعتذر، لم أتمكن من العثور على معلومات
    حول هذا الموضوع." and "أعتذر، يمكنني فقط المساعدة في الأسئلة المتعلقة
    بغرفة قطر وخدماتها." respectively. ADO-137536/137537 are scripted per
    their own stated expected wording regardless (137536 as an exact literal
    check — a legitimate, disclosed failure; 137537 as a detectably-Arabic
    fallback check, since the case supplies no literal Arabic string to
    compare against — the narrowest reasonable reading, not invented).
  - **Resubmitting an identical query before the first reply lands does NOT
    corrupt the thread** — confirmed live: firing "What documents do I need
    for membership?" twice in immediate succession (no wait between sends)
    produced exactly 2 new user bubbles and 2 new bot bubbles, in order, no
    merge/loss — a genuine, observed PASS candidate for ADO-137547.
  - **Blocking the widget's own real message endpoint produces a genuine,
    distinct error state, not a hang.** The live composer POSTs to
    `https://qcdev.ihorizons.com/o/qc-chatbot/v1.0/message` (captured via a
    `page.on("request", ...)` listener across a real send). Aborting exactly
    this endpoint (`page.route("**/o/qc-chatbot/**", ...)`, the same
    "block the real bundle path" technique this file's PBI-131021 sibling
    `accessibility_tools_component.py` already established for its own
    blocked-script simulation) and sending a query produces a real, distinct
    bot bubble reading "Sorry, something went wrong reaching the assistant.
    Please try again." within a few seconds — a genuine, observed PASS
    candidate for ADO-137549's "surfaces a clear error/retry state rather
    than hanging". Unblocking the route and resending the same query
    afterward returns a normal grounded, sourced reply — confirmed live, not
    assumed.
  - **XSS-ish input renders as inert, escaped plain text.** Sending
    `<script>alert(1)</script>` puts the literal string
    `<script>alert(1)</script>` into the user bubble's `innerText` (browser-
    decoded from the escaped `&lt;script&gt;...` markup Playwright's
    `outerHTML` confirmed underneath) — no `dialog` (alert) event fires, no
    application error, and the bot still replies normally afterward — a
    genuine, observed PASS candidate for ADO-137543.
  - **Precondition-gated cases documented as fixture requirements, not
    invented or silently skipped-without-reason:**
    - ADO-137539 (unpublished/removed dataset content must not resurface) —
      unpublishing a specific CMS dataset is a CMS/backend action outside
      this component's and Playwright's reach on the read-only public site;
      no admin credential or CMS path to that dataset lookup was available
      this session. Skipped with a concrete reason, not scripted as an
      assumed pass.
    - ADO-137545 (highest-confidence dataset wins when two datasets match at
      0.72 and 0.91) — the REAL, verifiable structural claim ("Chatbot
      returns exactly one grounded answer, no merged/duplicated content") IS
      scripted and passes live for the case's own query. The specific
      confidence-priority claim (0.91 beats 0.72) cannot be verified without
      seeding two competing published datasets at those exact scores — a
      documented fixture requirement, noted in the test rather than
      silently dropped.
    - ADO-137546 (a query engineered to score exactly at the threshold) —
      no UI-reachable way to engineer or observe a query's exact backend
      confidence score exists; skipped with a concrete reason.
    - ADO-137534/137536's "check interaction log" step — the case's own
      wording explicitly allows this: "log verification may require a
      GCP-side check — if inaccessible to automation, assert only the
      UI-visible response and flag the log-step as a known gap." No GCP
      console access was available this session; the log-check step is
      flagged in the test docstring and not asserted, per the case's own
      permission to do so — this is NOT a silent gap, unlike the three
      bullet points above which required an explicit `skip`.

--- PBI 131023 (QC-BOT-003 "Guided Conversational Flows & Hybrid Q&A")
batch — extends this SAME class, no locator/method already present above is
re-declared.

*** HEADLINE FINDING (reported to the QA Manager, not silently adjusted —
material to nearly every case in this batch): the "guided conversational
flow" concept this PBI's cases assume (multi-step flows with quick-reply
buttons, inline images, a final CTA button, restart/abandon controls, a
Published/Draft/Unpublished lifecycle) DOES NOT EXIST on the live
application. Two independent, CLI-first probes confirm this exhaustively,
never assumed: ***

  1. **Raw backend API schema** — captured the real `/o/qc-chatbot/v1.0/
     message` POST response via a `page.on("response", ...)` listener
     across 3 distinct live queries (a grounded "New Membership" hit, a
     fallback miss, a grounded "Halls Booking" hit). Every single response
     is exactly `{"sessionId": "<guid>", "reply": "<flat string>"}` — no
     `flow`, `step`, `options`, `buttons`, `quickReplies`, or `cta` field
     of any kind, in any response, ever.
  2. **DOM class-name sweep** — after opening the widget and sending a
     real message, enumerated EVERY distinct CSS class present anywhere
     under `.qc-panel`: `qc-header`, `qc-header-brand`, `qc-header-logo`,
     `qc-minimize`, `qc-body`, `qc-msg qc-msg-bot`, `qc-avatar`,
     `qc-bubble`, `qc-msg qc-msg-user`, `qc-link`, `qc-composer`,
     `qc-mic`, `qc-mic-stop`, `qc-input`, `qc-send`. No
     `quick-reply`/`option`/`button`/`cta`/`flow`/`step` class exists
     anywhere in that list.
  3. Additionally swept 15 distinct real trigger phrases across both
     languages, covering every plausible guided-flow entry point the
     cases imply (membership application steps, hall-booking steps,
     committee-joining steps, generic "menu"/"help"/"flows"/"start"):
     ZERO `<button>` elements ever rendered inside `.qc-body` (the
     composer's own mic/send buttons live outside `.qc-body` and are
     unrelated), at any point, for any query.

  **Conclusion: the chatbot is a single-turn grounded/fallback Q&A engine
  identical in kind to QC-BOT-002 (PBI 131022) — there is no multi-step
  state machine, no quick-reply/button affordance, and no flow-selection
  menu of any kind reachable or observable live.** This is the single most
  important finding of this batch. Per Result Integrity ("when in doubt,
  let it fail... a visible red is always preferred over a quiet skip"),
  every case below whose very first expected result is directly checkable
  against the real DOM (a flow/quick-reply/CTA-button appears) is scripted
  as a genuine, disclosed **failing** assertion rather than silently
  skipped — the test attempted the real Arrange/Act steps live and
  observed the feature's absence, which is itself the honest result.
  `skip` is reserved, per the usual rule, for the small subset of cases
  whose precondition needs backend/CMS control this session had no path
  to (Draft/Unpublished flow status, broken-link test data) — same
  category as PBI 131022's ADO-137539/137546 skips.

  Two things this same probe DID find, real and reusable, keeping several
  cases genuinely automatable despite the above:
    - **Bot replies DO contain real embedded hyperlinks** — the same
      `a.qc-link` element `is_grounded_reply()`'s sibling probes already
      encountered (e.g. `https://www.qatarchamber.com/membership/
      new-membership`, `target="_blank"`). Clicking it in a real browser
      context opens a genuine new tab and navigates (confirmed:
      `context.expect_page()` around the click landed on
      `https://www.qatarchamber.com/new-membership/`, a same-topic
      redirect of the linked URL) — a real, live mechanism reused for
      ADO-137570 instead of a non-existent "flow step link".
    - **Bullet-style lists render as real `<ul><li>` markup** (the
      backend's markdown-ish `*` bullets get converted client-side) —
      counted as real "structured content" for ADO-137554's text
      requirement, alongside the link; only the image/button parts of
      that case are the disclosed gap.

  **Streaming-response timing nuance discovered in this batch** (distinct
  from — and does not retroactively change — PBI 131022's already-scripted
  tests): the bot's reply text renders progressively AFTER
  `.qc-msg-bot` element count already increments (a client-side typing/
  streaming animation). Confirmed live: reading `last_bot_message_text()`
  immediately after `wait_for_bot_reply_count()` returned an EMPTY string
  on a fresh `.qc-bubble` that filled in ~1-2s later. `wait_for_bot_reply_
  text()` below additionally polls for non-empty bubble text and is used
  by every NEW test in this batch that reads reply content — existing
  PBI 131021/131022 tests are untouched (they were not observed to hit
  this race and are out of this batch's scope to re-touch).

  **Case-by-case dispositions this finding drives** (detailed per-test in
  the test module):
    - ADO-137550, 137556, 137566, 137567 — no guided-flow dependency;
      scripted and PASS on real live behavior.
    - ADO-137552, 137553, 137554, 137557, 137560, 137564, 137565, 137568,
      137569, 137571, 137572, 137597, 137598 — scripted as genuine,
      disclosed FAILING assertions (real Arrange/Act attempted, expected
      flow/quick-reply/CTA element never appears).
    - ADO-137558, 137559 — SKIPPED: the case's own wording explicitly
      permits this ("if discoverable/documentable live; otherwise
      document as untestable without CMS/backend access") — no
      Draft/Unpublished-status flow is discoverable because no flow
      concept exists at all, and no CMS/admin path to construct one this
      session.
    - ADO-137561 — the flow-abandonment premise doesn't apply (no flow to
      abandon), but the case's real, testable spirit — ask an unrelated
      question after an unanswered prior message and get a normal,
      unrelated direct answer — is scriptable and PASSES; documented as a
      substitution, not invented.
    - ADO-137562, 137563, 137573 — SKIPPED, same "no controllable broken-
      link/step test data" caveat the case text itself allows, compounded
      by there being no flow step to break in the first place.
    - ADO-137570 — PASSES using the real embedded reply hyperlink in
      place of a non-existent "flow step link" (documented substitution).

--- PBI 131024 (QC-BOT-004 "Speech-to-Text (Voice Input)") batch — extends
this SAME class, no locator/method already present above is re-declared.

*** HEADLINE FINDING (verified FIRST, before scripting anything, per this
batch's own routing instructions — the opposite outcome from PBI 131023):
Speech-to-Text is REAL and FUNCTIONING live. `button.qc-mic` (already
declared above as MIC_BUTTON, confirmed present since the PBI-131021 batch)
is not decorative — clicking it drives a real, working voice-capture
pipeline. Confirmed via four independent, CLI-first Playwright probes
against https://qcdev.ihorizons.com (never the Playwright MCP), never
assumed: ***

  1. **Clicking the mic genuinely calls `navigator.mediaDevices.
     getUserMedia({audio:true})`** — confirmed by wrapping (not stubbing)
     the real browser API before any interaction. `window.SpeechRecognition`
     / `webkitSpeechRecognition` EXISTS as a Chromium API but is NEVER
     constructed by the app (`speechRecognitionConstructed: 0` across every
     probe) — the app does not use the client-side Web Speech API; it
     captures raw audio and transcribes server-side.
  2. **With a real (headless-safe) fake MediaStream supplied** (Web Audio's
     `createMediaStreamDestination()` — a genuine audio-bearing MediaStream,
     the only way to satisfy `getUserMedia({audio:true})` without physical
     mic hardware in a headless run; the SAME class of disclosed browser-
     API substitution this file's `block_chat_endpoint()`/
     `start_dialog_watch()` probes already established, not an invented app
     behavior), the REAL app code drives a REAL `MediaRecorder` against it:
     `start` → `dataavailable` (real non-zero byte payload) → `stop` events
     all fired, confirmed via a wrapped (not stubbed) `MediaRecorder`
     constructor.
  3. **The composer's real, live recording-state DOM contract** (confirmed
     via `outerHTML` reads before/during/after a real click cycle):
     - Idle: `<button class="qc-mic" aria-label="Record a voice message"
       aria-pressed="false">`. Input placeholder: "Ask Something..."
       (matches PBI 131021's ADO-137456 finding), input enabled.
     - Recording (mic clicked, stream acquired): button gains
       `is-recording` class, `aria-pressed="true"`, `aria-label` flips to
       **"Stop recording and send"**. The composer `input.qc-input` becomes
       `disabled` and its placeholder changes to **"Recording... tap to
       send"**.
     - Clicking the SAME button again ("stop"): the captured audio blob is
       POSTed to a real, confirmed endpoint, **`/o/qc-chatbot/v1.0/audio`**
       (captured live via a `page.on("request", ...)` listener across a
       real record→stop cycle — same capture technique this file's
       `CHAT_ENDPOINT_PATTERN` already used for the text endpoint,
       PBI 131022). The button reverts fully to its idle state (class,
       aria-label, aria-pressed all revert) and the input re-enables with
       its normal placeholder — all within the same bounded window this
       file's other async-reply waits already use (no `time.sleep()`).
  4. **The real `/o/qc-chatbot/v1.0/audio` response schema, captured live**:
     `{"transcript": "<string>", "reply": "<string>", "sessionId": "<guid>",
     "languageCode": "en", "buttons": [...]}`. On a genuinely empty/
     unrecognized transcript (the probe's synthetic tone is not real
     speech, so the server-side STT correctly returned `""`), the app
     rendered a graceful fallback reply ("Hello, I am your assistant, how
     can I help you?") — no crash, no hang.

  **Real, live rendering contract for a completed voice message** (directly
  material to how several of the 13 automated cases below had to be
  scripted — several are genuine, disclosed MISMATCHES against the case
  text, reported here and in the test module, not silently adjusted):

  - **On "stop", the widget auto-uploads AND auto-sends in one step — there
    is NO intermediate "transcribed text lands in the composer input field
    for editing" state at all.** The user bubble that appears is a
    DISTINCT `div.qc-msg.qc-msg-user.qc-msg-voice` (not the plain
    `.qc-msg-user` a typed message renders), containing:
    - `audio.qc-voice-player` — a real, playable embedded recording
      (`controls`, `src="blob:..."`), and
    - `div.qc-voice-transcript` — the transcript text, rendered directly
      into the bubble, never into `input.qc-input`.
    A real bot reply bubble follows immediately, exactly like a typed
    query's reply (same avatar/bubble/alignment contract this file's
    PBI-131021 findings already established). This is a MATERIAL, genuine
    mismatch against **ADO-137590's** entire premise ("the transcribed text
    in the chat input field is editable before sending") — the live app
    never puts transcribed text in the input field at all, so there is no
    edit step to perform. Scripted as a real, disclosed failing assertion
    against the case's literal expected result, not silently substituted.
  - **The SAME auto-upload-and-send behavior fires even when the recording
    is force-stopped mid-capture** (confirmed by ending the mocked
    MediaStream's track — `track.stop()` + a dispatched `ended` event —
    while `is-recording` was active): the app still finalizes whatever
    partial audio it had and auto-sends it as a `.qc-msg-voice` bubble; no
    crash, no console error beyond the site's own pre-existing unrelated
    noise (confirmed by diffing console output WITH vs WITHOUT ever
    touching the mic — 4 identical unrelated messages, `404`/
    `requestStorageAccess`/two null-property warnings, present in BOTH
    runs). This is a real, observed PASS for **ADO-137594's** core "stops
    gracefully without error" claim, but the SAME real disclosed mismatch
    as ADO-137590 applies to its own "partial transcription remains
    editable" sub-clause — no editable-transcript state exists to remain
    in, live.
  - **Denying/never-granting mic permission does NOT disable or hide the
    mic icon.** Confirmed live: with no permission ever granted, clicking
    `.qc-mic` still calls the real `getUserMedia`, which Chromium
    auto-rejects (no permission decision made); the button's class/
    aria-label/aria-pressed are IDENTICAL before and after — still
    `qc-mic` / "Record a voice message" / not `disabled`. This is a real,
    disclosed mismatch against **ADO-137592's** stated expected result
    ("the microphone icon becomes disabled/hidden") — the mic remains
    exactly as clickable as before, ready for a future permission attempt.
    The case's OTHER claim — "typing remains available, text-only
    unaffected" — DOES hold live (confirmed: input never disabled by a
    denied mic attempt, a normal typed send still worked immediately
    after).
  - **Playwright's automation model cannot observe the browser's own
    native permission-prompt UI at all** — Chromium via CDP (which
    Playwright drives) auto-resolves `getUserMedia` permission decisions
    deterministically from `context.grant_permissions()` and never renders
    an interceptable native prompt to assert against, in headless or
    headed mode. This is a genuine TOOLING limitation, not a product gap —
    material to **ADO-137589**. The real, verifiable structural proxy this
    file's `spy_on_microphone_requests()`/`microphone_request_count()`
    below use instead: confirm the real (unmocked, unstubbed —
    `spy_on_microphone_requests()` only WRAPS the call to count it, per
    this file's established "spy vs. stub" distinction) `getUserMedia` is
    invoked exactly once per click, and that no `is-recording` state is
    ever reached before that promise settles — the closest honest
    approximation of "a decision is required before recording starts"
    without asserting on UI Playwright cannot see. Disclosed plainly in
    that test's own docstring, not silently skipped or force-passed.
  - **Cross-engine reality genuinely differs from both ADO-137581's and
    ADO-137582's premises** — checked by launching Playwright's `webkit`
    and `firefox` engines directly (this file's first use of a non-
    chromium engine; done via a test-module-local fixture reusing
    conftest.py's existing session-scoped `playwright_instance` fixture,
    not by editing conftest.py/browser.py's shared chromium `browser`
    fixture) against the same live page:
    - **WebKit (Playwright's standard proxy for testing Safari, per
      Playwright's own documentation — no real macOS Safari host was
      available this session):** `navigator.mediaDevices.getUserMedia` is
      literally `undefined` in this engine build, and the mic icon
      GENUINELY does not render (`is_mic_icon_visible()` → False) — a
      real, confirmed PASS for ADO-137581's exact premise: STT auto-
      disables, no error, and a normal typed query still works and gets a
      real reply.
    - **Firefox:** `navigator.mediaDevices.getUserMedia` EXISTS and the mic
      icon DOES render (`is_mic_icon_visible()` → True) — this directly
      CONTRADICTS ADO-137582's premise that STT "automatically degrades to
      text-only" on Firefox. Live reality: Firefox is NOT degraded: the
      mic icon is fully present. A real, disclosed mismatch, scripted per
      the case's literal expected result (mic icon absent/disabled)
      regardless of the real observed presence.
    - Also note: `context.grant_permissions(["microphone"])` itself raises
      `Unknown permission: microphone` on WebKit — a second, independent
      confirmation that Playwright's WebKit build has no microphone
      permission model to grant in the first place, consistent with
      `getUserMedia` being entirely absent there.
  - **No CMS/admin path this session to control an STT enable/disable
    toggle** — same category of precondition gap as PBI 131022's
    ADO-137539 and PBI 131023's ADO-137558/137559 (documented fixture
    requirements, not invented or silently forced to pass). Material to
    **ADO-137587** (mic hidden when admin disables STT) and **ADO-137595**
    (mic disappears on next interaction after a mid-session admin
    disable) — both `skip`ped with a concrete reason, per the case text's
    own explicit allowance ("if no way to control this via UI/available
    config, document as untestable without backend/admin access").

  **Case-by-case dispositions this batch's findings drive** (13 cases
  detailed here — this batch's own routing brief framed the backlog as
  "14 of 22", but only 13 Automation-tagged case numbers were actually
  supplied with content; no 14th case's text was ever provided, so only
  these 13 were authored — see the test module's own top-of-section note):
    - ADO-137574, 137575, 137576, 137577 — no live mismatch; scripted and
      PASS on real live behavior (mic renders correctly across LTR/RTL/
      desktop/tablet/mobile, and a real granted-permission recording cycle
      shows the real `is-recording` indicator without clipping).
    - ADO-137581 — PASSES on WebKit (real, confirmed degrade-to-text-only).
    - ADO-137582 — scripted as a genuine, disclosed FAILING assertion on
      Firefox (mic is NOT absent/disabled, contradicting the case).
    - ADO-137587, 137595 — SKIPPED, no admin/CMS path this session (case
      text's own explicit allowance).
    - ADO-137588 — PASSES using `mock_audio_transcription_response()` (the
      real network-boundary substitution technique, generalizing this
      file's existing `block_chat_endpoint()` from "abort" to "fulfill
      with a controlled body" — the real STT engine's own recognition
      accuracy is out of Automation scope, same carve-out as
      `is_grounded_reply()`'s "response-quality is Manual" note); the
      case's own "check logged interaction (GCP-side)" step is flagged as
      a known, permitted gap (no GCP console access this session), not
      asserted — same pattern as ADO-137534/137536.
    - ADO-137589 — scripted with the real, verifiable structural proxy
      (`spy_on_microphone_requests()`), the native-prompt-UI portion
      explicitly flagged in-test as a Playwright/Chromium tooling
      limitation, not silently skipped or force-passed.
    - ADO-137590 — scripted as a genuine, disclosed FAILING assertion (no
      editable-transcript-in-input state exists live).
    - ADO-137592 — scripted as a genuine, disclosed FAILING assertion on
      the "disabled/hidden" sub-claim; the "typing remains available"
      sub-claim is a real, observed PASS within the same test.
    - ADO-137594 — PASSES on the real, observed graceful-stop/no-crash/
      text-still-works claims; the "partial transcription remains
      editable" sub-clause is flagged in-test as the same disclosed
      mismatch as ADO-137590 (no editable state exists to remain in).
"""

import json
import re

from core.web.base_page import BasePage
from config.settings import web_url
from web.pages.components.header_component import HeaderComponent
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

HOME_PATH = "/home"
ABOUT_US_PATH = "/web/qatar-chamber/about-us"
CONTACT_US_PATH = "/web/qatar-chamber/contact-us"
# Real, live news-article detail page (CLI-confirmed via a live anchor sweep
# off the Home page's own Latest News section) — the "unrelated public page"
# ADO-137550 asks to navigate to, in place of inventing a placeholder path.
NEWS_ARTICLE_PATH = "/web/qatar-chamber/news-article?id=48759"

# The live backend's real, confirmed grounded-answer citation markers (see
# module docstring's PBI-131022 CLI-probe log) — the only structural signal
# distinguishing a grounded/sourced reply from a fallback; NOT visual style.
_SOURCE_MARKER_RE = re.compile(r"(Source|المصدر)\s*:", re.IGNORECASE)

# The real message endpoint the composer POSTs to (captured live via a
# page.on("request", ...) listener across a real send) — used by
# block_chat_endpoint()/unblock_chat_endpoint() for ADO-137549's simulated
# connection-drop case. Same "block the real path" technique
# accessibility_tools_component.py already established for its own
# blocked-script simulation.
CHAT_ENDPOINT_PATTERN = "**/o/qc-chatbot/**"
# The real, observed error bubble text when that endpoint is unreachable
# (confirmed live — see module docstring).
CONNECTION_ERROR_TEXT = "Sorry, something went wrong reaching the assistant. Please try again."

# ── PBI 131024 (QC-BOT-004 "Speech-to-Text (Voice Input)") constants ────────
# The real, confirmed STT audio endpoint the composer POSTs the recorded
# clip to on "stop" (captured live via a page.on("request", ...) listener
# across a real record->stop cycle — same capture technique
# CHAT_ENDPOINT_PATTERN already used for the text endpoint, PBI 131022).
AUDIO_ENDPOINT_PATTERN = "**/o/qc-chatbot/v1.0/audio"

# Real, CLI-confirmed live aria-label/placeholder strings for the mic
# control's two states (see module docstring's PBI-131024 probe log).
MIC_IDLE_ARIA_LABEL = "Record a voice message"
MIC_RECORDING_ARIA_LABEL = "Stop recording and send"
RECORDING_INPUT_PLACEHOLDER = "Recording... tap to send"

# One-off init-script JS, added via page.add_init_script() BEFORE the first
# navigation, that fakes navigator.mediaDevices.getUserMedia() with a REAL
# (silent-tone) MediaStream via Web Audio's createMediaStreamDestination() —
# headless Chromium has no physical mic device, so a genuine
# getUserMedia({audio:true}) call would otherwise reject with NotFoundError
# regardless of the permission decision. This is the same class of disclosed
# browser-API substitution as this file's existing block_chat_endpoint()/
# start_dialog_watch() probes: a real browser-level API substitution, never
# an invented app behavior. Confirmed live (module docstring) that with this
# fake stream in place, the REAL app code still drives its own real
# MediaRecorder against it and POSTs the real captured bytes to
# AUDIO_ENDPOINT_PATTERN — only the hardware source is faked.
_FAKE_MIC_STREAM_INIT_SCRIPT = """
(function() {
    if (!navigator.mediaDevices) { return; }
    navigator.mediaDevices.getUserMedia = function(constraints) {
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        var dest = ctx.createMediaStreamDestination();
        var osc = ctx.createOscillator();
        osc.frequency.value = 220;
        var gain = ctx.createGain();
        gain.gain.value = 0.05;
        osc.connect(gain).connect(dest);
        osc.start();
        window.__sttMockStream = dest.stream;
        return Promise.resolve(dest.stream);
    };
})();
"""

# One-off init-script JS that WRAPS (never stubs/replaces the resolution
# of) the REAL navigator.mediaDevices.getUserMedia — used only where the
# case's own subject IS the browser's real permission-decision path itself
# (ADO-137589/137592), where _FAKE_MIC_STREAM_INIT_SCRIPT's always-resolve
# stub would hide the real (Chromium auto-)denial this file needs to
# observe. Counts real invocations without altering the real outcome.
_SPY_GET_USER_MEDIA_INIT_SCRIPT = """
(function() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { return; }
    window.__sttSpyCalls = 0;
    var orig = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    navigator.mediaDevices.getUserMedia = function(constraints) {
        window.__sttSpyCalls += 1;
        return orig(constraints);
    };
})();
"""


class ChatbotWidgetComponent(BasePage):
    # ── Collapsed / launcher state ───────────────────────────────────────
    CHATBOT_ROOT = "#qcChatbot"
    LAUNCHER = f"{CHATBOT_ROOT} >> button.qc-launcher"
    TOOLTIP = "#qcChatbotTooltip"

    # ── Expanded / chat-window state ─────────────────────────────────────
    PANEL = f"{CHATBOT_ROOT} >> .qc-panel"
    HEADER = f"{CHATBOT_ROOT} >> .qc-header"
    HEADER_LOGO = f"{CHATBOT_ROOT} >> .qc-header-logo"
    MINIMIZE_BUTTON = f"{CHATBOT_ROOT} >> button.qc-minimize"
    BODY = f"{CHATBOT_ROOT} >> .qc-body"
    MESSAGES = f"{CHATBOT_ROOT} >> .qc-msg"
    BOT_MESSAGES = f"{CHATBOT_ROOT} >> .qc-msg-bot"
    USER_MESSAGES = f"{CHATBOT_ROOT} >> .qc-msg-user"
    BOT_BUBBLES = f"{CHATBOT_ROOT} >> .qc-msg-bot .qc-bubble"
    USER_BUBBLES = f"{CHATBOT_ROOT} >> .qc-msg-user .qc-bubble"
    BOT_AVATARS = f"{CHATBOT_ROOT} >> .qc-msg-bot .qc-avatar"
    USER_AVATARS = f"{CHATBOT_ROOT} >> .qc-msg-user .qc-avatar"
    COMPOSER = f"{CHATBOT_ROOT} >> form.qc-composer"
    MIC_BUTTON = f"{CHATBOT_ROOT} >> button.qc-mic"
    INPUT = f"{CHATBOT_ROOT} >> input.qc-input"
    SEND_BUTTON = f"{CHATBOT_ROOT} >> button.qc-send"

    HTML_ROOT = "html"

    # ── PBI 131023 additions ─────────────────────────────────────────────
    # No `quick-reply`/`option`/`cta`/`flow-step` class exists live (see
    # module docstring's PBI-131023 class-name sweep) — this locator
    # targets ANY `<button>` rendered inside the message thread itself
    # (never the composer's own mic/send buttons, which live outside
    # `.qc-body`), used purely to CHECK for the presence/absence of a
    # guided-flow option, never to assert a specific invented class name.
    GUIDED_FLOW_OPTION_BUTTONS = f"{CHATBOT_ROOT} >> .qc-body button"
    BOT_BUBBLE_LINKS = f"{CHATBOT_ROOT} >> .qc-msg-bot .qc-bubble a.qc-link"
    # Non-avatar images inside a bot bubble — for ADO-137554's inline-image
    # requirement (real finding: none ever render — see module docstring).
    BOT_BUBBLE_IMAGES = f"{CHATBOT_ROOT} >> .qc-msg-bot .qc-bubble img"
    BOT_BUBBLE_LISTS = f"{CHATBOT_ROOT} >> .qc-msg-bot .qc-bubble ul"

    # ── PBI 131024 additions (real, live: see module docstring's probe
    # log) — the voice-message wrapper `.qc-msg-voice` is a DISTINCT
    # variant of `.qc-msg-user`, not the plain typed-message markup.
    VOICE_MESSAGES = f"{CHATBOT_ROOT} >> .qc-msg-voice"
    VOICE_PLAYER = f"{CHATBOT_ROOT} >> .qc-msg-voice .qc-voice-player"
    VOICE_TRANSCRIPT = f"{CHATBOT_ROOT} >> .qc-msg-voice .qc-voice-transcript"
    # Real, live element observed ONLY on the audio endpoint's own
    # empty-transcript fallback response (its distinct `buttons` field —
    # see module docstring) — NOT part of the text `/message` endpoint
    # PBI 131023 exhaustively swept (that finding stands unchanged; this is
    # a separate, audio-endpoint-only mechanism this batch newly uncovered).
    QUICK_REPLY_CHIPS = f"{CHATBOT_ROOT} >> .qc-quick-replies .qc-chip"

    def __init__(self, page):
        super().__init__(page)
        # Reused for the language-switch case (ADO-137457) — see module
        # docstring's "composes HeaderComponent" note.
        self.header = HeaderComponent(page)
        # Reused for the Light/Dark theme cases (ADO-137530/137531, PBI
        # 131022) — same composition pattern, avoids re-declaring
        # DARK_MODE_SWITCH/HIGH_CONTRAST_SWITCH already owned by
        # AccessibilityToolsComponent (PBI 129364).
        self.a11y = AccessibilityToolsComponent(page)
        self._dialog_count = 0

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "ChatbotWidgetComponent":
        self.open(web_url(HOME_PATH))
        self.wait_for(self.LAUNCHER)
        return self

    def open_home_arabic(self) -> "ChatbotWidgetComponent":
        self.open(web_url(HOME_PATH, locale="ar"))
        self.wait_for(self.LAUNCHER)
        return self

    def open_about_us(self) -> "ChatbotWidgetComponent":
        self.open(web_url(ABOUT_US_PATH))
        self.wait_for(self.LAUNCHER)
        return self

    def open_contact_us(self) -> "ChatbotWidgetComponent":
        self.open(web_url(CONTACT_US_PATH))
        self.wait_for(self.LAUNCHER)
        return self

    def open_news_article(self) -> "ChatbotWidgetComponent":
        """The real, live "unrelated public page" for ADO-137550 (see
        module docstring — NEWS_ARTICLE_PATH is a CLI-confirmed real news
        detail URL, not an invented placeholder)."""
        self.open(web_url(NEWS_ARTICLE_PATH))
        self.wait_for(self.LAUNCHER)
        return self

    def switch_to_arabic(self) -> "ChatbotWidgetComponent":
        """Reuses HeaderComponent's own switch (click + network-idle wait) —
        see module docstring. Re-waits on the launcher afterward since this
        component, not HeaderComponent, owns that locator."""
        self.header.switch_to_arabic()
        self.wait_for(self.LAUNCHER)
        return self

    def switch_to_english(self) -> "ChatbotWidgetComponent":
        """Symmetric counterpart to switch_to_arabic(), for the mid-
        conversation language-switch case (ADO-137548, PBI 131022) — reuses
        HeaderComponent.switch_to_english() (see switch_to_arabic()'s own
        composition note)."""
        self.header.switch_to_english()
        self.wait_for(self.LAUNCHER)
        return self

    # ── Launcher state / position ────────────────────────────────────────
    def is_launcher_visible(self) -> bool:
        return self.is_visible(self.LAUNCHER)

    def launcher_box(self) -> dict:
        box = self.page.locator(self.LAUNCHER).bounding_box()
        return dict(box) if box else {}

    def launcher_aria_label(self) -> str:
        return self.page.locator(self.LAUNCHER).get_attribute("aria-label")

    def is_launcher_idle(self) -> bool:
        """True when the launcher shows its idle "Open chat" affordance
        (collapsed state) — the same live state whether the panel was never
        opened, was minimized, or was closed (see module docstring: minimize
        and close are functionally identical live)."""
        return self.launcher_aria_label() == "Open chat"

    def is_launcher_bottom_right(self, max_edge_gap: int = 60) -> bool:
        """True if the launcher sits within `max_edge_gap` px of BOTH the
        viewport's right and bottom edges. Real measured insets were 24px
        (desktop/tablet) and 12px (mobile) — the cases state no exact pixel
        value, only "bottom-right corner", so this checks a bounded gap
        rather than one hardcoded figure (see module docstring)."""
        box = self.launcher_box()
        viewport = self.page.viewport_size
        if not box or not viewport:
            return False
        right_gap = viewport["width"] - (box["x"] + box["width"])
        bottom_gap = viewport["height"] - (box["y"] + box["height"])
        return 0 <= right_gap <= max_edge_gap and 0 <= bottom_gap <= max_edge_gap

    def is_launcher_fully_within_viewport(self) -> bool:
        """No clipping / no overlap proxy: the launcher's own box is fully
        inside the current viewport bounds. The only floating widget
        observed live is the chatbot itself (no other floating widget to
        collide with at initial page load, before any scrolling) — the
        narrowest reasonable reading of "no overlap with other floating
        widgets" / "does not overlap page footer/navigation" without
        inventing a generic cross-widget overlap detector the cases never
        specify a second widget for."""
        box = self.launcher_box()
        viewport = self.page.viewport_size
        if not box or not viewport:
            return False
        return (
            box["x"] >= 0 and box["y"] >= 0
            and box["x"] + box["width"] <= viewport["width"]
            and box["y"] + box["height"] <= viewport["height"]
        )

    def launcher_render_fingerprint(self) -> dict:
        """Composite render snapshot for the "identical across pages" check
        (ADO-137454) — rounded size + computed shape/color, independent of
        the page it's read on."""
        box = self.launcher_box()
        style = self.page.locator(self.LAUNCHER).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {borderRadius: cs.borderRadius, backgroundColor: cs.backgroundColor}; }"
        )
        return {
            "width": round(box["width"]) if box else None,
            "height": round(box["height"]) if box else None,
            **style,
        }

    def is_tooltip_visible(self) -> bool:
        return self.is_visible(self.TOOLTIP)

    def tooltip_text(self) -> str:
        return self.page.locator(self.TOOLTIP).inner_text().strip()

    def is_mic_icon_visible(self) -> bool:
        return self.is_visible(self.MIC_BUTTON)

    # ── Open / minimize / close ──────────────────────────────────────────
    def open_chat(self) -> "ChatbotWidgetComponent":
        self.click(self.LAUNCHER)
        self.wait_for(self.INPUT)
        return self

    def close_chat(self) -> "ChatbotWidgetComponent":
        """Clicks the SAME launcher button (see module docstring: no
        separate floating close control exists live)."""
        self.click(self.LAUNCHER)
        self.wait_for(self.PANEL, state="hidden")
        return self

    def minimize_chat(self) -> "ChatbotWidgetComponent":
        self.click(self.MINIMIZE_BUTTON)
        self.wait_for(self.PANEL, state="hidden")
        return self

    def is_chat_open(self) -> bool:
        classes = self.page.locator(self.CHATBOT_ROOT).get_attribute("class") or ""
        return "is-open" in classes.split()

    def is_panel_visible(self) -> bool:
        return self.is_visible(self.PANEL)

    def panel_box(self) -> dict:
        box = self.page.locator(self.PANEL).bounding_box()
        return dict(box) if box else {}

    def is_panel_fully_within_viewport(self) -> bool:
        box = self.panel_box()
        viewport = self.page.viewport_size
        if not box or not viewport:
            return False
        return (
            box["x"] >= 0 and box["y"] >= 0
            and box["x"] + box["width"] <= viewport["width"]
            and box["y"] + box["height"] <= viewport["height"]
        )

    def is_header_visible(self) -> bool:
        return self.is_visible(self.HEADER)

    def is_header_logo_visible(self) -> bool:
        return self.is_visible(self.HEADER_LOGO)

    def is_minimize_button_visible(self) -> bool:
        return self.is_visible(self.MINIMIZE_BUTTON)

    def header_background_image(self) -> str:
        return self.page.locator(self.HEADER).evaluate("el => getComputedStyle(el).backgroundImage")

    # ── Message thread ───────────────────────────────────────────────────
    def message_count(self) -> int:
        return self.page.locator(self.MESSAGES).count()

    def bot_message_count(self) -> int:
        return self.page.locator(self.BOT_MESSAGES).count()

    def user_message_count(self) -> int:
        return self.page.locator(self.USER_MESSAGES).count()

    def first_bot_message_text(self) -> str:
        return self.page.locator(self.BOT_BUBBLES).first.inner_text().strip()

    def last_bot_message_text(self) -> str:
        return self.page.locator(self.BOT_BUBBLES).last.inner_text().strip()

    def last_user_message_text(self) -> str:
        return self.page.locator(self.USER_BUBBLES).last.inner_text().strip()

    def message_thread_snapshot(self) -> list:
        """[(role, text), ...] in on-screen order — used to compare the
        thread before/after minimize or close, per ADO-137464/137465."""
        items = self.page.locator(self.MESSAGES)
        out = []
        for i in range(items.count()):
            m = items.nth(i)
            classes = m.get_attribute("class") or ""
            role = "user" if "qc-msg-user" in classes else "bot"
            out.append((role, m.inner_text().strip()))
        return out

    def has_bot_avatar(self) -> bool:
        return self.page.locator(self.BOT_AVATARS).count() > 0

    def has_user_avatar(self) -> bool:
        return self.page.locator(self.USER_AVATARS).count() > 0

    def last_user_bubble_style(self) -> dict:
        loc = self.page.locator(self.USER_BUBBLES).last
        return loc.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {backgroundColor: cs.backgroundColor, color: cs.color, fontWeight: cs.fontWeight}; }"
        )

    def last_bot_bubble_style(self) -> dict:
        loc = self.page.locator(self.BOT_BUBBLES).last
        return loc.evaluate("el => getComputedStyle(el).backgroundColor")

    def is_last_user_bubble_right_of_bot_bubble(self) -> bool:
        """True if the last user bubble sits further right (closer to the
        panel's right edge) than the last bot bubble — the concrete,
        pixel-based stand-in for "right-aligned maroon" vs "left-aligned
        gray" (ADO-137463's described layout)."""
        bot_box = self.page.locator(self.BOT_BUBBLES).last.bounding_box()
        user_box = self.page.locator(self.USER_BUBBLES).last.bounding_box()
        if not bot_box or not user_box:
            return False
        return user_box["x"] > bot_box["x"]

    # ── Composer (input / send / mic) ────────────────────────────────────
    def input_placeholder(self) -> str:
        return self.page.locator(self.INPUT).get_attribute("placeholder")

    def input_value(self) -> str:
        return self.page.locator(self.INPUT).input_value()

    def is_input_focused(self) -> bool:
        return self.is_focused(self.INPUT)

    def fill_message(self, text: str) -> "ChatbotWidgetComponent":
        self.type(self.INPUT, text)
        return self

    def click_send(self) -> "ChatbotWidgetComponent":
        self.click(self.SEND_BUTTON)
        return self

    def send_message(self, text: str) -> "ChatbotWidgetComponent":
        self.fill_message(text)
        self.click_send()
        return self

    def input_box(self) -> dict:
        box = self.page.locator(self.INPUT).bounding_box()
        return dict(box) if box else {}

    def send_button_box(self) -> dict:
        box = self.page.locator(self.SEND_BUTTON).bounding_box()
        return dict(box) if box else {}

    def is_send_button_right_of_input(self) -> bool:
        s, i = self.send_button_box(), self.input_box()
        return bool(s and i) and s["x"] > i["x"]

    def is_send_button_left_of_input(self) -> bool:
        s, i = self.send_button_box(), self.input_box()
        return bool(s and i) and s["x"] < i["x"]

    def message_count_increased_within(self, before_count: int, timeout_ms: int = 3000) -> bool:
        """Bounded explicit wait (Playwright's own `wait_for_function`, NOT
        `time.sleep()`) used only to confirm a NEGATIVE outcome — "no new
        message landed within this window" — for the empty-send /
        whitespace-only-send cases (ADO-137470/137471). Returns False (never
        raises) on timeout, since "nothing happened" is the expected
        PASSING state for those two cases."""
        try:
            self.page.wait_for_function(
                "count => document.querySelectorAll('#qcChatbot .qc-msg').length > count",
                arg=before_count,
                timeout=timeout_ms,
            )
            return True
        except Exception:  # noqa: BLE001 — timeout means "no new message", the expected path
            return False

    def wait_for_bot_reply_count(self, min_count: int, timeout: int = 20000) -> None:
        """Explicit, no-sleep wait for the live backend's async bot reply to
        land in the DOM — polls the real bot-message count via Playwright's
        own `wait_for_function` (same mechanism footer_component.py's
        wait_for_scroll_top() already uses in this codebase), never
        time.sleep()."""
        self.page.wait_for_function(
            "count => document.querySelectorAll('#qcChatbot .qc-msg-bot').length >= count",
            arg=min_count,
            timeout=timeout,
        )

    # ── Page-level / misc ─────────────────────────────────────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    # ══ PBI 131022 (QC-BOT-002 "Controlled & Grounded Responses") ══════════
    # See module docstring's CLI-probe log for every real, live finding these
    # methods encode.

    # ── Grounded vs. fallback detection (ADO-137522/137523/137534-137539) ──
    @staticmethod
    def is_grounded_reply(text: str) -> bool:
        """True if `text` carries the live backend's real citation marker
        ("Source:" EN / "المصدر:" AR) — the ONLY confirmed, verifiable signal
        that a reply is grounded/sourced from the approved dataset (see
        module docstring: no distinct visual banner/style exists)."""
        return bool(text) and bool(_SOURCE_MARKER_RE.search(text))

    def last_bot_message_style(self) -> dict:
        """{backgroundColor, color} of the last bot bubble — used to confirm
        a grounded reply and a fallback reply render IDENTICALLY (the real,
        disclosed ADO-137523 mismatch), not merely to check one bubble's own
        legibility."""
        loc = self.page.locator(self.BOT_BUBBLES).last
        return loc.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {backgroundColor: cs.backgroundColor, color: cs.color}; }"
        )

    # ── Special-character / injection-safety (ADO-137543) ──────────────────
    def start_dialog_watch(self) -> "ChatbotWidgetComponent":
        """Registers a `dialog` (window.alert/confirm/prompt) listener —
        used to confirm an injected `<script>alert(1)</script>` payload never
        actually executes. Auto-dismisses any dialog that DOES fire so a
        real XSS hit cannot hang the test/browser."""
        self._dialog_count = 0

        def _on_dialog(dialog):
            self._dialog_count += 1
            dialog.dismiss()

        self.page.on("dialog", _on_dialog)
        return self

    def dialog_count(self) -> int:
        return self._dialog_count

    def last_user_message_outer_html(self) -> str:
        """Raw markup of the last user bubble — confirms a `<script>` payload
        is present as ESCAPED markup (`&lt;script&gt;...`), not live DOM,
        alongside last_user_message_text()'s browser-decoded plain-text
        check (see module docstring)."""
        return self.page.locator(self.USER_BUBBLES).last.evaluate("el => el.outerHTML")

    # ── Clear-before-send (ADO-137544) ──────────────────────────────────────
    def clear_input(self) -> "ChatbotWidgetComponent":
        self.fill_message("")
        return self

    # ── Connection-drop simulation (ADO-137549) ─────────────────────────────
    def block_chat_endpoint(self) -> "ChatbotWidgetComponent":
        """Aborts the widget's REAL message endpoint (CHAT_ENDPOINT_PATTERN —
        confirmed live via a request listener, see module docstring), the
        same "block the real path" technique this file's PBI-131021 sibling
        AccessibilityToolsComponent.start_open_failure_simulation() already
        established. Register BEFORE send_message()."""
        self.page.route(CHAT_ENDPOINT_PATTERN, lambda route: route.abort())
        return self

    def unblock_chat_endpoint(self) -> "ChatbotWidgetComponent":
        self.page.unroute(CHAT_ENDPOINT_PATTERN)
        return self

    def wait_for_connection_error_or_reply(self, min_bot_count: int, timeout: int = 15000) -> None:
        """Bounded, no-sleep wait for EITHER a new bot bubble (normal reply)
        or the real observed connection-error bubble to land — whichever the
        live app produces. Never raises past the timeout; the caller reads
        last_bot_message_text() afterward to see which one arrived."""
        try:
            self.page.wait_for_function(
                "count => document.querySelectorAll('#qcChatbot .qc-msg-bot').length >= count",
                arg=min_bot_count,
                timeout=timeout,
            )
        except Exception:  # noqa: BLE001 — timeout is itself a real, reportable outcome (a hang)
            pass

    def is_connection_error_shown(self) -> bool:
        return CONNECTION_ERROR_TEXT in (self.last_bot_message_text() or "")

    # ── Theme: Light (default) / Dark (ADO-137530/137531) ──────────────────
    def switch_to_dark_theme(self) -> "ChatbotWidgetComponent":
        """Opens the accessibility panel (composed AccessibilityToolsComponent
        — see __init__'s composition note) and activates Dark mode, WITHOUT
        touching the chat panel's own open/close state."""
        self.a11y.click_accessibility_button()
        self.a11y.switch_to_dark_mode()
        self.a11y.close_panel()
        return self

    def is_dark_theme_active(self) -> str:
        return self.a11y.dark_mode_toggle_state()

    # ── Contrast: Normal (default) / High (ADO-137532) ──────────────────────
    def switch_to_high_contrast(self) -> "ChatbotWidgetComponent":
        self.a11y.click_accessibility_button()
        self.a11y.activate_high_contrast()
        self.a11y.close_panel()
        return self

    def is_high_contrast_active(self) -> bool:
        return self.a11y.is_high_contrast_active()

    # ══ PBI 131023 (QC-BOT-003 "Guided Conversational Flows & Hybrid Q&A") ═
    # See module docstring's headline finding: no guided-flow/quick-reply
    # mechanism exists live. These methods detect/verify what actually does
    # (or does not) render, never invent an interaction that isn't there.

    def wait_for_bot_reply_text(self, min_count: int, timeout: int = 20000) -> None:
        """Fixes the real streaming-response race this batch discovered
        (see module docstring): waits for BOTH the bot-message count to
        reach `min_count` AND the last bot bubble's text to be non-empty —
        `wait_for_bot_reply_count()` alone can return while the bubble is
        still mid-stream/empty. No time.sleep(); one bounded
        `wait_for_function` poll, mirroring every other explicit wait in
        this file."""
        self.page.wait_for_function(
            "count => { const msgs = document.querySelectorAll('#qcChatbot .qc-msg-bot'); "
            "if (msgs.length < count) return false; "
            "const bubble = msgs[msgs.length - 1].querySelector('.qc-bubble'); "
            "return !!bubble && bubble.innerText.trim().length > 0; }",
            arg=min_count,
            timeout=timeout,
        )

    def has_guided_flow_options(self) -> bool:
        """True if ANY button rendered inside the message thread (a
        quick-reply/guided-flow option, by any name) — real, live finding
        (see module docstring): this is always False, confirmed across a
        15-query sweep and the raw API schema. Kept as a real, generic
        detector (not a hardcoded 'always False') so a future real flow
        would be honestly detected, not permanently hidden by an assumed
        constant."""
        return self.page.locator(self.GUIDED_FLOW_OPTION_BUTTONS).count() > 0

    def attempt_start_guided_flow(self, trigger_query: str) -> bool:
        """Sends `trigger_query` (a real, live phrase meant to plausibly
        trigger a guided flow) and reports whether any guided-flow option
        appeared afterward. The single shared Arrange/Act step for every
        case in this batch whose premise is "a guided flow starts" — real,
        live finding is this always returns False (see module docstring)."""
        bot_count_before = self.bot_message_count()
        self.send_message(trigger_query)
        self.wait_for_bot_reply_text(bot_count_before + 1)
        return self.has_guided_flow_options()

    def bot_bubble_link_count(self) -> int:
        return self.page.locator(self.BOT_BUBBLE_LINKS).count()

    def has_bot_bubble_image(self) -> bool:
        return self.page.locator(self.BOT_BUBBLE_IMAGES).count() > 0

    def has_bot_bubble_list(self) -> bool:
        return self.page.locator(self.BOT_BUBBLE_LISTS).count() > 0

    def click_last_bot_bubble_link(self):
        """Clicks the real, live embedded hyperlink inside the last bot
        bubble (`target="_blank"` — see module docstring) and returns the
        new tab's Page object for the caller to read `.url` from. Used by
        ADO-137570 in place of a non-existent "flow step link"."""
        with self.page.context.expect_page() as new_page_info:
            self.click(self.BOT_BUBBLE_LINKS)
        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        return new_page

    # ══ PBI 131024 (QC-BOT-004 "Speech-to-Text (Voice Input)") ═════════════
    # See module docstring's PBI-131024 CLI-probe log for the full live
    # findings. Headline: STT is REAL and functioning live — a real
    # button.qc-mic drives a real MediaRecorder against a real
    # getUserMedia({audio:true}) stream and POSTs the captured clip to
    # AUDIO_ENDPOINT_PATTERN. The app never constructs the browser's own Web
    # Speech API (SpeechRecognition) — transcription is server-side.

    def grant_microphone_permission(self) -> "ChatbotWidgetComponent":
        """Playwright's per-context permission grant — the deterministic
        stand-in for a user accepting the browser's native mic-permission
        prompt. Playwright auto-resolves that native UI from this grant and
        never renders it to script against (see
        spy_on_microphone_requests()'s docstring and the module docstring's
        disclosed tooling-limitation note for ADO-137589)."""
        self.page.context.grant_permissions(["microphone"])
        return self

    def mock_microphone_capture(self) -> "ChatbotWidgetComponent":
        """MUST be called BEFORE the first navigation (open_home() /
        open_home_arabic()) — registers _FAKE_MIC_STREAM_INIT_SCRIPT so the
        real app code receives a real (silent-tone) MediaStream instead of
        rejecting on missing physical mic hardware in this headless run."""
        self.page.add_init_script(_FAKE_MIC_STREAM_INIT_SCRIPT)
        return self

    def spy_on_microphone_requests(self) -> "ChatbotWidgetComponent":
        """MUST be called BEFORE the first navigation. WRAPS (never fakes
        the resolution of) the REAL navigator.mediaDevices.getUserMedia so
        a test can count real invocations without altering Chromium's own
        permission-decision behavior — used where the case's subject IS the
        permission-decision path itself (ADO-137589/137592), where
        mock_microphone_capture()'s always-resolve stub would hide the real
        (Chromium auto-)denial this file needs to observe."""
        self.page.add_init_script(_SPY_GET_USER_MEDIA_INIT_SCRIPT)
        return self

    def microphone_request_count(self) -> int:
        return self.page.evaluate("() => window.__sttSpyCalls || 0")

    def mock_audio_transcription_response(
        self, transcript: str, reply: str, buttons: list = None
    ) -> "ChatbotWidgetComponent":
        """Fulfills the real AUDIO_ENDPOINT_PATTERN with a controlled JSON
        body mirroring the live backend's own confirmed schema
        ({transcript, reply, sessionId, languageCode, buttons} — see module
        docstring) — lets a test assert the CLIENT's rendering/handling of
        a given transcript deterministically. The real server-side STT
        engine's own recognition accuracy is a third-party ML behavior out
        of this project's Automation scope — the same "response-quality is
        Manual, not Automation" carve-out this file's is_grounded_reply()
        docstring already applies to reply content."""
        body = json.dumps({
            "transcript": transcript,
            "reply": reply,
            "sessionId": "stt-mock-session",
            "languageCode": "en",
            "buttons": buttons or [],
        })
        self.page.route(
            AUDIO_ENDPOINT_PATTERN,
            lambda route: route.fulfill(status=200, content_type="application/json", body=body),
        )
        return self

    def unmock_audio_transcription_response(self) -> "ChatbotWidgetComponent":
        self.page.unroute(AUDIO_ENDPOINT_PATTERN)
        return self

    def click_microphone(self) -> "ChatbotWidgetComponent":
        self.click(self.MIC_BUTTON)
        return self

    def start_recording(self) -> "ChatbotWidgetComponent":
        """Clicks the mic and waits for the real, observed recording-state
        DOM change (is-recording class + aria-pressed=true — see module
        docstring)."""
        self.click(self.MIC_BUTTON)
        self.wait_for_recording_state(True)
        return self

    def stop_recording(self) -> "ChatbotWidgetComponent":
        """Clicks the SAME mic button again — its real, live aria-label
        flips to "Stop recording and send" while recording (see module
        docstring); there is no separate stop control."""
        self.click(self.MIC_BUTTON)
        return self

    def wait_for_recording_state(self, active: bool, timeout: int = 5000) -> None:
        self.page.wait_for_function(
            "active => { const b = document.querySelector('#qcChatbot button.qc-mic'); "
            "return !!b && b.classList.contains('is-recording') === active; }",
            arg=active,
            timeout=timeout,
        )

    def is_mic_recording_active(self) -> bool:
        classes = self.page.locator(self.MIC_BUTTON).get_attribute("class") or ""
        return "is-recording" in classes.split()

    def mic_aria_label(self) -> str:
        return self.page.locator(self.MIC_BUTTON).get_attribute("aria-label")

    def is_mic_button_disabled(self) -> bool:
        return self.page.locator(self.MIC_BUTTON).get_attribute("disabled") is not None

    def is_input_disabled(self) -> bool:
        return self.page.locator(self.INPUT).get_attribute("disabled") is not None

    def simulate_microphone_track_ended(self) -> None:
        """Fires a real 'ended' event on the active mocked MediaStream's
        track(s), simulating an OS/browser-level mid-recording permission
        revocation — the case's own explicitly-permitted fallback
        (ADO-137594) when the permission APIs themselves aren't
        independently revocable mid-test. Requires mock_microphone_capture()
        + a prior start_recording() in this same test."""
        self.page.evaluate(
            "() => { if (window.__sttMockStream) { "
            "window.__sttMockStream.getTracks().forEach(t => { t.stop(); "
            "t.dispatchEvent(new Event('ended')); }); } }"
        )

    def wait_for_voice_message(self, min_count: int, timeout: int = 20000) -> None:
        self.page.wait_for_function(
            "count => document.querySelectorAll('#qcChatbot .qc-msg-voice').length >= count",
            arg=min_count,
            timeout=timeout,
        )

    def voice_message_count(self) -> int:
        return self.page.locator(self.VOICE_MESSAGES).count()

    def has_voice_player(self) -> bool:
        return self.page.locator(self.VOICE_PLAYER).count() > 0

    def last_voice_transcript_text(self) -> str:
        return self.page.locator(self.VOICE_TRANSCRIPT).last.inner_text().strip()

    def quick_reply_chip_labels(self) -> list:
        """Real, live element rendered ONLY on the audio endpoint's own
        empty-transcript fallback response (see module docstring) — kept as
        a real, generic reader (not hardcoded) so this batch's own
        incidental discovery stays honestly reportable."""
        locs = self.page.locator(self.QUICK_REPLY_CHIPS)
        return [locs.nth(i).inner_text().strip() for i in range(locs.count())]
