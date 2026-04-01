#!/usr/bin/env bash
set -euo pipefail
scan_tasks() {
  # Emits line-delimited JSON for tasks found
  rg -n --no-heading -e 'TODO|FIXME|\[ \]|^- \[ \]|^## +Tasks|^#\s*Tasks' \
    --glob '!node_modules' --glob '!.git' --glob '!attic' --glob '!quarantine' \
    | awk -F: '{
      file=$1; line=$2; text=""; for(i=3;i<=NF;i++){text=text $i" "}; gsub(/^[ \t]+|[ \t]+$/,"",text);
      gsub(/"/,"\\\\"",text);
      printf("{\"file\":\"%s\",\"line\":%s,\"text\":\"%s\"}\n",file,line,text);
    }'
}
normalize_task() {
  # stdin: line JSON; stdout: single task JSON normalized for backlog
  jq -r '
    . as $t
    | {
        id: ( ($t.file|gsub("[^A-Za-z0-9]+";"_")) + "_" + ($t.line|tostring) ),
        tier: 1,
        priority: 5,
        title: ("Fix: " + ($t.text|.[0:120])),
        source: {file:$t.file, line:$t.line},
        action: "apply_patch_or_impl",
        expected_receipt: ("reports/receipt_" + (now|tostring) + "_" + ($t.file|gsub("[^A-Za-z0-9]+";"_")) + "_" + ($t.line|tostring) + ".json")
      }'
}