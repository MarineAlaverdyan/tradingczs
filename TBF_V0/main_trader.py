"""
Главная точка входа для торгового бота pump.fun.
Выполняет полный цикл: покупка → мониторинг 1 минута → продажа с логированием.
"""

import asyncio
import logging
import sys
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
import argparse

# Импорты модулей TBF_V0
from core.simple_client import SimpleClient
from core.simple_wallet import SimpleWallet
from core.priority_fee.manager import PriorityFeeManager
from core.token_info import TokenInfo
from pumpfun.address_provider import AddressProvider
from pumpfun.instruction_builder import InstructionBuilder
from trading.simple_buyer import SimpleBuyer
from trading.simple_seller import SimpleSeller
from trading.simple_tpsl_manager import SimpleTpSlManager, MonitoringConfig
from cleanup.simple_cleanup import SimpleCleanup

@dataclass
class TradeConfig:
    """Конфигурация торговли"""
    # Основные параметры - теперь принимаем данные слушателя
    listener_data: Optional[Dict[str, Any]] = None  # Данные от слушателя
    sol_amount: float = 0.001  # Количество SOL для покупки
    slippage_percent: float = 5.0  # Процент slippage
    
    # Параметры мониторинга
    monitoring_time_seconds: int = 60  # 1 минута мониторинга
    take_profit_percent: float = 50.0  # 50% прибыль для TP
    stop_loss_percent: float = 20.0   # 20% убыток для SL
    check_interval_seconds: float = 2.0  # Проверка каждые 2 секунды
    
    # Сетевые параметры
    rpc_endpoint: str = "https://api.devnet.solana.com"
    private_key: Optional[str] = None
    
    # Параметры логирования
    log_level: str = "INFO"
    log_to_file: bool = True


class MainTrader:
    """
    Главный торговый координатор.
    """
    
    def __init__(self, config: TradeConfig):
        """
        Инициализация торгового бота.
        
        Args:
            config: Конфигурация торговли
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Компоненты бота (будут инициализированы в setup)
        self.client = None
        self.wallet = None
        self.address_provider = None
        self.instruction_builder = None
        self.priority_fee_manager = None
        self.buyer = None
        self.seller = None
        self.tpsl_manager = None
        self.cleanup = None
        
        self.logger.info("🤖 MainTrader инициализирован")
        self.logger.info(f"📊 Конфигурация: {config}")
    
    def _setup_logging(self) -> logging.Logger:
        """Настройка системы логирования"""
        logger = logging.getLogger("MainTrader")
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Очистка существующих handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (если включен)
        if self.config.log_to_file:
            file_handler = logging.FileHandler(
                f'trading_log_{int(time.time())}.log',
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    async def setup(self) -> bool:
        """
        Инициализация всех компонентов бота.
        
        Returns:
            True если инициализация успешна
        """
        try:
            self.logger.info("🔧 Инициализация компонентов бота...")
            
            # 1. Инициализация клиента
            self.logger.info("📡 Подключение к Solana RPC...")
            self.client = SimpleClient(self.config.rpc_endpoint)
            await self.client.connect()
            
            health = await self.client.get_health()
            if health != "ok":
                raise Exception(f"RPC недоступен: {health}")
            self.logger.info(f"✅ RPC подключен: {health}")
            
            # 2. Инициализация кошелька
            self.logger.info("👛 Загрузка кошелька...")
            if not self.config.private_key:
                raise Exception("Не указан private_key")
            
            self.wallet = SimpleWallet()
            self.wallet.load_from_private_key(self.config.private_key)
            
            wallet_address = self.wallet.get_address_string()
            self.logger.info(f"✅ Кошелек загружен: {wallet_address}")
            
            # Проверка баланса
            balance_sol = await self.client.get_balance(wallet_address)
            self.logger.info(f"💰 Баланс кошелька: {balance_sol:.6f} SOL")
            
            if balance_sol < self.config.sol_amount:
                self.logger.warning(f"⚠️ Недостаточно SOL для торговли!")
            
            # 3. Инициализация вспомогательных компонентов
            self.logger.info("🔧 Инициализация вспомогательных компонентов...")
            self.address_provider = AddressProvider()
            self.instruction_builder = InstructionBuilder()
            self.priority_fee_manager = PriorityFeeManager(self.client)
            
            # 4. Инициализация торговых компонентов
            self.logger.info("💼 Инициализация торговых компонентов...")
            self.buyer = SimpleBuyer(
                self.client, self.wallet, self.address_provider, 
                self.instruction_builder, self.priority_fee_manager
            )
            
            self.seller = SimpleSeller(
                self.client, self.wallet, self.address_provider,
                self.instruction_builder, self.priority_fee_manager
            )
            
            # 5. Инициализация мониторинга и очистки
            from pumpfun.curve_manager import CurveManager
            curve_manager = CurveManager()
            
            self.tpsl_manager = SimpleTpSlManager(curve_manager, self.client)
            self.cleanup = SimpleCleanup(self.client, self.wallet, self.address_provider)
            
            self.logger.info("✅ Все компоненты инициализированы успешно!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации: {str(e)}")
            return False
    
    async def execute_trade_cycle(self, token_info: TokenInfo) -> Dict[str, Any]:
        """
        Выполняет полный цикл торговли: покупка → мониторинг → продажа.
        
        Returns:
            Словарь с результатами торговли
        """
        trade_start_time = time.time()
        results = {
            'success': False,
            'token_info': token_info.to_dict(),
            'start_time': trade_start_time,
            'phases': {}
        }
        
        try:
            self.logger.info("🚀 НАЧАЛО ТОРГОВОГО ЦИКЛА")
            self.logger.info("=" * 60)
            self.logger.info(f"🎯 Токен: {token_info.symbol} ({token_info.name})")
            self.logger.info(f"📍 Mint: {token_info.mint}")
            self.logger.info(f"🔗 Bonding Curve: {token_info.bonding_curve}")
            self.logger.info(f"👤 Создатель: {token_info.user}")
            self.logger.info(f"💰 Сумма: {self.config.sol_amount} SOL")
            self.logger.info(f"⏰ Мониторинг: {self.config.monitoring_time_seconds}s")
            
            # ФАЗА 1: ПОКУПКА
            self.logger.info("\n📈 ФАЗА 1: ПОКУПКА ТОКЕНА")
            self.logger.info("-" * 30)
            
            buy_start = time.time()
            buy_result = await self.buyer.buy_token(
                token_info=token_info,
                sol_amount=self.config.sol_amount,
                slippage_percent=self.config.slippage_percent
            )
            buy_duration = time.time() - buy_start
            
            results['phases']['buy'] = {
                'success': buy_result.success,
                'duration': buy_duration,
                'signature': buy_result.transaction_signature,
                'error': buy_result.error_message
            }
            
            if not buy_result.success:
                self.logger.error(f"❌ Покупка неудачна: {buy_result.error_message}")
                return results
            
            self.logger.info(f"✅ Покупка успешна!")
            self.logger.info(f"📝 Signature: {buy_result.transaction_signature}")
            self.logger.info(f"⏱️ Время покупки: {buy_duration:.2f}s")
            
            # Примерная цена покупки (для мониторинга)
            buy_price = self.config.sol_amount / (buy_result.tokens_received or 1000000)
            
            # ФАЗА 2: МОНИТОРИНГ
            self.logger.info(f"\n👁️ ФАЗА 2: МОНИТОРИНГ ПОЗИЦИИ ({self.config.monitoring_time_seconds}s)")
            self.logger.info("-" * 30)
            
            monitoring_config = MonitoringConfig(
                take_profit_percent=self.config.take_profit_percent,
                stop_loss_percent=self.config.stop_loss_percent,
                time_limit_seconds=self.config.monitoring_time_seconds,
                check_interval_seconds=self.config.check_interval_seconds
            )
            
            async def monitoring_callback(exit_reason, value):
                self.logger.info(f"🔔 Сигнал мониторинга: {exit_reason.value}, значение: {value}")
            
            monitor_start = time.time()
            monitor_result = await self.tpsl_manager.start_monitoring(
                token_info=token_info,
                buy_price=buy_price,
                config=monitoring_config,
                callback=monitoring_callback
            )
            monitor_duration = time.time() - monitor_start
            
            results['phases']['monitor'] = {
                'success': True,
                'duration': monitor_duration,
                'should_sell': monitor_result.should_sell,
                'exit_reason': monitor_result.exit_reason.value if monitor_result.exit_reason else None,
                'profit_loss_percent': monitor_result.profit_loss_percent
            }
            
            self.logger.info(f"📊 Мониторинг завершен:")
            self.logger.info(f"   Продавать: {monitor_result.should_sell}")
            self.logger.info(f"   Причина: {monitor_result.exit_reason}")
            self.logger.info(f"   P&L: {monitor_result.profit_loss_percent:.2f}%" if monitor_result.profit_loss_percent else "   P&L: н/д")
            
            # ФАЗА 3: ПРОДАЖА
            self.logger.info("\n📉 ФАЗА 3: ПРОДАЖА ТОКЕНА")
            self.logger.info("-" * 30)
            
            sell_start = time.time()
            sell_result = await self.seller.sell_all_tokens(
                token_info=token_info,
                slippage_percent=self.config.slippage_percent
            )
            sell_duration = time.time() - sell_start
            
            results['phases']['sell'] = {
                'success': sell_result.success,
                'duration': sell_duration,
                'signature': sell_result.transaction_signature,
                'sol_received': sell_result.sol_received,
                'error': sell_result.error_message
            }
            
            if not sell_result.success:
                self.logger.error(f"❌ Продажа неудачна: {sell_result.error_message}")
            else:
                self.logger.info(f"✅ Продажа успешна!")
                self.logger.info(f"📝 Signature: {sell_result.transaction_signature}")
                self.logger.info(f"💰 Получено SOL: {(sell_result.sol_received or 0) / 1_000_000_000:.6f}")
                self.logger.info(f"⏱️ Время продажи: {sell_duration:.2f}s")
            
            # ФАЗА 4: ОЧИСТКА
            self.logger.info("\n🧹 ФАЗА 4: ОЧИСТКА")
            self.logger.info("-" * 30)
            
            cleanup_start = time.time()
            cleanup_result = await self.cleanup.cleanup_after_sell(token_info.mint)
            cleanup_duration = time.time() - cleanup_start
            
            results['phases']['cleanup'] = {
                'success': cleanup_result.success,
                'duration': cleanup_duration,
                'closed_accounts': len(cleanup_result.closed_accounts),
                'sol_recovered': cleanup_result.sol_recovered,
                'error': cleanup_result.error_message
            }
            
            if cleanup_result.success:
                self.logger.info(f"✅ Очистка завершена!")
                self.logger.info(f"🗑️ Закрыто accounts: {len(cleanup_result.closed_accounts)}")
                self.logger.info(f"💰 Возвращено SOL: {cleanup_result.sol_recovered / 1_000_000_000:.6f}")
            else:
                self.logger.warning(f"⚠️ Очистка с ошибками: {cleanup_result.error_message}")
            
            # ИТОГИ
            total_duration = time.time() - trade_start_time
            results['success'] = buy_result.success and sell_result.success
            results['total_duration'] = total_duration
            
            self.logger.info("\n🏁 ИТОГИ ТОРГОВОГО ЦИКЛА")
            self.logger.info("=" * 60)
            self.logger.info(f"✅ Общий результат: {'УСПЕХ' if results['success'] else 'НЕУДАЧА'}")
            self.logger.info(f"⏱️ Общее время: {total_duration:.2f}s")
            self.logger.info(f"📊 Фазы:")
            for phase, data in results['phases'].items():
                status = "✅" if data['success'] else "❌"
                self.logger.info(f"   {status} {phase.upper()}: {data['duration']:.2f}s")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка в торговом цикле: {str(e)}")
            results['error'] = str(e)
            return results
    
    async def run(self, token_info: TokenInfo) -> bool:
        """
        Запуск торгового бота.
        
        Returns:
            True если торговля успешна
        """
        try:
            # Инициализация
            if not await self.setup():
                return False
            
            # Выполнение торгового цикла
            results = await self.execute_trade_cycle(token_info)
            
            return results['success']
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {str(e)}")
            return False
        finally:
            # Закрытие соединений
            if self.client:
                await self.client.close()
            self.logger.info("🔌 Соединения закрыты")


async def main():
    """Главная функция с примером данных от слушателя."""
    
    # Пример данных от слушателя (замените на реальные данные)
    listener_data = {
        'name': 'buy up',
        'symbol': 'buy up',
        'uri': 'https://ipfs.io/ipfs/Qmei5WUshDFeLJi5k8twgJZdKLC8g232r5RyjscjnTtjiT', 
        'mint': 'r8VCbeoXdsQ7RcXT9DF3CnJ2Fqdx9uNWywsV8Wepump', 
        'bondingCurve': 'AuUmsyXSAzKz4mTSEDX719rQvNpkz47rjbTn7QhU94SC',
        'associatedBondingCurve': 'CggVUQJEU2HWQRvMDAEiozNkPqKLMr5Mxc6zQPjnyrbz', 
        'user': '6pNDtUKGjbVVQLq8sQwdZW6heMuHAd6F5VpNSWfQvyfH'
    }
    
    # Создание TokenInfo из данных слушателя
    token_info = TokenInfo.from_listener_data(listener_data)
    print(f"📊 Создан TokenInfo: {token_info}")
    
    # Конфигурация (без mint_address, используем TokenInfo)
    config = TradeConfig(
        listener_data=listener_data,
        sol_amount=0.00001,
        private_key="YOUR_PRIVATE_KEY_HERE",  # Замените на реальный ключ
        slippage_percent=5.0,
        monitoring_time_seconds=60,
        take_profit_percent=50.0,
        stop_loss_percent=20.0,
        rpc_endpoint="https://api.devnet.solana.com",
        log_level="INFO"
    )
    
    # Запуск торгового бота с TokenInfo
    trader = MainTrader(config)
    success = await trader.run(token_info)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    print("🤖 ТОРГОВЫЙ БОТ PUMP.FUN (TBF_V0)")
    print("=" * 50)
    print("ВАЖНО: Этот бот использует данные от слушателя событий!")
    print("Замените listener_data в main() на реальные данные от вашего слушателя.")
    print("\nПример данных слушателя:")
    print("{'name': 'TokenName', 'symbol': 'SYM', 'mint': '...', 'bondingCurve': '...'}")
    print("\n⚠️  НЕ ЗАБУДЬТЕ:")
    print("1. Заменить YOUR_PRIVATE_KEY_HERE на реальный приватный ключ")
    print("2. Заменить listener_data на данные от слушателя")
    print("3. Проверить RPC endpoint (сейчас devnet)")
    print()
    
    asyncio.run(main())
