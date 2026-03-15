from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PROFILE_OUTPUT_ROOT = REPO_ROOT / "validation" / "execution_profiles" / "remote_workflow_v1b"
BRIEF_OUTPUT_ROOT = PROFILE_OUTPUT_ROOT / "briefs"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _title_from_content(item: dict[str, Any]) -> str:
    title = item.get("title", "").strip()
    if title:
        return title
    content = item.get("content", "").strip()
    return content.splitlines()[0] if content else "Untitled case"


def _bullet_list(items: list[str]) -> str:
    if not items:
        return "- none\n"
    return "".join(f"- {item}\n" for item in items)


def _supporting_lines(supporting_items: list[dict[str, Any]]) -> str:
    lines = []
    for item in supporting_items:
        content = item.get("content", "").strip().replace("\n\n", " | ")
        lines.append(f"- `{item['item_id']}` { _title_from_content(item) }: {content}")
    return "\n".join(lines) + ("\n" if lines else "")


def _kernel_reason_map(bundle: dict[str, Any]) -> dict[str, list[str]]:
    return {
        output["kernel_type"]: output.get("reasons", [])
        for output in bundle.get("kernel_outputs", [])
    }


def _next_action_text(arbiter_response: dict[str, Any]) -> str:
    action = arbiter_response.get("recommended_action", "")
    mapping = {
        "prioritise_for_review": "Prioritize for human review and concrete follow-up.",
        "hold_for_recheck": "Keep on watchlist and enrich the case before acting.",
        "suppress": "Do not prioritize further work unless new evidence appears.",
    }
    return mapping.get(action, action or "No next action provided.")


def build_case_brief(case_dir: Path) -> str:
    primary_item = _load_json(case_dir / "primary_item.json")
    supporting_items = _load_json(case_dir / "supporting_items.json")
    case_summary = _load_json(case_dir / "case_summary.json")
    bundle = _load_json(case_dir / "kernel_bundle_result.json")
    arbiter_response = _load_json(case_dir / "arbiter_response.json")

    kernel_reasons = _kernel_reason_map(bundle)
    title = _title_from_content(primary_item)
    summary = bundle["composed_summary"]["summary"]

    return (
        f"# Remote Workflow Opportunity Brief\n\n"
        f"## Title\n\n"
        f"{title}\n\n"
        f"## Primary Item\n\n"
        f"- id: `{primary_item['item_id']}`\n"
        f"- type: `{primary_item['item_type']}`\n"
        f"- content: {primary_item['content'].strip().replace(chr(10) + chr(10), ' | ')}\n\n"
        f"## Supporting Items\n\n"
        f"{_supporting_lines(supporting_items)}\n"
        f"## Case Summary\n\n"
        f"{summary}\n\n"
        f"## Bundle Result\n\n"
        f"- judgment: `{case_summary['bundle_judgment']}`\n"
        f"- confidence: `{case_summary['bundle_confidence']}`\n\n"
        f"## Arbiter Result\n\n"
        f"- judgement: `{arbiter_response['judgement']}`\n"
        f"- confidence: `{arbiter_response['confidence']}`\n"
        f"- recommended action: `{arbiter_response['recommended_action']}`\n\n"
        f"## Why It Landed Here\n\n"
        f"### Observed State\n\n"
        f"{_bullet_list(kernel_reasons.get('observed_state', []))}\n"
        f"### Expected State\n\n"
        f"{_bullet_list(kernel_reasons.get('expected_state', []))}\n"
        f"### Contradiction\n\n"
        f"{_bullet_list(kernel_reasons.get('contradiction', []))}\n"
        f"### Arbiter Factors\n\n"
        f"{_bullet_list(arbiter_response.get('key_factors', []))}\n"
        f"## Recommended Next Action\n\n"
        f"{_next_action_text(arbiter_response)}\n"
    )


def generate_opportunity_briefs() -> dict[str, Any]:
    summary = _load_json(PROFILE_OUTPUT_ROOT / "summary.json")
    case_dirs = sorted(path for path in PROFILE_OUTPUT_ROOT.iterdir() if path.is_dir() and path.name.startswith("case_"))
    BRIEF_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    generated_files: list[str] = []
    for case_dir in case_dirs:
        brief = build_case_brief(case_dir)
        output_path = BRIEF_OUTPUT_ROOT / f"{case_dir.name}.md"
        output_path.write_text(brief, encoding="utf-8")
        generated_files.append(str(output_path))

    index_lines = [
        "# Remote Workflow Opportunity Brief Pack",
        "",
        f"- profile: `{summary['profile_name']}`",
        f"- cases: `{summary['cases_run']}`",
        f"- promoted: `{summary['promoted']}`",
        f"- watchlist: `{summary['watchlist']}`",
        f"- rejected: `{summary['rejected']}`",
        "",
        "## Briefs",
        "",
    ]
    for path in generated_files:
        rel = Path(path).relative_to(REPO_ROOT)
        index_lines.append(f"- [{rel.as_posix()}](./{rel.as_posix()})")
    (BRIEF_OUTPUT_ROOT / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    return {
        "profile_name": summary["profile_name"],
        "cases": summary["cases_run"],
        "generated_files": generated_files,
        "status": "success",
    }


if __name__ == "__main__":
    print(json.dumps(generate_opportunity_briefs(), indent=2))
