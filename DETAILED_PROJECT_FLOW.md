# 🔄 ПОДРОБНАЯ СХЕМА РАБОТЫ ТОРГОВОГО БОТА

## 📋 ОБЩИЙ ОБЗОР

Торговый бот - это многокомпонентная система для автоматической торговли токенами на платформах pump.fun и letsbonk.fun. Система работает в режиме реального времени, отслеживая новые токены и выполняя торговые операции.

---

## 🚀 ГЛАВНЫЙ ПОТОК ВЫПОЛНЕНИЯ

### 1. ЗАПУСК СИСТЕМЫ (`bot_runner.py`)

```
main() → run_all_bots() → start_bot() → UniversalTrader.start()
```

**Последовательность:**
1. **Загрузка конфигурации** - читает YAML файлы из папки `bots/`
2. **Валидация платформы** - проверяет поддержку pump.fun/letsbonk.fun
3. **Валидация listener'а** - проверяет совместимость (geyser/logs/blocks/pumpportal)
4. **Создание UniversalTrader** - инициализация главного координатора
5. **Запуск торговли** - `trader.start()`

---

## 🎯 УНИВЕРСАЛЬНЫЙ ТОРГОВЕЦ (`UniversalTrader`)

### Инициализация компонентов:

```python
def __init__(self):
    # 1. Базовые компоненты
    self.client = SolanaClient(rpc_endpoint)           # Подключение к Solana
    self.wallet = Wallet(private_key)                  # Управление кошельком
    self.priority_fee_manager = PriorityFeeManager()   # Управление комиссиями
    
    # 2. Платформо-специфичные компоненты
    self.platform_impl = get_platform_implementations(platform)  # pump.fun/letsbonk
    self.buyer = PlatformAwareBuyer()                  # Покупатель
    self.seller = PlatformAwareSeller()                # Продавец
    
    # 3. Мониторинг
    self.listener = ListenerFactory.create()          # Слушатель блоков/логов
```

### Главный цикл торговли:

```python
async def start(self):
    # 1. Запуск мониторинга новых токенов
    await self.listener.start_listening(callback=self.handle_new_token)
    
    # 2. Обработка каждого нового токена
    async def handle_new_token(token_info: TokenInfo):
        await self.execute_trade_cycle(token_info)
```

---

## 🔍 МОНИТОРИНГ НОВЫХ ТОКЕНОВ

### Типы Listener'ов:

#### 1. **Geyser Listener** (самый быстрый)
```
Geyser API → WebSocket → parse_transaction() → TokenInfo → callback
```

#### 2. **Logs Listener** 
```
Solana WebSocket → blockSubscribe → filter_logs() → parse_create_event() → TokenInfo
```

#### 3. **Blocks Listener**
```
Solana WebSocket → blockSubscribe → parse_instructions() → TokenInfo
```

#### 4. **PumpPortal Listener**
```
PumpPortal WebSocket → JSON events → TokenInfo
```

### Процесс обнаружения токена:

```python
# 1. Получение данных
raw_data = await listener.receive_data()

# 2. Фильтрация (только pump.fun транзакции)
if platform_impl.is_create_transaction(raw_data):
    
    # 3. Парсинг данных токена
    token_info = platform_impl.parse_create_event(raw_data)
    
    # 4. Валидация токена
    if self.validate_token(token_info):
        
        # 5. Вызов callback
        await self.handle_new_token(token_info)
```

---

## 💰 ТОРГОВЫЙ ЦИКЛ

### Полный цикл торговли:

```python
async def execute_trade_cycle(self, token_info: TokenInfo):
    # 1. ПОДГОТОВКА
    position = Position(token_info)
    
    # 2. ПОКУПКА
    buy_result = await self.execute_buy(token_info)
    if not buy_result.success:
        await self.handle_buy_failure(token_info)
        return
    
    # 3. МОНИТОРИНГ ПОЗИЦИИ
    await self.monitor_position(position, buy_result)
    
    # 4. ПРОДАЖА (по условиям TP/SL/времени)
    sell_result = await self.execute_sell(position)
    
    # 5. CLEANUP
    await self.cleanup_after_trade(position, sell_result)
```

### Детальный процесс покупки:

```python
async def execute_buy(self, token_info: TokenInfo):
    # 1. Получение адресов через платформу
    addresses = platform_impl.get_addresses(token_info.mint)
    
    # 2. Расчет priority fee
    priority_fee = await priority_fee_manager.calculate_fee()
    
    # 3. Создание инструкции покупки
    instruction = platform_impl.build_buy_instruction(
        wallet=self.wallet,
        token_info=token_info,
        sol_amount=self.buy_amount,
        slippage=self.buy_slippage
    )
    
    # 4. Создание и подпись транзакции
    transaction = await self.client.create_transaction([instruction])
    transaction.add_priority_fee(priority_fee)
    signed_tx = self.wallet.sign_transaction(transaction)
    
    # 5. Отправка с retry логикой
    for attempt in range(self.max_retries):
        try:
            signature = await self.client.send_transaction(signed_tx)
            result = await self.client.confirm_transaction(signature)
            
            if result.success:
                return TradeResult(success=True, signature=signature)
                
        except Exception as e:
            if attempt == self.max_retries - 1:
                return TradeResult(success=False, error=str(e))
            await asyncio.sleep(self.retry_delay)
```

---

## 📊 МОНИТОРИНГ ПОЗИЦИИ

### Стратегии выхода:

#### 1. **Time-based** (по времени)
```python
async def monitor_time_based(self, position: Position):
    await asyncio.sleep(self.max_hold_time)
    return SellSignal(reason="time_limit")
```

#### 2. **TP/SL** (Take Profit / Stop Loss)
```python
async def monitor_tp_sl(self, position: Position):
    while True:
        current_price = await platform_impl.get_current_price(position.token_info)
        
        profit_pct = (current_price - position.buy_price) / position.buy_price * 100
        
        if profit_pct >= self.take_profit_percentage:
            return SellSignal(reason="take_profit", price=current_price)
            
        if profit_pct <= -self.stop_loss_percentage:
            return SellSignal(reason="stop_loss", price=current_price)
            
        await asyncio.sleep(self.price_check_interval)
```

#### 3. **Extreme Fast Mode**
```python
async def monitor_extreme_fast(self, position: Position):
    # Продажа сразу после покупки определенного количества токенов
    await asyncio.sleep(self.wait_time_after_buy)
    return SellSignal(reason="extreme_fast")
```

---

## 🏗️ ПЛАТФОРМО-СПЕЦИФИЧНАЯ ЛОГИКА

### PumpFun Implementation:

```python
class PumpFunImpl:
    def get_addresses(self, mint: Pubkey):
        return {
            'bonding_curve': self.get_bonding_curve_pda(mint),
            'associated_bonding_curve': self.get_abc_pda(mint),
            'metadata': self.get_metadata_pda(mint),
            'user_ata': self.get_user_ata(wallet, mint)
        }
    
    def build_buy_instruction(self, wallet, token_info, sol_amount, slippage):
        # Создание Solana инструкции для pump.fun программы
        return Instruction(
            program_id=PUMP_PROGRAM_ID,
            accounts=[...],  # Все необходимые аккаунты
            data=encode_buy_data(sol_amount, slippage)
        )
    
    def parse_create_event(self, transaction_data):
        # Парсинг логов транзакции создания токена
        return TokenInfo(
            mint=extract_mint(transaction_data),
            name=extract_name(transaction_data),
            symbol=extract_symbol(transaction_data),
            uri=extract_uri(transaction_data)
        )
```

---

## 🧹 CLEANUP СИСТЕМА

### Режимы cleanup:

#### 1. **После успешной продажи**
```python
async def handle_cleanup_after_sell(self, position: Position):
    # 1. Закрытие token account
    if position.token_account_balance == 0:
        await self.close_token_account(position.user_ata)
    
    # 2. Возврат SOL на основной кошелек
    sol_balance = await self.get_sol_balance(position.user_ata)
    if sol_balance > 0:
        await self.transfer_sol_to_main(sol_balance)
```

#### 2. **После неудачной покупки**
```python
async def handle_cleanup_after_failure(self, token_info: TokenInfo):
    # Cleanup созданных, но неиспользованных аккаунтов
    await self.cleanup_failed_accounts(token_info.mint)
```

#### 3. **Принудительное закрытие**
```python
async def force_cleanup_with_burn(self, position: Position):
    # Сжигание оставшихся токенов для закрытия аккаунта
    if position.token_balance > 0:
        await self.burn_remaining_tokens(position)
    await self.close_token_account(position.user_ata)
```

---

## ⚡ PRIORITY FEE УПРАВЛЕНИЕ

### Динамические комиссии:
```python
class PriorityFeeManager:
    async def calculate_dynamic_fee(self):
        # 1. Получение статистики сети
        recent_fees = await self.client.get_recent_priority_fees()
        
        # 2. Расчет рекомендуемой комиссии
        recommended = self.calculate_percentile(recent_fees, 75)
        
        # 3. Применение множителей
        final_fee = recommended * (1 + self.extra_percentage)
        
        # 4. Ограничение максимумом
        return min(final_fee, self.hard_cap)
    
    async def calculate_fixed_fee(self):
        return self.fixed_amount
```

---

## 🔄 RETRY И ERROR HANDLING

### Retry логика:
```python
async def execute_with_retry(self, operation, max_retries=10):
    for attempt in range(max_retries):
        try:
            return await operation()
        except TransactionFailedException as e:
            if "insufficient funds" in str(e):
                raise  # Не retry при недостатке средств
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(self.calculate_backoff(attempt))
        except NetworkException as e:
            # Retry сетевых ошибок
            await asyncio.sleep(self.network_retry_delay)
```

---

## 📈 ПОТОК ДАННЫХ

### Схема потока данных:
```
Blockchain → Listener → TokenInfo → UniversalTrader → PlatformImpl → 
→ Buyer → Transaction → SolanaClient → Blockchain
```

### Детальный поток:
1. **Blockchain Events** - новые транзакции создания токенов
2. **Listener** - получает и фильтрует события
3. **TokenInfo** - структурированная информация о токене
4. **UniversalTrader** - принимает решение о торговле
5. **PlatformImpl** - создает платформо-специфичные инструкции
6. **Buyer/Seller** - выполняет торговые операции
7. **SolanaClient** - отправляет транзакции в блокчейн

---

## 🎛️ КОНФИГУРАЦИЯ

### Основные параметры:
```yaml
# Торговые параметры
trade:
  buy_amount: 0.01          # Сумма покупки в SOL
  buy_slippage: 0.25        # Slippage для покупки (25%)
  sell_slippage: 0.25       # Slippage для продажи
  exit_strategy: "tp_sl"    # Стратегия выхода
  take_profit_percentage: 50 # Take profit (50%)
  stop_loss_percentage: 30  # Stop loss (30%)

# Мониторинг
filters:
  listener_type: "geyser"   # Тип слушателя
  max_token_age: 0.001      # Максимальный возраст токена (сек)

# Priority fees
priority_fees:
  enable_dynamic: true      # Динамические комиссии
  fixed_amount: 500000      # Фиксированная комиссия (lamports)
  hard_cap: 1000000        # Максимальная комиссия

# Cleanup
cleanup:
  mode: "after_sell"       # Режим cleanup
  force_close_with_burn: false
```

---

## 🔧 КЛЮЧЕВЫЕ ФУНКЦИИ ПО МОДУЛЯМ

### **SolanaClient** (`core/client.py`)
- `connect()` - подключение к RPC
- `send_transaction()` - отправка транзакции
- `confirm_transaction()` - подтверждение транзакции
- `get_balance()` - получение баланса

### **Wallet** (`core/wallet.py`)
- `load_from_private_key()` - загрузка кошелька
- `sign_transaction()` - подпись транзакции
- `get_public_key()` - получение публичного ключа

### **PlatformImpl** (`platforms/pumpfun/`)
- `get_addresses()` - расчет всех адресов
- `build_buy_instruction()` - создание инструкции покупки
- `build_sell_instruction()` - создание инструкции продажи
- `parse_create_event()` - парсинг события создания токена

### **Listener** (`monitoring/`)
- `start_listening()` - запуск мониторинга
- `handle_message()` - обработка входящих сообщений
- `filter_transactions()` - фильтрация транзакций

### **Buyer/Seller** (`trading/`)
- `execute_buy()` - выполнение покупки
- `execute_sell()` - выполнение продажи
- `calculate_slippage()` - расчет slippage

---

## ⏱️ ВРЕМЕННЫЕ ИНТЕРВАЛЫ

### Критические тайминги:
- **Token detection**: ~100-500ms (зависит от listener'а)
- **Buy execution**: ~1-3 секунды
- **Price monitoring**: каждые 10 секунд (настраивается)
- **Sell execution**: ~1-3 секунды
- **Cleanup**: ~5-10 секунд

### Retry интервалы:
- **Network retry**: 1-2 секунды
- **Transaction retry**: экспоненциальная задержка (1s, 2s, 4s...)
- **Price check**: 10 секунд (по умолчанию)

---

Эта схема показывает полный жизненный цикл торгового бота от обнаружения нового токена до завершения торговли и cleanup'а.
