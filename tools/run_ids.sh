#!/usr/bin/env bash
# Run each pytest nodeid listed in a file in its own process (own allure subdir).
# usage: tools/run_ids.sh <alluredir> <log> <nodeid-file>
ALLURE="$1"; LOG="$2"; IDS="$3"; : > "$LOG"; n=$(grep -c . "$IDS"); i=0
while IFS= read -r nodeid; do
  [ -z "$nodeid" ] && continue; i=$((i+1))
  if [ $((i % 6)) -eq 1 ]; then rm -f .auth/state_gw*.json; timeout 300 python tools/save_auth.py >/dev/null 2>&1; fi
  out=$(timeout 540 python -m pytest "$nodeid" -n 0 --timeout=480 --alluredir="$ALLURE/t$i" --no-clean-evidence -q -p no:cacheprovider 2>&1 | tail -1)
  [ -z "$out" ] && out="KILLED (hung >540s)"
  echo "[$i/$n] ${nodeid##*::} => $out" | tee -a "$LOG"
done < "$IDS"
echo "ALL DONE" >> "$LOG"
