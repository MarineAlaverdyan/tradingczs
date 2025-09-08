"""
Priority Fee Manager for Solana transactions.
Handles both dynamic and fixed priority fee calculations.
"""

import asyncio
from typing import Optional, Dict, Any
from enum import Enum


class FeeStrategy(Enum):
    """Priority fee calculation strategies."""
    DYNAMIC = "dynamic"
    FIXED = "fixed"


class PriorityFeeManager:
    """Manages priority fees for Solana transactions."""
    
    def __init__(
        self,
        strategy: FeeStrategy = FeeStrategy.DYNAMIC,
        fixed_fee: int = 100_000,  # 0.0001 SOL in lamports
        extra_percentage: float = 0.1,  # 10% extra
        hard_cap: int = 1_000_000,  # 0.001 SOL max
        client=None
    ):
        """
        Initialize priority fee manager.
        
        Args:
            strategy: Fee calculation strategy (dynamic/fixed)
            fixed_fee: Fixed fee amount in lamports
            extra_percentage: Extra percentage for dynamic fees (0.1 = 10%)
            hard_cap: Maximum fee in lamports
            client: Solana RPC client for dynamic fee calculation
        """
        self.strategy = strategy
        self.fixed_fee = fixed_fee
        self.extra_percentage = extra_percentage
        self.hard_cap = hard_cap
        self.client = client
        
        # Cache for recent fees (for dynamic calculation)
        self._recent_fees_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0
        self._cache_duration: int = 30  # seconds
    
    async def calculate_priority_fee(self) -> int:
        """
        Calculate priority fee based on current strategy.
        
        Returns:
            Priority fee in lamports
        """
        if self.strategy == FeeStrategy.FIXED:
            return self._calculate_fixed_fee()
        else:
            return await self._calculate_dynamic_fee()
    
    def _calculate_fixed_fee(self) -> int:
        """
        Calculate fixed priority fee.
        
        Returns:
            Fixed fee amount in lamports
        """
        return min(self.fixed_fee, self.hard_cap)
    
    async def _calculate_dynamic_fee(self) -> int:
        """
        Calculate dynamic priority fee based on recent network activity.
        
        Returns:
            Dynamic fee in lamports
        """
        if not self.client:
            # Fallback to fixed fee if no client available
            return self._calculate_fixed_fee()
        
        try:
            # Get recent priority fees from network
            recent_fees = await self._get_recent_priority_fees()
            
            if not recent_fees:
                return self._calculate_fixed_fee()
            
            # Calculate 75th percentile of recent fees
            percentile_75 = self._calculate_percentile(recent_fees, 75)
            
            # Add extra percentage
            dynamic_fee = int(percentile_75 * (1 + self.extra_percentage))
            
            # Apply hard cap
            return min(dynamic_fee, self.hard_cap)
            
        except Exception as e:
            print(f"Error calculating dynamic fee: {e}")
            return self._calculate_fixed_fee()
    
    async def _get_recent_priority_fees(self) -> list:
        """
        Get recent priority fees from the network.
        
        Returns:
            List of recent priority fees
        """
        import time
        current_time = time.time()
        
        # Check cache validity
        if (self._recent_fees_cache and 
            current_time - self._cache_timestamp < self._cache_duration):
            return self._recent_fees_cache.get('fees', [])
        
        try:
            # Get recent priority fees (this would be an RPC call)
            fees = await self._fetch_priority_fees_from_rpc()
            
            # Update cache
            self._recent_fees_cache = {'fees': fees}
            self._cache_timestamp = current_time
            
            return fees
            
        except Exception as e:
            print(f"Error fetching recent fees: {e}")
            return []
    
    async def _fetch_priority_fees_from_rpc(self) -> list:
        """
        Fetch priority fees from Solana RPC.
        This is a placeholder - would need actual RPC implementation.
        
        Returns:
            List of priority fees in lamports
        """
        # Simulate network call delay
        await asyncio.sleep(0.1)
        
        # Return simulated recent fees (in lamports)
        return [
            50_000, 75_000, 100_000, 125_000, 150_000,
            80_000, 90_000, 110_000, 130_000, 200_000,
            60_000, 85_000, 95_000, 140_000, 180_000
        ]
    
    def _calculate_percentile(self, values: list, percentile: int) -> float:
        """
        Calculate percentile of a list of values.
        
        Args:
            values: List of numeric values
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Percentile value
        """
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return float(sorted_values[int(index)])
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def set_strategy(self, strategy: FeeStrategy):
        """Change fee calculation strategy."""
        self.strategy = strategy
    
    def set_fixed_fee(self, fee: int):
        """Set fixed fee amount."""
        self.fixed_fee = min(fee, self.hard_cap)
    
    def set_extra_percentage(self, percentage: float):
        """Set extra percentage for dynamic fees."""
        self.extra_percentage = percentage
    
    def set_hard_cap(self, cap: int):
        """Set maximum fee limit."""
        self.hard_cap = cap
    
    def get_fee_info(self) -> Dict[str, Any]:
        """Get current fee manager configuration."""
        return {
            'strategy': self.strategy.value,
            'fixed_fee': self.fixed_fee,
            'extra_percentage': self.extra_percentage,
            'hard_cap': self.hard_cap
        }
    
    async def create_priority_fee_instruction(self):
        """
        Создать инструкцию priority fee для транзакции.
        
        Returns:
            Инструкция priority fee или None если не удалось создать
        """
        try:
            from solders.instruction import Instruction
            from solders.pubkey import Pubkey
            
            # Получаем размер комиссии
            fee_amount = await self.calculate_priority_fee()
            
            # Создаем инструкцию setPriorityFee
            # Program ID для Compute Budget Program
            compute_budget_program = Pubkey.from_string("ComputeBudget111111111111111111111111111111")
            
            # Данные для инструкции setPriorityFee (instruction discriminator + fee)
            instruction_data = bytes([3]) + fee_amount.to_bytes(8, 'little')
            
            return Instruction(
                program_id=compute_budget_program,
                accounts=[],
                data=instruction_data
            )
        except Exception as e:
            print(f"Ошибка создания priority fee инструкции: {e}")
            return None


# Example usage
async def main():
    """Example usage of PriorityFeeManager."""
    print("🔧 Priority Fee Manager Example")
    print("=" * 40)
    
    # Test fixed fee strategy
    print("\n📊 Fixed Fee Strategy:")
    fixed_manager = PriorityFeeManager(
        strategy=FeeStrategy.FIXED,
        fixed_fee=150_000
    )
    
    fixed_fee = await fixed_manager.calculate_priority_fee()
    print(f"   Fixed fee: {fixed_fee:,} lamports ({fixed_fee/1_000_000_000:.6f} SOL)")
    
    # Test dynamic fee strategy
    print("\n📈 Dynamic Fee Strategy:")
    dynamic_manager = PriorityFeeManager(
        strategy=FeeStrategy.DYNAMIC,
        extra_percentage=0.15,
        hard_cap=500_000
    )
    
    dynamic_fee = await dynamic_manager.calculate_priority_fee()
    print(f"   Dynamic fee: {dynamic_fee:,} lamports ({dynamic_fee/1_000_000_000:.6f} SOL)")
    
    print("\n⚙️  Configuration:")
    config = dynamic_manager.get_fee_info()
    for key, value in config.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
