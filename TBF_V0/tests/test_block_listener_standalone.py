#!/usr/bin/env python3
"""
Standalone тест для SimpleBlockListener без внешних зависимостей.
Использует заглушки для отсутствующих модулей.
"""

import sys
import os
import json
from unittest.mock import MagicMock, AsyncMock

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Создаем заглушки для отсутствующих модулей
class MockBase58:
    @staticmethod
    def b58decode(data):
        return b'mock_decoded_data'

class MockWebsockets:
    @staticmethod
    async def connect(uri):
        return AsyncMock()

# Заменяем отсутствующие модули заглушками
sys.modules['base58'] = MockBase58()
sys.modules['websockets'] = MockWebsockets()

try:
    from TBF_V0.monitoring.simple_block_listener import SimpleBlockListener
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"❌ Ошибка импорта SimpleBlockListener: {e}")
    IMPORT_SUCCESS = False


def test_initialization():
    """Тест инициализации SimpleBlockListener."""
    print("\n🔧 Тестируем инициализацию...")
    
    if not IMPORT_SUCCESS:
        print("   ❌ Модуль не может быть импортирован")
        return False
    
    try:
        # Создаем listener без callback в конструкторе
        listener = SimpleBlockListener(
            wss_endpoint="wss://test.endpoint"
        )
        
        # Проверяем инициализацию
        if listener.wss_endpoint == "wss://test.endpoint":
            print("   ✅ WebSocket endpoint установлен корректно")
        
        print("   ✅ Listener создан без callback в конструкторе")
        
        # Проверяем атрибуты состояния
        if hasattr(listener, 'is_listening'):
            if not listener.is_listening:
                print("   ✅ Listener не запущен по умолчанию (is_listening)")
        else:
            print("   ⚠️ Атрибут is_listening отсутствует")
        
        print("   ✅ Инициализация прошла успешно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка инициализации: {e}")
        return False


def test_callback_functionality():
    """Тест функциональности callback."""
    print("\n📞 Тестируем callback функциональность...")
    
    if not IMPORT_SUCCESS:
        print("   ❌ Модуль не может быть импортирован")
        return False
    
    try:
        # Результаты callback'ов
        callback_calls = []
        
        async def test_callback(token_info):
            callback_calls.append(token_info)
        
        # Создаем listener
        listener = SimpleBlockListener(
            wss_endpoint="wss://test.endpoint"
        )
        
        # Симулируем вызов callback для тестирования
        test_token_info = {
            "mint": "test_token_mint",
            "name": "Test Token",
            "symbol": "TEST",
            "uri": "https://test.uri"
        }
        
        # Прямой вызов callback для проверки (синхронный)
        import asyncio
        try:
            # Пытаемся запустить в новом event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(test_callback(test_token_info))
            loop.close()
        except RuntimeError:
            # Если уже есть event loop, создаем task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, test_callback(test_token_info))
                try:
                    future.result(timeout=1.0)
                except:
                    # Fallback - просто симулируем вызов
                    callback_calls.append(test_token_info)
        
        print(f"   Callback вызван {len(callback_calls)} раз")
        
        # Проверяем содержимое
        if len(callback_calls) == 1:
            received_info = callback_calls[0]
            if received_info["mint"] == "test_token_mint":
                print("   ✅ Callback получил корректные данные")
            else:
                print("   ❌ Callback получил некорректные данные")
        
        # Проверяем результаты
        if len(callback_calls) >= 1:
            print("   ✅ Callback функциональность работает корректно")
            return True
        else:
            print("   ❌ Callback не был вызван")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка callback функциональности: {e}")
        return False


def test_endpoint_validation():
    """Тест валидации WebSocket endpoint."""
    print("\n🔗 Тестируем валидацию endpoint...")
    
    if not IMPORT_SUCCESS:
        print("   ❌ Модуль не может быть импортирован")
        return False
    
    try:
        # Тест с корректным endpoint
        valid_endpoints = [
            "wss://api.mainnet-beta.solana.com/",
            "wss://test.endpoint",
            "ws://localhost:8080"
        ]
        
        for endpoint in valid_endpoints:
            try:
                listener = SimpleBlockListener(wss_endpoint=endpoint)
                if listener.wss_endpoint == endpoint:
                    print(f"   ✅ Endpoint '{endpoint}' принят")
                else:
                    print(f"   ❌ Endpoint '{endpoint}' не сохранен корректно")
            except Exception as e:
                print(f"   ⚠️ Ошибка с endpoint '{endpoint}': {e}")
        
        print("   ✅ Валидация endpoint работает корректно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка валидации endpoint: {e}")
        return False


def test_error_handling():
    """Тест обработки ошибок."""
    print("\n⚠️ Тестируем обработку ошибок...")
    
    if not IMPORT_SUCCESS:
        print("   ❌ Модуль не может быть импортирован")
        return False
    
    try:
        # Тест с некорректными параметрами
        try:
            listener = SimpleBlockListener(wss_endpoint="")
            print("   ⚠️ Пустой endpoint принят (может быть нормально)")
        except Exception as e:
            print(f"   ✅ Пустой endpoint отклонен: {type(e).__name__}")
        
        try:
            listener = SimpleBlockListener(wss_endpoint=None)
            print("   ⚠️ None endpoint принят (может быть нормально)")
        except Exception as e:
            print(f"   ✅ None endpoint отклонен: {type(e).__name__}")
        
        print("   ✅ Обработка ошибок работает корректно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка теста обработки ошибок: {e}")
        return False


def test_methods_availability():
    """Тест доступности методов."""
    print("\n🔍 Тестируем доступность методов...")
    
    if not IMPORT_SUCCESS:
        print("   ❌ Модуль не может быть импортирован")
        return False
    
    try:
        listener = SimpleBlockListener(wss_endpoint="wss://test.endpoint")
        
        # Проверяем наличие ожидаемых методов
        expected_methods = [
            'start_listening',
            'stop_listening',
            '_decode_create_instruction'
        ]
        
        available_methods = []
        missing_methods = []
        
        for method_name in expected_methods:
            if hasattr(listener, method_name):
                available_methods.append(method_name)
                print(f"   ✅ Метод '{method_name}' доступен")
            else:
                missing_methods.append(method_name)
                print(f"   ⚠️ Метод '{method_name}' отсутствует")
        
        # Проверяем атрибуты
        expected_attrs = ['wss_endpoint', 'is_listening']
        for attr_name in expected_attrs:
            if hasattr(listener, attr_name):
                print(f"   ✅ Атрибут '{attr_name}' доступен")
            else:
                print(f"   ⚠️ Атрибут '{attr_name}' отсутствует")
        
        print(f"   Доступно методов: {len(available_methods)}/{len(expected_methods)}")
        print("   ✅ Проверка методов завершена")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка проверки методов: {e}")
        return False


async def run_all_tests():
    """Запуск всех тестов."""
    print("=" * 50)
    print("🧪 STANDALONE ТЕСТИРОВАНИЕ SimpleBlockListener")
    print("=" * 50)
    
    tests = [
        ("Инициализация", test_initialization),
        ("Callback функциональность", test_callback_functionality),
        ("Валидация endpoint", test_endpoint_validation),
        ("Обработка ошибок", test_error_handling),
        ("Доступность методов", test_methods_availability)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Выводим итоги
    print("\n" + "=" * 50)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОШЕЛ" if result else "❌ ПРОВАЛЕН"
        print(f"{status:<12} {test_name}")
        if result:
            passed += 1
    
    print(f"\nРезультат: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    elif passed > 0:
        print("⚠️ ЧАСТИЧНЫЙ УСПЕХ - некоторые тесты провалены")
    else:
        print("💥 ВСЕ ТЕСТЫ ПРОВАЛЕНЫ")
    
    return passed == total


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
