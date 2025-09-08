"""
Standalone тест для CurveManager - без внешних зависимостей.
Копирует код CurveManager напрямую для изолированного тестирования.
"""

from typing import Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class CurveState:
    """Состояние bonding curve."""
    virtual_sol_reserves: float
    virtual_token_reserves: float
    real_sol_reserves: float
    real_token_reserves: float
    complete: bool = False


class CurveManager:
    """
    Менеджер bonding curve для pump.fun.
    Рассчитывает цены, slippage и состояние кривой.
    """
    
    def __init__(self, virtual_sol_reserves: float, virtual_token_reserves: float, 
                 real_sol_reserves: float, real_token_reserves: float):
        """
        Инициализация кривой.
        
        Args:
            virtual_sol_reserves: Виртуальные SOL резервы
            virtual_token_reserves: Виртуальные токен резервы
            real_sol_reserves: Реальные SOL резервы
            real_token_reserves: Реальные токен резервы
        """
        self.state = CurveState(
            virtual_sol_reserves=virtual_sol_reserves,
            virtual_token_reserves=virtual_token_reserves,
            real_sol_reserves=real_sol_reserves,
            real_token_reserves=real_token_reserves
        )
        
        # Константы pump.fun
        self.MIGRATION_TARGET = 85_000_000_000  # 85 SOL для миграции
        self.TOTAL_SUPPLY = 1_000_000_000_000_000  # 1B токенов
    
    def calculate_buy_price(self, sol_amount: float) -> float:
        """
        Рассчитать количество токенов за SOL.
        
        Args:
            sol_amount: Количество SOL для покупки (в lamports)
            
        Returns:
            Количество токенов
        """
        if sol_amount <= 0:
            return 0
        
        # Формула AMM: x * y = k
        # Где x = SOL резервы, y = токен резервы
        total_sol = self.state.virtual_sol_reserves + self.state.real_sol_reserves
        total_tokens = self.state.virtual_token_reserves + self.state.real_token_reserves
        
        # Константа произведения
        k = total_sol * total_tokens
        
        # Новые SOL резервы после покупки
        new_sol_reserves = total_sol + sol_amount
        
        # Новые токен резервы из формулы k = x * y
        new_token_reserves = k / new_sol_reserves
        
        # Количество токенов к выдаче
        tokens_out = total_tokens - new_token_reserves
        
        return max(0, tokens_out)
    
    def calculate_sell_price(self, token_amount: float) -> float:
        """
        Рассчитать количество SOL за токены.
        
        Args:
            token_amount: Количество токенов для продажи
            
        Returns:
            Количество SOL (в lamports)
        """
        if token_amount <= 0:
            return 0
        
        total_sol = self.state.virtual_sol_reserves + self.state.real_sol_reserves
        total_tokens = self.state.virtual_token_reserves + self.state.real_token_reserves
        
        # Проверяем, что есть достаточно токенов
        if token_amount > total_tokens:
            return 0
        
        k = total_sol * total_tokens
        
        # Новые токен резервы после продажи
        new_token_reserves = total_tokens + token_amount
        
        # Новые SOL резервы
        new_sol_reserves = k / new_token_reserves
        
        # Количество SOL к выдаче
        sol_out = total_sol - new_sol_reserves
        
        return max(0, sol_out)
    
    def get_current_price(self) -> float:
        """
        Получить текущую цену токена в SOL.
        
        Returns:
            Цена одного токена в SOL
        """
        total_sol = self.state.virtual_sol_reserves + self.state.real_sol_reserves
        total_tokens = self.state.virtual_token_reserves + self.state.real_token_reserves
        
        if total_tokens <= 0:
            return 0
        
        return total_sol / total_tokens
    
    def get_market_cap(self) -> float:
        """
        Рассчитать рыночную капитализацию.
        
        Returns:
            Market cap в SOL
        """
        current_price = self.get_current_price()
        return current_price * self.TOTAL_SUPPLY
    
    def get_migration_progress(self) -> float:
        """
        Получить прогресс до миграции на Raydium.
        
        Returns:
            Прогресс от 0 до 1
        """
        return min(1.0, self.state.real_sol_reserves / self.MIGRATION_TARGET)
    
    def calculate_slippage(self, sol_amount: float) -> float:
        """
        Рассчитать slippage для покупки.
        
        Args:
            sol_amount: Количество SOL для покупки
            
        Returns:
            Slippage в процентах (0-1)
        """
        if sol_amount <= 0:
            return 0
        
        # Текущая цена
        current_price = self.get_current_price()
        
        # Количество токенов при покупке
        tokens_received = self.calculate_buy_price(sol_amount)
        
        if tokens_received <= 0:
            return 1.0  # 100% slippage
        
        # Эффективная цена покупки
        effective_price = sol_amount / tokens_received
        
        # Slippage = (эффективная_цена - текущая_цена) / текущая_цена
        if current_price <= 0:
            return 1.0
        
        slippage = (effective_price - current_price) / current_price
        return max(0, min(1, slippage))
    
    def update_reserves(self, real_sol_reserves: float, real_token_reserves: float):
        """
        Обновить состояние резервов.
        
        Args:
            real_sol_reserves: Новые реальные SOL резервы
            real_token_reserves: Новые реальные токен резервы
        """
        self.state.real_sol_reserves = real_sol_reserves
        self.state.real_token_reserves = real_token_reserves
        
        # Проверяем завершение миграции
        if real_sol_reserves >= self.MIGRATION_TARGET:
            self.state.complete = True


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
        
        initial_price = curve.get_current_price()
        print(f"   Начальная цена: {initial_price:.12f} SOL")
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
        print(f"   Общий рост цены: {(final_price / initial_price - 1) * 100:.1f}%")
        
        if final_price > initial_price and final_progress > 0:
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
