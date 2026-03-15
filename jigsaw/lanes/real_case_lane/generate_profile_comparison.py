from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATION_ROOT = REPO_ROOT / "validation" / "execution_profiles"
BASELINE_PROFILE = "remote_workflow_v1b"
EXPERIMENT_PROFILE = "remote_workflow_localmix_v1"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _profile_summary(profile_name: str) -> dict[str, Any]:
    return _load_json(VALIDATION_ROOT / profile_name / "summary.json")


def _case_map(summary: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(case["primary_item_id"]): case for case in summary["cases"]}


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _lmstudio_retries(case: dict[str, Any]) -> int:
    runtime = case.get("kernel_runtime", {})
    observed = int(runtime.get("observed_state", {}).get("retries_used", 0) or 0)
    expected = int(runtime.get("expected_state", {}).get("retries_used", 0) or 0)
    return observed + expected


def _runtime_stability(case: dict[str, Any]) -> str:
    retries = _lmstudio_retries(case)
    if retries == 0:
        return "clean"
    return f"retries:{retries}"


def build_profile_comparison_markdown(baseline: dict[str, Any], experiment: dict[str, Any]) -> str:
    baseline_cases = _case_map(baseline)
    experiment_cases = _case_map(experiment)
    shared_ids = sorted(set(baseline_cases) & set(experiment_cases))

    flips: list[str] = []
    case_rows: list[str] = []
    for primary_item_id in shared_ids:
        base_case = baseline_cases[primary_item_id]
        exp_case = experiment_cases[primary_item_id]
        if base_case["arbiter_judgement"] != exp_case["arbiter_judgement"]:
            flips.append(
                f"- gc:item:{primary_item_id}: {base_case['arbiter_judgement']} -> {exp_case['arbiter_judgement']}"
            )
        case_rows.append(
            "| "
            f"`gc:item:{primary_item_id}` | "
            f"`{base_case['arbiter_judgement']}` | "
            f"`{exp_case['arbiter_judgement']}` | "
            f"`{base_case['bundle_confidence']}` | "
            f"`{exp_case['bundle_confidence']}` | "
            f"`{base_case['arbiter_fit_score']}` | "
            f"`{exp_case['arbiter_fit_score']}` | "
            f"`{_lmstudio_retries(exp_case)}` | "
            f"`{_runtime_stability(exp_case)}` |"
        )

    baseline_confidence = _avg([float(case["bundle_confidence"]) for case in baseline["cases"]])
    experiment_confidence = _avg([float(case["bundle_confidence"]) for case in experiment["cases"]])
    baseline_fit = _avg([float(case["arbiter_fit_score"]) for case in baseline["cases"]])
    experiment_fit = _avg([float(case["arbiter_fit_score"]) for case in experiment["cases"]])
    total_retries = sum(_lmstudio_retries(case) for case in experiment["cases"])

    lines = [
        "# Execution Profile Comparison",
        "",
        f"Baseline profile: `{baseline['profile_name']}`",
        f"Experiment profile: `{experiment['profile_name']}`",
        "",
        "## Batch totals",
        "",
        "| Metric | Baseline | Experiment |",
        "| --- | --- | --- |",
        f"| Promoted | `{baseline['promoted']}` | `{experiment['promoted']}` |",
        f"| Watchlist | `{baseline['watchlist']}` | `{experiment['watchlist']}` |",
        f"| Rejected | `{baseline['rejected']}` | `{experiment['rejected']}` |",
        f"| Avg bundle confidence | `{baseline_confidence}` | `{experiment_confidence}` |",
        f"| Avg Arbiter fit score | `{baseline_fit}` | `{experiment_fit}` |",
        f"| Total LM retries used | `0` | `{total_retries}` |",
        "",
        "## Case-by-case comparison",
        "",
        "| Case | Baseline outcome | Experiment outcome | Baseline confidence | Experiment confidence | Baseline fit score | Experiment fit score | LM retries | Runtime stability |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *case_rows,
        "",
        "## Case class flips",
        "",
    ]
    if flips:
        lines.extend(flips)
    else:
        lines.append("- No case class flips in this run.")
    lines.extend(
        [
            "",
            "## What this suggests",
            "",
            (
                f"The same controller-driven lane was run under `{baseline['profile_name']}` and "
                f"`{experiment['profile_name']}`. This comparison isolates kernel engine selection while keeping "
                "selection rules, controller logic, shaping, and Arbiter mapping fixed."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def generate_profile_comparison(
    baseline_profile: str = BASELINE_PROFILE,
    experiment_profile: str = EXPERIMENT_PROFILE,
) -> dict[str, Any]:
    baseline = _profile_summary(baseline_profile)
    experiment = _profile_summary(experiment_profile)
    output_dir = VALIDATION_ROOT / experiment_profile
    output_path = output_dir / f"COMPARISON_vs_{baseline_profile}.md"
    output_path.write_text(build_profile_comparison_markdown(baseline, experiment), encoding="utf-8")
    return {
        "baseline_profile": baseline_profile,
        "experiment_profile": experiment_profile,
        "output_path": str(output_path),
        "status": "success",
    }


if __name__ == "__main__":
    print(json.dumps(generate_profile_comparison(), indent=2))
