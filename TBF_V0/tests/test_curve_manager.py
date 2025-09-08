"""
Тест для CurveManager - проверка математики бондинговой кривой без трат.
Тестирует расчеты с тестовыми данными.
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Импортируем напрямую CurveManager (без зависимостей)
import importlib.util
curve_manager_path = os.path.join(os.path.dirname(__file__), '..', 'pumpfun', 'curve_manager.py')
spec = importlib.util.spec_from_file_location("curve_manager", curve_manager_path)
curve_manager_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(curve_manager_module)
CurveManager = curve_manager_module.CurveManager


def test_price_calculations():
    """Тест расчета цен покупки и продажи."""
    print("💰 Тестируем расчет цен...")
    
    try:
        # Тестовые параметры кривой
        virtual_sol_reserves = 30_000_000_000  # 30 SOL в lamports
        virtual_token_reserves = 1_073_000_000_000_000  # 1.073B токенов
        real_sol_reserves = 0
        real_token_reserves = 1_000_000_000_000_000  # 1B токенов
        
        # Создаем CurveManager
        curve = CurveManager(
            virtual_sol_reserves=virtual_sol_reserves,
            virtual_token_reserves=virtual_token_reserves,
            real_sol_reserves=real_sol_reserves,
            real_token_reserves=real_token_reserves
        )
        
        # Тест покупки 1 SOL
        sol_amount = 1_000_000_000  # 1 SOL в lamports
        tokens_out = curve.calculate_buy_price(sol_amount)
        
        print(f"   Покупка за 1 SOL: {tokens_out:,} токенов")
        
        # Тест продажи полученных токенов
        sol_out = curve.calculate_sell_price(tokens_out)
        
        print(f"   Продажа {tokens_out:,} токенов: {sol_out:,} lamports")
        
        # Проверяем, что получили меньше SOL (из-за слиппеджа)
        if tokens_out > 0 and sol_out > 0 and sol_out < sol_amount:
            print("   ✅ Расчеты цен работают корректно (есть слиппедж)")
            return True
        else:
            print(f"   ❌ Проблема с расчетами: покупка={tokens_out}, продажа={sol_out}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка расчета цен: {e}")
        return False


def test_current_price():
    """Тест расчета текущей цены токена."""
    print("\n📈 Тестируем расчет текущей цены...")
    
    try:
        # Начальные параметры
        curve = CurveManager(
            virtual_sol_reserves=30_000_000_000,
            virtual_token_reserves=1_073_000_000_000_000,
            real_sol_reserves=0,
            real_token_reserves=1_000_000_000_000_000
        )
        
        # Текущая цена
        current_price = curve.get_current_price()
        print(f"   Текущая цена: {current_price:.12f} SOL за токен")
        
        # Цена должна быть положительной и разумной
        if 0 < current_price < 1:
            print("   ✅ Текущая цена в разумных пределах")
            return True
        else:
            print(f"   ❌ Неразумная цена: {current_price}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка расчета текущей цены: {e}")
        return False


def test_market_cap():
    """Тест расчета рыночной капитализации."""
    print("\n🏦 Тестируем расчет рыночной капитализации...")
    
    try:
        curve = CurveManager(
            virtual_sol_reserves=30_000_000_000,
            virtual_token_reserves=1_073_000_000_000_000,
            real_sol_reserves=5_000_000_000,  # 5 SOL уже в пуле
            real_token_reserves=950_000_000_000_000  # 950M токенов осталось
        )
        
        # Рыночная капитализация
        market_cap = curve.get_market_cap()
        print(f"   Рыночная капитализация: {market_cap:.6f} SOL")
        
        # Market cap должен быть положительным
        if market_cap > 0:
            print("   ✅ Рыночная капитализация рассчитана корректно")
            return True
        else:
            print(f"   ❌ Неверная рыночная капитализация: {market_cap}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка расчета market cap: {e}")
        return False


def test_migration_progress():
    """Тест расчета прогресса до миграции."""
    print("\n🚀 Тестируем расчет прогресса миграции...")
    
    try:
        # Тест в начале (0% прогресс)
        curve_start = CurveManager(
            virtual_sol_reserves=30_000_000_000,
            virtual_token_reserves=1_073_000_000_000_000,
            real_sol_reserves=0,
            real_token_reserves=1_000_000_000_000_000
        )
        
        progress_start = curve_start.get_migration_progress()
        print(f"   Прогресс в начале: {progress_start:.2%}")
        
        # Тест в середине (~50% прогресс)
        curve_middle = CurveManager(
            virtual_sol_reserves=30_000_000_000,
            virtual_token_reserves=1_073_000_000_000_000,
            real_sol_reserves=40_000_000_000,  # 40 SOL
            real_token_reserves=500_000_000_000_000  # 500M токенов
        )
        
        progress_middle = curve_middle.get_migration_progress()
        print(f"   Прогресс в середине: {progress_middle:.2%}")
        
        # Тест почти в конце (~90% прогресс)
        curve_end = CurveManager(
            virtual_sol_reserves=30_000_000_000,
            virtual_token_reserves=1_073_000_000_000_000,
            real_sol_reserves=80_000_000_000,  # 80 SOL
            real_token_reserves=100_000_000_000_000  # 100M токенов
        )
        
        progress_end = curve_end.get_migration_progress()
        print(f"   Прогресс в конце: {progress_end:.2%}")
        
        # Проверяем логику прогресса
        if 0 <= progress_start < progress_middle < progress_end <= 1:
            print("   ✅ Прогресс миграции рассчитывается корректно")
            return True
        else:
            print(f"   ❌ Неверная логика прогресса: {progress_start:.2%} -> {progress_middle:.2%} -> {progress_end:.2%}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка расчета прогресса: {e}")
        return False


def test_slippage_calculation():
    """Тест расчета слиппеджа."""
    print("\n📉 Тестируем расчет слиппеджа...")
    
    try:
        curve = CurveManager(
            virtual_sol_reserves=30_000_000_000,
            virtual_token_reserves=1_073_000_000_000_000,
            real_sol_reserves=10_000_000_000,
            real_token_reserves=800_000_000_000_000
        )
        
        # Тест слиппеджа для разных сумм
        amounts = [
            100_000_000,    # 0.1 SOL
            1_000_000_000,  # 1 SOL
            5_000_000_000,  # 5 SOL
            10_000_000_000  # 10 SOL
        ]
        
        slippages = []
        for amount in amounts:
            slippage = curve.calculate_slippage(amount)
            slippages.append(slippage)
            print(f"   Слиппедж для {amount/1e9:.1f} SOL: {slippage:.4%}")
        
        # Слиппедж должен увеличиваться с размером сделки
        is_increasing = all(slippages[i] <= slippages[i+1] for i in range(len(slippages)-1))
        
        if is_increasing and all(0 <= s <= 1 for s in slippages):
            print("   ✅ Слиппедж рассчитывается корректно")
            return True
        else:
            print("   ❌ Проблема с расчетом слиппеджа")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка расчета слиппеджа: {e}")
        return False


def test_edge_cases():
    """Тест граничных случаев."""
    print("\n⚠️ Тестируем граничные случаи...")
    
    try:
        # Тест с нулевыми резервами
        try:
            curve_zero = CurveManager(0, 0, 0, 0)
            price_zero = curve_zero.get_current_price()
            print(f"   Цена с нулевыми резервами: {price_zero}")
        except Exception as e:
            print(f"   ✅ Нулевые резервы правильно обработаны: {type(e).__name__}")
        
        # Тест с очень большими числами
        curve_big = CurveManager(
            virtual_sol_reserves=10**18,
            virtual_token_reserves=10**18,
            real_sol_reserves=10**15,
            real_token_reserves=10**15
        )
        
        price_big = curve_big.get_current_price()
        print(f"   Цена с большими числами: {price_big}")
        
        # Тест покупки нулевого количества
        tokens_zero = curve_big.calculate_buy_price(0)
        print(f"   Покупка за 0 SOL: {tokens_zero} токенов")
        
        if tokens_zero == 0:
            print("   ✅ Граничные случаи обработаны корректно")
            return True
        else:
            print("   ❌ Проблема с граничными случаями")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка граничных случаев: {e}")
        return False


def test_curve_state_updates():
    """Тест обновления состояния кривой."""
    print("\n🔄 Тестируем обновление состояния кривой...")
    
    try:
        # Начальное состояние
        curve = CurveManager(
            virtual_sol_reserves=30_000_000_000,
            virtual_token_reserves=1_073_000_000_000_000,
            real_sol_reserves=0,
            real_token_reserves=1_000_000_000_000_000
        )
        
        initial_price = curve.get_current_price()
        initial_progress = curve.get_migration_progress()
        
        print(f"   Начальная цена: {initial_price:.12f}")
        print(f"   Начальный прогресс: {initial_progress:.2%}")
        
        # Обновляем состояние (симулируем покупки)
        curve.update_reserves(
            real_sol_reserves=20_000_000_000,  # 20 SOL добавлено
            real_token_reserves=600_000_000_000_000  # 600M токенов осталось
        )
        
        updated_price = curve.get_current_price()
        updated_progress = curve.get_migration_progress()
        
        print(f"   Обновленная цена: {updated_price:.12f}")
        print(f"   Обновленный прогресс: {updated_progress:.2%}")
        
        # Цена должна вырасти, прогресс увеличиться
        if updated_price > initial_price and updated_progress > initial_progress:
            print("   ✅ Обновление состояния работает корректно")
            return True
        else:
            print("   ❌ Проблема с обновлением состояния")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка обновления состояния: {e}")
        return False


def test_realistic_scenario():
    """Тест реалистичного сценария торговли."""
    print("\n🎯 Тестируем реалистичный сценарий...")
    
    try:
        # Создаем кривую для нового токена
        curve = CurveManager(
            virtual_sol_reserves=30_000_000_000,
            virtual_token_reserves=1_073_000_000_000_000,
            real_sol_reserves=0,
            real_token_reserves=1_000_000_000_000_000
        )
        
        print(f"   Начальная цена: {curve.get_current_price():.12f} SOL")
        print(f"   Начальный market cap: {curve.get_market_cap():.6f} SOL")
        
        # Симулируем несколько покупок
        purchases = [0.1, 0.5, 1.0, 2.0, 5.0]  # SOL
        total_sol_spent = 0
        total_tokens_bought = 0
        
        for sol_amount in purchases:
            sol_lamports = int(sol_amount * 1e9)
            tokens = curve.calculate_buy_price(sol_lamports)
            slippage = curve.calculate_slippage(sol_lamports)
            
            print(f"   Покупка {sol_amount} SOL: {tokens:,} токенов (слиппедж: {slippage:.2%})")
            
            # Обновляем состояние кривой
            total_sol_spent += sol_lamports
            total_tokens_bought += tokens
            new_real_sol = total_sol_spent
            new_real_tokens = 1_000_000_000_000_000 - total_tokens_bought
            
            curve.update_reserves(new_real_sol, new_real_tokens)
        
        final_price = curve.get_current_price()
        final_progress = curve.get_migration_progress()
        
        print(f"   Финальная цена: {final_price:.12f} SOL")
        print(f"   Финальный прогресс: {final_progress:.2%}")
        print(f"   Общий рост цены: {(final_price / curve.get_current_price() - 1) * 100:.1f}%")
        
        if final_price > 0 and final_progress > 0:
            print("   ✅ Реалистичный сценарий выполнен успешно")
            return True
        else:
            print("   ❌ Проблема в реалистичном сценарии")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка реалистичного сценария: {e}")
        return False


def run_all_curve_tests():
    """Запустить все тесты CurveManager."""
    print("🧪 ТЕСТИРОВАНИЕ CurveManager")
    print("=" * 50)
    
    tests = [
        ("Расчет цен", test_price_calculations),
        ("Текущая цена", test_current_price),
        ("Рыночная капитализация", test_market_cap),
        ("Прогресс миграции", test_migration_progress),
        ("Расчет слиппеджа", test_slippage_calculation),
        ("Граничные случаи", test_edge_cases),
        ("Обновление состояния", test_curve_state_updates),
        ("Реалистичный сценарий", test_realistic_scenario),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Тест: {test_name}")
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"   🎉 ПРОЙДЕН")
            else:
                print(f"   💥 НЕ ПРОЙДЕН")
        except Exception as e:
            print(f"   💥 ОШИБКА: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ!")
    else:
        print(f"⚠️ {total - passed} тестов не прошли")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_curve_tests()
    exit(0 if success else 1)
