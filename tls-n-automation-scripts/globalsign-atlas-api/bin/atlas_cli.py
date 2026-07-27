#!/usr/bin/env python3
# bin/atlas_cli.py

import argparse
import sys
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Injeta o diretório raiz no PATH para importações estáveis do core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core_atlas.auth import AuthManager
from core_atlas.certificates import CertificatesAPI
from core_atlas.domains import DomainsAPI
from core_atlas.utils import (
    Colors, 
    validate_csr_file, 
    extract_cn_from_csr,
    extract_eku_names_from_csr,
    validate_domain,
    normalize_domain
)


# =============================================================
# UTILITÁRIOS
# =============================================================

def format_timestamp(ts):
    """Converte timestamp Unix para data legível."""
    if not ts or ts == 'N/A':
        return 'N/A'
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(ts)


# =============================================================
# FUNÇÕES DE COMANDO
# =============================================================

def get_active_api(args):
    """Inicializa centralizadamente o motor de autenticação baseado nos argumentos da CLI"""
    if args.verbose:
        os.environ['VERBOSE'] = '1'
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
    manager = AuthManager()
    target_product = args.product if args.product else manager.get_default_product()
    
    try:
        auth = manager.get_auth(target_product)
        return auth, target_product, manager
    except Exception as e:
        print(f"{Colors.RED}[-] Erro crítico de inicialização de ambiente: {e}{Colors.NC}")
        sys.exit(1)


def cmd_product(args):
    """Lista metadados e contadores de licenças dos produtos ativos no cluster"""
    auth, product_id, _ = get_active_api(args)
    
    if args.list:
        manager = AuthManager()
        products = manager.list_products()
        print(f"\n{Colors.BLUE}📦 Produtos Mapeados no Workspace:{Colors.NC}")
        print("=" * 60)
        for p in products:
            marker = "➔ " if p['name'] == product_id else "  "
            available = f"{Colors.GREEN}✅ Disponível{Colors.NC}" if p.get('available') else f"{Colors.RED}❌ Indisponível{Colors.NC}"
            print(f"{Colors.GREEN}{marker}{p['name']}{Colors.NC} - {p['description']} [{p['type']}] {available}")
        return

    # Se pedir info (padrão se executado isolado)
    from core_atlas.products import ProductsAPI
    api = ProductsAPI(auth)
    counts = api.get_all_counts()
    
    print(f"\n{Colors.CYAN}📊 Status de Consumo - Produto: {product_id}{Colors.NC}")
    print("=" * 60)
    print(f"  • Certificados Emitidos:  {Colors.GREEN}{counts.get('issued', 0)}{Colors.NC}")
    print(f"  • Certificados Revogados: {Colors.RED}{counts.get('revoked', 0)}{Colors.NC}")
    print(f"  • Certificados Expirando: {Colors.YELLOW}{counts.get('expiring', 0)}{Colors.NC}")


def cmd_domain(args):
    """Gerencia ordens de validação de domínios (Claims)"""
    auth, _, _ = get_active_api(args)
    api = DomainsAPI(auth)
    
    if args.list:
        claims = api.list_all(status=args.status)
        print(f"\n{Colors.BLUE}🌐 Domínios Registados na Conta:{Colors.NC}")
        print("=" * 70)
        for c in claims:
            status_color = Colors.GREEN if c.is_verified else Colors.YELLOW
            print(f"  ID: {c.claim_id} | Domain: {Colors.BOLD}{c.domain}{Colors.NC} | Status: {status_color}{c.status}{Colors.NC}")
        return

    if args.create:
        if not validate_domain(args.create):
            print(f"{Colors.RED}[-] Domínio inválido: {args.create}{Colors.NC}")
            return
        claim = api.create_claim(normalize_domain(args.create))
        print(f"{Colors.GREEN}[+] Claim criada com sucesso!{Colors.NC}")
        print(f"  • ID: {claim.claim_id}\n  • Token: {Colors.CYAN}{claim.token}{Colors.NC}\n  • Validar até: {claim.expires_at_date}")
        return

    claim_id = args.check or args.delete or args.reassert or args.confirm_dns or args.confirm_http or args.send_email
    if not claim_id:
        print(f"{Colors.RED}[-] Erro: Especifique uma ação operacional para o domínio.{Colors.NC}")
        return

    if args.check:
        c = api.get_claim(claim_id)
        print(f"\n{Colors.CYAN}🔎 Detalhes do Claim [{claim_id}]:{Colors.NC}")
        print(f"  • Domínio: {c.domain}\n  • Status: {c.status}\n  • Token: {c.token}")
        if hasattr(c, 'get_approver_emails'):
            emails = api.get_approver_emails(claim_id)
            if emails:
                print(f"  • E-mails autorizados: {', '.join(emails)}")
            
    elif args.delete:
        api.delete_claim(claim_id)
        print(f"{Colors.GREEN}[+] Claim {claim_id} removida do cluster.{Colors.NC}")
        
    elif args.reassert:
        claim = api.renew_claim(claim_id)
        print(f"{Colors.GREEN}[+] Claim renovada. Novo token gerado: {claim.token}{Colors.NC}")
        
    elif args.confirm_dns:
        if not args.domain:
            print(f"{Colors.RED}[-] Parâmetro --domain (-d) é obrigatório para validação DNS.{Colors.NC}")
            return
        if not validate_domain(args.domain):
            print(f"{Colors.RED}[-] Domínio inválido: {args.domain}{Colors.NC}")
            return
        api.confirm_dns(claim_id, normalize_domain(args.domain))
        print(f"{Colors.GREEN}[+] Pedido de verificação DNS enviado para {args.domain}.{Colors.NC}")
        
    elif args.confirm_http:
        if not args.domain:
            print(f"{Colors.RED}[-] Parâmetro --domain (-d) é obrigatório para validação HTTP.{Colors.NC}")
            return
        if not validate_domain(args.domain):
            print(f"{Colors.RED}[-] Domínio inválido: {args.domain}{Colors.NC}")
            return
        api.confirm_http(claim_id, normalize_domain(args.domain))
        print(f"{Colors.GREEN}[+] Pedido de verificação HTTP enviado para {args.domain}.{Colors.NC}")
        
    elif args.send_email:
        if not args.email:
            print(f"{Colors.RED}[-] Parâmetro --email (-e) é obrigatório para validação de e-mail.{Colors.NC}")
            return
        api.verify_email(claim_id, args.email)
        print(f"{Colors.GREEN}[+] E-mail de desafio enviado para {args.email}.{Colors.NC}")


def cmd_pack(args):
    """Empacota certificados para entrega ao cliente."""
    auth, product_id, manager = get_active_api(args)
    api = CertificatesAPI(auth, auth_manager=manager)
    
    # =============================================================
    # MODO 1: Automático (usa serial)
    # =============================================================
    if args.serial:
        try:
            print(f"{Colors.YELLOW}📡 Buscando certificado {args.serial}...{Colors.NC}")
            
            cert = api.get(args.serial)
            if not cert.certificate:
                raise ValueError("Certificado não encontrado ou ainda não emitido")
            
            print(f"{Colors.YELLOW}🔗 Buscando cadeia de confiança...{Colors.NC}")
            chain = api.get_trust_chain()
            
            if len(chain) < 2:
                raise ValueError("Cadeia de confiança incompleta (menos de 2 certificados)")
            
            # Salva arquivos temporários
            temp_dir = Path(args.output) / f"temp_pack_{args.serial}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            domain_file = temp_dir / "domain.crt"
            intermediate_file = temp_dir / "intermediate.crt"
            root_file = temp_dir / "root.crt"
            
            with open(domain_file, 'w', encoding='utf-8') as f:
                f.write(cert.certificate)
            
            if len(chain) == 2:
                with open(intermediate_file, 'w', encoding='utf-8') as f:
                    f.write(chain[0])
                with open(root_file, 'w', encoding='utf-8') as f:
                    f.write(chain[1])
            elif len(chain) > 2:
                with open(intermediate_file, 'w', encoding='utf-8') as f:
                    for cert_pem in chain[:-1]:
                        f.write(cert_pem)
                        f.write('\n')
                with open(root_file, 'w', encoding='utf-8') as f:
                    f.write(chain[-1])
            else:
                raise ValueError("Cadeia de confiança incompleta")
            
            # Extrai CN
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend
            with open(domain_file, 'rb') as f:
                cert_obj = x509.load_pem_x509_certificate(f.read(), default_backend())
                cn = cert_obj.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
                common_name = str(cn[0].value) if cn else args.common_name or f"cert_{args.serial}"
            
            print(f"{Colors.YELLOW}📦 Empacotando certificados...{Colors.NC}")
            result = api.pack_certificates(
                domain_file=str(domain_file),
                intermediate_file=str(intermediate_file),
                root_file=str(root_file),
                common_name=common_name,
                output_dir=args.output or "."
            )
            
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # =============================================================
            # SAÍDA FORMATADA
            # =============================================================
            
            info = result['cert_info']
            
            print(f"\n{Colors.BLUE}╔══════════════════════════════════════════════════════════════╗{Colors.NC}")
            print(f"{Colors.BLUE}║              Pack de Certificados - bressix LABs             ║{Colors.NC}")
            print(f"{Colors.BLUE}╚══════════════════════════════════════════════════════════════╝{Colors.NC}")
            
            print(f"\n{Colors.GREEN}📋 Informações extraídas:{Colors.NC}")
            print(f"  • Common Name: {Colors.CYAN}{info['common_name']}{Colors.NC}")
            print(f"  • SANs: {Colors.CYAN}{info['sans']}{Colors.NC}")
            print(f"  • Data de hoje: {Colors.CYAN}{result['date']}{Colors.NC}")
            
            print(f"\n{Colors.GREEN}📁 Arquivos gerados:{Colors.NC}")
            print(f"  ✅ {Path(result['domain_file']).name}")
            print(f"  ✅ {Path(result['zip']).name}")
            
            print(f"\n{Colors.GREEN}🔍 Validando cadeia de certificados...{Colors.NC}")
            result_verify = subprocess.run(
                ['openssl', 'verify', '-CAfile', str(Path(result['domain_file'])), str(Path(result['domain_file']))],
                capture_output=True,
                text=True
            )
            if result_verify.returncode == 0 and 'OK' in result_verify.stdout:
                print(f"  {Colors.GREEN}✔ Cadeia válida:{Colors.NC} {result_verify.stdout.strip()}")
            else:
                print(f"  {Colors.YELLOW}⚠ Cadeia não verificada{Colors.NC}")
            
            print(f"\n{Colors.GREEN}📦 Compactando certificados em ZIP...{Colors.NC}")
            print(f"  {Colors.GREEN}✅ Pacote criado:{Colors.NC} {result['zip']}")
            
            print(f"\n{Colors.BLUE}╔══════════════════════════════════════════════════════════════╗{Colors.NC}")
            print(f"{Colors.BLUE}║                    RESULTADO FINAL                          ║{Colors.NC}")
            print(f"{Colors.BLUE}╠══════════════════════════════════════════════════════════════╣{Colors.NC}")
            print(f"{Colors.BLUE}║{Colors.NC} Common Name:  {Colors.GREEN}{info['common_name']}{Colors.NC}")
            print(f"{Colors.BLUE}║{Colors.NC} Data:          {Colors.GREEN}{result['date']}{Colors.NC}")
            print(f"{Colors.BLUE}║{Colors.NC} Arquivos:      {Colors.GREEN}1 domínio + 1 ZIP{Colors.NC}")
            print(f"{Colors.BLUE}║{Colors.NC} ZIP:           {Colors.GREEN}{result['zip']}{Colors.NC}")
            print(f"{Colors.BLUE}╠══════════════════════════════════════════════════════════════╣{Colors.NC}")
            print(f"{Colors.BLUE}║{Colors.NC}  Dados do Certificado do Domínio")
            print(f"{Colors.BLUE}║{Colors.NC}  Nome Comum: {info['common_name']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Nomes Alternativos (SANs): {info['sans']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Organização: {info['organization']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Unidade Organizacional: {info['organizational_unit']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Cidade: {info['locality']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Estado: {info['state']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Pais: {info['country']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Valido a partir de: {info['valid_from']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Valido até: {info['valid_to']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Emissor: {info['issuer']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Número serial: {info['serial']}")
            print(f"{Colors.BLUE}╚══════════════════════════════════════════════════════════════╝{Colors.NC}")
            
        except Exception as e:
            print(f"{Colors.RED}[-] Erro ao criar pacote: {e}{Colors.NC}")
            temp_dir = Path(args.output) / f"temp_pack_{args.serial}"
            shutil.rmtree(temp_dir, ignore_errors=True)
        return
    
    # =============================================================
    # MODO 2: Manual (usa arquivos fornecidos)
    # =============================================================
    if args.domain_cert and args.intermediate_cert and args.root_cert:
        try:
            result = api.pack_certificates(
                domain_file=args.domain_cert,
                intermediate_file=args.intermediate_cert,
                root_file=args.root_cert,
                common_name=args.common_name,
                output_dir=args.output or "."
            )
            
            info = result['cert_info']
            
            print(f"\n{Colors.BLUE}╔══════════════════════════════════════════════════════════════╗{Colors.NC}")
            print(f"{Colors.BLUE}║              Pack de Certificados - bressix LABs             ║{Colors.NC}")
            print(f"{Colors.BLUE}╚══════════════════════════════════════════════════════════════╝{Colors.NC}")
            
            print(f"\n{Colors.GREEN}📋 Informações extraídas:{Colors.NC}")
            print(f"  • Common Name: {Colors.CYAN}{info['common_name']}{Colors.NC}")
            print(f"  • SANs: {Colors.CYAN}{info['sans']}{Colors.NC}")
            print(f"  • Data de hoje: {Colors.CYAN}{result['date']}{Colors.NC}")
            
            print(f"\n{Colors.GREEN}📁 Arquivos gerados:{Colors.NC}")
            print(f"  ✅ {Path(result['domain_file']).name}")
            print(f"  ✅ {Path(result['zip']).name}")
            
            print(f"\n{Colors.GREEN}📦 Compactando certificados em ZIP...{Colors.NC}")
            print(f"  {Colors.GREEN}✅ Pacote criado:{Colors.NC} {result['zip']}")
            
            print(f"\n{Colors.BLUE}╔══════════════════════════════════════════════════════════════╗{Colors.NC}")
            print(f"{Colors.BLUE}║                    RESULTADO FINAL                          ║{Colors.NC}")
            print(f"{Colors.BLUE}╠══════════════════════════════════════════════════════════════╣{Colors.NC}")
            print(f"{Colors.BLUE}║{Colors.NC} Common Name:  {Colors.GREEN}{info['common_name']}{Colors.NC}")
            print(f"{Colors.BLUE}║{Colors.NC} Data:          {Colors.GREEN}{result['date']}{Colors.NC}")
            print(f"{Colors.BLUE}║{Colors.NC} Arquivos:      {Colors.GREEN}1 domínio + 1 ZIP{Colors.NC}")
            print(f"{Colors.BLUE}║{Colors.NC} ZIP:           {Colors.GREEN}{result['zip']}{Colors.NC}")
            print(f"{Colors.BLUE}╠══════════════════════════════════════════════════════════════╣{Colors.NC}")
            print(f"{Colors.BLUE}║{Colors.NC}  Dados do Certificado do Domínio")
            print(f"{Colors.BLUE}║{Colors.NC}  Nome Comum: {info['common_name']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Nomes Alternativos (SANs): {info['sans']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Organização: {info['organization']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Unidade Organizacional: {info['organizational_unit']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Cidade: {info['locality']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Estado: {info['state']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Pais: {info['country']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Valido a partir de: {info['valid_from']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Valido até: {info['valid_to']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Emissor: {info['issuer']}")
            print(f"{Colors.BLUE}║{Colors.NC}  Número serial: {info['serial']}")
            print(f"{Colors.BLUE}╚══════════════════════════════════════════════════════════════╝{Colors.NC}")
            
        except Exception as e:
            print(f"{Colors.RED}[-] Erro ao criar pacote: {e}{Colors.NC}")
        return
    
    # =============================================================
    # Nenhum modo selecionado
    # =============================================================
    print(f"{Colors.RED}[-] Para --pack, informe --serial <SERIAL> ou os três certificados.{Colors.NC}")
    print(f"{Colors.YELLOW}  Modo automático:  --pack --serial 12345{Colors.NC}")
    print(f"{Colors.YELLOW}  Modo manual:     --pack --domain-cert x --intermediate-cert y --root-cert z{Colors.NC}")


def cmd_cert(args):
    """Gerencia ciclo de vida, emissão e revogação de certificados TLS"""
    auth, product_id, manager = get_active_api(args)
    api = CertificatesAPI(auth, auth_manager=manager)
    
    if args.policy:
        print(api.format_validation_policy())
        return

    if args.trustchain:
        try:
            chain = api.get_trust_chain()
            print(f"\n{Colors.GREEN}🔗 Cadeia de Confiança (Trust Chain):{Colors.NC}")
            print("=" * 80)
            for i, cert in enumerate(chain, 1):
                print(f"\n{Colors.CYAN}📜 Certificado {i}:{Colors.NC}")
                lines = cert.split('\n')
                print('\n'.join(lines[:3]))
                print(f"  ... ({len(lines) - 5} linhas omitidas) ...")
                print('\n'.join(lines[-2:]))
                print(f"  📏 Tamanho: {len(cert)} caracteres")
            if not chain:
                print(f"{Colors.YELLOW}[!] Nenhum certificado na cadeia de confiança.{Colors.NC}")
        except Exception as e:
            print(f"{Colors.RED}[-] Erro ao buscar trust chain: {e}{Colors.NC}")
        return

    if args.pack:
        cmd_pack(args)
        return

    if args.search_cn:
        try:
            results = api.search_by_cn(args.search_cn, days=args.days or 30)
            
            if not results:
                print(f"\n{Colors.YELLOW}🔍 Nenhum certificado encontrado com CN contendo '{args.search_cn}'{Colors.NC}")
                return
            
            print(f"\n{Colors.GREEN}🔍 Certificados encontrados com CN contendo '{args.search_cn}':{Colors.NC}")
            print("=" * 80)
            
            for cert in results:
                status_color = Colors.GREEN if cert['status'] == 'ISSUED' else Colors.YELLOW
                print(f"  Serial: {Colors.CYAN}{cert['serial']}{Colors.NC}")
                print(f"  CN:     {Colors.BOLD}{cert['common_name']}{Colors.NC}")
                print(f"  Status: {status_color}{cert['status']}{Colors.NC}")
                print(f"  Expira: {format_timestamp(cert['not_after'])}")
                print("-" * 40)
                
        except Exception as e:
            print(f"{Colors.RED}[-] Erro na busca: {e}{Colors.NC}")
        return

    if args.issue:
        if not args.csr:
            print(f"{Colors.RED}[-] Arquivo CSR (--csr) é mandatório para emissões.{Colors.NC}")
            return
        
        if not validate_csr_file(args.csr):
            print(f"{Colors.RED}[-] Arquivo CSR inválido ou corrompido: {args.csr}{Colors.NC}")
            return
        
        cn = extract_cn_from_csr(args.csr)
        if cn:
            print(f"📡 Processando emissão para o CN detectado: {Colors.BOLD}{cn}{Colors.NC}...")
        else:
            print(f"{Colors.YELLOW}[!] Não foi possível extrair o CN do CSR.{Colors.NC}")
        
        # Extrai EKUs para informação, mas NÃO envia (política é STATIC)
        csr_ekus = extract_eku_names_from_csr(args.csr)
        if csr_ekus:
            print(f"  • EKUs detectados no CSR: {', '.join(csr_ekus)}")
            print(f"  • A política da CA definirá os EKUs automaticamente (STATIC)")
        else:
            print(f"  • Nenhum EKU detectado no CSR. A política da CA definirá os EKUs automaticamente.")
        
        try:
            # MODO ASSÍNCRONO É O PADRÃO
            if args.wait:
                # Modo síncrono (polling) - aguarda o certificado
                print(f"⏳ Aguardando emissão... (até {args.wait}s)")
                cert = api.issue(
                    csr_path=args.csr,
                    product=product_id,
                    validity_days=args.days,
                    max_wait=args.wait
                )
                
                print(f"\n{Colors.GREEN}[+] Certificado gerado com sucesso!{Colors.NC}")
                print(f"  • Serial Number: {Colors.CYAN}{cert.serial_number}{Colors.NC}")
                
                # Mostra status e datas se disponíveis
                status_value = cert.status.value if hasattr(cert.status, 'value') else cert.status
                print(f"  • Status: {status_value if status_value else 'ISSUED'}")
                print(f"  • Válido de: {cert.not_before if cert.not_before else 'N/A'}")
                print(f"  • Válido até: {cert.not_after if cert.not_after else 'N/A'}")
                
                if args.output:
                    out_path = Path(args.output)
                    if cert.certificate:
                        with open(out_path, 'w', encoding='utf-8') as f:
                            f.write(cert.certificate)
                        print(f"{Colors.BLUE}[+] Binário CRT salvo em: {out_path}{Colors.NC}")
                    else:
                        print(f"{Colors.YELLOW}[!] O certificado não contém o binário CRT.{Colors.NC}")
            else:
                # MODO ASSÍNCRONO (PADRÃO) - retorna o serial imediatamente
                serial = api.issue_async(
                    csr_path=args.csr,
                    product=product_id,
                    validity_days=args.days
                )
                
                print(f"\n{Colors.GREEN}[+] Certificado solicitado!{Colors.NC}")
                print(f"  • Serial Number: {Colors.CYAN}{serial}{Colors.NC}")
                print(f"  • Status: {Colors.YELLOW}PENDING (em processamento){Colors.NC}")
                print(f"\n{Colors.BLUE}💡 Para verificar o status:{Colors.NC}")
                print(f"  atlas_cli.py cert --get {serial}")
                if args.output:
                    print(f"  atlas_cli.py cert --get {serial} --output {args.output}")
                
        except Exception as e:
            print(f"{Colors.RED}[-] Falha na emissão: {e}{Colors.NC}")
            sys.exit(1)
        return

    if args.get:
        try:
            cert = api.get(args.get)
            print(f"\n{Colors.GREEN}📜 Certificado Encontrado [{args.get}]:{Colors.NC}")
            status_value = cert.status.value if hasattr(cert.status, 'value') else cert.status
            print(f"  • Status: {status_value if status_value else 'UNKNOWN'}")
            print(f"  • Válido de: {cert.not_before if cert.not_before else 'N/A'}")
            print(f"  • Válido até: {cert.not_after if cert.not_after else 'N/A'}")
            if args.output:
                out_path = Path(args.output)
                if cert.certificate:
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(cert.certificate)
                    print(f"{Colors.BLUE}[+] Binário CRT salvo em: {out_path}{Colors.NC}")
                else:
                    print(f"{Colors.YELLOW}[!] O certificado não contém o binário CRT.{Colors.NC}")
        except Exception as e:
            print(f"{Colors.RED}[-] Erro ao buscar certificado: {e}{Colors.NC}")
        return

    if args.revoke:
        if not args.reason:
            print(f"{Colors.RED}[-] Parâmetro --reason é obrigatório para revogações.{Colors.NC}")
            return
        try:
            api.revoke(args.revoke, args.reason)
            print(f"{Colors.GREEN}[+] Certificado {args.revoke} revogado com sucesso. Motivo: {args.reason}{Colors.NC}")
        except Exception as e:
            print(f"{Colors.RED}[-] Falha na revogação: {e}{Colors.NC}")
        return

    if args.rekey:
        if not args.csr:
            print(f"{Colors.RED}[-] Novo arquivo CSR (--csr) é mandatório para processo de Rekey.{Colors.NC}")
            return
        if not validate_csr_file(args.csr):
            print(f"{Colors.RED}[-] Arquivo CSR inválido ou corrompido: {args.csr}{Colors.NC}")
            return
        
        print(f"📡 Disparando processo de Rekey para o serial: {args.rekey}...")
        try:
            new_cert = api.rekey(args.rekey, args.csr)
            print(f"{Colors.GREEN}[+] Rekey concluído!{Colors.NC}")
            print(f"  • Novo Serial: {Colors.CYAN}{new_cert.serial_number}{Colors.NC}")
            status_value = new_cert.status.value if hasattr(new_cert.status, 'value') else new_cert.status
            print(f"  • Status: {status_value if status_value else 'UNKNOWN'}")
            if args.output:
                out_path = Path(args.output)
                if new_cert.certificate:
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(new_cert.certificate)
                    print(f"{Colors.BLUE}[+] Binário CRT salvo em: {out_path}{Colors.NC}")
                else:
                    print(f"{Colors.YELLOW}[!] O certificado não contém o binário CRT.{Colors.NC}")
        except Exception as e:
            print(f"{Colors.RED}[-] Falha no Rekey: {e}{Colors.NC}")
            sys.exit(1)
        return

    if args.list_issued:
        try:
            res = api.list_issued(days=args.days)
            # Inverte para mostrar os mais recentes primeiro
            res = list(reversed(res))
            
            # Limite de exibição: 20 por padrão, todos se --all
            display_limit = None if args.all else 20
            
            print(f"\n{Colors.BLUE}📜 Últimos Certificados Emitidos (Janela: {args.days} dias):{Colors.NC}")
            print("=" * 80)
            
            if display_limit:
                items = res[:display_limit]
            else:
                items = res
            
            for r in items:
                serial = r.get('serial_number', 'N/A')
                issued = format_timestamp(r.get('not_before'))
                expires = format_timestamp(r.get('not_after'))
                print(f"  Serial: {serial} | Emitido: {issued} | Expira: {expires}")
            
            if display_limit and len(res) > display_limit:
                print(f"  ... e mais {len(res) - display_limit} resultados. Use --all para ver todos.")
            
        except Exception as e:
            print(f"{Colors.RED}[-] Erro ao listar emitidos: {e}{Colors.NC}")
            
    elif args.list_revoked:
        try:
            res = api.list_revoked(days=args.days)
            # Inverte para mostrar os mais recentes primeiro
            res = list(reversed(res))
            
            # Limite de exibição: 20 por padrão, todos se --all
            display_limit = None if args.all else 20
            
            print(f"\n{Colors.RED}❌ Certificados Revogados na Janela ({args.days} dias):{Colors.NC}")
            print("=" * 80)
            
            if display_limit:
                items = res[:display_limit]
            else:
                items = res
            
            for r in items:
                serial = r.get('serial_number', 'N/A')
                reason = r.get('revocation_reason', 'N/A')
                print(f"  Serial: {serial} | Motivo: {reason}")
            
            if display_limit and len(res) > display_limit:
                print(f"  ... e mais {len(res) - display_limit} resultados. Use --all para ver todos.")
            
        except Exception as e:
            print(f"{Colors.RED}[-] Erro ao listar revogados: {e}{Colors.NC}")


# =============================================================
# MAIN
# =============================================================

def main():
    parser = argparse.ArgumentParser(
        description=f"""{Colors.BOLD}{Colors.CYAN}⚙️ bressix LABs - GlobalSign Atlas Automation Engine{Colors.NC}

Gerencia certificados TLS/mTLS via API GlobalSign Atlas.

┌─────────────────────────────────────────────────────────────────────────────┐
│  FLUXO DE TRABALHO RECOMENDADO                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Listar produtos disponíveis  →  atlas_cli.py product --list            │
│  2. Solicitar certificado        →  atlas_cli.py cert --issue --csr ...   │
│  3. Verificar status             →  atlas_cli.py cert --get <SERIAL>      │
│  4. Baixar certificado           →  atlas_cli.py cert --get <SERIAL> -o   │
│  5. Listar emitidos              →  atlas_cli.py cert --list-issued        │
│  6. Buscar por CN                →  atlas_cli.py cert --search-cn <CN>     │
│  7. Rekey (renovar chave)        →  atlas_cli.py cert --rekey <SERIAL>    │
│  8. Revogar certificado          →  atlas_cli.py cert --revoke <SERIAL>   │
└─────────────────────────────────────────────────────────────────────────────┘
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
╔═══════════════════════════════════════════════════════════════════════════════╗
║ 📘 EXEMPLOS DE USO                                                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

  🔹 PRODUTOS
  ────────────────────────────────────────────────────────────────────────────────
  atlas_cli.py product --list
      Lista todos os produtos disponíveis no workspace

  atlas_cli.py product
      Mostra status de consumo do produto ativo

  🔹 CERTIFICADOS (use o subcomando 'cert')
  ────────────────────────────────────────────────────────────────────────────────
  atlas_cli.py cert --trustchain
      Exibe a cadeia de confiança da CA

  atlas_cli.py cert --policy
      Exibe a política de validação da CA

  atlas_cli.py cert --issue --csr /path/to/meu.csr
      Solicita um certificado (retorna o serial imediatamente)

  atlas_cli.py cert --issue --csr /path/to/meu.csr --wait 60
      Solicita e aguarda o certificado ficar pronto (polling)

  atlas_cli.py cert --get 12345 --output certificado.crt
      Busca um certificado pelo serial e salva

  atlas_cli.py cert --list-issued --days 30
      Lista certificados emitidos nos últimos 30 dias

  atlas_cli.py cert --list-issued --days 30 --all
      Lista TODOS os certificados emitidos nos últimos 30 dias

  atlas_cli.py cert --list-revoked --days 30
      Lista certificados revogados nos últimos 30 dias

  atlas_cli.py cert --list-revoked --days 30 --all
      Lista TODOS os certificados revogados nos últimos 30 dias

  atlas_cli.py cert --search-cn "gruponk" --days 30
      Busca certificados por substring no Common Name (case-insensitive)

  atlas_cli.py cert --search-cn "*.keysec.com.br" --days 30
      Busca certificados por wildcard no Common Name

  atlas_cli.py cert --revoke 12345 --reason "Chave comprometida"
      Revoga um certificado

  atlas_cli.py cert --rekey 12345 --csr /path/to/novo.csr
      Executa rekey de um certificado

  atlas_cli.py cert --pack --serial 12345
      Empacota certificados para entrega ao cliente (automático)

  atlas_cli.py cert --pack --serial 12345 --output /caminho/para/pasta
      Empacota certificados e salva em um diretório específico

  atlas_cli.py cert --pack --domain-cert domain.crt --intermediate-cert intermediate.crt --root-cert root.crt
      Empacota certificados para entrega ao cliente (manual)

  🔹 DOMÍNIOS (use o subcomando 'domain')
  ────────────────────────────────────────────────────────────────────────────────
  atlas_cli.py domain --list
      Lista todos os domínios validados na conta

  atlas_cli.py domain --create meudominio.com
      Cria uma nova claim de domínio

  atlas_cli.py domain --check CLAIM_ID
      Verifica detalhes de uma claim específica

  atlas_cli.py domain --confirm-dns CLAIM_ID --domain meudominio.com
      Confirma validação de domínio via DNS TXT

  atlas_cli.py domain --delete CLAIM_ID
      Remove uma claim de domínio

  🔹 PRODUTO ESPECÍFICO
  ────────────────────────────────────────────────────────────────────────────────
  atlas_cli.py --product ssl_san5pack cert --issue --csr /path/to/meu.csr
      Usa um produto específico para emissão
"""
    )
    
    # Opções globais
    parser.add_argument('--product', '-p', default=None, 
                        help='Força um produto específico mapeado no YAML')
    parser.add_argument('--verbose', '-v', action='store_true', 
                        help='Modo de depuração de rede verboso')
    
    subparsers = parser.add_subparsers(dest='command', required=True,
                                        help='Subcomandos disponíveis')
    
    # ======================================================================
    # Subcomando: product
    # ======================================================================
    p_prod = subparsers.add_parser(
        'product',
        help='Status e contadores de licenças',
        description='Gerencia produtos e exibe status de consumo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  atlas_cli.py product --list     # Lista produtos disponíveis
  atlas_cli.py product            # Mostra status de consumo do produto ativo
"""
    )
    p_prod.add_argument('--list', action='store_true', 
                        help='Listar produtos configurados no sistema')
    p_prod.set_defaults(func=cmd_product)
    
    # ======================================================================
    # Subcomando: domain
    # ======================================================================
    p_dom = subparsers.add_parser(
        'domain',
        help='Gerenciamento de validação de domínios (Claims)',
        description='Gerencia claims de domínio para validação antes da emissão',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  atlas_cli.py domain --list
  atlas_cli.py domain --create meudominio.com
  atlas_cli.py domain --check CLAIM_ID
  atlas_cli.py domain --confirm-dns CLAIM_ID --domain meudominio.com
"""
    )
    p_dom.add_argument('--list', action='store_true', help='Listar claims cadastrados')
    p_dom.add_argument('--status', choices=['PENDING', 'VERIFIED'], 
                        help='Filtro de estado para listagem')
    p_dom.add_argument('--create', metavar='DOMAIN', 
                        help='Criar uma nova reivindicação de domínio')
    p_dom.add_argument('--check', metavar='CLAIM_ID', 
                        help='Ver metadados de uma claim ativa')
    p_dom.add_argument('--confirm-dns', metavar='CLAIM_ID', 
                        help='Disparar checagem via DNS TXT')
    p_dom.add_argument('--confirm-http', metavar='CLAIM_ID', 
                        help='Disparar checagem via arquivo HTTP')
    p_dom.add_argument('--send-email', metavar='CLAIM_ID', 
                        help='Enviar e-mail de desafio')
    p_dom.add_argument('--domain', '-d', 
                        help='Nome do domínio (requerido para confirmações de transporte)')
    p_dom.add_argument('--email', '-e', 
                        help='Endereço de e-mail (requerido para send-email)')
    p_dom.add_argument('--delete', metavar='CLAIM_ID', 
                        help='Deletar uma claim')
    p_dom.add_argument('--reassert', metavar='CLAIM_ID', 
                        help='Forçar renovação/reemissão de token expirado')
    p_dom.set_defaults(func=cmd_domain)
    
    # ======================================================================
    # Subcomando: cert
    # ======================================================================
    p_cert = subparsers.add_parser(
        'cert',
        help='Ciclo de vida e emissão de certificados TLS',
        description='Gerencia o ciclo de vida completo de certificados TLS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Cadeia de Confiança
  atlas_cli.py cert --trustchain

  # Política
  atlas_cli.py cert --policy

  # Emissão Assíncrona (PADRÃO)
  atlas_cli.py cert --issue --csr /path/to/meu.csr

  # Emissão com Polling
  atlas_cli.py cert --issue --csr /path/to/meu.csr --wait 60

  # Consulta
  atlas_cli.py cert --get 12345 --output certificado.crt

  # Revogação
  atlas_cli.py cert --revoke 12345 --reason "Chave comprometida"

  # Rekey
  atlas_cli.py cert --rekey 12345 --csr /path/to/novo.csr

  # Empacotamento (automático)
  atlas_cli.py cert --pack --serial 12345
  atlas_cli.py cert --pack --serial 12345 --output /caminho/para/pasta

  # Empacotamento (manual)
  atlas_cli.py cert --pack --domain-cert domain.crt --intermediate-cert intermediate.crt --root-cert root.crt

  # Listagens (com limite de 20)
  atlas_cli.py cert --list-issued --days 30
  atlas_cli.py cert --list-revoked --days 30

  # Listagens (todos os resultados)
  atlas_cli.py cert --list-issued --days 30 --all
  atlas_cli.py cert --list-revoked --days 30 --all

  # Busca por CN (substring ou wildcard)
  atlas_cli.py cert --search-cn "gruponk" --days 30
  atlas_cli.py cert --search-cn "*.keysec.com.br" --days 30
"""
    )
    p_cert.add_argument('--policy', action='store_true', 
                        help='Exibir políticas restritivas do CA')
    p_cert.add_argument('--trustchain', action='store_true',
                        help='Exibir a cadeia de confiança da CA')
    p_cert.add_argument('--issue', action='store_true', 
                        help='Solicitar um novo certificado (modo assíncrono)')
    p_cert.add_argument('--csr', 
                        help='Caminho local do ficheiro CSR (.csr / .pem)')
    p_cert.add_argument('--days', type=int, default=30, 
                        help='Dias de validade da ordem (Default: 30, Max: 90)')
    p_cert.add_argument('--wait', type=int, default=0,
                        help='Aguarda o certificado ficar pronto (polling). Ex: --wait 60')
    p_cert.add_argument('--get', metavar='SERIAL', 
                        help='Coletar binários de um certificado existente')
    p_cert.add_argument('--output', '-o', 
                        help='Diretório de saída para arquivos (certificados, pacotes, etc.)')
    p_cert.add_argument('--pack', action='store_true',
                        help='Empacota certificados para entrega ao cliente')
    p_cert.add_argument('--serial', help='Serial do certificado (modo automático)')
    p_cert.add_argument('--domain-cert', help='Certificado do domínio (modo manual)')
    p_cert.add_argument('--intermediate-cert', help='Certificado intermediário (modo manual)')
    p_cert.add_argument('--root-cert', help='Certificado raiz (modo manual)')
    p_cert.add_argument('--common-name', help='Nome comum para nomear os arquivos (opcional)')
    p_cert.add_argument('--search-cn', metavar='PATTERN',
                        help='Busca certificados por Common Name (suporta substring ou wildcards como *.dominio.com)')
    p_cert.add_argument('--all', action='store_true',
                        help='Lista todos os resultados (sem limite de 20)')
    p_cert.add_argument('--revoke', metavar='SERIAL', 
                        help='Revogar credencial no cluster')
    p_cert.add_argument('--reason', 
                        help='Motivo da revogação (Mandatório para a ação --revoke)')
    p_cert.add_argument('--rekey', metavar='SERIAL', 
                        help='Executar Rekey mantendo a identidade original')
    p_cert.add_argument('--list-issued', action='store_true', 
                        help='Listar emissões recentes')
    p_cert.add_argument('--list-revoked', action='store_true', 
                        help='Listar revogações recentes')
    p_cert.set_defaults(func=cmd_cert)
    
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
