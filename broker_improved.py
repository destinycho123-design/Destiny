import threading
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from typing import Dict, Optional

# Set precise but reasonable Decimal precision for money operations
# 10 = 8 integer digits + 2 fractional (sufficient for $99,999,999.99)
getcontext().prec = 10

class Account:
    def __init__(self):
        self._lock = threading.RLock()
        self._positions: Dict[str, 'Position'] = {}
        self.cash: Decimal = Decimal("0.00")

    def get_or_create_position(self, symbol: str) -> 'Position':
        with self._lock:
            return self._positions.setdefault(symbol, Position())

    def get_position(self, symbol: str) -> Optional['Position']:
        with self._lock:
            return self._positions.get(symbol)

    def increase_position(self, symbol: str, quantity: Decimal) -> None:
        """Atomically increase position by quantity."""
        with self._lock:
            pos = self._positions.setdefault(symbol, Position())
            pos.quantity += quantity.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def decrease_position(self, symbol: str, quantity: Decimal) -> None:
        """Atomically decrease position by quantity. Raises ValueError if insufficient."""
        with self._lock:
            pos = self._positions.get(symbol)
            if pos is None or pos.quantity < quantity:
                raise ValueError("Insufficient position")
            pos.quantity -= quantity.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def debit_cash(self, amount: Decimal) -> None:
        """Atomically debit cash. Raises ValueError if insufficient funds."""
        with self._lock:
            if self.cash < amount:
                raise ValueError("Insufficient funds")
            self.cash -= amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def credit_cash(self, amount: Decimal) -> None:
        """Atomically credit cash."""
        with self._lock:
            self.cash += amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class Position:
    def __init__(self):
        self.quantity: Decimal = Decimal("0.00")

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
    def price_lookup(self, symbol: str) -> Decimal:
        """Returns the current price for a symbol."""
        raise NotImplementedError

    def place_order(self, acct: Account, order: Order) -> Order:
        """
        Place an order atomically. Returns the order with status set.
        
        All account state changes happen within a single critical section
        to ensure consistency and prevent race conditions.
        """
        symbol = order.symbol
        side = order.side

        # Step 1: Validate and normalize quantity (outside lock for better concurrency)
        try:
            if order.quantity is None:
                raise ValueError("Quantity cannot be None")
            quantity = Decimal(str(order.quantity))
        except (InvalidOperation, TypeError, ValueError) as e:
            order.status = OrderStatus.REJECTED
            order.reject_reason = f"Invalid quantity: {e}"
            return order

        if quantity <= 0:
            order.status = OrderStatus.REJECTED
            order.reject_reason = "Quantity must be > 0"
            return order

        # Step 2: Look up price (outside lock to minimize critical section)
        try:
            raw_price = self.price_lookup(symbol)
            price = Decimal(str(raw_price))
        except Exception as e:
            order.status = OrderStatus.REJECTED
            order.reject_reason = f"Price lookup failed: {e}"
            return order

        # Validate price
        if not price.is_finite() or price <= Decimal("0"):
            order.status = OrderStatus.REJECTED
            order.reject_reason = f"Invalid price from price_lookup: {price}"
            return order

        # Quantize price to cents
        price = price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        order.price = price

        # Step 3: Execute order atomically within single lock
        with acct._lock:
            try:
                if side == Side.BUY:
                    cost = (price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    
                    # Check funds first
                    if acct.cash < cost:
                        raise ValueError("Insufficient funds")
                    
                    # Perform both operations atomically
                    pos = acct._positions.setdefault(symbol, Position())
                    pos.quantity += quantity.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    acct.cash -= cost
                    
                    order.status = OrderStatus.FILLED
                    return order

                elif side == Side.SELL:
                    # Check position
                    pos = acct._positions.get(symbol)
                    if pos is None or pos.quantity < quantity:
                        raise ValueError("Insufficient position")
                    
                    # Perform both operations atomically
                    pos.quantity -= quantity.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    proceeds = (price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    acct.cash += proceeds
                    
                    order.status = OrderStatus.FILLED
                    return order

                else:
                    order.status = OrderStatus.REJECTED
                    order.reject_reason = f"Unsupported side: {side}"
                    return order

            except ValueError as e:
                order.status = OrderStatus.REJECTED
                order.reject_reason = str(e)
                return order
