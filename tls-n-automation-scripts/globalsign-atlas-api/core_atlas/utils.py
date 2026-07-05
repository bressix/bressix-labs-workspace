# core_atlas/utils.py
import os
import re
from datetime import datetime
from typing import Optional, List, Any

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


class Colors:
    """Paleta de cores para saídas em terminais POSIX (CLI)"""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'


# =============================================================================
# CSR Validation
# =============================================================================

def validate_csr_file(csr_path: str) -> bool:
    """
    Valida se o arquivo CSR existe e se sua estrutura ASN.1 está intacta.
    
    Args:
        csr_path: Caminho para o arquivo CSR
        
    Returns:
        bool: True se o CSR for válido, False caso contrário
    """
    expanded_path = os.path.expanduser(csr_path)
    if not os.path.exists(expanded_path):
        return False
    
    try:
        with open(expanded_path, 'rb') as f:
            csr_data = f.read()
        x509.load_pem_x509_csr(csr_data, default_backend())
        return True
    except Exception:
        return False


def load_csr(csr_path: str) -> Optional[x509.CertificateSigningRequest]:
    """
    Carrega e parseia um arquivo CSR.
    
    Args:
        csr_path: Caminho para o arquivo CSR
        
    Returns:
        x509.CertificateSigningRequest: Objeto CSR ou None se falhar
    """
    expanded_path = os.path.expanduser(csr_path)
    if not os.path.exists(expanded_path):
        return None
    
    try:
        with open(expanded_path, 'rb') as f:
            csr_data = f.read()
        return x509.load_pem_x509_csr(csr_data, default_backend())
    except Exception:
        return None


# =============================================================================
# CSR Extractions
# =============================================================================

def extract_cn_from_csr(csr_path: str) -> Optional[str]:
    """
    Extrai o Common Name (CN) do CSR.
    
    Args:
        csr_path: Caminho para o arquivo CSR
        
    Returns:
        str: CN extraído ou None se falhar
    """
    csr = load_csr(csr_path)
    if not csr:
        return None
    
    try:
        cn_attributes = csr.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        if cn_attributes:
            return str(cn_attributes[0].value).strip().lower()
    except Exception:
        pass
    return None


def extract_sans_from_csr(csr_path: str) -> dict:
    """
    Extrai os Subject Alternative Names (SANs) do CSR.
    
    Args:
        csr_path: Caminho para o arquivo CSR
        
    Returns:
        dict: Dicionário com dns_names, ip_addresses, email_addresses, uris
    """
    csr = load_csr(csr_path)
    if not csr:
        return {'dns_names': [], 'ip_addresses': [], 'email_addresses': [], 'uris': []}
    
    result = {
        'dns_names': [],
        'ip_addresses': [],
        'email_addresses': [],
        'uris': []
    }
    
    try:
        # Procura pela extensão SAN no CSR
        for ext in csr.extensions:
            if ext.oid == x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME:
                san = ext.value
                
                # DNS Names
                for name in san.get_values_for_type(x509.DNSName):
                    result['dns_names'].append(str(name))
                
                # IP Addresses
                for ip in san.get_values_for_type(x509.IPAddress):
                    result['ip_addresses'].append(str(ip))
                
                # Email Addresses
                for email in san.get_values_for_type(x509.RFC822Name):
                    result['email_addresses'].append(str(email))
                
                # URIs
                for uri in san.get_values_for_type(x509.UniformResourceIdentifier):
                    result['uris'].append(str(uri))
                
                break
    except Exception:
        pass
    
    return result


def extract_eku_from_csr(csr_path: str) -> List[str]:
    """
    Extrai os Extended Key Usages (EKUs) do CSR.
    
    Args:
        csr_path: Caminho para o arquivo CSR
        
    Returns:
        List[str]: Lista de OIDs dos EKUs encontrados
    """
    csr = load_csr(csr_path)
    if not csr:
        return []
    
    ekus = []
    try:
        for ext in csr.extensions:
            if ext.oid == x509.ExtensionOID.EXTENDED_KEY_USAGE:
                eku_ext = ext.value
                for eku in eku_ext:
                    # OID como string (ex: "1.3.6.1.5.5.7.3.1")
                    ekus.append(eku.oid.dotted_string)
                break
    except Exception:
        pass
    
    return ekus


def extract_eku_names_from_csr(csr_path: str) -> List[str]:
    """
    Extrai os Extended Key Usages (EKUs) do CSR por nome amigável.
    
    Args:
        csr_path: Caminho para o arquivo CSR
        
    Returns:
        List[str]: Lista de nomes dos EKUs (ex: "serverAuth", "clientAuth")
    """
    ekus = extract_eku_from_csr(csr_path)
    
    # Mapeamento OID -> Nome
    eku_names = {
        "1.3.6.1.5.5.7.3.1": "serverAuth",
        "1.3.6.1.5.5.7.3.2": "clientAuth",
        "1.3.6.1.5.5.7.3.3": "codeSigning",
        "1.3.6.1.5.5.7.3.4": "emailProtection",
        "1.3.6.1.5.5.7.3.8": "timeStamping",
        "1.3.6.1.5.5.7.3.9": "ocspSigning"
    }
    
    return [eku_names.get(eku, eku) for eku in ekus]


def csr_summary(csr_path: str) -> dict:
    """
    Retorna um resumo completo de um CSR.
    
    Args:
        csr_path: Caminho para o arquivo CSR
        
    Returns:
        dict: Resumo com CN, SANs, EKUs e Subject
    """
    csr = load_csr(csr_path)
    if not csr:
        return {
            'valid': False,
            'error': 'Falha ao carregar o CSR'
        }
    
    # Subject
    subject = {}
    for attr in csr.subject:
        subject[attr.oid._name] = attr.value
    
    # SANs
    sans = extract_sans_from_csr(csr_path)
    
    # EKUs
    ekus = extract_eku_names_from_csr(csr_path)
    
    return {
        'valid': True,
        'subject': subject,
        'common_name': subject.get('commonName'),
        'sans': sans,
        'ekus': ekus,
        'has_sans': any(sans.values()),
        'has_ekus': bool(ekus)
    }


# =============================================================================
# Domain Validation
# =============================================================================

def validate_domain(domain: str) -> bool:
    """
    Valida a conformidade de sintaxe RFC para nomes de domínio.
    
    Args:
        domain: Nome de domínio a validar
        
    Returns:
        bool: True se o domínio for válido, False caso contrário
    """
    if not domain:
        return False
    clean_domain = domain.rstrip('.')
    if len(clean_domain) > 253:
        return False
    # RFC 1035 para labels de DNS
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, clean_domain))


def normalize_domain(domain: str) -> str:
    """Normaliza domínios: strip, lowercase, remove trailing dot."""
    return str(domain).strip().lower().rstrip('.')


# =============================================================================
# Date Utilities
# =============================================================================

def timestamp_to_date(timestamp: Any, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Converte timestamps para strings de data legíveis.
    
    Suporta:
    - Timestamps Unix (segundos ou milissegundos)
    - Strings ISO 8601
    - Objetos datetime
    """
    if not timestamp:
        return ''
    
    try:
        # Se for datetime object
        if isinstance(timestamp, datetime):
            return timestamp.strftime(fmt)
        
        # Se for string ISO
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime(fmt)
            except ValueError:
                pass
        
        # Se for numérico (timestamp)
        val = float(timestamp)
        if val > 5000000000:
            val = val / 1000.0
        return datetime.fromtimestamp(val).strftime(fmt)
    except Exception:
        return str(timestamp)
