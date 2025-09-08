import os
import asyncio
import json
import httpx
from typing import Optional, Any

from solders.transaction import VersionedTransaction
from solders.signature import Signature
from solders.hash import Hash

RPC_ENDPOINT = os.environ.get("SOLANA_NODE_RPC_ENDPOINT")

async def get_latest_blockhash() -> Optional[Hash]:
    """Получает последний хэш блока из Solana RPC."""
    if not RPC_ENDPOINT:
        print("Ошибка: SOLANA_NODE_RPC_ENDPOINT не установлен в переменных окружения.")
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RPC_ENDPOINT,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getLatestBlockhash",
                    "params": [
                        {
                            "commitment": "finalized"
                        }
                    ]
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if "result" in data and "value" in data["result"] and "blockhash" in data["result"]["value"]:
                return Hash.from_string(data["result"]["value"]["blockhash"])
            else:
                print(f"Ошибка получения blockhash: {data.get("error", "Неизвестная ошибка")}")
                return None
    except httpx.HTTPStatusError as e:
        print(f"Ошибка HTTP при получении blockhash: {e}")
        return None
    except httpx.RequestError as e:
        print(f"Ошибка запроса при получении blockhash: {e}")
        return None
    except Exception as e:
        print(f"Неизвестная ошибка при получении blockhash: {e}")
        return None

async def send_and_confirm_transaction(transaction: VersionedTransaction) -> Optional[Signature]:
    """Отправляет транзакцию в Solana и ожидает подтверждения."""
    if not RPC_ENDPOINT:
        print("Ошибка: SOLANA_NODE_RPC_ENDPOINT не установлен в переменных окружения.")
        return None

    try:
        async with httpx.AsyncClient() as client:
            # Отправка транзакции
            encoded_tx = transaction.to_bytes().hex()
            send_response = await client.post(
                RPC_ENDPOINT,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "sendTransaction",
                    "params": [
                        encoded_tx,
                        {"encoding": "base64", "skipPreflight": True, "preflightCommitment": "processed"}
                    ]
                },
                timeout=30
            )
            send_response.raise_for_status()
            send_data = send_response.json()

            if "result" in send_data:
                signature = Signature.from_string(send_data["result"])
                print(f"Транзакция отправлена. Signature: {signature}")
                
                # Ожидание подтверждения (упрощенный вариант, в реальном боте сложнее)
                # Здесь можно использовать getSignatureStatuses или blockSubscribe для более надежного подтверждения
                for _ in range(10): # Попытка 10 раз с задержкой
                    await asyncio.sleep(2)
                    status_response = await client.post(
                        RPC_ENDPOINT,
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getSignatureStatuses",
                            "params": [[str(signature)], {"searchTransactionHistory": True}]
                        },
                        timeout=10
                    )
                    status_response.raise_for_status()
                    status_data = status_response.json()

                    if "result" in status_data and "value" in status_data["result"] and status_data["result"]["value"]:
                        status = status_data["result"]["value"][0]
                        if status and status.get("confirmationStatus") == "finalized":
                            print(f"Транзакция {signature} подтверждена.")
                            return signature
                        elif status and status.get("err"): # Проверяем наличие ошибки
                            print(f"Транзакция {signature} завершилась с ошибкой: {status.get("err")}")
                            return None
                
                print(f"Транзакция {signature} не подтверждена в течение установленного времени.")
                return None
            else:
                print(f"Ошибка отправки транзакции: {send_data.get("error", "Неизвестная ошибка")}")
                return None
    except httpx.HTTPStatusError as e:
        print(f"Ошибка HTTP при отправке/подтверждении транзакции: {e}")
        return None
    except httpx.RequestError as e:
        print(f"Ошибка запроса при отправке/подтверждении транзакции: {e}")
        return None
    except Exception as e:
        print(f"Неизвестная ошибка при отправке/подтверждении транзакции: {e}")
        return None

