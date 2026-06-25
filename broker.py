import threading
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from typing import Dict, Optional

# set a reasonable Decimal precision for money operations
getcontext().prec = 28

class Account:
    def __init__(self):
        # Use an RLock so re-entrant calls from the same thread are safe.
        self._lock = threading.RLock()
        self._positions: Dict[str, 'Position'] = {}
        self.cash: Decimal = Decimal("0.00")

    # safe helpers to encapsulate locking + business logic
    def get_or_create_position(self, symbol: str) -> 'Position':
        with self._lock:
            return self._positions.setdefault(symbol, Position())

    def get_position(self, symbol: str) -> Optional['Position']:
        with self._lock:
            return self._positions.get(symbol)

    def increase_position(self, symbol: str, quantity: Decimal) -> None:
        with self._lock:
            pos = self._positions.setdefault(symbol, Position())
            pos.quantity += quantity

    def decrease_position(self, symbol: str, quantity: Decimal) -> None:
        with self._lock:
            pos = self._positions.get(symbol)
            if pos is None or pos.quantity < quantity:
                raise ValueError("Insufficient position")
            pos.quantity -= quantity

    def debit_cash(self, amount: Decimal) -> None:
        with self._lock:
            if self.cash < amount:
                raise ValueError("Insufficient funds")
            self.cash -= amount

    def credit_cash(self, amount: Decimal) -> None:
        with self._lock:
            self.cash += amount

# Minimal Position placeholder for type completeness
class Position:
    def __init__(self):
        self.quantity: Decimal = Decimal("0")

# Enums / dataclasses placeholders (adjust to your real definitions)
class Side:
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus:
    REJECTED = "REJECTED"
    FILLED = "FILLED"

class Order:
    def __init__(self, symbol: str, side: str, quantity):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.price = None
        self.status = None
        self.reject_reason = None

class Broker:
    # price_lookup should return a numeric or Decimal-like value; keep as-is
    def price_lookup(self, symbol: str):
        # placeholder; use your implementation
        raise NotImplementedError

    def place_order(self, acct: Account, order: Order) -> Order:
        symbol = order.symbol
        side = order.side

        # validate quantity
        try:
            quantity = Decimal(str(order.quantity))
        except (InvalidOperation, TypeError) as e:
            order.status = OrderStatus.REJECTED
            order.reject_reason = f"Invalid quantity: {e}"
            return order

        if quantity <= 0:
            order.status = OrderStatus.REJECTED
            order.reject_reason = "Quantity must be > 0"
            return order

        # Price lookup with robust validation using Decimal
        try:
            raw_price = self.price_lookup(symbol)
            price = Decimal(str(raw_price))
        except Exception as e:
            order.status = OrderStatus.REJECTED
            order.reject_reason = f"Price lookup failed: {e}"
            return order

        # validate price with Decimal
        if not price.is_finite() or price <= Decimal("0"):
            order.status = OrderStatus.REJECTED
            order.reject_reason = f"Invalid price from price_lookup: {price}"
            return order

        # set order.price using Decimal (optionally quantize to cents)
        order.price = price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Atomic operation: hold single lock for entire order execution
        with acct._lock:
            try:
                if side == Side.BUY:
                    cost = (order.price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    # Check funds and debit atomically
                    if acct.cash < cost:
                        raise ValueError("Insufficient funds")
                    # Increase position first, then debit cash
                    pos = acct._positions.setdefault(symbol, Position())
                    pos.quantity += quantity
                    acct.cash -= cost
                    order.status = OrderStatus.FILLED
                    return order

                elif side == Side.SELL:
                    # Ensure position exists and has enough quantity
                    pos = acct._positions.get(symbol)
                    if pos is None or pos.quantity < quantity:
                        raise ValueError("Insufficient position")
                    # Debit position and credit cash atomically
                    pos.quantity -= quantity
                    proceeds = (order.price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    acct.cash += proceeds
                    order.status = OrderStatus.FILLED
                    return order

                else:
                    order.status = OrderStatus.REJECTED
                    order.reject_reason = "Unsupported side"
                    return order

            except ValueError as e:
                # translate account-level errors into order rejections
                order.status = OrderStatus.REJECTED
                order.reject_reason = str(e)
                return order
