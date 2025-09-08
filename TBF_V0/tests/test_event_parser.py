"""
Тест для EventParser - проверка парсинга событий pump.fun без трат.
Тестирует парсинг с тестовыми данными.
"""

import sys
import os
import base64
import struct

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pumpfun.event_parser import EventParser, TokenInfo


def create_test_transaction_data():
    """Создать тестовые данные транзакции создания токена."""
    # Создаем тестовую транзакцию с правильной структурой
    return {
        "transaction": {
            "message": {
                "accountKeys": [
                    "So11111111111111111111111111111111111111112",  # mint
                    "11111111111111111111111111111112",            # mint_authority
                    "bonding_curve_test_address_123456789012",     # bonding_curve
                    "associated_bonding_curve_test_address123",    # associated_bonding_curve
                    "4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5db6hjPuMkCjDQF",  # global
                    "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s",   # mpl_token_metadata
                    "metadata_test_address_123456789012345",       # metadata
                    "creator_test_address_1234567890123456",       # user/creator
                    "11111111111111111111111111111112",            # system_program
                    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # token_program
                    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",  # associated_token_program
                    "SysvarRent111111111111111111111111111111111",   # rent
                    "Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1",  # event_authority
                    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"   # pump_program
                ],
                "instructions": [
                    {
                        "programIdIndex": 13,  # pump.fun программа
                        "accounts": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
                        "data": base64.b64encode(
                            EventParser.CREATE_DISCRIMINATOR + 
                            struct.pack("<I", 8) + b"TestCoin" +  # name
                            struct.pack("<I", 4) + b"TEST" +      # symbol
                            struct.pack("<I", 21) + b"https://test.com/meta"  # uri (исправлена длина)
                        ).decode()
                    }
                ]
            }
        }
    }


def create_invalid_transaction_data():
    """Создать невалидные тестовые данные."""
    return {
        "transaction": {
            "message": {
                "accountKeys": [
                    "So11111111111111111111111111111111111111112",
                    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
                ],
                "instructions": [
                    {
                        "programIdIndex": 1,  # НЕ pump.fun программа
                        "accounts": [0, 1],
                        "data": base64.b64encode(b"invalid_data").decode()
                    }
                ]
            }
        }
    }


def test_transaction_detection():
    """Тест определения транзакций создания токенов."""
    print("🔍 Тестируем определение транзакций создания...")
    
    try:
        # Тест с валидной транзакцией
        valid_tx = create_test_transaction_data()
        is_create_valid = EventParser.is_create_transaction(valid_tx)
        
        print(f"   Валидная транзакция определена как создание: {is_create_valid}")
        
        # Тест с невалидной транзакцией
        invalid_tx = create_invalid_transaction_data()
        is_create_invalid = EventParser.is_create_transaction(invalid_tx)
        
        print(f"   Невалидная транзакция определена как создание: {is_create_invalid}")
        
        if is_create_valid and not is_create_invalid:
            print("   ✅ Определение транзакций работает корректно")
            return True
        else:
            print("   ❌ Ошибка определения транзакций")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка теста определения: {e}")
        return False


def test_event_parsing():
    """Тест парсинга события создания токена."""
    print("\n📝 Тестируем парсинг события создания...")
    
    try:
        # Создаем тестовую транзакцию
        test_tx = create_test_transaction_data()
        
        # Парсим событие
        token_info = EventParser.parse_create_event(test_tx)
        
        if token_info:
            print(f"   ✅ Название: {token_info.name}")
            print(f"   ✅ Символ: {token_info.symbol}")
            print(f"   ✅ URI: {token_info.uri}")
            print(f"   ✅ Mint: {token_info.mint}")
            print(f"   ✅ Создатель: {token_info.creator}")
            print(f"   ✅ Платформа: {token_info.platform}")
            
            # Проверяем корректность данных
            expected_values = {
                "name": "TestCoin",
                "symbol": "TEST",
                "uri": "https://test.com/meta",
                "platform": "pump.fun"
            }
            
            for key, expected in expected_values.items():
                actual = getattr(token_info, key)
                if actual != expected:
                    print(f"   ❌ Неверное значение {key}: ожидалось '{expected}', получено '{actual}'")
                    return False
            
            print("   ✅ Все данные парсинга корректны")
            return True
        else:
            print("   ❌ Парсинг не вернул результат")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка парсинга: {e}")
        return False


def test_token_info_validation():
    """Тест валидации TokenInfo."""
    print("\n✅ Тестируем валидацию TokenInfo...")
    
    try:
        # Валидный TokenInfo
        valid_token = TokenInfo(
            mint="So11111111111111111111111111111111111111112",
            name="Test Token",
            symbol="TEST",
            uri="https://test.com",
            creator="11111111111111111111111111111112",
            bonding_curve="11111111111111111111111111111112",
            associated_bonding_curve="11111111111111111111111111111112"
        )
        
        is_valid = EventParser.validate_token_info(valid_token)
        print(f"   Валидный токен прошел валидацию: {is_valid}")
        
        # Невалидный TokenInfo (пустое название)
        invalid_token = TokenInfo(
            mint="So11111111111111111111111111111111111111112",
            name="",  # Пустое название
            symbol="TEST",
            uri="https://test.com",
            creator="11111111111111111111111111111112",
            bonding_curve="11111111111111111111111111111112",
            associated_bonding_curve="11111111111111111111111111111112"
        )
        
        is_invalid = EventParser.validate_token_info(invalid_token)
        print(f"   Невалидный токен прошел валидацию: {is_invalid}")
        
        if is_valid and not is_invalid:
            print("   ✅ Валидация TokenInfo работает корректно")
            return True
        else:
            print("   ❌ Ошибка валидации TokenInfo")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка теста валидации: {e}")
        return False


def test_invalid_addresses_validation():
    """Тест валидации с неверными адресами."""
    print("\n🚫 Тестируем валидацию с неверными адресами...")
    
    try:
        # TokenInfo с неверными адресами
        invalid_addresses_token = TokenInfo(
            mint="invalid_mint_address",
            name="Test Token",
            symbol="TEST",
            uri="https://test.com",
            creator="invalid_creator",
            bonding_curve="invalid_bonding_curve",
            associated_bonding_curve="invalid_abc"
        )
        
        is_valid = EventParser.validate_token_info(invalid_addresses_token)
        print(f"   Токен с неверными адресами прошел валидацию: {is_valid}")
        
        if not is_valid:
            print("   ✅ Неверные адреса правильно отклонены")
            return True
        else:
            print("   ❌ Неверные адреса не были отклонены")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка теста неверных адресов: {e}")
        return False


def test_long_strings_validation():
    """Тест валидации с длинными строками."""
    print("\n📏 Тестируем валидацию с длинными строками...")
    
    try:
        # TokenInfo с очень длинным названием
        long_name_token = TokenInfo(
            mint="So11111111111111111111111111111111111111112",
            name="A" * 150,  # Слишком длинное название
            symbol="TEST",
            uri="https://test.com",
            creator="11111111111111111111111111111112",
            bonding_curve="11111111111111111111111111111112",
            associated_bonding_curve="11111111111111111111111111111112"
        )
        
        is_valid_long_name = EventParser.validate_token_info(long_name_token)
        print(f"   Токен с длинным названием прошел валидацию: {is_valid_long_name}")
        
        # TokenInfo с длинным символом
        long_symbol_token = TokenInfo(
            mint="So11111111111111111111111111111111111111112",
            name="Test Token",
            symbol="VERYLONGSYMBOL123456789",  # Слишком длинный символ
            uri="https://test.com",
            creator="11111111111111111111111111111112",
            bonding_curve="11111111111111111111111111111112",
            associated_bonding_curve="11111111111111111111111111111112"
        )
        
        is_valid_long_symbol = EventParser.validate_token_info(long_symbol_token)
        print(f"   Токен с длинным символом прошел валидацию: {is_valid_long_symbol}")
        
        if not is_valid_long_name and not is_valid_long_symbol:
            print("   ✅ Длинные строки правильно отклонены")
            return True
        else:
            print("   ❌ Длинные строки не были отклонены")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка теста длинных строк: {e}")
        return False


def test_parsing_errors():
    """Тест обработки ошибок парсинга."""
    print("\n⚠️ Тестируем обработку ошибок парсинга...")
    
    try:
        # Пустые данные
        empty_data = {}
        result_empty = EventParser.parse_create_event(empty_data)
        print(f"   Результат парсинга пустых данных: {result_empty}")
        
        # Неполные данные
        incomplete_data = {"transaction": {"message": {}}}
        result_incomplete = EventParser.parse_create_event(incomplete_data)
        print(f"   Результат парсинга неполных данных: {result_incomplete}")
        
        # Данные без инструкций
        no_instructions = {
            "transaction": {
                "message": {
                    "accountKeys": [],
                    "instructions": []
                }
            }
        }
        result_no_instructions = EventParser.parse_create_event(no_instructions)
        print(f"   Результат парсинга без инструкций: {result_no_instructions}")
        
        # Все результаты должны быть None
        if result_empty is None and result_incomplete is None and result_no_instructions is None:
            print("   ✅ Ошибки парсинга обработаны корректно")
            return True
        else:
            print("   ❌ Ошибки парсинга обработаны некорректно")
            return False
            
    except Exception as e:
        print(f"   ❌ Неожиданная ошибка: {e}")
        return False


def test_metadata_extraction():
    """Тест извлечения метаданных."""
    print("\n📊 Тестируем извлечение метаданных...")
    
    try:
        # Тест с валидным URI
        test_uri = "https://test.com/metadata.json"
        metadata = EventParser.extract_token_metadata(test_uri)
        
        print(f"   URI: {test_uri}")
        print(f"   ✅ Метаданные получены: {type(metadata)}")
        
        # Проверяем, что возвращается словарь
        if isinstance(metadata, dict):
            print("   ✅ Метаданные в правильном формате")
            return True
        else:
            print("   ❌ Неверный формат метаданных")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка извлечения метаданных: {e}")
        return False


def run_all_parser_tests():
    """Запустить все тесты EventParser."""
    print("🧪 ТЕСТИРОВАНИЕ EventParser")
    print("=" * 50)
    
    tests = [
        ("Определение транзакций", test_transaction_detection),
        ("Парсинг события", test_event_parsing),
        ("Валидация TokenInfo", test_token_info_validation),
        ("Валидация неверных адресов", test_invalid_addresses_validation),
        ("Валидация длинных строк", test_long_strings_validation),
        ("Обработка ошибок", test_parsing_errors),
        ("Извлечение метаданных", test_metadata_extraction),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Тест: {test_name}")
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"   🎉 ПРОЙДЕН")
            else:
                print(f"   💥 НЕ ПРОЙДЕН")
        except Exception as e:
            print(f"   💥 ОШИБКА: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ!")
    else:
        print(f"⚠️ {total - passed} тестов не прошли")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_parser_tests()
    exit(0 if success else 1)
