import os

from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.hash import Hash
from solders.pubkey import Pubkey
from base58 import b58decode

def load_keypair_from_private_key(private_key_base58: str) -> Keypair:
    """Загружает Keypair из приватного ключа в формате base58."""
    private_key_bytes = b58decode(private_key_base58)
    keypair = Keypair.from_bytes(private_key_bytes)
    return keypair

def sign_transaction(transaction: VersionedTransaction, payer: Keypair, recent_blockhash: Hash) -> VersionedTransaction:
    """Подписывает транзакцию."""
    transaction.sign([payer], recent_blockhash)
    return transaction

