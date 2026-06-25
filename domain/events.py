"""Domain events for portfolio and trading operations."""

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional


@dataclass
class DomainEvent:
    """Base class for all domain events."""
    timestamp: datetime
    aggregate_id: str  # Portfolio ID


@dataclass
class OrderPlacedEvent(DomainEvent):
    """Event raised when an order is successfully placed."""
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal


@dataclass
class OrderRejectedEvent(DomainEvent):
    """Event raised when an order is rejected."""
    symbol: str
    side: str
    quantity: Decimal
    reject_reason: str


@dataclass
class PositionOpenedEvent(DomainEvent):
    """Event raised when a new position is opened."""
    symbol: str
    quantity: Decimal
    avg_price: Decimal


@dataclass
class PositionClosedEvent(DomainEvent):
    """Event raised when a position is fully closed."""
    symbol: str
    quantity: Decimal
    proceeds: Decimal


@dataclass
class CashDepositedEvent(DomainEvent):
    """Event raised when cash is deposited into the portfolio."""
    amount: Decimal


@dataclass
class CashWithdrawnEvent(DomainEvent):
    """Event raised when cash is withdrawn from the portfolio."""
    amount: Decimal


@dataclass
class PortfolioCreatedEvent(DomainEvent):
    """Event raised when a new portfolio is created."""
    portfolio_id: str
    initial_cash: Decimal
