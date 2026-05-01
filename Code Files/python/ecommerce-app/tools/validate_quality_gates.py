"""Validate the integrated AI demo quality gates."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path

import generate_demo_docs

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
SUMMARY_MD = REPORTS_DIR / "quality-gates-summary.md"
SUMMARY_JSON = REPORTS_DIR / "quality-gates.json"


@dataclass
class GateResult:
    name: str
    passed: bool
    detail: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def class_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def function_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def gate(name: str, condition: bool, detail: str) -> GateResult:
    return GateResult(name, condition, detail)


def validate_architecture() -> GateResult:
    condition = {"PaymentProcessor", "AbstractPaymentMethod"}.issubset(class_names(ROOT / "src" / "payment" / "payment_processor.py")) and "ApplePayPaymentMethod" in class_names(ROOT / "src" / "payment" / "apple_pay_payment_method.py")
    return gate("Architecture discovery", condition, "Strategy pattern classes present: PaymentProcessor, AbstractPaymentMethod, ApplePayPaymentMethod.")


def validate_implementation_contract() -> GateResult:
    source = read_text(ROOT / "src" / "payment" / "apple_pay_payment_method.py")
    required = {"process_payment", "process_apple_pay_payment", "validate_token", "validate_payment", "refund_payment", "_execute_with_retry", "_build_request_headers"}
    condition = required.issubset(function_names(ROOT / "src" / "payment" / "apple_pay_payment_method.py")) and "Idempotency-Key" in source
    return gate("Implementation contract", condition, "Apple Pay method exposes processing, validation, refund, retry, and idempotency behavior.")


def validate_technical_debt() -> GateResult:
    apple_source = read_text(ROOT / "src" / "payment" / "apple_pay_payment_method.py")
    ticket_text = read_text(ROOT / "docs" / "tickets" / "TECH-DEBT-payment-module-security-fixes.md").lower()
    logger_lines = [line for line in apple_source.splitlines() if "logger." in line]
    raw_payment_logging = any("payment_data" in line or "apple_pay_token" in line for line in logger_lines)
    hardcoded_secret = bool(re.search(r"['\"](?:sk|pk|apay)_(?:live|test)_[A-Za-z0-9]{12,}['\"]", apple_source))
    debt_registered = "hardcoded" in ticket_text and ("redact" in ticket_text or "sensitive payment data" in ticket_text) and "complexity" in ticket_text
    condition = "os.getenv(\"APPLE_PAY_API_KEY\"" in apple_source and debt_registered and not raw_payment_logging and not hardcoded_secret
    return gate("Technical debt guardrail", condition, "Known legacy debt is registered, and Apple Pay avoids hardcoded secrets plus raw payment-token logging.")


def validate_openapi_contract() -> GateResult:
    text = read_text(ROOT / "docs" / "api" / "apple-pay-openapi.yaml")
    required = ["openapi: 3.0", "/payments/apple-pay:", "BearerAuth:", "payments:write", "ApplePayRequest:", "PaymentSuccessResponse:", "ErrorResponse:", "Retry-After:", "INVALID_TOKEN", "UPSTREAM_UNAVAILABLE"]
    missing = [fragment for fragment in required if fragment not in text]
    return gate("API documentation", not missing, "OpenAPI spec includes endpoint, bearer auth, schemas, examples, retry headers, and expected errors." if not missing else f"Missing fragments: {', '.join(missing)}")


def validate_bdd_contract() -> GateResult:
    feature = read_text(ROOT / "tests" / "payment" / "apple_pay.feature")
    test_source = read_text(ROOT / "tests" / "payment" / "test_apple_pay.py")
    scenarios = re.findall(r"^\s*Scenario(?: Outline)?:", feature, flags=re.MULTILINE)
    topics = ["Successful", "invalid", "expired", "503", "limit", "timeout", "refunded"]
    condition = len(scenarios) >= 8 and all(topic.lower() in feature.lower() for topic in topics) and all(marker in test_source for marker in ["@given", "@when", "@then", "scenarios("])
    return gate("BDD test contract", condition, f"BDD suite defines {len(scenarios)} Apple Pay scenarios with pytest-bdd step definitions.")


def validate_living_docs() -> GateResult:
    stale = generate_demo_docs.check_artifacts(generate_demo_docs.build_artifacts())
    return gate("Living README/docs", not stale, "README and generated quality-gate docs match the current source digest." if not stale else "Stale generated files: " + ", ".join(str(path.relative_to(ROOT)) for path in stale))


def validate_workflow() -> GateResult:
    text = read_text(ROOT / ".github" / "workflows" / "integrated-ai-demo-quality-gates.yml")
    required = ["on:", "push:", "branches:", "'**'", "contents: write", "tools/generate_demo_docs.py", "tools/validate_quality_gates.py", "tools/generate_workflow_report.py", "reports/integrated-ai-workflow-report.html", "reports/logs/*.log", "pytest tests/payment/test_apple_pay.py", "github-actions[bot]"]
    missing = [fragment for fragment in required if fragment not in text]
    return gate("GitHub workflow", not missing, "Workflow runs on all branch pushes, generates docs, validates gates, runs tests, and can commit docs." if not missing else f"Missing fragments: {', '.join(missing)}")


def write_reports(results: list[GateResult]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for result in results if result.passed)
    lines = ["# Integrated AI Demo Quality Gate Summary", "", f"Passed: {passed}/{len(results)}", "", "| Gate | Status | Detail |", "|---|---|---|"]
    for result in results:
        lines.append(f"| {result.name} | {'PASS' if result.passed else 'FAIL'} | {result.detail} |")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps({"passed": passed, "total": len(results), "results": [result.__dict__ for result in results]}, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    results = [validate_architecture(), validate_implementation_contract(), validate_technical_debt(), validate_openapi_contract(), validate_bdd_contract(), validate_living_docs(), validate_workflow()]
    write_reports(results)
    for result in results:
        print(f"[{'PASS' if result.passed else 'FAIL'}] {result.name}: {result.detail}")
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
