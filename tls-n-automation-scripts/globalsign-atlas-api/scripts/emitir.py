#!/usr/bin/env python3
# scripts/emitir.py

import argparse
import os
import sys
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

# Injeta o diretório raiz no PATH para importações estáveis do core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core_atlas.auth import AuthManager
from core_atlas.certificates import CertificatesAPI
from core_atlas.utils import Colors, validate_domain, normalize_domain
from core_atlas.models import Certificate


def generate_native_csr(domain: str, output_dir: Path, san_list: list = None) -> tuple[Path, Path]:
    """
    Gera um par de chaves RSA de 2048 bits e um CSR com SANs.
    
    Args:
        domain: Common Name do certificado
        output_dir: Diretório para salvar os arquivos
        san_list: Lista de SANs (DNS names). Se não fornecido, usa o domínio.
    
    Returns:
        tuple[Path, Path]: (caminho do CSR, caminho da chave privada)
    """
    domain_clean = normalize_domain(domain)
    key_path = output_dir / f"{domain_clean}.key"
    csr_path = output_dir / f"{domain_clean}.csr"
    
    print(f"🔑 Gerando chave RSA privada para {domain_clean}...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Salva a chave privada
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    print(f"✍️  Gerando CSR com Common Name e SANs...")
    
    # Construção do Subject
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, domain_clean)
    ])
    
    # Construção do CSR
    csr_builder = x509.CertificateSigningRequestBuilder().subject_name(subject)
    
    # Adiciona SANs (Subject Alternative Names)
    if san_list is None:
        san_list = [domain_clean]
    else:
        # Adiciona o domínio à lista se não estiver presente
        for san in san_list:
            san_clean = normalize_domain(san)
            if san_clean not in san_list:
                san_list.append(san_clean)
    
    # Remove duplicatas
    san_list = list(dict.fromkeys(san_list))
    
    # Cria a extensão SAN
    san_ext = x509.SubjectAlternativeName([
        x509.DNSName(san) for san in san_list
    ])
    csr_builder = csr_builder.add_extension(san_ext, critical=False)
    
    # Assina o CSR
    csr = csr_builder.sign(private_key, hashes.SHA256())
    
    # Salva o CSR
    with open(csr_path, "wb") as f:
        f.write(csr.public_bytes(serialization.Encoding.PEM))
    
    print(f"  • SANs incluídos: {', '.join(san_list)}")
    
    return csr_path, key_path


def main():
    parser = argparse.ArgumentParser(
        description='bressix LABs - Emissor Rápido de Certificados via API Atlas'
    )
    parser.add_argument('domain', help='Domínio alvo para a ordem de emissão')
    parser.add_argument('--csr', '-c', help='Caminho de um CSR existente (Se omitido, gera um novo)')
    parser.add_argument('--san', '-s', nargs='+', help='SANs adicionais (DNS names)')
    parser.add_argument('--days', '-d', type=int, default=30, help='Validade em dias (Default: 30, Max: 90)')
    parser.add_argument('--product', '-p', default=None, help='ID do produto/perfil do YAML (Default: ativo)')
    parser.add_argument('--ekus', '-e', nargs='+', help='Extended Key Usages (ex: serverAuth, clientAuth)')
    parser.add_argument('--output-dir', '-o', default='.', help='Diretório para salvar chaves geradas')
    
    args = parser.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Valida domínio
    if not validate_domain(args.domain):
        print(f"{Colors.RED}❌ Domínio inválido: {args.domain}{Colors.NC}")
        sys.exit(1)
    
    # Inicialização unificada com o core
    manager = AuthManager()
    target_product = args.product if args.product else manager.get_default_product()
    
    try:
        print(f"🔐 Inicializando sessão mTLS para o produto: {Colors.CYAN}{target_product}{Colors.NC}...")
        auth = manager.get_auth(target_product)
        cert_api = CertificatesAPI(auth)
    except Exception as e:
        print(f"{Colors.RED}❌ Falha de autenticação: {e}{Colors.NC}")
        sys.exit(1)
    
    # Tratamento ou geração dinâmica de artefatos criptográficos
    if not args.csr:
        # Gera CSR com SANs
        san_list = [args.domain]
        if args.san:
            san_list.extend(args.san)
        csr_path, key_path = generate_native_csr(args.domain, out_dir, san_list)
        print(f"{Colors.GREEN}✅ Artefatos criptográficos criados com sucesso:{Colors.NC}")
        print(f"  • Chave Privada: {key_path}")
        print(f"  • CSR Gerado:    {csr_path}")
    else:
        csr_path = Path(args.csr)
        if not csr_path.exists():
            print(f"{Colors.RED}❌ Arquivo CSR informado não foi encontrado: {csr_path}{Colors.NC}")
            sys.exit(1)

    try:
        print(f"📡 Despachando requisição de assinatura de chave para a API da GlobalSign...")
        
        # Prepara os EKUs (se fornecidos)
        ekus = None
        if args.ekus:
            ekus = args.ekus
        
        # Chama a API com os parâmetros corretos
        cert = cert_api.issue(
            csr_path=str(csr_path),
            product=target_product,
            validity_days=args.days,
            ekus=ekus
        )
        
        print(f"\n{Colors.GREEN}🏆 CERTIFICADO EMITIDO COM SUCESSO!{Colors.NC}")
        print(f"  • Domínio:       {Colors.BOLD}{args.domain}{Colors.NC}")
        print(f"  • Serial Number: {Colors.CYAN}{cert.serial_number}{Colors.NC}")
        print(f"  • Status:        {cert.status.value if hasattr(cert.status, 'value') else cert.status}")
        
        print(f"\n💡 Utilize a CLI para coletar os binários finais se necessário:")
        print(f"  python bin/atlas_cli.py cert get {cert.serial_number} -o {out_dir / args.domain}.crt")
        
    except Exception as e:
        print(f"{Colors.RED}❌ Falha crítica no processamento de emissão: {e}{Colors.NC}")
        sys.exit(1)


if __name__ == '__main__':
    main()
