# Trading Bot From Scratch

Торговый бот для автоматической торговли токенами на платформах pump.fun и letsbonk.fun, построенный с нуля для глубокого понимания архитектуры.

## 🎯 Цель проекта

Этот проект создан для изучения и понимания работы торговых ботов путем пошаговой реализации всех компонентов с нуля. Каждый модуль подробно документирован и объяснен.

## 📁 Структура проекта

```
trading-bot-from-scratch/
├── src/
│   ├── interfaces/           # Базовые интерфейсы и типы
│   │   └── core.py          # Platform, TokenInfo, исключения
│   ├── utils/               # Утилиты
│   │   └── logger.py        # Система логирования
│   ├── core/                # Основные компоненты
│   │   ├── client.py        # SolanaClient - работа с RPC
│   │   └── wallet.py        # Wallet - управление кошельком
│   ├── config_loader.py     # Загрузка и валидация конфигурации
│   ├── platforms/           # Платформо-специфичные модули
│   ├── monitoring/          # Система мониторинга событий
│   ├── trading/             # Торговая логика
│   └── bot_runner.py        # Главный запускатель
├── bots/                    # Конфигурации ботов (YAML)
├── logs/                    # Логи работы ботов
├── tests/                   # Тесты
├── pyproject.toml          # Зависимости и настройки
├── .env.example            # Пример переменных окружения
├── DEVELOPMENT_PLAN.md     # План разработки
└── README.md               # Этот файл
```

## 🚀 Реализованные модули

### ✅ Фаза 1: Базовая инфраструктура
- **interfaces/core.py** - Базовые интерфейсы, типы данных и исключения
- **utils/logger.py** - Система логирования с ротацией файлов
- **pyproject.toml** - Настройка зависимостей и инструментов разработки

### ✅ Фаза 2: Solana клиент и кошелек  
- **core/client.py** - SolanaClient с кэшированием blockhash и retry логикой
- **core/wallet.py** - Wallet для управления приватными ключами и балансом

### ✅ Фаза 3: Конфигурация
- **config_loader.py** - Загрузка YAML конфигураций с валидацией

## 🔧 Ключевые особенности реализованных модулей

### SolanaClient (core/client.py)
```python
# Кэширование blockhash для оптимизации
async def get_cached_blockhash(self) -> Hash:
    # Blockhash кэшируется и обновляется каждые 5 секунд
    # Экономит 100-300ms на каждой транзакции

# Retry логика с экспоненциальной задержкой
async def build_and_send_transaction(self, ...):
    for attempt in range(max_retries):
        try:
            # Отправка транзакции
        except Exception:
            wait_time = 2 ** attempt  # 1s, 2s, 4s...
            await asyncio.sleep(wait_time)
```

### Wallet (core/wallet.py)
```python
# Поддержка разных форматов приватных ключей
def _load_keypair_from_string(self, private_key: str):
    if private_key.startswith('0x'):
        # Hex формат
        key_bytes = bytes.fromhex(private_key[2:])
    else:
        # Base58 формат (стандартный для Solana)
        key_bytes = base58.b58decode(private_key)
```

### Config Loader (config_loader.py)
```python
# Подстановка переменных окружения
# ${SOLANA_PRIVATE_KEY} → значение из .env файла
config = _substitute_environment_variables(config)

# Валидация обязательных полей и типов
_validate_configuration(config)
```

## 📋 План дальнейшей разработки

### 🔄 В процессе: Фаза 4 - Platform-specific компоненты
- [ ] PumpFunAddressProvider - адреса программ и аккаунтов
- [ ] PumpFunInstructionBuilder - создание инструкций для транзакций
- [ ] PumpFunEventParser - парсинг событий блокчейна
- [ ] PumpFunCurveManager - работа с bonding curve

### 📅 Следующие фазы:
- **Фаза 5**: Система мониторинга (Listeners)
- **Фаза 6**: Торговая логика (Buyer/Seller)
- **Фаза 7**: UniversalTrader (основной координатор)
- **Фаза 8**: Система очистки
- **Фаза 9**: Bot Runner
- **Фаза 10**: Тестирование

## 🛠 Установка и настройка

### Требования
- Python 3.9+
- uv (для управления зависимостями)

### Установка
```bash
# Клонировать репозиторий
cd trading-bot-from-scratch

# Установить зависимости
uv sync

# Скопировать пример конфигурации
cp .env.example .env

# Отредактировать .env файл с вашими настройками
```

### Настройка .env
```bash
# Solana RPC Configuration
SOLANA_NODE_RPC_ENDPOINT=https://api.mainnet-beta.solana.com
SOLANA_NODE_WSS_ENDPOINT=wss://api.mainnet-beta.solana.com

# Private key for trading wallet (base58 encoded)
SOLANA_PRIVATE_KEY=your_private_key_here

# Geyser configuration (optional)
GEYSER_ENDPOINT=
GEYSER_API_TOKEN=
```

## 🧪 Тестирование модулей

```bash
# Запуск всех тестов
uv run pytest

# Тестирование конкретного модуля
uv run pytest tests/test_client.py

# Проверка типов
uv run mypy src/

# Линтинг кода
uv run ruff check src/
```

## 📚 Обучающие материалы

### Архитектурные решения

1. **Модульность** - каждый компонент независим и может быть заменен
2. **Асинхронность** - все операции неблокирующие для максимальной производительности
3. **Кэширование** - критически важные данные кэшируются для скорости
4. **Retry логика** - автоматические повторы при временных ошибках
5. **Валидация** - строгая проверка всех входных данных

### Ключевые концепции Solana

- **Blockhash** - хэш последнего блока, нужен для каждой транзакции
- **Priority Fees** - дополнительная комиссия для быстрого включения в блок
- **Compute Units** - лимит вычислений для транзакции
- **Token Accounts** - аккаунты для хранения токенов (нужно создавать и закрывать)

## 🔍 Мониторинг и отладка

### Логирование
```python
from utils.logger import setup_dual_logging

# Настройка логирования в консоль и файл
setup_dual_logging(
    log_file="logs/bot.log",
    console_level=logging.INFO,
    file_level=logging.DEBUG
)
```

### Структура логов
```
2024-01-01 12:00:00 - core.client - INFO - Transaction sent successfully: 5K7x...
2024-01-01 12:00:01 - core.wallet - INFO - Balance check passed: 1.5 SOL available
2024-01-01 12:00:02 - config_loader - INFO - Configuration validated for bot: sniper-1
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Добавьте тесты для нового кода
4. Убедитесь, что все тесты проходят
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE

## 🔗 Полезные ссылки

- [Solana Documentation](https://docs.solana.com/)
- [Pump.fun API](https://docs.pump.fun/)
- [Python Solana SDK](https://github.com/michaelhly/solana-py)
- [Chainstack Solana Nodes](https://chainstack.com/)
