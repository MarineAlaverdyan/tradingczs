"""
Константы с публичными ключами программ Solana.
Используется для создания транзакций и расчета PDA адресов.
"""

from solders.pubkey import Pubkey


# === СИСТЕМНЫЕ ПРОГРАММЫ ===

# System Program ID
SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")

# SPL Token program ID
TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")

# Associated Token Account program ID  
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")

# Compute Budget Program ID (для priority fees)
COMPUTE_BUDGET_PROGRAM_ID = Pubkey.from_string("ComputeBudget111111111111111111111111111111")

# Rent Program ID
RENT_PROGRAM_ID = Pubkey.from_string("SysvarRent111111111111111111111111111111111")


# === PUMP.FUN ПРОГРАММЫ ===

# Pump.fun main program ID
PUMP_PROGRAM_ID = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")

# Pump.fun fee recipient
PUMP_FEE_RECIPIENT = Pubkey.from_string("CebN5WGQ4jvEPvsVU4EoHEpgzq1VV7AbicfhtW4xC9iM")

# Pump.fun global account
PUMP_GLOBAL = Pubkey.from_string("4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf")

# Pump.fun fee config program
PUMP_FEE_CONFIG_PROGRAM = Pubkey.from_string("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")

# Pump.fun fee config account - используем программу как аккаунт
PUMP_FEE_CONFIG_ACCOUNT = Pubkey.from_string("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")


# === METAPLEX ПРОГРАММЫ ===

# Metaplex Token Metadata program ID
METADATA_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")


# === RAYDIUM ПРОГРАММЫ (для миграции) ===

# Raydium AMM program ID
RAYDIUM_AMM_PROGRAM_ID = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")

# Raydium Authority
RAYDIUM_AUTHORITY = Pubkey.from_string("5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1")


# === WRAPPED SOL ===

# Wrapped SOL mint address
WSOL_MINT = Pubkey.from_string("So11111111111111111111111111111111111111112")


# === КОНСТАНТЫ ДЛЯ РАСЧЕТОВ ===

# Lamports в 1 SOL
LAMPORTS_PER_SOL = 1_000_000_000

# Стандартные размеры аккаунтов
ACCOUNT_SIZE_TOKEN = 165  # bytes
ACCOUNT_SIZE_MINT = 82    # bytes
ACCOUNT_SIZE_METADATA = 679  # bytes (примерно)


# === HELPER ФУНКЦИИ ===

def get_all_program_ids() -> dict:
    """
    Получить все program ID в виде словаря.
    
    Returns:
        Словарь с названиями программ и их ID
    """
    return {
        'system': SYSTEM_PROGRAM_ID,
        'token': TOKEN_PROGRAM_ID,
        'associated_token': ASSOCIATED_TOKEN_PROGRAM_ID,
        'compute_budget': COMPUTE_BUDGET_PROGRAM_ID,
        'rent': RENT_PROGRAM_ID,
        'pump_fun': PUMP_PROGRAM_ID,
        'pump_fee_config': PUMP_FEE_CONFIG_PROGRAM,
        'metadata': METADATA_PROGRAM_ID,
        'raydium_amm': RAYDIUM_AMM_PROGRAM_ID,
        'wsol_mint': WSOL_MINT
    }


def validate_program_id(program_id: Pubkey, expected_name: str) -> bool:
    """
    Проверить корректность program ID.
    
    Args:
        program_id: Публичный ключ программы
        expected_name: Ожидаемое название программы
        
    Returns:
        True если program ID корректен
    """
    all_programs = get_all_program_ids()
    expected_id = all_programs.get(expected_name)
    
    if not expected_id:
        return False
        
    return program_id == expected_id


# Пример использования
if __name__ == "__main__":
    print("🔑 Публичные ключи программ Solana")
    print("=" * 50)
    
    programs = get_all_program_ids()
    for name, pubkey in programs.items():
        print(f"{name:20}: {pubkey}")
    
    print(f"\n💰 LAMPORTS_PER_SOL: {LAMPORTS_PER_SOL:,}")
    print(f"📦 Token account size: {ACCOUNT_SIZE_TOKEN} bytes")
    print(f"🪙 Mint account size: {ACCOUNT_SIZE_MINT} bytes")
