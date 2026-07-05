#!/usr/bin/env python3
"""
Script para converter credenciais do formato texto para JSON criptografado.
Usa nomes padronizados: mtls.crt, mtls.key, private.pem, public.pem, credentials.enc

Suporta OAEP (SHA-256) para compatibilidade com o formato da GlobalSign.
"""

import argparse
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes


def load_private_key(key_path: Path):
    """Carrega a chave privada RSA do arquivo PEM."""
    with open(key_path, 'rb') as f:
        return serialization.load_pem_private_key(
            f.read(),
            password=None
        )


def load_public_key(key_path: Path):
    """Carrega a chave pública RSA do arquivo PEM."""
    with open(key_path, 'rb') as f:
        return serialization.load_pem_public_key(f.read())


def decrypt_credentials(enc_path: Path, private_key_path: Path) -> dict:
    """
    Descriptografa o arquivo .enc existente para extrair as credenciais.
    Suporta tanto JSON quanto formato texto legado.
    Tenta PKCS1v15 primeiro, depois OAEP como fallback.
    """
    private_key = load_private_key(private_key_path)
    
    with open(enc_path, 'rb') as f:
        encrypted_data = f.read()
    
    decrypted_str = None
    last_error = None
    
    # Tenta PKCS1v15 primeiro
    try:
        decrypted = private_key.decrypt(encrypted_data, padding.PKCS1v15())
        decrypted_str = decrypted.decode('utf-8')
    except Exception as e:
        last_error = e
        # Tenta OAEP com SHA-256
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
        except Exception as e2:
            raise RuntimeError(f"Falha ao descriptografar. PKCS1v15: {e}, OAEP: {e2}")
    
    # Tenta parserar como JSON primeiro
    try:
        return json.loads(decrypted_str)
    except json.JSONDecodeError:
        pass
    
    # Fallback: parserar como texto (formato antigo: key: / secret:)
    lines = decrypted_str.strip().split('\n')
    credentials = {}
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            credentials[key.strip()] = value.strip()
        elif '=' in line:
            key, value = line.split('=', 1)
            credentials[key.strip()] = value.strip()
    
    if 'key' in credentials and 'secret' in credentials:
        return {"api_key": credentials['key'], "api_secret": credentials['secret']}
    elif 'api_key' in credentials and 'api_secret' in credentials:
        return credentials
    else:
        raise ValueError(
            f"Formato inválido no arquivo {enc_path}. "
            f"Esperado 'key:/secret:' ou 'api_key:/api_secret:' ou JSON. "
            f"Recebido: {decrypted_str[:200]}"
        )


def encrypt_credentials(credentials: dict, public_key_path: Path, output_path: Path):
    """
    Criptografa as credenciais em formato JSON usando chave pública RSA.
    Usa OAEP com SHA-256 (formato da GlobalSign).
    """
    public_key = load_public_key(public_key_path)
    
    payload = json.dumps(credentials, indent=2).encode('utf-8')
    encrypted = public_key.encrypt(
        payload,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    with open(output_path, 'wb') as f:
        f.write(encrypted)
    
    print(f"✅ Credenciais criptografadas salvas em: {output_path}")


def convert_product(product_name: str, secrets_base: Path, dry_run: bool = False):
    """Converte as credenciais de um produto específico usando nomes padronizados."""
    
    product_map = {
        'san5pack': 'atlas_san_5pack',
        'test50pack': 'atlas_test_50pack',
    }
    
    folder_name = product_map.get(product_name, product_name)
    product_dir = secrets_base / folder_name
    
    if not product_dir.exists():
        print(f"❌ Diretório não encontrado: {product_dir}")
        return
    
    # Nomes padronizados
    enc_file = product_dir / "credentials.enc"
    private_key_file = product_dir / "private.pem"
    public_key_file = product_dir / "public.pem"
    
    # Fallback: tenta usar os nomes antigos
    if not private_key_file.exists():
        old_private = product_dir / f"{folder_name}_thiago_private-key.pem"
        if old_private.exists():
            private_key_file = old_private
            print(f"ℹ️  Usando chave privada antiga: {old_private.name}")
    
    if not public_key_file.exists():
        old_public = product_dir / f"{folder_name}_thiago_public-key.pem"
        if old_public.exists():
            public_key_file = old_public
            print(f"ℹ️  Usando chave pública antiga: {old_public.name}")
    
    # Verifica se os arquivos existem
    if not private_key_file.exists():
        print(f"❌ Chave privada não encontrada: {private_key_file}")
        return
    
    if not public_key_file.exists():
        print(f"❌ Chave pública não encontrada: {public_key_file}")
        return
    
    if not enc_file.exists():
        print(f"❌ Arquivo .enc não encontrado: {enc_file}")
        return
    
    # Verifica se o arquivo já está no formato JSON
    try:
        private_key = load_private_key(private_key_file)
        with open(enc_file, 'rb') as f:
            encrypted_data = f.read()
        
        # Tenta descriptografar com OAEP (o formato que a GlobalSign usa)
        try:
            decrypted = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            json.loads(decrypted.decode('utf-8'))
            print(f"✅ {enc_file} já está no formato JSON com OAEP. Nada a fazer.")
            return
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            # Não é JSON, precisa converter
            pass
    except Exception:
        pass
    
    if dry_run:
        print(f"🔍 [DRY RUN] Converteria {enc_file} para JSON com OAEP")
        return
    
    try:
        # Descriptografa o arquivo atual
        credentials = decrypt_credentials(enc_file, private_key_file)
        print(f"✅ Credenciais extraídas de {enc_file}")
        
        # Backup do arquivo antigo
        backup_file = product_dir / "credentials.enc.bak"
        if backup_file.exists():
            backup_file = product_dir / f"credentials.enc.bak.{int(Path(backup_file).stat().st_mtime)}"
        enc_file.rename(backup_file)
        print(f"📦 Backup do antigo: {backup_file}")
        
        # Criptografa no novo formato (JSON + OAEP)
        encrypt_credentials(credentials, public_key_file, enc_file)
        
    except Exception as e:
        print(f"❌ Erro ao converter {product_name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Converte credenciais para JSON criptografado com OAEP")
    parser.add_argument(
        '--product',
        help="Nome do produto (san5pack, test50pack)"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help="Converte todos os produtos"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Apenas mostra o que seria feito, sem executar"
    )
    parser.add_argument(
        '--secrets-dir',
        default=os.getenv(
            'ATLAS_SECRETS_DIR',
            str(Path.home() / '.secrets' / 'globalsign-atlas-api')
        ),
        help="Diretório base dos segredos"
    )
    
    args = parser.parse_args()
    secrets_base = Path(args.secrets_dir).expanduser()
    
    if not secrets_base.exists():
        print(f"❌ Diretório de segredos não encontrado: {secrets_base}")
        print("   Use --secrets-dir para especificar o caminho correto")
        return
    
    products_to_convert = []
    if args.product:
        products_to_convert = [args.product]
    elif args.all:
        products_to_convert = ['san5pack', 'test50pack']
    else:
        print("❌ Especifique --product ou --all")
        return
    
    for product in products_to_convert:
        convert_product(product, secrets_base, args.dry_run)


if __name__ == "__main__":
    main()
