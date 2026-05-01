Feature: Apple Pay Payment Processing
  As an e-commerce customer
  I want to pay using Apple Pay
  So that I can complete purchases securely without entering card details manually

  Background:
    Given the payment processor is initialised with Apple Pay support
    And an order exists with id "ORD-2026-001" for customer "CUST-42" totalling 99.99 USD

  Scenario: Successful Apple Pay payment processing
    Given a valid Apple Pay payment token "apay_tok_valid_abc123xyz456"
    And the Apple Pay API is available and authorises the charge
    When I submit the Apple Pay payment for order "ORD-2026-001"
    Then the payment result status should be "success"
    And the result should contain a non-empty payment id
    And the order status should be updated to "paid"
    And no sensitive payment data should appear in the application logs

  Scenario: Payment rejected due to invalid Apple Pay token format
    Given an invalid Apple Pay payment token "bad_token_no_prefix"
    When I submit the Apple Pay payment for order "ORD-2026-001"
    Then the payment result status should be "error"
    And the error message should contain "Invalid Apple Pay token"
    And no charge attempt should be made to the Apple Pay API
    And the order status should remain "pending"

  Scenario: Payment rejected due to expired Apple Pay token
    Given an expired Apple Pay payment token "apay_tok_expired_zzz999"
    And the Apple Pay API returns a token-expired error
    When I submit the Apple Pay payment for order "ORD-2026-001"
    Then the payment result status should be "error"
    And the error message should contain "token"
    And the order status should remain "pending"

  Scenario: Apple Pay API recovers after transient failures
    Given a valid Apple Pay payment token "apay_tok_valid_abc123xyz456"
    And the Apple Pay API fails with a 503 error on the first 2 attempts
    And the Apple Pay API succeeds on the 3rd attempt
    When I submit the Apple Pay payment for order "ORD-2026-001"
    Then the payment result status should be "success"
    And exactly 3 attempts should have been made to the Apple Pay API
    And exponential back-off delays should have been applied between retries
    And the order status should be updated to "paid"

  Scenario: Apple Pay API unavailable after all retries exhausted
    Given a valid Apple Pay payment token "apay_tok_valid_abc123xyz456"
    And the Apple Pay API fails with a 503 error on all 3 attempts
    When I submit the Apple Pay payment for order "ORD-2026-001"
    Then the payment result status should be "error"
    And the error message should contain "Payment processing failed after retries"
    And exactly 3 attempts should have been made to the Apple Pay API
    And the order status should remain "pending"

  Scenario: Payment amount exceeds Apple Pay transaction limit
    Given a valid Apple Pay payment token "apay_tok_valid_abc123xyz456"
    And a payment amount of 15000.00 USD which exceeds the Apple Pay limit of 10000.00
    When I submit the Apple Pay payment for order "ORD-2026-001"
    Then the payment result status should be "error"
    And the error message should contain "exceeds Apple Pay transaction limit"
    And no charge attempt should be made to the Apple Pay API
    And the order status should remain "pending"

  Scenario Outline: Boundary amounts around Apple Pay transaction limit
    Given a valid Apple Pay payment token "apay_tok_valid_abc123xyz456"
    And a payment amount of <amount> USD
    When I validate the Apple Pay payment data
    Then the validation result should be <expected>

    Examples:
      | amount    | expected |
      | 9999.99   | valid    |
      | 10000.00  | valid    |
      | 10000.01  | invalid  |
      | 0.00      | invalid  |
      | -50.00    | invalid  |

  Scenario: Network timeout causes payment failure
    Given a valid Apple Pay payment token "apay_tok_valid_abc123xyz456"
    And the Apple Pay API endpoint times out on all attempts
    When I submit the Apple Pay payment for order "ORD-2026-001"
    Then the payment result status should be "error"
    And the error message should contain "timeout"
    And the order status should remain "pending"
    And no sensitive payment data should appear in the application logs

  Scenario: Successful charge is refunded when order update fails
    Given a valid Apple Pay payment token "apay_tok_valid_abc123xyz456"
    And the Apple Pay API is available and authorises the charge
    And the order update service will raise an exception after payment succeeds
    And the Apple Pay refund API will succeed
    When I submit the Apple Pay payment for order "ORD-2026-001"
    Then the payment result status should be "error"
    And the error message should contain "Order update failed; payment refunded"
    And the Apple Pay charge should have been refunded
    And the order status should remain "pending"
    And no sensitive payment data should appear in the application logs

  Scenario: Successful charge cannot be refunded when order update fails
    Given a valid Apple Pay payment token "apay_tok_valid_abc123xyz456"
    And the Apple Pay API is available and authorises the charge
    And the order update service will raise an exception after payment succeeds
    And the Apple Pay refund API will also fail
    When I submit the Apple Pay payment for order "ORD-2026-001"
    Then the payment result status should be "error"
    And the error message should contain "manual intervention required"
    And the order status should remain "pending"
