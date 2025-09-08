# ДЕТАЛЬНАЯ СХЕМА РАБОТЫ PUMPFUN-BONKFUN-BOT

## 🚀 ТОЧКА ВХОДА И ИНИЦИАЛИЗАЦИЯ

### 1. Запуск бота (`src/bot_runner.py`)

**Файл:** `src/bot_runner.py`
**Функция:** `start_bot(config_path: str)`

```
ПОТОК ВЫПОЛНЕНИЯ:
1. load_bot_config(config_path) → загружает YAML конфиг
2. setup_logging(cfg["name"]) → настраивает логирование
3. print_config_summary(cfg) → выводит сводку конфига
4. get_platform_from_config(cfg) → определяет платформу (pump.fun/letsbonk.fun)
5. Валидация поддержки платформы через platform_factory
6. validate_platform_listener_combination() → проверяет совместимость listener'а с платформой
7. Создание UniversalTrader с параметрами из конфига
8. trader.start() → запуск торгового процесса
```

**Ключевые файлы на этом этапе:**
- `config_loader.py` - загрузка и валидация конфига
- `platforms/__init__.py` - фабрика платформ
- `utils/logger.py` - система логирования

---

## 🎯 СОЗДАНИЕ UNIVERSAL TRADER

### 2. Инициализация UniversalTrader (`src/trading/universal_trader.py`)

**Файл:** `src/trading/universal_trader.py`
**Класс:** `UniversalTrader.__init__()`

```
СОЗДАНИЕ КОМПОНЕНТОВ:
1. SolanaClient(rpc_endpoint) → подключение к Solana RPC
2. Wallet(private_key) → загрузка приватного ключа
3. PriorityFeeManager() → управление комиссиями
4. get_platform_implementations() → получение платформо-специфичных реализаций
5. PlatformAwareBuyer() → покупатель токенов
6. PlatformAwareSeller() → продавец токенов
7. ListenerFactory.create_listener() → создание слушателя событий
```

**Состояние после инициализации:**
- `self.traded_mints: set[Pubkey]` - отслеженные токены
- `self.token_queue: asyncio.Queue` - очередь токенов для обработки
- `self.processing: bool = False` - флаг обработки
- `self.processed_tokens: set[str]` - обработанные токены
- `self.token_timestamps: dict[str, float]` - временные метки токенов

---

## 👂 СИСТЕМА МОНИТОРИНГА

### 3. Создание Listener'а (`src/monitoring/listener_factory.py`)

**Файл:** `src/monitoring/listener_factory.py`
**Функция:** `ListenerFactory.create_listener()`

```
ТИПЫ LISTENER'ОВ:
1. "geyser" → UniversalGeyserListener (самый быстрый)
2. "logs" → UniversalLogsListener (WebSocket подписка на логи)
3. "blocks" → UniversalBlocksListener (подписка на блоки)
4. "pumpportal" → PumpPortalListener (внешний агрегатор)
```

**Каждый listener:**
- Фильтрует события по указанным платформам
- Парсит транзакции и извлекает информацию о новых токенах
- Вызывает callback функцию при обнаружении нового токена

---

## 🔄 ОСНОВНОЙ ЦИКЛ ТОРГОВЛИ

### 4. Запуск торгового процесса (`UniversalTrader.start()`)

**Файл:** `src/trading/universal_trader.py`
**Функция:** `start()`

```
РЕЖИМЫ РАБОТЫ:

A) SINGLE TOKEN MODE (yolo_mode = False):
   1. _wait_for_token() → ждет первый подходящий токен
   2. _handle_token(token_info) → обрабатывает токен
   3. Завершение работы

B) CONTINUOUS MODE (yolo_mode = True):
   1. Создание processor_task = _process_token_queue()
   2. token_listener.listen_for_tokens(callback=_on_new_token)
   3. Бесконечный цикл обработки токенов
```

---

## 🎯 ОБРАБОТКА НОВОГО ТОКЕНА

### 5. Callback при обнаружении токена (`_on_new_token()`)

**Файл:** `src/trading/universal_trader.py`
**Функция:** `_on_new_token(token_info: TokenInfo)`

```
ПОТОК ОБРАБОТКИ:
1. Проверка возраста токена (max_token_age)
2. Проверка дубликатов (processed_tokens)
3. Фильтрация по match_string (если указан)
4. Фильтрация по creator address (bro_address)
5. Добавление в token_queue для обработки
6. Логирование информации о токене
```

---

## 💰 ПРОЦЕСС ПОКУПКИ

### 6. Обработка токена (`_handle_token()`)

**Файл:** `src/trading/universal_trader.py`
**Функция:** `_handle_token(token_info: TokenInfo)`

```
ЭТАПЫ ОБРАБОТКИ:
1. Ожидание после создания (wait_time_after_creation)
2. Проверка баланса кошелька
3. buyer.execute(token_info) → покупка токена
4. Обработка результата покупки
5. Если успешно → переход к стратегии выхода
6. Если неудачно → cleanup при необходимости
```

### 7. Выполнение покупки (`PlatformAwareBuyer.execute()`)

**Файл:** `src/trading/platform_aware.py`
**Класс:** `PlatformAwareBuyer`

```
ПРОЦЕСС ПОКУПКИ:
1. get_platform_implementations() → получение платформо-специфичных компонентов
2. address_provider.get_mint_address() → получение адреса токена
3. instruction_builder.build_buy_instruction() → создание инструкции покупки
4. Расчет приоритетной комиссии
5. Отправка транзакции через SolanaClient
6. Подтверждение транзакции
7. Возврат TradeResult с результатами
```

---

## 📊 СТРАТЕГИИ ВЫХОДА

### 8. Управление позицией (`_manage_position()`)

**Файл:** `src/trading/universal_trader.py`
**Функция:** `_manage_position()`

```
СТРАТЕГИИ ВЫХОДА:

A) TIME_BASED:
   1. Ожидание max_hold_time секунд
   2. Продажа всех токенов

B) TP_SL (Take Profit / Stop Loss):
   1. Мониторинг цены каждые price_check_interval секунд
   2. Проверка условий:
      - Take Profit: цена выросла на take_profit_percentage%
      - Stop Loss: цена упала на stop_loss_percentage%
      - Max Hold Time: превышено максимальное время удержания
   3. Продажа при срабатывании любого условия

C) MANUAL:
   1. Ожидание внешнего сигнала для продажи
```

---

## 💸 ПРОЦЕСС ПРОДАЖИ

### 9. Выполнение продажи (`PlatformAwareSeller.execute()`)

**Файл:** `src/trading/platform_aware.py`
**Класс:** `PlatformAwareSeller`

```
ПРОЦЕСС ПРОДАЖИ:
1. Получение баланса токенов
2. get_platform_implementations() → платформо-специфичные компоненты
3. instruction_builder.build_sell_instruction() → создание инструкции продажи
4. Расчет приоритетной комиссии
5. Отправка транзакции
6. Подтверждение транзакции
7. Возврат TradeResult с результатами
```

---

## 🧹 СИСТЕМА CLEANUP

### 10. Очистка после торговли

**Файлы:** `src/cleanup/modes.py`

```
РЕЖИМЫ CLEANUP:

A) handle_cleanup_after_sell():
   - Закрытие token accounts
   - Возврат SOL с аккаунтов

B) handle_cleanup_after_failure():
   - Очистка после неудачной торговли
   - Закрытие частично созданных аккаунтов

C) handle_cleanup_post_session():
   - Финальная очистка после сессии
   - Закрытие всех связанных аккаунтов
```

---

## 🏗️ ПЛАТФОРМО-СПЕЦИФИЧНЫЕ КОМПОНЕНТЫ

### 11. Platform Implementations

**Файлы:** `src/platforms/pumpfun/`, `src/platforms/letsbonk/`

```
КАЖДАЯ ПЛАТФОРМА ПРЕДОСТАВЛЯЕТ:

1. AddressProvider:
   - get_mint_address() → адрес mint токена
   - get_bonding_curve_address() → адрес bonding curve
   - get_associated_token_address() → адрес token account

2. InstructionBuilder:
   - build_buy_instruction() → инструкция покупки
   - build_sell_instruction() → инструкция продажи

3. EventParser:
   - parse_create_event() → парсинг события создания токена
   - parse_trade_event() → парсинг события торговли

4. CurveManager:
   - calculate_buy_price() → расчет цены покупки
   - calculate_sell_price() → расчет цены продажи
   - get_curve_state() → состояние bonding curve
```

---

## 🔌 ТИПЫ LISTENER'ОВ В ДЕТАЛЯХ

### 12. Geyser Listener (Самый быстрый)

**Файл:** `src/monitoring/universal_geyser_listener.py`

```
ПРИНЦИП РАБОТЫ:
1. gRPC подключение к Geyser серверу
2. Подписка на изменения аккаунтов программы
3. Фильтрация по discriminator создания токена
4. Парсинг данных аккаунта
5. Извлечение информации о токене
6. Вызов callback с TokenInfo
```

### 13. Logs Listener

**Файл:** `src/monitoring/universal_logs_listener.py`

```
ПРИНЦИП РАБОТЫ:
1. WebSocket подключение к Solana RPC
2. logsSubscribe на программу платформы
3. Фильтрация логов по signature создания
4. Получение полной транзакции
5. Парсинг инструкций создания токена
6. Вызов callback с TokenInfo
```

### 14. Blocks Listener

**Файл:** `src/monitoring/universal_blocks_listener.py`

```
ПРИНЦИП РАБОТЫ:
1. WebSocket подключение к Solana RPC
2. blockSubscribe на новые блоки
3. Анализ всех транзакций в блоке
4. Поиск транзакций с программой платформы
5. Парсинг инструкций создания токена
6. Вызов callback с TokenInfo
```

### 15. PumpPortal Listener

**Файл:** `src/monitoring/pumpportal_listener.py`

```
ПРИНЦИП РАБОТЫ:
1. WebSocket подключение к PumpPortal API
2. Получение готовых событий создания токенов
3. Конвертация в TokenInfo формат
4. Фильтрация по платформам
5. Вызов callback с TokenInfo
```

---

## 📋 ДИАГРАММА ПОТОКА ВЫПОЛНЕНИЯ

```
┌─────────────────┐
│   bot_runner    │ ← Точка входа
│   start_bot()   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  config_loader  │ ← Загрузка конфига
│ load_bot_config │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ UniversalTrader │ ← Создание трейдера
│    __init__     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ ListenerFactory │ ← Создание слушателя
│ create_listener │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ UniversalTrader │ ← Запуск торговли
│     start()     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│   Listener      │ ← Мониторинг токенов
│ listen_for_     │
│    tokens()     │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ _on_new_token() │ ← Callback нового токена
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ _handle_token() │ ← Обработка токена
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│PlatformAware    │ ← Покупка токена
│Buyer.execute()  │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│_manage_position │ ← Управление позицией
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│PlatformAware    │ ← Продажа токена
│Seller.execute() │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│  Cleanup        │ ← Очистка аккаунтов
│   System        │
└─────────────────┘
```

---

## 🔍 КЛЮЧЕВЫЕ ФАЙЛЫ И ИХ РОЛИ

### Основные компоненты:
1. **`src/bot_runner.py`** - Точка входа, инициализация
2. **`src/trading/universal_trader.py`** - Главный координатор торговли
3. **`src/config_loader.py`** - Загрузка и валидация конфигурации
4. **`src/core/client.py`** - Абстракция Solana RPC
5. **`src/core/wallet.py`** - Управление кошельком
6. **`src/core/priority_fee/manager.py`** - Управление комиссиями

### Мониторинг:
7. **`src/monitoring/listener_factory.py`** - Фабрика слушателей
8. **`src/monitoring/universal_*_listener.py`** - Реализации слушателей

### Торговля:
9. **`src/trading/platform_aware.py`** - Покупка/продажа токенов
10. **`src/trading/position.py`** - Управление позициями

### Платформы:
11. **`src/platforms/pumpfun/`** - Pump.fun специфичные компоненты
12. **`src/platforms/letsbonk/`** - Letsbonk.fun специфичные компоненты

### Очистка:
13. **`src/cleanup/modes.py`** - Система очистки аккаунтов

---

## 📊 СОСТОЯНИЕ И ДАННЫЕ

### Основные структуры данных:
- **`TokenInfo`** - Информация о токене (mint, название, символ, платформа)
- **`TradeResult`** - Результат торговой операции
- **`Position`** - Информация о позиции

### Состояние UniversalTrader:
- **`traded_mints`** - Множество уже торгованных токенов
- **`token_queue`** - Очередь токенов для обработки
- **`processed_tokens`** - Множество обработанных токенов
- **`token_timestamps`** - Временные метки токенов

---

## ⚙️ КОНФИГУРАЦИЯ

### Основные параметры:
- **Подключение:** `rpc_endpoint`, `wss_endpoint`, `private_key`
- **Торговля:** `buy_amount`, `buy_slippage`, `sell_slippage`
- **Стратегия выхода:** `exit_strategy`, `take_profit_percentage`, `stop_loss_percentage`
- **Фильтры:** `match_string`, `bro_address`, `listener_type`
- **Режимы:** `yolo_mode`, `marry_mode`, `extreme_fast_mode`

Эта схема показывает полный поток выполнения от запуска бота до завершения торговли с детализацией каждого этапа и указанием конкретных файлов и функций.
