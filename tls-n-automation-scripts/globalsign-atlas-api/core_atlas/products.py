# core_atlas/products.py
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

from .auth import AuthManager
from .models import Certificate


class ProductsAPI:
    """
    Interface de consumo dos contadores e produtos da API GlobalSign Atlas.
    
    Gerencia:
    - Consulta de contadores de certificados (emitidos, revogados)
    - Listagem de produtos disponíveis
    - Informações de consumo por produto
    """
    
    def __init__(self, auth):
        """
        Inicializa a API de produtos.
        
        Args:
            auth: Instância autenticada do AtlasAuth
        """
        self.auth = auth
        self.client = auth.get_client()
    
    def get_issued_count(self) -> int:
        """
        Retorna o número de certificados emitidos.
        
        Returns:
            int: Quantidade de certificados emitidos
        """
        try:
            response = self.client.request('GET', '/counters/certificates/issued')
            return response.get('value', 0)
        except Exception as e:
            # Log silencioso para não poluir a CLI
            return 0
    
    def get_revoked_count(self) -> int:
        """
        Retorna o número de certificados revogados.
        
        Returns:
            int: Quantidade de certificados revogados
        """
        try:
            response = self.client.request('GET', '/counters/certificates/revoked')
            return response.get('value', 0)
        except Exception as e:
            return 0
    
    def get_expiring_count(self, days: int = 30) -> int:
        """
        Retorna o número de certificados que expiram nos próximos N dias.
        
        Args:
            days: Janela de dias para verificar expiração
            
        Returns:
            int: Quantidade de certificados expirando
        """
        try:
            response = self.client.request(
                'GET',
                '/counters/certificates/expiring',
                params={'days': days}
            )
            return response.get('value', 0)
        except Exception as e:
            return 0
    
    def get_all_counts(self) -> Dict[str, int]:
        """
        Retorna todos os contadores de uma vez.
        
        Returns:
            Dict[str, int]: Dicionário com 'issued', 'revoked', 'expiring'
        """
        return {
            'issued': self.get_issued_count(),
            'revoked': self.get_revoked_count(),
            'expiring': self.get_expiring_count()
        }


def get_products_info() -> List[Dict[str, Any]]:
    """
    Retorna informações de todos os produtos disponíveis com seus contadores.
    
    Usa o AuthManager para gerenciar autenticação e cache.
    
    Returns:
        List[Dict[str, Any]]: Lista de produtos com nome, descrição, contadores
    """
    manager = AuthManager()
    products = manager.list_products()
    result = []
    
    for product in products:
        name = product['name']
        
        # Verifica se o produto está disponível (pasta de segredos existe)
        if not product.get('available', False):
            result.append({
                'name': name,
                'description': product['description'],
                'type': product['type'],
                'available': False,
                'issued': 0,
                'revoked': 0,
                'expiring': 0,
                'error': 'Produto indisponível (credenciais não encontradas)'
            })
            continue
        
        try:
            # Usa o AuthManager para obter autenticação (com cache)
            auth = manager.get_auth(name)
            api = ProductsAPI(auth)
            counts = api.get_all_counts()
            
            result.append({
                'name': name,
                'description': product['description'],
                'type': product['type'],
                'available': True,
                'issued': counts['issued'],
                'revoked': counts['revoked'],
                'expiring': counts['expiring']
            })
        except Exception as e:
            result.append({
                'name': name,
                'description': product['description'],
                'type': product['type'],
                'available': False,
                'issued': 0,
                'revoked': 0,
                'expiring': 0,
                'error': str(e)
            })
    
    return result


def get_product_info(product_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Retorna informações de um produto específico.
    
    Args:
        product_name: Nome do produto (ex: 'ssl_san5pack')
        
    Returns:
        Dict[str, Any]: Informações do produto
    """
    manager = AuthManager()
    
    if not product_name:
        product_name = manager.get_default_product()
    
    # Verifica se o produto existe
    products = manager.list_products()
    product = None
    for p in products:
        if p['name'] == product_name:
            product = p
            break
    
    if not product:
        raise KeyError(f"Produto '{product_name}' não encontrado.")
    
    # Tenta obter contadores
    try:
        auth = manager.get_auth(product_name)
        api = ProductsAPI(auth)
        counts = api.get_all_counts()
        
        return {
            'name': product_name,
            'description': product['description'],
            'type': product['type'],
            'available': True,
            'issued': counts['issued'],
            'revoked': counts['revoked'],
            'expiring': counts['expiring']
        }
    except Exception as e:
        return {
            'name': product_name,
            'description': product['description'],
            'type': product['type'],
            'available': False,
            'issued': 0,
            'revoked': 0,
            'expiring': 0,
            'error': str(e)
        }
