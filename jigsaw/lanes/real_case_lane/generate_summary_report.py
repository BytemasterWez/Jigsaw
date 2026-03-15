from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PROFILE_OUTPUT_ROOT = REPO_ROOT / "validation" / "execution_profiles" / "remote_workflow_v1b"
BRIEF_OUTPUT_ROOT = PROFILE_OUTPUT_ROOT / "briefs"
REPORT_OUTPUT_ROOT = REPO_ROOT / "deliverables" / "remote_workflow" / "summary_report"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _display_value(value: str) -> str:
    return value.replace("_", " ").strip()


def _title_case(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _sentence_case(value: str) -> str:
    text = _display_value(value)
    if not text:
        return "Unknown"
    return text[0].upper() + text[1:]


def _generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _case_title(case_dir: Path) -> str:
    primary_item = _load_json(case_dir / "primary_item.json")
    title = primary_item.get("title", "").strip()
    if title:
        return title
    content = primary_item.get("content", "").strip()
    return content.splitlines()[0] if content else f"Case {case_dir.name}"


def _brief_links(case_dir: Path) -> tuple[str, str]:
    markdown_name = f"{case_dir.name}.md"
    html_name = f"{case_dir.name}.html"
    markdown_path = BRIEF_OUTPUT_ROOT / markdown_name
    html_path = BRIEF_OUTPUT_ROOT / html_name
    rel_md = markdown_path.relative_to(REPO_ROOT).as_posix()
    rel_html = html_path.relative_to(REPO_ROOT).as_posix()
    return rel_md, rel_html


def _batch_suggestion(summary: dict[str, Any]) -> str:
    promoted = summary["promoted"]
    watchlist = summary["watchlist"]
    rejected = summary["rejected"]
    if promoted and watchlist and not rejected:
        return (
            "The current batch shows a mix of clearly actionable remote workflow cases "
            "and weaker adjacent cases that still need more evidence before review."
        )
    if promoted and not watchlist and not rejected:
        return "The current batch is dominated by strong cases that are ready for review."
    if watchlist and not promoted and not rejected:
        return "The current batch suggests interest, but most cases still need more evidence before review."
    if rejected:
        return "The current batch includes weaker cases that are not yet strong enough to act on."
    return "The current batch is mixed and should be reviewed case by case."


def _case_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    case_dirs = {path.name: path for path in PROFILE_OUTPUT_ROOT.iterdir() if path.is_dir() and path.name.startswith("case_")}
    for index, case in enumerate(summary["cases"], start=1):
        case_dir_name = f"case_{index:02d}_gc_{case['primary_item_id']}"
        case_dir = case_dirs[case_dir_name]
        markdown_link, html_link = _brief_links(case_dir)
        rows.append(
            {
                "case_id": case_dir_name,
                "title": _case_title(case_dir),
                "outcome": _title_case(case["arbiter_judgement"]),
                "confidence": case["bundle_confidence"],
                "next_step": _sentence_case(case["recommended_action"]),
                "markdown_link": markdown_link,
                "html_link": html_link,
            }
        )
    return rows


def build_summary_report_markdown(summary: dict[str, Any], generated_at: str) -> str:
    rows = _case_rows(summary)
    lines = [
        "# Remote Workflow Summary Report",
        "",
        "## Overview",
        (
            f"This report summarizes {summary['cases_run']} remote workflow opportunity cases processed "
            f"under the {summary['profile_name']} execution profile."
        ),
        "",
        f"- generated: {generated_at}",
        f"- cases reviewed: {summary['cases_run']}",
        f"- promoted: {summary['promoted']}",
        f"- watchlist: {summary['watchlist']}",
        f"- rejected: {summary['rejected']}",
        "",
        "## What this batch suggests",
        _batch_suggestion(summary),
        "",
        "## Case list",
        "| Case | Title | Outcome | Confidence | Next step |",
        "|------|-------|---------|------------|-----------|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['title']} | {row['outcome']} | {row['confidence']} | {row['next_step']} |"
        )
    lines.extend(["", "## Individual briefs"])
    for row in rows:
        lines.append(
            f"- {row['case_id']}: [HTML](/"
            f"{row['html_link']}) | [Markdown](/"
            f"{row['markdown_link']})"
        )
    lines.append("")
    return "\n".join(lines)


def build_summary_report_html(summary: dict[str, Any], generated_at: str) -> str:
    rows = _case_rows(summary)
    table_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['case_id'])}</td>"
        f"<td>{html.escape(row['title'])}</td>"
        f"<td><span class=\"badge {row['outcome'].lower()}\">{html.escape(row['outcome'])}</span></td>"
        f"<td>{row['confidence']}</td>"
        f"<td>{html.escape(row['next_step'])}</td>"
        "</tr>"
        for row in rows
    )
    brief_rows = "".join(
        "<li>"
        f"<strong>{html.escape(row['case_id'])}</strong>: "
        f"<a href=\"/{html.escape(row['html_link'])}\">HTML brief</a> | "
        f"<a href=\"/{html.escape(row['markdown_link'])}\">Markdown brief</a>"
        "</li>"
        for row in rows
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Remote Workflow Summary Report</title>
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
      --font-serif: Georgia, "Times New Roman", serif;
      --font-sans: "Segoe UI", Tahoma, sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: linear-gradient(180deg, #f8f3e9 0%, var(--bg) 100%);
      color: var(--ink);
      font-family: var(--font-sans);
      line-height: 1.55;
    }}
    .shell {{
      max-width: 1040px;
      margin: 0 auto;
      padding: 40px 20px 56px;
    }}
    .card {{
      background: var(--paper);
      border: 1px solid var(--border);
      border-radius: 24px;
      box-shadow: 0 18px 40px var(--shadow);
      overflow: hidden;
    }}
    .hero {{
      padding: 32px;
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
      font-size: clamp(30px, 4vw, 44px);
      line-height: 1.05;
    }}
    .lede {{
      margin: 0;
      max-width: 760px;
      font-size: 18px;
      color: var(--muted);
    }}
    .content {{
      padding: 28px 32px 32px;
      display: grid;
      gap: 24px;
    }}
    .panel {{
      padding: 20px 22px;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: rgba(255,255,255,0.68);
    }}
    .panel h2 {{
      margin: 0 0 12px;
      font-family: var(--font-serif);
      font-size: 20px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }}
    .stat {{
      padding: 16px;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: #f8f3ea;
    }}
    .stat-label {{
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .stat-value {{
      font-size: 28px;
      font-weight: 700;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      text-align: left;
      padding: 12px 10px;
      border-bottom: 1px solid rgba(99, 91, 79, 0.16);
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .badge.promoted {{ color: var(--promoted); background: var(--promoted-bg); }}
    .badge.watchlist {{ color: var(--watchlist); background: var(--watchlist-bg); }}
    .badge.rejected {{ color: var(--rejected); background: var(--rejected-bg); }}
    ul {{
      margin: 0;
      padding-left: 20px;
    }}
    a {{
      color: #8d4c20;
    }}
    @media (max-width: 820px) {{
      .stats {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      th:nth-child(4), td:nth-child(4) {{
        display: none;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <article class="card">
      <header class="hero">
        <p class="eyebrow">Remote Workflow Summary Report</p>
        <h1>{html.escape(summary['profile_name'])}</h1>
        <p class="lede">
          This report summarizes {summary['cases_run']} remote workflow opportunity cases processed under the
          <strong>{html.escape(summary['profile_name'])}</strong> execution profile.
        </p>
      </header>
      <section class="content">
        <section class="panel">
          <h2>Overview</h2>
          <div class="stats">
            <div class="stat"><div class="stat-label">Generated</div><div class="stat-value" style="font-size:18px">{html.escape(generated_at)}</div></div>
            <div class="stat"><div class="stat-label">Cases reviewed</div><div class="stat-value">{summary['cases_run']}</div></div>
            <div class="stat"><div class="stat-label">Promoted</div><div class="stat-value">{summary['promoted']}</div></div>
            <div class="stat"><div class="stat-label">Watchlist / Rejected</div><div class="stat-value">{summary['watchlist']} / {summary['rejected']}</div></div>
          </div>
        </section>
        <section class="panel">
          <h2>What this batch suggests</h2>
          <p>{html.escape(_batch_suggestion(summary))}</p>
        </section>
        <section class="panel">
          <h2>Case list</h2>
          <table>
            <thead>
              <tr>
                <th>Case</th>
                <th>Title</th>
                <th>Outcome</th>
                <th>Confidence</th>
                <th>Next step</th>
              </tr>
            </thead>
            <tbody>
              {table_rows}
            </tbody>
          </table>
        </section>
        <section class="panel">
          <h2>Individual briefs</h2>
          <ul>{brief_rows}</ul>
        </section>
      </section>
    </article>
  </main>
</body>
</html>
"""


def generate_summary_report() -> dict[str, Any]:
    summary = _load_json(PROFILE_OUTPUT_ROOT / "summary.json")
    REPORT_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    generated_at = _generated_at()
    markdown_path = REPORT_OUTPUT_ROOT / "remote_workflow_v1b_summary.md"
    html_path = REPORT_OUTPUT_ROOT / "remote_workflow_v1b_summary.html"
    readme_path = REPORT_OUTPUT_ROOT / "README.md"

    markdown_text = build_summary_report_markdown(summary, generated_at)
    html_text = build_summary_report_html(summary, generated_at)

    markdown_path.write_text(markdown_text, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")
    readme_path.write_text(
        "\n".join(
            [
                "# Remote Workflow Summary Report",
                "",
                f"- profile: {summary['profile_name']}",
                f"- generated: {generated_at}",
                "",
                "## Available outputs",
                "",
                f"- [Markdown summary]({markdown_path.name})",
                f"- [HTML summary]({html_path.name})",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "profile_name": summary["profile_name"],
        "cases": summary["cases_run"],
        "markdown_report": str(markdown_path),
        "html_report": str(html_path),
        "readme": str(readme_path),
        "status": "success",
    }


if __name__ == "__main__":
    print(json.dumps(generate_summary_report(), indent=2))
