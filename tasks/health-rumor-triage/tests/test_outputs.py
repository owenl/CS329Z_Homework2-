"""Hidden verifier for health-rumor-triage: every claim needs the right card and verdict."""

import csv
import sys
from pathlib import Path

GOLD = {
    "C01": {
        "evidence_id": [
            "EV-116"
        ],
        "verdict": "SUPPORTED"
    },
    "C02": {
        "evidence_id": [
            "EV-500"
        ],
        "verdict": "OVERSTATED"
    },
    "C03": {
        "evidence_id": [
            "EV-315"
        ],
        "verdict": "SUPPORTED"
    },
    "C04": {
        "evidence_id": [
            "EV-387"
        ],
        "verdict": "SUPPORTED"
    },
    "C05": {
        "evidence_id": [
            "EV-387"
        ],
        "verdict": "CONTRADICTED"
    },
    "C06": {
        "evidence_id": [
            "EV-212"
        ],
        "verdict": "OVERSTATED"
    },
    "C07": {
        "evidence_id": [
            "EV-506"
        ],
        "verdict": "SUPPORTED"
    },
    "C08": {
        "evidence_id": [
            "EV-480"
        ],
        "verdict": "CONTRADICTED"
    },
    "C09": {
        "evidence_id": [
            "EV-171"
        ],
        "verdict": "CONTRADICTED"
    },
    "C10": {
        "evidence_id": [
            "EV-578"
        ],
        "verdict": "SUPPORTED"
    },
    "C11": {
        "evidence_id": [
            "EV-839"
        ],
        "verdict": "CONTRADICTED"
    },
    "C12": {
        "evidence_id": [
            "EV-612"
        ],
        "verdict": "OVERSTATED"
    },
    "C13": {
        "evidence_id": [
            "EV-932"
        ],
        "verdict": "CONTRADICTED"
    },
    "C14": {
        "evidence_id": [
            "EV-359"
        ],
        "verdict": "CONTRADICTED"
    },
    "C15": {
        "evidence_id": [
            "EV-564"
        ],
        "verdict": "CONTRADICTED"
    },
    "C16": {
        "evidence_id": [
            "EV-356"
        ],
        "verdict": "SUPPORTED"
    },
    "C17": {
        "evidence_id": [
            "EV-271"
        ],
        "verdict": "CONTRADICTED"
    },
    "C18": {
        "evidence_id": [
            "EV-353"
        ],
        "verdict": "OVERSTATED"
    },
    "C19": {
        "evidence_id": [
            "EV-949"
        ],
        "verdict": "OVERSTATED"
    },
    "C20": {
        "evidence_id": [
            "EV-315",
            "EV-389"
        ],
        "verdict": "OVERSTATED"
    }
}

VERDICTS = {"SUPPORTED", "CONTRADICTED", "OVERSTATED"}


def main() -> int:
    path = Path("/app/verdicts.csv")
    if not path.exists():
        print("FAIL: /app/verdicts.csv does not exist")
        return 1
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows or set(rows[0].keys()) < {"claim_id", "evidence_id", "verdict"}:
        print("FAIL: header must be claim_id,evidence_id,verdict")
        return 1

    answers = {}
    for row in rows:
        cid = (row.get("claim_id") or "").strip()
        if cid in answers:
            print(f"FAIL: duplicate row for {cid}")
            return 1
        answers[cid] = row

    errors = []
    for cid, want in GOLD.items():
        row = answers.get(cid)
        if row is None:
            errors.append(f"{cid}: missing")
            continue
        ev = (row.get("evidence_id") or "").strip().upper()
        verdict = (row.get("verdict") or "").strip().upper()
        if verdict not in VERDICTS:
            errors.append(f"{cid}: invalid verdict {verdict!r}")
        if ev not in want["evidence_id"]:
            errors.append(f"{cid}: wrong evidence card")
        if verdict != want["verdict"]:
            errors.append(f"{cid}: wrong verdict")
    extra = set(answers) - set(GOLD)
    if extra:
        errors.append(f"unexpected claim ids: {sorted(extra)}")

    correct = sum(
        1 for cid, want in GOLD.items()
        if cid in answers
        and (answers[cid].get("evidence_id") or "").strip().upper() in want["evidence_id"]
        and (answers[cid].get("verdict") or "").strip().upper() == want["verdict"]
    )
    print(f"{correct}/{len(GOLD)} claims fully correct")
    for e in errors:
        print("  -", e)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
