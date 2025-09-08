"""
Position management for trading operations.
Tracks open positions and manages exit strategies.
"""

import time
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass


class ExitStrategy(Enum):
    """Exit strategies for positions."""
    TIME_BASED = "time_based"
    TP_SL = "tp_sl"  # Take Profit / Stop Loss
    EXTREME_FAST = "extreme_fast"


class PositionStatus(Enum):
    """Position status states."""
    OPEN = "open"
    MONITORING = "monitoring"
    SELLING = "selling"
    CLOSED = "closed"
    FAILED = "failed"


@dataclass
class TokenInfo:
    """Information about a token."""
    mint: str
    name: str
    symbol: str
    uri: str
    market_cap: float
    created_timestamp: int
    bonding_curve: str
    metadata: str


@dataclass
class TradeResult:
    """Result of a trade operation."""
    success: bool
    signature: Optional[str]
    error: Optional[str]
    amount: Optional[float]
    price: Optional[float]
    timestamp: int


class Position:
    """Represents an open trading position."""
    
    def __init__(
        self,
        token_info: TokenInfo,
        buy_amount_sol: float,
        exit_strategy: ExitStrategy,
        strategy_params: Dict[str, Any]
    ):
        """
        Initialize a new position.
        
        Args:
            token_info: Information about the token
            buy_amount_sol: Amount to buy in SOL
            exit_strategy: Exit strategy to use
            strategy_params: Parameters for the exit strategy
        """
        self.token_info = token_info
        self.buy_amount_sol = buy_amount_sol
        self.exit_strategy = exit_strategy
        self.strategy_params = strategy_params
        
        # Position state
        self.status = PositionStatus.OPEN
        self.created_at = int(time.time() * 1000)  # milliseconds
        self.updated_at = self.created_at
        
        # Trade results
        self.buy_result: Optional[TradeResult] = None
        self.sell_result: Optional[TradeResult] = None
        
        # Position tracking
        self.token_balance: float = 0.0
        self.entry_price: Optional[float] = None
        self.current_price: Optional[float] = None
        self.unrealized_pnl: float = 0.0
        
        # Exit strategy specific
        self._exit_signal_time: Optional[int] = None
    
    def update_buy_result(self, result: TradeResult):
        """Update position with buy result."""
        self.buy_result = result
        self.updated_at = int(time.time() * 1000)
        
        if result.success:
            self.status = PositionStatus.MONITORING
            self.entry_price = result.price
            self.token_balance = result.amount or 0.0
            self._setup_exit_strategy()
        else:
            self.status = PositionStatus.FAILED
    
    def update_sell_result(self, result: TradeResult):
        """Update position with sell result."""
        self.sell_result = result
        self.updated_at = int(time.time() * 1000)
        
        if result.success:
            self.status = PositionStatus.CLOSED
        else:
            self.status = PositionStatus.FAILED
    
    def update_price(self, current_price: float):
        """Update current token price and calculate PnL."""
        self.current_price = current_price
        self.updated_at = int(time.time() * 1000)
        
        if self.entry_price and self.token_balance > 0:
            # Calculate unrealized PnL
            current_value = self.token_balance * current_price
            entry_value = self.buy_amount_sol
            self.unrealized_pnl = current_value - entry_value
    
    def _setup_exit_strategy(self):
        """Setup exit strategy based on configuration."""
        if self.exit_strategy == ExitStrategy.TIME_BASED:
            max_hold_time = self.strategy_params.get('max_hold_time_ms', 300_000)  # 5 min
            self._exit_signal_time = self.created_at + max_hold_time
            
        elif self.exit_strategy == ExitStrategy.EXTREME_FAST:
            wait_after_buy = self.strategy_params.get('wait_after_buy_ms', 5_000)  # 5 sec
            self._exit_signal_time = self.created_at + wait_after_buy
    
    def should_exit(self) -> tuple[bool, str]:
        """
        Check if position should be exited.
        
        Returns:
            (should_exit, reason)
        """
        current_time = int(time.time() * 1000)
        
        if self.status != PositionStatus.MONITORING:
            return False, "position_not_monitoring"
        
        # Time-based exit
        if (self.exit_strategy == ExitStrategy.TIME_BASED or 
            self.exit_strategy == ExitStrategy.EXTREME_FAST):
            if self._exit_signal_time and current_time >= self._exit_signal_time:
                return True, f"{self.exit_strategy.value}_timeout"
        
        # TP/SL exit
        elif self.exit_strategy == ExitStrategy.TP_SL:
            if not self.current_price or not self.entry_price:
                return False, "no_price_data"
            
            take_profit = self.strategy_params.get('take_profit_percentage', 0.5)  # 50%
            stop_loss = self.strategy_params.get('stop_loss_percentage', -0.2)  # -20%
            
            profit_percentage = (self.current_price - self.entry_price) / self.entry_price
            
            if profit_percentage >= take_profit:
                return True, "take_profit_hit"
            elif profit_percentage <= stop_loss:
                return True, "stop_loss_hit"
        
        return False, "no_exit_signal"
    
    def get_position_info(self) -> Dict[str, Any]:
        """Get complete position information."""
        return {
            'token': {
                'mint': self.token_info.mint,
                'symbol': self.token_info.symbol,
                'name': self.token_info.name,
                'market_cap': self.token_info.market_cap
            },
            'trade': {
                'buy_amount_sol': self.buy_amount_sol,
                'token_balance': self.token_balance,
                'entry_price': self.entry_price,
                'current_price': self.current_price,
                'unrealized_pnl': self.unrealized_pnl
            },
            'status': {
                'current': self.status.value,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'age_ms': int(time.time() * 1000) - self.created_at
            },
            'strategy': {
                'type': self.exit_strategy.value,
                'params': self.strategy_params,
                'exit_signal_time': self._exit_signal_time
            },
            'results': {
                'buy_success': self.buy_result.success if self.buy_result else None,
                'sell_success': self.sell_result.success if self.sell_result else None,
                'buy_signature': self.buy_result.signature if self.buy_result else None,
                'sell_signature': self.sell_result.signature if self.sell_result else None
            }
        }
    
    def get_profit_percentage(self) -> Optional[float]:
        """Calculate profit percentage."""
        if not self.entry_price or not self.current_price:
            return None
        
        return (self.current_price - self.entry_price) / self.entry_price
    
    def get_age_seconds(self) -> float:
        """Get position age in seconds."""
        current_time = int(time.time() * 1000)
        return (current_time - self.created_at) / 1000


class PositionManager:
    """Manages multiple trading positions."""
    
    def __init__(self):
        """Initialize position manager."""
        self.positions: Dict[str, Position] = {}  # mint -> Position
        self.closed_positions: Dict[str, Position] = {}
    
    def add_position(self, position: Position) -> str:
        """
        Add new position to tracking.
        
        Args:
            position: Position to track
            
        Returns:
            Position ID (mint address)
        """
        mint = position.token_info.mint
        self.positions[mint] = position
        return mint
    
    def get_position(self, mint: str) -> Optional[Position]:
        """Get position by mint address."""
        return self.positions.get(mint)
    
    def close_position(self, mint: str):
        """Move position to closed positions."""
        if mint in self.positions:
            position = self.positions.pop(mint)
            self.closed_positions[mint] = position
    
    def get_active_positions(self) -> Dict[str, Position]:
        """Get all active positions."""
        return self.positions.copy()
    
    def get_positions_to_exit(self) -> list[tuple[str, Position, str]]:
        """
        Get positions that should be exited.
        
        Returns:
            List of (mint, position, reason) tuples
        """
        to_exit = []
        
        for mint, position in self.positions.items():
            should_exit, reason = position.should_exit()
            if should_exit:
                to_exit.append((mint, position, reason))
        
        return to_exit
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all positions."""
        active_count = len(self.positions)
        closed_count = len(self.closed_positions)
        
        total_unrealized_pnl = sum(
            pos.unrealized_pnl for pos in self.positions.values()
        )
        
        return {
            'active_positions': active_count,
            'closed_positions': closed_count,
            'total_unrealized_pnl': total_unrealized_pnl,
            'oldest_position_age': max(
                (pos.get_age_seconds() for pos in self.positions.values()),
                default=0
            )
        }


# Example usage
def main():
    """Example usage of Position and PositionManager."""
    print("📊 Position Management Example")
    print("=" * 40)
    
    # Create sample token info
    token_info = TokenInfo(
        mint="BMp9rLwaJwFyaLiaDzwrQAG9qX8z4tVnvvT21Ct8pump",
        name="Test Token",
        symbol="TEST",
        uri="https://example.com/metadata.json",
        market_cap=50000.0,
        created_timestamp=int(time.time() * 1000),
        bonding_curve="BondingCurveAddress",
        metadata="MetadataAddress"
    )
    
    # Create position with TP/SL strategy
    position = Position(
        token_info=token_info,
        buy_amount_sol=0.1,
        exit_strategy=ExitStrategy.TP_SL,
        strategy_params={
            'take_profit_percentage': 0.5,  # 50% profit
            'stop_loss_percentage': -0.2    # -20% loss
        }
    )
    
    # Simulate buy result
    buy_result = TradeResult(
        success=True,
        signature="BuySignature123",
        error=None,
        amount=1000000.0,  # tokens received
        price=0.0001,      # SOL per token
        timestamp=int(time.time() * 1000)
    )
    
    position.update_buy_result(buy_result)
    
    # Test position manager
    manager = PositionManager()
    mint = manager.add_position(position)
    
    print(f"✅ Position created for {token_info.symbol}")
    print(f"   Mint: {mint}")
    print(f"   Status: {position.status.value}")
    print(f"   Entry price: {position.entry_price}")
    
    # Simulate price update
    position.update_price(0.00015)  # 50% profit
    should_exit, reason = position.should_exit()
    
    print(f"\n📈 Price updated to 0.00015")
    print(f"   Profit: {position.get_profit_percentage():.1%}")
    print(f"   Should exit: {should_exit} ({reason})")
    
    # Manager summary
    summary = manager.get_summary()
    print(f"\n📊 Manager Summary:")
    for key, value in summary.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    main()
