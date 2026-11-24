"""CS329Z HW2, Problem 7: visualize mini-SWE-agent trajectories.

Run from the repo root:
    uv run python p7_plots.py

Reads the three Section 3 jobs from writeup/3_run_example_tasks/artifacts/,
writes three PNGs into writeup/3_run_example_tasks/, and prints the numbers
behind each figure so you can write the interpretation.
"""

import glob
import json
import re
import shlex
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ARTIFACTS = Path("writeup/3_run_example_tasks/artifacts")
OUT_DIR = Path("writeup/3_run_example_tasks")

JOBS = {
    "HumanEval": "humaneval-agent",
    "SWE-bench": "swebench-django-11099",
    "Terminal-Bench": "terminal-bench-model-extraction",
}

CATEGORIES = ["inspect", "edit", "test/run", "other", "submit"]
COLORS = {
    "inspect": "#4C72B0",
    "edit": "#DD8452",
    "test/run": "#55A868",
    "other": "#8C8C8C",
    "submit": "#C44E52",
}


# ---------------------------------------------------------------- loading
def find_trajectory(job: str):
    """Return the path of the first trajectory file found for a job."""
    patterns = [
        ARTIFACTS / job / "*" / "agent" / "mini-swe-agent.trajectory.json",
        ARTIFACTS / job / "*" / "agent" / "trajectory.json",
        ARTIFACTS / job / "*" / "agent" / "*.json",
    ]
    for pattern in patterns:
        hits = sorted(glob.glob(str(pattern)))
        if hits:
            return Path(hits[0])
    return None


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return ""


def _commands_from_tool_calls(tool_calls) -> list[str]:
    cmds = []
    for tc in tool_calls or []:
        args = None
        if isinstance(tc, dict):
            fn = tc.get("function") or {}
            args = fn.get("arguments", tc.get("arguments"))
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"command": args}
        if isinstance(args, dict) and args.get("command"):
            cmds.append(str(args["command"]))
    return cmds


def extract_commands(data) -> list[str]:
    """Pull the agent's bash commands, in order, from either trajectory format."""
    cmds: list[str] = []

    # mini-swe-agent format: {"messages": [...]}
    for msg in data.get("messages", []) if isinstance(data, dict) else []:
        if msg.get("role") != "assistant":
            continue
        found = _commands_from_tool_calls(msg.get("tool_calls"))
        if not found:  # extra.actions duplicates tool_calls; use only as fallback
            extra = msg.get("extra") or {}
            for action in extra.get("actions", []) or []:
                if isinstance(action, dict) and action.get("command"):
                    found.append(str(action["command"]))
        if not found:
            found = re.findall(
                r"```(?:bash|sh)?\s*\n(.*?)```", _text(msg.get("content")), re.S
            )
        cmds.extend(c.strip() for c in found if c.strip())

    # Harbor ATIF format: {"steps": [...]}
    if not cmds and isinstance(data, dict):
        for step in data.get("steps", []):
            if step.get("source") not in (None, "agent"):
                continue
            cmds.extend(_commands_from_tool_calls(step.get("tool_calls")))

    return cmds


# ---------------------------------------------------------- classification
INSPECT = {"ls", "cat", "head", "tail", "grep", "rg", "find", "nl", "wc",
           "pwd", "tree", "file", "less", "which", "stat", "du", "awk"}
TEST = {"python", "python3", "pytest", "bash", "sh", "make", "node", "pip",
        "pip3", "uv", "./runtests.py", "tox"}


def first_program(segment: str) -> str:
    try:
        tokens = shlex.split(segment, posix=True)
    except ValueError:
        tokens = segment.split()
    # skip VAR=value prefixes and sudo
    while tokens and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]) or tokens[0] == "sudo"):
        tokens = tokens[1:]
    return Path(tokens[0]).name if tokens else ""


def programs_in(cmd: str) -> list[str]:
    """Every program invoked in a command line (split on && || ; |)."""
    shell = re.sub(r"<<\s*'?(\w+)'?.*?^\1\s*$", "", cmd, flags=re.S | re.M)  # drop heredoc bodies
    shell = re.sub(r"\"(?:\\.|[^\"\\])*\"|'[^']*'", "''", shell, flags=re.S)  # drop quoted code
    segments = re.split(r"&&|\|\||;|\||\n", shell)
    progs = [first_program(s) for s in segments if s.strip()]
    progs = ["python" if re.fullmatch(r"python[\d.]*", p) else p for p in progs]
    return [p for p in progs if p and p != "cd" and re.fullmatch(r"[\w.\-/]+", p)]


def classify(cmd: str) -> str:
    c = cmd.strip()
    if "COMPLETE_TASK_AND_SUBMIT" in c:
        return "submit"
    edit_patterns = [
        r"\bsed\s+-i", r"cat\s*<<", r"cat\s*>", r">\s*\S+\.(py|txt|json|sh|cfg|toml)\b",
        r"\btee\b", r"\bpatch\b", r"git\s+apply", r"open\([^)]*['\"]w", r"write_text",
        r"\bmv\b", r"\bcp\b", r"\bperl\s+-pi",
    ]
    if any(re.search(p, c) for p in edit_patterns):
        return "edit"
    progs = programs_in(c)
    # running code (scripts, test suites); merely reading a tests/ file is "inspect"
    if any(p in TEST or p.endswith("python") or p.startswith("python") for p in progs) \
            or re.search(r"runtests|pytest", c):
        return "test/run"
    if progs and all(p in INSPECT or p in {"sed", "git", "echo"} for p in progs):
        return "inspect"
    return "other"


# ------------------------------------------------------------------ main
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tasks: dict[str, list[str]] = {}

    for label, job in JOBS.items():
        path = find_trajectory(job)
        if path is None:
            print(f"[skip] {label}: no trajectory under {ARTIFACTS / job}")
            continue
        data = json.loads(path.read_text())
        cmds = extract_commands(data)
        tasks[label] = cmds
        print(f"[ok]   {label}: {len(cmds)} commands  ({path})")

    if not tasks:
        raise SystemExit("No trajectories found. Run P4-P6 first.")

    labels = list(tasks)
    cats_per_task = {t: [classify(c) for c in cmds] for t, cmds in tasks.items()}

    # ---- Figure 1: effort distribution (share of commands per activity)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    left = [0.0] * len(labels)
    print("\nFigure 1 - effort distribution (% of commands)")
    for cat in CATEGORIES:
        shares = []
        for t in labels:
            n = len(cats_per_task[t]) or 1
            shares.append(100 * cats_per_task[t].count(cat) / n)
        ax.barh(labels, shares, left=left, color=COLORS[cat], label=cat)
        left = [a + b for a, b in zip(left, shares)]
        print(f"  {cat:9s} " + "  ".join(f"{t}={s:.0f}%" for t, s in zip(labels, shares)))
    for i, t in enumerate(labels):
        ax.text(101, i, f"n={len(cats_per_task[t])}", va="center", fontsize=9)
    ax.set_xlim(0, 112)
    ax.set_xlabel("Share of agent commands (%)")
    ax.set_title("How mini-SWE-agent split its effort across activities")
    ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.15), frameon=False)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "effort-distribution.png", dpi=200)
    plt.close(fig)

    # ---- Figure 2: bash command usage (top programs per task)
    counts = {t: Counter(p for c in tasks[t] for p in programs_in(c)) for t in labels}
    top = [p for p, _ in sum(counts.values(), Counter()).most_common(10)]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    width = 0.8 / len(labels)
    for i, t in enumerate(labels):
        xs = [j + i * width for j in range(len(top))]
        ax.bar(xs, [counts[t][p] for p in top], width=width, label=t)
    ax.set_xticks([j + width * (len(labels) - 1) / 2 for j in range(len(top))])
    ax.set_xticklabels(top, rotation=30, ha="right")
    ax.set_ylabel("Times invoked")
    ax.set_title("Command-line programs used by the agent, by task (top 10 overall)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "bash-command-usage.png", dpi=200)
    plt.close(fig)
    print("\nFigure 2 - program counts")
    for t in labels:
        print(f"  {t}: {dict(counts[t].most_common(8))}")

    # ---- Figure 3: exploration -> implementation timeline
    fig, ax = plt.subplots(figsize=(10, 1.4 + 1.1 * len(labels)))
    print("\nFigure 3 - first edit step (exploration -> implementation)")
    for row, t in enumerate(labels):
        cats = cats_per_task[t]
        for step, cat in enumerate(cats, start=1):
            ax.scatter(step, row, color=COLORS[cat], s=60, marker="s")
        first_edit = next((i for i, c in enumerate(cats, start=1) if c == "edit"), None)
        if first_edit:
            ax.vlines(first_edit - 0.5, row - 0.35, row + 0.35, colors="black", linestyles="--")
            ax.text(first_edit - 0.4, row + 0.38, f"first edit: step {first_edit}", fontsize=8)
        pct = f"{100 * (first_edit - 1) / len(cats):.0f}%" if first_edit and cats else "n/a"
        print(f"  {t}: first edit at step {first_edit} of {len(cats)} "
              f"(explored for {pct} of the run)")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_ylim(-0.6, len(labels) - 0.2)
    ax.invert_yaxis()
    ax.set_xlabel("Agent step (one bash command per step)")
    ax.set_title("When did the agent stop exploring and start implementing?")
    handles = [plt.Line2D([], [], marker="s", ls="", color=COLORS[c], label=c) for c in CATEGORIES]
    ax.legend(handles=handles, ncol=5, loc="upper center",
              bbox_to_anchor=(0.5, -0.35), frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "exploration-to-implementation.png", dpi=200)
    plt.close(fig)

    print(f"\nSaved 3 figures to {OUT_DIR}/")


if __name__ == "__main__":
    main()
