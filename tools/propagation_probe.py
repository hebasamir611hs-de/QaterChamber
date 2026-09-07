#!/usr/bin/env python3
"""
propagation_probe.py — measure publish→delivery propagation latency (Python
port; replaces the retired qa/cms-automation/tools/propagation-probe.js,
which was deleted with the old REST framework while cms-profile.md still
referenced it).

Fills the UNVERIFIED "Publish / Propagation Latency Budget" section of
.claude/context/active/cms-profile.md. Until that section holds REAL numbers
from this probe, no test may hardcode a propagation timeout — that is a
stop-and-report condition, not a "guess 30s" condition.

Works with the team's current UI-only policy: the PUBLISH step is manual.

    1. Stage the change in the Control Panel (do not publish yet).
    2. Start the probe — it takes a baseline sample of the delivery URL:
           python tools/propagation_probe.py \
               --url https://qcdev.ihorizons.com/some-page \
               --marker "QCTEST-PROBE-<unique>" \
               --timeout 300 --interval 2
    3. Publish in the Control Panel the moment the probe prints
       "BASELINE OK — publish now", and press Enter in the probe terminal.
    4. The probe polls until the marker appears (or --absent: disappears),
       then keeps sampling for --settle seconds to detect flapping (mixed
       cache nodes serving old+new alternately — a real CDN symptom that a
       single first-seen measurement would hide).

Output: human summary + JSON (--json <path>) with first_seen_s, publish→seen
delta, per-sample log, and flap count. Record typical AND worst-case into
cms-profile.md — the budget is the worst case, not the average.

Plain HTTP GET (urllib, no new dependency) is deliberate: the public site is
server-rendered, and the probe must see exactly what an anonymous visitor's
first request sees — no browser cache, no storageState, no cookies beyond
what the server sets. If a CDN varies on headers, extend --header.
"""
import argparse
import json
import sys
import time
import urllib.request


def fetch(url: str, headers: dict, timeout: float = 15.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "qc-propagation-probe/1.0", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — QA-controlled target URL
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish→delivery propagation latency probe")
    ap.add_argument("--url", required=True, help="public delivery URL to poll")
    ap.add_argument("--marker", required=True, help="unique string the published change adds (e.g. QCTEST-PROBE-...)")
    ap.add_argument("--absent", action="store_true", help="measure REMOVAL: wait for the marker to disappear")
    ap.add_argument("--timeout", type=float, default=300, help="max seconds to wait (default 300)")
    ap.add_argument("--interval", type=float, default=2, help="poll interval seconds (default 2)")
    ap.add_argument("--settle", type=float, default=30, help="post-detection flap-watch seconds (default 30)")
    ap.add_argument("--header", action="append", default=[], metavar="K:V", help="extra request header (repeatable)")
    ap.add_argument("--json", dest="json_out", default=None, help="write machine-readable result here")
    ap.add_argument("--no-wait", action="store_true", help="skip the baseline/Enter step (publish already done)")
    args = ap.parse_args()

    headers = {}
    for h in args.header:
        k, _, v = h.partition(":")
        headers[k.strip()] = v.strip()

    def state() -> bool:
        """True == target state reached (marker present, or absent with --absent)."""
        body = fetch(args.url, headers)
        present = args.marker in body
        return (not present) if args.absent else present

    samples = []

    if not args.no_wait:
        try:
            if state():
                sys.exit("Baseline already in target state — marker "
                         + ("absent" if args.absent else "present")
                         + " before publish. Use a unique marker per run.")
        except Exception as exc:  # noqa: BLE001
            sys.exit(f"Baseline fetch failed: {exc}")
        print("BASELINE OK — publish now in the Control Panel, then press Enter here...")
        input()

    t0 = time.monotonic()
    first_seen = None
    while time.monotonic() - t0 < args.timeout:
        elapsed = round(time.monotonic() - t0, 2)
        try:
            reached = state()
            samples.append({"t": elapsed, "reached": reached})
            print(f"  t={elapsed:7.2f}s  {'REACHED' if reached else 'stale'}")
            if reached and first_seen is None:
                first_seen = elapsed
                break
        except Exception as exc:  # noqa: BLE001 — transient fetch errors are data, keep polling
            samples.append({"t": elapsed, "error": str(exc)})
            print(f"  t={elapsed:7.2f}s  fetch error: {exc}")
        time.sleep(args.interval)

    flaps = 0
    if first_seen is not None and args.settle > 0:
        print(f"first seen at {first_seen}s — flap-watching for {args.settle}s...")
        t1 = time.monotonic()
        last = True
        while time.monotonic() - t1 < args.settle:
            try:
                now = state()
                if now != last:
                    flaps += 1
                    print(f"  FLAP: state changed to {'REACHED' if now else 'stale'}")
                last = now
                samples.append({"t": round(time.monotonic() - t0, 2), "reached": now, "settle": True})
            except Exception as exc:  # noqa: BLE001
                samples.append({"t": round(time.monotonic() - t0, 2), "error": str(exc), "settle": True})
            time.sleep(args.interval)

    result = {
        "url": args.url,
        "marker": args.marker,
        "mode": "absent" if args.absent else "present",
        "first_seen_s": first_seen,
        "timed_out": first_seen is None,
        "flaps_during_settle": flaps,
        "interval_s": args.interval,
        "samples": samples,
    }
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"JSON result -> {args.json_out}")

    if first_seen is None:
        print(f"TIMED OUT after {args.timeout}s — propagation exceeds the probe window "
              f"(raise --timeout) or the publish/marker is wrong.")
        return 1
    print(f"\nPropagation: {first_seen}s to first consistent read"
          + (f", {flaps} flap(s) during settle — CACHE-NODE INCONSISTENCY, budget must cover it" if flaps else ", stable"))
    print("Record typical AND worst-case into .claude/context/active/cms-profile.md "
          "(Publish / Propagation Latency Budget) — the budget is the worst case.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
