"""
SolanaClient - основной класс для взаимодействия с блокчейном Solana.

Этот модуль предоставляет абстракцию над Solana RPC API и управляет:
- Подключением к RPC узлу
- Кэшированием blockhash для оптимизации
- Отправкой транзакций с retry логикой
- Подтверждением транзакций
"""

import asyncio
import json
from typing import Any, Dict, Optional

import aiohttp
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from solana.rpc.types import TxOpts
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.hash import Hash
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction

from utils.logger import get_logger

logger = get_logger(__name__)


class SolanaClient:
    """
    Основной клиент для работы с Solana блокчейном.
    
    Ключевые особенности:
    1. Кэширование blockhash - blockhash нужен для каждой транзакции, 
       но получение его через RPC занимает время. Мы кэшируем его и 
       обновляем в фоновом режиме каждые 5 секунд.
    
    2. Retry логика - если транзакция не прошла, автоматически повторяем
       попытку с экспоненциальной задержкой.
    
    3. Priority fees - добавляем приоритетные комиссии для быстрого 
       включения транзакции в блок.
    """

    def __init__(self, rpc_endpoint: str):
        """
        Инициализация клиента.
        
        Args:
            rpc_endpoint: URL RPC узла Solana (например, https://api.mainnet-beta.solana.com)
        """
        self.rpc_endpoint = rpc_endpoint
        self._client: Optional[AsyncClient] = None
        
        # Кэш для blockhash - это хэш последнего блока, который нужен для транзакций
        self._cached_blockhash: Optional[Hash] = None
        self._blockhash_lock = asyncio.Lock()  # Защита от race conditions
        
        # Запускаем фоновую задачу для обновления blockhash
        self._blockhash_updater_task = None

    async def initialize(self) -> None:
        """Инициализация асинхронных компонентов."""
        self._blockhash_updater_task = asyncio.create_task(
            self._start_blockhash_updater()
        )

    async def _start_blockhash_updater(self, interval: float = 5.0) -> None:
        """
        Фоновая задача для обновления blockhash.
        
        Почему это важно:
        - Blockhash действителен только ~150 блоков (~60-90 секунд)
        - Получение blockhash через RPC занимает 100-300ms
        - Кэшируя его, мы экономим время на каждой транзакции
        
        Args:
            interval: Интервал обновления в секундах
        """
        while True:
            try:
                # Получаем свежий blockhash
                blockhash = await self.get_latest_blockhash()
                
                # Атомарно обновляем кэш
                async with self._blockhash_lock:
                    self._cached_blockhash = blockhash
                    
                logger.debug(f"Blockhash updated: {blockhash}")
                
            except Exception as e:
                logger.warning(f"Failed to update blockhash: {e}")
            
            await asyncio.sleep(interval)

    async def get_cached_blockhash(self) -> Hash:
        """
        Получить кэшированный blockhash.
        
        Returns:
            Последний кэшированный blockhash
            
        Raises:
            RuntimeError: Если blockhash еще не был загружен
        """
        async with self._blockhash_lock:
            if self._cached_blockhash is None:
                # Если кэш пуст, получаем blockhash синхронно
                logger.info("No cached blockhash, fetching synchronously...")
                self._cached_blockhash = await self.get_latest_blockhash()
            
            return self._cached_blockhash

    async def get_client(self) -> AsyncClient:
        """
        Получить или создать AsyncClient.
        
        Ленивая инициализация - создаем клиент только когда он нужен.
        """
        if self._client is None:
            self._client = AsyncClient(self.rpc_endpoint)
        return self._client

    async def close(self) -> None:
        """Закрыть соединения и остановить фоновые задачи."""
        # Останавливаем обновление blockhash
        if self._blockhash_updater_task:
            self._blockhash_updater_task.cancel()
            try:
                await self._blockhash_updater_task
            except asyncio.CancelledError:
                pass

        # Закрываем RPC клиент
        if self._client:
            await self._client.close()
            self._client = None

    async def get_health(self) -> Optional[str]:
        """
        Проверить здоровье RPC узла.
        
        Returns:
            Статус узла или None при ошибке
        """
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getHealth",
        }
        result = await self._post_rpc(body)
        if result and "result" in result:
            return result["result"]
        return None

    async def get_account_info(self, pubkey: Pubkey) -> Dict[str, Any]:
        """
        Получить информацию об аккаунте.
        
        Args:
            pubkey: Публичный ключ аккаунта
            
        Returns:
            Информация об аккаунте
            
        Raises:
            ValueError: Если аккаунт не найден
        """
        client = await self.get_client()
        response = await client.get_account_info(pubkey, encoding="base64")
        
        if not response.value:
            raise ValueError(f"Account {pubkey} not found")
            
        return response.value

    async def get_token_account_balance(self, token_account: Pubkey) -> int:
        """
        Получить баланс токен-аккаунта.
        
        Args:
            token_account: Адрес токен-аккаунта
            
        Returns:
            Баланс в базовых единицах токена
        """
        client = await self.get_client()
        response = await client.get_token_account_balance(token_account)
        
        if response.value:
            return int(response.value.amount)
        return 0

    async def get_latest_blockhash(self) -> Hash:
        """
        Получить последний blockhash.
        
        Returns:
            Свежий blockhash
        """
        client = await self.get_client()
        response = await client.get_latest_blockhash(commitment="processed")
        return response.value.blockhash

    async def build_and_send_transaction(
        self,
        instructions: list[Instruction],
        signer_keypair: Keypair,
        skip_preflight: bool = True,
        max_retries: int = 3,
        priority_fee: Optional[int] = None,
    ) -> str:
        """
        Построить и отправить транзакцию.
        
        Это основной метод для отправки транзакций. Он:
        1. Добавляет priority fee инструкции (если указаны)
        2. Создает транзакцию с кэшированным blockhash
        3. Подписывает транзакцию
        4. Отправляет с retry логикой
        
        Args:
            instructions: Список инструкций для выполнения
            signer_keypair: Ключевая пара для подписи
            skip_preflight: Пропустить предварительные проверки (быстрее)
            max_retries: Максимальное количество попыток
            priority_fee: Приоритетная комиссия в микроламports
            
        Returns:
            Подпись транзакции
        """
        client = await self.get_client()

        logger.info(f"Sending transaction with priority fee: {priority_fee or 0} microlamports")

        # Добавляем priority fee инструкции в начало
        if priority_fee is not None:
            priority_instructions = [
                set_compute_unit_limit(300_000),  # Лимит compute units
                set_compute_unit_price(priority_fee),  # Цена за compute unit
            ]
            instructions = priority_instructions + instructions

        # Получаем кэшированный blockhash для экономии времени
        recent_blockhash = await self.get_cached_blockhash()
        
        # Создаем транзакцию
        message = Message(instructions, signer_keypair.pubkey())
        transaction = Transaction([signer_keypair], message, recent_blockhash)

        # Отправляем с retry логикой
        for attempt in range(max_retries):
            try:
                tx_opts = TxOpts(
                    skip_preflight=skip_preflight,  # Пропускаем симуляцию для скорости
                    preflight_commitment=Processed
                )
                
                response = await client.send_transaction(transaction, tx_opts)
                signature = response.value
                
                logger.info(f"Transaction sent successfully: {signature}")
                return signature

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Transaction failed after {max_retries} attempts: {e}")
                    raise

                # Экспоненциальная задержка: 1s, 2s, 4s...
                wait_time = 2 ** attempt
                logger.warning(
                    f"Transaction attempt {attempt + 1} failed: {e}, "
                    f"retrying in {wait_time}s"
                )
                await asyncio.sleep(wait_time)

    async def confirm_transaction(
        self, 
        signature: str, 
        commitment: str = "confirmed",
        timeout: int = 60
    ) -> bool:
        """
        Дождаться подтверждения транзакции.
        
        Args:
            signature: Подпись транзакции
            commitment: Уровень подтверждения
            timeout: Таймаут в секундах
            
        Returns:
            True если транзакция подтверждена
        """
        client = await self.get_client()
        
        try:
            await client.confirm_transaction(
                signature, 
                commitment=commitment, 
                sleep_seconds=1
            )
            logger.info(f"Transaction confirmed: {signature}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to confirm transaction {signature}: {e}")
            return False

    async def _post_rpc(self, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Отправить прямой RPC запрос.
        
        Используется для методов, которые не поддерживаются в solana-py.
        
        Args:
            body: JSON-RPC тело запроса
            
        Returns:
            Ответ от RPC или None при ошибке
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.rpc_endpoint,
                    json=body,
                    timeout=aiohttp.ClientTimeout(10),
                ) as response:
                    response.raise_for_status()
                    return await response.json()
                    
        except aiohttp.ClientError as e:
            logger.error(f"RPC request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode RPC response: {e}")
            return None
