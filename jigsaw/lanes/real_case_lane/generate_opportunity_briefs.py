from __future__ import annotations

import html
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


def _title_case(value: str) -> str:
    return value.replace("_", " ").strip().title()


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


def _decision_badge_class(judgement: str) -> str:
    return {
        "promoted": "promoted",
        "watchlist": "watchlist",
        "rejected": "rejected",
    }.get(judgement, "neutral")


def _headline(case_summary: dict[str, Any], arbiter_response: dict[str, Any], primary_item: dict[str, Any]) -> str:
    title = _title_from_content(primary_item)
    judgement = arbiter_response.get("judgement", "")
    if judgement == "promoted":
        return f"{title} looks strong enough to prioritize now."
    if judgement == "watchlist":
        return f"{title} looks promising but needs more evidence before action."
    return f"{title} does not currently justify further work."


def _status_snapshot(case_summary: dict[str, Any], arbiter_response: dict[str, Any]) -> str:
    return (
        f"- outcome: `{arbiter_response['judgement']}`\n"
        f"- bundle judgment: `{case_summary['bundle_judgment']}`\n"
        f"- bundle confidence: `{case_summary['bundle_confidence']}`\n"
        f"- Arbiter confidence: `{arbiter_response['confidence']}`\n"
        f"- recommended action: `{arbiter_response['recommended_action']}`\n"
    )


def _brief_rationale(case_summary: dict[str, Any], bundle: dict[str, Any], arbiter_response: dict[str, Any]) -> str:
    bundle_summary = bundle["composed_summary"]["summary"]
    arbiter_reason = arbiter_response.get("reason_summary", "").strip()
    if arbiter_reason:
        return f"{bundle_summary} {arbiter_reason}"
    return bundle_summary


def _human_reason_lines(bundle: dict[str, Any], arbiter_response: dict[str, Any]) -> str:
    kernel_reasons = _kernel_reason_map(bundle)
    sections = [
        ("Observed picture", kernel_reasons.get("observed_state", [])),
        ("Expected fit", kernel_reasons.get("expected_state", [])),
        ("Contradiction check", kernel_reasons.get("contradiction", [])),
        ("Arbiter factors", arbiter_response.get("key_factors", [])),
    ]
    parts = []
    for title, items in sections:
        parts.append(f"### {title}\n\n{_bullet_list(items)}")
    return "\n".join(parts)


def build_case_brief(case_dir: Path) -> str:
    primary_item = _load_json(case_dir / "primary_item.json")
    supporting_items = _load_json(case_dir / "supporting_items.json")
    case_summary = _load_json(case_dir / "case_summary.json")
    bundle = _load_json(case_dir / "kernel_bundle_result.json")
    arbiter_response = _load_json(case_dir / "arbiter_response.json")

    title = _title_from_content(primary_item)
    headline = _headline(case_summary, arbiter_response, primary_item)
    brief_rationale = _brief_rationale(case_summary, bundle, arbiter_response)

    return (
        f"# Remote Workflow Opportunity Brief\n\n"
        f"## Headline\n\n"
        f"{headline}\n\n"
        f"## Title\n\n"
        f"{title}\n\n"
        f"## Decision Snapshot\n\n"
        f"{_status_snapshot(case_summary, arbiter_response)}\n"
        f"## Primary Item\n\n"
        f"- id: `{primary_item['item_id']}`\n"
        f"- type: `{primary_item['item_type']}`\n"
        f"- content: {primary_item['content'].strip().replace(chr(10) + chr(10), ' | ')}\n\n"
        f"## Supporting Items\n\n"
        f"{_supporting_lines(supporting_items)}\n"
        f"## Case Summary\n\n"
        f"{brief_rationale}\n\n"
        f"## Bundle Result\n\n"
        f"- judgment: `{_title_case(case_summary['bundle_judgment'])}`\n"
        f"- confidence: `{case_summary['bundle_confidence']}`\n\n"
        f"## Arbiter Result\n\n"
        f"- judgement: `{_title_case(arbiter_response['judgement'])}`\n"
        f"- confidence: `{arbiter_response['confidence']}`\n"
        f"- recommended action: `{arbiter_response['recommended_action']}`\n\n"
        f"## Why It Landed Here\n\n"
        f"{_human_reason_lines(bundle, arbiter_response)}\n"
        f"## Recommended Next Action\n\n"
        f"{_next_action_text(arbiter_response)}\n"
    )


def _html_list(items: list[str]) -> str:
    if not items:
        return "<ul><li>none</li></ul>"
    rendered = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    return f"<ul>{rendered}</ul>"


def _html_supporting_items(supporting_items: list[dict[str, Any]]) -> str:
    parts = []
    for item in supporting_items:
        title = html.escape(_title_from_content(item))
        content = html.escape(item.get("content", "").strip().replace("\n\n", " | "))
        parts.append(
            "<li>"
            f"<strong>{title}</strong> "
            f"<span class=\"item-meta\">#{item['item_id']}</span>"
            f"<div class=\"item-content\">{content}</div>"
            "</li>"
        )
    return "<ul class=\"supporting-list\">" + "".join(parts) + "</ul>"


def _html_reason_sections(bundle: dict[str, Any], arbiter_response: dict[str, Any]) -> str:
    kernel_reasons = _kernel_reason_map(bundle)
    sections = [
        ("Observed picture", kernel_reasons.get("observed_state", [])),
        ("Expected fit", kernel_reasons.get("expected_state", [])),
        ("Contradiction check", kernel_reasons.get("contradiction", [])),
        ("Arbiter factors", arbiter_response.get("key_factors", [])),
    ]
    rendered = []
    for title, items in sections:
        rendered.append(
            "<section class=\"reason-block\">"
            f"<h3>{html.escape(title)}</h3>"
            f"{_html_list(items)}"
            "</section>"
        )
    return "".join(rendered)


def build_case_brief_html(case_dir: Path) -> str:
    primary_item = _load_json(case_dir / "primary_item.json")
    supporting_items = _load_json(case_dir / "supporting_items.json")
    case_summary = _load_json(case_dir / "case_summary.json")
    bundle = _load_json(case_dir / "kernel_bundle_result.json")
    arbiter_response = _load_json(case_dir / "arbiter_response.json")

    title = _title_from_content(primary_item)
    headline = _headline(case_summary, arbiter_response, primary_item)
    case_summary_text = _brief_rationale(case_summary, bundle, arbiter_response)
    judgement = arbiter_response["judgement"]
    badge_class = _decision_badge_class(judgement)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} - Opportunity Brief</title>
  <style>
    :root {{
      --bg: #f4efe4;
      --paper: #fffdf7;
      --ink: #1d1b16;
      --muted: #635b4f;
      --border: #d8cdb7;
      --promoted: #1f7a4d;
      --promoted-bg: #d9f3e4;
      --watchlist: #9a6700;
      --watchlist-bg: #fff0c2;
      --rejected: #a1271f;
      --rejected-bg: #f8d9d5;
      --shadow: rgba(59, 48, 31, 0.08);
      --accent: #c7692b;
      --font-serif: Georgia, "Times New Roman", serif;
      --font-sans: "Segoe UI", Tahoma, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top right, rgba(199, 105, 43, 0.14), transparent 30%),
        linear-gradient(180deg, #f8f3e9 0%, var(--bg) 100%);
      color: var(--ink);
      font-family: var(--font-sans);
      line-height: 1.55;
    }}
    .shell {{
      max-width: 980px;
      margin: 0 auto;
      padding: 40px 20px 56px;
    }}
    .card {{
      background: var(--paper);
      border: 1px solid var(--border);
      box-shadow: 0 18px 40px var(--shadow);
      border-radius: 24px;
      overflow: hidden;
    }}
    .hero {{
      padding: 32px 32px 20px;
      border-bottom: 1px solid var(--border);
      background: linear-gradient(180deg, rgba(255,255,255,0.7), rgba(242,233,215,0.7));
    }}
    .eyebrow {{
      margin: 0 0 8px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 12px;
      color: var(--muted);
    }}
    h1 {{
      margin: 0 0 12px;
      font-family: var(--font-serif);
      font-size: clamp(32px, 4vw, 46px);
      line-height: 1.05;
    }}
    .headline {{
      margin: 0 0 18px;
      max-width: 760px;
      font-size: 20px;
      color: var(--muted);
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 14px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .badge.promoted {{ color: var(--promoted); background: var(--promoted-bg); }}
    .badge.watchlist {{ color: var(--watchlist); background: var(--watchlist-bg); }}
    .badge.rejected {{ color: var(--rejected); background: var(--rejected-bg); }}
    .grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 24px;
      padding: 28px 32px 32px;
    }}
    .panel {{
      padding: 20px 22px;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: rgba(255,255,255,0.65);
    }}
    .panel h2 {{
      margin: 0 0 14px;
      font-size: 18px;
      font-family: var(--font-serif);
    }}
    .meta-list {{
      margin: 0;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 10px;
    }}
    .meta-list li {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding-bottom: 8px;
      border-bottom: 1px dashed rgba(99, 91, 79, 0.18);
    }}
    .meta-label {{ color: var(--muted); }}
    .meta-value {{ font-weight: 600; text-align: right; }}
    .summary {{
      margin: 0;
      font-size: 17px;
    }}
    .primary-box, .action-box {{
      padding: 18px 20px;
      border-radius: 18px;
      background: #f8f3ea;
      border: 1px solid var(--border);
    }}
    .primary-title {{
      margin: 0 0 8px;
      font-weight: 700;
    }}
    .item-meta {{
      color: var(--muted);
      font-size: 13px;
      margin-left: 8px;
    }}
    .item-content {{
      margin-top: 8px;
      color: var(--muted);
    }}
    .supporting-list {{
      margin: 0;
      padding-left: 20px;
      display: grid;
      gap: 14px;
    }}
    .reason-block + .reason-block {{
      margin-top: 16px;
    }}
    .reason-block h3 {{
      margin: 0 0 8px;
      font-size: 15px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }}
    .reason-block ul {{
      margin: 0;
      padding-left: 20px;
    }}
    .action-box {{
      border-left: 6px solid var(--accent);
    }}
    .action-box p {{
      margin: 0;
      font-size: 17px;
    }}
    @media (max-width: 820px) {{
      .grid {{
        grid-template-columns: 1fr;
        padding: 20px;
      }}
      .hero {{
        padding: 24px 20px 16px;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <article class="card">
      <header class="hero">
        <p class="eyebrow">Remote Workflow Opportunity Brief</p>
        <h1>{html.escape(title)}</h1>
        <p class="headline">{html.escape(headline)}</p>
        <span class="badge {badge_class}">{html.escape(_title_case(judgement))}</span>
      </header>
      <section class="grid">
        <div class="panel">
          <h2>Decision Snapshot</h2>
          <ul class="meta-list">
            <li><span class="meta-label">Bundle judgment</span><span class="meta-value">{html.escape(_title_case(case_summary['bundle_judgment']))}</span></li>
            <li><span class="meta-label">Bundle confidence</span><span class="meta-value">{case_summary['bundle_confidence']}</span></li>
            <li><span class="meta-label">Arbiter confidence</span><span class="meta-value">{arbiter_response['confidence']}</span></li>
            <li><span class="meta-label">Recommended action</span><span class="meta-value">{html.escape(arbiter_response['recommended_action'])}</span></li>
          </ul>
        </div>
        <div class="panel">
          <h2>Case Summary</h2>
          <p class="summary">{html.escape(case_summary_text)}</p>
        </div>
        <div class="panel">
          <h2>Primary Item</h2>
          <div class="primary-box">
            <p class="primary-title">{html.escape(title)} <span class="item-meta">#{primary_item['item_id']} · {html.escape(primary_item['item_type'])}</span></p>
            <div class="item-content">{html.escape(primary_item['content'].strip().replace(chr(10) + chr(10), ' | '))}</div>
          </div>
        </div>
        <div class="panel">
          <h2>Supporting Items</h2>
          {_html_supporting_items(supporting_items)}
        </div>
        <div class="panel">
          <h2>Why It Landed Here</h2>
          {_html_reason_sections(bundle, arbiter_response)}
        </div>
        <div class="panel">
          <h2>Recommended Next Action</h2>
          <div class="action-box">
            <p>{html.escape(_next_action_text(arbiter_response))}</p>
          </div>
        </div>
      </section>
    </article>
  </main>
</body>
</html>
"""


def generate_opportunity_briefs() -> dict[str, Any]:
    summary = _load_json(PROFILE_OUTPUT_ROOT / "summary.json")
    case_dirs = sorted(path for path in PROFILE_OUTPUT_ROOT.iterdir() if path.is_dir() and path.name.startswith("case_"))
    BRIEF_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    generated_files: list[str] = []
    generated_html_files: list[str] = []
    for case_dir in case_dirs:
        brief = build_case_brief(case_dir)
        markdown_path = BRIEF_OUTPUT_ROOT / f"{case_dir.name}.md"
        html_path = BRIEF_OUTPUT_ROOT / f"{case_dir.name}.html"
        markdown_path.write_text(brief, encoding="utf-8")
        html_path.write_text(build_case_brief_html(case_dir), encoding="utf-8")
        generated_files.append(str(markdown_path))
        generated_html_files.append(str(html_path))

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
    for markdown_path, html_path in zip(generated_files, generated_html_files):
        rel_md = Path(markdown_path).relative_to(REPO_ROOT)
        rel_html = Path(html_path).relative_to(REPO_ROOT)
        index_lines.append(
            f"- HTML: [{rel_html.as_posix()}](./{rel_html.as_posix()}) | "
            f"Markdown: [{rel_md.as_posix()}](./{rel_md.as_posix()})"
        )
    (BRIEF_OUTPUT_ROOT / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    return {
        "profile_name": summary["profile_name"],
        "cases": summary["cases_run"],
        "generated_files": generated_files,
        "generated_html_files": generated_html_files,
        "status": "success",
    }


if __name__ == "__main__":
    print(json.dumps(generate_opportunity_briefs(), indent=2))
