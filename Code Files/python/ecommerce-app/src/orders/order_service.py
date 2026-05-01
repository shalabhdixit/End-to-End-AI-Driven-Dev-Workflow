"""Order service module for the e-commerce payment demo."""

import uuid
from datetime import datetime
from typing import Dict, Optional


class OrderStatus:
    PENDING = "pending"
    PAYMENT_PROCESSING = "payment_processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Order:
    def __init__(self, order_id: str, customer_id: str, amount: float, currency: str = "usd"):
        self.order_id = order_id
        self.customer_id = customer_id
        self.amount = amount
        self.currency = currency
        self.status = OrderStatus.PENDING
        self.created_at = datetime.utcnow()
        self.payment_id = None

    def to_dict(self) -> Dict:
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "payment_id": self.payment_id,
        }


class OrderService:
    def __init__(self):
        self.orders = {}

    def create_order(self, customer_id: str, amount: float, currency: str = "usd") -> Order:
        order_id = str(uuid.uuid4())
        order = Order(order_id, customer_id, amount, currency)
        self.orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        return self.orders.get(order_id)

    def update_order_status(self, order_id: str, status: str, payment_id: Optional[str] = None) -> bool:
        order = self.orders.get(order_id)
        if not order:
            return False
        order.status = status
        if payment_id:
            order.payment_id = payment_id
        return True

    def cancel_order(self, order_id: str) -> bool:
        return self.update_order_status(order_id, OrderStatus.CANCELLED)


default_order_service = OrderService()
