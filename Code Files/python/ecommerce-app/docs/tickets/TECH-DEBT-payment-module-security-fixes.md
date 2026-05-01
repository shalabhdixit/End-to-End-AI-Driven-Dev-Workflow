# TECH-DEBT: Payment Module Security Fixes - API Key, Log Redaction, Complexity

| Field | Value |
|---|---|
| Issue Type | Bug / Technical Debt |
| Priority | High |
| Original Estimate | 4h |
| Component | Payment |
| Labels | security, pci-dss, tech-debt |

## Description

The `payment_processor.py` module contains three confirmed issues identified in a security audit. All three must be resolved before the next PCI DSS review cycle.

## Acceptance Criteria

### AC-1 - Move Stripe API Key to Environment Variable

- Remove the hardcoded API key placeholder from source.
- Load the key at runtime from an environment variable.
- Keep `.env.example` updated and `.env` ignored.

### AC-2 - Redact Sensitive Payment Data from Logs

- Remove plaintext payment data logging.
- Replace with a log statement that records only safe operational identifiers.
- Ensure no sensitive payment data appears in application logs.

### AC-3 - Refactor `validate_payment()` to Reduce Complexity

- Reduce cyclomatic complexity.
- Preserve existing validation behavior.
- Add focused tests for validation rules.

## Out of Scope

- Apple Pay implementation.
- Persistence layer changes.
- Stripe SDK migration.
