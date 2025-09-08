"""
Простой покупатель токенов для pump.fun.
Выполняет покупку токенов через bonding curve с логированием.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
from solders.hash import Hash

# Настройка логирования
logger = logging.getLogger(__name__)

@dataclass
class BuyResult:
    """Результат операции покупки"""
    success: bool
    transaction_signature: Optional[str] = None
    tokens_received: Optional[int] = None
    sol_spent: Optional[int] = None
    error_message: Optional[str] = None
    gas_used: Optional[int] = None


class SimpleBuyer:
    """
    Простой покупатель токенов через pump.fun bonding curve.
    """
    
    def __init__(self, client, wallet, address_provider, instruction_builder, priority_fee_manager=None):
        """
        Инициализация покупателя.
        
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
        
        logger.info("SimpleBuyer инициализирован")
    
    async def buy_token(
        self,
        token_info,
        sol_amount: float,
        slippage_percent: float = 5.0,
        max_retries: int = 3
    ) -> BuyResult:
        """
        Покупает токены через pump.fun bonding curve.
        
        Args:
            token_info: TokenInfo объект с данными токена от слушателя
            sol_amount: Количество SOL для покупки
            slippage_percent: Процент slippage (по умолчанию 5%)
            max_retries: Максимальное количество попыток
            
        Returns:
            BuyResult с результатом операции
        """
        logger.info(f"🛒 Начинаем покупку токена {token_info.symbol} ({token_info.mint})")
        logger.info(f"💰 Сумма: {sol_amount} SOL, Slippage: {slippage_percent}%")
        
        try:
            # Конвертация в lamports
            sol_lamports = int(sol_amount * 1_000_000_000)
            
            # Используем готовые адреса от слушателя (НЕ пересчитываем!)
            mint_pubkey = token_info.mint
            wallet_pubkey = self.wallet.get_public_key()
            bonding_curve = token_info.bonding_curve
            associated_bonding_curve = token_info.associated_bonding_curve
            
            # Только пользовательский ATA нужно рассчитать
            associated_user = self.address_provider.get_associated_token_address(
                wallet_pubkey, mint_pubkey
            )
            
            logger.info(f"📊 Используем данные от слушателя:")
            logger.info(f"   Mint: {mint_pubkey}")
            logger.info(f"   Bonding Curve: {bonding_curve}")
            logger.info(f"   Associated BC: {associated_bonding_curve}")
            logger.info(f"   User ATA: {associated_user}")
            
            logger.debug(f"Bonding curve: {bonding_curve}")
            logger.debug(f"User ATA: {associated_user}")
            
            # Расчет slippage
            min_amount, max_amount = self.instruction_builder.calculate_slippage_amounts(
                sol_lamports, slippage_percent
            )
            
            # Проверка существования ATA и создание если нужно
            logger.debug("Проверка существования ATA пользователя")
            ata_exists = await self._check_ata_exists(associated_user)
            
            instructions = []
            
            # Добавляем инструкцию создания ATA если не существует
            if not ata_exists:
                logger.info("🔧 ATA не существует, создаем инструкцию создания")
                create_ata_instruction = self.instruction_builder.build_create_ata_instruction(
                    payer=wallet_pubkey,
                    owner=wallet_pubkey,
                    mint=mint_pubkey,
                    ata_address=associated_user
                )
                instructions.append(create_ata_instruction)
            else:
                logger.info("✅ ATA уже существует")
            
            # Создание инструкции покупки
            logger.debug("Создание buy инструкции")
            buy_instruction = self.instruction_builder.build_buy_instruction(
                buyer_wallet=wallet_pubkey,
                mint_address=mint_pubkey,
                bonding_curve=bonding_curve,
                associated_bonding_curve=associated_bonding_curve,
                associated_user=associated_user,
                sol_amount=sol_lamports,
                max_sol_cost=max_amount
            )
            instructions.append(buy_instruction)
            
            # Выполнение покупки с повторными попытками
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔄 Попытка покупки #{attempt + 1}/{max_retries}")
                    
                    result = await self._execute_buy_transaction(
                        instructions, sol_lamports, max_amount
                    )
                    
                    if result.success:
                        logger.info(f"✅ Покупка успешна! Signature: {result.transaction_signature}")
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
            error_msg = f"Не удалось купить токен после {max_retries} попыток"
            logger.error(error_msg)
            return BuyResult(success=False, error_message=error_msg)
            
        except Exception as e:
            error_msg = f"Критическая ошибка при покупке: {str(e)}"
            logger.error(error_msg)
            return BuyResult(success=False, error_message=error_msg)
    
    async def _execute_buy_transaction(
        self, 
        instructions_list, 
        sol_amount: int, 
        max_sol_cost: int
    ) -> BuyResult:
        """
        Выполняет транзакцию покупки.
        
        Args:
            instructions_list: Список инструкций (включая создание ATA если нужно)
            sol_amount: Количество SOL в lamports
            max_sol_cost: Максимальная стоимость с slippage
            
        Returns:
            BuyResult с результатом
        """
        try:
            # Получение последнего blockhash
            logger.debug("Получение blockhash")
            blockhash = await self.client.get_latest_blockhash()
            if not blockhash:
                raise Exception("Не удалось получить blockhash")
            
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
            
            # Добавление всех инструкций из списка (ATA + buy)
            instructions.extend(instructions_list)
            
            # Создание транзакции
            logger.debug("Создание и подписание транзакции")
            hash_obj = Hash.from_string(blockhash)
            message = Message.new_with_blockhash(
                instructions=instructions,
                payer=self.wallet.get_public_key(),
                blockhash=hash_obj
            )
            
            transaction = Transaction.new_unsigned(message)
            signed_transaction = self.wallet.sign_transaction(transaction, hash_obj)
            
            # Отправка транзакции
            logger.info("📤 Отправка транзакции...")
            send_response = await self.client.send_transaction(signed_transaction)
            logger.info(f"📤 Ответ отправки: {send_response}")
            
            if not send_response.get('success'):
                error_msg = send_response.get('error', 'Неизвестная ошибка при отправке')
                logger.error(f"❌ Ошибка отправки: {error_msg}")
                return BuyResult(success=False, error_message=error_msg)
            
            signature = send_response['signature']
            logger.info(f"📤 Транзакция отправлена: {signature}")
            
            # Подтверждение транзакции
            logger.info("⏳ Ожидание подтверждения транзакции...")
            confirm_response = await self.client.confirm_transaction(signature)
            logger.info(f"⏳ Ответ подтверждения: {confirm_response}")
            
            if confirm_response.get('success'):
                logger.info(f"✅ Транзакция подтверждена: {signature}")
                
                # Попытка получить детали транзакции
                tokens_received = await self._estimate_tokens_received(sol_amount)
                
                return BuyResult(
                    success=True,
                    transaction_signature=signature,
                    tokens_received=tokens_received,
                    sol_spent=sol_amount
                )
            else:
                error_msg = confirm_response.get('error', 'Транзакция не подтверждена')
                logger.error(f"❌ Ошибка подтверждения: {error_msg}")
                return BuyResult(success=False, error_message=error_msg)
                
        except Exception as e:
            error_msg = f"Ошибка выполнения транзакции: {str(e)}"
            logger.error(error_msg)
            return BuyResult(success=False, error_message=error_msg)
    
    async def _check_ata_exists(self, ata_address: Pubkey) -> bool:
        """
        Проверяет существование Associated Token Account.
        
        Args:
            ata_address: Адрес ATA для проверки
            
        Returns:
            True если ATA существует, False иначе
        """
        try:
            response = await self.client._make_rpc_call("getAccountInfo", [str(ata_address)])
            if response and response.get('value') is not None:
                logger.debug(f"ATA {ata_address} существует")
                return True
            else:
                logger.debug(f"ATA {ata_address} не существует")
                return False
        except Exception as e:
            logger.warning(f"Ошибка проверки ATA {ata_address}: {e}")
            return False  # Считаем что не существует если ошибка
    
    async def _estimate_tokens_received(self, sol_amount: int) -> Optional[int]:
        """
        Оценивает количество полученных токенов.
        
        Args:
            sol_amount: Потраченное количество SOL в lamports
            
        Returns:
            Примерное количество токенов или None
        """
        try:
            # Здесь можно добавить логику расчета через CurveManager
            # Пока возвращаем примерную оценку
            estimated_tokens = sol_amount * 1000000  # Примерный курс
            logger.debug(f"Оценка полученных токенов: {estimated_tokens}")
            return estimated_tokens
        except Exception as e:
            logger.warning(f"Не удалось оценить количество токенов: {e}")
            return None
    
    async def get_buy_quote(self, mint_address: str, sol_amount: float) -> Dict[str, Any]:
        """
        Получает котировку для покупки без выполнения транзакции.
        
        Args:
            mint_address: Адрес mint токена
            sol_amount: Количество SOL
            
        Returns:
            Словарь с информацией о котировке
        """
        logger.info(f"📊 Получение котировки для {mint_address}, сумма: {sol_amount} SOL")
        
        try:
            sol_lamports = int(sol_amount * 1_000_000_000)
            
            # Здесь можно добавить интеграцию с CurveManager для точного расчета
            estimated_tokens = sol_lamports * 1000000  # Примерная оценка
            
            quote = {
                'mint_address': mint_address,
                'sol_amount': sol_amount,
                'sol_lamports': sol_lamports,
                'estimated_tokens': estimated_tokens,
                'price_per_token': sol_lamports / estimated_tokens if estimated_tokens > 0 else 0,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            logger.debug(f"Котировка: {quote}")
            return quote
            
        except Exception as e:
            logger.error(f"Ошибка получения котировки: {e}")
            return {'error': str(e)}


# Пример использования
if __name__ == "__main__":
    async def example_usage():
        """Пример использования SimpleBuyer"""
        print("🛒 ПРИМЕР ИСПОЛЬЗОВАНИЯ SIMPLE BUYER")
        print("=" * 50)
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Здесь должна быть инициализация компонентов
        # client = SimpleClient(...)
        # wallet = SimpleWallet(...)
        # address_provider = AddressProvider(...)
        # instruction_builder = InstructionBuilder(...)
        
        print("⚠️  Для полного примера необходимы инициализированные компоненты:")
        print("   - SimpleClient")
        print("   - SimpleWallet") 
        print("   - AddressProvider")
        print("   - InstructionBuilder")
        
        # buyer = SimpleBuyer(client, wallet, address_provider, instruction_builder)
        
        # Пример получения котировки
        # quote = await buyer.get_buy_quote("So11111111111111111111111111111111111111112", 0.001)
        # print(f"📊 Котировка: {quote}")
        
        # Пример покупки
        # result = await buyer.buy_token("So11111111111111111111111111111111111111112", 0.001, 5.0)
        # print(f"🛒 Результат покупки: {result}")
        
        print("\n🎯 SimpleBuyer готов к использованию!")
    
    # Запуск примера
    asyncio.run(example_usage())
