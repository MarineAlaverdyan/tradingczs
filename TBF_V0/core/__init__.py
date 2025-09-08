"""
Основные модули для работы с Solana блокчейном.
Включает клиент, кошелек, константы и управление приоритетными комиссиями.
"""

# Импорт констант (не требует внешних зависимостей)
from .pubkeys import *

# Условный импорт модулей с зависимостями
try:
    from .simple_client import SimpleClient
except ImportError:
    SimpleClient = None

try:
    from .simple_wallet import SimpleWallet
except ImportError:
    SimpleWallet = None

# Импорт модуля приоритетных комиссий
try:
    from .priority_fee import PriorityFeeManager
except ImportError:
    PriorityFeeManager = None

# Экспорт всех публичных классов и функций
__all__ = [
    'SimpleClient',
    'SimpleWallet', 
    'PriorityFeeManager',
    # Константы из pubkeys
    'SYSTEM_PROGRAM_ID',
    'TOKEN_PROGRAM_ID',
    'ASSOCIATED_TOKEN_PROGRAM_ID',
    'COMPUTE_BUDGET_PROGRAM_ID',
    'RENT_PROGRAM_ID',
    'PUMP_PROGRAM_ID',
    'METADATA_PROGRAM_ID',
    'RAYDIUM_AMM_PROGRAM_ID',
    'WSOL_MINT',
    'LAMPORTS_PER_SOL'
]
