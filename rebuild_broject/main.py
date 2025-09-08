import asyncio
import os
from dotenv import load_dotenv
from typing import Dict, Any

from .block_listener import start_block_listener
from .simple_trader import handle_new_token_for_trading

load_dotenv()

async def main():
    print("Starting the Pump.fun simple bot...")
    
    # Здесь мы могли бы загрузить RPC_ENDPOINT и PRIVATE_KEY для simple_trader,
    # но пока мы просто запускаем слушатель.

    try:
        await start_block_listener(handle_new_token_for_trading)
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"An unhandled error occurred in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
