# core_atlas/client.py
import os
import time
import logging
from typing import Optional, Dict, Any, Union
from urllib3.util.retry import Retry

import requests
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)


class AtlasError(Exception):
    """Erro base para a API Atlas."""
    pass


class AuthenticationError(AtlasError):
    """Erro de autenticação (401)."""
    pass


class AuthorizationError(AtlasError):
    """Erro de permissão (403)."""
    pass


class MTLSError(AtlasError):
    """Erro de mTLS (certificado, chave, etc)."""
    pass


class RateLimitError(AtlasError):
    """Erro de limite de requisições (429)."""
    pass


class ServerError(AtlasError):
    """Erro do servidor (500+)."""
    pass


class AtlasClient:
    """
    Cliente HTTP para a API GlobalSign Atlas com suporte a mTLS.
    
    Features:
    - mTLS com certificado e chave
    - Retry automático para erros transitórios (429, 503)
    - Timeout configurável
    - Logging estruturado
    - Exceções específicas por tipo de erro
    """
    
    def __init__(
        self,
        base_url: str,
        cert_path: str,
        key_path: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        verbose: bool = False
    ):
        """
        Inicializa o cliente HTTP.
        
        Args:
            base_url: URL base da API
            cert_path: Caminho do certificado mTLS (.pem)
            key_path: Caminho da chave mTLS (.key)
            timeout: Timeout em segundos para requisições
            max_retries: Número máximo de tentativas para erros transitórios
            backoff_factor: Fator de backoff entre tentativas
            verbose: Loga detalhes das requisições
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verbose = verbose
        self.token: Optional[str] = None
        self.cert = (cert_path, key_path)
        self.last_location: Optional[str] = None
        
        # Cria a sessão com retry
        self.session = requests.Session()
        self.session.cert = self.cert
        
        # Configura retry com backoff exponencial
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PATCH", "DELETE"],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Headers padrão
        user_agent = os.getenv('ATLAS_USER_AGENT', 'AtlasPKIAutomationEngine/1.0')
        self.session.headers.update({
            'Content-Type': 'application/json; charset=utf-8',
            'User-Agent': user_agent,
            'Accept': 'application/json'
        })
    
    def set_token(self, token: str):
        """Define o token JWT para autenticação."""
        self.token = token
        self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def _log_request(self, method: str, endpoint: str, status: int, **kwargs):
        """Loga detalhes da requisição (se verbose)."""
        if self.verbose:
            logger.info(f"[API] {method} {endpoint} → {status}")
            if self.last_location:
                logger.info(f"  ↳ Location: {self.last_location}")
            if 'json' in kwargs and kwargs['json']:
                payload = kwargs['json']
                if 'api_key' in payload:
                    payload = payload.copy()
                    payload['api_key'] = '***'
                if 'api_secret' in payload:
                    payload = payload.copy()
                    payload['api_secret'] = '***'
                logger.debug(f"  ↳ Payload: {payload}")
    
    def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Executa uma requisição HTTP com tratamento de erros.
        
        Args:
            method: Método HTTP (GET, POST, PATCH, DELETE)
            endpoint: Endpoint da API (ex: '/v2/login')
            **kwargs: Argumentos passados para requests.Session.request()
            
        Returns:
            Dict[str, Any]: Resposta da API parseada como JSON, com 'location' se disponível
            
        Raises:
            AuthenticationError: 401 - Credenciais inválidas
            AuthorizationError: 403 - Sem permissão
            RateLimitError: 429 - Muitas requisições
            ServerError: 500+ - Erro do servidor
            MTLSError: Erro de mTLS
            AtlasError: Outros erros
        """
        url = f"{self.base_url}{endpoint}"
        
        kwargs.setdefault('timeout', self.timeout)
        
        headers = kwargs.setdefault('headers', {})
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Captura o header Location (essencial para operações assíncronas)
            self.last_location = response.headers.get('Location')
            
            self._log_request(method, endpoint, response.status_code, **kwargs)
            
            # Tratamento de erros HTTP
            if response.status_code >= 400:
                error_msg = self._parse_error(response)
                
                if response.status_code == 401:
                    raise AuthenticationError(f"Falha de autenticação (401): {error_msg}")
                elif response.status_code == 403:
                    raise AuthorizationError(f"Sem permissão (403): {error_msg}")
                elif response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', 'N/A')
                    raise RateLimitError(f"Limite de requisições excedido (429). Aguarde {retry_after} segundos. {error_msg}")
                elif response.status_code >= 500:
                    raise ServerError(f"Erro do servidor {response.status_code}: {error_msg}")
                else:
                    raise AtlasError(f"Erro {response.status_code}: {error_msg}")
            
            # Processa resposta - INCLUINDO O LOCATION
            result = response.json() if response.content else {}
            if self.last_location:
                result['location'] = self.last_location
            return result
            
        except requests.exceptions.SSLError as e:
            raise MTLSError(f"Falha de SSL/mTLS. Verifique certificado e chave: {e}")
        except requests.exceptions.ConnectionError as e:
            raise AtlasError(f"Falha de conexão com a API: {e}")
        except requests.exceptions.Timeout as e:
            raise AtlasError(f"Timeout na requisição (>{self.timeout}s): {e}")
        except requests.exceptions.RequestException as e:
            raise AtlasError(f"Erro na requisição: {e}")
    
    def _parse_error(self, response: requests.Response) -> str:
        """Extrai a mensagem de erro da resposta da API."""
        try:
            data = response.json()
            if 'description' in data:
                return data['description']
            elif 'message' in data:
                return data['message']
            elif 'error' in data:
                return str(data['error'])
            else:
                return str(data)
        except (ValueError, KeyError):
            return response.text[:200] if response.text else "Sem detalhes do erro"
    
    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request."""
        return self.request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """POST request."""
        return self.request('POST', endpoint, **kwargs)
    
    def patch(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """PATCH request."""
        return self.request('PATCH', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request."""
        return self.request('DELETE', endpoint, **kwargs)
    
    def close(self):
        """Fecha a sessão HTTP."""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
