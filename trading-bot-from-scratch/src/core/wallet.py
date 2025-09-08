"""
Wallet - класс для управления кошельком и подписи транзакций.

Этот модуль отвечает за:
- Загрузку приватного ключа из разных форматов
- Подпись транзакций
- Проверку баланса кошелька
- Безопасное хранение ключевой пары
"""

import base58
from typing import Optional

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from utils.logger import get_logger

logger = get_logger(__name__)


class Wallet:
    """
    Класс для управления кошельком торгового бота.
    
    Основные функции:
    1. Безопасная загрузка приватного ключа
    2. Подпись транзакций
    3. Проверка баланса SOL
    4. Получение публичного ключа
    """

    def __init__(self, private_key: str):
        """
        Инициализация кошелька из приватного ключа.
        
        Args:
            private_key: Приватный ключ в формате base58 или hex
            
        Raises:
            ValueError: Если приватный ключ невалидный
        """
        self._keypair = self._load_keypair_from_string(private_key)
        logger.info(f"Wallet initialized with address: {self.public_key}")

    def _load_keypair_from_string(self, private_key: str) -> Keypair:
        """
        Загрузить ключевую пару из строки.
        
        Поддерживает два формата:
        1. Base58 (стандартный формат Solana) - например из Phantom wallet
        2. Hex (альтернативный формат) - начинается с 0x
        
        Args:
            private_key: Приватный ключ в виде строки
            
        Returns:
            Ключевая пара Solana
            
        Raises:
            ValueError: Если формат ключа неподдерживается
        """
        try:
            # Убираем пробелы и переводы строк
            private_key = private_key.strip()
            
            if private_key.startswith('0x'):
                # Hex формат - конвертируем в bytes
                key_bytes = bytes.fromhex(private_key[2:])
            else:
                # Base58 формат (стандартный для Solana)
                key_bytes = base58.b58decode(private_key)
            
            # Проверяем длину ключа (должен быть 64 байта для ed25519)
            if len(key_bytes) != 64:
                raise ValueError(f"Invalid private key length: {len(key_bytes)}, expected 64")
            
            # Создаем ключевую пару
            keypair = Keypair.from_bytes(key_bytes)
            
            logger.debug("Private key loaded successfully")
            return keypair
            
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
            raise ValueError(f"Invalid private key format: {e}")

    @property
    def public_key(self) -> Pubkey:
        """
        Получить публичный ключ кошелька.
        
        Returns:
            Публичный ключ (адрес кошелька)
        """
        return self._keypair.pubkey()

    @property
    def keypair(self) -> Keypair:
        """
        Получить ключевую пару для подписи транзакций.
        
        Returns:
            Ключевая пара
        """
        return self._keypair

    async def get_sol_balance(self, client: AsyncClient) -> float:
        """
        Получить баланс SOL в кошельке.
        
        Args:
            client: Solana RPC клиент
            
        Returns:
            Баланс в SOL (не в lamports)
        """
        try:
            response = await client.get_balance(self.public_key)
            
            # Конвертируем lamports в SOL (1 SOL = 1,000,000,000 lamports)
            balance_lamports = response.value
            balance_sol = balance_lamports / 1_000_000_000
            
            logger.debug(f"Wallet balance: {balance_sol} SOL ({balance_lamports} lamports)")
            return balance_sol
            
        except Exception as e:
            logger.error(f"Failed to get wallet balance: {e}")
            return 0.0

    async def ensure_sufficient_balance(
        self, 
        client: AsyncClient, 
        required_sol: float,
        buffer_sol: float = 0.01  # Буфер для комиссий
    ) -> bool:
        """
        Проверить, достаточно ли SOL для операции.
        
        Args:
            client: Solana RPC клиент
            required_sol: Необходимое количество SOL
            buffer_sol: Дополнительный буфер для комиссий
            
        Returns:
            True если баланса достаточно
        """
        current_balance = await self.get_sol_balance(client)
        total_required = required_sol + buffer_sol
        
        if current_balance < total_required:
            logger.error(
                f"Insufficient balance: {current_balance} SOL, "
                f"required: {total_required} SOL "
                f"({required_sol} + {buffer_sol} buffer)"
            )
            return False
        
        logger.info(
            f"Balance check passed: {current_balance} SOL available, "
            f"{total_required} SOL required"
        )
        return True

    def __str__(self) -> str:
        """Строковое представление кошелька (только публичный ключ)."""
        return f"Wallet({self.public_key})"

    def __repr__(self) -> str:
        """Детальное представление кошелька."""
        return f"Wallet(public_key={self.public_key})"
