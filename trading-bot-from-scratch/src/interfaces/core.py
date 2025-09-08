"""
Core interfaces and types for the trading bot.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from solders.pubkey import Pubkey
from solders.instruction import Instruction


class Platform(Enum):
    """Supported trading platforms."""
    PUMP_FUN = "pump_fun"
    LETS_BONK = "lets_bonk"


class ListenerType(Enum):
    """Types of event listeners."""
    LOGS = "logs"
    BLOCKS = "blocks"
    GEYSER = "geyser"
    PUMPPORTAL = "pumpportal"


class ExitStrategy(Enum):
    """Exit strategies for positions."""
    TIME_BASED = "time_based"
    TAKE_PROFIT_STOP_LOSS = "tp_sl"
    MANUAL = "manual"


@dataclass
class TokenInfo:
    """Information about a token."""
    mint: Pubkey
    name: str
    symbol: str
    creator: Pubkey
    bonding_curve: Optional[Pubkey] = None
    associated_bonding_curve: Optional[Pubkey] = None
    metadata_uri: Optional[str] = None
    created_at: Optional[float] = None


@dataclass
class TradeResult:
    """Result of a trade operation."""
    success: bool
    signature: Optional[str] = None
    error: Optional[str] = None
    amount_in: Optional[float] = None
    amount_out: Optional[float] = None
    slippage: Optional[float] = None


class TradingBotException(Exception):
    """Base exception for trading bot errors."""
    pass


class ConfigurationError(TradingBotException):
    """Configuration related errors."""
    pass


class PlatformError(TradingBotException):
    """Platform specific errors."""
    pass


class TransactionError(TradingBotException):
    """Transaction related errors."""
    pass


# Abstract interfaces

class AddressProvider(ABC):
    """Provides platform-specific addresses."""
    
    @abstractmethod
    def get_program_id(self) -> Pubkey:
        """Get the main program ID for the platform."""
        pass
    
    @abstractmethod
    def get_fee_recipient(self) -> Pubkey:
        """Get the fee recipient address."""
        pass
    
    @abstractmethod
    def get_global_account(self) -> Pubkey:
        """Get the global account address."""
        pass


class InstructionBuilder(ABC):
    """Builds platform-specific instructions."""
    
    @abstractmethod
    async def build_buy_instruction(
        self,
        token_info: TokenInfo,
        buyer: Pubkey,
        sol_amount: float,
        slippage: float
    ) -> List[Instruction]:
        """Build buy instruction for a token."""
        pass
    
    @abstractmethod
    async def build_sell_instruction(
        self,
        token_info: TokenInfo,
        seller: Pubkey,
        token_amount: int,
        slippage: float
    ) -> List[Instruction]:
        """Build sell instruction for a token."""
        pass


class EventParser(ABC):
    """Parses platform-specific events."""
    
    @abstractmethod
    def parse_token_creation_event(self, log_data: str) -> Optional[TokenInfo]:
        """Parse token creation event from log data."""
        pass
    
    @abstractmethod
    def parse_trade_event(self, log_data: str) -> Optional[Dict[str, Any]]:
        """Parse trade event from log data."""
        pass


class CurveManager(ABC):
    """Manages bonding curve operations."""
    
    @abstractmethod
    async def get_curve_state(self, bonding_curve: Pubkey) -> Dict[str, Any]:
        """Get current state of bonding curve."""
        pass
    
    @abstractmethod
    async def calculate_buy_price(
        self,
        bonding_curve: Pubkey,
        sol_amount: float
    ) -> float:
        """Calculate expected token amount for SOL input."""
        pass
    
    @abstractmethod
    async def calculate_sell_price(
        self,
        bonding_curve: Pubkey,
        token_amount: int
    ) -> float:
        """Calculate expected SOL amount for token input."""
        pass


class TokenListener(ABC):
    """Listens for new token events."""
    
    @abstractmethod
    async def start(self) -> None:
        """Start listening for events."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop listening for events."""
        pass
    
    @abstractmethod
    def on_token_created(self, token_info: TokenInfo) -> None:
        """Called when a new token is created."""
        pass
