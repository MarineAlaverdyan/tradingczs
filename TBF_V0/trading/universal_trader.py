"""
Universal Trader - Main trading coordinator for TBF_V0.
Orchestrates token discovery, buying, monitoring, and selling.
"""

import asyncio
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from ..core import SimpleClient, SimpleWallet, PriorityFeeManager, FeeStrategy, pubkeys
from ..pumpfun import AddressProvider, CurveManager, EventParser
from ..monitoring import SimpleBlockListener
from .position import Position, PositionManager, TokenInfo, TradeResult, ExitStrategy


@dataclass
class TradingConfig:
    """Trading configuration."""
    buy_amount_sol: float = 0.01
    exit_strategy: ExitStrategy = ExitStrategy.TP_SL
    max_positions: int = 5
    strategy_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.strategy_params is None:
            self.strategy_params = {
                'take_profit_percentage': 0.5,  # 50%
                'stop_loss_percentage': -0.2,   # -20%
                'max_hold_time_ms': 300_000     # 5 minutes
            }


class UniversalTrader:
    """Main trading coordinator for pump.fun tokens."""
    
    def __init__(
        self,
        rpc_endpoint: str,
        private_key: str,
        config: TradingConfig,
        websocket_url: str = "wss://api.mainnet-beta.solana.com"
    ):
        """
        Initialize universal trader.
        
        Args:
            rpc_endpoint: Solana RPC endpoint
            private_key: Wallet private key
            config: Trading configuration
            websocket_url: WebSocket URL for block listening
        """
        self.config = config
        
        # Core components
        self.client = SimpleClient(rpc_endpoint)
        self.wallet = SimpleWallet(private_key)
        self.fee_manager = PriorityFeeManager(
            strategy=FeeStrategy.DYNAMIC,
            client=self.client
        )
        
        # Platform components
        self.address_provider = AddressProvider()
        self.curve_manager = CurveManager()
        self.event_parser = EventParser()
        
        # Trading components
        self.position_manager = PositionManager()
        
        # Monitoring
        self.block_listener = SimpleBlockListener(websocket_url)
        
        # State
        self.is_running = False
        self._monitoring_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the trading bot."""
        print("🚀 Starting Universal Trader...")
        
        # Connect to Solana
        connected = await self.client.connect()
        if not connected:
            raise Exception("Failed to connect to Solana RPC")
        
        print(f"✅ Connected to Solana")
        print(f"💰 Wallet: {self.wallet.get_address_string()}")
        
        # Check wallet balance
        balance = await self.client.get_balance(self.wallet.get_address_string())
        print(f"💰 Balance: {balance:.4f} SOL")
        
        if balance < 0.01:
            print("⚠️  Warning: Low SOL balance for trading")
        
        # Start monitoring
        self.is_running = True
        
        # Start block listener with callback
        await self.block_listener.start_listening(
            callback=self._handle_new_token
        )
        
        # Start position monitoring
        self._monitoring_task = asyncio.create_task(self._monitor_positions())
        
        print("🎯 Trading bot started - monitoring for new tokens...")
    
    async def stop(self):
        """Stop the trading bot."""
        print("🛑 Stopping Universal Trader...")
        
        self.is_running = False
        
        # Stop monitoring task
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Stop block listener
        await self.block_listener.stop_listening()
        
        # Close client connection
        await self.client.close()
        
        print("✅ Trading bot stopped")
    
    async def _handle_new_token(self, token_data: Dict[str, Any]):
        """
        Handle new token discovery.
        
        Args:
            token_data: Raw token data from listener
        """
        try:
            # Parse token information
            token_info = self._parse_token_info(token_data)
            
            if not token_info:
                return
            
            print(f"🆕 New token discovered: {token_info.symbol} ({token_info.name})")
            print(f"   Market cap: ${token_info.market_cap:,.2f}")
            
            # Check if we should trade this token
            if not self._should_trade_token(token_info):
                print(f"⏭️  Skipping {token_info.symbol} - doesn't meet criteria")
                return
            
            # Check position limits
            if len(self.position_manager.get_active_positions()) >= self.config.max_positions:
                print(f"⏭️  Skipping {token_info.symbol} - max positions reached")
                return
            
            # Create position
            position = Position(
                token_info=token_info,
                buy_amount_sol=self.config.buy_amount_sol,
                exit_strategy=self.config.exit_strategy,
                strategy_params=self.config.strategy_params
            )
            
            # Add to position manager
            self.position_manager.add_position(position)
            
            # Execute buy
            await self._execute_buy(position)
            
        except Exception as e:
            print(f"❌ Error handling new token: {e}")
    
    def _parse_token_info(self, token_data: Dict[str, Any]) -> Optional[TokenInfo]:
        """Parse raw token data into TokenInfo object."""
        try:
            # Use event parser to extract token information
            parsed = self.event_parser.parse_create_event(token_data)
            
            if not parsed:
                return None
            
            return TokenInfo(
                mint=parsed.get('mint', ''),
                name=parsed.get('name', ''),
                symbol=parsed.get('symbol', ''),
                uri=parsed.get('uri', ''),
                market_cap=0.0,  # Will be calculated
                created_timestamp=int(time.time() * 1000),
                bonding_curve=parsed.get('bonding_curve', ''),
                metadata=parsed.get('metadata', '')
            )
            
        except Exception as e:
            print(f"Error parsing token info: {e}")
            return None
    
    def _should_trade_token(self, token_info: TokenInfo) -> bool:
        """
        Determine if we should trade this token.
        
        Args:
            token_info: Token information
            
        Returns:
            True if we should trade
        """
        # Basic validation
        if not token_info.mint or not token_info.symbol:
            return False
        
        # Add your trading criteria here
        # For example:
        # - Market cap limits
        # - Symbol filters
        # - Name filters
        # - etc.
        
        return True
    
    async def _execute_buy(self, position: Position):
        """
        Execute buy transaction for position.
        
        Args:
            position: Position to buy
        """
        try:
            print(f"💰 Executing buy for {position.token_info.symbol}...")
            
            # Get all required addresses
            addresses = self.address_provider.get_all_addresses(
                position.token_info.mint,
                self.wallet.get_address_string()
            )
            
            # Calculate priority fee
            priority_fee = await self.fee_manager.calculate_priority_fee()
            
            # Build buy instruction (simplified - would need actual implementation)
            # This is where you'd use instruction builder
            
            # For now, simulate buy result
            await asyncio.sleep(1)  # Simulate transaction time
            
            # Simulate successful buy
            buy_result = TradeResult(
                success=True,
                signature=f"BuyTx_{int(time.time())}",
                error=None,
                amount=position.buy_amount_sol / 0.0001,  # Simulate token amount
                price=0.0001,  # Simulate entry price
                timestamp=int(time.time() * 1000)
            )
            
            position.update_buy_result(buy_result)
            
            print(f"✅ Buy successful for {position.token_info.symbol}")
            print(f"   Signature: {buy_result.signature}")
            print(f"   Amount: {buy_result.amount:,.0f} tokens")
            
        except Exception as e:
            print(f"❌ Buy failed for {position.token_info.symbol}: {e}")
            
            # Update with failed result
            buy_result = TradeResult(
                success=False,
                signature=None,
                error=str(e),
                amount=None,
                price=None,
                timestamp=int(time.time() * 1000)
            )
            
            position.update_buy_result(buy_result)
    
    async def _execute_sell(self, position: Position, reason: str):
        """
        Execute sell transaction for position.
        
        Args:
            position: Position to sell
            reason: Reason for selling
        """
        try:
            print(f"💸 Executing sell for {position.token_info.symbol} (reason: {reason})...")
            
            # Simulate sell transaction
            await asyncio.sleep(1)
            
            # Calculate profit/loss
            if position.current_price and position.entry_price:
                profit_pct = (position.current_price - position.entry_price) / position.entry_price
                profit_sol = position.buy_amount_sol * profit_pct
            else:
                profit_sol = 0.0
            
            # Simulate sell result
            sell_result = TradeResult(
                success=True,
                signature=f"SellTx_{int(time.time())}",
                error=None,
                amount=position.buy_amount_sol + profit_sol,
                price=position.current_price,
                timestamp=int(time.time() * 1000)
            )
            
            position.update_sell_result(sell_result)
            
            print(f"✅ Sell successful for {position.token_info.symbol}")
            print(f"   Profit: {profit_sol:+.6f} SOL ({profit_pct:+.1%})")
            print(f"   Signature: {sell_result.signature}")
            
            # Move to closed positions
            self.position_manager.close_position(position.token_info.mint)
            
        except Exception as e:
            print(f"❌ Sell failed for {position.token_info.symbol}: {e}")
            
            sell_result = TradeResult(
                success=False,
                signature=None,
                error=str(e),
                amount=None,
                price=None,
                timestamp=int(time.time() * 1000)
            )
            
            position.update_sell_result(sell_result)
    
    async def _monitor_positions(self):
        """Monitor open positions and execute sells when needed."""
        while self.is_running:
            try:
                # Check positions that need to exit
                positions_to_exit = self.position_manager.get_positions_to_exit()
                
                for mint, position, reason in positions_to_exit:
                    await self._execute_sell(position, reason)
                
                # Update prices for TP/SL positions
                await self._update_position_prices()
                
                # Wait before next check
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"❌ Error in position monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _update_position_prices(self):
        """Update current prices for all positions."""
        active_positions = self.position_manager.get_active_positions()
        
        for mint, position in active_positions.items():
            if position.exit_strategy == ExitStrategy.TP_SL:
                try:
                    # Get current price from curve
                    # This would need actual implementation
                    # For now, simulate price movement
                    if position.entry_price:
                        # Simulate ±20% random price movement
                        import random
                        price_change = random.uniform(-0.2, 0.2)
                        new_price = position.entry_price * (1 + price_change)
                        position.update_price(new_price)
                        
                except Exception as e:
                    print(f"Error updating price for {position.token_info.symbol}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current trader status."""
        return {
            'is_running': self.is_running,
            'wallet_address': self.wallet.get_address_string(),
            'config': {
                'buy_amount_sol': self.config.buy_amount_sol,
                'exit_strategy': self.config.exit_strategy.value,
                'max_positions': self.config.max_positions
            },
            'positions': self.position_manager.get_summary(),
            'fee_strategy': self.fee_manager.get_fee_info()
        }


# Example usage
async def main():
    """Example usage of UniversalTrader."""
    print("🤖 Universal Trader Example")
    print("=" * 40)
    
    # Configuration
    config = TradingConfig(
        buy_amount_sol=0.01,
        exit_strategy=ExitStrategy.TIME_BASED,
        max_positions=3,
        strategy_params={'max_hold_time_ms': 60_000}  # 1 minute for demo
    )
    
    # Create trader (using devnet for safety)
    trader = UniversalTrader(
        rpc_endpoint="https://api.devnet.solana.com",
        private_key="your_private_key_here",  # Replace with actual key
        config=config,
        websocket_url="wss://api.devnet.solana.com"
    )
    
    try:
        # Start trading
        await trader.start()
        
        # Run for demo period
        await asyncio.sleep(30)  # Run for 30 seconds
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping trader...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await trader.stop()


if __name__ == "__main__":
    asyncio.run(main())
