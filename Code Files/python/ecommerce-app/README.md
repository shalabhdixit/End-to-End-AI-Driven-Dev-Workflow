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
