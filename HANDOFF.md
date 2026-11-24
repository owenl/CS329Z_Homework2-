# CS329Z Assignment 2: handoff for another AI assistant

Owner: Owen Liu. Repo on disk: `~/assignment2-evals` (macOS, Apple Silicon).
Handout: `cs329z_assignment2_evaluation.pdf` in this repo (v26.1.0).
Task submission is due **Monday Nov 23** (Gradescope, GitHub integration).
Peer review is due Dec 2 and is not covered here.

Read this whole file before running anything. Every command below runs **from the repo root**
(`cd ~/assignment2-evals`) with **Docker Desktop running**.

---

## 1. Status at handoff

| Part | Weight | Status |
|---|---|---|
| Section 2 (Basics) | 5% | Done. `writeup/2_basics/responses.md` complete. |
| Section 3 (Run example tasks, P3–P7) | 10% | Done. `writeup/3_run_example_tasks/responses.md`, 3 figures, 4 artifact jobs. |
| Section 4 (Own task) | 70% | Done: oracle reward 1, clean Run 3 = 5/5 at 38/38, `report.pdf` written. **Only push + submit left.** |
| Push to private GitHub | n/a | **Failed with "Repository not found"** (see section 5). |
| Gradescope submit | n/a | Not done. |

`uv run python check_submission.py` currently passes Sections 2–3. Section 4 is missing
`report.pdf` and a complete `health-rumor-triage-gemini` job with 5 attempts.

---

## 2. The Section 4 task: `tasks/health-rumor-triage/`

**Idea.** This comes from Owen's CS329Z project "医谣粉碎机" (a health-rumor checker with
true/false/misleading verdicts and a "perturbation" feature). The agent gets **38 Chinese health
claims** and **100 English evidence cards** (one card per rationale from the project's
`rumors.json`). For each claim it must find the one card it is about and label it `SUPPORTED`,
`CONTRADICTED`, or `OVERSTATED`, following `environment/RULES.md`. The claims are perturbations of
the card facts: negation, overclaim, wrong scope or population, added mechanism, upgraded
evidence ("observational" becomes "RCT proves"), quantifier ("most" becomes "all"), and hedge
removal ("possible" becomes "definitely").

**Files**
```
tasks/health-rumor-triage/
├── task.toml              # name MUST be org/name format: "owenliu/health-rumor-triage"
├── instruction.md         # 38 claims, output /app/verdicts.csv (claim_id,evidence_id,verdict)
├── environment/
│   ├── Dockerfile         # same pinned python:3.12 image as tasks/humaneval-0
│   ├── claims.csv         # 38 claims (C01–C38)
│   ├── RULES.md           # verdict definitions + clarifications
│   └── evidence/EV-###.txt  # 100 cards (ids shuffled with seed 329)
├── tests/test.sh          # runs test_outputs.py; writes 1/0 to /logs/verifier/reward.txt
├── tests/test_outputs.py  # hidden GOLD; reward 1 only if all 38 card ids + verdicts correct
└── solution/solve.sh      # oracle: writes the gold verdicts.csv
```
- Label mix: 14 CONTRADICTED, 12 SUPPORTED, 12 OVERSTATED.
- Two claims accept two cards each: C20 (EV-315 or EV-389) and C27 (EV-504 or EV-156).
- The verifier tolerates case, extra spaces, and a UTF-8 BOM. Missing file, header only, any
  wrong row, duplicates, or extra ids all give 0.

**Validation already done (locally, outside Docker)**
- Oracle gets 38/38 and reward 1. Calling everything SUPPORTED gets 12/38 and reward 0.
  Answering only the first 20 claims gets 20/38 and reward 0.
- Two independent blind reviews (no answer key) agreed with the gold labels on every claim.
  Their wording suggestions are applied.

**Gemini results so far (mini-SWE-agent + gemini-3.8-flash)**

| Run | Task version | Attempts | Result |
|---|---|---|---|
| Run 1 (started 23:01 local, Nov 23) | 20 claims | interrupted; 2 finished, 1 crashed | Both finished attempts scored **20/20 (reward 1)**. Crash was `NonZeroAgentExitCodeError` (`tee: /logs/agent/... No such file`), an agent/infra error. |
| Run 2 (22 min, finished ~23:20 local) | 38 claims | 5 started, 4 finished, 1 crashed (`BxbmTYz`, no result) | **All 4 finished attempts scored 38/38 (reward 1)**: `ygegNvn` 6m17s $0.16, `yGLqqdW` 5m36s $0.15, `5tnNyXC` 6m00s $0.24, `sTRQBvF` 4m28s $0.16. |

Run 1 never actually stopped, so its process kept writing into the same job folder, and Run 2's
folder ended up mixing both runs. In Run 2's printout, `crmTca4`, `JwhJGkj`, `ULtaqgB` and `whFRnhQ`
are leftovers from Run 1: they are 20-claim answers re-graded against the 38-claim key, which is
why they show "20/38". **Do not submit that mixed folder.**

**How Gemini solved it** (from the `ygegNvn` and `sTRQBvF` trajectories, about 18–22 commands):
`cat RULES.md` and `claims.csv`, short Python scripts to print all 100 cards a chunk at a time,
keyword matching of claims to cards, one Python script that writes `verdicts.csv`, a format check,
then submit.

**Conclusion:** the task is too easy for the Difficulty criterion. Owen chose to **submit
tonight anyway**, with an honest report, rather than redesign. Likely reason: `RULES.md` names
every distortion type, which turns judgment into lookup. A harder redesign would need evidence
that must be combined across cards, or cards that only partly address a claim.

**Run 3 (clean):** started 23:30:34 local into an empty folder. `run_section4.sh` now kills any
leftover `harbor run` process first; doing so ended Run 1/2's process, and that is the
`KeyboardInterrupt`/SIGTERM traceback in the last printout. Use Run 3's 5 attempts for the report.

**Run 3 result (final, clean): 5/5 attempts scored 38/38 (reward 1), no crashes, no leaked keys.**
`N52zaBA` 5m09s $0.15, `yahg52K` 5m41s $0.19, `ZBokvk8` 7m03s $0.25, `odqkDZ3` 6m17s $0.20,
`KsRSwnc` 5m38s $0.20. `report.pdf` has been regenerated from these (difficulty self-rating 1).
`check_submission.py` passes all of Sections 2–4.

---

## 3. Run Section 4 (on Owen's Mac)

One command does the oracle run, the 5 Gemini attempts, and key redaction:
```bash
bash ~/assignment2-evals/run_section4.sh
```
What it runs (equivalent manual commands):
```bash
uv run harbor run --path tasks/health-rumor-triage --agent oracle \
  --n-attempts 1 --n-concurrent 1 --job-name health-rumor-triage-oracle \
  --jobs-dir tasks/health-rumor-triage/artifacts --yes

uv run harbor run --path tasks/health-rumor-triage --agent-import-path pinned_agent:MiniSweAgent \
  --model gemini/gemini-3.8-flash --env-file .env \
  --n-attempts 5 --n-concurrent 1 --job-name health-rumor-triage-gemini \
  --jobs-dir tasks/health-rumor-triage/artifacts --yes
```
- Expected: oracle reward 1.0. Gemini takes about 20–40 min. **Do not interrupt it**: the last run
  was cut off and left only 3 of 5 attempts.
- Then check the per-attempt summary printed at the end (`N/38 claims fully correct`).
- **Difficulty target: at most 2 of 5 attempts succeed.** If 3 or more succeed, make the task
  harder (add more subtle claims of the same kinds) and rerun.

**Known gotchas**
- `.env` must contain an **old-format key starting with `AIza`** (`GEMINI_API_KEY=AIza...`).
  New-format keys starting with `AQ.` fail with `ACCESS_TOKEN_TYPE_UNSUPPORTED` in the pinned
  litellm. The Google Cloud project has billing enabled (Tier 1), so 503 overload errors should
  be rare.
- Gemini sometimes runs `env`, which **prints the API key into trajectories**. `run_section4.sh`
  redacts keys afterwards. `push_to_github.sh` scans and refuses to push if a key is found.
  Never commit `.env` (it is git-ignored).
- Harbor fails with "Either datasets or tasks must be provided" if `task.toml` `[task].name` is
  not in `org/name` format.
- On Apple Silicon only the SWE-bench task needed `export DOCKER_DEFAULT_PLATFORM=linux/amd64`.
  This task does not.

---

## 4. Report: `tasks/health-rumor-triage/report.pdf` (one page)

**Generator already written:** `python3 writeup/4_create_tasks/make_report.py` reads the 5
attempts in `artifacts/health-rumor-triage-gemini/` (reward, N/38, time, cost) and fills the
template. It writes `writeup/4_create_tasks/report_filled.tex` and compiles
`tasks/health-rumor-triage/report.pdf`, checked to fit on one page. It needs `pdflatex`. It
creates stub `twemojis`/`DejaVuSansMono` packages only if the TeX install lacks them. The
self-assessment it writes: reproducibility 5, capability 4, fidelity 4, difficulty 2. The
sentence about how Gemini solved the task is based on the real trajectories (see section 2).
Rerun it after Run 3 finishes.

Start from `writeup/4_create_tasks/report.tex` and compile to PDF at
`tasks/health-rumor-triage/report.pdf`. Rubric (handout 4.4–4.5): name the capability, the
environment and initial assets, the verification strategy, **the outcomes of all 5 attempts
(report every one, including N/38 per attempt from `verifier/test-stdout.txt`)**, and the most
informative success or failure.

Suggested content:
- **Capability**: catching subtly distorted health information (cross-lingual evidence matching
  plus judging scope, strength and evidence type). It is motivated by the 医谣粉碎机 project and
  real fact-checking workflows.
- **Environment**: the 38 claims, 100 cards, and RULES.md described above. No internet is needed
  for the solution.
- **Verification**: hidden gold, exact card and verdict for all 38. Alternatives are accepted for
  C20 and C27. Do-nothing gives 0. Shortcuts (all one label, partial answers) give 0.
- **Outcomes**: fill in from `tasks/health-rumor-triage/artifacts/health-rumor-triage-gemini/*/verifier/test-stdout.txt`.
  For the failures, name which claim types Gemini missed (e.g. OVERSTATED vs SUPPORTED on
  evidence-type or quantifier upgrades) and check that each miss is the model's error, not a
  task defect.

---

## 5. Push to GitHub and submit

Target repo: `https://github.com/owenyliu/stanfordcs329zhw2` (**must be Private**).
The first attempt already committed locally (commit `ca74be8`) and switched remotes
(`origin` is now Owen's repo, the course repo is `upstream`), but **the push failed with
"Repository not found"**. Likely causes, in order:
1. The repo does not exist under that exact name or owner. Check by opening the URL while logged
   in as `owenyliu`.
2. macOS Keychain has cached credentials for a **different GitHub account**. A private repo then
   looks "not found". Fix:
   ```bash
   printf "protocol=https\nhost=github.com\n\n" | git credential-osxkeychain erase
   git push -u origin HEAD:main     # sign in as owenyliu; use a Personal Access Token as the password
   ```
   (Owen enters the credentials himself.)

After the Section 4 runs and the report are done, push again (this commits new files and pushes):
```bash
bash ~/assignment2-evals/push_to_github.sh https://github.com/owenyliu/stanfordcs329zhw2.git
```
`push_to_github.sh` stages `writeup tasks p7_plots.py run_section4.sh push_to_github.sh`, runs
the secret scan and `check_submission.py`, commits, and pushes to `main`. `HANDOFF.md` is not
committed. Then on Gradescope choose **GitHub**, pick `owenyliu/stanfordcs329zhw2`, branch `main`, and
submit. Gradescope grades a snapshot, so you can resubmit until the deadline.

---

## 6. Other context

- Section 3 write-ups were rewritten in Owen's plain student voice. Keep that tone for the report.
- `p7_plots.py` (repo root) regenerates the three P7 figures: `uv run python p7_plots.py`.
- An unrelated `harbor analyze` run was moved to `jobs/` (git-ignored) on purpose.
- Owen has an OAE accommodation letter for CS329Z. If time runs out, he may request an extension.
- Owen prefers explanations in simple language (Chinese is fine for explanations, English for
  graded write-ups).
