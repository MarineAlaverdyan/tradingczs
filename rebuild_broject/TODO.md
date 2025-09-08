# Задачи по проекту "Воссоздание Pump.fun слушателя"

## Модуль слушателя blockSubscribe
- [x] Воссоздать `block_subscriber_original_logic.py` с базовой логикой подписки на блоки.
- [x] Добавить в вывод для каждого токена поле со временем его существования (event_timestamp_ms).

## Предстоящие задачи для полного воссоздания проекта

7
### 1. Core Functionality (Основные функции)
- [ ] `config_loader.py`: Менеджер конфигурации для загрузки настроек бота.
- [ ] `core/client.py`: Абстракция клиента Solana RPC для взаимодействия с блокчейном.
- [ ] `core/wallet.py`: Модуль для управления операциями с кошельком (подписание транзакций, баланс).
- [ ] `core/priority_fee/dynamic_fee.py`: Логика для динамического расчета приоритетных комиссий.
- [ ] `core/priority_fee/fixed_fee.py`: Логика для использования фиксированных приоритетных комиссий.
- [ ] `core/priority_fee/manager.py`: Менеджер для выбора и применения приоритетных комиссий.
- [ ] `core/pubkeys.py`: Константы с публичными ключами различных программ Solana.

6 
### 2. Monitoring and Listening (Мониторинг и слушатели)
- [ ] `monitoring/base_listener.py`: Абстрактный базовый класс для всех слушателей.
- [ ] `monitoring/listener_factory.py`: Фабрика для создания различных типов слушателей.
- [ ] `monitoring/universal_block_listener.py`: Универсальный слушатель блоков (будет использовать логику `block_subscriber_original_logic.py`).
- [ ] `monitoring/universal_geyser_listener.py`: Слушатель, использующий Geyser-протокол для получения данных.
- [ ] `monitoring/universal_logs_listener.py`: Слушатель, работающий через подписку на логи транзакций.
- [ ] `monitoring/universal_pumpportal_listener.py`: Слушатель для данных из Pump.portal.

5 
### 3. Platforms (Платформы) - Пример для Pump.fun
- [ ] `platforms/pumpfun/address_provider.py`: Предоставляет специфичные для Pump.fun адреса программ.
- [ ] `platforms/pumpfun/curve_manager.py`: Управление и расчеты, связанные с кривой бондинга Pump.fun.
- [ ] `platforms/pumpfun/event_parser.py`: Парсер событий, специфичных для Pump.fun.
- [ ] `platforms/pumpfun/instruction_builder.py`: Строитель инструкций для взаимодействия с Pump.fun.
- [ ] `platforms/pumpfun/pumpportal_processor.py`: Обработчик для взаимодействия с Pump.portal (если отличается от универсального).

4
### 4. Trading Logic (Торговая логика)
- [ ] `trading/base.py`: Базовые классы для торговых стратегий.
- [ ] `trading/platform_aware.py`: Торговая логика, адаптированная под конкретные платформы.
- [ ] `trading/position.py`: Управление открытыми торговыми позициями.
- [ ] `trading/universal_trader.py`: Универсальный торговый модуль, способный работать с разными платформами.

3
### 5. Utilities and Helpers (Утилиты и помощники)
- [ ] `utils/logger.py`: Настройка и управление логированием.
- [ ] `utils/idl_manager.py`: Менеджер для работы с IDL файлами (загрузка, кэширование).
- [ ] `utils/idl_parser.py`: Парсер для разбора IDL схем.

1
### 6. Entry Points (Точки входа)
- [ ] `bot_runner.py`: Основной скрипт для запуска и оркестрации бота.

### 7. Interfaces (Интерфейсы)
- [ ] `interfaces/core.py`: Определение абстрактных классов и интерфейсов для соблюдения архитектуры.

### 8. Geyser Integration (Интеграция с Geyser)
- [ ] `geyser/generated/` и `geyser/proto/`: Понимание и (при необходимости) генерация protobuf-файлов для Geyser-протокола. (Обычно генерируются, не пишутся вручную).

graph TD
    A[Начало: Запуск бота] --> B{Инициализация: получение конфигурации например, из .env};
    B --> C[Инициализация UniversalTrader];
    C --> D[UniversalTrader: Создание Platform-Specific Trader например, PumpFunTrader];
    D --> E[UniversalTrader: Инициализация Listener например, UniversalBlockListener];
    E --> F{Listener: Подписка на данные например, BlockSubscribe};
    F --> G{Listener: Получение и декодирование событий например, Create Instruction};
    G --> H{UniversalTrader: Обработка декодированного события};
    H --> I{Platform-Specific Trader: Принятие решения о торговле};
    I --> J{Platform-Specific Trader: Построение и подписание транзакции};
    J --> K{Platform-Specific Trader: Отправка транзакции в Solana};
    K --> L[UniversalTrader: Мониторинг позиций и выходных стратегий];
    L --> M[Конец: Завершение работы бота];






    
Отлично! Я объясню как работают оба скрипта:

## 📋 AddressProvider.py - Основной модуль

**Назначение**: Рассчитывает все необходимые адреса для работы с pump.fun токенами

### 🔧 Основные функции:

1. **[get_bonding_curve_address(mint)](cci:1://file:///c:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/pumpfun/address_provider.py:32:4-50:91)** 
   - Рассчитывает PDA адрес bonding curve для токена
   - Использует seed `"bonding-curve"` + mint адрес
   - Возвращает `(адрес, bump)`

2. **[get_associated_bonding_curve_address(mint)](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/tests/test_address_provider.py:98:8-105:33)**
   - Рассчитывает associated token account для bonding curve
   - Нужен для хранения токенов в bonding curve
   - Возвращает `(адрес, bump)`

3. **[get_associated_token_address(wallet, mint)](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/tests/test_address_provider.py:119:8-121:92)**
   - Рассчитывает ATA (Associated Token Account) для пользователя
   - Где будут храниться купленные токены
   - Возвращает адрес

4. **[get_metadata_address(mint)](cci:1://file:///c:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/pumpfun/address_provider.py:103:4-125:86)**
   - Рассчитывает адрес метаданных токена (название, символ, изображение)
   - Использует Metaplex стандарт
   - Возвращает `(адрес, bump)`

5. **[get_all_addresses(mint, wallet)](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/pumpfun/address_provider.py:127:4-172:92)**
   - **Главная функция** - возвращает ВСЕ адреса сразу
   - Включает системные программы и pump.fun константы
   - Используется при создании транзакций

### 🎯 Пример работы:
```python
# Входные данные
mint = "So11111111111111111111111111111111111111112"  # WSOL
wallet = "11111111111111111111111111111112"  # System Program

# Получаем все адреса
addresses = AddressProvider.get_all_addresses(mint_pubkey, wallet_pubkey)
```

## 🧪 test_address_provider.py - Тестовый модуль

**Назначение**: Проверяет корректность работы AddressProvider без реальных трат

### 📝 Тестовые сценарии:

1. **[test_address_validation()](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/tests/test_address_provider.py:170:0-195:20)**
   - Проверяет валидацию mint и wallet адресов
   - Тестирует корректные типы возвращаемых объектов

2. **[test_bonding_curve_calculation()](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/tests/test_address_provider.py:198:0-231:20)**
   - Проверяет расчет bonding curve адреса
   - Валидирует bump значения (0-255)

3. **[test_associated_bonding_curve()](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/tests/test_address_provider.py:233:0-257:20)**
   - Тестирует расчет associated bonding curve
   - Проверяет корректность типов результата

4. **[test_associated_token_account()](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/tests/test_address_provider.py:261:0-288:20)**
   - Проверяет расчет ATA для пользователя
   - Валидирует результат как Pubkey

5. **[test_metadata_address()](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/tests/test_address_provider.py:290:0-313:20)**
   - Тестирует расчет metadata адреса
   - Проверяет bump значения

6. **[test_all_addresses()](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/tests/test_address_provider.py:317:0-359:20)**
   - **Главный тест** - проверяет [get_all_addresses()](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/pumpfun/address_provider.py:127:4-172:92)
   - Валидирует наличие всех обязательных полей
   - Проверяет корректность структуры результата

7. **[test_address_errors()](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/tests/test_address_provider.py:362:0-395:20)**
   - Тестирует обработку ошибок
   - Проверяет реакцию на невалидные адреса

8. **[test_address_consistency()](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/tests/test_address_provider.py:397:0-432:20)**
   - Проверяет консистентность между разными методами
   - Сравнивает результаты отдельных функций с [get_all_addresses()](cci:1://file:///C:/Users/User/PycharmProjects/colect_trader_tradHistori_and_analize_them/AA/pumpfun-bonkfun-bot-main/TBF_V0/pumpfun/address_provider.py:127:4-172:92)

### 🎭 Mock система:
- Если реальные модули недоступны, использует заглушки
- Позволяет тестировать без установки solders/solana
- Эмулирует поведение реальных функций

### 🚀 Как запустить:
```python
# Запуск всех тестов
python TBF_V0/tests/test_address_provider.py

# Или импорт функции
from TBF_V0.tests.test_address_provider import run_all_address_tests
run_all_address_tests()
```

## 🔄 Связь между модулями:

1. **AddressProvider** - производственный код для расчета адресов
2. **test_address_provider** - проверяет что AddressProvider работает корректно
3. Тесты гарантируют, что при торговле будут использованы правильные адреса
4. Без правильных адресов транзакции pump.fun будут отклонены

Это критически важно для торгового бота - неправильные адреса = потеря средств!