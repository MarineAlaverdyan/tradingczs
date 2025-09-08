"""
Отладочный скрипт для проверки fee_config аккаунта
"""

try:
    from core.pubkeys import PUMP_FEE_CONFIG_ACCOUNT, PUMP_FEE_CONFIG_PROGRAM
    from pumpfun.instruction_builder import InstructionBuilder, PumpFunConstants
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    exit(1)

def main():
    print("🔍 ОТЛАДКА FEE_CONFIG АККАУНТА")
    print("=" * 50)
    
    # Проверяем константы
    print(f"PUMP_FEE_CONFIG_PROGRAM: {PUMP_FEE_CONFIG_PROGRAM}")
    print(f"PUMP_FEE_CONFIG_ACCOUNT: {PUMP_FEE_CONFIG_ACCOUNT}")
    
    # Проверяем InstructionBuilder
    builder = InstructionBuilder()
    
    fee_config = builder._get_fee_config()
    print(f"InstructionBuilder._get_fee_config(): {fee_config}")
    
    # Проверяем, что это тот же адрес
    print(f"Адреса совпадают: {fee_config == PUMP_FEE_CONFIG_ACCOUNT}")
    
    # Проверяем строковое представление
    print(f"fee_config как строка: {str(fee_config)}")
    print(f"PUMP_FEE_CONFIG_ACCOUNT как строка: {str(PUMP_FEE_CONFIG_ACCOUNT)}")
    
    # Проверяем, что это именно программа fee config
    expected = "pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ"
    print(f"Ожидаемый адрес: {expected}")
    print(f"Получили правильный адрес: {str(fee_config) == expected}")

if __name__ == "__main__":
    main()
