"""
Тест для SimpleClient - проверка подключения к Solana RPC без трат.
Все тесты используют devnet (бесплатно).
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.simple_client import SimpleClient


async def test_devnet_connection():
    """Тест подключения к devnet RPC."""
    print("🔌 Тестируем подключение к devnet...")
    
    client = SimpleClient("https://api.devnet.solana.com")
    
    try:
        # Тест подключения
        connected = await client.connect()
        print(f"   Подключение: {'✅ успешно' if connected else '❌ неудачно'}")
        
        if not connected:
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False
    finally:
        await client.close()


async def test_rpc_health():
    """Тест проверки здоровья RPC."""
    print("🏥 Тестируем здоровье RPC...")
    
    client = SimpleClient("https://api.devnet.solana.com")
    
    try:
        await client.connect()
        
        health = await client.get_health()
        print(f"   Здоровье RPC: {health}")
        
        if health == "ok":
            print("   ✅ RPC работает нормально")
            return True
        else:
            print(f"   ❌ RPC проблемы: {health}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка проверки здоровья: {e}")
        return False
    finally:
        await client.close()


async def test_get_slot():
    """Тест получения текущего слота."""
    print("🎰 Тестируем получение слота...")
    
    client = SimpleClient("https://api.devnet.solana.com")
    
    try:
        await client.connect()
        
        slot = await client.get_slot()
        print(f"   Текущий слот: {slot}")
        
        if isinstance(slot, int) and slot > 0:
            print("   ✅ Слот получен успешно")
            return True
        else:
            print(f"   ❌ Неверный слот: {slot}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка получения слота: {e}")
        return False
    finally:
        await client.close()


async def test_get_blockhash():
    """Тест получения blockhash."""
    print("🧱 Тестируем получение blockhash...")
    
    client = SimpleClient("https://api.devnet.solana.com")
    
    try:
        await client.connect()
        
        blockhash = await client.get_latest_blockhash()
        print(f"   Blockhash: {blockhash[:20]}...")
        
        if isinstance(blockhash, str) and len(blockhash) > 20:
            print("   ✅ Blockhash получен успешно")
            return True
        else:
            print(f"   ❌ Неверный blockhash: {blockhash}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка получения blockhash: {e}")
        return False
    finally:
        await client.close()


async def test_get_balance():
    """Тест получения баланса."""
    print("💰 Тестируем получение баланса...")
    
    client = SimpleClient("https://api.devnet.solana.com")
    
    try:
        await client.connect()
        
        # Тестируем с System Program (всегда существует)
        system_program = "11111111111111111111111111111111"
        balance = await client.get_balance(system_program)
        print(f"   Баланс System Program: {balance} SOL")
        
        if isinstance(balance, (int, float)) and balance >= 0:
            print("   ✅ Баланс получен успешно")
            return True
        else:
            print(f"   ❌ Неверный баланс: {balance}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка получения баланса: {e}")
        return False
    finally:
        await client.close()


async def test_transaction_count():
    """Тест получения количества транзакций."""
    print("📊 Тестируем получение количества транзакций...")
    
    client = SimpleClient("https://api.devnet.solana.com")
    
    try:
        await client.connect()
        
        tx_count = await client.get_transaction_count()
        print(f"   Количество транзакций: {tx_count}")
        
        if isinstance(tx_count, int) and tx_count > 0:
            print("   ✅ Количество транзакций получено успешно")
            return True
        else:
            print(f"   ❌ Неверное количество транзакций: {tx_count}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка получения количества транзакций: {e}")
        return False
    finally:
        await client.close()


async def test_invalid_endpoint():
    """Тест с неверным эндпоинтом."""
    print("🚫 Тестируем неверный эндпоинт...")
    
    client = SimpleClient("https://invalid-endpoint.com")
    
    try:
        connected = await client.connect()
        
        if not connected:
            print("   ✅ Правильно обработан неверный эндпоинт")
            return True
        else:
            print("   ❌ Неверный эндпоинт не был обнаружен")
            return False
            
    except Exception as e:
        print(f"   ✅ Ожидаемая ошибка: {e}")
        return True
    finally:
        await client.close()


async def run_all_tests():
    """Запустить все тесты."""
    print("🧪 ЗАПУСК ТЕСТОВ SimpleClient")
    print("=" * 50)
    
    tests = [
        ("Подключение к devnet", test_devnet_connection),
        ("Здоровье RPC", test_rpc_health),
        ("Получение слота", test_get_slot),
        ("Получение blockhash", test_get_blockhash),
        ("Получение баланса", test_get_balance),
        ("Количество транзакций", test_transaction_count),
        ("Неверный эндпоинт", test_invalid_endpoint),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Тест: {test_name}")
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"   ❌ Неожиданная ошибка: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно!")
    else:
        print(f"⚠️  {total - passed} тестов не прошли")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
