"""
Config Loader - модуль для загрузки и валидации конфигурации ботов.

Этот модуль отвечает за:
- Загрузку YAML конфигураций из файлов
- Подстановку переменных окружения (${VARIABLE})
- Валидацию обязательных полей
- Проверку совместимости платформ и слушателей
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

from interfaces.core import Platform, ListenerType, ConfigurationError
from utils.logger import get_logger

logger = get_logger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Обязательные поля в конфигурации
REQUIRED_FIELDS = [
    "name",
    "rpc_endpoint", 
    "wss_endpoint",
    "private_key",
    "trade.buy_amount",
    "trade.buy_slippage", 
    "trade.sell_slippage",
    "filters.listener_type",
    "filters.max_token_age",
]

# Правила валидации для числовых полей
VALIDATION_RULES = [
    ("trade.buy_amount", (int, float), 0, float("inf"), "buy_amount must be positive"),
    ("trade.buy_slippage", (int, float), 0, 1, "buy_slippage must be between 0 and 1"),
    ("trade.sell_slippage", (int, float), 0, 1, "sell_slippage must be between 0 and 1"),
    ("priority_fees.fixed_amount", int, 0, float("inf"), "fixed_amount must be non-negative"),
    ("priority_fees.extra_percentage", (int, float), 0, 1, "extra_percentage must be between 0 and 1"),
    ("priority_fees.hard_cap", int, 0, float("inf"), "hard_cap must be non-negative"),
    ("retries.max_attempts", int, 0, 100, "max_attempts must be between 0 and 100"),
    ("filters.max_token_age", (int, float), 0, float("inf"), "max_token_age must be non-negative"),
]

# Допустимые значения для enum-подобных полей
VALID_VALUES = {
    "filters.listener_type": ["logs", "blocks", "geyser", "pumpportal"],
    "cleanup.mode": ["disabled", "on_fail", "after_sell", "post_session"],
    "trade.exit_strategy": ["time_based", "tp_sl", "manual"],
    "platform": ["pump_fun", "lets_bonk"],
}

# Совместимость платформ и слушателей
PLATFORM_LISTENER_COMPATIBILITY = {
    Platform.PUMP_FUN: [ListenerType.LOGS, ListenerType.BLOCKS, ListenerType.GEYSER, ListenerType.PUMPPORTAL],
    Platform.LETS_BONK: [ListenerType.LOGS, ListenerType.BLOCKS, ListenerType.GEYSER],  # PumpPortal только для PumpFun
}


def load_bot_config(config_path: str) -> Dict[str, Any]:
    """
    Загрузить и валидировать конфигурацию бота из YAML файла.
    
    Процесс загрузки:
    1. Читаем YAML файл
    2. Заменяем переменные окружения ${VARIABLE}
    3. Валидируем обязательные поля
    4. Проверяем типы и диапазоны значений
    5. Валидируем enum значения
    
    Args:
        config_path: Путь к YAML файлу конфигурации
        
    Returns:
        Словарь с валидированной конфигурацией
        
    Raises:
        ConfigurationError: При ошибках в конфигурации
    """
    try:
        # Читаем YAML файл
        config_file = Path(config_path)
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config:
            raise ConfigurationError(f"Empty configuration file: {config_path}")
        
        logger.info(f"Loaded configuration from {config_path}")
        
        # Заменяем переменные окружения
        config = _substitute_environment_variables(config)
        
        # Валидируем конфигурацию
        _validate_configuration(config)
        
        logger.info(f"Configuration validated successfully for bot: {config.get('name', 'unknown')}")
        return config
        
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML syntax in {config_path}: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration from {config_path}: {e}")


def _substitute_environment_variables(config: Any) -> Any:
    """
    Рекурсивно заменить переменные окружения в конфигурации.
    
    Поддерживает синтаксис ${VARIABLE_NAME} и ${VARIABLE_NAME:-default_value}
    
    Args:
        config: Конфигурация (может быть dict, list, str)
        
    Returns:
        Конфигурация с замененными переменными
    """
    if isinstance(config, dict):
        return {key: _substitute_environment_variables(value) for key, value in config.items()}
    elif isinstance(config, list):
        return [_substitute_environment_variables(item) for item in config]
    elif isinstance(config, str):
        return _substitute_string_variables(config)
    else:
        return config


def _substitute_string_variables(text: str) -> str:
    """
    Заменить переменные окружения в строке.
    
    Поддерживаемые форматы:
    - ${VARIABLE} - обязательная переменная
    - ${VARIABLE:-default} - переменная с значением по умолчанию
    
    Args:
        text: Строка с переменными
        
    Returns:
        Строка с замененными переменными
        
    Raises:
        ConfigurationError: Если обязательная переменная не найдена
    """
    def replace_var(match):
        var_expr = match.group(1)
        
        # Проверяем наличие значения по умолчанию
        if ':-' in var_expr:
            var_name, default_value = var_expr.split(':-', 1)
            return os.getenv(var_name, default_value)
        else:
            var_name = var_expr
            value = os.getenv(var_name)
            if value is None:
                raise ConfigurationError(f"Required environment variable not found: {var_name}")
            return value
    
    # Регулярное выражение для поиска ${VARIABLE} или ${VARIABLE:-default}
    pattern = r'\$\{([^}]+)\}'
    return re.sub(pattern, replace_var, text)


def _validate_configuration(config: Dict[str, Any]) -> None:
    """
    Валидировать конфигурацию бота.
    
    Проверяет:
    1. Наличие обязательных полей
    2. Типы и диапазоны числовых значений
    3. Допустимые значения для enum полей
    
    Args:
        config: Конфигурация для валидации
        
    Raises:
        ConfigurationError: При ошибках валидации
    """
    # Проверяем обязательные поля
    _validate_required_fields(config)
    
    # Проверяем числовые поля
    _validate_numeric_fields(config)
    
    # Проверяем enum поля
    _validate_enum_fields(config)
    
    logger.debug("All configuration validations passed")


def _validate_required_fields(config: Dict[str, Any]) -> None:
    """Проверить наличие всех обязательных полей."""
    missing_fields = []
    
    for field_path in REQUIRED_FIELDS:
        if not _get_nested_value(config, field_path):
            missing_fields.append(field_path)
    
    if missing_fields:
        raise ConfigurationError(f"Missing required fields: {', '.join(missing_fields)}")


def _validate_numeric_fields(config: Dict[str, Any]) -> None:
    """Проверить числовые поля на соответствие типам и диапазонам."""
    for field_path, expected_type, min_val, max_val, error_msg in VALIDATION_RULES:
        value = _get_nested_value(config, field_path)
        
        # Пропускаем отсутствующие необязательные поля
        if value is None:
            continue
            
        # Проверяем тип
        if not isinstance(value, expected_type):
            raise ConfigurationError(f"Field {field_path}: {error_msg} (got {type(value).__name__})")
        
        # Проверяем диапазон
        if not (min_val <= value <= max_val):
            raise ConfigurationError(f"Field {field_path}: {error_msg} (got {value})")


def _validate_enum_fields(config: Dict[str, Any]) -> None:
    """Проверить enum поля на допустимые значения."""
    for field_path, valid_values in VALID_VALUES.items():
        value = _get_nested_value(config, field_path)
        
        # Пропускаем отсутствующие необязательные поля
        if value is None:
            continue
            
        if value not in valid_values:
            raise ConfigurationError(
                f"Field {field_path}: invalid value '{value}'. "
                f"Valid values: {', '.join(valid_values)}"
            )


def _get_nested_value(config: Dict[str, Any], field_path: str) -> Any:
    """
    Получить значение по вложенному пути (например, 'trade.buy_amount').
    
    Args:
        config: Конфигурация
        field_path: Путь к полю через точку
        
    Returns:
        Значение поля или None если не найдено
    """
    keys = field_path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value


def get_platform_from_config(config: Dict[str, Any]) -> Platform:
    """
    Получить платформу из конфигурации.
    
    Args:
        config: Конфигурация бота
        
    Returns:
        Enum платформы
        
    Raises:
        ConfigurationError: Если платформа не указана или неподдерживается
    """
    platform_str = config.get("platform", "pump_fun")  # По умолчанию pump_fun
    
    try:
        return Platform(platform_str)
    except ValueError:
        supported_platforms = [p.value for p in Platform]
        raise ConfigurationError(
            f"Unsupported platform: {platform_str}. "
            f"Supported platforms: {', '.join(supported_platforms)}"
        )


def validate_platform_listener_combination(platform: Platform, listener_type: str) -> bool:
    """
    Проверить совместимость платформы и типа слушателя.
    
    Args:
        platform: Платформа
        listener_type: Тип слушателя
        
    Returns:
        True если комбинация поддерживается
    """
    try:
        listener_enum = ListenerType(listener_type)
        supported_listeners = PLATFORM_LISTENER_COMPATIBILITY.get(platform, [])
        return listener_enum in supported_listeners
    except ValueError:
        return False


def get_supported_listeners_for_platform(platform: Platform) -> List[str]:
    """
    Получить список поддерживаемых слушателей для платформы.
    
    Args:
        platform: Платформа
        
    Returns:
        Список строковых названий слушателей
    """
    supported_listeners = PLATFORM_LISTENER_COMPATIBILITY.get(platform, [])
    return [listener.value for listener in supported_listeners]


def print_config_summary(config: Dict[str, Any]) -> None:
    """
    Вывести краткую сводку конфигурации бота.
    
    Args:
        config: Конфигурация бота
    """
    bot_name = config.get("name", "Unknown")
    platform = config.get("platform", "pump_fun")
    listener_type = config.get("filters", {}).get("listener_type", "unknown")
    buy_amount = config.get("trade", {}).get("buy_amount", 0)
    enabled = config.get("enabled", True)
    
    logger.info(f"Bot Configuration Summary:")
    logger.info(f"  Name: {bot_name}")
    logger.info(f"  Platform: {platform}")
    logger.info(f"  Listener: {listener_type}")
    logger.info(f"  Buy Amount: {buy_amount} SOL")
    logger.info(f"  Enabled: {enabled}")
    
    if not enabled:
        logger.warning(f"Bot '{bot_name}' is disabled and will be skipped")
