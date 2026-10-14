"""
cms/pages/certificate_of_origin/fragment_form_mixin.py — form-mechanics overrides
for Engineer B's Object Authoring Page Objects (PBIs 130947, 130949).

Healed 2026-10-01 (user-approved one-shot heal) from run-1 evidence:

1. Rich text. The shared `description_editor_iframe(ref)` looks for
   `div[id*="ObjectField_<ref>"] iframe`, but on the COO / Proposal forms the
   EN editor sits in `#fragment-<uuid>-rich-text-input`, next to
   `textarea[name="ObjectField_<ref>"]` (id `fragment-<uuid>-ObjectField_<ref>`),
   and the AR editor sits next to `textarea#qc-ar-<ref>` with no id'd
   container (read live 2026-10-01). Every fill timed out at 30 s. The iframe
   is now resolved from those anchors in the DOM and tagged with
   `data-qcb-rich="<ref>-<locale>"`, and the selector targets that tag.
2. "Status" picklist. `get_by_role("combobox", name="Status")` also matched
   the entries list's own status filter (`select[data-qc-oel-status-filter]`),
   a strict-mode violation. Combobox lookups are scoped to non-<select>
   elements (the form's picklist is an <input role=combobox>).

3. Save detection, refusal and record identity (review fixes, 2026-10-03).
   A Save as Draft / Submit on these forms runs `POST /c/portal/edit_info_item`
   (302 back to the manage page), then the page's own JS sends
   `PUT /o/c/<plural>/<id>` with the full record. An invalid Submit sends
   neither: the refusal bar is hidden by site CSS, so the network is the
   oracle. Every save is watched; the record ID is taken from the write whose
   body carries this record's title, and status / open / history / delete
   then resolve BY ID instead of by a (possibly long) title.
   `/validate` POSTs fire continuously while fields are edited (640 in one
   trace), so they are counted but are not, on their own, a save.
4. Role sessions are cached per worker (cookies of a real login, swapped in
   with clear_cookies()/add_cookies()), instead of logout + login per call.

Nothing here is shared: the shared ObjectAuthoringPage / DisposableObjectAdminPage
are not edited.
"""

import json
import time

from cms.pages.components.disposable_object_admin import ADMIN_HOME_EN_URL_PATH, DISPOSABLE_PREFIX
from cms.pages.components.object_authoring_page import normalize_status
from cms.pages.control_panel import login_page as _lp
from config.settings import cms_role_credentials, control_panel_url, settings

_WRITE_METHODS = ("POST", "PUT", "PATCH")
# fields the browser / Liferay flags invalid after a Save / Submit click
_INVALID_FIELDS_JS = """() => Array.from(document.querySelectorAll(
  'form [aria-invalid="true"], form input:invalid, form textarea:invalid, form select:invalid'
)).map(e => e.name || e.id || e.getAttribute('aria-label') || e.tagName).slice(0, 10)"""


class NeedsInvestigation(Exception):
    """Not an AssertionError on purpose: check_required_by_case re-labels
    AssertionErrors as PRODUCT_BUG, and an unproven refusal is neither a
    pass nor a product verdict. pytest reports it as broken."""
# per-worker role-session cache: email -> cookies of a real login
_ROLE_COOKIES: dict[str, list] = {}
_LEFTOVER_LOG = "reports/phase3-b6-teardown-leftovers.txt"


def _log(line: str) -> None:
    print(f"[coo/pfr] {line}")


def log_leftover(line: str) -> None:
    _log(line)
    try:
        with open(_LEFTOVER_LOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def _path(url: str) -> str:
    return url.split("?", 1)[0].rstrip("/")


def _write_target(url: str):
    """(plural, id|None) for an `/o/c/` write URL, else None."""
    p = _path(url)
    if "/o/c/" not in p or p.endswith("/validate"):
        return None
    rest = p.split("/o/c/", 1)[1].split("/")
    plural = rest[0]
    if len(rest) == 2 and rest[1].isdigit():
        return plural, rest[1]
    return plural, None


_API_JS = """async ([m, u, b]) => {
  const t = (window.Liferay && Liferay.authToken) || '';
  const r = await fetch(u, {method: m, credentials: 'same-origin',
    headers: {'accept': 'application/json', 'content-type': 'application/json', 'x-csrf-token': t},
    body: b});
  let txt = '';
  try { txt = await r.text(); } catch (e) {}
  return [r.status, txt];
}"""

_TAG_JS = r"""([ref, loc, tag]) => {
  // HEALED 2026-10-03 (tc_141057: the EN body received the AR text). The
  // nearest-editor walk from the EN anchor could land on the AR editor, so
  // each side now excludes the other side's editor before picking.
  const enAnchor = document.querySelector('textarea[name="ObjectField_' + ref + '"]');
  const arAnchor = document.getElementById('qc-ar-' + ref);
  const suffix = '-ObjectField_' + ref;
  const enContainer = () => {
    if (!enAnchor || !enAnchor.id || !enAnchor.id.endsWith(suffix)) return null;
    const c = document.getElementById(enAnchor.id.slice(0, -suffix.length) + '-rich-text-input');
    return c ? c.querySelector('iframe[title="editor"]') : null;
  };
  const walk = (anchor, exclude) => {
    let el = anchor;
    while (el && el.parentElement) {
      el = el.parentElement;
      const all = [...el.querySelectorAll('iframe[title="editor"]')].filter(f => f !== exclude);
      if (all.length) {
        // nearest editor that follows the anchor; else the last one before it
        const after = all.filter(f => anchor.compareDocumentPosition(f) & Node.DOCUMENT_POSITION_FOLLOWING);
        return after.length ? after[0] : all[all.length - 1];
      }
    }
    return null;
  };
  let fr = null;
  if (loc === 'ar') {
    if (!arAnchor) return 'no-anchor';
    const en = enContainer() || (enAnchor ? walk(enAnchor, null) : null);
    fr = walk(arAnchor, en);
  } else {
    if (!enAnchor) return 'no-anchor';
    fr = enContainer();
    if (!fr) {
      const ar = arAnchor ? walk(arAnchor, null) : null;
      fr = walk(enAnchor, ar);
    }
  }
  if (!fr) return 'no-iframe';
  document.querySelectorAll('[data-qcb-rich="' + tag + '"]').forEach(x => x.removeAttribute('data-qcb-rich'));
  fr.setAttribute('data-qcb-rich', tag);
  return 'ok';
}"""


class FragmentFormMixin:
    RICH_WAIT_MS = 35000

    # ---- rich text ------------------------------------------------------
    def _rich_iframe(self, key: str, locale: str) -> str:
        ref = self.spec(key).ref
        tag = f"{ref}-{'ar' if locale == 'ar' else 'en'}"
        self.page.locator('iframe[title="editor"]').first.wait_for(state="attached", timeout=self.RICH_WAIT_MS)
        self.last_rich_tag_result = self.page.evaluate(_TAG_JS, [ref, "ar" if locale == "ar" else "en", tag])
        return f'iframe[data-qcb-rich="{tag}"]'

    # ---- scoped combobox ------------------------------------------------
    def _combo(self, key: str):
        return self.page.get_by_role("combobox", name=self.label_pattern(self.spec(key).label)).and_(
            self.page.locator(":not(select)")
        )

    def select_option(self, key: str, option_label: str):
        combobox = self._combo(key)
        listbox_id = combobox.get_attribute("aria-controls")
        option = self.page.locator(f'#{listbox_id} [role="option"]:text-is("{option_label}")')
        # HEALED 2026-10-03: select_options()' Escape does not close this
        # listbox, so an unconditional click here toggled it shut (trace for
        # tc_141007). Open it only when the option isn't already showing.
        if not option.is_visible():
            self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
        option.wait_for(state="visible", timeout=5000)
        option.click()
        return self

    def select_options(self, key: str) -> list[str]:
        combobox = self._combo(key)
        listbox_id = combobox.get_attribute("aria-controls")
        self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
        opts = self.page.locator(f'#{listbox_id} [role="option"]')
        opts.first.wait_for(state="visible", timeout=5000)
        texts = [t.strip() for t in opts.all_inner_texts()]
        self.page.keyboard.press("Escape")
        return texts

    def upload(self, key: str, fixture_path: str, tag: str = ""):
        copy = self.disposable_copy(fixture_path, tag)
        self.__dict__.setdefault("_qcb_uploads", {})[key] = copy.replace("\\", "/").rsplit("/", 1)[-1]
        self.upload_file(self.spec(key).label, copy)
        return self

    def _stored_file_name(self, key: str) -> str:
        """File name stored on the open record (by ID) for `key`'s upload."""
        uploaded = self.__dict__.get("_qcb_uploads", {}).get(key)
        title = self._ident().get("pending")
        data = self.entry_json(title) if (uploaded and title) else None
        if not data:
            return ""
        stem = uploaded.rsplit(".", 1)[0]
        for v in data.values():
            if isinstance(v, dict) and stem in json.dumps(v):
                href = ((v.get("link") or {}).get("href") or "")
                return v.get("name") or href.split("?", 1)[0].rsplit("/", 2)[-2] or stem
        return ""

    def _date_input(self, key: str):
        """b9 (2026-10-04, tc_141360/141361): the audit-date inputs carry no
        textbox role, so the shared label lookup hung 30 s. They are read by
        their live `name="ObjectField_<ref>"`."""
        return self.page.locator(f'input[name="ObjectField_{self.spec(key).ref}"]').first

    def field_editable(self, key: str) -> bool:
        if self.spec(key).kind == "date" and self.spec(key).ref:
            el = self._date_input(key)
            return el.is_editable() and not el.evaluate("e => e.readOnly || e.disabled")
        return self.page.get_by_role("textbox", name=self.label_pattern(self.spec(key).label)).first.is_editable()

    def value(self, key: str, locale: str = "en") -> str:
        if self.spec(key).kind == "date" and self.spec(key).ref:
            return self._date_input(key).input_value(timeout=10000)
        if self.spec(key).kind == "select":
            return self._combo(key).input_value()
        if self.spec(key).kind == "file":
            # Live 2026-10-03 (tc_141071): the stored record carries the file
            # (entry JSON), but the reopened form's readout can stay empty.
            # Short readout poll, then read the file by record ID: the link
            # of a file object in the entry JSON that holds the uploaded name.
            name = ""
            for _ in range(6):
                name = super().value(key, locale)
                if name:
                    return name
                self.page.wait_for_timeout(500)
            return self._stored_file_name(key)
        return super().value(key, locale)

    # ---- raw list status ---------------------------------------------
    def row_status_raw(self, title: str) -> str:
        """The Status cell's raw text (upper-cased), for rows whose badge
        carries more than the workflow state."""
        self.filter_entries(title)
        row = self._row_locator(title)
        if row.count() == 0:
            return ""
        return " ".join(row.locator("td").nth(1).inner_text().split()).upper()

    # =================================================================
    # Record identity (review fix 2026-10-03): title -> (plural, id)
    # =================================================================
    SAVE_FIRE_WINDOW_S = 10.0  # an invalid Submit sends nothing at all
    SAVE_FIRE_VALIDATE_CAP_S = 40.0  # a /validate still in flight may delay the save
    SAVE_FOLLOW_PUT_S = 25.0  # edit_info_item -> the page's own PUT /o/c/<plural>/<id>
    ROW_MATCH_CHARS = 40  # rows / search are matched on the unique title prefix

    def _ident(self) -> dict:
        d = self.__dict__.get("_qcb_ident")
        if d is None:
            d = self.__dict__["_qcb_ident"] = {
                "ids": {}, "absent": set(), "pending": None, "editing": None, "last": None,
            }
        return d

    def id_for(self, title: str | None) -> str | None:
        rec = self._ident()["ids"].get(title) if title else None
        return rec[1] if rec else None

    def plural_for(self, title: str | None) -> str | None:
        rec = self._ident()["ids"].get(title) if title else None
        return rec[0] if rec else None

    @property
    def last_save(self) -> dict | None:
        return self._ident()["last"]

    def _needle(self, title: str) -> str:
        return title[: self.ROW_MATCH_CHARS]

    def fill_required(self, title, skip=(), active=False, files=None):
        ident = self._ident()
        ident["pending"] = title
        ident["absent"].discard(title)
        return super().fill_required(title, skip=skip, active=active, files=files)

    def fill(self, key, value, locale="en"):
        # a whitespace/empty title probe (tc_141222) keeps the QCTEST title as
        # the record's identity, so the refusal list check searches for it
        if key == self.TITLE_FIELD and locale != "ar" and self._ident()["editing"] is None and str(value).strip():
            self._ident()["pending"] = value
        return super().fill(key, value, locale)

    # ---- in-page API (the same calls the manage page itself makes) -----
    def _on_liferay_page(self) -> bool:
        try:
            return bool(self.page.evaluate("() => !!(window.Liferay && Liferay.authToken)"))
        except Exception:  # noqa: BLE001
            return False

    def _api(self, method: str, path: str, body: str | None = None) -> tuple[int, str]:
        url = control_panel_url(path)
        status, text = -1, ""
        for attempt in (0, 1):
            if attempt or not self._on_liferay_page():
                self.open(self._manage_url(locale="en"))
            try:
                status, text = self.page.evaluate(_API_JS, [method, url, body])
            except Exception as exc:  # noqa: BLE001
                status, text = -1, str(exc)[:200]
            if status not in (-1, 401, 403):
                return status, text
        return status, text

    # Liferay workflow status (entry JSON `status.label`) -> editorial state
    # Live 2026-10-03: an Editor Publish with Active unticked stores Liferay
    # status "incomplete"; the CMS UI shows it as Draft (user-checked by hand).
    _WF_STATUS = {"approved": "Published", "draft": "Draft", "incomplete": "Draft",
                  "pending": "Pending Review", "denied": "Rejected", "scheduled": "Scheduled",
                  "expired": "Unpublished"}

    def status_by_id(self, entry_id: str, plural: str | None = None) -> str:
        """Editorial state of one record by ID, from
        `/o/qc-object-status/transitions/<id>` (the call the list itself
        makes): statusLabelEn, normalized.

        Live 2026-10-03: for a record whose Active Status is unticked that
        endpoint answers statusKey "inactive" (the list badge INACTIVE) and
        hides the workflow state. The state is then read from the record
        itself, `GET /o/c/<plural>/<id>` -> status.label. Returns the raw
        label when it is not one of the seven states, "" when unreadable."""
        status, text = self._api("GET", f"/o/qc-object-status/transitions/{entry_id}")
        if status != 200:
            return ""
        try:
            data = json.loads(text)
        except ValueError:
            return ""
        label = data.get("statusLabelEn") or data.get("statusLabel") or ""
        self.last_status_raw = f"transitions={label!r}"
        if (data.get("statusKey") or "").casefold() != "inactive" or not plural:
            st = normalize_status(label)
            return st if st != "Unknown" else (label or st)
        status, text = self._api("GET", f"/o/c/{plural}/{entry_id}")
        try:
            wf = (json.loads(text).get("status") or {}).get("label", "") if status == 200 else ""
        except ValueError:
            wf = ""
        self.last_status_raw = f"transitions={label!r}, Liferay status={wf!r}"
        return self._WF_STATUS.get(wf.casefold(), f"Inactive/{wf or '?'}")

    def entry_json(self, title: str) -> dict | None:
        plural, eid = self.plural_for(title), self.id_for(title)
        if not (plural and eid):
            return None
        status, text = self._api("GET", f"/o/c/{plural}/{eid}")
        if status != 200:
            return None
        try:
            return json.loads(text)
        except ValueError:
            return None

    # ---- save watch ---------------------------------------------------
    def _watched_click(self, selector: str) -> dict:
        ident = self._ident()
        title = ident["pending"]
        editing = ident["editing"]
        log = {"title": title, "validate": 0, "validate_open": 0, "edit_info": [], "writes": [],
               "started": False, "id": None, "plural": None, "editing": bool(editing)}

        def on_req(req):
            try:
                u, m = req.url, req.method
                if "/c/portal/edit_info_item" in u:
                    log["started"] = True
                elif "/o/c/" in u and m in _WRITE_METHODS:
                    if _path(u).endswith("/validate"):
                        log["validate"] += 1
                        log["validate_open"] += 1
                    else:
                        log["started"] = True
            except Exception:  # noqa: BLE001
                pass

        def on_resp(resp):
            try:
                req = resp.request
                u, m = resp.url, req.method
                if "/c/portal/edit_info_item" in u:
                    log["edit_info"].append(resp.status)
                elif "/o/c/" in u and m in _WRITE_METHODS:
                    if _path(u).endswith("/validate"):
                        log["validate_open"] = max(0, log["validate_open"] - 1)
                        return
                    tgt = _write_target(u)
                    if tgt:
                        log["writes"].append({"method": m, "plural": tgt[0], "id": tgt[1],
                                              "status": resp.status, "body": req.post_data or "",
                                              "resp": resp})
            except Exception:  # noqa: BLE001
                pass

        def match():
            for w in log["writes"]:
                if not (200 <= w["status"] < 300):
                    continue
                wid = w["id"]
                if wid is None and w["method"] == "POST" and w.get("resp") is not None:
                    try:
                        wid = str(w["resp"].json().get("id") or "") or None
                    except Exception:  # noqa: BLE001
                        wid = None
                    if wid:
                        w["id"] = wid
                if not wid:
                    continue
                if (editing and wid == editing[1]) or (title and title in w["body"]):
                    return w["plural"], wid
            return None

        # Review fix 2026-10-04: a refusal must carry a POSITIVE signal, so the
        # button's at-rest state is read before the click, and the click is
        # proven to land on the button. The site-wide chatbot launcher can
        # intercept pointer events (the same reason _run_row_action forces its
        # click); a forced click would then hit the launcher, so on an
        # intercepted click the button is clicked through the DOM instead.
        button = self.page.locator(selector).first
        button.wait_for(state="visible", timeout=15000)
        try:
            button.scroll_into_view_if_needed(timeout=5000)
        except Exception:  # noqa: BLE001
            pass
        log["disabled_at_rest"] = bool(button.is_disabled())
        log["refusal_before"] = self._refusal_text()
        log["click_via"] = None
        self.page.on("request", on_req)
        self.page.on("response", on_resp)
        t0 = time.monotonic()
        try:
            if not log["disabled_at_rest"]:
                try:
                    button.click(timeout=5000)
                    log["click_via"] = "pointer"
                except Exception:  # noqa: BLE001 - intercepted (chatbot) or detached
                    button.evaluate("b => b.click()")
                    log["click_via"] = "dom"
            deadline = t0 + self.SAVE_FIRE_WINDOW_S
            while time.monotonic() < deadline and not log["started"]:
                if log["validate_open"] > 0:
                    deadline = min(max(deadline, time.monotonic() + 3), t0 + self.SAVE_FIRE_VALIDATE_CAP_S)
                self.page.wait_for_timeout(250)
            if log["started"]:
                hard = t0 + self.SETTLE_OUTCOME_TIMEOUT_MS / 1000
                info_at = None
                while time.monotonic() < hard:
                    if match():
                        break
                    if log["edit_info"] and info_at is None:
                        info_at = time.monotonic()
                    if info_at and time.monotonic() - info_at > self.SAVE_FOLLOW_PUT_S:
                        break
                    if log["writes"] and not log["edit_info"] and all(w["status"] >= 400 for w in log["writes"]):
                        break
                    self.page.wait_for_timeout(300)
                self.page.wait_for_timeout(1000)
        finally:
            self.page.remove_listener("request", on_req)
            self.page.remove_listener("response", on_resp)
        # Refusal TEXT (a signal): only real error elements, and only text that
        # was not already there before the click. b8 run 1 showed the wider
        # selector (.lfr-alert-container / [data-qc-oel-validation]) matching
        # every field wrapper ("Item Title (Read Only) ..."), which would make
        # any no-save outcome look refused. The wide text is kept as a
        # diagnostic only.
        refusal_now = self._refusal_text()
        log["hidden_refusal"] = refusal_now if refusal_now and refusal_now != log.get("refusal_before") else ""
        try:
            log["diag_text"] = " | ".join(
                " ".join(t.split()) for t in self.page.locator(
                    ".alert-danger, .lfr-alert-container, .form-feedback-item, [data-qc-oel-validation]"
                ).all_text_contents() if t.strip()
            )[:300]
        except Exception:  # noqa: BLE001
            log["diag_text"] = ""
        try:
            log["invalid_fields"] = self.page.evaluate(_INVALID_FIELDS_JS)
        except Exception:  # noqa: BLE001 - page navigated away (a save that went out)
            log["invalid_fields"] = []
        found = match()
        if found:
            log["plural"], log["id"] = found
        elif log["started"] and title and not editing:
            # the save went out but no write carried the title: one list lookup
            log["id"] = self._id_from_list(title)
            log["plural"] = next((w["plural"] for w in log["writes"]), None) or self.plural_for(title)
        elif log["started"] and editing and any(200 <= s < 400 for s in log["edit_info"]):
            log["plural"], log["id"] = editing
        log["elapsed_s"] = round(time.monotonic() - t0, 1)
        for w in log["writes"]:
            w.pop("resp", None)
            w["body"] = len(w["body"])
        if title and log["id"]:
            ident["ids"][title] = (log["plural"] or self.plural_for(title), log["id"])
            ident["absent"].discard(title)
        ident["last"] = log
        _log(
            f"{selector.split(':')[0][:12]} {self.SLUG} title={str(title)[:50]!r} started={log['started']} "
            f"{self.save_counts(log)} id={log['id']} in {log['elapsed_s']}s"
            + (f" hidden_refusal={log.get('hidden_refusal')!r}" if log.get("hidden_refusal") else "")
            + f" disabled_at_rest={log['disabled_at_rest']} click_via={log['click_via']}"
            + (f" invalid_fields={log['invalid_fields']}" if log.get("invalid_fields") else "")
        )
        return log

    REFUSAL_TEXT_SEL = (
        ".alert-danger, .form-feedback-item, "
        '[data-qc-oel-editbar]:has-text("not saved"), :text("Please complete the required fields")'
    )

    def _refusal_text(self) -> str:
        try:
            return " | ".join(
                " ".join(t.split()) for t in self.page.locator(self.REFUSAL_TEXT_SEL).all_text_contents()
                if t.strip() and "(Read Only)" not in t
            )[:400]
        except Exception:  # noqa: BLE001 - page navigating
            return ""

    def save_as_draft(self):
        self._watched_click(self.SAVE_AS_DRAFT_BUTTON)
        return self

    def submit_for_review(self):
        self._watched_click(self.SUBMIT_FOR_REVIEW_BUTTON)
        return self

    def save_counts(self, log: dict | None = None) -> str:
        ls = log or self.last_save or {}
        return (f"validate={ls.get('validate')} edit_info_item={ls.get('edit_info')} "
                f"writes={[(w['method'], w['id'], w['status']) for w in ls.get('writes', [])]}")

    @staticmethod
    def _refusal_signals(ls: dict) -> list[str]:
        """POSITIVE refusal evidence captured by _watched_click (review fix
        2026-10-04). Absence of a save request alone is not a refusal."""
        signals = []
        if ls.get("disabled_at_rest"):
            signals.append("submit button disabled at rest")
        # Only while nothing was sent: after a save the page resets to a blank
        # create form whose required inputs are :invalid at rest (b8 trace,
        # tc_140981), which is not a refusal.
        if ls.get("invalid_fields") and not ls.get("started"):
            signals.append(f"invalid field(s) {ls['invalid_fields']}")
        if ls.get("hidden_refusal"):
            signals.append(f"refusal text {ls['hidden_refusal'][:160]!r}")
        rejected = [w["status"] for w in ls.get("writes", []) if 400 <= w["status"] < 500]
        if rejected and not any(200 <= w["status"] < 300 for w in ls.get("writes", [])):
            signals.append(f"/o/c/ write rejected HTTP {rejected}")
        return signals

    def refusal_visible(self) -> bool:
        """Refusal oracle (Liferay's refusal bar is hidden by site CSS).

        Review fix 2026-10-04: a refusal is True only with a POSITIVE signal
        (submit disabled at rest, an aria-invalid / :invalid field, non-empty
        refusal text, or a rejected /o/c/ write) and no stored record. An
        `edit_info_item` answer of HTTP >= 400 is an error, not a refusal.
        Nothing sent and no positive signal raises NeedsInvestigation: the
        click may never have reached the form."""
        ls = self.last_save
        if ls is None:
            return super().refusal_visible()
        title = ls.get("title")
        info = ls.get("edit_info") or []
        if any(s >= 400 for s in info) and not any(200 <= s < 400 for s in info):
            raise NeedsInvestigation(
                f"NEEDS_INVESTIGATION: the save errored (edit_info_item HTTP {info}) - an error is "
                f"not a refusal. {self.save_counts(ls)}"
            )
        if ls["id"] and ls["started"]:
            return False
        if not ls["started"] and title and not ls.get("editing") and not ls.get("list_checked"):
            ls["list_checked"] = True
            found = self._id_from_list(title)
            if found:
                self._ident()["ids"][title] = (self.plural_for(title), found)
                ls["id"] = found
                return False
            self._ident()["absent"].add(title)
        signals = self._refusal_signals(ls)
        if not signals:
            raise NeedsInvestigation(
                f"NEEDS_INVESTIGATION: no positive refusal signal for {self.SLUG} "
                f"title={str(title)[:50]!r} (started={ls['started']}, click_via={ls.get('click_via')}, "
                f"editing={bool(ls.get('editing'))}): no save was stored, but the submit button was not "
                f"disabled, no field was invalid and no refusal text rendered. {self.save_counts(ls)}"
            )
        ls["refusal_signals"] = signals
        _log(f"refused {self.SLUG} title={str(title)[:50]!r}: {'; '.join(signals)} | {self.save_counts(ls)}")
        return True

    # ---- list helpers -------------------------------------------------
    def _id_from_list(self, title: str) -> str | None:
        """One bounded search of the entries list by the title prefix: the
        id of the single matching row, else None."""
        try:
            self.open(self._manage_url(locale="en"))
            self.page.locator(self.ENTRIES_TABLE_ROW).first.wait_for(state="attached", timeout=35000)
            needle = self._needle(title)
            box = self.page.locator(self.ENTRIES_SEARCH_INPUT)
            if box.count():
                box.fill(needle)
                box.press("Enter")
            rows = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{needle}")')
            try:
                rows.first.wait_for(state="visible", timeout=8000)
            except Exception:  # noqa: BLE001
                return None
            if rows.count() != 1:
                return None
            hist = rows.first.locator("[data-qc-oel-history]")
            return hist.first.get_attribute("data-qc-oel-history") if hist.count() else None
        except Exception:  # noqa: BLE001
            return None

    def _row_locator(self, title_or_code: str):
        eid = self.id_for(title_or_code)
        if eid:
            return self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has([data-qc-oel-history="{eid}"])').first
        return self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{self._needle(title_or_code)}")').first

    def filter_entries(self, text: str):
        """Search the list by the title prefix and wait for the row (by id
        when known); one re-search for a lagging index, no longer loop."""
        box = self.page.locator(self.ENTRIES_SEARCH_INPUT)
        if box.count() == 0:
            return self
        row = self._row_locator(text)
        for _ in range(2):
            box.fill(self._needle(text))
            box.press("Enter")
            try:
                row.wait_for(state="visible", timeout=8000)
                return self
            except Exception:  # noqa: BLE001
                continue
        return self

    def row_status_text(self, title: str) -> str:
        self.filter_entries(title)
        row = self._row_locator(title)
        if row.count() == 0:
            return ""
        return normalize_status(row.locator("td").nth(1).inner_text())

    def row_visible(self, title: str) -> bool:
        self.filter_entries(title)
        return self._row_locator(title).count() > 0

    def row_offers_action(self, title: str, action: str) -> bool:
        self.filter_entries(title)
        return self._row_locator(title).locator(f"[{self.ROW_ACTION_ATTRS[action]}]").count() > 0

    def status_of(self, title: str, role: str) -> str:
        eid = self.id_for(title)
        if eid:
            self._switch_role(role)
            st = self.status_by_id(eid, self.plural_for(title))
            # Batch 2026-10-04 (tc_141135, creator Test Editor): an Editor
            # submit passes through Pending Review for a few seconds before
            # the workflow auto-publishes it. Re-read for up to 12s; a
            # Pending Review that holds longer is reported as it is.
            if st == "Pending Review" and role == _EDITOR_ROLE:
                for _ in range(6):
                    self.page.wait_for_timeout(2000)
                    st = self.status_by_id(eid, self.plural_for(title)) or st
                    if st != "Pending Review":
                        break
            if st:
                return st
        if title in self._ident()["absent"]:
            return ""
        return super().status_of(title, role)

    def entry_exists(self, title: str, role: str) -> bool:
        if title in self._ident()["absent"] and not self.id_for(title):
            return False
        return super().entry_exists(title, role)

    def open_entry_by_edit_link(self, title: str):
        rec = self._ident()["ids"].get(title)
        editor = _lp._SESSION_OWNER.get(self.page) == cms_role_credentials(_EDITOR_ROLE)[0]
        # Direct ?editEntry=<erc> only for the Editor. Smoke 2026-10-03: the
        # Author's own draft opened that way rendered "(Read Only)" and its
        # Submit sent nothing (b5, via the row's Edit link, passed).
        data = self.entry_json(title) if rec and editor else None
        erc = (data or {}).get("externalReferenceCode")
        if erc:
            try:
                self.open_entry_by_code(erc, locale="en")
            except Exception as exc:  # noqa: BLE001 - see _open_manage (tc_141274)
                if "ERR_ABORTED" not in str(exc):
                    raise
                self.page.wait_for_timeout(2000)
                self.open_entry_by_code(erc, locale="en")
        else:
            super().open_entry_by_edit_link(title)
        self._ident()["pending"] = title
        self._ident()["editing"] = rec
        return self

    def open_new_entry_form(self, locale=None):
        self._ident()["editing"] = None
        return super().open_new_entry_form(locale=locale)

    def open_entries_list(self, locale=None):
        self._ident()["editing"] = None
        return super().open_entries_list(locale=locale)

    def history_entries(self, title_or_code: str) -> list[dict]:
        """History of the record whose row is located BY ID (when known).
        Clicks the row's History control directly: the shared row-action path
        waits up to 30s for the control to detach, which History never does."""
        self.filter_entries(title_or_code)
        ctl = self._row_locator(title_or_code).locator(f"[{self.ROW_ACTION_ATTRS['history']}]").first
        if ctl.count() == 0:
            return []
        ctl.click(force=True)
        history_list = self.page.locator(self.HISTORY_LIST).first
        try:
            history_list.wait_for(state="visible", timeout=10000)
            # Batch 2026-10-04 (tc_140998): the list renders before its entries
            # are filled; wait for a populated "who" before reading.
            history_list.locator(f"{self.HISTORY_WHO}:not(:empty)").first.wait_for(state="attached", timeout=10000)
        except Exception:  # noqa: BLE001 — reported as empty / as read, never raised
            if history_list.count() == 0:
                return []
        entries = []
        # direct children only: each entry nests a ul.qc-oel__history-changes
        # whose own <li>s (one per changed field) carry no who/when (tc_140998)
        items = history_list.locator(":scope > li")
        for i in range(items.count()):
            item = items.nth(i)

            def _part(selector: str) -> str:
                node = item.locator(selector)
                return node.first.inner_text().strip() if node.count() else ""

            entries.append({"action": _part(".qc-oel__history-action"), "who": _part(self.HISTORY_WHO),
                            "when": _part(self.HISTORY_WHEN), "comment": _part(self.HISTORY_COMMENT)})
        # Live 2026-10-04: the list is NEWEST FIRST (e.g. the auto-publish
        # entry above "Edited" above "Submitted for review", same minute).
        # Returned oldest-first ("newest last"), as the shared method promises.
        entries.reverse()
        return entries

    # ---- delete by ID -------------------------------------------------
    def delete_disposable(self, title: str, role: str | None = None) -> bool:
        """Delete our own QCTEST record BY ID: the row is located by its
        `data-qc-oel-delete="<id>"`, after checking the stored record carries
        our title. A refused trash call (e.g. HTTP 400) is logged and left,
        with no retry. Falls back to the exact-title delete when no ID is
        known. Never raises on a teardown error."""
        role = role or _EDITOR_ROLE
        if not title or not title.startswith(DISPOSABLE_PREFIX):
            raise ValueError(f"refusing to delete non-disposable record {title!r}")
        eid = self.id_for(title)
        if not eid:
            if title in self._ident()["absent"]:
                return True  # nothing was ever created
            return super().delete_disposable(title, role)
        try:
            self._switch_role(role)
            data = self.entry_json(title)
            if data is not None and self._needle(title)[:30] not in json.dumps(data, ensure_ascii=False):
                log_leftover(f"NOT DELETED {self.SLUG} id={eid}: stored record does not carry {title[:50]!r}")
                return False
            self.open_list(role)
            self.filter_entries(title)
            link = self.page.locator(f'a[data-qc-oel-delete="{eid}"]')
            if link.count() == 0:
                log_leftover(f"NOT DELETED {self.SLUG} id={eid} {title[:50]!r}: no Delete control for this id")
                return False
            with self.page.expect_response(
                lambda r: f"/o/qc-object-status/trash/{eid}" in r.url, timeout=30000
            ) as rinfo:
                self.page.once("dialog", lambda d: d.accept())
                link.first.click(force=True)
            resp = rinfo.value
            if resp.status >= 400:
                try:
                    body = resp.text()[:200]
                except Exception:  # noqa: BLE001
                    body = ""
                log_leftover(f"trash refused {self.SLUG} id={eid} {title[:50]!r}: HTTP {resp.status} {body!r}")
                return False
            self._ident()["ids"].pop(title, None)
            self._ident()["absent"].add(title)
            return True
        except Exception as exc:  # noqa: BLE001 - teardown never masks the result
            log_leftover(f"delete error {self.SLUG} id={eid} {title[:50]!r}: {str(exc)[:160]}")
            return False

    # =================================================================
    # Role sessions cached per worker (review fix 2026-10-03)
    # =================================================================
    def _fresh_login(self, email: str, password: str) -> None:
        ctx = self.page.context
        ctx.clear_cookies()
        _lp.CmsLoginPage(self.page).open_login().login(email, password)
        _ROLE_COOKIES[email] = ctx.cookies()
        self.__dict__["_qcb_fresh"] = email
        _lp._SESSION_OWNER[self.page] = email

    def _switch_role(self, role: str) -> None:
        """Cookie swap from this worker's cached login of `role`; a real
        login only the first time. Never hits /c/portal/logout, which would
        end the cached session server-side for every later test."""
        email, password = cms_role_credentials(role)
        if _lp._SESSION_OWNER.get(self.page, settings.test_user) == email:
            return
        self.__dict__.pop("_qcb_verified", None)
        cached = _ROLE_COOKIES.get(email)
        if cached:
            ctx = self.page.context
            ctx.clear_cookies()
            ctx.add_cookies(cached)
            _lp._SESSION_OWNER[self.page] = email
        else:
            self._fresh_login(email, password)

    def _session_email(self) -> str:
        try:
            status, text = self.page.evaluate(
                _API_JS, ["GET", control_panel_url("/o/headless-admin-user/v1.0/my-user-account"), None]
            )
            return (json.loads(text).get("emailAddress") or "").casefold() if status == 200 else ""
        except Exception:  # noqa: BLE001
            return ""

    def _signed_in_or_relogin(self, role: str, url: str) -> None:
        """Signed in AND as the role's own account (identity read from
        my-user-account, review 2026-10-04); else a real re-login."""
        email, password = cms_role_credentials(role)
        if _lp.CmsLoginPage(self.page).login_succeeded():
            if self.__dict__.get("_qcb_verified") == email:
                return
            who = self._session_email()
            if who == email.casefold() or (not who and self.__dict__.get("_qcb_fresh") == email):
                self.__dict__["_qcb_verified"] = email
                return
            _log(f"identity mismatch: expected {role}, session is {who or 'unreadable'!r}; re-login")
        _ROLE_COOKIES.pop(email, None)
        self._fresh_login(email, password)
        self.open(url)
        who = self._session_email()
        # an account without headless-admin-user access reads "" - accepted
        # only straight after its own fresh login
        assert who in ("", email.casefold()), f"after a fresh login the session is {who!r}, not the {role} account"
        self.__dict__["_qcb_verified"] = email

    def sign_in(self, role: str):
        """Same contract as before (the session belongs to `role` and lands
        on the admin home), without a logout + login per call."""
        self._switch_role(role)
        url = control_panel_url(ADMIN_HOME_EN_URL_PATH)
        self.open(url)
        self._signed_in_or_relogin(role, url)
        return self

    def _open_manage(self, role: str, locale, form: bool):
        """The manage URL directly (no admin-home landing first)."""
        self._switch_role(role)
        url = self._manage_url(locale=locale)
        try:
            self.open(url)
        except Exception as exc:  # noqa: BLE001
            # Batch 2026-10-04 (tc_141067): the previous save's own redirect
            # can abort this navigation (net::ERR_ABORTED). Once, then on.
            if "ERR_ABORTED" not in str(exc):
                raise
            self.page.wait_for_timeout(2000)
            self.open(url)
        self._signed_in_or_relogin(role, url)
        self._entry_code = None
        self._locale = locale
        self._ident()["editing"] = None
        if form:
            self.wait_for(self.SAVE_AS_DRAFT_BUTTON, timeout=35000)
        else:
            self.wait_for(self.ENTRIES_TABLE_ROW, first=True, timeout=35000)
        return self

    def open_form(self, role: str, locale="en"):
        return self._open_manage(role, locale, form=True)

    def open_list(self, role: str, locale="en"):
        return self._open_manage(role, locale, form=False)


_EDITOR_ROLE = "Site Content Editor"
