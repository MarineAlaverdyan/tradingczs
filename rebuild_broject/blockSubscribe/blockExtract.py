import asyncio
import websockets
import json
import os

API_KEY = "e6fa031e-699e-49ed-9672-4582bdb4950d"
WS_URL = "wss://solana-mainnet.core.chainstack.com/9a6c42741789e5c382251d7fe4589435"

async def subscribe():
    async with websockets.connect(WS_URL) as ws:
        print("✅ Connected to Helius WS")

        subscribe_req = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "blockSubscribe",
            "params": [
                {
                    "mentionsAccountOrProgram": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
                },
                {
                    "commitment": "confirmed",
                    "encoding": "base64",
                    "transactionDetails": "full",
                    "maxSupportedTransactionVersion": 0,
                    "showRewards": True
                }
            ]
        }

        await ws.send(json.dumps(subscribe_req))

        while True:
            try:
                message = await ws.recv()
                data = json.loads(message)
                print("📩", json.dumps(data, indent=2))

                with open("solana_blocks.json", "a") as f:
                    f.write(json.dumps(data, indent=2) + "\n")

            except websockets.exceptions.ConnectionClosed as e:
                print(f"❌ WS Closed: {e}")
                break
            except Exception as e:
                print(f"❌ WS Error: {e}")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(subscribe())