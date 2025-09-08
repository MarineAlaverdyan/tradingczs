"""
Упрощенный модуль для работы с Solana кошельком.
Только базовые функции - загрузка приватного ключа и получение публичного ключа.
"""

import base58
from typing import Optional
from solders.keypair import Keypair
from solders.pubkey import Pubkey


class SimpleWallet:
    """Простой кошелек для работы с Solana."""
    
    def __init__(self, private_key: Optional[str] = None):
        """
        Инициализация кошелька.
        
        Args:
            private_key: Приватный ключ в формате base58 строки (опционально)
        """
        self.keypair: Optional[Keypair] = None
        
        if private_key:
            self.load_from_private_key(private_key)
    
    def load_from_private_key(self, private_key: str) -> bool:
        """
        Загрузить кошелек из приватного ключа.
        
        Args:
            private_key: Приватный ключ в формате base58 строки
            
        Returns:
            True если загрузка успешна
            
        Raises:
            Exception: При ошибке загрузки ключа
        """
        try:
            # Декодируем base58 строку в байты
            private_key_bytes = base58.b58decode(private_key)
            
            # Создаем keypair из байтов
            self.keypair = Keypair.from_bytes(private_key_bytes)
            
            return True
            
        except Exception as e:
            raise Exception(f"Ошибка загрузки приватного ключа: {e}")
    
    def generate_new(self) -> str:
        """
        Сгенерировать новый кошелек.
        
        Returns:
            Приватный ключ нового кошелька в формате base58
        """
        # Генерируем новый keypair
        self.keypair = Keypair()
        
        # Возвращаем приватный ключ в base58 формате
        return base58.b58encode(bytes(self.keypair)).decode('utf-8')
    
    def get_public_key(self) -> Pubkey:
        """
        Получить публичный ключ кошелька.
        
        Returns:
            Публичный ключ как объект Pubkey
            
        Raises:
            Exception: Если кошелек не загружен
        """
        if not self.keypair:
            raise Exception("Кошелек не загружен. Используйте load_from_private_key() или generate_new()")
        
        return self.keypair.pubkey()
    
    def get_address_string(self) -> str:
        """
        Получить адрес кошелька как строку.
        
        Returns:
            Адрес кошелька в формате base58 строки
        """
        pubkey = self.get_public_key()
        return str(pubkey)
    
    def get_private_key_string(self) -> str:
        """
        Получить приватный ключ как строку.
        
        Returns:
            Приватный ключ в формате base58 строки
            
        Raises:
            Exception: Если кошелек не загружен
        """
        if not self.keypair:
            raise Exception("Кошелек не загружен")
        
        return base58.b58encode(bytes(self.keypair)).decode('utf-8')
    
    def sign_message(self, message: bytes) -> bytes:
        """
        Подписать сообщение приватным ключом.
        
        Args:
            message: Сообщение для подписи в байтах
            
        Returns:
            Подпись в байтах
            
        Raises:
            Exception: Если кошелек не загружен
        """
        if not self.keypair:
            raise Exception("Кошелек не загружен")
        
        return self.keypair.sign_message(message)
    
    def is_loaded(self) -> bool:
        """
        Проверить, загружен ли кошелек.
        
        Returns:
            True если кошелек загружен
        """
        return self.keypair is not None
    
    def get_keypair(self) -> Keypair:
        """
        Получить объект Keypair для использования в транзакциях.
        
        Returns:
            Объект Keypair
            
        Raises:
            Exception: Если кошелек не загружен
        """
        if not self.keypair:
            raise Exception("Кошелек не загружен")
        
        return self.keypair
    
    def sign_transaction(self, transaction, recent_blockhash):
        """
        Подписать транзакцию приватным ключом.
        
        Args:
            transaction: Транзакция для подписи
            recent_blockhash: Recent blockhash для подписи
            
        Returns:
            Подписанная транзакция
            
        Raises:
            Exception: Если кошелек не загружен
        """
        if not self.keypair:
            raise Exception("Кошелек не загружен")
        
        # Подписываем транзакцию с помощью keypair и recent_blockhash
        signed_tx = transaction
        signed_tx.sign([self.keypair], recent_blockhash)
        return signed_tx


# Пример использования
def main():
    """Пример использования SimpleWallet."""
    
    print("🔑 Пример работы с SimpleWallet")
    print("=" * 40)
    
    # Создаем новый кошелек
    wallet = SimpleWallet()
    
    # Генерируем новый кошелек
    print("📱 Генерируем новый кошелек...")
    private_key = wallet.generate_new()
    print(f"   Приватный ключ: {private_key[:20]}...")
    print(f"   Адрес: {wallet.get_address_string()}")
    
    # Проверяем загрузку
    print(f"   Кошелек загружен: {wallet.is_loaded()}")
    
    # Создаем второй кошелек из существующего ключа
    print("\n🔄 Загружаем кошелек из приватного ключа...")
    wallet2 = SimpleWallet()
    
    try:
        wallet2.load_from_private_key(private_key)
        print(f"   Адрес загруженного кошелька: {wallet2.get_address_string()}")
        print(f"   Адреса совпадают: {wallet.get_address_string() == wallet2.get_address_string()}")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Тестируем подпись
    print("\n✍️  Тестируем подпись сообщения...")
    test_message = b"Hello, Solana!"
    try:
        signature = wallet.sign_message(test_message)
        print(f"   Сообщение: {test_message}")
        print(f"   Подпись: {signature.hex()[:40]}...")
    except Exception as e:
        print(f"   Ошибка подписи: {e}")
    
    # Тестируем ошибки
    print("\n❌ Тестируем обработку ошибок...")
    empty_wallet = SimpleWallet()
    
    try:
        empty_wallet.get_public_key()
    except Exception as e:
        print(f"   Ожидаемая ошибка: {e}")
    
    try:
        empty_wallet.load_from_private_key("invalid_key")
    except Exception as e:
        print(f"   Ожидаемая ошибка: {e}")


if __name__ == "__main__":
    main()
