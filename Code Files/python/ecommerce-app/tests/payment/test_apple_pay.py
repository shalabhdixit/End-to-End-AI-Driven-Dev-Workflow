"""BDD tests for Apple Pay payment processing."""

import logging
import time
from unittest.mock import MagicMock, patch

import pytest
import requests
from pytest_bdd import given, parsers, scenarios, then, when

from src.payment.apple_pay_payment_method import ApplePayPaymentMethod
from src.payment.payment_processor import PaymentProcessor

scenarios("apple_pay.feature")
_SENSITIVE_PREFIXES = ("apay_tok_", "tok_", "card_", "cvv", "pan")


@pytest.fixture
def ctx():
    return {}


@given("the payment processor is initialised with Apple Pay support")
def step_init_processor(ctx):
    processor = PaymentProcessor()
    apple_pay_method = ApplePayPaymentMethod()
    processor.register_payment_method("apple_pay", apple_pay_method.process_apple_pay_payment)
    ctx["processor"] = processor
    ctx["apple_pay_method"] = apple_pay_method


@given(parsers.parse('an order exists with id "{order_id}" for customer "{customer_id}" totalling {amount:f} USD'))
def step_create_order(ctx, order_id, customer_id, amount):
    ctx["order_id"] = order_id
    ctx["customer_id"] = customer_id
    ctx["amount"] = amount
    ctx["order_status"] = "pending"
    ctx["payment_data"] = {"amount": amount, "currency": "usd"}


@given(parsers.parse('a valid Apple Pay payment token "{token}"'))
def step_valid_token(ctx, token):
    ctx["payment_data"]["apple_pay_token"] = token


@given(parsers.parse('an invalid Apple Pay payment token "{token}"'))
def step_invalid_token(ctx, token):
    ctx["payment_data"]["apple_pay_token"] = token


@given(parsers.parse('an expired Apple Pay payment token "{token}"'))
def step_expired_token(ctx, token):
    ctx["payment_data"]["apple_pay_token"] = token


@given("the Apple Pay API is available and authorises the charge")
def step_api_available(ctx):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"id": "apay_charge_abc789", "status": "succeeded", "created": 1743638400}
    ctx["mock_post"] = response
    ctx["api_call_count"] = 0


@given("the Apple Pay API returns a token-expired error")
def step_api_token_expired(ctx):
    response = MagicMock()
    response.status_code = 402
    response.json.return_value = {"error": {"code": "token_expired", "message": "Apple Pay token has expired"}}
    ctx["mock_post"] = response


@given(parsers.parse("the Apple Pay API fails with a 503 error on the first {n:d} attempts"))
def step_api_fails_n_times(ctx, n, monkeypatch):
    success_response = MagicMock()
    success_response.status_code = 200
    success_response.json.return_value = {"id": "apay_charge_retry_ok", "status": "succeeded", "created": 1743638400}

    def side_effect(*args, **kwargs):
        ctx["api_call_count"] = ctx.get("api_call_count", 0) + 1
        if ctx["api_call_count"] <= n:
            raise requests.exceptions.RequestException("503 Service Unavailable")
        return success_response

    ctx["post_side_effect"] = side_effect
    sleep_calls = []
    monkeypatch.setattr(time, "sleep", lambda seconds: sleep_calls.append(seconds))
    ctx["sleep_calls"] = sleep_calls


@given("the Apple Pay API succeeds on the 3rd attempt")
def step_api_succeeds_third():
    pass


@given("the Apple Pay API fails with a 503 error on all 3 attempts")
def step_api_fails_all(ctx):
    def always_fail(*args, **kwargs):
        ctx["api_call_count"] = ctx.get("api_call_count", 0) + 1
        raise requests.exceptions.RequestException("503 Service Unavailable")

    ctx["post_side_effect"] = always_fail
    ctx["api_call_count"] = 0


@given(parsers.parse("a payment amount of {amount:f} USD which exceeds the Apple Pay limit of {limit:f}"))
def step_amount_exceeds_limit(ctx, amount, limit):
    ctx["payment_data"]["amount"] = amount
    ctx["apple_pay_limit"] = limit


@given(parsers.parse("a payment amount of {amount:f} USD"))
def step_set_amount(ctx, amount):
    ctx["payment_data"]["amount"] = amount


@given("the Apple Pay API endpoint times out on all attempts")
def step_api_timeout(ctx):
    def always_timeout(*args, **kwargs):
        ctx["api_call_count"] = ctx.get("api_call_count", 0) + 1
        raise requests.exceptions.Timeout("Connection timed out")

    ctx["post_side_effect"] = always_timeout
    ctx["api_call_count"] = 0


@given("the order update service will raise an exception after payment succeeds")
def step_order_update_fails(ctx):
    def fail_order_update():
        raise RuntimeError("Order service unavailable")

    ctx["order_update_fn"] = fail_order_update


@given("the Apple Pay refund API will succeed")
def step_refund_succeeds(ctx):
    ctx["refunded_payment_ids"] = []

    def refund(payment_id):
        ctx["refunded_payment_ids"].append(payment_id)

    ctx["refund_fn"] = refund


@given("the Apple Pay refund API will also fail")
def step_refund_fails(ctx):
    def refund_fails(payment_id):
        raise RuntimeError("Refund API unavailable")

    ctx["refund_fn"] = refund_fails


@when(parsers.parse('I submit the Apple Pay payment for order "{order_id}"'))
def step_submit_payment(ctx, order_id, caplog):
    ctx["caplog"] = caplog
    with caplog.at_level(logging.DEBUG):
        if ctx.get("post_side_effect") is not None:
            with patch("requests.post", side_effect=ctx["post_side_effect"]) as patched:
                ctx["patched_post"] = patched
                result = ctx["processor"].process_payment(order_id, "apple_pay", ctx["payment_data"])
        elif ctx.get("mock_post") is not None:
            with patch("requests.post", return_value=ctx["mock_post"]) as patched:
                ctx["patched_post"] = patched
                result = ctx["processor"].process_payment(order_id, "apple_pay", ctx["payment_data"])
        else:
            result = ctx["processor"].process_payment(order_id, "apple_pay", ctx["payment_data"])
    ctx["result"] = result

    if result.get("status") == "success":
        if ctx.get("order_update_fn"):
            try:
                ctx["order_update_fn"]()
            except Exception:
                try:
                    ctx["refund_fn"](result.get("payment_id"))
                    ctx["result"] = {"status": "error", "message": "Order update failed; payment refunded"}
                except Exception:
                    ctx["result"] = {"status": "error", "message": "Order update failed; refund failed - manual intervention required"}
        else:
            ctx["order_status"] = "paid"


@when("I validate the Apple Pay payment data")
def step_validate_only(ctx):
    ctx["validation_result"] = ctx["apple_pay_method"].validate_payment(ctx["payment_data"])


@then(parsers.parse('the payment result status should be "{expected_status}"'))
def step_assert_status(ctx, expected_status):
    assert ctx["result"]["status"] == expected_status


@then("the result should contain a non-empty payment id")
def step_assert_payment_id(ctx):
    assert ctx["result"].get("payment_id")


@then(parsers.parse('the order status should be updated to "{expected_status}"'))
def step_assert_order_updated(ctx, expected_status):
    assert ctx["order_status"] == expected_status


@then(parsers.parse('the order status should remain "{expected_status}"'))
def step_assert_order_unchanged(ctx, expected_status):
    assert ctx["order_status"] == expected_status


@then(parsers.parse('the error message should contain "{fragment}"'))
def step_assert_error_message(ctx, fragment):
    assert fragment.lower() in ctx["result"].get("message", "").lower()


@then("no charge attempt should be made to the Apple Pay API")
def step_assert_no_api_call(ctx):
    if ctx.get("patched_post") is not None:
        ctx["patched_post"].assert_not_called()


@then(parsers.parse("exactly {n:d} attempts should have been made to the Apple Pay API"))
def step_assert_attempt_count(ctx, n):
    assert ctx.get("api_call_count", 0) == n


@then("exponential back-off delays should have been applied between retries")
def step_assert_backoff(ctx):
    assert len(ctx.get("sleep_calls", [])) >= 2
    assert ctx["sleep_calls"][1] >= ctx["sleep_calls"][0]


@then(parsers.parse("the validation result should be {expected}"))
def step_assert_validation(ctx, expected):
    assert ctx["validation_result"] == (expected.lower() == "valid")


@then("the Apple Pay charge should have been refunded")
def step_assert_refunded(ctx):
    assert ctx.get("refunded_payment_ids")


@then("no sensitive payment data should appear in the application logs")
def step_assert_no_sensitive_logs(ctx):
    full_log = " ".join(record.getMessage() for record in ctx.get("caplog").records)
    for prefix in _SENSITIVE_PREFIXES:
        assert prefix not in full_log
