import asyncio
import base64
import json
import os
import struct

import base58
import websockets
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

load_dotenv()

WSS_ENDPOINT = os.environ.get("SOLANA_NODE_WSS_ENDPOINT")
PUMP_PROGRAM_ID = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")

from typing import Dict, Any, Callable, Awaitable, Optional
from .my_client import MySolanaClient
from .my_token_parser import TokenDataParser

class MyBlockListener:
    """
    Слушатель блоков Solana, который использует MySolanaClient для подписки
    и MyTokenDataParser для извлечения информации о токенах.
    """
    def __init__(
        self, 
        client: MySolanaClient, 
        token_parser: TokenDataParser,
        on_new_token_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    ):
        self.client = client
        self.token_parser = token_parser
        self.on_new_token_callback = on_new_token_callback

    async def start_listening(self):
        print("[MyBlockListener] Начинаем прослушивание блоков...")
        try:
            # Параметры для blockSubscribe
            # "transactionDetails": "full" - крайне важно для получения логов транзакций
            subscription_params = [
                {"commitment": "confirmed"},
                {"encoding": "json", "transactionDetails": "full", "rewards": False, "maxSupportedTransactionVersion": 0}
            ]

            async for block_message in self.client.subscribe("blockSubscribe", subscription_params):
                if block_message and "params" in block_message and "result" in block_message["params"] and "value" in block_message["params"]["result"]:
                    block_data = block_message["params"]["result"]["value"]
                    # print(f"[MyBlockListener] Получен блок: {block_data.get('blockHeight', 'N/A')}")

                    if "transactions" in block_data and block_data["transactions"] is not None:
                        for tx_info in block_data["transactions"]:
                            if tx_info and "meta" in tx_info and tx_info["meta"] and "logMessages" in tx_info["meta"] and tx_info["meta"]["logMessages"] is not None:
                                logs = tx_info["meta"]["logMessages"]
                                token_data = self.token_parser.parse_transaction_logs(logs)
                                
                                if token_data:
                                    print(f"[MyBlockListener] === Обнаружен НОВЫЙ ТОКЕН в блоке {block_data.get('blockHeight', 'N/A')} ===")
                                    print(f"[MyBlockListener] Данные токена: {token_data}")
                                    if self.on_new_token_callback:
                                        await self.on_new_token_callback(token_data)

                else:
                    print(f"[MyBlockListener] Получено сообщение без данных блока: {block_message}")
        except Exception as e:
            print(f"[MyBlockListener] Критическая ошибка при прослушивании: {e}")
            # В реальном приложении здесь может быть логика для повторного подключения или graceful shutdown

async def handle_new_token(token_info: Dict[str, Any]):
    """
    Пример функции обратного вызова для обработки новых токенов.
    В реальном боте здесь будет запущена логика покупки.
    """
    print(f"[handle_new_token] Получено для обработки: {token_info["""name"""]}-{token_info["""symbol"""]}")
    # Здесь можно добавить логику для UniversalTrader
    await asyncio.sleep(0.1) # Имитация асинхронной обработки

async def main():
    WSS_URL = "wss://api.devnet.solana.com" # Используйте Devnet или другой публичный RPC
    # Для локального тестирования можно использовать "ws://localhost:8900/"
    
    client = MySolanaClient(WSS_URL)
    token_parser = TokenDataParser()
    listener = MyBlockListener(client, token_parser, on_new_token_callback=handle_new_token)

    try:
        await listener.start_listening()
    except KeyboardInterrupt:
        print("[MyBlockListener] Прослушивание остановлено пользователем.")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
