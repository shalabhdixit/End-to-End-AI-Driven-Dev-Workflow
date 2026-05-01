"""Apple Pay payment method implementation for the demo workflow."""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import requests

from .payment_processor import AbstractPaymentMethod

logger = logging.getLogger(__name__)

_TOKEN_PREFIX = "apay_tok_"
_TOKEN_MIN_LENGTH = 20
_MAX_AMOUNT = 10_000.00
_VALID_CURRENCIES = frozenset({"usd", "eur", "gbp", "cad", "aud"})
_MAX_RETRIES = 3
_BASE_DELAY_SECONDS = 1.0
_DEFAULT_API_URL = "https://api.example.com/v1/payments/apple-pay"
_REQUEST_TIMEOUT_SECONDS = 10


class ApplePayPaymentMethod(AbstractPaymentMethod):
    """Apple Pay strategy implementation with validation, retry, and refund support."""

    def __init__(self) -> None:
        self._api_key = os.getenv("APPLE_PAY_API_KEY", "")
        self._api_url = os.getenv("APPLE_PAY_API_URL", _DEFAULT_API_URL)
        self._max_retries = _MAX_RETRIES
        self._base_delay = _BASE_DELAY_SECONDS
        if self._api_key:
            self._validate_api_url(self._api_url)
        else:
            logger.warning("APPLE_PAY_API_KEY is not set. Apple Pay payments will fail at runtime.")

    def process_payment(self, order_id: str, payment_data: dict) -> dict:
        return self.process_apple_pay_payment(order_id, payment_data)

    def validate_token(self, token: str) -> bool:
        return isinstance(token, str) and token.startswith(_TOKEN_PREFIX) and len(token) >= _TOKEN_MIN_LENGTH

    def refund_payment(self, payment_id: str) -> dict:
        if not payment_id:
            return {"status": "error", "message": "payment_id is required for refund"}
        response = requests.post(
            f"{self._api_url}/{payment_id}/refund",
            headers=self._build_request_headers(),
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code == 200:
            logger.info("Refund issued successfully for payment_id=%s", payment_id)
            return {"status": "success", "payment_id": payment_id}
        return {"status": "error", "message": _extract_api_error(response)}

    def process_apple_pay_payment(self, order_id: str, payment_data: dict) -> dict:
        validation_error = self._validate_payment_data(payment_data)
        if validation_error:
            logger.warning("Apple Pay validation failed for order_id=%s: %s", order_id, validation_error)
            return {"status": "error", "message": validation_error}
        return self._execute_with_retry(order_id, payment_data)

    def validate_payment(self, payment_data: dict) -> bool:
        return self._validate_payment_data(payment_data) is None

    def _validate_payment_data(self, payment_data: dict) -> Optional[str]:
        if not payment_data:
            return "Invalid Apple Pay token: payment data is missing"
        token_error = self._validate_token_field(payment_data.get("apple_pay_token"))
        if token_error:
            return token_error
        amount_error = self._validate_amount_field(payment_data.get("amount"))
        if amount_error:
            return amount_error
        currency_error = self._validate_currency_field(payment_data.get("currency", "usd"))
        if currency_error:
            return currency_error
        return None

    def _validate_token_field(self, token: object) -> Optional[str]:
        if not self.validate_token(token):  # type: ignore[arg-type]
            return f"Invalid Apple Pay token: must start with '{_TOKEN_PREFIX}' and be at least {_TOKEN_MIN_LENGTH} characters"
        return None

    def _validate_amount_field(self, amount: object) -> Optional[str]:
        if amount is None or not isinstance(amount, (int, float)):
            return "Invalid payment data: amount is required and must be numeric"
        if amount <= 0:
            return "Invalid payment data: amount must be greater than zero"
        if amount > _MAX_AMOUNT:
            return f"Payment amount {amount} exceeds Apple Pay transaction limit of {_MAX_AMOUNT}"
        return None

    def _validate_currency_field(self, currency: object) -> Optional[str]:
        if not isinstance(currency, str) or currency.lower() not in _VALID_CURRENCIES:
            return f"Invalid payment data: unsupported currency '{currency}'"
        return None

    def _execute_with_retry(self, order_id: str, payment_data: dict) -> dict:
        last_exception: Optional[Exception] = None
        for attempt in range(self._max_retries):
            try:
                result = self._call_apple_pay_api(order_id, payment_data)
                if result.get("status") == "success":
                    logger.info("Apple Pay payment succeeded: order_id=%s payment_id=%s", order_id, result.get("payment_id"))
                    return result
                return result
            except requests.exceptions.Timeout as exc:
                last_exception = exc
                delay = self._base_delay * (2 ** attempt)
                logger.warning("Apple Pay API timeout on attempt %d/%d for order_id=%s, retrying in %.1fs", attempt + 1, self._max_retries, order_id, delay)
                time.sleep(delay)
            except requests.exceptions.RequestException as exc:
                last_exception = exc
                delay = self._base_delay * (2 ** attempt)
                logger.warning("Apple Pay API error on attempt %d/%d for order_id=%s (%s), retrying in %.1fs", attempt + 1, self._max_retries, order_id, type(exc).__name__, delay)
                time.sleep(delay)
        if isinstance(last_exception, requests.exceptions.Timeout):
            return {"status": "error", "message": "Payment processing failed: connection timeout after retries"}
        return {"status": "error", "message": "Payment processing failed after retries"}

    def _call_apple_pay_api(self, order_id: str, payment_data: dict) -> dict:
        response = requests.post(
            self._api_url,
            json={
                "order_id": order_id,
                "apple_pay_token": payment_data["apple_pay_token"],
                "amount": payment_data["amount"],
                "currency": payment_data.get("currency", "usd"),
            },
            headers=self._build_request_headers(idempotency_key=f"order-{order_id}"),
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code == 200:
            payload = response.json()
            return {"status": "success", "payment_id": payload["id"], "timestamp": payload["created"]}
        return {"status": "error", "message": _extract_api_error(response)}

    def _build_request_headers(self, *, idempotency_key: Optional[str] = None) -> dict:
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    @staticmethod
    def _validate_api_url(url: str) -> None:
        if not url.startswith("https://"):
            raise ValueError(f"APPLE_PAY_API_URL must use HTTPS to protect credentials in transit. Got: '{url}'")


def _extract_api_error(response: requests.Response) -> str:
    try:
        return response.json().get("error", {}).get("message", "Unknown error")
    except ValueError:
        return f"Unknown error (HTTP {response.status_code})"
