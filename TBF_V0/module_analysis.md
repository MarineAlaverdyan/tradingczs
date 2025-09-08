# 🔍 Анализ модулей при покупке токена в pump.fun боте

## 📋 Все задействованные модули

### 1. 🌐 **Сетевые модули**
```
core/simple_client.py
├── Подключение к Solana RPC
├── Получение баланса кошелька
├── Отправка транзакций
└── Получение последнего blockhash
```

### 2. 🔑 **Управление кошельком**
```
core/simple_wallet.py
├── Загрузка приватного ключа
├── Генерация публичного ключа
├── Подписание транзакций
└── Управление keypair
```

### 3. 💰 **Управление комиссиями**
```
core/priority_fee/manager.py
├── Расчет priority fee
├── Анализ загруженности сети
├── Оптимизация стоимости транзакций
└── Создание compute budget инструкций
```

### 4. 📍 **Адресация и PDA**
```
pumpfun/address_provider.py
├── Расчет bonding curve PDA
├── Расчет associated token account
├── Расчет creator vault PDA
├── Расчет volume accumulator PDA
└── Получение системных адресов
```

### 5. 🔧 **Построение инструкций**
```
pumpfun/instruction_builder.py
├── Создание buy инструкции
├── Формирование списка аккаунтов (16 шт)
├── Создание instruction data
├── Добавление discriminator
└── Упаковка параметров (sol_amount, max_sol_cost)
```

### 6. 🛒 **Торговая логика**
```
trading/simple_buyer.py
├── Координация всего процесса покупки
├── Создание ATA если не существует
├── Построение полной транзакции
├── Retry логика (3 попытки)
├── Обработка ошибок
└── Возврат результата покупки
```

### 7. 📊 **Информация о токене**
```
core/token_info.py
├── Парсинг данных токена из listener
├── Хранение mint адреса
├── Хранение bonding curve адресов
├── Метаданные токена (name, symbol, uri)
└── Валидация данных
```

### 8. 🏗️ **Константы и адреса**
```
core/pubkeys.py
├── PUMP_PROGRAM_ID
├── PUMP_GLOBAL_ACCOUNT
├── PUMP_FEE_RECIPIENT
├── PUMP_EVENT_AUTHORITY
├── TOKEN_PROGRAM_ID
├── SYSTEM_PROGRAM_ID
└── PUMP_FEE_CONFIG_ACCOUNT
```

## 🔄 Поток выполнения покупки

### Этап 1: Инициализация
1. **SimpleClient** - подключение к RPC
2. **SimpleWallet** - загрузка ключей
3. **PriorityFeeManager** - настройка комиссий
4. **AddressProvider** - подготовка адресов
5. **InstructionBuilder** - готовность к созданию инструкций

### Этап 2: Подготовка данных
1. **TokenInfo** - парсинг данных токена
2. **AddressProvider** - расчет всех PDA адресов
3. **SimpleClient** - проверка баланса кошелька

### Этап 3: Построение транзакции
1. **PriorityFeeManager** - создание compute budget инструкций
2. **SimpleBuyer** - проверка/создание ATA
3. **InstructionBuilder** - создание buy инструкции с 16 аккаунтами
4. **SimpleWallet** - подписание транзакции

### Этап 4: Отправка и обработка
1. **SimpleClient** - отправка транзакции в сеть
2. **SimpleBuyer** - retry логика при ошибках
3. **SimpleClient** - подтверждение транзакции
4. **SimpleBuyer** - возврат результата

## 🔗 Взаимодействие модулей

```
test_console_buy.py
    ↓
SimpleBuyer (координатор)
    ├── SimpleClient (RPC)
    ├── SimpleWallet (подпись)
    ├── AddressProvider (адреса)
    ├── InstructionBuilder (инструкции)
    ├── PriorityFeeManager (комиссии)
    └── TokenInfo (данные токена)
```

## 🎯 Ключевые компоненты

### Критически важные:
- **InstructionBuilder** - правильная структура buy инструкции
- **AddressProvider** - корректные PDA расчеты
- **SimpleClient** - стабильное RPC соединение

### Вспомогательные:
- **PriorityFeeManager** - оптимизация скорости
- **SimpleWallet** - безопасность ключей
- **TokenInfo** - валидация данных

## 🚨 Текущие проблемы

1. **AccountNotEnoughKeys** - нужно точно 16 аккаунтов
2. **fee_config** аккаунт требует правильного owner
3. Порядок аккаунтов должен соответствовать IDL

## 📈 Статус модулей

✅ **Работающие:**
- SimpleClient (RPC подключение)
- SimpleWallet (загрузка ключей)
- TokenInfo (парсинг данных)
- AddressProvider (PDA расчеты)

⚠️ **Проблемные:**
- InstructionBuilder (структура аккаунтов)
- SimpleBuyer (обработка ошибок транзакций)

❌ **Не работающие:**
- Полный цикл покупки (из-за ошибок инструкции)
