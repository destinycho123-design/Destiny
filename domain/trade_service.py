"""Trade domain service - orchestrates broker operations with portfolio state management."""

from decimal import Decimal
from typing import Optional, Tuple

from broker_improved import Broker, Account, Order, OrderStatus, Side
from domain.portfolio import Portfolio


class TradeService:
    """
    Domain service that coordinates trading between the Portfolio (domain) 
    and the Broker (infrastructure).
    
    Responsibilities:
    - Accept trade requests from application layer
    - Coordinate with broker to execute orders
    - Update portfolio state based on order results
    - Maintain consistency between broker and portfolio
    """
    
    def __init__(self, broker: Broker):
        """
        Initialize trade service with a broker implementation.
        
        Args:
            broker: Broker instance (implements price_lookup and place_order)
        """
        self.broker = broker
    
    def execute_buy_order(
        self, 
        portfolio: Portfolio, 
        broker_account: Account, 
        symbol: str, 
        quantity: Decimal
    ) -> Tuple[bool, Optional[str]]:
        """
        Execute a buy order, updating both broker account and portfolio.
        
        Args:
            portfolio: Portfolio domain entity to update
            broker_account: Broker's Account (infrastructure state)
            symbol: Stock symbol
            quantity: Quantity to buy
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Create order
            order = Order(symbol=symbol, side=Side.BUY, quantity=quantity)
            
            # Execute order via broker (handles price lookup, validation, atomicity)
            order = self.broker.place_order(broker_account, order)
            
            if order.status == OrderStatus.FILLED:
                # Update portfolio state
                cost = (order.price * quantity).quantize(Decimal("0.01"))
                portfolio.update_cash_on_buy(cost)
                portfolio.record_order_placed(symbol, Side.BUY, quantity, order.price)
                return True, None
            else:
                # Order rejected
                portfolio.record_order_rejected(symbol, Side.BUY, quantity, order.reject_reason)
                return False, order.reject_reason
                
        except Exception as e:
            portfolio.record_order_rejected(symbol, Side.BUY, quantity, str(e))
            return False, str(e)
    
    def execute_sell_order(
        self, 
        portfolio: Portfolio, 
        broker_account: Account, 
        symbol: str, 
        quantity: Decimal
    ) -> Tuple[bool, Optional[str]]:
        """
        Execute a sell order, updating both broker account and portfolio.
        
        Args:
            portfolio: Portfolio domain entity to update
            broker_account: Broker's Account (infrastructure state)
            symbol: Stock symbol
            quantity: Quantity to sell
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Create order
            order = Order(symbol=symbol, side=Side.SELL, quantity=quantity)
            
            # Execute order via broker
            order = self.broker.place_order(broker_account, order)
            
            if order.status == OrderStatus.FILLED:
                # Update portfolio state
                proceeds = (order.price * quantity).quantize(Decimal("0.01"))
                portfolio.update_cash_on_sell(proceeds)
                portfolio.record_order_placed(symbol, Side.SELL, quantity, order.price)
                return True, None
            else:
                # Order rejected
                portfolio.record_order_rejected(symbol, Side.SELL, quantity, order.reject_reason)
                return False, order.reject_reason
                
        except Exception as e:
            portfolio.record_order_rejected(symbol, Side.SELL, quantity, str(e))
            return False, str(e)
    
    def get_portfolio_snapshot(self, portfolio: Portfolio) -> dict:
        """
        Get a snapshot of the portfolio's current state.
        
        Returns:
            Dictionary with portfolio details including positions and value
        """
        value_info = portfolio.get_portfolio_value()
        positions = {
            symbol: {
                "quantity": str(pos.quantity),
                "avg_price": str(pos.avg_price)
            }
            for symbol, pos in portfolio.positions.items()
        }
        
        return {
            "portfolio_id": portfolio.portfolio_id,
            "cash": str(value_info["cash"]),
            "positions": positions,
            "positions_value": str(value_info["positions_value"]),
            "total_value": str(value_info["total_value"])
        }
    
    def get_portfolio_events(self, portfolio: Portfolio) -> list:
        """
        Get all domain events recorded for the portfolio.
        Useful for audit trail and event sourcing.
        
        Returns:
            List of domain events
        """
        events = portfolio.get_events()
        return [
            {
                "type": event.__class__.__name__,
                "timestamp": event.timestamp.isoformat(),
                "details": self._event_to_dict(event)
            }
            for event in events
        ]
    
    @staticmethod
    def _event_to_dict(event) -> dict:
        """Convert domain event to dictionary."""
        return {k: str(v) if isinstance(v, Decimal) else v 
                for k, v in event.__dict__.items() 
                if not k.startswith('_')}
