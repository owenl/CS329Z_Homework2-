"""Fill the Section 4 report from the Gemini run artifacts and compile report.pdf.

Usage (repo root):  python3 writeup/4_create_tasks/make_report.py
Writes writeup/4_create_tasks/report_filled.tex and tasks/health-rumor-triage/report.pdf.
"""
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOB = ROOT / "tasks/health-rumor-triage/artifacts/health-rumor-triage-gemini"
OUT_TEX = ROOT / "writeup/4_create_tasks/report_filled.tex"
OUT_PDF = ROOT / "tasks/health-rumor-triage/report.pdf"


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


trials = []
for d in sorted(p for p in JOB.iterdir() if p.is_dir() and p.name.startswith("health-rumor-triage__")):
    rj = d / "result.json"
    r = json.loads(rj.read_text()) if rj.exists() else {}
    start, end = ts(r.get("started_at")), ts(r.get("finished_at"))
    reward = (r.get("verifier_result") or {}).get("rewards", {}).get("reward")
    exc = (r.get("exception_info") or {}).get("exception_type")
    ar = r.get("agent_result") or {}
    stdout = d / "verifier/test-stdout.txt"
    first = stdout.read_text().splitlines()[0] if stdout.exists() else ""
    m = re.match(r"(\d+)/(\d+)", first)
    errs = [l.strip("- ").strip() for l in (stdout.read_text().splitlines()[1:] if stdout.exists() else [])]
    trials.append(dict(name=d.name, start=start, end=end, reward=reward, exc=exc,
                       cost=ar.get("cost_usd"), tok=(ar.get("n_input_tokens") or 0) + (ar.get("n_output_tokens") or 0),
                       score=f"{m.group(1)}/{m.group(2)}" if m else "--", errs=errs))
trials.sort(key=lambda t: t["start"].timestamp() if t["start"] else 0)
trials = trials[-5:]

def cell_reward(t):
    if t["reward"] is None:
        return "0 (crash)" if t["exc"] else "--"
    return f"{t['reward']:.0f} ({t['score']})"

def cell_time(t):
    if t["start"] and t["end"]:
        s = int((t["end"] - t["start"]).total_seconds())
        return f"{s // 60}m {s % 60:02d}s"
    return "--"

def cell_cost(t):
    return f"\\${t['cost']:.2f} / {t['tok'] / 1000:.0f}k" if t["cost"] else "--"

n_pass = sum(1 for t in trials if t["reward"] == 1)
n_crash = sum(1 for t in trials if t["reward"] is None and t["exc"])
fails = [t for t in trials if t["reward"] == 0]
fail_txt = ""
if fails:
    bits = []
    for t in fails:
        wrong = [e.split(":")[0] for e in t["errs"] if "wrong" in e]
        bits.append(f"{t['score']} correct" + (f" (missed {', '.join(sorted(set(wrong))[:6])})" if wrong else ""))
    fail_txt = " The failed attempt" + ("s" if len(fails) > 1 else "") + " scored " + "; ".join(bits) + "."
crash_txt = (f" {n_crash} attempt{'s' if n_crash > 1 else ''} crashed before writing an answer "
             "(\\texttt{NonZeroAgentExitCodeError}, an agent/API error rather than a task defect).") if n_crash else ""

row = lambda f: " & ".join(f(t) for t in trials) + " " * 0
tex = rf"""\documentclass[11pt]{{article}}
\usepackage{{cs329z}}
\usepackage{{array}}
\usepackage{{booktabs}}
\usepackage{{tabularx}}
\titlespacing*{{\subsection}}{{0pt}}{{1.0ex}}{{0.3ex}}
\titlespacing*{{\section}}{{0pt}}{{0pt}}{{0.6ex}}
\begin{{document}}
\small
\setlength{{\parskip}}{{0.35\baselineskip}}

\section*{{Task ID: \texttt{{health-rumor-triage}}}}

\subsection*{{Description}}
The agent acts as a fact-checker for a health-information site. It gets 38 user-submitted health claims in
Chinese, 100 short English evidence cards (one file each), and \texttt{{RULES.md}}. For each claim it must find
the one card the claim is about and label it \textsc{{supported}}, \textsc{{contradicted}}, or
\textsc{{overstated}} in \texttt{{/app/verdicts.csv}}. The capability is catching health misinformation that is
\emph{{almost}} right: claims that keep the direction of a real finding but stretch its strength, scope,
numbers, mechanism, or evidence type. It comes from my CS329Z project (a Chinese health-rumor checker), where
these near-miss rumors were the hardest to label. The agent has to search 100 files and match across languages,
so it cannot answer in one step.

\subsection*{{Construction}}
The cards are the expert rationales from my project's rumor dataset, with shuffled ids. I wrote the claims by
perturbing card facts the way my project's perturbation feature does (negation, overclaim, wrong population or
time frame, invented mechanism, ``observational'' $\to$ ``RCT proves'', ``most'' $\to$ ``all'', ``possible''
$\to$ ``definitely''), plus correct paraphrases so over-flagging is also penalized (12/14/12
supported/contradicted/overstated). \texttt{{RULES.md}} defines every label and edge case. The hidden verifier
checks each row's card id and verdict against a gold key and gives reward 1 only if all 38 are right (two
claims accept either of two valid cards). No file, header only, one label for everything, or partial answers all
score 0; the oracle scores 1. Two blind reviews without the key matched it on every claim, and I reworded the
claims they found borderline.

\subsection*{{Outcomes}}
\begin{{center}}
\renewcommand{{\arraystretch}}{{1.1}}
\small
\begin{{tabularx}}{{\linewidth}}{{>{{\raggedright\arraybackslash}}Xccccc}}
  \toprule
  Metric & Attempt 1 & Attempt 2 & Attempt 3 & Attempt 4 & Attempt 5 \\
  \midrule
  Verifier reward & {row(cell_reward)} \\
  Wall-clock time & {row(cell_time)} \\
  Cost / tokens & {row(cell_cost)} \\
  \bottomrule
\end{{tabularx}}
\end{{center}}
mini-SWE-agent with Gemini 3.8 Flash passed {n_pass} of 5 attempts.{crash_txt}{fail_txt}
The most informative result is how the successes worked: in about 20 commands the agent read the rules and
claims, printed all 100 cards with short Python scripts, matched claims to cards by keywords, and then wrote and
format-checked the CSV, catching even the evidence-type and quantifier distortions. The task is easier than I
intended because \texttt{{RULES.md}} names every distortion type, which turns judgment into lookup. A harder
version would need evidence combined across cards, or cards that only partly address a claim.

\subsection*{{Self-assessment}}
\begin{{center}}
\renewcommand{{\arraystretch}}{{1.05}}
\small
\begin{{tabularx}}{{\linewidth}}{{>{{\bfseries\raggedright\arraybackslash}}p{{0.22\linewidth}}p{{0.1\linewidth}}X}}
  \toprule
  Axis & Rating & Brief justification \\
  \midrule
  Reproducibility & 5 & Pinned image, local files only, oracle reward 1. \\
  Capability & 4 & Real fact-checking need from my project; multi-turn search across languages. \\
  Task--verifier fidelity & 4 & Every rule is checked, shortcuts score 0, blind reviews matched the key. \\
  Difficulty & 2 & Gemini passed {n_pass}/5; explicit rules made the distortions easy to spot. \\
  \bottomrule
\end{{tabularx}}
\end{{center}}
\end{{document}}
"""
OUT_TEX.write_text(tex)
import tempfile
build = Path(tempfile.mkdtemp())
shutil.copy(OUT_TEX, build / OUT_TEX.name)
shutil.copy(ROOT / "writeup/4_create_tasks/cs329z.sty", build / "cs329z.sty")
# stand-ins for two optional font/emoji packages some TeX installs lack (no visual effect on this report)
for pkg, body in {"twemojis": r"\newcommand{\twemoji}[2][]{}", "DejaVuSansMono": ""}.items():
    if subprocess.run(["kpsewhich", f"{pkg}.sty"], capture_output=True, text=True).stdout.strip() == "":
        (build / f"{pkg}.sty").write_text(f"\\ProvidesPackage{{{pkg}}}\n{body}\n")
for _ in range(2):
    p = subprocess.run(["pdflatex", "-interaction=nonstopmode", OUT_TEX.name], cwd=build, capture_output=True, text=True)
pdf = build / "report_filled.pdf"
if not pdf.exists():
    print(p.stdout[-2000:]); raise SystemExit("pdflatex failed")
shutil.copy(pdf, OUT_PDF)
pages = re.search(r"Output written on .*?\((\d+) page", p.stdout)
print(f"wrote {OUT_PDF} ({pages.group(1) if pages else '?'} page(s)); passed {n_pass}/5")
for t in trials:
    print(t["name"], cell_reward(t), cell_time(t), cell_cost(t))
