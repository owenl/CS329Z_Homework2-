#!/bin/bash
# Push this assignment to YOUR OWN PRIVATE GitHub repo for Gradescope.
# Usage:  bash ~/assignment2-evals/push_to_github.sh https://github.com/<you>/<private-repo>.git
set -euo pipefail
cd "$(dirname "$0")"
URL="${1:?Give your private repo URL, e.g. https://github.com/<you>/cs329z-assignment2.git}"

echo "== 1. secret scan (stops if any API key is found outside .env)"
if grep -rlE "AIza[0-9A-Za-z_-]{20,}|AQ\.[A-Za-z0-9_-]{20,}|sk-or-[A-Za-z0-9]{20,}" \
     --exclude-dir=.venv --exclude-dir=.git --exclude=.env . ; then
  echo "STOP: the files above contain an API key. Ask Claude to redact them."; exit 1
fi
git check-ignore -q .env && echo "ok: .env is git-ignored"

echo "== 2. submission check"
uv run python check_submission.py || true

echo "== 3. point origin at your private repo (course repo kept as 'upstream')"
if git remote get-url origin 2>/dev/null | grep -q "cs329z/assignment2"; then
  git remote rename origin upstream
fi
git remote remove origin 2>/dev/null || true
git remote add origin "$URL"
git remote -v

echo "== 4. commit"
git add writeup tasks p7_plots.py run_section4.sh push_to_github.sh
git status --short | head -30
git commit -m "CS329Z Assignment 2: Sections 2-4" || echo "(nothing new to commit)"

echo "== 5. push"
git push -u origin HEAD:main
echo "Done. On Gradescope choose GitHub, pick this repo and branch 'main'."
