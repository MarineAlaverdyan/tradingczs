#!/usr/bin/env python3
"""
Простой тест покупки с выводом в консоль для отладки.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.simple_client import SimpleClient
from core.simple_wallet import SimpleWallet
from trading.simple_buyer import SimpleBuyer
from core.priority_fee.manager import PriorityFeeManager
from pumpfun.instruction_builder import InstructionBuilder
from core.token_info import TokenInfo

async def test_console_buy():
    """Тест покупки с выводом в консоль"""
    
    print("🔬 ТЕСТ ПОКУПКИ С КОНСОЛЬНЫМ ВЫВОДОМ")
    print("=" * 50)
    
    # Конфигурация
    RPC_ENDPOINT = "https://mainnet.helius-rpc.com/?api-key=e6fa031e-699e-49ed-9672-4582bdb4950d"
    PRIVATE_KEY = "S8AmRgsyBPMqQL8BkY8PJoo7Gxj31HZZzpNWhfzUXwEkdQu56AJT9LSixAqGzAcR2b1W9XnuRPykZeZ9A6AXRRv"
    
    # Данные токена
    listener_data = {
        'name': 'buy up',
        'symbol': 'buy up', 
        'uri': 'https://ipfs.io/ipfs/Qmei5WUshDFeLJi5k8twgJZdKLC8g232r5RyjscjnTtjiT',
        'mint': 'r8VCbeoXdsQ7RcXT9DF3CnJ2Fqdx9uNWywsV8Wepump',
        'bondingCurve': 'AuUmsyXSAzKz4mTSEDX719rQvNpkz47rjbTn7QhU94SC',
        'associatedBondingCurve': 'CggVUQJEU2HWQRvMDAEiozNkPqKLMr5Mxc6zQPjnyrbz',
        'user': '6pNDtUKGjbVVQLq8sQwdZW6heMuHAd6F5VpNSWfQvyfH'
    }
    
    try:
        print("🔧 Инициализация компонентов...")
        
        # Клиент
        client = SimpleClient(RPC_ENDPOINT)
        await client.connect()
        print("✅ Клиент подключен")
        
        # Кошелек
        wallet = SimpleWallet()
        wallet.load_from_private_key(PRIVATE_KEY)
        print(f"✅ Кошелек загружен: {wallet.get_public_key()}")
        
        # Баланс
        balance = await client.get_balance(str(wallet.get_public_key()))
        print(f"💰 Баланс: {balance} SOL")
        
        # Компоненты торговли
        from pumpfun.address_provider import AddressProvider
        
        priority_fee_manager = PriorityFeeManager(client)
        instruction_builder = InstructionBuilder()
        address_provider = AddressProvider()
        buyer = SimpleBuyer(client, wallet, address_provider, instruction_builder, priority_fee_manager)
        print("✅ Торговые компоненты инициализированы")
        
        # TokenInfo
        token_info = TokenInfo.from_listener_data(listener_data)
        print(f"✅ TokenInfo создан: {token_info.name}")
        
        print("\n🛒 НАЧИНАЕМ ПОКУПКУ...")
        print("-" * 30)
        
        # Покупка
        result = await buyer.buy_token(
            token_info=token_info,
            sol_amount=0.001,
            slippage_percent=15.0
        )
        
        print("\n📊 РЕЗУЛЬТАТ ПОКУПКИ:")
        print("-" * 30)
        print(f"Success: {result.success}")
        print(f"Error: {result.error_message}")
        print(f"Signature: {result.transaction_signature}")
        print(f"Tokens: {result.tokens_received}")
        print(f"SOL spent: {result.sol_spent}")
        
        if result.success:
            print("\n🎉 ПОКУПКА УСПЕШНА!")
        else:
            print("\n❌ ПОКУПКА НЕУДАЧНА!")
        
        await client.close()
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_console_buy())
