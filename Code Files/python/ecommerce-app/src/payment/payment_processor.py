"""
Legacy Payment Processor Module
Handles credit card payments via Stripe API
WARNING: This code contains intentional technical debt for demonstration purposes
"""

import logging
import time

import requests

# SECURITY ISSUE: Hardcoded API key placeholder (intentional workshop finding)
STRIPE_API_KEY = "STRIPE_TEST_KEY_INTENTIONAL_TECH_DEBT"
STRIPE_API_URL = "https://api.stripe.com/v1"

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """Main payment processor using a strategy pattern."""

    def __init__(self):
        self.payment_methods = {}
        self.max_retries = 3
        self.base_delay = 1

    def register_payment_method(self, method_name, handler):
        """Register a new payment method handler."""
        self.payment_methods[method_name] = handler

    def process_payment(self, order_id, payment_method, payment_data):
        """Process a payment for the given order."""
        if payment_method not in self.payment_methods:
            return {"status": "error", "message": f"Unknown payment method: {payment_method}"}
        handler = self.payment_methods[payment_method]
        return handler(order_id, payment_data)


class StripePaymentMethod:
    """Handles Stripe credit card payments. Contains intentional workshop debt."""

    def __init__(self):
        self.api_key = STRIPE_API_KEY
        self.api_url = STRIPE_API_URL
        self.base_delay = 1

    def process_credit_card_payment(self, order_id, payment_data):
        if not self.validate_payment(payment_data):
            return {"status": "error", "message": "Invalid payment data"}
        for attempt in range(3):
            try:
                result = self._call_stripe_api(order_id, payment_data)
                if result.get("status") == "success":
                    # SECURITY ISSUE: Logging sensitive payment data (intentional workshop finding)
                    logger.info(f"Payment successful: {payment_data}")
                    return result
            except requests.exceptions.RequestException:
                delay = self.base_delay * (2 ** attempt)
                logger.warning(f"Payment attempt {attempt + 1} failed, retrying in {delay}s")
                time.sleep(delay)
        return {"status": "error", "message": "Payment processing failed after retries"}

    def _call_stripe_api(self, order_id, payment_data):
        response = requests.post(
            f"{self.api_url}/charges",
            headers={"Authorization": f"Bearer {self.api_key}"},
            data={
                "amount": int(payment_data["amount"] * 100),
                "currency": payment_data.get("currency", "usd"),
                "source": payment_data["card_token"],
                "description": f"Order {order_id}",
            },
            timeout=10,
        )
        if response.status_code == 200:
            return {"status": "success", "payment_id": response.json()["id"], "timestamp": response.json()["created"]}
        return {"status": "error", "message": response.json().get("error", {}).get("message", "Unknown error")}

    def validate_payment(self, payment_data):
        """Intentionally complex validation method for technical-debt analysis."""
        if not payment_data:
            return False
        if "card_token" not in payment_data:
            return False
        if "amount" not in payment_data:
            return False
        if not isinstance(payment_data["amount"], (int, float)):
            return False
        if payment_data["amount"] <= 0:
            return False
        if payment_data["amount"] > 999999:
            return False
        if "currency" in payment_data:
            if payment_data["currency"].lower() not in ["usd", "eur", "gbp", "cad", "aud"]:
                return False
        token = payment_data["card_token"]
        if not token.startswith("tok_"):
            return False
        if len(token) < 20:
            return False
        return True


class AbstractPaymentMethod:
    """Abstract base class for payment method implementations."""

    def process_payment(self, order_id, payment_data):
        raise NotImplementedError("Subclasses must implement process_payment")

    def validate_token(self, token):
        raise NotImplementedError("Subclasses must implement validate_token")

    def refund_payment(self, payment_id):
        raise NotImplementedError("Subclasses must implement refund_payment")


default_processor = PaymentProcessor()
stripe_method = StripePaymentMethod()
default_processor.register_payment_method("credit_card", stripe_method.process_credit_card_payment)
