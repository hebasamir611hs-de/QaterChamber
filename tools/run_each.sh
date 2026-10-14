#!/usr/bin/env bash
# Run each selected test in its own pytest process so one hang can't kill the batch.
# usage: tools/run_each.sh <alluredir> <log> "<marker expr>"
ALLURE="$1"; LOG="$2"; EXPR="$3"
: > "$LOG"
ids=$(python -m pytest cms/tests -m "$EXPR" --collect-only -q -n 0 -p no:cacheprovider --no-clean-evidence 2>/dev/null | grep "::")
n=$(echo "$ids" | grep -c .); i=0
while IFS= read -r nodeid; do
  [ -z "$nodeid" ] && continue; i=$((i+1))
  if [ $((i % 6)) -eq 1 ]; then rm -f .auth/state_gw*.json; timeout 300 python tools/save_auth.py >/dev/null 2>&1; fi
  out=$(timeout 540 python -m pytest "$nodeid" -n 0 --timeout=480 --alluredir="$ALLURE/t$i" --no-clean-evidence -q -p no:cacheprovider 2>&1 | tail -1)
  rc=$?
  [ -z "$out" ] && out="KILLED (hung >540s)"
  echo "[$i/$n] ${nodeid##*::} => $out" | tee -a "$LOG"
done <<< "$ids"
echo "ALL DONE" >> "$LOG"
