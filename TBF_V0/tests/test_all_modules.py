#!/usr/bin/env python3
"""
Простой тест всех модулей TBF_V0 без внешних зависимостей.
"""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_module_imports():
    """Тестируем импорты всех модулей."""
    print("🧪 ТЕСТИРОВАНИЕ ИМПОРТОВ МОДУЛЕЙ TBF_V0")
    print("=" * 50)
    
    modules = [
        ("SimpleClient", "TBF_V0.core.simple_client"),
        ("SimpleWallet", "TBF_V0.core.simple_wallet"),
        ("EventParser", "TBF_V0.pumpfun.event_parser"),
        ("CurveManager", "TBF_V0.pumpfun.curve_manager"),
        ("AddressProvider", "TBF_V0.pumpfun.address_provider"),
        ("SimpleBlockListener", "TBF_V0.monitoring.simple_block_listener")
    ]
    
    results = []
    
    for name, module_path in modules:
        try:
            __import__(module_path)
            print(f"✅ {name:<18} - импорт успешен")
            results.append((name, True, None))
        except Exception as e:
            print(f"❌ {name:<18} - ошибка: {str(e)[:50]}")
            results.append((name, False, str(e)))
    
    return results


def test_basic_functionality():
    """Тестируем базовую функциональность модулей."""
    print("\n🔧 ТЕСТИРОВАНИЕ БАЗОВОЙ ФУНКЦИОНАЛЬНОСТИ")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 0
    
    # Тест SimpleBlockListener
    try:
        from TBF_V0.monitoring.simple_block_listener import SimpleBlockListener
        
        listener = SimpleBlockListener(wss_endpoint="wss://test.endpoint")
        
        # Проверяем атрибуты
        assert listener.wss_endpoint == "wss://test.endpoint"
        assert hasattr(listener, 'is_listening')
        assert listener.is_listening == False
        
        # Проверяем методы
        assert hasattr(listener, 'start_listening')
        assert hasattr(listener, 'stop_listening')
        assert hasattr(listener, '_decode_create_instruction')
        
        print("✅ SimpleBlockListener - базовая функциональность работает")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ SimpleBlockListener - ошибка: {e}")
    
    tests_total += 1
    
    # Тест CurveManager
    try:
        from TBF_V0.pumpfun.curve_manager import CurveManager, CurveState
        
        # Создаем тестовое состояние кривой
        curve_state = CurveState(
            virtual_token_reserves=1000000000000,  # 1M токенов
            virtual_sol_reserves=30000000000,      # 30 SOL
            real_token_reserves=800000000000,      # 800K токенов
            real_sol_reserves=0,
            complete=False
        )
        
        manager = CurveManager()
        
        # Тест расчета цены покупки
        sol_amount = 1.0  # 1 SOL
        tokens_out, price_per_token, new_state = manager.calculate_buy_price(sol_amount, curve_state)
        assert tokens_out > 0
        assert price_per_token > 0
        
        print("✅ CurveManager - базовая функциональность работает")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ CurveManager - ошибка: {e}")
    
    tests_total += 1
    
    # Тест AddressProvider
    try:
        from TBF_V0.pumpfun.address_provider import AddressProvider
        
        provider = AddressProvider()
        
        # Тест генерации адресов
        from solders.pubkey import Pubkey
        mint_pubkey = Pubkey.from_string("So11111111111111111111111111111111111111112")
        bonding_curve, _ = provider.get_bonding_curve_address(mint_pubkey)
        metadata, _ = provider.get_metadata_address(mint_pubkey)
        
        assert bonding_curve is not None
        assert metadata is not None
        
        print("✅ AddressProvider - базовая функциональность работает")
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ AddressProvider - ошибка: {e}")
    
    tests_total += 1
    
    return tests_passed, tests_total


def main():
    """Главная функция тестирования."""
    print("🚀 ЗАПУСК ПОЛНОГО ТЕСТИРОВАНИЯ TBF_V0")
    print("=" * 60)
    
    # Тест импортов
    import_results = test_module_imports()
    
    # Подсчет успешных импортов
    successful_imports = sum(1 for _, success, _ in import_results if success)
    total_modules = len(import_results)
    
    print(f"\nИмпорты: {successful_imports}/{total_modules} модулей успешно")
    
    # Тест функциональности
    if successful_imports > 0:
        tests_passed, tests_total = test_basic_functionality()
        print(f"\nФункциональность: {tests_passed}/{tests_total} тестов прошли")
    else:
        tests_passed, tests_total = 0, 0
        print("\nФункциональность: пропущено из-за ошибок импорта")
    
    # Итоговый результат
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print("=" * 60)
    
    if successful_imports == total_modules and tests_passed == tests_total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Все модули TBF_V0 работают корректно")
        return True
    elif successful_imports > 0:
        print("⚠️ ЧАСТИЧНЫЙ УСПЕХ")
        print(f"✅ Импорты: {successful_imports}/{total_modules}")
        print(f"✅ Функциональность: {tests_passed}/{tests_total}")
        return False
    else:
        print("💥 КРИТИЧЕСКИЕ ОШИБКИ")
        print("❌ Не удалось импортировать ни одного модуля")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
