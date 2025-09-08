"""
Упрощенный Solana RPC клиент для базовых операций.
Без кэширования и сложной логики - только необходимый минимум.
"""

import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any


class SimpleClient:
    """Простой клиент для работы с Solana RPC."""
    
    def __init__(self, rpc_endpoint: str):
        """
        Инициализация клиента.
        
        Args:
            rpc_endpoint: URL RPC эндпоинта (например, https://api.devnet.solana.com)
        """
        self.rpc_endpoint = rpc_endpoint
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def connect(self) -> bool:
        """
        Создать HTTP сессию для подключения к RPC.
        
        Returns:
            True если подключение успешно
        """
        try:
            self.session = aiohttp.ClientSession()
            # Проверяем подключение через getHealth
            health = await self.get_health()
            return health == "ok"
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    async def close(self):
        """Закрыть HTTP сессию."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _make_rpc_call(self, method: str, params: list = None) -> Dict[str, Any]:
        """
        Выполнить RPC запрос к Solana.
        
        Args:
            method: Название RPC метода
            params: Параметры запроса
            
        Returns:
            Ответ от RPC сервера
            
        Raises:
            Exception: При ошибке запроса
        """
        if not self.session:
            raise Exception("Клиент не подключен. Вызовите connect() сначала.")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        
        try:
            async with self.session.post(
                self.rpc_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if "error" in result:
                    raise Exception(f"RPC ошибка: {result['error']}")
                
                return result.get("result")
                
        except Exception as e:
            raise Exception(f"Ошибка RPC запроса {method}: {e}")
    
    async def get_health(self) -> str:
        """
        Проверить здоровье RPC сервера.
        
        Returns:
            "ok" если сервер работает нормально
        """
        result = await self._make_rpc_call("getHealth")
        return result
    
    async def get_balance(self, pubkey: str) -> float:
        """
        Получить баланс кошелька в SOL.
        
        Args:
            pubkey: Публичный ключ кошелька (строка)
            
        Returns:
            Баланс в SOL
        """
        result = await self._make_rpc_call("getBalance", [pubkey])
        # Конвертируем lamports в SOL (1 SOL = 1_000_000_000 lamports)
        lamports = result.get("value", 0)
        return lamports / 1_000_000_000
    
    async def get_latest_blockhash(self) -> str:
        """
        Получить последний blockhash.
        
        Returns:
            Строка с blockhash
        """
        result = await self._make_rpc_call("getLatestBlockhash")
        return result.get("value", {}).get("blockhash", "")
    
    async def get_slot(self) -> int:
        """
        Получить текущий слот.
        
        Returns:
            Номер текущего слота
        """
        result = await self._make_rpc_call("getSlot")
        return result
    
    async def get_transaction_count(self) -> int:
        """
        Получить общее количество транзакций.
        
        Returns:
            Количество транзакций
        """
        result = await self._make_rpc_call("getTransactionCount")
        return result
    
    async def send_transaction(self, signed_transaction) -> Dict[str, Any]:
        """
        Отправить подписанную транзакцию.
        
        Args:
            signed_transaction: Подписанная транзакция
            
        Returns:
            Результат отправки с signature
        """
        try:
            # Сериализуем транзакцию в base58
            serialized = bytes(signed_transaction)
            import base58
            tx_base58 = base58.b58encode(serialized).decode('utf-8')
            
            result = await self._make_rpc_call("sendTransaction", [tx_base58])
            return {"success": True, "signature": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def confirm_transaction(self, signature: str) -> Dict[str, Any]:
        """
        Подтвердить транзакцию.
        
        Args:
            signature: Подпись транзакции
            
        Returns:
            Результат подтверждения
        """
        try:
            # Используем getSignatureStatuses для проверки статуса транзакции
            result = await self._make_rpc_call("getSignatureStatuses", [[signature]])
            
            if result and result.get('value') and len(result['value']) > 0:
                status = result['value'][0]
                if status is None:
                    return {"success": False, "error": "Транзакция не найдена"}
                
                # Проверяем статус подтверждения
                if status.get('confirmationStatus') in ['confirmed', 'finalized']:
                    if status.get('err') is None:
                        return {"success": True, "result": status}
                    else:
                        return {"success": False, "error": f"Транзакция завершилась с ошибкой: {status.get('err')}"}
                else:
                    return {"success": False, "error": f"Транзакция не подтверждена: {status.get('confirmationStatus', 'unknown')}"}
            else:
                return {"success": False, "error": "Не удалось получить статус транзакции"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


# Пример использования
async def main():
    """Пример использования SimpleClient."""
    client = SimpleClient("https://api.devnet.solana.com")
    
    try:
        # Подключаемся
        connected = await client.connect()
        print(f"Подключение: {'успешно' if connected else 'неудачно'}")
        
        if connected:
            # Проверяем здоровье
            health = await client.get_health()
            print(f"Здоровье RPC: {health}")
            
            # Получаем текущий слот
            slot = await client.get_slot()
            print(f"Текущий слот: {slot}")
            
            # Получаем blockhash
            blockhash = await client.get_latest_blockhash()
            print(f"Последний blockhash: {blockhash[:20]}...")
            
            # Проверяем баланс тестового адреса
            test_pubkey = "11111111111111111111111111111111"  # System Program
            balance = await client.get_balance(test_pubkey)
            print(f"Баланс {test_pubkey}: {balance} SOL")
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
