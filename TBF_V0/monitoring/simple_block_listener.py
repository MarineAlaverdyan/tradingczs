"""
Упрощенный блок-слушатель для pump.fun.
Адаптирован из rebuild_broject/block_listener.py с упрощениями.
"""

import asyncio
import base64
import json
import struct
from typing import Callable, Dict, Any, Awaitable, Optional
import sys
import os

# Импорты с fallback для отсутствующих зависимостей
try:
    import base58
except ImportError:
    # Заглушка для base58
    class MockBase58:
        @staticmethod
        def b58decode(data):
            return b'mock_decoded_data'
    base58 = MockBase58()

try:
    import websockets
except ImportError:
    # Заглушка для websockets
    class MockWebsockets:
        @staticmethod
        async def connect(uri):
            from unittest.mock import AsyncMock
            return AsyncMock()
    websockets = MockWebsockets()

try:
    from solders.pubkey import Pubkey
    from solders.transaction import VersionedTransaction
except ImportError:
    # Заглушки для solders
    class MockPubkey:
        def __init__(self, data):
            self.data = data
        def __str__(self):
            return "MockPubkey"
    
    class MockVersionedTransaction:
        def __init__(self, data):
            self.data = data
    
    Pubkey = MockPubkey
    VersionedTransaction = MockVersionedTransaction

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Импортируем из TBF_V0 пакета
try:
    from pumpfun.event_parser import EventParser, TokenInfo
except ImportError:
    # Fallback для локального импорта
    try:
        from pumpfun.event_parser import EventParser, TokenInfo
    except ImportError:
        # Если EventParser недоступен, создаем заглушку
        class TokenInfo:
            def __init__(self, mint=None, name=None, symbol=None, uri=None, creator=None, 
                        bonding_curve=None, associated_bonding_curve=None, platform=None):
                self.mint = mint
                self.name = name
                self.symbol = symbol
                self.uri = uri
                self.creator = creator
                self.bonding_curve = bonding_curve
                self.associated_bonding_curve = associated_bonding_curve
                self.platform = platform
        
        class EventParser:
            pass


class SimpleBlockListener:
    """Упрощенный слушатель блоков для pump.fun."""
    
    def __init__(self, wss_endpoint: str):
        """
        Инициализация слушателя.
        
        Args:
            wss_endpoint: WebSocket эндпоинт Solana RPC
        """
        self.wss_endpoint = wss_endpoint
        self.websocket = None
        self.is_listening = False
        self.pump_program_id = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
        
        # Discriminator для инструкции создания токена (precalculated)
        self.create_discriminator = 8576854823835016728
    
    async def start_listening(self, on_new_token_callback: Callable[[dict], Awaitable[None]]):
        """
        Начать слушать блоки и искать создание токенов.
        
        Args:
            on_new_token_callback: Callback функция для новых токенов
        """
        try:
            print(f"🔌 Подключаемся к WebSocket: {self.wss_endpoint}")
            
            async with websockets.connect(self.wss_endpoint) as websocket:
                self.websocket = websocket
                self.is_listening = True
                
                # Подписываемся на блоки с упоминанием pump.fun программы
                subscription_message = json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "blockSubscribe",
                    "params": [
                        {"mentionsAccountOrProgram": self.pump_program_id},
                        {
                            "commitment": "confirmed",
                            "encoding": "base64",
                            "showRewards": False,
                            "transactionDetails": "full",
                            "maxSupportedTransactionVersion": 0,
                        },
                    ],
                })
                
                await websocket.send(subscription_message)
                print(f"✅ Подписались на блоки с программой: {self.pump_program_id}")
                
                # Основной цикл обработки сообщений
                while self.is_listening:
                    try:
                        response = await websocket.recv()
                        data = json.loads(response)
                        
                        await self._process_message(data, on_new_token_callback)
                        
                    except websockets.exceptions.ConnectionClosed:
                        print("❌ WebSocket соединение закрыто")
                        break
                    except Exception as e:
                        print(f"⚠️ Ошибка обработки сообщения: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ Ошибка подключения к WebSocket: {e}")
        finally:
            self.is_listening = False
            self.websocket = None
    
    async def stop_listening(self):
        """Остановить слушание блоков."""
        self.is_listening = False
        if self.websocket:
            await self.websocket.close()
    
    async def _process_message(self, data: Dict[str, Any], callback: Callable[[TokenInfo], Awaitable[None]]):
        """
        Обработать сообщение от WebSocket.
        
        Args:
            data: Данные сообщения
            callback: Callback для новых токенов
        """
        try:
            #print(data)
            # Проверяем тип сообщения
            if "method" in data and data["method"] == "blockNotification":
                await self._process_block_notification(data, callback)
            elif "result" in data:
                print("📋 Подписка подтверждена")
            else:
                print(f"🤷 Неизвестный тип сообщения: {data.get('method', 'Unknown')}")

        except Exception as e:
            print(f"⚠️ Ошибка обработки сообщения: {e}")
    
    async def _process_block_notification(self, data: Dict[str, Any], callback: Callable[[TokenInfo], Awaitable[None]]):
        """
        Обработать уведомление о новом блоке.
        
        Args:
            data: Данные блока
            callback: Callback для новых токенов
        """
        try:
            # Извлекаем данные блока
            if "params" not in data or "result" not in data["params"]:
                return
            
            block_data = data["params"]["result"]
            if "value" not in block_data or "block" not in block_data["value"]:
                return
            
            block = block_data["value"]["block"]
            if "transactions" not in block:
                return
            
            # Обрабатываем каждую транзакцию в блоке
            for tx in block["transactions"]:
                await self._process_transaction(tx, callback)
                
        except Exception as e:
            print(f"⚠️ Ошибка обработки блока: {e}")
    
    async def _process_transaction(self, tx: Dict[str, Any], callback: Callable[[TokenInfo], Awaitable[None]]):
        """
        Обработать транзакцию и найти создание токенов.
        
        Args:
            tx: Данные транзакции
            callback: Callback для новых токенов
        """
        try:
            if not isinstance(tx, dict) or "transaction" not in tx:
                return
            
            # Декодируем транзакцию
            tx_data_encoded = tx["transaction"][0]
            tx_data_decoded = base64.b64decode(tx_data_encoded)
            transaction = VersionedTransaction.from_bytes(tx_data_decoded)
            
            # Получаем ключи аккаунтов
            account_keys = [str(key) for key in transaction.message.account_keys]
            
            # Проверяем каждую инструкцию
            for instruction in transaction.message.instructions:
                await self._process_instruction(instruction, account_keys, callback)
                
        except Exception as e:
            print(f"⚠️ Ошибка обработки транзакции: {e}")
    
    async def _process_instruction(self, instruction, account_keys: list, callback: Callable[[TokenInfo], Awaitable[None]]):
        """
        Обработать инструкцию и найти создание токена.
        
        Args:
            instruction: Инструкция транзакции
            account_keys: Ключи аккаунтов
            callback: Callback для новых токенов
        """
        try:
            # Проверяем, что это pump.fun программа
            program_id_index = instruction.program_id_index
            if program_id_index >= len(account_keys):
                return
            
            program_id = account_keys[program_id_index]
            if program_id != self.pump_program_id:
                return
            
            # Декодируем данные инструкции
            ix_data = bytes(instruction.data)
            if len(ix_data) < 8:
                return
            
            # Проверяем discriminator
            discriminator = struct.unpack("<Q", ix_data[:8])[0]
            if discriminator != self.create_discriminator:
                return
            
            print("🎉 Найдена инструкция создания токена!")
            
            # Декодируем данные токена
            decoded_args = self._decode_create_instruction(ix_data, instruction.accounts, account_keys)
            
            if decoded_args is None:
                return
            
            print(f"🎯 Найден новый токен: {decoded_args.get('name', 'Unknown')} ({decoded_args.get('symbol', 'Unknown')})")
            print(f"   Mint: {decoded_args.get('mint', 'Unknown')}")
            print(f"   Создатель: {decoded_args.get('user', 'Unknown')}")
            print("ix_data", ix_data, "decoded_args", decoded_args)
            print("-"*30,"\n", decoded_args ,"\n", )

            # Вызываем callback с Dict[str, Any] как в оригинальном файле
            await callback(decoded_args)
            
        except Exception as e:
            print(f"⚠️ Ошибка обработки инструкции: {e}")
    
    def _decode_create_instruction(self, ix_data: bytes, accounts: list, account_keys: list) -> Optional[dict]:
        """
        Декодировать инструкцию создания токена (как в оригинальном файле).
        
        Args:
            ix_data: Данные инструкции
            accounts: Индексы аккаунтов
            account_keys: Ключи аккаунтов
            
        Returns:
            Dict с данными токена если декодирование успешно
        """
        try:
            args = {}
            offset = 8  # Пропускаем discriminator
            
            # Парсим название (string)
            name_length = struct.unpack_from("<I", ix_data, offset)[0]
            offset += 4
            name = ix_data[offset:offset + name_length].decode("utf-8")
            offset += name_length
            args["name"] = name
            
            # Парсим символ (string)
            symbol_length = struct.unpack_from("<I", ix_data, offset)[0]
            offset += 4
            symbol = ix_data[offset:offset + symbol_length].decode("utf-8")
            offset += symbol_length
            args["symbol"] = symbol
            
            # Парсим URI (string)
            uri_length = struct.unpack_from("<I", ix_data, offset)[0]
            offset += 4
            uri = ix_data[offset:offset + uri_length].decode("utf-8")
            args["uri"] = uri
            
            # Извлекаем адреса из аккаунтов (как в оригинальном файле)
            if len(accounts) >= 8:
                args["mint"] = str(account_keys[accounts[0]])
                args["bondingCurve"] = str(account_keys[accounts[2]])
                args["associatedBondingCurve"] = str(account_keys[accounts[3]])
                args["user"] = str(account_keys[accounts[7]])
                
                return args
            
            return None
            
        except Exception as e:
            print(f"⚠️ Ошибка декодирования инструкции: {e}")
            return None


# Пример использования
async def example_callback(token_data: dict):
    """Пример callback функции для новых токенов (как в оригинальном файле)."""
    print(f"🎯 CALLBACK: Получен новый токен!")
    print(f"   Название: {token_data.get('name', 'Unknown')}")
    print(f"   Символ: {token_data.get('symbol', 'Unknown')}")
    print(f"   Mint: {token_data.get('mint', 'Unknown')}")
    print(f"   Создатель: {token_data.get('user', 'Unknown')}")
    print(f"   URI: {token_data.get('uri', 'Unknown')}")
    print("-" * 50)


async def main():
    """Пример использования SimpleBlockListener."""
    
    print("👂 Пример работы с SimpleBlockListener")
    print("=" * 50)
    
    # Используем devnet для тестирования
    wss_endpoint = 'wss://solana-mainnet.core.chainstack.com/9a6c42741789e5c382251d7fe4589435'

    
    listener = SimpleBlockListener(wss_endpoint)
    
    try:
        print("🚀 Запускаем слушатель блоков...")
        print("⏰ Слушаем 30 секунд...")
        
        # Запускаем слушатель с таймаутом
        await asyncio.wait_for(
            listener.start_listening(example_callback),
            timeout=30.0
        )
        
    except asyncio.TimeoutError:
        print("⏰ Время тестирования истекло")
    except KeyboardInterrupt:
        print("⛔ Остановлено пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await listener.stop_listening()
        print("🏁 Слушатель остановлен")


if __name__ == "__main__":
    asyncio.run(main())
