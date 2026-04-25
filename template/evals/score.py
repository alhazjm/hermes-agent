"""Score the agent's triage decisions against the gold-labelled dataset.

Usage:
    python evals/score.py                  # run agent on dataset, print metrics
    python evals/score.py --report          # write evals/report.md alongside
    python evals/score.py --predictions FILE  # score an existing predictions file
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATASET = REPO / "evals" / "dataset.jsonl"
PREDICTIONS_DEFAULT = REPO / "evals" / "predictions.jsonl"
REPORT = REPO / "evals" / "report.md"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def run_agent_on_dataset(dataset: list[dict], out_path: Path) -> None:
    """Invoke the configured Hermes runtime once per dataset case.

    The runtime is responsible for honouring AGENTS.md and emitting the
    decision contract. We pipe each case as JSON on stdin and collect
    one decision per line on stdout.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as out:
        for case in dataset:
            payload = json.dumps({
                "task": "triage_one",
                "update": case,
            })
            result = subprocess.run(
                ["hermes", "run", "--skill", "airwallex-regulatory-triage",
                 "--input", payload, "--output", "json"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                print(f"[skip] {case['id']}: {result.stderr.strip()}", file=sys.stderr)
                continue
            out.write(result.stdout.strip() + "\n")


def score(dataset: list[dict], predictions: list[dict]) -> dict:
    by_id = {p["update_id"]: p for p in predictions}
    tp = fp = tn = fn = 0
    licence_hits = licence_misses = 0
    misses: list[dict] = []

    for gold in dataset:
        pred = by_id.get(gold["id"])
        if pred is None:
            continue
        gold_flag = gold["gold_decision"] == "flag"
        pred_flag = pred["decision"] == "flag"

        if gold_flag and pred_flag:
            tp += 1
            gold_lic = set(gold.get("gold_affected_licences", []))
            pred_lic = set(pred.get("affected_licences", []))
            if gold_lic and gold_lic & pred_lic:
                licence_hits += 1
            else:
                licence_misses += 1
                misses.append({"id": gold["id"], "kind": "licence-mismatch",
                                "gold": list(gold_lic), "pred": list(pred_lic)})
        elif not gold_flag and not pred_flag:
            tn += 1
        elif gold_flag and not pred_flag:
            fn += 1
            misses.append({"id": gold["id"], "kind": "false-negative",
                            "rationale": pred.get("rationale", "")})
        else:
            fp += 1
            misses.append({"id": gold["id"], "kind": "false-positive",
                            "rationale": pred.get("rationale", "")})

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "n": len(dataset),
        "scored": tp + fp + tn + fn,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "licence_accuracy": round(licence_hits / (licence_hits + licence_misses), 3)
            if (licence_hits + licence_misses) else 0.0,
        "misses": misses,
    }


def write_report(metrics: dict) -> None:
    lines = [
        "# Eval report",
        "",
        f"- Cases: **{metrics['scored']} / {metrics['n']}**",
        f"- Precision: **{metrics['precision']}**",
        f"- Recall: **{metrics['recall']}**",
        f"- F1: **{metrics['f1']}**",
        f"- Licence-tag accuracy (on flags): **{metrics['licence_accuracy']}**",
        "",
        "## Confusion",
        "",
        f"|       | gold flag | gold ignore |",
        f"|-------|-----------|-------------|",
        f"| pred flag   | {metrics['tp']} | {metrics['fp']} |",
        f"| pred ignore | {metrics['fn']} | {metrics['tn']} |",
        "",
        "## Misses",
        "",
    ]
    if not metrics["misses"]:
        lines.append("_none_")
    else:
        for m in metrics["misses"]:
            lines.append(f"- `{m['id']}` — {m['kind']}")
    REPORT.write_text("\n".join(lines) + "\n")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--predictions", type=Path, default=None,
                   help="Score an existing predictions file instead of running the agent.")
    p.add_argument("--report", action="store_true", help="Write evals/report.md")
    args = p.parse_args()

    dataset = load_jsonl(DATASET)
    pred_path = args.predictions or PREDICTIONS_DEFAULT

    if args.predictions is None:
        if os.environ.get("HERMES_SKIP_RUN") != "1":
            run_agent_on_dataset(dataset, pred_path)

    if not pred_path.exists():
        print(f"No predictions at {pred_path}. Run without --predictions, or "
              f"unset HERMES_SKIP_RUN.", file=sys.stderr)
        return 2

    predictions = load_jsonl(pred_path)
    metrics = score(dataset, predictions)
    print(json.dumps({k: v for k, v in metrics.items() if k != "misses"}, indent=2))
    if args.report:
        write_report(metrics)
        print(f"Wrote {REPORT}")
    return 0 if metrics["f1"] >= 0.7 else 1


if __name__ == "__main__":
    sys.exit(main())
