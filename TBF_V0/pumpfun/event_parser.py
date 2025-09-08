"""
EventParser для pump.fun - парсинг событий создания токенов из транзакций.
Извлекает данные о новых токенах из сырых данных блокчейна.
"""

import base64
import json
import struct
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction


@dataclass
class TokenInfo:
    """Информация о токене."""
    mint: str
    name: str
    symbol: str
    uri: str
    creator: str
    bonding_curve: str
    associated_bonding_curve: str
    platform: str = "pump.fun"


class EventParser:
    """Парсер событий pump.fun."""
    
    # Константы pump.fun
    PUMP_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
    
    # Discriminator для инструкции создания токена (первые 8 байт)
    CREATE_DISCRIMINATOR = bytes([24, 30, 200, 40, 5, 28, 7, 119])
    
    @staticmethod
    def is_create_transaction(transaction_data: Dict[str, Any]) -> bool:
        """
        Проверить, является ли транзакция созданием токена pump.fun.
        
        Args:
            transaction_data: Данные транзакции из RPC
            
        Returns:
            True если это создание токена
        """
        try:
            # Проверяем наличие необходимых полей
            if "transaction" not in transaction_data:
                return False
            
            transaction = transaction_data["transaction"]
            
            # Проверяем наличие инструкций
            if "message" not in transaction or "instructions" not in transaction["message"]:
                return False
            
            instructions = transaction["message"]["instructions"]
            account_keys = transaction["message"]["accountKeys"]
            
            # Ищем инструкции pump.fun программы
            for instruction in instructions:
                program_id_index = instruction.get("programIdIndex")
                if program_id_index is not None and program_id_index < len(account_keys):
                    program_id = account_keys[program_id_index]
                    
                    # Проверяем, что это pump.fun программа
                    if program_id == EventParser.PUMP_PROGRAM_ID:
                        # Проверяем discriminator инструкции
                        data = instruction.get("data", "")
                        if data:
                            try:
                                decoded_data = base64.b64decode(data)
                                if len(decoded_data) >= 8:
                                    discriminator = decoded_data[:8]
                                    if discriminator == EventParser.CREATE_DISCRIMINATOR:
                                        return True
                            except Exception:
                                continue
            
            return False
            
        except Exception:
            return False
    
    @staticmethod
    def parse_create_event(transaction_data: Dict[str, Any]) -> Optional[TokenInfo]:
        """
        Парсить событие создания токена из транзакции.
        
        Args:
            transaction_data: Данные транзакции из RPC
            
        Returns:
            TokenInfo если парсинг успешен, иначе None
        """
        try:
            if not EventParser.is_create_transaction(transaction_data):
                return None
            
            transaction = transaction_data["transaction"]
            instructions = transaction["message"]["instructions"]
            account_keys = transaction["message"]["accountKeys"]
            
            # Находим инструкцию создания
            for instruction in instructions:
                program_id_index = instruction.get("programIdIndex")
                if program_id_index is not None and program_id_index < len(account_keys):
                    program_id = account_keys[program_id_index]
                    
                    if program_id == EventParser.PUMP_PROGRAM_ID:
                        data = instruction.get("data", "")
                        if data:
                            try:
                                decoded_data = base64.b64decode(data)
                                if len(decoded_data) >= 8 and decoded_data[:8] == EventParser.CREATE_DISCRIMINATOR:
                                    # Парсим данные инструкции
                                    return EventParser._parse_instruction_data(
                                        decoded_data, 
                                        instruction.get("accounts", []),
                                        account_keys
                                    )
                            except Exception:
                                continue
            
            return None
            
        except Exception as e:
            print(f"Ошибка парсинга события создания: {e}")
            return None
    
    @staticmethod
    def _parse_instruction_data(instruction_data: bytes, account_indices: List[int], account_keys: List[str]) -> Optional[TokenInfo]:
        """
        Парсить данные инструкции создания токена.
        
        Args:
            instruction_data: Байты данных инструкции
            account_indices: Индексы аккаунтов в инструкции
            account_keys: Список всех ключей аккаунтов
            
        Returns:
            TokenInfo если парсинг успешен
        """
        try:
            offset = 8  # Пропускаем discriminator
            
            # Парсим название токена (string)
            name_length = struct.unpack_from("<I", instruction_data, offset)[0]
            offset += 4
            name = instruction_data[offset:offset + name_length].decode("utf-8")
            offset += name_length
            
            # Парсим символ токена (string)
            symbol_length = struct.unpack_from("<I", instruction_data, offset)[0]
            offset += 4
            symbol = instruction_data[offset:offset + symbol_length].decode("utf-8")
            offset += symbol_length
            
            # Парсим URI метаданных (string)
            uri_length = struct.unpack_from("<I", instruction_data, offset)[0]
            offset += 4
            uri = instruction_data[offset:offset + uri_length].decode("utf-8")
            offset += uri_length
            
            # Извлекаем адреса из аккаунтов инструкции
            # Стандартный порядок аккаунтов в pump.fun create инструкции:
            # 0: mint
            # 1: mint_authority (pda)
            # 2: bonding_curve (pda)
            # 3: associated_bonding_curve (pda)
            # 4: global
            # 5: mpl_token_metadata
            # 6: metadata (pda)
            # 7: user (создатель)
            # 8: system_program
            # 9: token_program
            # 10: associated_token_program
            # 11: rent
            # 12: event_authority
            # 13: program
            
            if len(account_indices) >= 8:
                mint = account_keys[account_indices[0]]
                bonding_curve = account_keys[account_indices[2]]
                associated_bonding_curve = account_keys[account_indices[3]]
                creator = account_keys[account_indices[7]]
                
                return TokenInfo(
                    mint=mint,
                    name=name,
                    symbol=symbol,
                    uri=uri,
                    creator=creator,
                    bonding_curve=bonding_curve,
                    associated_bonding_curve=associated_bonding_curve,
                    platform="pump.fun"
                )
            
            return None
            
        except Exception as e:
            print(f"Ошибка парсинга данных инструкции: {e}")
            return None
    
    @staticmethod
    def parse_from_logs(logs: List[str]) -> Optional[TokenInfo]:
        """
        Парсить информацию о токене из логов транзакции.
        
        Args:
            logs: Список логов транзакции
            
        Returns:
            TokenInfo если найдена информация о создании токена
        """
        try:
            # Ищем логи pump.fun программы
            for log in logs:
                if "Program log:" in log and EventParser.PUMP_PROGRAM_ID in log:
                    # Здесь можно добавить парсинг специфичных логов pump.fun
                    # если они содержат дополнительную информацию
                    pass
            
            return None
            
        except Exception as e:
            print(f"Ошибка парсинга логов: {e}")
            return None
    
    @staticmethod
    def extract_token_metadata(uri: str) -> Dict[str, Any]:
        """
        Извлечь метаданные токена по URI.
        
        Args:
            uri: URI метаданных токена
            
        Returns:
            Словарь с метаданными
        """
        try:
            # Здесь можно добавить HTTP запрос к URI для получения метаданных
            # Пока возвращаем пустой словарь
            return {
                "description": "",
                "image": "",
                "external_url": "",
                "attributes": []
            }
            
        except Exception as e:
            print(f"Ошибка извлечения метаданных: {e}")
            return {}
    
    @staticmethod
    def validate_token_info(token_info: TokenInfo) -> bool:
        """
        Валидировать информацию о токене.
        
        Args:
            token_info: Информация о токене
            
        Returns:
            True если информация валидна
        """
        try:
            # Проверяем обязательные поля
            if not token_info.mint or not token_info.name or not token_info.symbol:
                return False
            
            # Проверяем валидность адресов
            try:
                Pubkey.from_string(token_info.mint)
                Pubkey.from_string(token_info.creator)
                Pubkey.from_string(token_info.bonding_curve)
                Pubkey.from_string(token_info.associated_bonding_curve)
            except Exception:
                return False
            
            # Проверяем длину названия и символа
            if len(token_info.name) > 100 or len(token_info.symbol) > 20:
                return False
            
            return True
            
        except Exception:
            return False


# Пример использования
def main():
    """Пример использования EventParser."""
    
    print("🔍 Пример работы с EventParser")
    print("=" * 40)
    
    # Пример транзакции создания токена (упрощенный формат)
    sample_transaction = {
        "transaction": {
            "message": {
                "accountKeys": [
                    "So11111111111111111111111111111111111111112",  # mint
                    "11111111111111111111111111111112",            # mint_authority
                    "bonding_curve_address_here",                 # bonding_curve
                    "associated_bonding_curve_address_here",      # associated_bonding_curve
                    "4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5db6hjPuMkCjDQF",  # global
                    "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s",   # mpl_token_metadata
                    "metadata_address_here",                      # metadata
                    "creator_address_here",                       # user/creator
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
                            struct.pack("<I", 20) + b"https://test.com/meta"  # uri
                        ).decode()
                    }
                ]
            }
        }
    }
    
    # Тестируем определение транзакции создания
    print("🔍 Проверяем, является ли транзакция созданием токена...")
    is_create = EventParser.is_create_transaction(sample_transaction)
    print(f"   Результат: {is_create}")
    
    # Тестируем парсинг (будет ошибка из-за неполных данных, но покажет процесс)
    print("\n📝 Пытаемся парсить событие создания...")
    try:
        token_info = EventParser.parse_create_event(sample_transaction)
        if token_info:
            print(f"   Название: {token_info.name}")
            print(f"   Символ: {token_info.symbol}")
            print(f"   Mint: {token_info.mint}")
            print(f"   Создатель: {token_info.creator}")
        else:
            print("   Не удалось парсить (ожидаемо для тестовых данных)")
    except Exception as e:
        print(f"   Ошибка парсинга: {e}")
    
    # Тестируем валидацию
    print("\n✅ Тестируем валидацию TokenInfo...")
    test_token = TokenInfo(
        mint="So11111111111111111111111111111111111111112",
        name="Test Token",
        symbol="TEST",
        uri="https://test.com",
        creator="11111111111111111111111111111112",
        bonding_curve="11111111111111111111111111111112",
        associated_bonding_curve="11111111111111111111111111111112"
    )
    
    is_valid = EventParser.validate_token_info(test_token)
    print(f"   Токен валиден: {is_valid}")
    
    print("\n🎉 Демонстрация EventParser завершена!")


if __name__ == "__main__":
    main()
