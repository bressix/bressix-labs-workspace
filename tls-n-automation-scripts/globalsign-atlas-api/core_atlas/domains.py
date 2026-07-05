# core_atlas/domains.py
from typing import List, Dict, Any, Optional
from .models import DomainClaim


class DomainsAPI:
    """
    Interface de gerenciamento e validação de domínios na API Atlas.
    
    Gerencia:
    - Criação de claims de domínio
    - Validação via DNS, HTTP, Email
    - Listagem e consulta de claims
    - Renovação e deleção
    """
    
    def __init__(self, auth):
        self.auth = auth
        self.client = auth.get_client()
    
    def _extract_claim_id_from_response(self, response: Dict[str, Any]) -> Optional[str]:
        """Extrai o ID do claim da resposta da API."""
        # Tenta extrair do header Location
        if 'location' in response:
            location = response['location']
            clean_url = location.split('?')[0].rstrip('/')
            return clean_url.split('/')[-1]
        
        # Tenta extrair do corpo
        if 'id' in response:
            return str(response['id'])
        
        if 'claim_id' in response:
            return str(response['claim_id'])
        
        return None
    
    def list_all(self, status: Optional[str] = None) -> List[DomainClaim]:
        """
        Lista todas as reivindicações de domínio cadastradas.
        
        Args:
            status: Filtro de status ('PENDING' ou 'VERIFIED')
            
        Returns:
            List[DomainClaim]: Lista de claims
        """
        params = {}
        if status:
            params['status'] = str(status).upper()
        
        response = self.client.request('GET', '/claims/domains', params=params)
        
        # Normaliza a resposta
        claims_data = []
        if isinstance(response, list):
            claims_data = response
        elif isinstance(response, dict):
            for key in ['claims', 'data', 'items']:
                if key in response and isinstance(response[key], list):
                    claims_data = response[key]
                    break
        
        return [DomainClaim.from_api_response(c) for c in claims_data]
    
    def get_claim(self, claim_id: str) -> DomainClaim:
        """
        Busca metadados detalhados de um claim específico.
        
        Args:
            claim_id: ID do claim
            
        Returns:
            DomainClaim: Claim encontrado
            
        Raises:
            ValueError: Se claim_id for vazio
        """
        if not claim_id:
            raise ValueError("O parâmetro 'claim_id' não pode ser vazio.")
        
        response = self.client.request('GET', f'/claims/domains/{claim_id}')
        return DomainClaim.from_api_response(response)
    
    def create_claim(self, domain: str) -> DomainClaim:
        """
        Cria uma nova ordem de validação para um domínio.
        
        Args:
            domain: Nome do domínio
            
        Returns:
            DomainClaim: Claim criado
            
        Raises:
            RuntimeError: Se a API não retornar um ID válido
        """
        clean_domain = str(domain).strip().lower()
        response = self.client.request('POST', f'/claims/domains/{clean_domain}')
        
        claim_id = self._extract_claim_id_from_response(response)
        
        if not claim_id:
            raise RuntimeError(
                f"Falha crítica: Gateway não retornou um identificador de Claim "
                f"válido para o domínio {clean_domain}"
            )
        
        # Constrói o DomainClaim a partir da resposta
        return DomainClaim(
            claim_id=claim_id,
            domain=clean_domain,
            status='PENDING',
            token=response.get('token'),
            expires_at=response.get('assert_by'),
            raw_data=response
        )
    
    def confirm_dns(self, claim_id: str, domain: str) -> bool:
        """
        Dispara a checagem do token via entrada TXT/CNAME no DNS.
        
        Args:
            claim_id: ID do claim
            domain: Domínio a validar
            
        Returns:
            bool: True se a requisição foi bem-sucedida
        """
        if not claim_id:
            raise ValueError("O parâmetro 'claim_id' não pode ser vazio.")
        
        payload = {"authorization_domain": str(domain).strip().lower()}
        self.client.request('POST', f'/claims/domains/{claim_id}/dns', json=payload)
        return True
    
    def confirm_http(self, claim_id: str, domain: str, scheme: str = "HTTP") -> bool:
        """
        Dispara a checagem do token via arquivo estático exposto em HTTP/.well-known.
        
        Args:
            claim_id: ID do claim
            domain: Domínio a validar
            scheme: Protocolo ('HTTP' ou 'HTTPS')
            
        Returns:
            bool: True se a requisição foi bem-sucedida
        """
        if not claim_id:
            raise ValueError("O parâmetro 'claim_id' não pode ser vazio.")
        
        scheme = str(scheme).upper()
        if scheme not in ['HTTP', 'HTTPS']:
            raise ValueError("O parâmetro 'scheme' deve ser 'HTTP' ou 'HTTPS'.")
        
        payload = {
            "authorization_domain": str(domain).strip().lower(),
            "scheme": scheme
        }
        self.client.request('POST', f'/claims/domains/{claim_id}/http', json=payload)
        return True
    
    def verify_email(self, claim_id: str, email: str) -> bool:
        """
        Envia o e-mail de aprovação para o endereço selecionado.
        
        Args:
            claim_id: ID do claim
            email: Endereço de e-mail para envio do desafio
            
        Returns:
            bool: True se a requisição foi bem-sucedida
        """
        if not claim_id:
            raise ValueError("O parâmetro 'claim_id' não pode ser vazio.")
        if not email:
            raise ValueError("O parâmetro 'email' não pode ser vazio.")
        
        payload = {"email_address": str(email).strip()}
        self.client.request('POST', f'/claims/domains/{claim_id}/email', json=payload)
        return True
    
    def get_approver_emails(self, claim_id: str) -> List[str]:
        """
        Retorna a lista de e-mails autorizados para aprovação do domínio.
        
        Args:
            claim_id: ID do claim
            
        Returns:
            List[str]: Lista de e-mails
        """
        if not claim_id:
            raise ValueError("O parâmetro 'claim_id' não pode ser vazio.")
        
        response = self.client.request('GET', f'/claims/domains/{claim_id}/email')
        
        # Normaliza a resposta
        emails = []
        if isinstance(response, dict):
            for key in ['constructed', 'emails', 'email_addresses']:
                if key in response and isinstance(response[key], list):
                    emails = [str(e).strip() for e in response[key]]
                    break
        elif isinstance(response, list):
            emails = [str(e).strip() for e in response]
        
        return emails
    
    def delete_claim(self, claim_id: str) -> bool:
        """
        Remove o domínio do escopo da API.
        
        Args:
            claim_id: ID do claim
            
        Returns:
            bool: True se a requisição foi bem-sucedida
        """
        if not claim_id:
            raise ValueError("O parâmetro 'claim_id' não pode ser vazio.")
        
        self.client.request('DELETE', f'/claims/domains/{claim_id}')
        return True
    
    def renew_claim(self, claim_id: str) -> DomainClaim:
        """
        Força a reemissão do token de desafio de um claim existente (Reassert).
        
        Args:
            claim_id: ID do claim
            
        Returns:
            DomainClaim: Claim renovado
            
        Raises:
            RuntimeError: Se a API não retornar os dados esperados
        """
        if not claim_id:
            raise ValueError("O parâmetro 'claim_id' não pode ser vazio.")
        
        response = self.client.request('POST', f'/claims/domains/{claim_id}/reassert')
        
        domain = response.get('domain')
        token = response.get('token')
        expires_at = response.get('assert_by')
        
        if not domain:
            raise RuntimeError(
                f"Falha ao renovar claim {claim_id}: resposta da API não contém 'domain'"
            )
        
        return DomainClaim(
            claim_id=claim_id,
            domain=domain,
            status='PENDING',
            token=token,
            expires_at=expires_at,
            raw_data=response
        )
