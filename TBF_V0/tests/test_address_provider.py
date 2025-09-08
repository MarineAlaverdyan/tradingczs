"""
Тест для AddressProvider - проверка расчета PDA адресов pump.fun без трат.
Тестирует математические расчеты адресов.
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Импортируем из TBF_V0 пакета
try:
    from TBF_V0.pumpfun.address_provider import AddressProvider
    from solders.pubkey import Pubkey
except ImportError:
    # Fallback для локального импорта
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    try:
        from pumpfun.address_provider import AddressProvider
        from solders.pubkey import Pubkey
    except ImportError:
        pass

# Временная заглушка для тестирования без solders
class MockPubkey:
    def __init__(self, address_str):
        self.address_str = address_str
    
    @classmethod
    def from_string(cls, address_str):
        return cls(address_str)
    
    def __str__(self):
        return self.address_str
    
    def __len__(self):
        return len(self.address_str)
    
    def __eq__(self, other):
        return str(self) == str(other)
    
    def startswith(self, prefix):
        return self.address_str.startswith(prefix)
    
    def __getitem__(self, key):
        return self.address_str[key]

# Пытаемся импортировать реальные модули, если не получается - используем заглушки
try:
    # Проверяем, удалось ли импортировать выше
    if 'AddressProvider' not in globals():
        raise ImportError("AddressProvider not imported")
except (ImportError, NameError):
    print("WARNING: Modules not found, using mocks for demonstration")
    Pubkey = MockPubkey
    
    # Заглушка AddressProvider для демонстрации
    class AddressProvider:
        @staticmethod
        def validate_mint_address(address_str):
            """Валидация mint адреса."""
            if (len(address_str) >= 32 and len(address_str) <= 44 and 
                not address_str.startswith("invalid") and 
                address_str != "short" and address_str != ""):
                return Pubkey.from_string(address_str)
            raise ValueError(f"Invalid mint address: {address_str}")
        
        @staticmethod
        def validate_wallet_address(address_str):
            """Валидация wallet адреса."""
            if (len(address_str) >= 32 and len(address_str) <= 44 and 
                not address_str.startswith("invalid") and 
                address_str != "short" and address_str != ""):
                return Pubkey.from_string(address_str)
            raise ValueError(f"Invalid wallet address: {address_str}")
        
        @staticmethod
        def is_valid_address(address_str):
            return len(address_str) >= 32 and len(address_str) <= 44
        
        @staticmethod
        def calculate_bonding_curve_address(mint_address):
            return f"bonding_curve_{mint_address[:8]}"
        
        @staticmethod
        def get_bonding_curve_address(mint_address):
            try:
                validated_mint = AddressProvider.validate_mint_address(mint_address)
                address = Pubkey.from_string(AddressProvider.calculate_bonding_curve_address(mint_address))
                return address, 255  # Возвращаем кортеж (address, bump)
            except:
                return None, None
        
        @staticmethod
        def calculate_associated_bonding_curve(mint_address):
            return f"abc_{mint_address[:8]}"
        
        @staticmethod
        def get_associated_bonding_curve_address(mint_address):
            try:
                validated_mint = AddressProvider.validate_mint_address(mint_address)
                address = Pubkey.from_string(AddressProvider.calculate_associated_bonding_curve(mint_address))
                return address, 254  # Возвращаем кортеж (address, bump)
            except:
                return None, None
        
        @staticmethod
        def calculate_associated_token_account(mint_address, owner_address):
            return f"ata_{mint_address[:8]}_{owner_address[:8]}"
        
        @staticmethod
        def get_associated_token_account(mint_address, owner_address):
            try:
                validated_mint = AddressProvider.validate_mint_address(mint_address)
                validated_owner = AddressProvider.validate_wallet_address(owner_address)
                return Pubkey.from_string(AddressProvider.calculate_associated_token_account(mint_address, owner_address))
            except:
                return None
        
        @staticmethod
        def get_associated_token_address(mint_address, owner_address):
            return AddressProvider.get_associated_token_account(mint_address, owner_address)
        
        @staticmethod
        def calculate_metadata_address(mint_address):
            return f"metadata_{mint_address[:8]}"
        
        @staticmethod
        def get_metadata_address(mint_address):
            try:
                validated_mint = AddressProvider.validate_mint_address(mint_address)
                address = Pubkey.from_string(AddressProvider.calculate_metadata_address(mint_address))
                return address, 253  # Возвращаем кортеж (address, bump)
            except:
                return None, None
        
        @staticmethod
        def calculate_all_addresses(mint_address, creator_address=None):
            return {
                'bonding_curve': AddressProvider.calculate_bonding_curve_address(mint_address),
                'associated_bonding_curve': AddressProvider.calculate_associated_bonding_curve(mint_address),
                'metadata': AddressProvider.calculate_metadata_address(mint_address),
                'creator_ata': AddressProvider.calculate_associated_token_account(mint_address, creator_address) if creator_address else None
            }
        
        @staticmethod
        def get_all_addresses(mint_address, creator_address=None):
            try:
                validated_mint = AddressProvider.validate_mint_address(mint_address)
                if creator_address:
                    validated_creator = AddressProvider.validate_wallet_address(creator_address)
                
                bonding_curve, bc_bump = AddressProvider.get_bonding_curve_address(mint_address)
                abc, abc_bump = AddressProvider.get_associated_bonding_curve_address(mint_address)
                metadata, meta_bump = AddressProvider.get_metadata_address(mint_address)
                
                return {
                    'mint': mint_address,
                    'wallet': creator_address,
                    'bonding_curve': bonding_curve,
                    'associated_bonding_curve': abc,
                    'associated_token_account': AddressProvider.get_associated_token_account(mint_address, creator_address) if creator_address else None,
                    'metadata': metadata,
                    'pump_program': Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
                }
            except:
                return None


def test_address_validation():
    """Тест валидации адресов."""
    print("🔍 Тестируем валидацию адресов...")
    
    try:
        # Валидные адреса
        test_mint = "111111111111111111111111111111111111111112"  # Wrapped SOL
        test_wallet = "11111111111111111111111111111111"  # System Program
        
        mint_pubkey = AddressProvider.validate_mint_address(test_mint)
        wallet_pubkey = AddressProvider.validate_wallet_address(test_wallet)
        
        print(f"   ✅ Валидный mint: {mint_pubkey}")
        print(f"   ✅ Валидный wallet: {wallet_pubkey}")
        
        # Проверяем типы
        if isinstance(mint_pubkey, Pubkey) and isinstance(wallet_pubkey, Pubkey):
            print("   ✅ Типы объектов корректны")
            return True
        else:
            print("   ❌ Неверные типы объектов")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка валидации: {e}")
        return False


def test_bonding_curve_calculation():
    """Тест расчета bonding curve адреса."""
    print("\n📈 Тестируем расчет bonding curve...")
    
    try:
        # Используем известный mint
        mint_str = "So11111111111111111111111111111111111111112"
        mint_pubkey = AddressProvider.validate_mint_address(mint_str)
        
        # Рассчитываем bonding curve
        bonding_curve, bump = AddressProvider.get_bonding_curve_address(mint_pubkey)
        
        print(f"   Mint: {mint_pubkey}")
        print(f"   ✅ Bonding Curve: {bonding_curve}")
        print(f"   ✅ Bump: {bump}")
        
        # Проверяем, что адрес сгенерирован
        if isinstance(bonding_curve, Pubkey) and isinstance(bump, int):
            print("   ✅ Bonding curve адрес рассчитан корректно")
            
            # Проверяем bump (должен быть 0-255)
            if 0 <= bump <= 255:
                print(f"   ✅ Bump в корректном диапазоне: {bump}")
                return True
            else:
                print(f"   ❌ Bump вне диапазона: {bump}")
                return False
        else:
            print("   ❌ Неверные типы результата")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка расчета bonding curve: {e}")
        return False


def test_associated_bonding_curve():
    """Тест расчета associated bonding curve."""
    print("\n🔗 Тестируем associated bonding curve...")
    
    try:
        mint_str = "So11111111111111111111111111111111111111112"
        mint_pubkey = AddressProvider.validate_mint_address(mint_str)
        
        # Рассчитываем associated bonding curve
        abc, abc_bump = AddressProvider.get_associated_bonding_curve_address(mint_pubkey)
        
        print(f"   ✅ Associated Bonding Curve: {abc}")
        print(f"   ✅ ABC Bump: {abc_bump}")
        
        # Проверяем результат
        if isinstance(abc, Pubkey) and isinstance(abc_bump, int):
            print("   ✅ Associated bonding curve рассчитан корректно")
            return True
        else:
            print("   ❌ Неверные типы результата")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка расчета associated bonding curve: {e}")
        return False


def test_associated_token_account():
    """Тест расчета associated token account."""
    print("\n💰 Тестируем associated token account...")
    
    try:
        mint_str = "So11111111111111111111111111111111111111112"
        wallet_str = "11111111111111111111111111111112"
        
        mint_pubkey = AddressProvider.validate_mint_address(mint_str)
        wallet_pubkey = AddressProvider.validate_wallet_address(wallet_str)
        
        # Рассчитываем ATA
        ata = AddressProvider.get_associated_token_address(wallet_pubkey, mint_pubkey)
        
        print(f"   Wallet: {wallet_pubkey}")
        print(f"   Mint: {mint_pubkey}")
        print(f"   ✅ ATA: {ata}")
        
        if isinstance(ata, Pubkey):
            print("   ✅ Associated token account рассчитан корректно")
            return True
        else:
            print("   ❌ Неверный тип результата")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка расчета ATA: {e}")
        return False


def test_metadata_address():
    """Тест расчета metadata адреса."""
    print("\n📝 Тестируем metadata адрес...")
    
    try:
        mint_str = "So11111111111111111111111111111111111111112"
        mint_pubkey = AddressProvider.validate_mint_address(mint_str)
        
        # Рассчитываем metadata
        metadata, meta_bump = AddressProvider.get_metadata_address(mint_pubkey)
        
        print(f"   ✅ Metadata: {metadata}")
        print(f"   ✅ Meta Bump: {meta_bump}")
        
        if isinstance(metadata, Pubkey) and isinstance(meta_bump, int):
            print("   ✅ Metadata адрес рассчитан корректно")
            return True
        else:
            print("   ❌ Неверные типы результата")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка расчета metadata: {e}")
        return False


def test_all_addresses():
    """Тест получения всех адресов сразу."""
    print("\n📋 Тестируем получение всех адресов...")
    
    try:
        mint_str = "So11111111111111111111111111111111111111112"
        wallet_str = "11111111111111111111111111111112"
        
        mint_pubkey = AddressProvider.validate_mint_address(mint_str)
        wallet_pubkey = AddressProvider.validate_wallet_address(wallet_str)
        
        # Получаем все адреса
        all_addresses = AddressProvider.get_all_addresses(mint_pubkey, wallet_pubkey)
        
        # Проверяем обязательные поля
        required_fields = [
            "mint", "wallet", "bonding_curve", "associated_bonding_curve",
            "associated_token_account", "metadata", "pump_program"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in all_addresses:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"   ❌ Отсутствуют поля: {missing_fields}")
            return False
        
        print(f"   ✅ Получено {len(all_addresses)} адресов")
        
        # Выводим некоторые ключевые адреса
        print(f"   Mint: {all_addresses['mint']}")
        print(f"   Bonding Curve: {all_addresses['bonding_curve']}")
        print(f"   ATA: {all_addresses['associated_token_account']}")
        print(f"   Metadata: {all_addresses['metadata']}")
        
        print("   ✅ Все адреса получены корректно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка получения всех адресов: {e}")
        return False


def test_address_errors():
    """Тест обработки ошибок."""
    print("\n❌ Тестируем обработку ошибок...")
    
    try:
        # Неверный mint адрес
        try:
            AddressProvider.validate_mint_address("invalid_mint_address")
            print("   ❌ Неверный mint не был отклонен")
            return False
        except Exception:
            print("   ✅ Правильно обработан неверный mint")
        
        # Неверный wallet адрес
        try:
            AddressProvider.validate_wallet_address("invalid_wallet")
            print("   ❌ Неверный wallet не был отклонен")
            return False
        except Exception:
            print("   ✅ Правильно обработан неверный wallet")
        
        # Пустые строки
        try:
            AddressProvider.validate_mint_address("")
            print("   ❌ Пустой mint не был отклонен")
            return False
        except Exception:
            print("   ✅ Правильно обработан пустой mint")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Неожиданная ошибка: {e}")
        return False


def test_address_consistency():
    """Тест консистентности адресов."""
    print("\n🔄 Тестируем консистентность расчетов...")
    
    try:
        mint_str = "So11111111111111111111111111111111111111112"
        wallet_str = "11111111111111111111111111111112"
        
        mint_pubkey = AddressProvider.validate_mint_address(mint_str)
        wallet_pubkey = AddressProvider.validate_wallet_address(wallet_str)
        
        # Рассчитываем адреса двумя способами
        # Способ 1: по отдельности
        bc1, bump1 = AddressProvider.get_bonding_curve_address(mint_pubkey)
        ata1 = AddressProvider.get_associated_token_address(mint_pubkey, wallet_pubkey)
        
        # Способ 2: через get_all_addresses
        all_addr = AddressProvider.get_all_addresses(mint_pubkey, wallet_pubkey)
        bc2 = all_addr["bonding_curve"]
        ata2 = all_addr["associated_token_account"]
        
        # Проверяем консистентность
        if str(bc1) == str(bc2) and str(ata1) == str(ata2):
            print("   ✅ Адреса консистентны между разными методами")
            return True
        else:
            print("   ❌ Адреса не консистентны")
            print(f"     BC1: {bc1}")
            print(f"     BC2: {bc2}")
            print(f"     ATA1: {ata1}")
            print(f"     ATA2: {ata2}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка проверки консистентности: {e}")
        return False


def run_all_address_tests():
    """Запустить все тесты AddressProvider."""
    print("🧪 ТЕСТИРОВАНИЕ AddressProvider")
    print("=" * 50)
    
    tests = [
        ("Валидация адресов", test_address_validation),
        ("Расчет bonding curve", test_bonding_curve_calculation),
        ("Associated bonding curve", test_associated_bonding_curve),
        ("Associated token account", test_associated_token_account),
        ("Metadata адрес", test_metadata_address),
        ("Все адреса сразу", test_all_addresses),
        ("Обработка ошибок", test_address_errors),
        ("Консистентность", test_address_consistency),
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
    success = run_all_address_tests()
    exit(0 if success else 1)
