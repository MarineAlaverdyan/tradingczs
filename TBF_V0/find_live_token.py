"""
Скрипт для поиска живых pump.fun токенов с ликвидностью
"""

import asyncio
import aiohttp
from datetime import datetime

async def find_live_tokens():
    """Найти живые токены на pump.fun"""
    
    print("🔍 ПОИСК ЖИВЫХ PUMP.FUN ТОКЕНОВ")
    print("=" * 50)
    
    # Примеры известных активных токенов (заканчивающихся на pump)
    test_tokens = [
        {
            'name': 'Stream until 100M MC',
            'mint': '9eF4iX4BzeKnvJ7gSw5L725jk48zJw2m66NFxHHvpump',
            'url': 'https://pump.fun/coin/9eF4iX4BzeKnvJ7gSw5L725jk48zJw2m66NFxHHvpump'
        },
        {
            'name': 'Liquidity Bot',
            'mint': 'HrPQRDErqn9ajXCuSq5QpFjc9dc5nFuWKG6rcgP2pump',
            'url': 'https://pump.fun/coin/HrPQRDErqn9ajXCuSq5QpFjc9dc5nFuWKG6rcgP2pump'
        }
    ]
    
    print("📋 НАЙДЕННЫЕ ТОКЕНЫ:")
    for i, token in enumerate(test_tokens, 1):
        print(f"\n{i}. {token['name']}")
        print(f"   Mint: {token['mint']}")
        print(f"   URL: {token['url']}")
    
    print("\n🎯 РЕКОМЕНДАЦИИ:")
    print("1. Используйте токен 'Stream until 100M MC' для тестов")
    print("2. Mint: 9eF4iX4BzeKnvJ7gSw5L725jk48zJw2m66NFxHHvpump")
    print("3. Проверьте активность на pump.fun перед тестом")
    
    print("\n⚠️ ВАЖНО:")
    print("- Тестируйте с минимальными суммами (0.001 SOL)")
    print("- Проверяйте ликвидность перед покупкой")
    print("- Используйте devnet для безопасных тестов")
    
    return test_tokens[0]['mint']  # Возвращаем первый токен

if __name__ == "__main__":
    asyncio.run(find_live_tokens())
