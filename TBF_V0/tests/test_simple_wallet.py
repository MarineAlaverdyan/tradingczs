"""
Тест для SimpleWallet - проверка работы с кошельком без трат.
Тестирует генерацию, загрузку и подпись.
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.simple_wallet import SimpleWallet


def test_wallet_generation():
    """Тест генерации нового кошелька."""
    print("🔑 Тестируем генерацию нового кошелька...")
    
    try:
        wallet = SimpleWallet()
        
        # Генерируем новый кошелек
        private_key = wallet.generate_new()
        
        print(f"   ✅ Приватный ключ сгенерирован: {private_key[:20]}...")
        print(f"   ✅ Кошелек загружен: {wallet.is_loaded()}")
        
        # Получаем адрес
        address = wallet.get_address_string()
        print(f"   ✅ Адрес кошелька: {address}")
        
        # Проверяем длину ключа (должен быть base58)
        if len(private_key) > 40:
            print("   ✅ Длина приватного ключа корректна")
            return True
        else:
            print("   ❌ Неверная длина приватного ключа")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка генерации: {e}")
        return False


def test_wallet_loading():
    """Тест загрузки кошелька из приватного ключа."""
    print("\n🔄 Тестируем загрузку кошелька из ключа...")
    
    try:
        # Создаем первый кошелек
        wallet1 = SimpleWallet()
        private_key = wallet1.generate_new()
        address1 = wallet1.get_address_string()
        
        # Создаем второй кошелек из того же ключа
        wallet2 = SimpleWallet()
        wallet2.load_from_private_key(private_key)
        address2 = wallet2.get_address_string()
        
        print(f"   Адрес 1: {address1}")
        print(f"   Адрес 2: {address2}")
        
        if address1 == address2:
            print("   ✅ Адреса совпадают - загрузка успешна")
            return True
        else:
            print("   ❌ Адреса не совпадают")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка загрузки: {e}")
        return False


def test_wallet_signing():
    """Тест подписи сообщений."""
    print("\n✍️ Тестируем подпись сообщений...")
    
    try:
        wallet = SimpleWallet()
        wallet.generate_new()
        
        # Тестовое сообщение
        test_message = b"Hello, Solana!"
        
        # Подписываем
        signature = wallet.sign_message(test_message)
        
        print(f"   Сообщение: {test_message}")
        print(f"   ✅ Подпись создана: {bytes(signature).hex()[:40]}...")
        
        # Проверяем длину подписи (должна быть 64 байта)
        if len(bytes(signature)) == 64:
            print("   ✅ Длина подписи корректна (64 байта)")
            return True
        else:
            print(f"   ❌ Неверная длина подписи: {len(bytes(signature))}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка подписи: {e}")
        return False


def test_wallet_errors():
    """Тест обработки ошибок."""
    print("\n❌ Тестируем обработку ошибок...")
    
    try:
        # Пустой кошелек
        empty_wallet = SimpleWallet()
        
        # Попытка получить ключ без загрузки
        try:
            empty_wallet.get_public_key()
            print("   ❌ Ошибка не была поймана")
            return False
        except Exception:
            print("   ✅ Правильно обработана ошибка пустого кошелька")
        
        # Попытка загрузить неверный ключ
        try:
            empty_wallet.load_from_private_key("invalid_key_123")
            print("   ❌ Неверный ключ не был отклонен")
            return False
        except Exception:
            print("   ✅ Правильно обработан неверный ключ")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Неожиданная ошибка: {e}")
        return False


def test_wallet_keypair_access():
    """Тест доступа к keypair объекту."""
    print("\n🔐 Тестируем доступ к keypair...")
    
    try:
        wallet = SimpleWallet()
        wallet.generate_new()
        
        # Получаем keypair
        keypair = wallet.get_keypair()
        
        # Проверяем, что это правильный объект
        if hasattr(keypair, 'pubkey') and hasattr(keypair, 'sign_message'):
            print("   ✅ Keypair объект корректен")
            
            # Проверяем совпадение публичных ключей
            pubkey1 = wallet.get_public_key()
            pubkey2 = keypair.pubkey()
            
            if str(pubkey1) == str(pubkey2):
                print("   ✅ Публичные ключи совпадают")
                return True
            else:
                print("   ❌ Публичные ключи не совпадают")
                return False
        else:
            print("   ❌ Keypair объект некорректен")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка доступа к keypair: {e}")
        return False


def run_all_wallet_tests():
    """Запустить все тесты кошелька."""
    print("🧪 ТЕСТИРОВАНИЕ SimpleWallet")
    print("=" * 50)
    
    tests = [
        ("Генерация кошелька", test_wallet_generation),
        ("Загрузка кошелька", test_wallet_loading),
        ("Подпись сообщений", test_wallet_signing),
        ("Обработка ошибок", test_wallet_errors),
        ("Доступ к keypair", test_wallet_keypair_access),
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
    success = run_all_wallet_tests()
    exit(0 if success else 1)
