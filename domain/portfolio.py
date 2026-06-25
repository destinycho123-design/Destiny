"""Portfolio domain entity - represents a user's trading account and positions."""

import threading
from decimal import Decimal
from typing import Dict, Optional, List
from datetime import datetime

from domain.events import (
    OrderPlacedEvent, OrderRejectedEvent, PositionOpenedEvent, 
    PositionClosedEvent, CashDepositedEvent, CashWithdrawnEvent,
    PortfolioCreatedEvent, DomainEvent
)


class Portfolio:
    """
    Portfolio domain entity encapsulates trading account state and position management.
    
    This entity is responsible for:
    - Managing positions and cash balance
    - Recording domain events for audit trail and event sourcing
    - Enforcing business rules around positions and cash
    - Providing snapshots of portfolio state
    """
    
    def __init__(self, portfolio_id: str, initial_cash: Decimal = Decimal("0.00")):
        self.portfolio_id = portfolio_id
        self.initial_cash = initial_cash
        self.current_cash = initial_cash
        self.positions: Dict[str, PositionSnapshot] = {}
        self._events: List[DomainEvent] = []
        self._lock = threading.RLock()
        
        # Record portfolio creation event
        self._record_event(
            PortfolioCreatedEvent(
                timestamp=datetime.now(),
                aggregate_id=portfolio_id,
                portfolio_id=portfolio_id,
                initial_cash=initial_cash
            )
        )
    
    def get_position(self, symbol: str) -> Optional['PositionSnapshot']:
        """Get current position for a symbol."""
        with self._lock:
            return self.positions.get(symbol)
    
    def get_cash_balance(self) -> Decimal:
        """Get current cash balance."""
        with self._lock:
            return self.current_cash
    
    def get_portfolio_value(self) -> Dict[str, Decimal]:
        """Get portfolio value snapshot: total_cash, total_positions_value, total_value."""
        with self._lock:
            total_positions_value = sum(
                pos.quantity * pos.avg_price 
                for pos in self.positions.values()
            )
            return {
                "cash": self.current_cash,
                "positions_value": total_positions_value,
                "total_value": self.current_cash + total_positions_value
            }
    
    def record_order_placed(self, symbol: str, side: str, quantity: Decimal, price: Decimal) -> None:
        """Record a successfully executed order."""
        with self._lock:
            event = OrderPlacedEvent(
                timestamp=datetime.now(),
                aggregate_id=self.portfolio_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price
            )
            self._record_event(event)
            
            if side == "BUY":
                self._update_position_on_buy(symbol, quantity, price)
            elif side == "SELL":
                self._update_position_on_sell(symbol, quantity, price)
    
    def record_order_rejected(self, symbol: str, side: str, quantity: Decimal, reason: str) -> None:
        """Record a rejected order."""
        with self._lock:
            event = OrderRejectedEvent(
                timestamp=datetime.now(),
                aggregate_id=self.portfolio_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                reject_reason=reason
            )
            self._record_event(event)
    
    def update_cash_on_buy(self, cost: Decimal) -> None:
        """Debit cash for a buy order. Called when order is filled."""
        with self._lock:
            if self.current_cash < cost:
                raise ValueError("Insufficient cash in portfolio")
            self.current_cash -= cost
    
    def update_cash_on_sell(self, proceeds: Decimal) -> None:
        """Credit cash for a sell order. Called when order is filled."""
        with self._lock:
            self.current_cash += proceeds
            event = CashWithdrawnEvent(
                timestamp=datetime.now(),
                aggregate_id=self.portfolio_id,
                amount=proceeds  # Using proceeds as withdrawn (confusing naming, but matches event)
            )
            self._record_event(event)
    
    def deposit_cash(self, amount: Decimal) -> None:
        """Deposit cash into portfolio."""
        with self._lock:
            if amount <= 0:
                raise ValueError("Deposit amount must be positive")
            self.current_cash += amount
            event = CashDepositedEvent(
                timestamp=datetime.now(),
                aggregate_id=self.portfolio_id,
                amount=amount
            )
            self._record_event(event)
    
    def withdraw_cash(self, amount: Decimal) -> None:
        """Withdraw cash from portfolio."""
        with self._lock:
            if amount <= 0:
                raise ValueError("Withdrawal amount must be positive")
            if self.current_cash < amount:
                raise ValueError("Insufficient cash for withdrawal")
            self.current_cash -= amount
            event = CashWithdrawnEvent(
                timestamp=datetime.now(),
                aggregate_id=self.portfolio_id,
                amount=amount
            )
            self._record_event(event)
    
    def get_events(self) -> List[DomainEvent]:
        """Get all recorded domain events (for event sourcing/audit)."""
        with self._lock:
            return list(self._events)
    
    def clear_events(self) -> None:
        """Clear recorded events after they've been persisted."""
        with self._lock:
            self._events.clear()
    
    # Private methods
    
    def _update_position_on_buy(self, symbol: str, quantity: Decimal, price: Decimal) -> None:
        """Update position state after a buy order. Must be called within lock."""
        if symbol not in self.positions:
            self.positions[symbol] = PositionSnapshot(quantity=quantity, avg_price=price)
            event = PositionOpenedEvent(
                timestamp=datetime.now(),
                aggregate_id=self.portfolio_id,
                symbol=symbol,
                quantity=quantity,
                avg_price=price
            )
            self._record_event(event)
        else:
            pos = self.positions[symbol]
            # Update average price
            total_value = (pos.quantity * pos.avg_price) + (quantity * price)
            new_quantity = pos.quantity + quantity
            pos.avg_price = total_value / new_quantity
            pos.quantity = new_quantity
    
    def _update_position_on_sell(self, symbol: str, quantity: Decimal, price: Decimal) -> None:
        """Update position state after a sell order. Must be called within lock."""
        if symbol not in self.positions:
            raise ValueError(f"Cannot sell position that doesn't exist: {symbol}")
        
        pos = self.positions[symbol]
        if pos.quantity < quantity:
            raise ValueError(f"Cannot sell more than owned: {symbol}")
        
        pos.quantity -= quantity
        
        # If position fully closed, record event
        if pos.quantity == 0:
            del self.positions[symbol]
            event = PositionClosedEvent(
                timestamp=datetime.now(),
                aggregate_id=self.portfolio_id,
                symbol=symbol,
                quantity=quantity,
                proceeds=quantity * price
            )
            self._record_event(event)
    
    def _record_event(self, event: DomainEvent) -> None:
        """Record a domain event. Must be called within lock."""
        self._events.append(event)


class PositionSnapshot:
    """Snapshot of a position at a point in time."""
    
    def __init__(self, quantity: Decimal, avg_price: Decimal):
        self.quantity = quantity
        self.avg_price = avg_price
    
    def __repr__(self):
        return f"PositionSnapshot(quantity={self.quantity}, avg_price={self.avg_price})"
