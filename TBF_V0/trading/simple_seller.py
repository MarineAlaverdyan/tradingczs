"""
Простой продавец токенов для pump.fun.
Выполняет продажу токенов через bonding curve с логированием.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message

# Настройка логирования
logger = logging.getLogger(__name__)

@dataclass
class SellResult:
    """Результат операции продажи"""
    success: bool
    transaction_signature: Optional[str] = None
    sol_received: Optional[int] = None
    tokens_sold: Optional[int] = None
    error_message: Optional[str] = None
    gas_used: Optional[int] = None


class SimpleSeller:
    """
    Простой продавец токенов через pump.fun bonding curve.
    """
    
    def __init__(self, client, wallet, address_provider, instruction_builder, priority_fee_manager=None):
        """
        Инициализация продавца.
        
        Args:
            client: SimpleClient для взаимодействия с Solana
            wallet: SimpleWallet для подписания транзакций
            address_provider: AddressProvider для расчета адресов
            instruction_builder: InstructionBuilder для создания инструкций
            priority_fee_manager: PriorityFeeManager для комиссий (опционально)
        """
        self.client = client
        self.wallet = wallet
        self.address_provider = address_provider
        self.instruction_builder = instruction_builder
        self.priority_fee_manager = priority_fee_manager
        
        logger.info("SimpleSeller инициализирован")
    
    async def sell_token(
        self,
        token_info,
        token_amount: Optional[int] = None,
        percentage: Optional[float] = None,
        slippage_percent: float = 5.0,
        max_retries: int = 3
    ) -> SellResult:
        """
        Продает токены через pump.fun bonding curve.
        
        Args:
            token_info: TokenInfo объект с данными токена от слушателя
            token_amount: Точное количество токенов для продажи (опционально)
            percentage: Процент от баланса для продажи (опционально)
            slippage_percent: Процент slippage (по умолчанию 5%)
            max_retries: Максимальное количество попыток
            
        Returns:
            SellResult с результатом операции
        """
        logger.info(f"💰 Начинаем продажу токена {token_info.symbol} ({token_info.mint})")
        
        try:
            # Получение баланса токенов
            mint_pubkey = token_info.mint
            wallet_pubkey = self.wallet.get_public_key()
            
            current_balance = await self._get_token_balance(mint_pubkey, wallet_pubkey)
            if current_balance == 0:
                error_msg = "Нет токенов для продажи"
                logger.warning(error_msg)
                return SellResult(success=False, error_message=error_msg)
            
            # Определение количества токенов для продажи
            if token_amount is not None:
                tokens_to_sell = min(token_amount, current_balance)
                logger.info(f"📊 Продаем точное количество: {tokens_to_sell} токенов")
            elif percentage is not None:
                tokens_to_sell = int(current_balance * (percentage / 100.0))
                logger.info(f"📊 Продаем {percentage}% от баланса: {tokens_to_sell} токенов")
            else:
                tokens_to_sell = current_balance
                logger.info(f"📊 Продаем весь баланс: {tokens_to_sell} токенов")
            
            if tokens_to_sell <= 0:
                error_msg = "Количество токенов для продажи равно 0"
                logger.warning(error_msg)
                return SellResult(success=False, error_message=error_msg)
            
            # Используем готовые адреса от слушателя
            mint_pubkey = token_info.mint
            wallet_pubkey = self.wallet.get_public_key()
            bonding_curve = token_info.bonding_curve
            associated_bonding_curve = token_info.associated_bonding_curve
            
            # Только пользовательский ATA нужно рассчитать
            associated_user = await self.address_provider.get_associated_token_address(
                wallet_pubkey, mint_pubkey
            )
            
            logger.info(f"📊 Используем данные от слушателя для продажи")
            logger.info(f"   Bonding Curve: {bonding_curve}")
            logger.info(f"   Associated BC: {associated_bonding_curve}")
            
            # Оценка получаемого SOL
            estimated_sol = await self._estimate_sol_output(tokens_to_sell)
            min_sol_output, _ = self.instruction_builder.calculate_slippage_amounts(
                estimated_sol, slippage_percent
            )
            
            logger.info(f"💎 Ожидаемый SOL: {estimated_sol / 1_000_000_000:.6f}, минимум: {min_sol_output / 1_000_000_000:.6f}")
            
            # Создание инструкции продажи
            logger.debug("Создание sell инструкции")
            sell_instruction = self.instruction_builder.build_sell_instruction(
                seller_wallet=wallet_pubkey,
                mint_address=mint_pubkey,
                bonding_curve=bonding_curve,
                associated_bonding_curve=associated_bonding_curve,
                associated_user=associated_user,
                token_amount=tokens_to_sell,
                min_sol_output=min_sol_output
            )
            
            # Выполнение продажи с повторными попытками
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔄 Попытка продажи #{attempt + 1}/{max_retries}")
                    
                    result = await self._execute_sell_transaction(
                        sell_instruction, tokens_to_sell, min_sol_output
                    )
                    
                    if result.success:
                        logger.info(f"✅ Продажа успешна! Signature: {result.transaction_signature}")
                        return result
                    else:
                        logger.warning(f"❌ Попытка #{attempt + 1} неудачна: {result.error_message}")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)  # Пауза перед повтором
                            
                except Exception as e:
                    logger.error(f"❌ Ошибка в попытке #{attempt + 1}: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(1)
            
            # Все попытки неудачны
            error_msg = f"Не удалось продать токен после {max_retries} попыток"
            logger.error(error_msg)
            return SellResult(success=False, error_message=error_msg)
            
        except Exception as e:
            error_msg = f"Критическая ошибка при продаже: {str(e)}"
            logger.error(error_msg)
            return SellResult(success=False, error_message=error_msg)
    
    async def _execute_sell_transaction(
        self, 
        sell_instruction, 
        token_amount: int, 
        min_sol_output: int
    ) -> SellResult:
        """
        Выполняет транзакцию продажи.
        
        Args:
            sell_instruction: Инструкция продажи
            token_amount: Количество токенов для продажи
            min_sol_output: Минимальное количество SOL
            
        Returns:
            SellResult с результатом
        """
        try:
            # Получение последнего blockhash
            logger.debug("Получение blockhash")
            blockhash_response = await self.client.get_latest_blockhash()
            if not blockhash_response.get('success'):
                raise Exception("Не удалось получить blockhash")
            
            blockhash = blockhash_response['blockhash']
            
            # Создание списка инструкций
            instructions = []
            
            # Добавление priority fee если доступен менеджер
            if self.priority_fee_manager:
                try:
                    logger.debug("Добавление priority fee")
                    priority_fee_ix = await self.priority_fee_manager.create_priority_fee_instruction()
                    if priority_fee_ix:
                        instructions.append(priority_fee_ix)
                except Exception as e:
                    logger.warning(f"Не удалось добавить priority fee: {e}")
            
            # Добавление основной инструкции
            instructions.append(sell_instruction)
            
            # Создание транзакции
            logger.debug("Создание и подписание транзакции")
            message = Message.new_with_blockhash(
                instructions=instructions,
                payer=self.wallet.get_public_key(),
                blockhash=blockhash
            )
            
            transaction = Transaction.new_unsigned(message)
            signed_transaction = self.wallet.sign_transaction(transaction)
            
            # Отправка транзакции
            logger.debug("Отправка транзакции")
            send_response = await self.client.send_transaction(signed_transaction)
            
            if not send_response.get('success'):
                error_msg = send_response.get('error', 'Неизвестная ошибка при отправке')
                return SellResult(success=False, error_message=error_msg)
            
            signature = send_response['signature']
            logger.info(f"📤 Транзакция отправлена: {signature}")
            
            # Подтверждение транзакции
            logger.debug("Ожидание подтверждения транзакции")
            confirm_response = await self.client.confirm_transaction(signature)
            
            if confirm_response.get('success'):
                logger.info(f"✅ Транзакция подтверждена: {signature}")
                
                return SellResult(
                    success=True,
                    transaction_signature=signature,
                    tokens_sold=token_amount,
                    sol_received=min_sol_output  # Примерная оценка
                )
            else:
                error_msg = confirm_response.get('error', 'Транзакция не подтверждена')
                return SellResult(success=False, error_message=error_msg)
                
        except Exception as e:
            error_msg = f"Ошибка выполнения транзакции: {str(e)}"
            logger.error(error_msg)
            return SellResult(success=False, error_message=error_msg)
    
    async def _get_token_balance(self, mint_pubkey: Pubkey, wallet_pubkey: Pubkey) -> int:
        """
        Получает баланс токенов в кошельке.
        
        Args:
            mint_pubkey: Публичный ключ mint токена
            wallet_pubkey: Публичный ключ кошелька
            
        Returns:
            Баланс токенов
        """
        try:
            # Получение ATA адреса
            ata_address = await self.address_provider.get_associated_token_address(
                wallet_pubkey, mint_pubkey
            )
            
            # Запрос баланса через клиент
            balance_response = await self.client.get_token_account_balance(str(ata_address))
            
            if balance_response.get('success'):
                balance = balance_response.get('balance', 0)
                logger.debug(f"Баланс токенов: {balance}")
                return balance
            else:
                logger.warning("Не удалось получить баланс токенов, возвращаем 0")
                return 0
                
        except Exception as e:
            logger.error(f"Ошибка получения баланса токенов: {e}")
            return 0
    
    async def _estimate_sol_output(self, token_amount: int) -> int:
        """
        Оценивает количество SOL, которое можно получить за токены.
        
        Args:
            token_amount: Количество токенов для продажи
            
        Returns:
            Примерное количество SOL в lamports
        """
        try:
            # Здесь можно добавить интеграцию с CurveManager для точного расчета
            # Пока используем примерную оценку
            estimated_sol = token_amount // 1000000  # Примерный курс
            logger.debug(f"Оценка получаемого SOL: {estimated_sol} lamports")
            return max(estimated_sol, 1000)  # Минимум 1000 lamports
        except Exception as e:
            logger.warning(f"Не удалось оценить количество SOL: {e}")
            return 1000  # Минимальное значение
    
    async def get_sell_quote(self, token_info, token_amount: Optional[int] = None) -> Dict[str, Any]:
        """
        Получает котировку для продажи без выполнения транзакции.
        
        Args:
            token_info: TokenInfo объект с данными токена от слушателя
            token_amount: Количество токенов (если None, используется весь баланс)
            
        Returns:
            Словарь с информацией о котировке
        """
        logger.info(f"📊 Получение котировки продажи для {token_info.symbol} ({token_info.mint})")
        
        try:
            mint_pubkey = token_info.mint
            wallet_pubkey = self.wallet.get_public_key()
            
            # Получение текущего баланса
            current_balance = await self._get_token_balance(mint_pubkey, wallet_pubkey)
            
            if token_amount is None:
                tokens_to_sell = current_balance
            else:
                tokens_to_sell = min(token_amount, current_balance)
            
            # Оценка получаемого SOL
            estimated_sol = await self._estimate_sol_output(tokens_to_sell)
            
            quote = {
                'mint_address': token_info.mint,
                'current_balance': current_balance,
                'tokens_to_sell': tokens_to_sell,
                'estimated_sol': estimated_sol,
                'estimated_sol_formatted': estimated_sol / 1_000_000_000,
                'price_per_token': estimated_sol / tokens_to_sell if tokens_to_sell > 0 else 0,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            logger.debug(f"Котировка продажи: {quote}")
            return quote
            
        except Exception as e:
            logger.error(f"Ошибка получения котировки продажи: {e}")
            return {'error': str(e)}
    
    async def sell_all_tokens(self, token_info, slippage_percent: float = 5.0) -> SellResult:
        """
        Продает все токены данного mint'а.
        
        Args:
            token_info: TokenInfo объект с данными токена от слушателя
            slippage_percent: Процент slippage (по умолчанию 5%)
            
        Returns:
            SellResult с результатом операции
        """
        logger.info(f"🔥 Продажа ВСЕХ токенов {token_info.symbol} ({token_info.mint})")
        return await self.sell_token(token_info, percentage=100.0, slippage_percent=slippage_percent)


# Пример использования
if __name__ == "__main__":
    async def example_usage():
        """Пример использования SimpleSeller"""
        print("💰 ПРИМЕР ИСПОЛЬЗОВАНИЯ SIMPLE SELLER")
        print("=" * 50)
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        print("⚠️  Для полного примера необходимы инициализированные компоненты:")
        print("   - SimpleClient")
        print("   - SimpleWallet") 
        print("   - AddressProvider")
        print("   - InstructionBuilder")
        
        # Пример использования (требует инициализированные компоненты)
        # seller = SimpleSeller(client, wallet, address_provider, instruction_builder)
        
        # Пример получения котировки
        # quote = await seller.get_sell_quote("So11111111111111111111111111111111111111112")
        # print(f"📊 Котировка продажи: {quote}")
        
        # Пример продажи 50% токенов
        # result = await seller.sell_token("So11111111111111111111111111111111111111112", percentage=50.0)
        # print(f"💰 Результат продажи: {result}")
        
        # Пример продажи всех токенов
        # result = await seller.sell_all_tokens("So11111111111111111111111111111111111111112")
        # print(f"🔥 Результат продажи всех токенов: {result}")
        
        print("\n🎯 SimpleSeller готов к использованию!")
    
    # Запуск примера
    asyncio.run(example_usage())
