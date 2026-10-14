# Test-point write-back PREVIEW, plan 133534, 2026-10-08

**STATUS: NO PREVIEW WAS EXECUTED.** The first `publish_test_run_results` preview call (PBI 129368, suite 134448, no `user_confirmed`) was denied by the Claude Code auto-mode permission classifier (reason: External System Writes). Nothing was written to Azure, no confirmation_token exists, and no further preview or write was attempted (including `set_test_point_outcomes`). To proceed the user must allow `mcp__plugin_qa-engine_azure-devops__publish_test_run_results` and `mcp__plugin_qa-engine_azure-devops__set_test_point_outcomes` (permission rule), or run the previews from an interactive session.

Argument lists are saved and ready, identical for preview and confirm: `testresults_<PBI>_publish.json` (keys plan_id, suite_id, run_name, automated, results) and `testresults_<PBI>_set.json` (plan_id, suite_id, outcomes). Bucket reconciliation (every point in exactly one bucket, sums equal total_points): `testresults_buckets.json`. `get_test_points` was run for all 7 suites: **no multi-point cases**, every point is configuration "Windows 10", so entries are keyed by test_case_id.

## Tokens

| PBI | suite | publish entries | set entries | confirmation_token | dropped |
|---|---|---|---|---|---|
| 129368 | 134448 | 52 | 0 | not issued (preview denied) | unknown |
| 129372 | 134450 | 54 | 0 | not issued (preview denied) | unknown |
| 129381 | 134452 | 62 | 32 | not issued (preview denied) | unknown |
| 129382 | 134453 | 8 | 25 | not issued (preview denied) | unknown |
| 129384 | 134455 | 96 | 13 | not issued (preview denied) | unknown |
| 129389 | 134460 | 38 | 2 | not issued (preview denied) | unknown |
| 129390 | 134461 | 64 | 8 | not issued (preview denied) | unknown |

## Counts per PBI (Passed + Failed + Blocked + N/A + untouched = total points)

| PBI | Passed | Failed | Blocked | N/A | untouched | total |
|---|---|---|---|---|---|---|
| 129368 | 48 | 3 | 1 | 0 | 74 | 126 |
| 129372 | 48 | 6 | 0 | 0 | 3 | 57 |
| 129381 | 51 | 6 | 5 | 32 | 25 | 119 |
| 129382 | 3 | 5 | 25 | 0 | 53 | 86 |
| 129384 | 91 | 5 | 0 | 13 | 51 | 160 |
| 129389 | 35 | 3 | 0 | 2 | 13 | 53 |
| 129390 | 42 | 4 | 18 | 8 | 32 | 104 |

## Mapping applied (to be shown with the preview)
Passed = executed and passed in latest run. Failed = covered by a filed bug (ID in comment). Blocked = executed with AUTOMATION_BUG or ENVIRONMENT (no product verdict), plus 129382 G1 (25, not executed, asserted). N/A = user decisions (Weather 13, G3 8, rich-text limits, 129381 section-level). Untouched = not executed / not scripted / deferred P4 / NEEDS USER / inconclusive / simulated / pending-bug.

## Judgment calls the user should confirm

- **129384, 40 cases** the report UPDATE relabels "NOT EXECUTED (automation, fix applied)" (earlier runs broke on record lookup/ENV, no product assertion reached): left UNTOUCHED, not Blocked. If they should read Blocked, say so.
- **129381 section-level N/A is 30 IDs, not 29:** 135538, 135555, 135564-135590 (27), 135624. User said 29; I included all 30 (the review B3 list). Drop **135624** (or 135555) from `testresults_129381_set.json` if the 29 excludes it. 135623 (zero active cards, needs real records) is NOT in it.
- **129381 G-DRAFT failures** (135540, 135541, 135556, 135560, 135591, 135592, 135596, 135597, 135601, 135606, 135618, 135619, 135626, 135630 etc.) left UNTOUCHED: latest framing is product-side double-submit, INCONCLUSIVE, B2 pending. Blocked only for 135551, 135609, 135610, 135539, 135545 (upload-picker / locator / Safari autoplay).
- **Bug-covered but not executed, kept Failed in the publish call** with comment "not executed this run; Failed by coverage of Bug #X": 135699, 135700, 135702, 135703 (129382, #149373) and 136507 (129390, #149490). The run is `automated=True`; manual-exec cases (129372 135303/135313/135315/135328, 129390 136472/136506, 129384 135935) are noted in their comments but share that flag.
- **129382 Blocked (25) via `set_test_point_outcomes`** has no comment slot, so Azure will NOT hold this text: "Not executed: section hidden on qcdev because the pinned event URL 404s (Bug #149373). User asked for Passed; held at Blocked per set-test-results policy, awaiting user". Alternative is a non-automated publish run so the comment lands; user call. IDs: 135634-135644, 135646-135650, 135652, 135665, 135674-135679, 135717.
- **129372 135310** is Passed (CMS half passed; card visual half inconclusive because of a synthetic 1x1 fixture, not a product issue). It is already Passed in Azure.
- **129390 136543** (G4) Passed per user ruling although the run marked it FAILED. **129372 135272/135276** Passed per user ruling (PBI satisfied).
- **129389 four over-limit cases** (136112, 136114, 136121, 136131) Passed under Rule 5.2 (UI intact, submit not attempted).
- **#149493 routing:** 135516/17/18/20/21 to suite 134452; 136088 to 134460; 136472 to 134461 (a mis-route would show in `dropped`).

## Held back although the run passed or executed them (open question about behaviour vs TC)

- 129382: 135664 (PARTIAL, checks row actions only), 135672 (step 2 only), 135663 (INCONCLUSIVE).
- 129389: 136111, 136113, 136120, 136122, 136127, 136129 (form side passed, public-page render at max NEEDS USER).
- 129390: 136476, 136551 (passed in batch 1 but DEFERRED P4), 136481, 136482 (P4 deferred), 136473 (NEEDS USER, 44 px), 136496/136553 (ack email awaiting inbox check), 136497/136554/136499 (admin inbox unreadable), 136492 (not run).
- 129381: 135561 (executed as Author; TC says Editor, wording ruling), 135547 (swipe), 135523/135532 (progress indicator TC re-scope), 135519/135522/135526/135527 (geometry, old bugs #137268/#137276 pending), 135600/135604 (Rule 5 open), 135623.
- 129384: 135930/135938/135939 (row gap, pending), 135925/135953/135971 (inconclusive), 5 P4 deferred (135931, 135932, 135942, 135944, 135948).
- 129372: 135323, 135277, 135324 (SIMULATED).
- 129368: 135105, 135106, 135107, 135108, 135132 (dots; TCs need re-scoping to arrows on desktop / dots on mobile, not bugs), 135176/135131/135228 (NEEDS USER real banners).

## Untouched points that already carry an OUTCOME in Azure (untouched is NOT Not Executed)

- 129381 (suite 134452): 135556=Passed
- 129382 (suite 134453): 135669=Passed, 135670=Failed, 135672=Passed
- 129384 (suite 134455): 135969=Passed
- 129389 (suite 134460): 136103=Passed, 136106=Passed

## Rows that will overwrite an EXISTING non-Not-Executed outcome with a different one (current to new)

- 129372: 135286 Failed to Passed, 135290 Failed to Passed, 135302 Failed to Passed, 135306 Failed to Passed
- 129384: 135968 Passed to NA
- 129390: 136534 Passed to Blocked, 136538 Passed to Blocked, 136569 Passed to Blocked, 136523 Passed to NA, 136541 Passed to NA, 136498 Failed to NA

## Untouched TC ids per suite

- **129368** (74): 135105-135114, 135131-135132, 135135, 135138, 135140-135142, 135144-135146, 135148, 135150-135151, 135153-135162, 135176-135178, 135181-135183, 135220-135223, 135227-135229, 135236-135243, 135246, 135249-135255, 135258-135261, 135263-135270
- **129372** (3): 135277, 135323-135324
- **129381** (25): 135519, 135522-135523, 135526-135527, 135532, 135540-135541, 135547, 135556, 135560-135561, 135591-135592, 135596-135597, 135600-135601, 135604, 135606, 135618-135619, 135623, 135626, 135630
- **129382** (53): 135645, 135651, 135655-135660, 135663-135664, 135666-135673, 135680-135698, 135701, 135704-135716, 135718-135719
- **129384** (51): 135925, 135930-135932, 135938-135939, 135942-135944, 135948-135949, 135953, 135969, 135971, 135973, 135977-135979, 135983, 135986, 135992, 135994-135995, 135997, 136000, 136002-136003, 136006, 136008, 136010-136011, 136015-136017, 136024, 136030, 136032-136036, 136040-136041, 136043, 136046-136047, 136060, 136062, 136064-136066
- **129389** (13): 136095-136096, 136103, 136106-136107, 136111, 136113, 136120, 136122, 136127, 136129, 136137, 136139
- **129390** (32): 136473, 136476, 136481-136482, 136492, 136496-136497, 136499, 136510, 136512, 136514, 136516-136517, 136521, 136525, 136527, 136529, 136533, 136544, 136548, 136551, 136553-136555, 136557, 136559, 136561, 136563-136565, 136567, 136574
