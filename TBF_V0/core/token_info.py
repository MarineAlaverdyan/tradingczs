"""
TokenInfo класс для хранения данных о токене от слушателя.
Содержит все необходимые данные для торговли без пересчета адресов.
"""

from dataclasses import dataclass
from typing import Optional
from solders.pubkey import Pubkey


@dataclass
class TokenInfo:
    """
    Информация о токене, полученная от слушателя событий.
    Содержит все готовые адреса для торговли.
    """
    
    # Основные данные токена
    name: str
    symbol: str
    uri: str
    mint: Pubkey
    
    # Готовые адреса от слушателя (НЕ пересчитывать!)
    bonding_curve: Pubkey
    associated_bonding_curve: Pubkey
    
    # Пользователи
    user: Pubkey  # Создатель токена
    creator: Optional[Pubkey] = None  # Может совпадать с user
    
    # Дополнительная информация
    creation_timestamp: Optional[float] = None
    
    @classmethod
    def from_listener_data(cls, listener_data: dict) -> 'TokenInfo':
        """
        Создает TokenInfo из данных слушателя.
        
        Args:
            listener_data: Словарь с данными от слушателя
            
        Returns:
            TokenInfo объект
        """
        return cls(
            name=listener_data['name'],
            symbol=listener_data['symbol'],
            uri=listener_data['uri'],
            mint=Pubkey.from_string(listener_data['mint']),
            bonding_curve=Pubkey.from_string(listener_data['bondingCurve']),
            associated_bonding_curve=Pubkey.from_string(listener_data['associatedBondingCurve']),
            user=Pubkey.from_string(listener_data['user']),
            creator=Pubkey.from_string(listener_data.get('creator', listener_data['user']))
        )
    
    def to_dict(self) -> dict:
        """
        Конвертирует TokenInfo в словарь для логирования.
        
        Returns:
            Словарь с данными токена
        """
        return {
            'name': self.name,
            'symbol': self.symbol,
            'uri': self.uri,
            'mint': str(self.mint),
            'bonding_curve': str(self.bonding_curve),
            'associated_bonding_curve': str(self.associated_bonding_curve),
            'user': str(self.user),
            'creator': str(self.creator) if self.creator else None,
            'creation_timestamp': self.creation_timestamp
        }
    
    def __str__(self) -> str:
        """Строковое представление токена."""
        return f"TokenInfo(symbol={self.symbol}, mint={self.mint})"
    
    def __repr__(self) -> str:
        """Детальное представление токена."""
        return (f"TokenInfo(name='{self.name}', symbol='{self.symbol}', "
                f"mint={self.mint}, bonding_curve={self.bonding_curve})")


# Пример использования
if __name__ == "__main__":
    # Пример данных от слушателя
    listener_data = {
        'name': 'buy up',
        'symbol': 'buy up',
        'uri': 'https://ipfs.io/ipfs/Qmei5WUshDFeLJi5k8twgJZdKLC8g232r5RyjscjnTtjiT', 
        'mint': 'r8VCbeoXdsQ7RcXT9DF3CnJ2Fqdx9uNWywsV8Wepump', 
        'bondingCurve': 'AuUmsyXSAzKz4mTSEDX719rQvNpkz47rjbTn7QhU94SC',
        'associatedBondingCurve': 'CggVUQJEU2HWQRvMDAEiozNkPqKLMr5Mxc6zQPjnyrbz', 
        'user': '6pNDtUKGjbVVQLq8sQwdZW6heMuHAd6F5VpNSWfQvyfH'
    }
    
    # Создание TokenInfo
    token_info = TokenInfo.from_listener_data(listener_data)
    print("✅ TokenInfo создан:")
    print(f"   {token_info}")
    print(f"   Данные: {token_info.to_dict()}")
