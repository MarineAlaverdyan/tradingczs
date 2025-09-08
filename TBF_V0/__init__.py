"""
TBF_V0 - Модульная архитектура для pump.fun торгового бота.

Основные модули:
- core: базовые компоненты (клиент, кошелек)
- pumpfun: специфичные для pump.fun компоненты
- monitoring: мониторинг блокчейна
- tests: тестовые модули
"""

__version__ = "0.1.0"
__author__ = "Trading Bot Framework"

# Экспортируем основные классы для удобства импорта
try:
    from .core.simple_client import SimpleClient
    from .core.simple_wallet import SimpleWallet
    from .pumpfun.address_provider import AddressProvider
    from .pumpfun.curve_manager import CurveManager
    from .pumpfun.event_parser import EventParser
    from .monitoring.simple_block_listener import SimpleBlockListener
    
    __all__ = [
        'SimpleClient',
        'SimpleWallet', 
        'AddressProvider',
        'CurveManager',
        'EventParser',
        'SimpleBlockListener'
    ]
except ImportError:
    # Если модули не найдены, просто пропускаем
    __all__ = []
