#!/usr/bin/env python3
"""
Скрипт для проверки баланса токенов после покупки.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.simple_client import SimpleClient
from core.simple_wallet import SimpleWallet
from pumpfun.address_provider import AddressProvider

async def check_token_balance():
    """Проверяет баланс токенов в кошельке"""
    
    # Конфигурация
    RPC_ENDPOINT = "https://mainnet.helius-rpc.com/?api-key=e6fa031e-699e-49ed-9672-4582bdb4950d"
    PRIVATE_KEY = "S8AmRgsyBPMqQL8BkY8PJoo7Gxj31HZZzpNWhfzUXwEkdQu56AJT9LSixAqGzAcR2b1W9XnuRPykZeZ9A6AXRRv"
    TOKEN_MINT = "r8VCbeoXdsQ7RcXT9DF3CnJ2Fqdx9uNWywsV8Wepump"
    
    print("🔍 ПРОВЕРКА БАЛАНСА ТОКЕНОВ")
    print("=" * 50)
    
    try:
        # Инициализация клиента и кошелька
        client = SimpleClient(RPC_ENDPOINT)
        await client.connect()
        
        wallet = SimpleWallet()
        wallet.load_from_private_key(PRIVATE_KEY)
        
        print(f"👛 Кошелек: {wallet.get_public_key()}")
        print(f"🪙 Токен: {TOKEN_MINT}")
        
        # Получение SOL баланса
        sol_balance = await client.get_balance(str(wallet.get_public_key()))
        print(f"💰 SOL баланс: {sol_balance} SOL")
        
        # Получение адреса токен-аккаунта
        address_provider = AddressProvider()
        user_ata = address_provider.get_associated_token_address(
            str(wallet.get_public_key()),
            TOKEN_MINT
        )
        
        print(f"📍 User ATA: {user_ata}")
        
        # Проверка баланса токенов через RPC
        try:
            token_balance_response = await client._make_rpc_call(
                "getTokenAccountBalance", 
                [str(user_ata)]
            )
            print(f"🎯 Ответ RPC: {token_balance_response}")
            
            if token_balance_response:
                token_amount = token_balance_response.get('value', {}).get('amount', '0')
                decimals = token_balance_response.get('value', {}).get('decimals', 6)
                ui_amount = int(token_amount) / (10 ** decimals)
                
                print(f"🪙 Баланс токенов: {ui_amount} ({token_amount} raw)")
                
                if ui_amount > 0:
                    print("✅ ТОКЕНЫ НАЙДЕНЫ! Покупка была успешной!")
                else:
                    print("❌ Токены не найдены. Покупка не прошла.")
            else:
                print("❌ Не удалось получить баланс токенов")
                
        except Exception as e:
            print(f"⚠️  Ошибка проверки токенов: {e}")
            print("💡 Возможно, токен-аккаунт еще не создан")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(check_token_balance())
