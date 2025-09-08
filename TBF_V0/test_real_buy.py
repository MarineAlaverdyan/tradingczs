"""
Тест реальной покупки токена с детальным измерением времени выполнения каждой функции.
Включает профилировщик производительности для анализа узких мест.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
import json

# Добавляем путь к TBF_V0 в sys.path
sys.path.append(str(Path(__file__).parent))

from core.token_info import TokenInfo
from main_trader import MainTrader, TradeConfig


@dataclass
class PerformanceMetric:
    """Метрика производительности для функции."""
    function_name: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    error: str = None


class PerformanceProfiler:
    """Профилировщик производительности для измерения времени выполнения функций."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.logger = logging.getLogger("performance")
    
    async def measure_async_function(self, func_name: str, func, *args, **kwargs):
        """Измеряет время выполнения асинхронной функции."""
        start_time = time.perf_counter()
        success = True
        error = None
        result = None
        
        try:
            self.logger.info(f"⏱️  Начало выполнения: {func_name}")
            result = await func(*args, **kwargs)
            self.logger.info(f"✅ Завершено: {func_name}")
        except Exception as e:
            success = False
            error = str(e)
            self.logger.error(f"❌ Ошибка в {func_name}: {error}")
            raise
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            metric = PerformanceMetric(
                function_name=func_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                success=success,
                error=error
            )
            self.metrics.append(metric)
            
            self.logger.info(f"📊 {func_name}: {duration_ms:.2f} мс")
        
        return result
    
    def measure_sync_function(self, func_name: str, func, *args, **kwargs):
        """Измеряет время выполнения синхронной функции."""
        start_time = time.perf_counter()
        success = True
        error = None
        result = None
        
        try:
            self.logger.info(f"⏱️  Начало выполнения: {func_name}")
            result = func(*args, **kwargs)
            self.logger.info(f"✅ Завершено: {func_name}")
        except Exception as e:
            success = False
            error = str(e)
            self.logger.error(f"❌ Ошибка в {func_name}: {error}")
            raise
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            metric = PerformanceMetric(
                function_name=func_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                success=success,
                error=error
            )
            self.metrics.append(metric)
            
            self.logger.info(f"📊 {func_name}: {duration_ms:.2f} мс")
        
        return result
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Генерирует отчет о производительности."""
        if not self.metrics:
            return {"error": "Нет данных для анализа"}
        
        total_time = sum(m.duration_ms for m in self.metrics)
        successful_calls = [m for m in self.metrics if m.success]
        failed_calls = [m for m in self.metrics if not m.success]
        
        # Сортируем по времени выполнения (самые медленные первые)
        sorted_metrics = sorted(self.metrics, key=lambda x: x.duration_ms, reverse=True)
        
        report = {
            "summary": {
                "total_functions": len(self.metrics),
                "successful_calls": len(successful_calls),
                "failed_calls": len(failed_calls),
                "total_time_ms": total_time,
                "average_time_ms": total_time / len(self.metrics) if self.metrics else 0
            },
            "slowest_functions": [
                {
                    "name": m.function_name,
                    "duration_ms": m.duration_ms,
                    "percentage": (m.duration_ms / total_time) * 100 if total_time > 0 else 0
                }
                for m in sorted_metrics[:10]  # Топ 10 самых медленных
            ],
            "failed_functions": [
                {
                    "name": m.function_name,
                    "error": m.error,
                    "duration_ms": m.duration_ms
                }
                for m in failed_calls
            ],
            "detailed_metrics": [
                {
                    "name": m.function_name,
                    "duration_ms": m.duration_ms,
                    "success": m.success,
                    "error": m.error
                }
                for m in self.metrics
            ]
        }
        
        return report
    
    def print_performance_report(self):
        """Выводит отчет о производительности в консоль."""
        report = self.get_performance_report()
        
        print("\n" + "="*80)
        print("📊 ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ")
        print("="*80)
        
        summary = report["summary"]
        print(f"📈 Общая статистика:")
        print(f"   Всего функций: {summary['total_functions']}")
        print(f"   Успешных: {summary['successful_calls']}")
        print(f"   Неудачных: {summary['failed_calls']}")
        print(f"   Общее время: {summary['total_time_ms']:.2f} мс")
        print(f"   Среднее время: {summary['average_time_ms']:.2f} мс")
        
        print(f"\n🐌 Самые медленные функции:")
        for func in report["slowest_functions"][:5]:
            print(f"   {func['name']}: {func['duration_ms']:.2f} мс ({func['percentage']:.1f}%)")
        
        if report["failed_functions"]:
            print(f"\n❌ Неудачные функции:")
            for func in report["failed_functions"]:
                print(f"   {func['name']}: {func['error']}")
        
        print("="*80)


def setup_detailed_logging():
    """Настройка детального логирования."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Очистка существующих handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler для детальных логов
    file_handler = logging.FileHandler(
        log_dir / 'real_buy_performance.log',
        encoding='utf-8',
        mode='w'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    print(f"📝 Логирование настроено: {log_dir / 'real_buy_performance.log'}")


async def test_real_token_purchase():
    """Тестирует реальную покупку токена с измерением производительности."""
    
    profiler = PerformanceProfiler()
    logger = logging.getLogger("real_buy_test")
    
    print("🚀 ТЕСТ РЕАЛЬНОЙ ПОКУПКИ ТОКЕНА С ПРОФИЛИРОВАНИЕМ")
    print("="*80)
    print("⚠️  ВНИМАНИЕ: Это реальная покупка на mainnet!")
    print("💰 Убедитесь, что у вас достаточно SOL")
    print("🔑 Проверьте правильность приватного ключа")
    print()
    
    try:
        # 1. Создание TokenInfo
        logger.info("🧪 Шаг 1: Создание TokenInfo из данных слушателя")
        
        listener_data = {
            'name': 'TROLL COIN',
            'symbol': 'TROLL COIN',
            'uri': 'https://ipfs.io/ipfs/bafkreib5hc7ubyb2lublh43bwgke465vcmzfzw5gvmtpehvwpcac7gazlu',
            'mint': 'Cs64tSzj49EP5GKFZPXB9qXDp27wSMgJT9HPZmyrpump',
            'bondingCurve': 'DyGTjGW7DXqGGutRAn4yvSqkfj5EtFZ3wALcctFT233a',
            'associatedBondingCurve': 'DmHUXyDfC3yHZaG9dSqusdcGbTBwsqurvYitR5UqnRAo',
            'user': 'GPcsmRJK9rYzbFLLgVWyYaT6cS8o5iCZpLTrTwkfqj9C'
        }

        # {'name': 'TROLL COIN\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        # 'symbol': 'TROLLCOIN\x00',
        # 'uri': 'https://ipfs.io/ipfs/bafkreib5hc7ubyb2lublh43bwgke465vcmzfzw5gvmtpehvwpcac7gazlu\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        # 'mint': 'Cs64tSzj49EP5GKFZPXB9qXDp27wSMgJT9HPZmyrpump',
        # 'bondingCurve': 'DyGTjGW7DXqGGutRAn4yvSqkfj5EtFZ3wALcctFT233a',
        # 'associatedBondingCurve': 'DmHUXyDfC3yHZaG9dSqusdcGbTBwsqurvYitR5UqnRAo',
        # 'user': 'GPcsmRJK9rYzbFLLgVWyYaT6cS8o5iCZpLTrTwkfqj9C'}



        token_info = profiler.measure_sync_function(
            "TokenInfo.from_listener_data",
            TokenInfo.from_listener_data,
            listener_data
        )
        
        logger.info(f"✅ TokenInfo создан: {token_info.symbol}")
        
        # 2. Создание конфигурации
        logger.info("🧪 Шаг 2: Создание конфигурации торгового бота")
        
        config = profiler.measure_sync_function(
            "TradeConfig.creation",
            lambda: TradeConfig(
                listener_data=listener_data,
                sol_amount=0.0001,  # 0.0001 SOL для реальной покупки
                slippage_percent=15.0,  # Увеличенный slippage для успешной покупки
                monitoring_time_seconds=60,
                take_profit_percent=200.0,
                stop_loss_percent=50.0,
                rpc_endpoint="https://mainnet.helius-rpc.com/?api-key=e6fa031e-699e-49ed-9672-4582bdb4950d",
                private_key= "",#real private key,
                log_level="DEBUG"
            )
        )
        
        logger.info(f"✅ Конфигурация создана: {config.sol_amount} SOL")
        
        # 3. Инициализация торгового бота
        logger.info("🧪 Шаг 3: Инициализация торгового бота")
        
        trader = profiler.measure_sync_function(
            "MainTrader.creation",
            MainTrader,
            config
        )
        
        # 4. Настройка компонентов
        logger.info("🧪 Шаг 4: Настройка компонентов бота")
        
        setup_success = await profiler.measure_async_function(
            "MainTrader.setup",
            trader.setup
        )
        
        if not setup_success:
            raise Exception("Не удалось настроить компоненты бота")
        
        logger.info("✅ Все компоненты настроены успешно")
        
        # 5. Проверка баланса
        logger.info("🧪 Шаг 5: Проверка баланса кошелька")
        
        wallet_address = trader.wallet.get_address_string()
        balance = await profiler.measure_async_function(
            "SimpleClient.get_balance",
            trader.client.get_balance,
            wallet_address
        )
        
        logger.info(f"💰 Баланс кошелька: {balance:.6f} SOL")
        
        if balance < config.sol_amount:
            raise Exception(f"Недостаточно SOL! Нужно: {config.sol_amount}, есть: {balance}")
        
        # 6. РЕАЛЬНАЯ ПОКУПКА ТОКЕНА
        logger.info("🧪 Шаг 6: РЕАЛЬНАЯ ПОКУПКА ТОКЕНА")
        logger.warning("⚠️  ВНИМАНИЕ: Начинается реальная покупка!")
        
        buy_result = await profiler.measure_async_function(
            "SimpleBuyer.buy_token",
            trader.buyer.buy_token,
            token_info=token_info,
            sol_amount=config.sol_amount,
            slippage_percent=config.slippage_percent
        )
        
        logger.info(f"🔍 ДЕТАЛЬНЫЙ РЕЗУЛЬТАТ ПОКУПКИ:")
        logger.info(f"   Success: {buy_result.success}")
        logger.info(f"   Error message: {buy_result.error_message}")
        logger.info(f"   Transaction signature: {buy_result.transaction_signature}")
        logger.info(f"   Tokens received: {buy_result.tokens_received}")
        logger.info(f"   SOL spent: {buy_result.sol_spent}")
        
        if buy_result.success:
            logger.info(f"🎉 ПОКУПКА УСПЕШНА!")
            logger.info(f"   Транзакция: {buy_result.transaction_signature}")
            logger.info(f"   Получено токенов: {buy_result.tokens_received}")
            logger.info(f"   Потрачено SOL: {buy_result.sol_spent}")
        else:
            logger.error(f"❌ ПОКУПКА НЕУДАЧНА: {buy_result.error_message}")
        
        # 7. Закрытие соединений
        await profiler.measure_async_function(
            "SimpleClient.close",
            trader.client.close
        )
        
        # 8. Генерация отчета о производительности
        logger.info("🧪 Шаг 7: Генерация отчета о производительности")
        
        profiler.print_performance_report()
        
        # Сохранение отчета в файл
        report = profiler.get_performance_report()
        with open("logs/performance_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info("📊 Отчет сохранен в logs/performance_report.json")
        
        return buy_result.success if buy_result else False
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        logger.exception("Детали ошибки:")
        
        # Все равно показываем отчет о производительности
        profiler.print_performance_report()
        
        return False


async def main():
    """Главная функция."""
    
    print("🔬 ТЕСТ РЕАЛЬНОЙ ПОКУПКИ С ПРОФИЛИРОВАНИЕМ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 80)
    
    # Настройка логирования
    setup_detailed_logging()
    
    logger = logging.getLogger("main")
    logger.info("🚀 НАЧАЛО ТЕСТА РЕАЛЬНОЙ ПОКУПКИ")
    
    try:
        success = await test_real_token_purchase()
        
        if success:
            print("\n🎉 ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
            print("✅ Токен успешно куплен")
            print("📊 Проверьте отчет о производительности")
        else:
            print("\n❌ ТЕСТ ЗАВЕРШЕН С ОШИБКОЙ")
            print("📊 Проверьте логи и отчет о производительности")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в main: {e}")
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
