import asyncio
import websockets
import json
from typing import AsyncGenerator, Dict, Any, Optional

class MySolanaClient:
    """
    Базовый асинхронный клиент для взаимодействия с Solana RPC через WebSocket.
    """
    def __init__(self, rpc_wss_url: str):
        self.rpc_wss_url = rpc_wss_url
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None

    async def _connect(self):
        """Устанавливает WebSocket соединение."""
        if self._websocket is None or self._websocket.closed:
            print(f"Подключение к WebSocket: {self.rpc_wss_url}")
            self._websocket = await websockets.connect(self.rpc_wss_url)
            print("Соединение установлено.")

    async def _send_request(self, method: str, params: Any) -> Dict[str, Any]:
        """Отправляет RPC запрос и возвращает ответ."""
        await self._connect()
        request_id = 1 # Упрощенный ID для примера
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        await self._websocket.send(json.dumps(request))
        response = await self._websocket.recv()
        return json.loads(response)

    async def subscribe(self, method: str, params: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Подписывается на события и возвращает асинхронный генератор для получения данных.
        """
        await self._connect()
        request_id = 1 # Упрощенный ID для примера
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        await self._websocket.send(json.dumps(request))
        
        # Первый ответ будет содержать ID подписки
        subscription_response = json.loads(await self._websocket.recv())
        if "result" not in subscription_response:
            print(f"Ошибка подписки: {subscription_response}")
            raise Exception(f"Не удалось подписаться: {subscription_response}")
        
        print(f"Подписка успешна, ID: {subscription_response['result']}")

        while True:
            try:
                message = await self._websocket.recv()
                yield json.loads(message)
            except websockets.exceptions.ConnectionClosed:
                print("Соединение WebSocket закрыто, переподключаемся...")
                await self._connect() # Попытка переподключения
                # После переподключения нужно повторно подписаться, но для простоты этого примера
                # мы просто продолжим получать сообщения. В реальном приложении нужно 
                # повторно отправить запрос subscribe.
            except Exception as e:
                print(f"Ошибка при получении сообщения: {e}")
                await asyncio.sleep(1) # Небольшая задержка перед следующей попыткой
    
    async def close(self):
        """Закрывает WebSocket соединение."""
        if self._websocket and not self._websocket.closed:
            await self._websocket.close()
            print("Соединение WebSocket закрыто.")

async def main():
    # Пример использования клиента для blockSubscribe
    # Замените на реальный WSS RPC endpoint Solana
    WSS_URL = "ws://localhost:8900/" # Пример: "wss://api.devnet.solana.com"
    client = MySolanaClient(WSS_URL)

    try:
        print("Начинаем подписку на блоки...")
        async for block in client.subscribe("blockSubscribe", [
            {"commitment": "confirmed"},
            {"encoding": "json", "transactionDetails": "full", "rewards": False, "maxSupportedTransactionVersion": 0}
        ]):
            if block and "params" in block and "result" in block["params"] and "value" in block["params"]["result"]:
                block_data = block["params"]["result"]["value"]
                print(f"Получен блок: {block_data['blockHeight']}")
                # print(json.dumps(block_data, indent=2)) # Раскомментируйте для полного просмотра блока
            else:
                print(f"Получено сообщение, не являющееся блоком: {block}")
    except Exception as e:
        print(f"Ошибка в основном цикле подписки: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
