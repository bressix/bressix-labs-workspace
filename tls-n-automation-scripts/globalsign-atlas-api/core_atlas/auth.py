# core_atlas/auth.py
import os
import json
import time
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from dotenv import load_dotenv

from .client import AtlasClient
from .models import AtlasCredentials, LoginResponse

# Carrega variáveis de ambiente uma vez no módulo
load_dotenv()


class AuthManager:
    """
    Gerenciador multi-produto com isolamento de credenciais (OPSEC).
    
    Responsável por:
    - Carregar a configuração de produtos do products.yaml
    - Mapear produtos para seus respectivos diretórios de segredos
    - Instanciar e cachear objetos AtlasAuth por produto
    """
    
    def __init__(self, config_dir: str = "config"):
        # Define o diretório base do projeto (onde está o auth.py)
        self.base_dir = Path(__file__).resolve().parent.parent
        self.config_dir = Path(config_dir)
        
        self.products = self._load_products()
        self.instances: Dict[str, 'AtlasAuth'] = {}
        
        # Define o diretório base dos segredos (fora do repositório)
        # Prioridade: 1. Variável de ambiente, 2. ~/.secrets/, 3. Appendix (fallback)
        secrets_dir_env = os.getenv('ATLAS_SECRETS_DIR')
        if secrets_dir_env:
            self.secrets_base_dir = Path(secrets_dir_env).expanduser()
            print(f"[INFO] Usando ATLAS_SECRETS_DIR: {self.secrets_base_dir}")
        else:
            # Fallback 1: ~/.secrets/globalsign-atlas-api
            default_dir = Path.home() / '.secrets' / 'globalsign-atlas-api'
            if default_dir.exists():
                self.secrets_base_dir = default_dir
                print(f"[INFO] Usando diretório padrão: {self.secrets_base_dir}")
            else:
                # Fallback 2: Appendix (base_dir é globalsign-atlas-api, parents[2] vai para bressix-labs-workspace)
                appendix_fallback = self.base_dir.parents[2] / 'bressix-labs-workspace-appendix' / 'atlas_secrets'
                if appendix_fallback.exists():
                    self.secrets_base_dir = appendix_fallback
                    print(f"[WARN] Usando fallback (appendix): {self.secrets_base_dir}")
                else:
                    # Fallback 3: diretório atual (pode não existir)
                    self.secrets_base_dir = default_dir
                    print(f"[WARN] Nenhum diretório de segredos encontrado. Usando: {self.secrets_base_dir}")

    def _load_products(self) -> dict:
        """Carrega o mapeamento de produtos a partir do arquivo YAML."""
        # Usa o diretório base do projeto (não o diretório de execução)
        config_file = self.base_dir / self.config_dir / "products.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(
                f"Arquivo de configuração não encontrado: {config_file}"
            )
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def get_default_product(self) -> str:
        """Retorna o nome do produto padrão definido no YAML."""
        return self.products.get('default', 'ssl_test50pack')
        
    def list_products(self) -> List[Dict[str, str]]:
        """
        Lista todos os produtos disponíveis com metadados.
        
        Retorna:
            Lista de dicionários com 'name', 'description', 'type', 'secrets_folder'
        """
        prod_dict = self.products.get('products', {})
        result = []
        
        for name, meta in prod_dict.items():
            # Obtém o nome da pasta de segredos
            folder_name = meta.get('secrets_folder')
            if not folder_name:
                # Fallback para compatibilidade com versões anteriores
                if "san" in name:
                    folder_name = "atlas_san_5pack"
                elif "test" in name:
                    folder_name = "atlas_test_50pack"
                else:
                    folder_name = name.replace('ssl_', '')
            
            target_folder = self.secrets_base_dir / folder_name
            
            # Verifica se a pasta existe
            folder_exists = target_folder.exists()
            
            result.append({
                'name': name,
                'description': meta.get('description', ''),
                'type': meta.get('type', ''),
                'secrets_folder': folder_name,
                'available': folder_exists
            })
        
        return result
    
    def list_available_products(self) -> List[Dict[str, str]]:
        """
        Lista apenas os produtos que estão disponíveis 
        (ou seja, que têm a pasta de segredos existente).
        """
        return [p for p in self.list_products() if p['available']]
        
    def get_auth(self, product: Optional[str] = None) -> 'AtlasAuth':
        """
        Retorna uma instância autenticada para o produto especificado.
        
        Args:
            product: Nome do produto (ex: 'ssl_san5pack' ou 'san5pack')
            
        Returns:
            AtlasAuth: Instância autenticada e pronta para uso
            
        Raises:
            KeyError: Se o produto não existir no products.yaml
            FileNotFoundError: Se os arquivos de segredos não existirem
        """
        if not product:
            product = self.get_default_product()
            
        # Normaliza o nome do produto (remove prefixo 'ssl_' se presente)
        lookup_id = product
        if not lookup_id.startswith('ssl_'):
            lookup_id = f"ssl_{lookup_id}"
        
        products = self.products.get('products', {})
        if lookup_id not in products:
            # Mostra os produtos disponíveis para ajudar o usuário
            available = [p['name'] for p in self.list_products()]
            raise KeyError(
                f"Produto '{product}' não encontrado.\n"
                f"Produtos disponíveis: {', '.join(available)}"
            )
            
        if lookup_id not in self.instances:
            meta = products[lookup_id]
            
            # Obtém o nome da pasta de segredos a partir do YAML
            folder_name = meta.get('secrets_folder')
            if not folder_name:
                # Fallback para compatibilidade com versões anteriores
                if "san" in lookup_id:
                    folder_name = "atlas_san_5pack"
                elif "test" in lookup_id:
                    folder_name = "atlas_test_50pack"
                else:
                    folder_name = lookup_id.replace('ssl_', '')
            
            target_folder = self.secrets_base_dir / folder_name
            
            # Verifica se o diretório existe
            if not target_folder.exists():
                # Lista as pastas disponíveis para ajudar o usuário
                available_folders = [d.name for d in self.secrets_base_dir.iterdir() if d.is_dir()]
                raise FileNotFoundError(
                    f"Diretório de segredos não encontrado: {target_folder}\n"
                    f"Verifique se ATLAS_SECRETS_DIR está configurado corretamente.\n"
                    f"Valor atual: {self.secrets_base_dir}\n"
                    f"Pastas disponíveis em secrets: {', '.join(available_folders)}"
                )
            
            # Nomes padronizados (prioridade) com fallback para nomes antigos
            cert_file = self._find_file(target_folder, ['mtls.crt', f"{folder_name}-mtls_thiago.pem"])
            key_file = self._find_file(target_folder, ['mtls.key', f"{folder_name}-mtls_thiago.key"])
            private_key_file = self._find_file(target_folder, ['private.pem', f"{folder_name}_thiago_private-key.pem"])
            credentials_enc_file = self._find_file(target_folder, ['credentials.enc', f"{folder_name}_thiago_credentials.enc"])
            
            # Validação preventiva com mensagens claras
            missing_files = []
            file_names = [
                ("Certificado mTLS", cert_file),
                ("Chave mTLS", key_file),
                ("Chave privada RSA", private_key_file),
                ("Credenciais criptografadas", credentials_enc_file)
            ]
            
            for name, path in file_names:
                if path is None or not path.exists():
                    missing_files.append(f"  - {name}: {path or 'não encontrado'}")
            
            if missing_files:
                # Lista os arquivos disponíveis para ajudar o usuário
                available_files = [f.name for f in target_folder.iterdir() if f.is_file()]
                raise FileNotFoundError(
                    f"Erro OPSEC: Artefatos vitais do produto '{lookup_id}' ausentes em:\n"
                    f"  {target_folder}\n"
                    f"Arquivos esperados:\n" +
                    "\n".join(missing_files) +
                    f"\n\nArquivos disponíveis na pasta: {', '.join(available_files) if available_files else 'nenhum'}"
                )
            
            # Carrega configurações específicas do produto (product.env)
            product_env = target_folder / "product.env"
            env_vars = {}
            if product_env.exists():
                with open(product_env, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                env_vars[key.strip()] = value.strip()
            
            # Configuração para o AtlasAuth
            config = {
                'name': lookup_id,
                'base_url': env_vars.get('ATLAS_BASE_URL') or os.getenv(
                    'ATLAS_BASE_URL',
                    'https://emea.api.hvca.globalsign.com:8443/v2'
                ),
                'product_code': env_vars.get('ATLAS_PRODUCT_CODE', 'DV_SAN_5'),
                'mtls_cert': str(cert_file),
                'mtls_key': str(key_file),
                'private_key': str(private_key_file),
                'credentials_enc': str(credentials_enc_file)
            }
            
            self.instances[lookup_id] = AtlasAuth(config)
            
        return self.instances[lookup_id]
    
    def _find_file(self, directory: Path, candidates: list) -> Optional[Path]:
        """Procura um arquivo por lista de candidatos em ordem de prioridade."""
        for candidate in candidates:
            path = directory / candidate
            if path.exists():
                return path
        return None


class AtlasAuth:
    """
    Orquestrador de autenticação para a API GlobalSign Atlas.
    
    Gerencia:
    - Descriptografia RSA das credenciais em memória
    - Login e obtenção de token JWT
    - Renovação automática de token
    - Cliente HTTP com mTLS e JWT
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = AtlasClient(
            base_url=config['base_url'],
            cert_path=config['mtls_cert'],
            key_path=config['mtls_key']
        )
        self.credentials: Optional[AtlasCredentials] = None
        self.token: Optional[str] = None
        self.token_expires_at: float = 0.0

    def _decrypt_credentials(self) -> AtlasCredentials:
        """
        Descriptografa o arquivo .enc usando a chave privada RSA.
        
        Suporta tanto PKCS1v15 (legado) quanto OAEP (formato atual da GlobalSign).
        O arquivo .enc deve conter um JSON com os campos 'api_key' e 'api_secret'.
        
        Returns:
            AtlasCredentials: Credenciais descriptografadas
            
        Raises:
            RuntimeError: Se a descriptografia falhar
            ValueError: Se o formato do arquivo for inválido
        """
        try:
            # Lê a chave privada
            with open(self.config['private_key'], 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None  # Assumindo chave sem senha
                )
                
            # Lê os dados criptografados
            with open(self.config['credentials_enc'], 'rb') as f:
                encrypted_data = f.read()
                
            # Tenta descriptografar com PKCS1v15 (legado)
            decrypted_str = None
            try:
                decrypted = private_key.decrypt(encrypted_data, padding.PKCS1v15())
                decrypted_str = decrypted.decode('utf-8')
            except Exception as pkcs1_error:
                # Fallback: OAEP com SHA-256 (formato atual da GlobalSign)
                try:
                    decrypted = private_key.decrypt(
                        encrypted_data,
                        padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None
                        )
                    )
                    decrypted_str = decrypted.decode('utf-8')
                except Exception as oaep_error:
                    raise RuntimeError(
                        f"Falha ao descriptografar credenciais para {self.config['name']}.\n"
                        f"PKCS1v15: {pkcs1_error}\n"
                        f"OAEP: {oaep_error}\n"
                        f"Verifique se a chave privada corresponde ao arquivo .enc."
                    ) from oaep_error
            
            # Parser do JSON
            try:
                data = json.loads(decrypted_str)
            except json.JSONDecodeError:
                # Fallback: tenta parserar como texto plano (legado)
                lines = decrypted_str.strip().split('\n')
                credentials = {}
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        credentials[key.strip()] = value.strip()
                    elif '=' in line:
                        key, value = line.split('=', 1)
                        credentials[key.strip()] = value.strip()
                
                # Tenta diferentes formatos de chave
                if 'key' in credentials and 'secret' in credentials:
                    return AtlasCredentials(
                        api_key=credentials['key'],
                        api_secret=credentials['secret']
                    )
                elif 'api_key' in credentials and 'api_secret' in credentials:
                    return AtlasCredentials(
                        api_key=credentials['api_key'],
                        api_secret=credentials['api_secret']
                    )
                else:
                    # Se tiver apenas duas linhas sem chave, assume que são key e secret
                    if len(lines) >= 2 and not credentials:
                        return AtlasCredentials(
                            api_key=lines[0].strip(),
                            api_secret=lines[1].strip()
                        )
                    else:
                        raise ValueError(
                            f"Formato inválido no arquivo .enc.\n"
                            f"Esperado 'key:/secret:' ou 'api_key:/api_secret:' ou JSON.\n"
                            f"Conteúdo: {decrypted_str[:200]}..."
                        )
            
            # Valida o JSON
            if 'api_key' not in data or 'api_secret' not in data:
                raise ValueError(
                    f"JSON inválido no arquivo .enc. Campos esperados: 'api_key', 'api_secret'. "
                    f"Recebido: {list(data.keys())}"
                )
                
            return AtlasCredentials(
                api_key=data['api_key'],
                api_secret=data['api_secret']
            )
            
        except (OSError, ValueError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Falha ao descriptografar credenciais para {self.config['name']}: {e}"
            ) from e

    def login(self) -> str:
        """
        Realiza o login na API e obtém um token JWT.
        
        Returns:
            str: Access token JWT
            
        Raises:
            RuntimeError: Se o login falhar
        """
        if not self.credentials:
            self.credentials = self._decrypt_credentials()
            
        try:
            response = self.client.request(
                'POST',
                '/login',
                json={
                    "api_key": self.credentials.api_key,
                    "api_secret": self.credentials.api_secret
                }
            )
        except Exception as e:
            raise RuntimeError(
                f"Falha no login para {self.config['name']}: {e}"
            ) from e
        
        # Usa o método de fábrica para construir o LoginResponse
        try:
            login_response = LoginResponse.from_api_response(response)
        except (KeyError, TypeError, ValueError) as e:
            raise RuntimeError(
                f"Resposta de login inválida da GlobalSign: {response}"
            ) from e
        
        self.token = login_response.access_token
        # Margem de segurança de 60 segundos antes da expiração
        self.token_expires_at = time.time() + login_response.expires_in - 60
        self.client.set_token(self.token)
        
        return self.token

    def get_valid_token(self) -> str:
        """
        Retorna um token válido, renovando automaticamente se necessário.
        
        Returns:
            str: Token JWT válido
        """
        if not self.token or time.time() >= self.token_expires_at:
            return self.login()
        return self.token

    def get_client(self) -> AtlasClient:
        """Retorna o cliente HTTP com autenticação mTLS e token JWT válido."""
        self.get_valid_token()
        return self.client

    def get_info(self) -> dict:
        """Retorna informações sobre o produto configurado."""
        return {
            'name': self.config['name'],
            'base_url': self.config['base_url'],
            'product_code': self.config.get('product_code', 'N/A')
        }
