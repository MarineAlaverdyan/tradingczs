"""
CurveManager для pump.fun - математика bonding curve.
Расчет цен покупки/продажи, slippage и состояния кривой.
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
    """Менеджер bonding curve для pump.fun."""
    
    # Константы pump.fun bonding curve
    VIRTUAL_SOL_RESERVES = 30.0  # 30 SOL виртуальных резервов
    VIRTUAL_TOKEN_RESERVES = 1_073_000_000.0  # ~1.073B токенов виртуальных резервов
    INITIAL_REAL_SOL_RESERVES = 0.0  # Начальные реальные SOL резервы
    INITIAL_REAL_TOKEN_RESERVES = 1_000_000_000.0  # 1B токенов реальных резервов
    
    # Константы для расчетов
    LAMPORTS_PER_SOL = 1_000_000_000
    BONDING_CURVE_COMPLETE_SOL = 85.0  # SOL для завершения bonding curve
    
    @staticmethod
    def get_initial_curve_state() -> CurveState:
        """
        Получить начальное состояние bonding curve.
        
        Returns:
            Начальное состояние кривой
        """
        return CurveState(
            virtual_sol_reserves=CurveManager.VIRTUAL_SOL_RESERVES,
            virtual_token_reserves=CurveManager.VIRTUAL_TOKEN_RESERVES,
            real_sol_reserves=CurveManager.INITIAL_REAL_SOL_RESERVES,
            real_token_reserves=CurveManager.INITIAL_REAL_TOKEN_RESERVES,
            complete=False
        )
    
    @staticmethod
    def calculate_buy_price(sol_amount: float, curve_state: CurveState) -> Tuple[float, float, CurveState]:
        """
        Рассчитать количество токенов при покупке за SOL.
        
        Args:
            sol_amount: Количество SOL для покупки
            curve_state: Текущее состояние кривой
            
        Returns:
            Tuple[float, float, CurveState]: (токены, цена за токен, новое состояние)
        """
        try:
            if sol_amount <= 0:
                raise ValueError("Количество SOL должно быть положительным")
            
            if curve_state.complete:
                raise ValueError("Bonding curve завершена")
            
            # Используем формулу constant product: x * y = k
            # где x = virtual_sol_reserves, y = virtual_token_reserves
            
            # Текущий продукт
            k = curve_state.virtual_sol_reserves * curve_state.virtual_token_reserves
            
            # Новые SOL резервы после покупки
            new_virtual_sol = curve_state.virtual_sol_reserves + sol_amount
            
            # Новые токен резервы (из формулы k = x * y)
            new_virtual_tokens = k / new_virtual_sol
            
            # Количество токенов к выдаче
            tokens_out = curve_state.virtual_token_reserves - new_virtual_tokens
            
            if tokens_out <= 0:
                raise ValueError("Недостаточно токенов в резервах")
            
            # Проверяем, не превышает ли покупка доступные реальные токены
            if tokens_out > curve_state.real_token_reserves:
                tokens_out = curve_state.real_token_reserves
                # Пересчитываем необходимое количество SOL
                required_virtual_tokens = curve_state.virtual_token_reserves - tokens_out
                required_virtual_sol = k / required_virtual_tokens
                sol_amount = required_virtual_sol - curve_state.virtual_sol_reserves
                new_virtual_sol = required_virtual_sol
                new_virtual_tokens = required_virtual_tokens
            
            # Цена за токен
            price_per_token = sol_amount / tokens_out if tokens_out > 0 else 0
            
            # Новое состояние кривой
            new_state = CurveState(
                virtual_sol_reserves=new_virtual_sol,
                virtual_token_reserves=new_virtual_tokens,
                real_sol_reserves=curve_state.real_sol_reserves + sol_amount,
                real_token_reserves=curve_state.real_token_reserves - tokens_out,
                complete=curve_state.real_sol_reserves + sol_amount >= CurveManager.BONDING_CURVE_COMPLETE_SOL
            )
            
            return tokens_out, price_per_token, new_state
            
        except Exception as e:
            raise Exception(f"Ошибка расчета цены покупки: {e}")
    
    @staticmethod
    def calculate_sell_price(token_amount: float, curve_state: CurveState) -> Tuple[float, float, CurveState]:
        """
        Рассчитать количество SOL при продаже токенов.
        
        Args:
            token_amount: Количество токенов для продажи
            curve_state: Текущее состояние кривой
            
        Returns:
            Tuple[float, float, CurveState]: (SOL, цена за токен, новое состояние)
        """
        try:
            if token_amount <= 0:
                raise ValueError("Количество токенов должно быть положительным")
            
            if curve_state.complete:
                raise ValueError("Bonding curve завершена")
            
            # Используем формулу constant product: x * y = k
            k = curve_state.virtual_sol_reserves * curve_state.virtual_token_reserves
            
            # Новые токен резервы после продажи
            new_virtual_tokens = curve_state.virtual_token_reserves + token_amount
            
            # Новые SOL резервы (из формулы k = x * y)
            new_virtual_sol = k / new_virtual_tokens
            
            # Количество SOL к выдаче
            sol_out = curve_state.virtual_sol_reserves - new_virtual_sol
            
            if sol_out <= 0:
                raise ValueError("Недостаточно SOL в резервах")
            
            # Проверяем, не превышает ли продажа доступные реальные SOL
            if sol_out > curve_state.real_sol_reserves:
                sol_out = curve_state.real_sol_reserves
                # Пересчитываем необходимое количество токенов
                required_virtual_sol = curve_state.virtual_sol_reserves - sol_out
                required_virtual_tokens = k / required_virtual_sol
                token_amount = required_virtual_tokens - curve_state.virtual_token_reserves
                new_virtual_sol = required_virtual_sol
                new_virtual_tokens = required_virtual_tokens
            
            # Цена за токен
            price_per_token = sol_out / token_amount if token_amount > 0 else 0
            
            # Новое состояние кривой
            new_state = CurveState(
                virtual_sol_reserves=new_virtual_sol,
                virtual_token_reserves=new_virtual_tokens,
                real_sol_reserves=curve_state.real_sol_reserves - sol_out,
                real_token_reserves=curve_state.real_token_reserves + token_amount,
                complete=False  # Продажа не может завершить кривую
            )
            
            return sol_out, price_per_token, new_state
            
        except Exception as e:
            raise Exception(f"Ошибка расчета цены продажи: {e}")
    
    @staticmethod
    def calculate_slippage(amount: float, is_buy: bool, curve_state: CurveState) -> float:
        """
        Рассчитать slippage для сделки.
        
        Args:
            amount: Количество SOL (для покупки) или токенов (для продажи)
            is_buy: True для покупки, False для продажи
            curve_state: Текущее состояние кривой
            
        Returns:
            Slippage в процентах (0.05 = 5%)
        """
        try:
            if is_buy:
                # Для покупки рассчитываем изменение цены
                small_amount = amount * 0.01  # 1% от суммы
                
                _, price_small, _ = CurveManager.calculate_buy_price(small_amount, curve_state)
                _, price_full, _ = CurveManager.calculate_buy_price(amount, curve_state)
                
                if price_small > 0:
                    slippage = abs(price_full - price_small) / price_small
                else:
                    slippage = 0.0
            else:
                # Для продажи рассчитываем изменение цены
                small_amount = amount * 0.01  # 1% от количества
                
                _, price_small, _ = CurveManager.calculate_sell_price(small_amount, curve_state)
                _, price_full, _ = CurveManager.calculate_sell_price(amount, curve_state)
                
                if price_small > 0:
                    slippage = abs(price_full - price_small) / price_small
                else:
                    slippage = 0.0
            
            return slippage
            
        except Exception:
            return 0.0  # Возвращаем 0 при ошибке
    
    @staticmethod
    def get_current_price(curve_state: CurveState) -> float:
        """
        Получить текущую цену токена в SOL.
        
        Args:
            curve_state: Состояние кривой
            
        Returns:
            Цена одного токена в SOL
        """
        try:
            # Текущая цена = virtual_sol_reserves / virtual_token_reserves
            if curve_state.virtual_token_reserves > 0:
                return curve_state.virtual_sol_reserves / curve_state.virtual_token_reserves
            else:
                return 0.0
        except Exception:
            return 0.0
    
    @staticmethod
    def get_market_cap(curve_state: CurveState, total_supply: float = 1_000_000_000.0) -> float:
        """
        Рассчитать рыночную капитализацию токена.
        
        Args:
            curve_state: Состояние кривой
            total_supply: Общее предложение токенов
            
        Returns:
            Рыночная капитализация в SOL
        """
        try:
            current_price = CurveManager.get_current_price(curve_state)
            return current_price * total_supply
        except Exception:
            return 0.0
    
    @staticmethod
    def calculate_progress_to_raydium(curve_state: CurveState) -> float:
        """
        Рассчитать прогресс до миграции на Raydium.
        
        Args:
            curve_state: Состояние кривой
            
        Returns:
            Прогресс в процентах (0.0 - 1.0)
        """
        try:
            progress = curve_state.real_sol_reserves / CurveManager.BONDING_CURVE_COMPLETE_SOL
            return min(progress, 1.0)
        except Exception:
            return 0.0


# Пример использования
def main():
    """Пример использования CurveManager."""
    
    print("📈 Пример работы с CurveManager")
    print("=" * 50)
    
    # Получаем начальное состояние
    print("🚀 Начальное состояние bonding curve:")
    curve_state = CurveManager.get_initial_curve_state()
    print(f"   Virtual SOL: {curve_state.virtual_sol_reserves}")
    print(f"   Virtual Tokens: {curve_state.virtual_token_reserves:,.0f}")
    print(f"   Real SOL: {curve_state.real_sol_reserves}")
    print(f"   Real Tokens: {curve_state.real_token_reserves:,.0f}")
    
    # Текущая цена
    current_price = CurveManager.get_current_price(curve_state)
    print(f"   Текущая цена: {current_price:.10f} SOL за токен")
    
    # Рыночная капитализация
    market_cap = CurveManager.get_market_cap(curve_state)
    print(f"   Рыночная капитализация: {market_cap:.2f} SOL")
    
    # Тестируем покупку
    print("\n💰 Тестируем покупку за 1 SOL:")
    try:
        sol_amount = 1.0
        tokens_out, price_per_token, new_state = CurveManager.calculate_buy_price(sol_amount, curve_state)
        
        print(f"   Покупаем за: {sol_amount} SOL")
        print(f"   Получаем: {tokens_out:,.2f} токенов")
        print(f"   Цена за токен: {price_per_token:.10f} SOL")
        
        # Slippage
        slippage = CurveManager.calculate_slippage(sol_amount, True, curve_state)
        print(f"   Slippage: {slippage:.4f} ({slippage*100:.2f}%)")
        
        # Обновляем состояние
        curve_state = new_state
        print(f"   Новые virtual SOL: {curve_state.virtual_sol_reserves:.2f}")
        print(f"   Новые virtual tokens: {curve_state.virtual_token_reserves:,.0f}")
        
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Тестируем продажу
    print("\n💸 Тестируем продажу 10,000 токенов:")
    try:
        token_amount = 10_000.0
        sol_out, price_per_token, new_state = CurveManager.calculate_sell_price(token_amount, curve_state)
        
        print(f"   Продаем: {token_amount:,.0f} токенов")
        print(f"   Получаем: {sol_out:.6f} SOL")
        print(f"   Цена за токен: {price_per_token:.10f} SOL")
        
        # Slippage
        slippage = CurveManager.calculate_slippage(token_amount, False, curve_state)
        print(f"   Slippage: {slippage:.4f} ({slippage*100:.2f}%)")
        
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    # Прогресс до Raydium
    progress = CurveManager.calculate_progress_to_raydium(curve_state)
    print(f"\n🎯 Прогресс до миграции на Raydium: {progress:.4f} ({progress*100:.2f}%)")
    
    # Тестируем большую покупку
    print("\n🚀 Тестируем большую покупку за 50 SOL:")
    try:
        big_sol_amount = 50.0
        tokens_out, price_per_token, final_state = CurveManager.calculate_buy_price(big_sol_amount, curve_state)
        
        print(f"   Покупаем за: {big_sol_amount} SOL")
        print(f"   Получаем: {tokens_out:,.2f} токенов")
        print(f"   Средняя цена: {price_per_token:.10f} SOL")
        
        # Финальный прогресс
        final_progress = CurveManager.calculate_progress_to_raydium(final_state)
        print(f"   Финальный прогресс: {final_progress:.4f} ({final_progress*100:.2f}%)")
        print(f"   Кривая завершена: {final_state.complete}")
        
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    print("\n🎉 Демонстрация CurveManager завершена!")


if __name__ == "__main__":
    main()
