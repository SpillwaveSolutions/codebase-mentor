#!/usr/bin/env python3
"""
Skill trigger eval runner for codebase-wizard.

Sends each labeled query to Claude and asks whether the skill description
would match. Collects pass_rate, duration_ms, and total_tokens metrics
across N runs, then writes results back to evals.json.

Usage:
    python evals/run_evals.py                  # 1 run (quick check)
    python evals/run_evals.py --runs 5         # 5 runs (benchmark with stddev)
    python evals/run_evals.py --set-baseline   # mark current run as baseline
    python evals/run_evals.py --verbose         # print per-query details
"""

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import anthropic

EVALS_PATH = Path(__file__).parent / "evals.json"
MODEL = "claude-haiku-4-5-20251001"

# Decoy skills to make the trigger decision realistic.
# Claude must pick codebase-wizard OR one of these OR "none".
DECOY_SKILLS = [
    {
        "name": "test-runner",
        "description": "Runs test suites, generates unit tests, and reports coverage. "
        "Use when a user wants to write tests, run tests, or check test coverage.",
    },
    {
        "name": "pr-reviewer",
        "description": "Reviews pull requests for code quality, security issues, and style. "
        "Use when a user submits a PR for review or asks for code review feedback.",
    },
    {
        "name": "refactor-helper",
        "description": "Refactors code for better structure, readability, and maintainability. "
        "Use when a user wants to restructure, rename, extract, or simplify code.",
    },
    {
        "name": "deploy-assistant",
        "description": "Manages deployment pipelines, Docker containers, CI/CD, and infrastructure. "
        "Use when a user wants to deploy, set up pipelines, or manage environments.",
    },
    {
        "name": "doc-generator",
        "description": "Auto-generates API documentation, README files, and changelogs from source code. "
        "Use when a user wants to generate docs, create API references, or produce changelogs.",
    },
]

SYSTEM_PROMPT = """\
You are a skill router. Given a user query and a list of available skills, \
decide which skill (if any) should handle the query.

Rules:
- Reply with ONLY the skill name if one matches, or "none" if no skill fits.
- Do not explain. One word (the skill name) or "none".
- Match based on user INTENT, not surface keyword overlap.
- A skill should only trigger if the user's primary goal aligns with the skill's purpose."""


def build_skills_block(target_description: str) -> str:
    skills = [{"name": "codebase-wizard", "description": target_description}]
    skills.extend(DECOY_SKILLS)
    lines = ["Available skills:"]
    for s in skills:
        lines.append(f'- **{s["name"]}**: {s["description"]}')
    return "\n".join(lines)


def evaluate_query(
    client: anthropic.Anthropic, skills_block: str, query: str
) -> dict:
    """Send one query to Claude and return (triggered_skill, duration_ms, tokens)."""
    prompt = f"{skills_block}\n\nUser query: \"{query}\"\n\nWhich skill handles this?"

    t0 = time.monotonic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=10,
        temperature=0.0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    duration_ms = (time.monotonic() - t0) * 1000

    answer = response.content[0].text.strip().lower().rstrip(".")
    total_tokens = response.usage.input_tokens + response.usage.output_tokens

    return {
        "answer": answer,
        "triggered": answer == "codebase-wizard",
        "duration_ms": round(duration_ms, 1),
        "total_tokens": total_tokens,
    }


def mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def stddev(vals: list[float]) -> float:
    if len(vals) < 2:
        return 0.0
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def run_eval_suite(client: anthropic.Anthropic, evals: dict, verbose: bool) -> dict:
    """Run all queries once and return per-query results + aggregate metrics."""
    skills_block = build_skills_block(evals["description_snapshot"])
    results = []
    durations = []
    tokens = []
    correct = 0

    for q in evals["queries"]:
        r = evaluate_query(client, skills_block, q["query"])
        passed = r["triggered"] == q["expected"]
        if passed:
            correct += 1

        result = {
            "id": q["id"],
            "query": q["query"],
            "expected": q["expected"],
            "actual": r["triggered"],
            "answer_raw": r["answer"],
            "passed": passed,
            "duration_ms": r["duration_ms"],
            "total_tokens": r["total_tokens"],
        }
        results.append(result)
        durations.append(r["duration_ms"])
        tokens.append(r["total_tokens"])

        status = "PASS" if passed else "FAIL"
        if verbose:
            arrow = "should trigger" if q["expected"] else "should NOT trigger"
            print(
                f"  [{status}] {q['id']}: \"{q['query'][:60]}...\" "
                f"({arrow}) → got '{r['answer']}' "
                f"[{r['duration_ms']:.0f}ms, {r['total_tokens']}tok]"
            )

    pass_rate = correct / len(evals["queries"]) * 100

    return {
        "results": results,
        "pass_rate": pass_rate,
        "duration_ms_mean": mean(durations),
        "duration_ms_stddev": stddev(durations),
        "total_tokens_mean": mean(tokens),
        "total_tokens_stddev": stddev(tokens),
    }


def main():
    parser = argparse.ArgumentParser(description="Run skill trigger evals")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs (default: 1)")
    parser.add_argument("--set-baseline", action="store_true", help="Mark this run as baseline")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print per-query details")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    with open(EVALS_PATH) as f:
        evals = json.load(f)

    client = anthropic.Anthropic()

    all_pass_rates = []
    all_duration_means = []
    all_token_means = []
    last_results = None

    print(f"Running {args.runs} eval run(s) against '{evals['skill']}' skill...")
    print(f"Model: {MODEL}")
    print(f"Queries: {len(evals['queries'])} ({sum(1 for q in evals['queries'] if q['expected'])} true, "
          f"{sum(1 for q in evals['queries'] if not q['expected'])} false)")
    print()

    for run_idx in range(args.runs):
        if args.runs > 1:
            print(f"━━━ Run {run_idx + 1}/{args.runs} ━━━")

        suite = run_eval_suite(client, evals, args.verbose)
        all_pass_rates.append(suite["pass_rate"])
        all_duration_means.append(suite["duration_ms_mean"])
        all_token_means.append(suite["total_tokens_mean"])
        last_results = suite["results"]

        # Print run summary
        failures = [r for r in suite["results"] if not r["passed"]]
        print(f"  Pass rate: {suite['pass_rate']:.0f}% ({len(suite['results']) - len(failures)}/{len(suite['results'])})")
        if failures:
            print(f"  Failures:")
            for f_item in failures:
                direction = "FALSE TRIGGER" if f_item["actual"] and not f_item["expected"] else "MISFIRE"
                print(f"    {direction} {f_item['id']}: \"{f_item['query'][:55]}\" → '{f_item['answer_raw']}'")
        print()

    # Compute aggregate metrics
    baseline = evals.get("baseline_run")

    metrics = {
        "pass_rate": {
            "mean": round(mean(all_pass_rates), 2),
            "stddev": round(stddev(all_pass_rates), 2) if args.runs > 1 else 0.0,
            "delta_vs_baseline": (
                round(mean(all_pass_rates) - baseline["pass_rate"]["mean"], 2)
                if baseline
                else None
            ),
        },
        "duration_ms": {
            "mean": round(mean(all_duration_means), 1),
            "stddev": round(stddev(all_duration_means), 1) if args.runs > 1 else 0.0,
            "delta_vs_baseline": (
                round(mean(all_duration_means) - baseline["duration_ms"]["mean"], 1)
                if baseline
                else None
            ),
        },
        "total_tokens": {
            "mean": round(mean(all_token_means), 1),
            "stddev": round(stddev(all_token_means), 1) if args.runs > 1 else 0.0,
            "delta_vs_baseline": (
                round(mean(all_token_means) - baseline["total_tokens"]["mean"], 1)
                if baseline
                else None
            ),
        },
    }

    # Print final report
    print("═══════════════════════════════════════════")
    print(f"  BENCHMARK RESULTS ({args.runs} run{'s' if args.runs > 1 else ''})")
    print("═══════════════════════════════════════════")
    for metric_name, vals in metrics.items():
        delta_str = ""
        if vals["delta_vs_baseline"] is not None:
            sign = "+" if vals["delta_vs_baseline"] >= 0 else ""
            delta_str = f"  (Δ {sign}{vals['delta_vs_baseline']})"
        sd_str = f" ± {vals['stddev']}" if vals["stddev"] else ""
        print(f"  {metric_name:15s}: {vals['mean']}{sd_str}{delta_str}")
    print("═══════════════════════════════════════════")

    # Update evals.json
    evals["metrics"] = metrics
    evals["last_run"] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": MODEL,
        "runs": args.runs,
        "results": last_results,
    }

    if args.set_baseline:
        evals["baseline_run"] = metrics
        print("\n  ✓ Baseline set from this run")

    with open(EVALS_PATH, "w") as f:
        json.dump(evals, f, indent=2)
        f.write("\n")

    print(f"\n  Results written to {EVALS_PATH}")

    # Exit with non-zero if any failures in last run
    if any(not r["passed"] for r in last_results):
        sys.exit(1)


if __name__ == "__main__":
    main()
