"""
Простой менеджер Take Profit / Stop Loss для мониторинга позиций.
Отслеживает цену токена и генерирует сигналы на продажу.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import time

# Настройка логирования
logger = logging.getLogger(__name__)

class ExitReason(Enum):
    """Причины выхода из позиции"""
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    TIME_LIMIT = "time_limit"
    MANUAL = "manual"

@dataclass
class MonitoringConfig:
    """Конфигурация мониторинга позиции"""
    take_profit_percent: float = 50.0  # % прибыли для TP
    stop_loss_percent: float = 20.0    # % убытка для SL
    time_limit_seconds: int = 60       # Лимит времени в секундах
    check_interval_seconds: float = 1.0  # Интервал проверки цены
    
@dataclass
class MonitoringResult:
    """Результат мониторинга"""
    should_sell: bool
    exit_reason: Optional[ExitReason] = None
    current_price: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    time_elapsed: Optional[float] = None


class SimpleTpSlManager:
    """
    Простой менеджер TP/SL для мониторинга позиций.
    """
    
    def __init__(self, curve_manager, client=None):
        """
        Инициализация менеджера.
        
        Args:
            curve_manager: CurveManager для расчета цен
            client: SimpleClient для получения данных (опционально)
        """
        self.curve_manager = curve_manager
        self.client = client
        self.is_monitoring = False
        self.monitoring_task = None
        
        logger.info("SimpleTpSlManager инициализирован")
    
    async def start_monitoring(
        self,
        mint_address: str,
        buy_price: float,
        config: MonitoringConfig,
        callback: Optional[Callable] = None
    ) -> MonitoringResult:
        """
        Запускает мониторинг позиции с TP/SL.
        
        Args:
            mint_address: Адрес токена для мониторинга
            buy_price: Цена покупки для расчета P&L
            config: Конфигурация мониторинга
            callback: Функция обратного вызова для уведомлений
            
        Returns:
            MonitoringResult с результатом мониторинга
        """
        logger.info(f"🔍 Начинаем мониторинг позиции: {mint_address}")
        logger.info(f"💰 Цена покупки: {buy_price}")
        logger.info(f"📊 TP: {config.take_profit_percent}%, SL: {config.stop_loss_percent}%")
        logger.info(f"⏰ Лимит времени: {config.time_limit_seconds}s")
        
        self.is_monitoring = True
        start_time = time.time()
        
        try:
            while self.is_monitoring:
                # Проверка времени
                elapsed_time = time.time() - start_time
                if elapsed_time >= config.time_limit_seconds:
                    logger.info(f"⏰ Достигнут лимит времени: {elapsed_time:.1f}s")
                    if callback:
                        await callback(ExitReason.TIME_LIMIT, elapsed_time)
                    return MonitoringResult(
                        should_sell=True,
                        exit_reason=ExitReason.TIME_LIMIT,
                        time_elapsed=elapsed_time
                    )
                
                # Получение текущей цены
                try:
                    current_price = await self._get_current_price(mint_address)
                    if current_price is None:
                        logger.warning("Не удалось получить текущую цену, пропускаем проверку")
                        await asyncio.sleep(config.check_interval_seconds)
                        continue
                    
                    # Расчет P&L
                    profit_loss_percent = ((current_price - buy_price) / buy_price) * 100
                    
                    logger.debug(f"💹 Цена: {current_price:.8f}, P&L: {profit_loss_percent:.2f}%")
                    
                    # Проверка условий выхода
                    exit_reason = None
                    
                    if profit_loss_percent >= config.take_profit_percent:
                        exit_reason = ExitReason.TAKE_PROFIT
                        logger.info(f"🎯 Take Profit достигнут! P&L: {profit_loss_percent:.2f}%")
                    elif profit_loss_percent <= -config.stop_loss_percent:
                        exit_reason = ExitReason.STOP_LOSS
                        logger.info(f"🛑 Stop Loss достигнут! P&L: {profit_loss_percent:.2f}%")
                    
                    if exit_reason:
                        if callback:
                            await callback(exit_reason, profit_loss_percent)
                        
                        return MonitoringResult(
                            should_sell=True,
                            exit_reason=exit_reason,
                            current_price=current_price,
                            profit_loss_percent=profit_loss_percent,
                            time_elapsed=elapsed_time
                        )
                    
                except Exception as e:
                    logger.error(f"Ошибка при проверке цены: {e}")
                
                # Пауза перед следующей проверкой
                await asyncio.sleep(config.check_interval_seconds)
            
            # Мониторинг остановлен вручную
            logger.info("🛑 Мониторинг остановлен вручную")
            return MonitoringResult(
                should_sell=False,
                exit_reason=ExitReason.MANUAL,
                time_elapsed=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Критическая ошибка в мониторинге: {e}")
            return MonitoringResult(
                should_sell=False,
                time_elapsed=time.time() - start_time
            )
        finally:
            self.is_monitoring = False
    
    async def _get_current_price(self, mint_address: str) -> Optional[float]:
        """
        Получает текущую цену токена.
        
        Args:
            mint_address: Адрес токена
            
        Returns:
            Текущая цена или None при ошибке
        """
        try:
            # Здесь можно добавить различные источники цены:
            # 1. Через CurveManager (bonding curve)
            # 2. Через DEX API
            # 3. Через on-chain данные
            
            # Пока используем заглушку
            if hasattr(self.curve_manager, 'get_current_price'):
                price = await self.curve_manager.get_current_price(mint_address)
                return price
            else:
                # Симуляция изменения цены для тестирования
                import random
                base_price = 0.000001
                variation = random.uniform(-0.1, 0.1)  # ±10% изменение
                simulated_price = base_price * (1 + variation)
                logger.debug(f"Симулированная цена: {simulated_price:.8f}")
                return simulated_price
                
        except Exception as e:
            logger.error(f"Ошибка получения цены: {e}")
            return None
    
    def stop_monitoring(self):
        """Останавливает мониторинг позиции."""
        logger.info("🛑 Остановка мониторинга...")
        self.is_monitoring = False
        
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
    
    async def monitor_position_async(
        self,
        mint_address: str,
        buy_price: float,
        config: MonitoringConfig,
        callback: Optional[Callable] = None
    ):
        """
        Запускает асинхронный мониторинг позиции в фоне.
        
        Args:
            mint_address: Адрес токена
            buy_price: Цена покупки
            config: Конфигурация мониторинга
            callback: Функция обратного вызова
        """
        logger.info(f"🔄 Запуск асинхронного мониторинга для {mint_address}")
        
        self.monitoring_task = asyncio.create_task(
            self.start_monitoring(mint_address, buy_price, config, callback)
        )
        
        return self.monitoring_task
    
    async def get_position_status(self, mint_address: str, buy_price: float) -> Dict[str, Any]:
        """
        Получает текущий статус позиции без запуска мониторинга.
        
        Args:
            mint_address: Адрес токена
            buy_price: Цена покупки
            
        Returns:
            Словарь со статусом позиции
        """
        try:
            current_price = await self._get_current_price(mint_address)
            
            if current_price is None:
                return {'error': 'Не удалось получить текущую цену'}
            
            profit_loss_percent = ((current_price - buy_price) / buy_price) * 100
            profit_loss_absolute = current_price - buy_price
            
            status = {
                'mint_address': mint_address,
                'buy_price': buy_price,
                'current_price': current_price,
                'profit_loss_percent': profit_loss_percent,
                'profit_loss_absolute': profit_loss_absolute,
                'is_profitable': profit_loss_percent > 0,
                'timestamp': time.time()
            }
            
            logger.debug(f"Статус позиции: {status}")
            return status
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса позиции: {e}")
            return {'error': str(e)}


# Пример использования
if __name__ == "__main__":
    async def example_callback(exit_reason: ExitReason, value: float):
        """Пример функции обратного вызова"""
        print(f"🔔 Сигнал: {exit_reason.value}, значение: {value}")
    
    async def example_usage():
        """Пример использования SimpleTpSlManager"""
        print("🔍 ПРИМЕР ИСПОЛЬЗОВАНИЯ SIMPLE TP/SL MANAGER")
        print("=" * 50)
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Создание менеджера (требует CurveManager)
        # curve_manager = CurveManager(...)
        # manager = SimpleTpSlManager(curve_manager)
        
        print("⚠️  Для полного примера необходим инициализированный CurveManager")
        
        # Создание заглушки для демонстрации
        class MockCurveManager:
            pass
        
        manager = SimpleTpSlManager(MockCurveManager())
        
        # Конфигурация мониторинга
        config = MonitoringConfig(
            take_profit_percent=20.0,  # 20% прибыль
            stop_loss_percent=10.0,    # 10% убыток
            time_limit_seconds=30,     # 30 секунд
            check_interval_seconds=2.0  # Проверка каждые 2 секунды
        )
        
        print(f"📊 Конфигурация: TP={config.take_profit_percent}%, SL={config.stop_loss_percent}%")
        print(f"⏰ Лимит времени: {config.time_limit_seconds}s")
        
        # Пример мониторинга
        mint_address = "So11111111111111111111111111111111111111112"
        buy_price = 0.000001
        
        print(f"🔍 Начинаем мониторинг {mint_address}")
        print(f"💰 Цена покупки: {buy_price}")
        
        result = await manager.start_monitoring(
            mint_address=mint_address,
            buy_price=buy_price,
            config=config,
            callback=example_callback
        )
        
        print(f"📋 Результат мониторинга:")
        print(f"   Продавать: {result.should_sell}")
        print(f"   Причина: {result.exit_reason}")
        print(f"   Время: {result.time_elapsed:.1f}s")
        if result.profit_loss_percent:
            print(f"   P&L: {result.profit_loss_percent:.2f}%")
        
        print("\n🎯 SimpleTpSlManager готов к использованию!")
    
    # Запуск примера
    asyncio.run(example_usage())
