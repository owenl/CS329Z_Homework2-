#!/bin/bash
# Section 4: run the oracle once, then 5 Gemini attempts, for tasks/health-rumor-triage.
# Usage (from anywhere):  bash ~/assignment2-evals/run_section4.sh
set -uo pipefail
cd "$(dirname "$0")"
TASK=health-rumor-triage
ART=tasks/$TASK/artifacts

echo "== checks"
docker info >/dev/null 2>&1 || { echo "Docker is not running. Open Docker Desktop, wait for the whale icon, then rerun."; exit 1; }
grep -q '^GEMINI_API_KEY=AIza' .env || { echo ".env has no AIza-format GEMINI_API_KEY. Fix .env, then rerun."; exit 1; }
echo "ok: docker running, key present"

echo; echo "== 1/2 oracle (should be reward 1.0)"
rm -rf "$ART/$TASK-oracle"
uv run harbor run --path tasks/$TASK --agent oracle \
  --n-attempts 1 --n-concurrent 1 \
  --job-name $TASK-oracle --jobs-dir "$ART" --yes

echo; echo "== 2/2 Gemini, 5 attempts (10-30 min)"
rm -rf "$ART/$TASK-gemini"
uv run harbor run --path tasks/$TASK --agent-import-path pinned_agent:MiniSweAgent \
  --model gemini/gemini-3.8-flash --env-file .env \
  --n-attempts 5 --n-concurrent 1 \
  --job-name $TASK-gemini --jobs-dir "$ART" --yes

echo; echo "== redacting any API keys the agent printed (e.g. by running env)"
grep -rlE "AIza[0-9A-Za-z_-]{20,}|AQ\.[A-Za-z0-9_-]{20,}" "$ART" 2>/dev/null | while read -r f; do
  sed -i '' -E 's/AIza[0-9A-Za-z_-]{20,}/[REDACTED]/g; s/AQ\.[A-Za-z0-9_-]{20,}/[REDACTED]/g' "$f"; echo "redacted: $f"
done

echo; echo "== per-attempt verifier summary"
for d in "$ART/$TASK-gemini"/*/; do
  [ -f "$d/verifier/reward.txt" ] || continue
  echo "$(basename "$d"): reward=$(cat "$d/verifier/reward.txt")  $(head -1 "$d/verifier/test-stdout.txt" 2>/dev/null)"
done
echo; echo "Done. Tell Claude it finished."
