# core_atlas/certificates.py
import os
import time
import logging
import json
import shutil
import zipfile
import re
import fnmatch
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from .models import Certificate, CertificateStatus
from .utils import (
    validate_csr_file,
    extract_sans_from_csr,
    extract_cn_from_csr
)

logger = logging.getLogger(__name__)


class CertificatesAPI:
    """
    API de Gerenciamento de Certificados da GlobalSign Atlas.
    
    Gerencia:
    - Emissão de certificados a partir de CSR (síncrono e assíncrono)
    - Consulta de certificados
    - Revogação e rekey
    - Listagem de certificados emitidos/revogados/expirados
    - Empacotamento de certificados para entrega ao cliente
    - Busca de certificados por Common Name (substring ou wildcard)
    """
    
    def __init__(self, auth, auth_manager=None):
        """
        Inicializa a API de Certificados.
        
        Args:
            auth: Instância autenticada do AtlasAuth
            auth_manager: Instância do AuthManager (para listar produtos e obter padrão)
        """
        self.auth = auth
        self.auth_manager = auth_manager
        self.client = None
        self._policy_cache = None
    
    def _get_client(self):
        """Obtém o cliente HTTP com token válido."""
        if not self.client:
            self.client = self.auth.get_client()
        return self.client
    
    def _format_csr_for_api(self, csr_path: str) -> str:
        """
        Lê o CSR e retorna o conteúdo com quebras de linha reais.
        
        O json.dumps() no client.py se encarregará de escapar as quebras
        de linha para o formato correto (\n) que a GlobalSign espera.
        
        Args:
            csr_path: Caminho para o arquivo CSR
            
        Returns:
            str: Conteúdo do CSR com quebras de linha reais
            
        Raises:
            ValueError: Se o arquivo não for um CSR válido
        """
        expanded_path = Path(csr_path).expanduser()
        
        if not expanded_path.exists():
            raise ValueError(f"Arquivo CSR não encontrado: {csr_path}")
        
        with open(expanded_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica se é um CSR válido
        if '-----BEGIN CERTIFICATE REQUEST-----' not in content:
            raise ValueError(f"Arquivo inválido: {csr_path} (não é um CSR PEM válido)")
        
        if '-----END CERTIFICATE REQUEST-----' not in content:
            raise ValueError(f"Arquivo inválido: {csr_path} (não contém o final do CSR)")
        
        # Remove espaços extras no início e fim, mantendo as quebras de linha internas
        return content.strip()
    
    def _extract_serial_from_response(self, response: Dict[str, Any]) -> Optional[str]:
        """
        Extrai o número serial da resposta da API.
        
        Suporta:
        - Header Location: /v2/certificates/12345
        - Header Location: https://api.atlas.globalsign.com/v2/certificates/12345
        - Campo serial_number no corpo da resposta
        - Campo id no corpo da resposta
        """
        # 1. Tenta extrair do campo 'location' no corpo da resposta
        if 'location' in response:
            location = response['location']
            if '/certificates/' in location:
                parts = location.split('/certificates/')
                if len(parts) > 1:
                    serial_part = parts[1].split('?')[0].rstrip('/')
                    if serial_part:
                        return serial_part
            # Fallback: último segmento da URL
            parts = location.rstrip('/').split('/')
            if parts:
                return parts[-1]
        
        # 2. Tenta extrair do header Location (se disponível no client)
        if hasattr(self, '_get_client'):
            client = self._get_client()
            if hasattr(client, 'last_location') and client.last_location:
                location = client.last_location
                if '/certificates/' in location:
                    parts = location.split('/certificates/')
                    if len(parts) > 1:
                        serial_part = parts[1].split('?')[0].rstrip('/')
                        if serial_part:
                            return serial_part
                parts = location.rstrip('/').split('/')
                if parts:
                    return parts[-1]
        
        # 3. Tenta extrair do corpo da resposta
        if 'serial_number' in response:
            return str(response['serial_number'])
        
        if 'id' in response:
            return str(response['id'])
        
        return None
    
    def _get_validation_policy(self) -> Dict[str, Any]:
        """Obtém a política de validação com cache."""
        if self._policy_cache is None:
            try:
                self._policy_cache = self._get_client().request('GET', '/validationpolicy')
            except Exception as e:
                logger.warning(f"Falha ao obter política de validação: {e}")
                self._policy_cache = {}
        return self._policy_cache
    
    def _wait_for_certificate(self, serial: str, max_wait: int = 60, interval: int = 3) -> Certificate:
        """
        Aguarda o certificado ficar pronto com polling.
        
        A emissão de certificados na GlobalSign Atlas é assíncrona.
        Esta função faz polling até o certificado estar disponível.
        
        Args:
            serial: Número serial do certificado
            max_wait: Tempo máximo de espera em segundos (padrão: 60)
            interval: Intervalo entre tentativas em segundos (padrão: 3)
            
        Returns:
            Certificate: Certificado completo
            
        Raises:
            RuntimeError: Se o tempo limite for excedido
        """
        waited = 0
        
        while waited < max_wait:
            try:
                cert = self.get(serial)
                
                # Verifica se é "Operation in Progress" (raw_data)
                if cert.raw_data and 'Operation in Progress' in str(cert.raw_data):
                    print(f"⏳ Certificado {serial} em processamento... ({waited}s)")
                    time.sleep(interval)
                    waited += interval
                    continue
                
                # Verifica se o certificado está pronto
                if cert.certificate:
                    return cert
                
                if cert.status == CertificateStatus.ISSUED:
                    return cert
                    
            except Exception as e:
                error_str = str(e)
                if 'Operation in Progress' in error_str or 'not found' in error_str.lower():
                    print(f"⏳ Certificado {serial} em processamento... ({waited}s)")
                    time.sleep(interval)
                    waited += interval
                    continue
                else:
                    raise
            
            time.sleep(interval)
            waited += interval
        
        # Se chegou aqui, o tempo máximo foi excedido
        raise RuntimeError(
            f"Tempo limite excedido ({max_wait}s) aguardando o certificado {serial}. "
            "Verifique o status manualmente com: atlas_cli.py cert --get <serial>"
        )
    
    def issue(
        self,
        csr_path: str,
        product: Optional[str] = None,
        validity_days: int = 90,
        ekus: Optional[List[str]] = None,  # Mantido para compatibilidade, mas ignorado
        max_wait: int = 60
    ) -> Certificate:
        """
        Emite um novo certificado a partir de um CSR (síncrono).
        
        Aguarda o certificado ficar pronto antes de retornar.
        
        Args:
            csr_path: Caminho para o arquivo CSR (.csr ou .pem)
            product: Nome do produto (ex: 'ssl_san5pack')
            validity_days: Dias de validade (máx 90)
            ekus: Ignorado - a política da CA define os EKUs automaticamente (STATIC)
            max_wait: Tempo máximo de espera em segundos (padrão: 60)
            
        Returns:
            Certificate: Instância do certificado emitido
            
        Raises:
            ValueError: Se o CSR for inválido
            RuntimeError: Se a API falhar ou o tempo limite for excedido
        """
        # 1. Valida CSR
        if not validate_csr_file(csr_path):
            raise ValueError(f"Arquivo CSR inválido ou inacessível: {csr_path}")
        
        # 2. Extrai informações do CSR
        csr_sans = extract_sans_from_csr(csr_path)
        csr_cn = extract_cn_from_csr(csr_path)
        
        if not csr_cn:
            raise ValueError("Não foi possível extrair o Common Name do CSR")
        
        # 3. Obtém o produto (se não fornecido, usa o padrão do AuthManager)
        if not product:
            if self.auth_manager:
                product = self.auth_manager.get_default_product()
            else:
                raise ValueError("Produto não especificado e AuthManager não disponível")
        
        # 4. Formata o CSR para a API (com quebras de linha reais)
        csr_encoded = self._format_csr_for_api(csr_path)
        
        # 5. Timestamps
        now = int(time.time())
        not_after = now + (validity_days * 24 * 60 * 60)
        
        # 6. CONSTRUÇÃO DO PAYLOAD - IDÊNTICO AO TESTE MANUAL
        payload = {
            "validity": {
                "not_before": now,
                "not_after": not_after
            },
            "subject_dn": {
                "common_name": csr_cn
            },
            "san": {
                "dns_names": csr_sans.get('dns_names', [csr_cn])
            },
            "signature": {
                "hash_algorithm": "SHA-256"
            },
            "public_key": csr_encoded
        }
        
        # 7. Log do payload (verbose)
        if os.getenv('VERBOSE'):
            logger.info(f"📦 [ISSUE] Product: {product}, Validity: {validity_days}d")
            logger.info(f"📦 [PAYLOAD] {json.dumps(payload, indent=2)}")
        
        # 8. Faz a requisição POST
        client = self._get_client()
        response = client.request('POST', '/certificates', json=payload)
        
        # 9. Extrai o serial da resposta
        serial = self._extract_serial_from_response(response)
        if not serial:
            raise RuntimeError(
                "A requisição foi aceita, mas o serial não foi retornado. "
                "Verifique o header 'Location' na resposta."
            )
        
        logger.info(f"✅ Certificado solicitado. Serial: {serial}")
        
        # 10. Aguarda o certificado ficar pronto
        return self._wait_for_certificate(serial, max_wait)
    
    def issue_async(
        self,
        csr_path: str,
        product: Optional[str] = None,
        validity_days: int = 90,
        ekus: Optional[List[str]] = None
    ) -> str:
        """
        Emite um novo certificado a partir de um CSR (assíncrono).
        
        Retorna o serial imediatamente, sem aguardar a conclusão.
        O usuário deve usar get() ou list_issued() para verificar o status.
        
        Args:
            csr_path: Caminho para o arquivo CSR (.csr ou .pem)
            product: Nome do produto (ex: 'ssl_san5pack')
            validity_days: Dias de validade (máx 90)
            ekus: Ignorado - a política da CA define os EKUs automaticamente (STATIC)
            
        Returns:
            str: Serial do certificado solicitado
            
        Raises:
            ValueError: Se o CSR for inválido
            RuntimeError: Se a API falhar
        """
        # 1. Valida CSR
        if not validate_csr_file(csr_path):
            raise ValueError(f"Arquivo CSR inválido ou inacessível: {csr_path}")
        
        # 2. Extrai informações do CSR
        csr_sans = extract_sans_from_csr(csr_path)
        csr_cn = extract_cn_from_csr(csr_path)
        
        if not csr_cn:
            raise ValueError("Não foi possível extrair o Common Name do CSR")
        
        # 3. Obtém o produto (se não fornecido, usa o padrão do AuthManager)
        if not product:
            if self.auth_manager:
                product = self.auth_manager.get_default_product()
            else:
                raise ValueError("Produto não especificado e AuthManager não disponível")
        
        # 4. Formata o CSR para a API (com quebras de linha reais)
        csr_encoded = self._format_csr_for_api(csr_path)
        
        # 5. Timestamps
        now = int(time.time())
        not_after = now + (validity_days * 24 * 60 * 60)
        
        # 6. CONSTRUÇÃO DO PAYLOAD - IDÊNTICO AO TESTE MANUAL
        payload = {
            "validity": {
                "not_before": now,
                "not_after": not_after
            },
            "subject_dn": {
                "common_name": csr_cn
            },
            "san": {
                "dns_names": csr_sans.get('dns_names', [csr_cn])
            },
            "signature": {
                "hash_algorithm": "SHA-256"
            },
            "public_key": csr_encoded
        }
        
        # 7. Log do payload (verbose)
        if os.getenv('VERBOSE'):
            logger.info(f"📦 [ISSUE_ASYNC] Product: {product}, Validity: {validity_days}d")
            logger.info(f"📦 [PAYLOAD] {json.dumps(payload, indent=2)}")
        
        # 8. Faz a requisição POST
        client = self._get_client()
        response = client.request('POST', '/certificates', json=payload)
        
        # 9. Extrai o serial da resposta
        serial = self._extract_serial_from_response(response)
        if not serial:
            raise RuntimeError(
                "A requisição foi aceita, mas o serial não foi retornado. "
                "Verifique o header 'Location' na resposta."
            )
        
        return serial
    
    def get(self, serial: str) -> Certificate:
        """Busca um certificado pelo número serial."""
        if not serial:
            raise ValueError("O parâmetro 'serial' é obrigatório.")
        
        response = self._get_client().request('GET', f'/certificates/{serial}')
        # Passa o serial para o from_api_response() como fallback
        return Certificate.from_api_response(response, serial=serial)
    
    def revoke(self, serial: str, reason: str = "Unspecified") -> bool:
        """Revoga um certificado."""
        if not serial:
            raise ValueError("O parâmetro 'serial' é obrigatório.")
        
        payload = {"revocation_reason": reason.strip()}
        self._get_client().request('PATCH', f'/certificates/{serial}', json=payload)
        return True
    
    def rekey(self, serial: str, csr_path: str) -> Certificate:
        """Executa rekey de um certificado."""
        if not serial:
            raise ValueError("O parâmetro 'serial' é obrigatório.")
        
        if not validate_csr_file(csr_path):
            raise ValueError(f"Arquivo CSR inválido: {csr_path}")
        
        csr_encoded = self._format_csr_for_api(csr_path)
        
        payload = {
            "public_key": csr_encoded,
            "signature": {
                "hash_algorithm": "SHA-256"
            }
        }
        
        response = self._get_client().request('POST', f'/certificates/{serial}/rekey', json=payload)
        new_serial = self._extract_serial_from_response(response)
        
        if not new_serial:
            raise RuntimeError("Falha ao capturar o novo serial após rekey.")
        
        return self.get(new_serial)
    
    def get_trust_chain(self) -> List[str]:
        """
        Retorna a cadeia de confiança da CA.
        
        A API GlobalSign Atlas retorna uma lista de certificados PEM
        diretamente no corpo da resposta.
        
        Returns:
            List[str]: Lista de certificados PEM da cadeia de confiança
        """
        response = self._get_client().request('GET', '/trustchain')
        
        # A API retorna uma lista diretamente
        if isinstance(response, list):
            return response
        
        # Fallback: se for um dict com a chave 'certificates'
        if isinstance(response, dict):
            return response.get('certificates', [])
        
        # Caso inesperado
        return []
    
    def list_issued(self, days: Optional[int] = None, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Lista certificados emitidos nos últimos N dias."""
        max_days = 30
        days = min(days or max_days, max_days)
        
        now = int(time.time())
        from_time = now - (days * 24 * 60 * 60)
        params = {
            'from': from_time,
            'to': now,
            'page': page,
            'per_page': min(per_page, 100)
        }
        response = self._get_client().request('GET', '/stats/issued', params=params)
        return self._normalize_list_response(response)
    
    def list_revoked(self, days: Optional[int] = None, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Lista certificados revogados nos últimos N dias."""
        max_days = 30
        days = min(days or max_days, max_days)
        
        now = int(time.time())
        from_time = now - (days * 24 * 60 * 60)
        params = {
            'from': from_time,
            'to': now,
            'page': page,
            'per_page': min(per_page, 100)
        }
        response = self._get_client().request('GET', '/stats/revoked', params=params)
        return self._normalize_list_response(response)
    
    def list_expiring(self, days: Optional[int] = None, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Lista certificados que expiram nos próximos N dias."""
        max_days = 30
        days = min(days or max_days, max_days)
        
        now = int(time.time())
        to_time = now + (days * 24 * 60 * 60)
        params = {
            'from': now,
            'to': to_time,
            'page': page,
            'per_page': min(per_page, 100)
        }
        response = self._get_client().request('GET', '/stats/expiring', params=params)
        return self._normalize_list_response(response)
    
    def _normalize_list_response(self, response: Any) -> List[Dict[str, Any]]:
        """Normaliza a resposta de listagem da API."""
        if isinstance(response, list):
            return response
        if isinstance(response, dict):
            for key in ['certificates', 'data', 'items', 'claims']:
                if key in response and isinstance(response[key], list):
                    return response[key]
        return []
    
    def format_validation_policy(self) -> str:
        """Formata a política de validação para exibição."""
        try:
            policy = self._get_validation_policy()
        except Exception as e:
            return f"Erro ao obter política: {e}"
        
        lines = ["\n📋 POLÍTICA DE VALIDAÇÃO", "=" * 60]
        
        if 'subject_dn' in policy:
            lines.append("\n📛 Subject DN:")
            for field, rules in policy['subject_dn'].items():
                presence = rules.get('presence', 'unknown')
                format_rules = rules.get('format', '')
                lines.append(f"  • {field}: {presence} {format_rules}")
        
        if 'dns_names' in policy:
            lines.append(f"\n🌐 DNS Names:")
            lines.append(f"  • min: {policy['dns_names'].get('mincount', 0)}")
            lines.append(f"  • max: {policy['dns_names'].get('maxcount', 0)}")
        
        if 'validity' in policy:
            val = policy['validity']
            min_days = val.get('secondsmin', 0) // 86400
            max_days = val.get('secondsmax', 0) // 86400
            lines.append(f"\n⏰ Validade:")
            lines.append(f"  • min: {min_days} dias")
            lines.append(f"  • max: {max_days} dias")
        
        if 'extended_key_usages' in policy:
            eku_policy = policy['extended_key_usages']
            lines.append(f"\n🔑 Extended Key Usages:")
            lines.append(f"  • min: {eku_policy.get('mincount', 0)}")
            lines.append(f"  • max: {eku_policy.get('maxcount', 0)}")
            if 'ekus' in eku_policy:
                allowed = eku_policy['ekus'].get('list', [])
                if allowed:
                    lines.append(f"  • permitidos: {', '.join(allowed)}")
        
        return "\n".join(lines)
    
    # =============================================================
    # SEARCH BY CN
    # =============================================================
    
    def search_by_cn(self, cn_pattern: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Busca certificados emitidos que correspondem a um padrão de CN.
        
        Suporta:
        - Substring: "gruponk" → encontra "www.gruponk.com.br"
        - Wildcard: "*.keysec.com.br" → encontra "www.keysec.com.br"
        - Exato: "www.gruponk.com.br" → encontra exatamente
        
        Args:
            cn_pattern: Padrão do Common Name
            days: Período de busca em dias (padrão: 30)
            
        Returns:
            Lista de certificados que correspondem ao padrão
        """
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        
        issued = self.list_issued(days=days)
        results = []
        
        print(f"🔍 Buscando certificados com CN contendo '{cn_pattern}'...")
        print(f"📊 Verificando {len(issued)} certificados emitidos nos últimos {days} dias...")
        
        for i, item in enumerate(issued):
            serial = item.get('serial_number')
            if not serial:
                continue
            
            if (i + 1) % 5 == 0:
                print(f"  ⏳ Processando {i + 1}/{len(issued)}...")
            
            try:
                cert = self.get(serial)
                cert_pem = cert.certificate
                
                if not cert_pem:
                    continue
                
                # Extrai o CN do certificado PEM
                cert_obj = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
                subject = cert_obj.subject
                cn_attrs = subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
                cn = str(cn_attrs[0].value) if cn_attrs else ''
                
                if not cn:
                    continue
                
                # Verifica se o CN corresponde ao padrão
                if '*' in cn_pattern:
                    if fnmatch.fnmatch(cn.lower(), cn_pattern.lower()):
                        results.append({
                            'serial': serial,
                            'common_name': cn,
                            'not_before': cert.not_before,
                            'not_after': cert.not_after,
                            'status': cert.status.value if hasattr(cert.status, 'value') else cert.status,
                            'certificate': cert.certificate,
                            'raw_data': cert.raw_data
                        })
                else:
                    if cn_pattern.lower() in cn.lower():
                        results.append({
                            'serial': serial,
                            'common_name': cn,
                            'not_before': cert.not_before,
                            'not_after': cert.not_after,
                            'status': cert.status.value if hasattr(cert.status, 'value') else cert.status,
                            'certificate': cert.certificate,
                            'raw_data': cert.raw_data
                        })
                        
            except Exception as e:
                print(f"  ⚠️ Erro ao buscar serial {serial}: {e}")
                continue
        
        print(f"✅ Encontrados {len(results)} certificados correspondentes.")
        return results
    
    # =============================================================
    # PACK CERTIFICATES
    # =============================================================
    
    def _extract_cert_info(self, cert_path: str) -> Dict[str, str]:
        """
        Extrai informações detalhadas de um certificado X.509.
        
        Retorna:
            {
                'common_name': str,
                'sans': str,
                'organization': str,
                'organizational_unit': str,
                'locality': str,
                'state': str,
                'country': str,
                'valid_from': str,
                'valid_to': str,
                'issuer': str,
                'serial': str
            }
        """
        with open(cert_path, 'rb') as f:
            cert = x509.load_pem_x509_certificate(f.read(), default_backend())
        
        # Subject
        subject = cert.subject
        cn = subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
        o = subject.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)
        ou = subject.get_attributes_for_oid(x509.NameOID.ORGANIZATIONAL_UNIT_NAME)
        l = subject.get_attributes_for_oid(x509.NameOID.LOCALITY_NAME)
        st = subject.get_attributes_for_oid(x509.NameOID.STATE_OR_PROVINCE_NAME)
        c = subject.get_attributes_for_oid(x509.NameOID.COUNTRY_NAME)
        
        # SANs
        sans = []
        try:
            san_ext = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            for name in san_ext.value:
                if isinstance(name, x509.DNSName):
                    sans.append(str(name))
        except x509.ExtensionNotFound:
            pass
        
        # Issuer
        issuer = cert.issuer
        issuer_cn = issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
        issuer_o = issuer.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)
        issuer_c = issuer.get_attributes_for_oid(x509.NameOID.COUNTRY_NAME)
        
        issuer_str = []
        if issuer_cn:
            issuer_str.append(f"CN={issuer_cn[0].value}")
        if issuer_o:
            issuer_str.append(f"O={issuer_o[0].value}")
        if issuer_c:
            issuer_str.append(f"C={issuer_c[0].value}")
        
        return {
            'common_name': str(cn[0].value) if cn else 'N/A',
            'sans': ', '.join(sans) if sans else 'N/A',
            'organization': str(o[0].value) if o else 'N/A',
            'organizational_unit': str(ou[0].value) if ou else 'N/A',
            'locality': str(l[0].value) if l else 'N/A',
            'state': str(st[0].value) if st else 'N/A',
            'country': str(c[0].value) if c else 'N/A',
            'valid_from': cert.not_valid_before_utc.strftime('%b %d %H:%M:%S %Y GMT'),
            'valid_to': cert.not_valid_after_utc.strftime('%b %d %H:%M:%S %Y GMT'),
            'issuer': ', '.join(issuer_str) if issuer_str else 'N/A',
            'serial': format(cert.serial_number, 'X').zfill(2)
        }
    
    def pack_certificates(
        self,
        domain_file: str,
        intermediate_file: str,
        root_file: str,
        common_name: Optional[str] = None,
        output_dir: str = "."
    ) -> Dict[str, Any]:
        """
        Empacota certificados para entrega ao cliente.
        
        Gera:
        - domain_<nome>_<data>.crt (arquivo único no diretório)
        - <nome>_certs_<data>.zip (com todos os 15 arquivos)
        
        Args:
            domain_file: Caminho do certificado do domínio
            intermediate_file: Caminho do certificado intermediário
            root_file: Caminho do certificado raiz
            common_name: Nome comum (opcional, extraído do cert se não fornecido)
            output_dir: Diretório de saída
            
        Returns:
            Dict com caminhos dos arquivos gerados
        """
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        import re
        
        # Valida arquivos de entrada
        for file_path, name in [
            (domain_file, "domain"),
            (intermediate_file, "intermediate"),
            (root_file, "root")
        ]:
            if not Path(file_path).exists():
                raise ValueError(f"{name} certificate not found: {file_path}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Extrai CN se não foi fornecido
        if not common_name:
            with open(domain_file, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
                cn = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
                common_name = str(cn[0].value) if cn else "certificate"
        
        date = datetime.now().strftime("%Y%m%d")
        
        # Sanitiza nome
        name = str(common_name).strip()
        if name.startswith('*.'):
            name = 'wc.' + name[2:]
        # www é mantido
        name = re.sub(r'[^a-zA-Z0-9._-]', '_', name)
        
        # =============================================================
        # ARQUIVO ÚNICO NO DIRETÓRIO: domain_<nome>_<data>.crt
        # =============================================================
        domain_out = f"domain_{name}_{date}.crt"
        domain_path = output_path / domain_out
        shutil.copy2(domain_file, domain_path)
        
        # =============================================================
        # CRIA O ZIP COM TODOS OS 15 ARQUIVOS
        # =============================================================
        prefixes = ['domain', 'intermediate', 'root', 'ca_chain', 'fullchain']
        extensions = ['crt', 'pem', 'cer']
        
        zip_name = f"{name}_certs_{date}.zip"
        zip_path = output_path / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for prefix in prefixes:
                for ext in extensions:
                    # Nome do arquivo dentro do ZIP
                    filename = f"{prefix}_{name}_{date}.{ext}"
                    
                    # Conteúdo do arquivo
                    if prefix == 'domain':
                        content = Path(domain_file).read_text(encoding='utf-8')
                    elif prefix == 'intermediate':
                        content = Path(intermediate_file).read_text(encoding='utf-8')
                    elif prefix == 'root':
                        content = Path(root_file).read_text(encoding='utf-8')
                    elif prefix == 'ca_chain':
                        content = Path(intermediate_file).read_text(encoding='utf-8') + Path(root_file).read_text(encoding='utf-8')
                    elif prefix == 'fullchain':
                        content = Path(domain_file).read_text(encoding='utf-8') + Path(intermediate_file).read_text(encoding='utf-8') + Path(root_file).read_text(encoding='utf-8')
                    else:
                        continue
                    
                    # Adiciona ao ZIP
                    zf.writestr(filename, content)
        
        # =============================================================
        # EXTRAI INFORMAÇÕES DO CERTIFICADO
        # =============================================================
        cert_info = self._extract_cert_info(domain_file)
        
        return {
            'dir': str(output_path),
            'zip': str(zip_path),
            'domain_file': str(domain_path),
            'files': {
                'domain_crt': str(domain_path),
                'zip': str(zip_path)
            },
            'common_name': common_name,
            'sanitized_name': name,
            'date': date,
            'cert_info': cert_info
        }
