"""
AddressProvider для pump.fun - расчет всех необходимых адресов.
Содержит константы pump.fun и функции для расчета PDA адресов.
"""

from solders.pubkey import Pubkey
from typing import Tuple


# Константы pump.fun программы
PUMP_PROGRAM_ID = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
PUMP_GLOBAL = Pubkey.from_string("4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5db6hjPuMkCjDQF")
PUMP_EVENT_AUTHORITY = Pubkey.from_string("Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1")
PUMP_FEE = Pubkey.from_string("CebN5WGQ4jvEPvsVU4EoHEpgzq1VV7AbicfhtW4xC9iM")

# Системные программы
SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
RENT_PROGRAM_ID = Pubkey.from_string("SysvarRent111111111111111111111111111111111")

# Метаданные программы
METADATA_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")

# Seeds для PDA расчетов
BONDING_CURVE_SEED = b"bonding-curve"
METADATA_SEED = b"metadata"


class AddressProvider:
    """Провайдер адресов для pump.fun операций."""
    
    @staticmethod
    def get_bonding_curve_address(mint: Pubkey) -> Tuple[Pubkey, int]:
        """
        Рассчитать адрес bonding curve для токена.
        
        Args:
            mint: Адрес mint токена
            
        Returns:
            Tuple[Pubkey, int]: (адрес bonding curve, bump)
        """
        try:
            bonding_curve, bump = Pubkey.find_program_address(
                [BONDING_CURVE_SEED, bytes(mint)],
                PUMP_PROGRAM_ID
            )
            return bonding_curve, bump
        except Exception as e:
            raise Exception(f"Ошибка расчета bonding curve адреса: {e}")
    
    @staticmethod
    def get_associated_bonding_curve_address(mint: Pubkey) -> Tuple[Pubkey, int]:
        """
        Рассчитать адрес associated bonding curve токен аккаунта.
        
        Args:
            mint: Адрес mint токена
            
        Returns:
            Tuple[Pubkey, int]: (адрес associated bonding curve, bump)
        """
        try:
            bonding_curve, _ = AddressProvider.get_bonding_curve_address(mint)
            
            associated_bonding_curve, bump = Pubkey.find_program_address(
                [
                    bytes(bonding_curve),
                    bytes(TOKEN_PROGRAM_ID),
                    bytes(mint)
                ],
                ASSOCIATED_TOKEN_PROGRAM_ID
            )
            return associated_bonding_curve, bump
        except Exception as e:
            raise Exception(f"Ошибка расчета associated bonding curve адреса: {e}")
    
    @staticmethod
    def get_associated_token_address(wallet: Pubkey, mint: Pubkey) -> Pubkey:
        """
        Рассчитать адрес associated token account для кошелька.
        
        Args:
            wallet: Публичный ключ кошелька
            mint: Адрес mint токена
            
        Returns:
            Адрес associated token account
        """
        try:
            associated_token_address, _ = Pubkey.find_program_address(
                [
                    bytes(wallet),
                    bytes(TOKEN_PROGRAM_ID),
                    bytes(mint)
                ],
                ASSOCIATED_TOKEN_PROGRAM_ID
            )
            return associated_token_address
        except Exception as e:
            raise Exception(f"Ошибка расчета associated token адреса: {e}")
    
    @staticmethod
    def get_metadata_address(mint: Pubkey) -> Tuple[Pubkey, int]:
        """
        Рассчитать адрес метаданных токена.
        
        Args:
            mint: Адрес mint токена
            
        Returns:
            Tuple[Pubkey, int]: (адрес метаданных, bump)
        """
        try:
            metadata_address, bump = Pubkey.find_program_address(
                [
                    METADATA_SEED,
                    bytes(METADATA_PROGRAM_ID),
                    bytes(mint)
                ],
                METADATA_PROGRAM_ID
            )
            return metadata_address, bump
        except Exception as e:
            raise Exception(f"Ошибка расчета metadata адреса: {e}")
    
    @staticmethod
    def get_all_addresses(mint: Pubkey, wallet: Pubkey) -> dict:
        """
        Получить все необходимые адреса для торговли токеном.
        
        Args:
            mint: Адрес mint токена
            wallet: Публичный ключ кошелька
            
        Returns:
            Словарь со всеми адресами
        """
        try:
            bonding_curve, bonding_curve_bump = AddressProvider.get_bonding_curve_address(mint)
            associated_bonding_curve, abc_bump = AddressProvider.get_associated_bonding_curve_address(mint)
            associated_token_account = AddressProvider.get_associated_token_address(wallet, mint)
            metadata, metadata_bump = AddressProvider.get_metadata_address(mint)
            
            return {
                # Основные адреса
                "mint": mint,
                "wallet": wallet,
                
                # PDA адреса
                "bonding_curve": bonding_curve,
                "bonding_curve_bump": bonding_curve_bump,
                "associated_bonding_curve": associated_bonding_curve,
                "associated_bonding_curve_bump": abc_bump,
                "associated_token_account": associated_token_account,
                "metadata": metadata,
                "metadata_bump": metadata_bump,
                
                # Системные программы
                "pump_program": PUMP_PROGRAM_ID,
                "system_program": SYSTEM_PROGRAM_ID,
                "token_program": TOKEN_PROGRAM_ID,
                "associated_token_program": ASSOCIATED_TOKEN_PROGRAM_ID,
                "rent_program": RENT_PROGRAM_ID,
                
                # pump.fun константы
                "pump_global": PUMP_GLOBAL,
                "pump_event_authority": PUMP_EVENT_AUTHORITY,
                "pump_fee": PUMP_FEE,
            }
        except Exception as e:
            raise Exception(f"Ошибка получения всех адресов: {e}")
    
    @staticmethod
    def validate_mint_address(mint_str: str) -> Pubkey:
        """
        Валидировать и конвертировать строку mint адреса в Pubkey.
        
        Args:
            mint_str: Mint адрес как строка
            
        Returns:
            Валидный Pubkey объект
            
        Raises:
            Exception: Если адрес невалидный
        """
        try:
            return Pubkey.from_string(mint_str)
        except Exception as e:
            raise Exception(f"Невалидный mint адрес '{mint_str}': {e}")
    
    @staticmethod
    def validate_wallet_address(wallet_str: str) -> Pubkey:
        """
        Валидировать и конвертировать строку wallet адреса в Pubkey.
        
        Args:
            wallet_str: Wallet адрес как строка
            
        Returns:
            Валидный Pubkey объект
            
        Raises:
            Exception: Если адрес невалидный
        """
        try:
            return Pubkey.from_string(wallet_str)
        except Exception as e:
            raise Exception(f"Невалидный wallet адрес '{wallet_str}': {e}")


# Пример использования
def main():
    """Пример использования AddressProvider."""
    
    print("🏠 Пример работы с AddressProvider")
    print("=" * 50)
    
    # Тестовые адреса (реальные devnet адреса)
    test_mint = Pubkey.from_string("11111111111111111111111111111111")  # System Program
    test_wallet = Pubkey.from_string("11111111111111111111111111111111")
    
    try:
        # Валидируем адреса
        print("🔍 Валидация адресов...")
        mint_pubkey = AddressProvider.validate_mint_address("11111111111111111111111111111111")
        wallet_pubkey = AddressProvider.validate_wallet_address("11111111111111111111111111111111")
        print(f"   Mint: {mint_pubkey}")
        print(f"   Wallet: {wallet_pubkey}")
        
        # Рассчитываем bonding curve
        print("\n📈 Расчет bonding curve...")
        bonding_curve, bc_bump = AddressProvider.get_bonding_curve_address(mint_pubkey)
        print(f"   Bonding Curve: {bonding_curve}")
        print(f"   Bump: {bc_bump}")
        
        # Рассчитываем associated bonding curve
        print("\n🔗 Расчет associated bonding curve...")
        abc, abc_bump = AddressProvider.get_associated_bonding_curve_address(mint_pubkey)
        print(f"   Associated Bonding Curve: {abc}")
        print(f"   Bump: {abc_bump}")
        
        # Рассчитываем associated token account
        print("\n💰 Расчет associated token account...")
        ata = AddressProvider.get_associated_token_address(wallet_pubkey, mint_pubkey)
        print(f"   Associated Token Account: {ata}")
        
        # Рассчитываем metadata
        print("\n📝 Расчет metadata...")
        metadata, meta_bump = AddressProvider.get_metadata_address(mint_pubkey)
        print(f"   Metadata: {metadata}")
        print(f"   Bump: {meta_bump}")
        
        # Получаем все адреса сразу
        print("\n📋 Все адреса:")
        all_addresses = AddressProvider.get_all_addresses(mint_pubkey, wallet_pubkey)
        
        for key, value in all_addresses.items():
            if isinstance(value, Pubkey):
                print(f"   {key}: {value}")
            else:
                print(f"   {key}: {value}")
        
        print("\n✅ Все расчеты выполнены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тестируем ошибки
    print("\n🚫 Тестирование обработки ошибок...")
    try:
        AddressProvider.validate_mint_address("invalid_address")
    except Exception as e:
        print(f"   Ожидаемая ошибка: {e}")


if __name__ == "__main__":
    main()
