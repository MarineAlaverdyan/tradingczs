"""
Построитель инструкций для pump.fun транзакций.
Создает Solana инструкции для покупки и продажи токенов.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.system_program import ID as SYSTEM_PROGRAM_ID

try:
    from ..core.pubkeys import PUMP_PROGRAM_ID, TOKEN_PROGRAM_ID
except ImportError:
    from core.pubkeys import PUMP_PROGRAM_ID, TOKEN_PROGRAM_ID
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")

# Настройка логирования
logger = logging.getLogger(__name__)

@dataclass
class PumpFunConstants:
    """Константы для pump.fun программы"""
    PROGRAM_ID = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
    GLOBAL_ACCOUNT = Pubkey.from_string("4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf")
    FEE_RECIPIENT = Pubkey.from_string("CebN5WGQ4jvEPvsVU4EoHEpgzq1VV7AbicfhtW4xC9iM")
    EVENT_AUTHORITY = Pubkey.from_string("Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1")
    RENT_SYSVAR = Pubkey.from_string("SysvarRent111111111111111111111111111111111")
    
    # Discriminators для инструкций
    BUY_DISCRIMINATOR = bytes([102, 6, 61, 18, 1, 218, 235, 234])
    SELL_DISCRIMINATOR = bytes([51, 230, 133, 164, 1, 127, 131, 173])


class InstructionBuilder:
    """
    Построитель инструкций для pump.fun транзакций.
    """
    
    def __init__(self):
        self.constants = PumpFunConstants()
        logger.info("InstructionBuilder инициализирован")
    
    def build_buy_instruction(
        self,
        buyer_wallet: Pubkey,
        mint_address: Pubkey,
        bonding_curve: Pubkey,
        associated_bonding_curve: Pubkey,
        associated_user: Pubkey,
        sol_amount: int,
        max_sol_cost: int
    ) -> Instruction:
        """
        Создает инструкцию покупки токенов через pump.fun.
        
        Args:
            buyer_wallet: Публичный ключ покупателя
            mint_address: Адрес mint токена
            bonding_curve: Адрес bonding curve
            associated_bonding_curve: ATA bonding curve
            associated_user: ATA пользователя
            sol_amount: Количество SOL для покупки (в lamports)
            max_sol_cost: Максимальная стоимость с учетом slippage
            
        Returns:
            Solana инструкция для покупки
        """
        logger.info(f"Создание buy инструкции: mint={mint_address}, sol_amount={sol_amount}")
        
        # Данные инструкции: discriminator + sol_amount + max_sol_cost
        instruction_data = (
            self.constants.BUY_DISCRIMINATOR +
            sol_amount.to_bytes(8, 'little') +
            max_sol_cost.to_bytes(8, 'little')
        )
        
        # Аккаунты для инструкции согласно IDL (16 аккаунтов с fee_config PDA)
        # Исправленная структура аккаунтов без fee_config
        accounts = [
            AccountMeta(pubkey=self.constants.GLOBAL_ACCOUNT, is_signer=False, is_writable=False),
            AccountMeta(pubkey=self.constants.FEE_RECIPIENT, is_signer=False, is_writable=True),
            AccountMeta(pubkey=mint_address, is_signer=False, is_writable=False),
            AccountMeta(pubkey=bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(pubkey=associated_bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(pubkey=associated_user, is_signer=False, is_writable=True),
            AccountMeta(pubkey=buyer_wallet, is_signer=True, is_writable=True),  # user
            AccountMeta(pubkey=SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=self.constants.RENT_SYSVAR, is_signer=False, is_writable=False),
            AccountMeta(pubkey=self.constants.EVENT_AUTHORITY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=self.constants.PROGRAM_ID, is_signer=False, is_writable=False),
        ]
        
        instruction = Instruction(
            program_id=self.constants.PROGRAM_ID,
            accounts=accounts,
            data=instruction_data
        )
        
        logger.debug(f"Buy инструкция создана с {len(accounts)} аккаунтами")
        return instruction
    
    def build_sell_instruction(
        self,
        seller_wallet: Pubkey,
        mint_address: Pubkey,
        bonding_curve: Pubkey,
        associated_bonding_curve: Pubkey,
        associated_user: Pubkey,
        token_amount: int,
        min_sol_output: int
    ) -> Instruction:
        """
        Создает инструкцию продажи токенов через pump.fun.
        
        Args:
            seller_wallet: Публичный ключ продавца
            mint_address: Адрес mint токена
            bonding_curve: Адрес bonding curve
            associated_bonding_curve: ATA bonding curve
            associated_user: ATA пользователя
            token_amount: Количество токенов для продажи
            min_sol_output: Минимальное количество SOL с учетом slippage
            
        Returns:
            Solana инструкция для продажи
        """
        logger.info(f"Создание sell инструкции: mint={mint_address}, token_amount={token_amount}")
        
        # Данные инструкции: discriminator + token_amount + min_sol_output
        instruction_data = (
            self.constants.SELL_DISCRIMINATOR +
            token_amount.to_bytes(8, 'little') +
            min_sol_output.to_bytes(8, 'little')
        )
        
        # Аккаунты для инструкции (аналогично покупке)
        accounts = [
            AccountMeta(pubkey=self.constants.GLOBAL_ACCOUNT, is_signer=False, is_writable=False),
            AccountMeta(pubkey=self.constants.FEE_RECIPIENT, is_signer=False, is_writable=True),
            AccountMeta(pubkey=mint_address, is_signer=False, is_writable=False),
            AccountMeta(pubkey=bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(pubkey=associated_bonding_curve, is_signer=False, is_writable=True),
            AccountMeta(pubkey=associated_user, is_signer=False, is_writable=True),
            AccountMeta(pubkey=seller_wallet, is_signer=True, is_writable=True),
            AccountMeta(pubkey=SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=self.constants.RENT_SYSVAR, is_signer=False, is_writable=False),
            AccountMeta(pubkey=self.constants.EVENT_AUTHORITY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=self.constants.PROGRAM_ID, is_signer=False, is_writable=False),
        ]
        
        instruction = Instruction(
            program_id=self.constants.PROGRAM_ID,
            accounts=accounts,
            data=instruction_data
        )
        
        logger.debug(f"Sell инструкция создана с {len(accounts)} аккаунтами")
        return instruction
    
    def calculate_slippage_amounts(self, base_amount: int, slippage_percent: float) -> tuple[int, int]:
        """
        Рассчитывает минимальные/максимальные суммы с учетом slippage.
        
        Args:
            base_amount: Базовая сумма
            slippage_percent: Процент slippage (например, 5.0 для 5%)
            
        Returns:
            Tuple (min_amount, max_amount)
        """
        slippage_multiplier = slippage_percent / 100.0
        min_amount = int(base_amount * (1.0 - slippage_multiplier))
        max_amount = int(base_amount * (1.0 + slippage_multiplier))
        
        logger.debug(f"Slippage расчет: base={base_amount}, slippage={slippage_percent}%, min={min_amount}, max={max_amount}")
        return min_amount, max_amount
    
    def build_create_ata_instruction(
        self,
        payer: Pubkey,
        owner: Pubkey,
        mint: Pubkey,
        ata_address: Pubkey
    ) -> Instruction:
        """
        Создает инструкцию для создания Associated Token Account.
        
        Args:
            payer: Кто платит за создание аккаунта
            owner: Владелец токен аккаунта
            mint: Mint адрес токена
            ata_address: Адрес ATA для создания
            
        Returns:
            Solana инструкция для создания ATA
        """
        logger.info(f"Создание ATA инструкции: owner={owner}, mint={mint}")
        
        accounts = [
            AccountMeta(pubkey=payer, is_signer=True, is_writable=True),
            AccountMeta(pubkey=ata_address, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=False, is_writable=False),
            AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        ]
        
        instruction = Instruction(
            program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
            accounts=accounts,
            data=b''  # CreateAssociatedTokenAccount не требует данных
        )
        
        logger.debug(f"ATA инструкция создана для {ata_address}")
        return instruction


# Пример использования
if __name__ == "__main__":
    import asyncio
    
    # Настройка логирования для примера
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def example_usage():
        """Пример использования InstructionBuilder"""
        print("🔧 ПРИМЕР ИСПОЛЬЗОВАНИЯ INSTRUCTION BUILDER")
        print("=" * 50)
        
        builder = InstructionBuilder()
        
        # Тестовые адреса (devnet)
        buyer_wallet = Pubkey.from_string("11111111111111111111111111111111")
        mint_address = Pubkey.from_string("So11111111111111111111111111111111111111112")
        bonding_curve = Pubkey.from_string("11111111111111111111111111111111")
        associated_bonding_curve = Pubkey.from_string("11111111111111111111111111111111")
        associated_user = Pubkey.from_string("11111111111111111111111111111111")
        
        # Создание buy инструкции
        sol_amount = 1000000  # 0.001 SOL
        min_amount, max_amount = builder.calculate_slippage_amounts(sol_amount, 5.0)
        
        buy_ix = builder.build_buy_instruction(
            buyer_wallet=buyer_wallet,
            mint_address=mint_address,
            bonding_curve=bonding_curve,
            associated_bonding_curve=associated_bonding_curve,
            associated_user=associated_user,
            sol_amount=sol_amount,
            max_sol_cost=max_amount
        )
        
        print(f"✅ Buy инструкция создана:")
        print(f"   Program ID: {buy_ix.program_id}")
        print(f"   Accounts: {len(buy_ix.accounts)}")
        print(f"   Data length: {len(buy_ix.data)} bytes")
        
        # Создание sell инструкции
        token_amount = 1000000  # 1M токенов
        min_sol, _ = builder.calculate_slippage_amounts(sol_amount, 5.0)
        
        sell_ix = builder.build_sell_instruction(
            seller_wallet=buyer_wallet,
            mint_address=mint_address,
            bonding_curve=bonding_curve,
            associated_bonding_curve=associated_bonding_curve,
            associated_user=associated_user,
            token_amount=token_amount,
            min_sol_output=min_sol
        )
        
        print(f"✅ Sell инструкция создана:")
        print(f"   Program ID: {sell_ix.program_id}")
        print(f"   Accounts: {len(sell_ix.accounts)}")
        print(f"   Data length: {len(sell_ix.data)} bytes")
        
        print("\n🎯 InstructionBuilder готов к использованию!")
    
    # Запуск примера
    asyncio.run(example_usage())
