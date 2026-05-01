# End-to-End AI-Driven Development Workflow

This repository contains a workshop-ready Python demo that turns an AI-assisted payment feature workflow into repeatable engineering quality gates.

## What It Demonstrates

- Architecture discovery from source code
- Technical debt containment for known legacy payment risks
- BDD acceptance tests for Apple Pay payment flows
- OpenAPI contract validation
- Living README and generated documentation updates
- GitHub Actions automation on every branch push
- A self-contained HTML execution report with logs, file inventory, quality-gate status, troubleshooting guidance, and coverage details

## Demo Entry Points

- Workflow: [.github/workflows/python-integrated-ai-demo-quality-gates.yml](.github/workflows/python-integrated-ai-demo-quality-gates.yml)
- Python app: [Code Files/python/ecommerce-app](Code%20Files/python/ecommerce-app)
- Generated quality-gate docs: [Code Files/python/ecommerce-app/docs/generated/integrated-ai-demo-quality-gates.md](Code%20Files/python/ecommerce-app/docs/generated/integrated-ai-demo-quality-gates.md)
- Apple Pay BDD feature: [Code Files/python/ecommerce-app/tests/payment/apple_pay.feature](Code%20Files/python/ecommerce-app/tests/payment/apple_pay.feature)
- OpenAPI contract: [Code Files/python/ecommerce-app/docs/api/apple-pay-openapi.yaml](Code%20Files/python/ecommerce-app/docs/api/apple-pay-openapi.yaml)

## Local Verification

```bash
cd "Code Files/python/ecommerce-app"
python -m pip install -r requirements.txt pytest-cov
python tools/generate_demo_docs.py
python tools/validate_quality_gates.py
python -m compileall src tests tools
python -m pytest tests/payment/test_apple_pay.py --cov=src.payment --cov-branch --cov-report=term-missing --cov-fail-under=55
python tools/generate_workflow_report.py
```

## GitHub Actions Result

On push to any branch, the workflow regenerates documentation, validates quality gates, runs BDD tests and coverage, creates `reports/integrated-ai-workflow-report.html`, uploads workflow evidence, and commits generated documentation updates back to the branch when needed.
