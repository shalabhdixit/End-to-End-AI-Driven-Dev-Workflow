"""Generate a self-contained HTML execution report for the demo workflow."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
LOGS = REPORTS / "logs"
OUTPUT = REPORTS / "integrated-ai-workflow-report.html"
WATCHED_FILES = [
    "README.md",
    "docs/generated/integrated-ai-demo-quality-gates.md",
    "docs/api/apple-pay-openapi.yaml",
    "docs/tickets/TECH-DEBT-payment-module-security-fixes.md",
    "tests/payment/apple_pay.feature",
    "tests/payment/test_apple_pay.py",
    "src/payment/apple_pay_payment_method.py",
    "src/payment/payment_processor.py",
    "tools/generate_demo_docs.py",
    "tools/validate_quality_gates.py",
    "tools/generate_workflow_report.py",
    ".github/workflows/integrated-ai-demo-quality-gates.yml",
]


def read_text(path: Path, fallback: str = "") -> str:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return fallback
    for encoding in ("utf-8", "utf-16", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_quality_gates() -> dict:
    path = REPORTS / "quality-gates.json"
    if not path.exists():
        return {"passed": 0, "total": 0, "results": []}
    return json.loads(read_text(path))


def collect_logs() -> list[dict[str, str | int]]:
    logs = []
    if LOGS.exists():
        for path in sorted(LOGS.glob("*.log")):
            text = read_text(path)
            logs.append({"name": path.name, "path": path.relative_to(ROOT).as_posix(), "lines": len(text.splitlines()), "chars": len(text), "text": text})
    return logs


def purpose_for(path: str) -> str:
    if path.endswith("README.md"):
        return "Living documentation entry point"
    if "docs/generated" in path:
        return "Generated architecture, BDD, and quality-gate evidence"
    if "openapi" in path:
        return "Downstream API contract"
    if "TECH-DEBT" in path:
        return "Known-risk register for legacy security debt"
    if path.endswith(".feature"):
        return "BDD business acceptance contract"
    if path.endswith("test_apple_pay.py"):
        return "pytest-bdd executable scenarios"
    if "apple_pay_payment_method" in path:
        return "Secure Apple Pay implementation under test"
    if "payment_processor" in path:
        return "Legacy strategy-pattern payment processor"
    if path.endswith(".yml"):
        return "GitHub Actions orchestration"
    return "Workflow support automation"


def file_inventory() -> list[dict[str, str | int | bool]]:
    files = []
    for relative in WATCHED_FILES:
        path = ROOT / relative
        text = read_text(path)
        files.append({"path": relative, "exists": path.exists(), "lines": len(text.splitlines()) if path.exists() else 0, "bytes": path.stat().st_size if path.exists() else 0, "purpose": purpose_for(relative)})
    return files


def extract_digest() -> str:
    match = re.search(r"Source digest: `([a-f0-9]+)`", read_text(ROOT / "README.md"))
    return match.group(1) if match else "not-found"


def summarize_tests(logs: list[dict[str, str | int]]) -> dict[str, str | int]:
    combined = "\n".join(str(log["text"]) for log in logs)
    passed_match = re.search(r"(\d+) passed", combined)
    failed_match = re.search(r"(\d+) failed", combined)
    coverage_match = re.search(r"Total coverage:\s*([0-9.]+%)", combined)
    threshold_match = re.search(r"Required test coverage of\s*([0-9.]+%) reached", combined)
    return {"passed": int(passed_match.group(1)) if passed_match else 0, "failed": int(failed_match.group(1)) if failed_match else 0, "coverage": coverage_match.group(1) if coverage_match else "not captured", "threshold": threshold_match.group(1) if threshold_match else "not captured"}


def render_gate_rows(gates: dict) -> str:
    rows = []
    for result in gates.get("results", []):
        passed = bool(result.get("passed"))
        rows.append(f"<tr><td><span class='pill {'pass' if passed else 'fail'}'>{'PASS' if passed else 'FAIL'}</span></td><td>{escape(result.get('name', 'Unknown'))}</td><td>{escape(result.get('detail', ''))}</td></tr>")
    return "\n".join(rows) or "<tr><td colspan='3'>No quality-gate data was produced.</td></tr>"


def render_file_rows(files: list[dict[str, str | int | bool]]) -> str:
    return "\n".join(f"<tr><td><span class='pill {'pass' if item['exists'] else 'fail'}'>{'FOUND' if item['exists'] else 'MISSING'}</span></td><td><code>{escape(item['path'])}</code></td><td>{escape(item['purpose'])}</td><td>{item['lines']}</td><td>{item['bytes']}</td></tr>" for item in files)


def render_log_panels(logs: list[dict[str, str | int]]) -> str:
    if not logs:
        return "<p class='muted'>No logs were captured. Check whether the workflow reached the logging steps.</p>"
    panels = []
    for index, log in enumerate(logs, 1):
        open_attr = "open" if index == 1 else ""
        panels.append(f"<details class='log-card' {open_attr}><summary><span>{escape(log['name'])}</span><span class='muted'>{log['lines']} lines · {log['chars']} chars · {escape(log['path'])}</span></summary><pre>{escape(log['text'])}</pre></details>")
    return "\n".join(panels)


def render_report(args: argparse.Namespace) -> str:
    gates = load_quality_gates()
    logs = collect_logs()
    files = file_inventory()
    tests = summarize_tests(logs)
    digest = extract_digest()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    passed = int(gates.get("passed", 0))
    total = int(gates.get("total", 0))
    failed = total - passed
    health = "pass" if failed == 0 and tests["failed"] == 0 else "fail"
    run_url = args.run_url or os.getenv("GITHUB_RUN_URL", "local execution")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Integrated AI Workflow Execution Report</title>
<style>:root{{--bg:#071018;--surface:#101b29;--surface2:#162538;--line:#284057;--text:#e8f1f8;--muted:#9fb3c8;--pass:#16a34a;--fail:#dc2626;--warn:#f59e0b;--info:#38bdf8;--accent:#8b5cf6}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Segoe UI,system-ui,sans-serif}}header{{position:sticky;top:0;padding:18px 28px;background:rgba(7,16,24,.94);border-bottom:1px solid var(--line)}}main{{padding:24px 28px 40px;max-width:1440px;margin:0 auto}}section{{margin:0 0 22px;padding:20px;background:var(--surface);border:1px solid var(--line);border-radius:8px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}.card,.step{{padding:16px;background:var(--surface2);border:1px solid var(--line);border-radius:8px}}.metric{{font-size:34px;font-weight:750}}.label,.muted{{color:var(--muted)}}.pill{{display:inline-flex;padding:4px 9px;border-radius:999px;font-size:12px;font-weight:700}}.pass{{background:rgba(22,163,74,.14);color:#86efac;border:1px solid rgba(22,163,74,.42)}}.fail{{background:rgba(220,38,38,.14);color:#fca5a5;border:1px solid rgba(220,38,38,.42)}}table{{width:100%;border-collapse:collapse}}th,td{{padding:11px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}th{{background:#0c1723;color:var(--muted);font-size:12px;text-transform:uppercase}}code,pre{{font-family:Cascadia Code,Consolas,monospace}}pre{{white-space:pre-wrap;word-break:break-word;max-height:460px;overflow:auto;padding:14px;background:#07121d;border:1px solid var(--line);border-radius:8px;font-size:12px}}.timeline{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}.log-card{{margin-bottom:12px;background:var(--surface2);border:1px solid var(--line);border-radius:8px}}.log-card summary{{cursor:pointer;display:flex;justify-content:space-between;gap:12px;padding:13px 15px}}.two-col{{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(300px,.9fr);gap:16px}}@media(max-width:760px){{.two-col{{display:block}}}}</style></head>
<body><header><h1>Integrated AI Workflow Execution Report</h1><p class="muted">Generated: {escape(generated_at)} · Branch: {escape(args.branch)} · Event: {escape(args.event)} · Source digest: <code>{escape(digest)}</code> · Run: {escape(run_url)}</p><span class="pill {health}">{'WORKFLOW READY' if health == 'pass' else 'NEEDS ATTENTION'}</span></header><main>
<section><h2>Executive Summary</h2><div class="grid"><div class="card"><div class="metric">{passed}/{total}</div><div class="label">Quality gates passed</div></div><div class="card"><div class="metric">{tests['passed']}</div><div class="label">BDD tests passed</div></div><div class="card"><div class="metric">{escape(tests['coverage'])}</div><div class="label">Coverage achieved, threshold {escape(tests['threshold'])}</div></div><div class="card"><div class="metric">{len(logs)}</div><div class="label">Captured execution logs</div></div></div></section>
<section><h2>Change Summary</h2><div class="two-col"><div><p>The workflow validates a complete AI-assisted development loop for the Python payment demo. It regenerates documentation, validates architecture and security guardrails, executes Apple Pay BDD tests, enforces coverage, and publishes this report as a debugging artifact.</p><p>Documentation freshness is tracked with source digest <code>{escape(digest)}</code>.</p></div><div class="card"><h3>Debug Signals</h3><ul><li>Quality gate table identifies the failing stage.</li><li>Raw logs preserve exact command output.</li><li>File inventory confirms source-of-truth artifacts.</li><li>Troubleshooting guidance maps failures to likely fixes.</li></ul></div></div></section>
<section><h2>Workflow Stages</h2><div class="timeline"><div class="step"><strong>1. Generate docs</strong><br><span class="muted">README and generated docs.</span></div><div class="step"><strong>2. Validate gates</strong><br><span class="muted">Architecture, security, BDD, OpenAPI, docs.</span></div><div class="step"><strong>3. Compile</strong></div><div class="step"><strong>4. Test</strong></div><div class="step"><strong>5. Coverage</strong></div><div class="step"><strong>6. Evidence</strong></div></div></section>
<section><h2>Quality Gate Results</h2><table><thead><tr><th>Status</th><th>Gate</th><th>Detail</th></tr></thead><tbody>{render_gate_rows(gates)}</tbody></table></section>
<section><h2>File Details</h2><table><thead><tr><th>Status</th><th>File</th><th>Purpose</th><th>Lines</th><th>Bytes</th></tr></thead><tbody>{render_file_rows(files)}</tbody></table></section>
<section><h2>Analysis And Troubleshooting</h2><div class="grid"><div class="card"><h3>If Documentation Gate Fails</h3><ul><li>Run <code>python tools/generate_demo_docs.py</code>.</li><li>Commit changed README and generated docs.</li></ul></div><div class="card"><h3>If BDD Tests Fail</h3><ul><li>Open <code>tests/payment/apple_pay.feature</code>.</li><li>Inspect <code>reports/logs/04-bdd-tests.log</code>.</li></ul></div><div class="card"><h3>If API Docs Fail</h3><ul><li>Restore bearer auth, <code>payments:write</code>, schemas, examples, and retry headers.</li></ul></div><div class="card"><h3>If Security Gate Fails</h3><ul><li>Remove hardcoded Apple Pay secrets.</li><li>Avoid raw token logging.</li></ul></div></div></section>
<section><h2>Raw Execution Logs</h2>{render_log_panels(logs)}</section></main></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-url", default=os.getenv("GITHUB_RUN_URL", "local execution"))
    parser.add_argument("--branch", default=os.getenv("GITHUB_REF_NAME", "local"))
    parser.add_argument("--sha", default=os.getenv("GITHUB_SHA", "local"))
    parser.add_argument("--event", default=os.getenv("GITHUB_EVENT_NAME", "local"))
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_report(args), encoding="utf-8")
    print(f"Generated HTML workflow report: {OUTPUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
