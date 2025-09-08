# Анализ проекта PumpFun-BonkFun Trading Bot

## Обзор проекта

Это универсальный торговый бот для автоматической торговли токенами на платформах pump.fun и letsbonk.fun в блокчейне Solana. Основная функция - снайпинг новых токенов (быстрая покупка сразу после создания).

## Архитектура проекта

### 1. Основные компоненты

```
src/
├── bot_runner.py              # Главный запускатель ботов
├── config_loader.py           # Загрузка и валидация конфигурации
├── core/                      # Базовые компоненты
│   ├── client.py             # SolanaClient - работа с RPC
│   ├── wallet.py             # Управление кошельком
│   └── priority_fee/         # Управление комиссиями
├── trading/                   # Торговая логика
│   ├── universal_trader.py   # Основной торговый координатор
│   ├── platform_aware.py    # Покупка/продажа с учетом платформы
│   └── position.py           # Управление позициями
├── platforms/                 # Платформо-специфичные модули
│   ├── pumpfun/              # Реализация для pump.fun
│   └── letsbonk/             # Реализация для letsbonk.fun
├── monitoring/                # Система мониторинга
│   ├── listener_factory.py   # Фабрика слушателей
│   ├── universal_geyser_listener.py
│   ├── universal_logs_listener.py
│   ├── universal_block_listener.py
│   └── universal_pumpportal_listener.py
├── cleanup/                   # Система очистки аккаунтов
└── utils/                     # Утилиты (логирование и т.д.)
```

### 2. Поток выполнения программы

#### Этап 1: Инициализация
1. **bot_runner.py:main()** - точка входа
2. **load_bot_config()** - загрузка YAML конфигурации из папки `bots/`
3. **validate_platform_listener_combination()** - проверка совместимости платформы и типа слушателя
4. **get_platform_from_config()** - определение платформы (pump_fun/lets_bonk)

#### Этап 2: Создание торгового бота
1. **UniversalTrader.__init__()** - инициализация основного координатора
   - Создание SolanaClient для RPC операций
   - Инициализация Wallet из приватного ключа
   - Настройка PriorityFeeManager для управления комиссиями
   - Загрузка платформо-специфичных компонентов

#### Этап 3: Запуск мониторинга
1. **UniversalTrader.start()** - запуск торгового процесса
2. **ListenerFactory.create_listener()** - создание слушателя событий
   - **GeyserListener** - самый быстрый, требует специальный endpoint
   - **LogsListener** - WebSocket подписка на логи
   - **BlockListener** - подписка на блоки
   - **PumpPortalListener** - сторонний агрегатор

#### Этап 4: Обработка событий
1. **Listener.on_token_created()** - обнаружение нового токена
2. **validate_token()** - проверка возраста токена и фильтров
3. **PlatformAwareBuyer.buy_token()** - покупка токена
4. **Position.create()** - создание позиции для отслеживания

#### Этап 5: Управление позициями
1. **ExitStrategy** - стратегии выхода:
   - **time_based** - продажа через фиксированное время
   - **tp_sl** - take profit / stop loss
   - **manual** - ручная продажа
2. **PlatformAwareSeller.sell_token()** - продажа токена
3. **Cleanup** - очистка токен-аккаунтов

### 3. Ключевые классы и их функции

#### UniversalTrader
- **Основной координатор** всех торговых операций
- Управляет жизненным циклом позиций
- Координирует работу всех компонентов

#### SolanaClient
- **Абстракция для работы с Solana RPC**
- Кэширование blockhash для оптимизации
- Отправка транзакций с retry логикой
- Подтверждение транзакций

#### PlatformAwareBuyer/Seller
- **Универсальные компоненты** для покупки/продажи
- Автоматически используют правильные инструкции для каждой платформы
- Обработка slippage и priority fees

#### Platform-specific модули
- **AddressProvider** - адреса программ и аккаунтов
- **InstructionBuilder** - создание инструкций для транзакций
- **EventParser** - парсинг событий блокчейна
- **CurveManager** - работа с bonding curve

### 4. Конфигурация бота

Боты настраиваются через YAML файлы в папке `bots/`:

```yaml
name: "bot-sniper-1"
platform: "pump_fun"
enabled: true
separate_process: true

# Подключение к Solana
rpc_endpoint: "${SOLANA_NODE_RPC_ENDPOINT}"
wss_endpoint: "${SOLANA_NODE_WSS_ENDPOINT}"
private_key: "${SOLANA_PRIVATE_KEY}"

# Торговые параметры
trade:
  buy_amount: 0.0001          # SOL для покупки
  buy_slippage: 0.3           # 30% slippage
  sell_slippage: 0.3
  exit_strategy: "time_based"
  max_hold_time: 15           # секунд
  extreme_fast_mode: true     # быстрый режим

# Комиссии
priority_fees:
  enable_fixed: true
  fixed_amount: 1_000_000     # микроламports

# Фильтры токенов
filters:
  listener_type: "geyser"
  max_token_age: 0.001        # максимальный возраст токена
  match_string: null          # фильтр по названию
  marry_mode: false           # только покупка
  yolo_mode: false            # непрерывная торговля
```

### 5. Типы слушателей и их особенности

#### Geyser Listener
- **Самый быстрый** способ получения данных
- Требует специальный Geyser endpoint
- Прямой поток данных от валидатора

#### Logs Listener
- WebSocket подписка на логи программ
- Хороший баланс скорости и доступности
- Поддерживается большинством RPC провайдеров

#### Block Listener
- Подписка на новые блоки
- Более медленный, но надежный
- Не все провайдеры поддерживают

#### PumpPortal Listener
- Сторонний агрегатор данных
- Простая интеграция
- Зависимость от внешнего сервиса

### 6. Стратегии выхода

#### Time-based
- Продажа через фиксированное время после покупки
- Простая и предсказуемая стратегия

#### Take Profit / Stop Loss
- Продажа при достижении целевой прибыли или убытка
- Требует постоянный мониторинг цены

#### Manual
- Ручное управление продажами
- Для продвинутых пользователей

### 7. Режимы работы

#### Extreme Fast Mode
- Пропускает проверки цены и стабилизации bonding curve
- Покупает фиксированное количество токенов
- Максимальная скорость, минимальная точность

#### Marry Mode
- Только покупка токенов без продажи
- Стратегия накопления

#### YOLO Mode
- Непрерывная торговля без пауз
- Высокий риск, высокая активность

### 8. Система очистки (Cleanup)

#### Режимы очистки:
- **disabled** - без очистки
- **on_fail** - очистка при неудачной покупке
- **after_sell** - очистка после продажи
- **post_session** - очистка в конце сессии

#### Функции:
- Закрытие пустых токен-аккаунтов
- Возврат SOL от аренды аккаунтов
- Опциональное сжигание остатков токенов

## Последовательность работы основных функций

### 1. Запуск бота
```
main() → run_all_bots() → start_bot() → UniversalTrader.__init__() → trader.start()
```

### 2. Обнаружение токена
```
Listener.start() → on_token_created() → validate_token() → process_new_token()
```

### 3. Покупка токена
```
buy_token() → build_buy_instruction() → send_transaction() → confirm_transaction()
```

### 4. Управление позицией
```
create_position() → monitor_position() → check_exit_conditions() → sell_token()
```

### 5. Продажа токена
```
sell_token() → build_sell_instruction() → send_transaction() → cleanup_if_needed()
```

## Зависимости и технологии

- **Python 3.9+** - основной язык
- **solana** - SDK для работы с Solana
- **websockets** - WebSocket соединения
- **aiohttp** - HTTP клиент
- **grpcio** - gRPC для Geyser
- **pyyaml** - парсинг конфигурации
- **uvloop** - быстрый event loop

## Особенности реализации

1. **Модульная архитектура** - легко добавлять новые платформы
2. **Асинхронность** - все операции неблокирующие
3. **Кэширование** - blockhash и другие данные кэшируются
4. **Retry логика** - автоматические повторы при ошибках
5. **Приоритетные комиссии** - для быстрого включения в блок
6. **Мультипроцессность** - каждый бот может работать в отдельном процессе
