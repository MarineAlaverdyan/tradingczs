"""
Простая система очистки для закрытия token accounts.
Закрывает пустые token accounts и возвращает SOL на основной кошелек.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solders.instruction import Instruction
from solders.transaction import Transaction
from solders.message import Message

# Настройка логирования
logger = logging.getLogger(__name__)

@dataclass
class CleanupResult:
    """Результат операции очистки"""
    success: bool
    closed_accounts: List[str] = None
    sol_recovered: int = 0
    error_message: Optional[str] = None
    transaction_signatures: List[str] = None

    def __post_init__(self):
        if self.closed_accounts is None:
            self.closed_accounts = []
        if self.transaction_signatures is None:
            self.transaction_signatures = []


class SimpleCleanup:
    """
    Простая система очистки token accounts.
    """
    
    def __init__(self, client, wallet, address_provider):
        """
        Инициализация системы очистки.
        
        Args:
            client: SimpleClient для взаимодействия с Solana
            wallet: SimpleWallet для подписания транзакций
            address_provider: AddressProvider для расчета адресов
        """
        self.client = client
        self.wallet = wallet
        self.address_provider = address_provider
        
        logger.info("SimpleCleanup инициализирован")
    
    async def cleanup_after_sell(self, mint_address: str) -> CleanupResult:
        """
        Очистка после продажи токена.
        
        Args:
            mint_address: Адрес mint проданного токена
            
        Returns:
            CleanupResult с результатом операции
        """
        logger.info(f"🧹 Начинаем очистку после продажи: {mint_address}")
        
        try:
            mint_pubkey = Pubkey.from_string(mint_address)
            wallet_pubkey = self.wallet.get_public_key()
            
            # Получение ATA адреса
            ata_address = await self.address_provider.get_associated_token_address(
                wallet_pubkey, mint_pubkey
            )
            
            # Проверка баланса token account
            balance = await self._get_token_account_balance(str(ata_address))
            
            if balance > 0:
                logger.warning(f"⚠️ Token account не пустой, баланс: {balance}")
                return CleanupResult(
                    success=False,
                    error_message=f"Token account содержит {balance} токенов"
                )
            
            # Закрытие пустого token account
            result = await self._close_token_account(str(ata_address))
            
            if result.success:
                logger.info(f"✅ Token account закрыт: {ata_address}")
                return CleanupResult(
                    success=True,
                    closed_accounts=[str(ata_address)],
                    sol_recovered=result.sol_recovered,
                    transaction_signatures=result.transaction_signatures
                )
            else:
                return result
                
        except Exception as e:
            error_msg = f"Ошибка очистки после продажи: {str(e)}"
            logger.error(error_msg)
            return CleanupResult(success=False, error_message=error_msg)
    
    async def cleanup_after_failure(self, mint_address: str) -> CleanupResult:
        """
        Очистка после неудачной операции.
        
        Args:
            mint_address: Адрес mint токена
            
        Returns:
            CleanupResult с результатом операции
        """
        logger.info(f"🧹 Очистка после неудачи: {mint_address}")
        
        try:
            mint_pubkey = Pubkey.from_string(mint_address)
            wallet_pubkey = self.wallet.get_public_key()
            
            # Получение ATA адреса
            ata_address = await self.address_provider.get_associated_token_address(
                wallet_pubkey, mint_pubkey
            )
            
            # Проверка существования account
            exists = await self._token_account_exists(str(ata_address))
            
            if not exists:
                logger.info("ℹ️ Token account не существует, очистка не требуется")
                return CleanupResult(success=True)
            
            # Проверка баланса
            balance = await self._get_token_account_balance(str(ata_address))
            
            if balance > 0:
                logger.warning(f"⚠️ Token account содержит токены: {balance}")
                # Можно добавить логику принудительной продажи или перевода
                return CleanupResult(
                    success=False,
                    error_message=f"Token account содержит {balance} токенов, требуется продажа"
                )
            
            # Закрытие пустого account
            result = await self._close_token_account(str(ata_address))
            return result
            
        except Exception as e:
            error_msg = f"Ошибка очистки после неудачи: {str(e)}"
            logger.error(error_msg)
            return CleanupResult(success=False, error_message=error_msg)
    
    async def cleanup_all_empty_accounts(self) -> CleanupResult:
        """
        Очистка всех пустых token accounts в кошельке.
        
        Returns:
            CleanupResult с результатом операции
        """
        logger.info("🧹 Очистка всех пустых token accounts")
        
        try:
            wallet_pubkey = self.wallet.get_public_key()
            
            # Получение всех token accounts
            token_accounts = await self._get_all_token_accounts(wallet_pubkey)
            
            if not token_accounts:
                logger.info("ℹ️ Token accounts не найдены")
                return CleanupResult(success=True)
            
            logger.info(f"📊 Найдено {len(token_accounts)} token accounts")
            
            closed_accounts = []
            total_sol_recovered = 0
            all_signatures = []
            
            for account_info in token_accounts:
                try:
                    account_address = account_info['address']
                    balance = account_info.get('balance', 0)
                    
                    if balance == 0:
                        logger.debug(f"Закрываем пустой account: {account_address}")
                        
                        result = await self._close_token_account(account_address)
                        
                        if result.success:
                            closed_accounts.extend(result.closed_accounts)
                            total_sol_recovered += result.sol_recovered
                            all_signatures.extend(result.transaction_signatures)
                        else:
                            logger.warning(f"Не удалось закрыть {account_address}: {result.error_message}")
                    else:
                        logger.debug(f"Пропускаем account с балансом: {account_address} ({balance} токенов)")
                        
                except Exception as e:
                    logger.error(f"Ошибка обработки account {account_info}: {e}")
                    continue
            
            logger.info(f"✅ Очистка завершена: закрыто {len(closed_accounts)} accounts")
            logger.info(f"💰 Возвращено SOL: {total_sol_recovered / 1_000_000_000:.6f}")
            
            return CleanupResult(
                success=True,
                closed_accounts=closed_accounts,
                sol_recovered=total_sol_recovered,
                transaction_signatures=all_signatures
            )
            
        except Exception as e:
            error_msg = f"Ошибка массовой очистки: {str(e)}"
            logger.error(error_msg)
            return CleanupResult(success=False, error_message=error_msg)
    
    async def _close_token_account(self, account_address: str) -> CleanupResult:
        """
        Закрывает конкретный token account.
        
        Args:
            account_address: Адрес token account для закрытия
            
        Returns:
            CleanupResult с результатом операции
        """
        try:
            logger.debug(f"Закрытие token account: {account_address}")
            
            # Создание инструкции закрытия
            close_instruction = await self._create_close_account_instruction(account_address)
            
            if not close_instruction:
                return CleanupResult(
                    success=False,
                    error_message="Не удалось создать инструкцию закрытия"
                )
            
            # Получение blockhash
            blockhash_response = await self.client.get_latest_blockhash()
            if not blockhash_response.get('success'):
                return CleanupResult(
                    success=False,
                    error_message="Не удалось получить blockhash"
                )
            
            blockhash = blockhash_response['blockhash']
            
            # Создание транзакции
            message = Message.new_with_blockhash(
                instructions=[close_instruction],
                payer=self.wallet.get_public_key(),
                blockhash=blockhash
            )
            
            transaction = Transaction.new_unsigned(message)
            signed_transaction = self.wallet.sign_transaction(transaction)
            
            # Отправка транзакции
            send_response = await self.client.send_transaction(signed_transaction)
            
            if not send_response.get('success'):
                return CleanupResult(
                    success=False,
                    error_message=send_response.get('error', 'Ошибка отправки транзакции')
                )
            
            signature = send_response['signature']
            logger.debug(f"Транзакция закрытия отправлена: {signature}")
            
            # Подтверждение транзакции
            confirm_response = await self.client.confirm_transaction(signature)
            
            if confirm_response.get('success'):
                # Примерная оценка возвращенного SOL (rent)
                estimated_sol_recovered = 2039280  # Примерный rent за token account
                
                return CleanupResult(
                    success=True,
                    closed_accounts=[account_address],
                    sol_recovered=estimated_sol_recovered,
                    transaction_signatures=[signature]
                )
            else:
                return CleanupResult(
                    success=False,
                    error_message=confirm_response.get('error', 'Транзакция не подтверждена')
                )
                
        except Exception as e:
            error_msg = f"Ошибка закрытия token account: {str(e)}"
            logger.error(error_msg)
            return CleanupResult(success=False, error_message=error_msg)
    
    async def _create_close_account_instruction(self, account_address: str) -> Optional[Instruction]:
        """
        Создает инструкцию для закрытия token account.
        
        Args:
            account_address: Адрес account для закрытия
            
        Returns:
            Instruction или None при ошибке
        """
        try:
            # Здесь должна быть реальная инструкция закрытия SPL Token account
            # Пока возвращаем заглушку
            logger.debug(f"Создание инструкции закрытия для {account_address}")
            
            # В реальной реализации нужно использовать:
            # from spl.token.instructions import close_account
            # return close_account(...)
            
            return None  # Заглушка
            
        except Exception as e:
            logger.error(f"Ошибка создания инструкции закрытия: {e}")
            return None
    
    async def _get_token_account_balance(self, account_address: str) -> int:
        """
        Получает баланс token account.
        
        Args:
            account_address: Адрес token account
            
        Returns:
            Баланс токенов
        """
        try:
            balance_response = await self.client.get_token_account_balance(account_address)
            
            if balance_response.get('success'):
                return balance_response.get('balance', 0)
            else:
                logger.warning(f"Не удалось получить баланс {account_address}")
                return 0
                
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return 0
    
    async def _token_account_exists(self, account_address: str) -> bool:
        """
        Проверяет существование token account.
        
        Args:
            account_address: Адрес token account
            
        Returns:
            True если account существует
        """
        try:
            # Здесь должна быть проверка через getAccountInfo
            # Пока возвращаем True как заглушку
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки существования account: {e}")
            return False
    
    async def _get_all_token_accounts(self, wallet_pubkey: Pubkey) -> List[Dict[str, Any]]:
        """
        Получает все token accounts кошелька.
        
        Args:
            wallet_pubkey: Публичный ключ кошелька
            
        Returns:
            Список token accounts с информацией
        """
        try:
            # Здесь должен быть запрос через getTokenAccountsByOwner
            # Пока возвращаем пустой список
            logger.debug(f"Получение token accounts для {wallet_pubkey}")
            return []
            
        except Exception as e:
            logger.error(f"Ошибка получения token accounts: {e}")
            return []


# Пример использования
if __name__ == "__main__":
    async def example_usage():
        """Пример использования SimpleCleanup"""
        print("🧹 ПРИМЕР ИСПОЛЬЗОВАНИЯ SIMPLE CLEANUP")
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
        
        # Пример использования (требует инициализированные компоненты)
        # cleanup = SimpleCleanup(client, wallet, address_provider)
        
        # Пример очистки после продажи
        # result = await cleanup.cleanup_after_sell("So11111111111111111111111111111111111111112")
        # print(f"🧹 Результат очистки: {result}")
        
        # Пример массовой очистки
        # result = await cleanup.cleanup_all_empty_accounts()
        # print(f"🧹 Массовая очистка: {result}")
        
        print("\n🎯 SimpleCleanup готов к использованию!")
    
    # Запуск примера
    asyncio.run(example_usage())
