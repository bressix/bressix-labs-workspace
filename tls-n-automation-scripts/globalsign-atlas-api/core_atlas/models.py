# core_atlas/models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class VerificationMethod(str, Enum):
    """Métodos de validação de domínio suportados pela GlobalSign."""
    DNS = "DNS"
    EMAIL = "EMAIL"
    FILE = "FILE"
    CNAME = "CNAME"
    HTTP = "HTTP"


class CertificateStatus(str, Enum):
    """Status possíveis de um certificado."""
    PENDING = "PENDING"
    ISSUED = "ISSUED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


# =============================================================================
# Utilitários de Data
# =============================================================================

def parse_api_date(date_val: Any) -> Optional[str]:
    """
    Parser robusto para datas da API GlobalSign Atlas.
    
    Suporta:
    - Timestamps Unix (segundos ou milissegundos)
    - Strings ISO 8601 com ou sem timezone
    - Strings simples de data
    """
    if not date_val:
        return None
    
    try:
        # Se for int ou float (timestamp Unix)
        if isinstance(date_val, (int, float)):
            # Detecta se está em milissegundos (comum em APIs Java/Go)
            if date_val > 5000000000:
                date_val = date_val / 1000.0
            return datetime.fromtimestamp(date_val).strftime('%Y-%m-%d %H:%M:%S')
        
        # Se for string
        if isinstance(date_val, str):
            date_str = date_val.strip()
            
            # Timestamp numérico em string
            if date_str.isdigit():
                ts = int(date_str)
                if ts > 5000000000:
                    ts = ts // 1000
                return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            
            # Tenta ISO 8601
            try:
                # Remove timezone info para simplificar
                if 'Z' in date_str:
                    date_str = date_str.replace('Z', '+00:00')
                
                # Tenta parse com fromisoformat (Python 3.7+)
                dt = datetime.fromisoformat(date_str)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
            
            # Tenta formatos comuns
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
            
            # Retorna a string original se não conseguir parserar
            return date_str
        
        return str(date_val)
        
    except Exception:
        return str(date_val)


# =============================================================================
# Modelos
# =============================================================================

@dataclass
class AtlasCredentials:
    """Credenciais descriptografadas da API."""
    api_key: str
    api_secret: str


@dataclass
class LoginResponse:
    """Resposta do endpoint /login."""
    access_token: str
    expires_in: int = 600
    token_type: str = "Bearer"
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'LoginResponse':
        """Constrói a partir da resposta da API com validação."""
        access_token = data.get('access_token')
        if not access_token:
            raise ValueError("Resposta de login inválida: 'access_token' ausente")
        
        expires_in = data.get('expires_in', 600)
        if isinstance(expires_in, str):
            expires_in = int(expires_in)
        
        token_type = data.get('token_type', 'Bearer')
        
        return cls(
            access_token=access_token,
            expires_in=expires_in,
            token_type=token_type
        )


@dataclass
class Certificate:
    """
    Representação de um certificado TLS.
    
    A API GlobalSign Atlas retorna:
    - certificate: O certificado PEM (contém not_before e not_after)
    - status: "ISSUED", "REVOKED", etc.
    - not_after: Timestamp de expiração (Unix) - também no PEM
    - updated_at: Timestamp da última atualização (Unix)
    """
    serial_number: str
    certificate: Optional[str] = None
    status: Optional[CertificateStatus] = None
    not_before: Optional[str] = None
    not_after: Optional[str] = None
    updated_at: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = field(default=None, repr=False)
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any], serial: Optional[str] = None) -> 'Certificate':
        """
        Constrói um Certificate a partir da resposta da API.
        
        Args:
            data: Resposta da API (dict com 'certificate', 'status', 'not_after', 'updated_at')
            serial: Número serial (se não estiver no data, usado como fallback)
            
        Returns:
            Certificate: Instância preenchida
        """
        # Tenta obter o serial de várias fontes
        serial_number = data.get('serial_number')
        if not serial_number and serial:
            serial_number = serial
        if not serial_number:
            serial_number = data.get('id') or data.get('certificate_id') or 'unknown'
        
        # Extrai status
        status = data.get('status')
        if status:
            try:
                status = CertificateStatus(status.upper())
            except ValueError:
                status = None
        
        # Extrai o certificado PEM
        cert_pem = data.get('certificate')
        
        # Tenta extrair not_before e not_after do PEM
        # (a API nem sempre retorna not_before no JSON)
        not_before = None
        not_after = parse_api_date(data.get('not_after'))
        
        if cert_pem:
            try:
                from cryptography import x509
                from cryptography.hazmat.backends import default_backend
                cert_obj = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
                
                # Extrai not_before do PEM (usando not_valid_before_utc para evitar warning)
                not_before = cert_obj.not_valid_before_utc.strftime('%Y-%m-%d %H:%M:%S')
                
                # Se a API não retornou not_after, extrai do PEM também
                if not not_after:
                    not_after = cert_obj.not_valid_after_utc.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.debug(f"Não foi possível extrair datas do PEM: {e}")
        
        return cls(
            serial_number=str(serial_number),
            certificate=cert_pem,
            status=status,
            not_before=not_before,
            not_after=not_after,
            updated_at=parse_api_date(data.get('updated_at')),
            raw_data=data
        )
    
    @property
    def is_issued(self) -> bool:
        return self.status == CertificateStatus.ISSUED
    
    @property
    def is_expired(self) -> bool:
        return self.status == CertificateStatus.EXPIRED
    
    @property
    def is_revoked(self) -> bool:
        return self.status == CertificateStatus.REVOKED


@dataclass
class DomainClaim:
    """Representação de uma validação/reivindicação de domínio."""
    claim_id: str
    domain: str
    status: str
    token: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: Optional[str] = None
    last_verified_at: Optional[str] = None
    verification_method: Optional[VerificationMethod] = None
    raw_data: Optional[Dict[str, Any]] = field(default=None, repr=False)
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'DomainClaim':
        """Constrói a partir da resposta da API."""
        claim_id = data.get('id') or data.get('claim_id')
        if not claim_id:
            raise ValueError("Resposta de domain claim inválida: 'id' ausente")
        
        domain = data.get('domain')
        if not domain:
            raise ValueError("Resposta de domain claim inválida: 'domain' ausente")
        
        method = data.get('verification_method') or data.get('method')
        if method:
            try:
                method = VerificationMethod(method.upper())
            except ValueError:
                method = None
        
        return cls(
            claim_id=str(claim_id),
            domain=domain,
            status=data.get('status', 'PENDING'),
            token=data.get('token'),
            expires_at=parse_api_date(data.get('expires_at')),
            created_at=parse_api_date(data.get('created_at')),
            last_verified_at=parse_api_date(data.get('last_verified_at')),
            verification_method=method,
            raw_data=data
        )
    
    @property
    def is_verified(self) -> bool:
        return str(self.status).upper() == 'VERIFIED'
    
    @property
    def is_pending(self) -> bool:
        return str(self.status).upper() == 'PENDING'


@dataclass
class ApiError:
    """Representação de um erro da API."""
    description: str
    id: Optional[str] = None
    status_code: Optional[int] = None
    
    @classmethod
    def from_response(cls, response: Any) -> 'ApiError':
        """Constrói a partir de uma resposta HTTP."""
        if hasattr(response, 'status_code'):
            status_code = response.status_code
        else:
            status_code = None
        
        try:
            data = response.json()
            description = data.get('description', data.get('message', str(data)))
            error_id = data.get('id') or data.get('error_id')
        except Exception:
            description = getattr(response, 'text', str(response))[:200]
            error_id = None
        
        return cls(
            description=description,
            id=error_id,
            status_code=status_code
        )
    
    def __str__(self):
        if self.id:
            return f"[{self.id}] {self.description}"
        return self.description


@dataclass
class CertificateRequest:
    """Parâmetros para emissão de um certificado."""
    common_name: str
    san_dns: List[str]
    san_emails: Optional[List[str]] = None
    san_ips: Optional[List[str]] = None
    san_uris: Optional[List[str]] = None
    organization: Optional[str] = None
    organizational_unit: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    locality: Optional[str] = None
    validity_days: int = 90
    
    def to_api_payload(self) -> Dict[str, Any]:
        """Converte para o payload da API GlobalSign Atlas."""
        payload = {
            "common_name": self.common_name,
            "dns_names": self.san_dns,
            "validity_days": self.validity_days
        }
        
        if self.san_emails:
            payload["email_addresses"] = self.san_emails
        
        if self.san_ips:
            payload["ip_addresses"] = self.san_ips
        
        if self.san_uris:
            payload["uniform_resource_identifiers"] = self.san_uris
        
        # Subject DN (opcional)
        subject = {}
        if self.organization:
            subject["organization"] = self.organization
        if self.organizational_unit:
            subject["organizational_unit"] = self.organizational_unit
        if self.country:
            subject["country"] = self.country.upper()
        if self.state:
            subject["state"] = self.state
        if self.locality:
            subject["locality"] = self.locality
        
        if subject:
            payload["subject_dn"] = subject
        
        return payload
