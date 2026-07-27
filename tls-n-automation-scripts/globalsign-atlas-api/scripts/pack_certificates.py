#!/usr/bin/env python3
"""
pack_certificates.py - Empacota certificados para entrega ao cliente

Gera 15 arquivos (5 prefixos x 3 extensões):
- domain, intermediate, root, ca_chain, fullchain
- Extensões: .crt, .pem, .cer

Uso como script standalone:
    python scripts/pack_certificates.py \\
        --domain domain.crt \\
        --intermediate intermediate.crt \\
        --root root.crt \\
        --common-name "meudominio.com.br" \\
        --output-dir ./pacotes/

Uso importado:
    from scripts.pack_certificates import pack_certificates
    result = pack_certificates(...)
"""

import argparse
import shutil
import zipfile
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from cryptography import x509
from cryptography.hazmat.backends import default_backend


def extract_cn(cert_path: str) -> str:
    """Extrai o Common Name do certificado."""
    with open(cert_path, 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read(), default_backend())
    cn = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
    if not cn:
        raise ValueError("Certificate has no Common Name")
    return str(cn[0].value)


def sanitize_name(name: str) -> str:
    """
    Sanitiza o nome para uso em arquivos.
    
    - *.dominio.com → wc.dominio.com
    - www.dominio.com → www.dominio.com (mantém)
    - dominio.com → dominio.com (mantém)
    """
    name = str(name).strip()
    
    # Wildcard: *.dominio.com → wc.dominio.com
    if name.startswith('*.'):
        name = 'wc.' + name[2:]
    
    # www é mantido (NÃO removemos)
    
    # Remove caracteres especiais (mantém letras, números, pontos, hífens)
    name = re.sub(r'[^a-zA-Z0-9._-]', '_', name)
    
    return name


def extract_cert_info(cert_path: str) -> Dict[str, str]:
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
    domain_file: str,
    intermediate_file: str,
    root_file: str,
    common_name: Optional[str] = None,
    output_dir: str = "."
) -> Dict[str, Any]:
    """
    Empacota certificados nos formatos solicitados.
    
    Gera 15 arquivos (5 prefixos x 3 extensões):
    - domain, intermediate, root, ca_chain, fullchain
    - Extensões: .crt, .pem, .cer
    
    Args:
        domain_file: Caminho do certificado do domínio
        intermediate_file: Caminho do certificado intermediário
        root_file: Caminho do certificado raiz
        common_name: Nome comum (opcional, extraído do cert se não fornecido)
        output_dir: Diretório de saída
        
    Returns:
        Dict com caminhos dos arquivos gerados e informações do certificado
    """
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
        common_name = extract_cn(domain_file)
    
    date = datetime.now().strftime("%Y%m%d")
    name = sanitize_name(common_name)
    
    # Define os prefixos e extensões
    prefixes = ['domain', 'intermediate', 'root', 'ca_chain', 'fullchain']
    extensions = ['crt', 'pem', 'cer']
    
    # Gera todos os nomes de arquivos (15)
    files = {}
    for prefix in prefixes:
        for ext in extensions:
            key = f"{prefix}_{ext}"
            files[key] = f"{prefix}_{name}_{date}.{ext}"
    
    paths = {k: output_path / v for k, v in files.items()}
    
    # Remove arquivos antigos
    for path in paths.values():
        if path.exists():
            path.unlink()
    
    # =============================================================
    # GERA OS ARQUIVOS .crt (5 arquivos)
    # =============================================================
    
    shutil.copy2(domain_file, paths['domain_crt'])
    shutil.copy2(intermediate_file, paths['intermediate_crt'])
    shutil.copy2(root_file, paths['root_crt'])
    
    # ca_chain.crt (intermediate + root)
    with open(paths['ca_chain_crt'], 'w', encoding='utf-8') as f_out:
        with open(intermediate_file, 'r', encoding='utf-8') as f_in:
            f_out.write(f_in.read())
        with open(root_file, 'r', encoding='utf-8') as f_in:
            f_out.write(f_in.read())
    
    # fullchain.crt (domain + intermediate + root)
    with open(paths['fullchain_crt'], 'w', encoding='utf-8') as f_out:
        with open(domain_file, 'r', encoding='utf-8') as f_in:
            f_out.write(f_in.read())
        with open(intermediate_file, 'r', encoding='utf-8') as f_in:
            f_out.write(f_in.read())
        with open(root_file, 'r', encoding='utf-8') as f_in:
            f_out.write(f_in.read())
    
    # =============================================================
    # GERA OS ARQUIVOS .pem e .cer (cópias dos .crt)
    # =============================================================
    
    for prefix in prefixes:
        shutil.copy2(paths[f'{prefix}_crt'], paths[f'{prefix}_pem'])
        shutil.copy2(paths[f'{prefix}_crt'], paths[f'{prefix}_cer'])
    
    # =============================================================
    # CRIA O ZIP
    # =============================================================
    
    zip_name = f"{name}_certs_{date}.zip"
    zip_path = output_path / zip_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in paths.values():
            if path.exists():
                zf.write(path, path.name)
    
    # Extrai informações do certificado do domínio
    cert_info = extract_cert_info(domain_file)
    
    return {
        'dir': str(output_path),
        'zip': str(zip_path),
        'files': {k: str(v) for k, v in paths.items()},
        'common_name': common_name,
        'sanitized_name': name,
        'date': date,
        'cert_info': cert_info
    }


def main():
    parser = argparse.ArgumentParser(
        description="Empacota certificados para entrega ao cliente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s --domain domain.crt --intermediate intermediate.crt --root root.crt
  %(prog)s --domain domain.crt --intermediate intermediate.crt --root root.crt --common-name "meudominio.com.br"
  %(prog)s --domain domain.crt --intermediate intermediate.crt --root root.crt --output-dir ./pacotes/
"""
    )
    parser.add_argument('--domain', required=True, help='Certificado do domínio')
    parser.add_argument('--intermediate', required=True, help='Certificado intermediário')
    parser.add_argument('--root', required=True, help='Certificado raiz')
    parser.add_argument('--common-name', help='Nome comum (opcional)')
    parser.add_argument('--output-dir', '-o', default='.', help='Diretório de saída')
    
    args = parser.parse_args()
    
    try:
        result = pack_certificates(
            domain_file=args.domain,
            intermediate_file=args.intermediate,
            root_file=args.root,
            common_name=args.common_name,
            output_dir=args.output_dir
        )
        
        info = result['cert_info']
        
        print("\n✅ Pacote criado com sucesso!")
        print(f"  • Common Name: {result['common_name']}")
        print(f"  • Data: {result['date']}")
        print(f"  • ZIP: {result['zip']}")
        print(f"\n📦 Arquivos gerados (15 arquivos):")
        for key, path in sorted(result['files'].items()):
            print(f"  • {key}: {path}")
        
        print(f"\n📋 Dados do Certificado do Domínio:")
        print(f"  • Nome Comum: {info['common_name']}")
        print(f"  • Nomes Alternativos (SANs): {info['sans']}")
        print(f"  • Organização: {info['organization']}")
        print(f"  • Unidade Organizacional: {info['organizational_unit']}")
        print(f"  • Cidade: {info['locality']}")
        print(f"  • Estado: {info['state']}")
        print(f"  • Pais: {info['country']}")
        print(f"  • Valido a partir de: {info['valid_from']}")
        print(f"  • Valido até: {info['valid_to']}")
        print(f"  • Emissor: {info['issuer']}")
        print(f"  • Número serial: {info['serial']}")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
