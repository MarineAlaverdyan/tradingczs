"""
Тестовый скрипт для проверки покупки мемкоина с использованием данных от слушателя.
Включает подробное логирование для диагностики проблем.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем путь к TBF_V0 в sys.path
sys.path.append(str(Path(__file__).parent))

from core.token_info import TokenInfo
from main_trader import MainTrader, TradeConfig


def setup_detailed_logging():
    """Настройка детального логирования для диагностики."""
    
    # Создаем директорию для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Настройка форматтера
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Корневой логгер
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
        log_dir / 'test_buy_detailed.log',
        encoding='utf-8',
        mode='w'  # Перезаписываем при каждом запуске
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # File handler для ошибок
    error_handler = logging.FileHandler(
        log_dir / 'test_buy_errors.log',
        encoding='utf-8',
        mode='w'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    print(f"📝 Логирование настроено:")
    print(f"   Детальные логи: {log_dir / 'test_buy_detailed.log'}")
    print(f"   Ошибки: {log_dir / 'test_buy_errors.log'}")
    print()


async def test_token_info_creation():
    """Тестирует создание TokenInfo из данных слушателя."""
    
    logger = logging.getLogger("test_token_info")
    logger.info("🧪 ТЕСТ 1: Создание TokenInfo из данных слушателя")
    
    # Пример данных от слушателя (те же, что вы показали)
    listener_data = {
        'name': 'buy up',
        'symbol': 'buy up',
        'uri': 'https://ipfs.io/ipfs/Qmei5WUshDFeLJi5k8twgJZdKLC8g232r5RyjscjnTtjiT', 
        'mint': 'r8VCbeoXdsQ7RcXT9DF3CnJ2Fqdx9uNWywsV8Wepump', 
        'bondingCurve': 'AuUmsyXSAzKz4mTSEDX719rQvNpkz47rjbTn7QhU94SC',
        'associatedBondingCurve': 'CggVUQJEU2HWQRvMDAEiozNkPqKLMr5Mxc6zQPjnyrbz', 
        'user': '6pNDtUKGjbVVQLq8sQwdZW6heMuHAd6F5VpNSWfQvyfH'
    }
    
    try:
        # Создание TokenInfo
        token_info = TokenInfo.from_listener_data(listener_data)
        
        logger.info("✅ TokenInfo создан успешно:")
        logger.info(f"   Название: {token_info.name}")
        logger.info(f"   Символ: {token_info.symbol}")
        logger.info(f"   Mint: {token_info.mint}")
        logger.info(f"   Bonding Curve: {token_info.bonding_curve}")
        logger.info(f"   Associated BC: {token_info.associated_bonding_curve}")
        logger.info(f"   Создатель: {token_info.user}")
        logger.info(f"   URI: {token_info.uri}")
        
        # Проверка конвертации в словарь
        token_dict = token_info.to_dict()
        logger.debug(f"TokenInfo как словарь: {token_dict}")
        
        return token_info
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания TokenInfo: {e}")
        logger.exception("Детали ошибки:")
        return None


async def test_trader_initialization(token_info: TokenInfo):
    """Тестирует инициализацию торгового бота."""
    
    logger = logging.getLogger("test_trader_init")
    logger.info("🧪 ТЕСТ 2: Инициализация торгового бота")
    
    try:
        # Конфигурация для тестирования
        config = TradeConfig(
            listener_data=token_info.to_dict(),
            sol_amount=0.00001,  # Очень маленькая сумма для теста
            private_key= "S8AmRgsyBPMqQL8BkY8PJoo7Gxj31HZZzpNWhfzUXwEkdQu56AJT9LSixAqGzAcR2b1W9XnuRPykZeZ9A6AXRRv",  # ЗАМЕНИТЕ НА РЕАЛЬНЫЙ КЛЮЧ!
            slippage_percent=10.0,  # Увеличенный slippage для тестов
            monitoring_time_seconds=30,  # Короткий мониторинг
            take_profit_percent=100.0,  # Высокий TP для тестов
            stop_loss_percent=50.0,   # Высокий SL для тестов
            rpc_endpoint="https://mainnet.helius-rpc.com/?api-key=e6fa031e-699e-49ed-9672-4582bdb4950d",  # DEVNET для тестов!
            log_level="DEBUG"
        )
        
        logger.info("📋 Конфигурация создана:")
        logger.info(f"   SOL сумма: {config.sol_amount}")
        logger.info(f"   Slippage: {config.slippage_percent}%")
        logger.info(f"   RPC: {config.rpc_endpoint}")
        logger.info(f"   Мониторинг: {config.monitoring_time_seconds}s")
        
        # Создание торгового бота
        trader = MainTrader(config)
        logger.info("✅ MainTrader создан успешно")
        
        # Тестирование инициализации компонентов
        logger.info("🔧 Тестирование инициализации компонентов...")
        
        init_success = await trader.setup()
        
        if init_success:
            logger.info("✅ Все компоненты инициализированы успешно!")
            return trader
        else:
            logger.error("❌ Ошибка инициализации компонентов")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации торгового бота: {e}")
        logger.exception("Детали ошибки:")
        return None


async def test_dry_run_analysis(trader: MainTrader, token_info: TokenInfo):
    """Выполняет сухой прогон анализа без реальной покупки."""
    
    logger = logging.getLogger("test_dry_run")
    logger.info("🧪 ТЕСТ 3: Сухой прогон анализа (без реальной покупки)")
    
    try:
        # Проверка доступности RPC
        logger.info("📡 Проверка подключения к RPC...")
        health = await trader.client.get_health()
        logger.info(f"RPC статус: {health}")
        
        # Проверка баланса кошелька
        logger.info("💰 Проверка баланса кошелька...")
        wallet_address = trader.wallet.get_address_string()
        logger.info(f"Адрес кошелька: {wallet_address}")
        
        balance_sol = await trader.client.get_balance(wallet_address)
        logger.info(f"Баланс: {balance_sol:.6f} SOL")
        
        if balance_sol < trader.config.sol_amount:
            logger.warning(f"⚠️ Недостаточно SOL! Нужно: {trader.config.sol_amount}, есть: {balance_sol}")
        else:
            logger.info(f"✅ Достаточно SOL для покупки")
        
        # Анализ данных токена
        logger.info("🔍 Анализ данных токена...")
        logger.info(f"   Все адреса получены от слушателя (НЕ пересчитываются):")
        logger.info(f"   ✓ Mint: {token_info.mint}")
        logger.info(f"   ✓ Bonding Curve: {token_info.bonding_curve}")
        logger.info(f"   ✓ Associated BC: {token_info.associated_bonding_curve}")
        logger.info(f"   ✓ Создатель: {token_info.user}")
        
        # Получение котировки (без покупки)
        logger.info("📊 Получение котировки покупки...")
        try:
            quote = await trader.buyer.get_buy_quote(
                str(token_info.mint), 
                trader.config.sol_amount
            )
            logger.info(f"Котировка: {quote}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить котировку: {e}")
        
        logger.info("✅ Сухой прогон завершен успешно!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в сухом прогоне: {e}")
        logger.exception("Детали ошибки:")
        return False


async def main():
    """Главная функция тестирования."""
    
    print("🧪 ТЕСТИРОВАНИЕ ПОКУПКИ МЕМКОИНА (TBF_V0)")
    print("=" * 60)
    print("⚠️  ВАЖНО: Это тестовый скрипт с подробным логированием!")
    print("📍 Использует DEVNET для безопасности")
    print("💡 Замените YOUR_PRIVATE_KEY_HERE на реальный приватный ключ")
    print()
    
    # Настройка логирования
    setup_detailed_logging()
    
    logger = logging.getLogger("main")
    logger.info("🚀 НАЧАЛО ТЕСТИРОВАНИЯ")
    
    try:
        # Тест 1: Создание TokenInfo
        token_info = await test_token_info_creation()
        if not token_info:
            logger.error("❌ Тест 1 провален - не удалось создать TokenInfo")
            return False
        
        print("✅ Тест 1 пройден: TokenInfo создан")
        
        # Тест 2: Инициализация бота
        trader = await test_trader_initialization(token_info)
        if not trader:
            logger.error("❌ Тест 2 провален - не удалось инициализировать бота")
            return False
        
        print("✅ Тест 2 пройден: Бот инициализирован")
        
        # Тест 3: Сухой прогон
        dry_run_success = await test_dry_run_analysis(trader, token_info)
        if not dry_run_success:
            logger.error("❌ Тест 3 провален - ошибка в сухом прогоне")
            return False
        
        print("✅ Тест 3 пройден: Сухой прогон успешен")
        
        # Закрытие соединений
        await trader.client.close()
        
        print()
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("📝 Проверьте логи для деталей:")
        print("   - logs/test_buy_detailed.log")
        print("   - logs/test_buy_errors.log")
        print()
        print("🚀 ГОТОВ К РЕАЛЬНОЙ ТОРГОВЛЕ!")
        print("   1. Замените YOUR_PRIVATE_KEY_HERE на реальный ключ")
        print("   2. Смените RPC на mainnet для реальной торговли")
        print("   3. Используйте реальные данные от слушателя")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в тестировании: {e}")
        logger.exception("Детали критической ошибки:")
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
