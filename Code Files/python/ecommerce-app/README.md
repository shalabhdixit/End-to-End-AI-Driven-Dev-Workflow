# E-Commerce Payment Demo Application

## Overview

This is a demo e-commerce application used for the "Multi-Track - Your AI Development Toolkit" workshop. It demonstrates how to integrate documentation, testing, and technical debt analysis skills when adding new features to legacy code.

## Current Features

- Credit card payments via a legacy Stripe-style payment method
- Apple Pay payments via a strategy-pattern extension
- BDD acceptance tests for the Apple Pay flow
- OpenAPI contract documentation
- Living documentation generated from source, tests, API docs, and technical debt records

## Setup

```bash
pip install -r requirements.txt
pytest tests/payment/test_apple_pay.py -v
```

## Integrated AI Workflow Quality Gates

This repository includes an end-to-end GitHub Actions demo that mirrors architecture discovery, technical debt assessment, test-first development, implementation validation, and API documentation generation.

Generated docs:
- [Integrated AI demo quality gates](docs/generated/integrated-ai-demo-quality-gates.md)
- [Apple Pay OpenAPI spec](docs/api/apple-pay-openapi.yaml)
- `reports/integrated-ai-workflow-report.html` as a workflow artifact after each Actions run

Workflow entry points:
- `.github/workflows/integrated-ai-demo-quality-gates.yml` when `ecommerce-app` is the repository root
- `../../../.github/workflows/python-integrated-ai-demo-quality-gates.yml` when the full workshop folder is the repository root

<!-- AI-DEMO-DOCS:START -->
## Integrated AI Workflow Quality Gates

This repository includes an end-to-end GitHub Actions demo that mirrors architecture discovery, technical debt assessment, test-first development, implementation validation, and API documentation generation.

| Gate | Evidence |
|---|---|
| Architecture discovery | Confirms PaymentProcessor strategy registration and ApplePayPaymentMethod extension points. |
| Technical debt guardrail | Requires the legacy security debt ticket while preventing new Apple Pay secret or raw-token logging regressions. |
| BDD test contract | Runs 10 Apple Pay scenarios covering happy path, validation, retries, timeout, and rollback. |
| API documentation | Validates docs/api/apple-pay-openapi.yaml for auth, schemas, examples, retry headers, and error responses. |
| Living README | This section is regenerated from source digest `36ef3916d3c2d9bb` on every workflow run. |
| HTML execution report | Publishes a self-contained debugging report with gate results, file inventory, raw logs, and troubleshooting guidance. |

**Current Apple Pay scenario map:** Successful Apple Pay payment processing, Payment rejected due to invalid Apple Pay token format, Payment rejected due to expired Apple Pay token, Apple Pay API recovers after transient failures, plus 6 more.

Generated docs:
- [Integrated AI demo quality gates](docs/generated/integrated-ai-demo-quality-gates.md)
- [Apple Pay OpenAPI spec](docs/api/apple-pay-openapi.yaml)
- `reports/integrated-ai-workflow-report.html` as a workflow artifact after each Actions run

Source digest: `36ef3916d3c2d9bb`
<!-- AI-DEMO-DOCS:END -->
