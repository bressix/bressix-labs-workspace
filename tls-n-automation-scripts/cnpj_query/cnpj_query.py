#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================================
#
#  +-+ +-+ +-+ +-+ +-+ +-+ +-+   +-+ +-+ +-+ +-+
#  |b| |r| |e| |s| |s| |i| |x|   |L| |A| |B| |s|
#  +-+ +-+ +-+ +-+ +-+ +-+ +-+   +-+ +-+ +-+ +-+
#                                                                                                        
# ==============================================================================
#  Project: bressix-labs-workspace
#  File: cnpj_query.py
#  Description: Consultador de CNPJ resiliente com validação local,
#               mecanismo de fallback inteligente e suporte a lote.
#
#  Copyright (C) 2026 bressix LABs <https://github.com/bressix>
#  License: GNU GPL v3.0
#
#  SECURITY WARNING: Never hardcode private keys or active API tokens.
# ==============================================================================

import json
import sys
import urllib.request
import urllib.error
import time
import random

# ==================== CONFIGURAÇÕES ====================
USER_AGENT = "BressixLabCNPJQuery/1.0 (Contato: https://github.com/bressix)"
DELAY_ENTRE_REQUISICOES = 1
MAX_TENTATIVAS = 3
TIMEOUT = 10


def mostrar_help():
    """Exibe ajuda do script"""
    print("""
CONSULTADOR DE CNPJ

USO:
  ./cnpj_query.py <CNPJ>                    # Consulta única
  ./cnpj_query.py --lote <arquivo.txt>      # Consulta em lote
  ./cnpj_query.py --lote <arquivo.txt> --json <saida.json>  # Lote com JSON
  ./cnpj_query.py --help                    # Exibe esta ajuda

EXEMPLOS:
  # Consulta única (aceita formatos com ou sem pontuação)
  ./cnpj_query.py 53020152000112
  ./cnpj_query.py 53.020.152/0001-12

  # Consulta em lote
  ./cnpj_query.py --lote cnpjs.txt

  # Lote salvando resultados em JSON
  ./cnpj_query.py --lote cnpjs.txt --json resultados.json

FORMATO DO ARQUIVO (cnpjs.txt):
  Um CNPJ por linha, com ou sem pontuação:
   
    53020152000112
    12.345.678/0001-99

CARACTERÍSTICAS:
  - Validação matemática local de dígitos verificadores antes de usar a rede
  - User-Agent personalizado para evitar bloqueios e cumprir boas práticas
  - Delay de 1s entre consultas no modo lote (evita rate limit)
  - Retry automático com backoff exponencial para erro 429
  - Interrupção imediata em erros estruturais (HTTP 400/404)
  - Fallback e mesclagem inteligente entre APIs (MinhaReceita + PublicaCNPJ)
""")
    sys.exit(0)


# ==================== FUNÇÃO DE VALIDAÇÃO LOCAL ====================
def cnpj_valido(cnpj: str) -> bool:
    """Valida matematicamente o dígito verificador de um CNPJ de forma local"""
    cnpj = "".join(filter(str.isdigit, cnpj))

    if len(cnpj) != 14:
        return False

    if cnpj in [str(i) * 14 for i in range(10)]:
        return False

    # Validação do primeiro dígito verificador (13º dígito)
    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma_1 = sum(int(digito) * peso for digito, peso in zip(cnpj[:12], pesos_1))
    resto_1 = soma_1 % 11
    digito_1 = 0 if resto_1 < 2 else 11 - resto_1

    if int(cnpj[12]) != digito_1:
        return False

    # Validação do segundo dígito verificador (14º dígito)
    pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma_2 = sum(int(digito) * peso for digito, peso in zip(cnpj[:13], pesos_2))
    resto_2 = soma_2 % 11
    digito_2 = 0 if resto_2 < 2 else 11 - resto_2

    if int(cnpj[13]) != digito_2:
        return False

    return True


# ==================== FUNÇÃO DE CONSULTA PRINCIPAL ====================
def consultar_api(url, max_tentativas=MAX_TENTATIVAS):
    """Faz requisição com tratamento cirúrgico de erros HTTP e rede"""
    for tentativa in range(max_tentativas):
        try:
            headers = {
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            }
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
                return None
                
        except urllib.error.HTTPError as e:
            if e.code in [400, 404]:
                print(f" Aviso API: HTTP {e.code} ({e.reason}) para o endereço: {url}", file=sys.stderr)
                return None
                
            if e.code == 429:
                wait_time = (2 ** tentativa) + random.uniform(0, 1)
                print(f"Rate limit na API. Aguardando {wait_time:.1f}s...", file=sys.stderr)
                time.sleep(wait_time)
                continue
                
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)
                continue
                
        except Exception as e:
            if tentativa < max_tentativas - 1:
                time.sleep(2 ** tentativa)
                continue
            print(f"Erro de conexão/rede: {e}", file=sys.stderr)
            return None
            
    return None


def consultar_cnpj(cnpj, modo_batch=False):
    if not cnpj_valido(cnpj):
        if not modo_batch:
            print(f"Erro: O CNPJ '{cnpj}' é matematicamente INVÁLIDO.")
        return None

    cnpj_limpo = "".join(filter(str.isdigit, cnpj))
    dados = None
    api_origem = None

    # 1. Tenta obter a estrutura principal pela MinhaReceita
    url_minhareceita = f"https://minhareceita.org/{cnpj_limpo}"
    dados_minhareceita = consultar_api(url_minhareceita)
    
    if dados_minhareceita:
        dados = dados_minhareceita
        api_origem = "MinhaReceita"

    # 2. Avalia se precisa acionar o fallback para dados de contato
    necessita_contato = (
        not dados 
        or not dados.get("email") 
        or dados.get("email") in ["Não informado", ""]
        or not dados.get("telefone_1") 
        or dados.get("telefone_1") in ["0", "Não informado", ""]
    )
    
    if necessita_contato:
        url_publica = f"https://publica.cnpj.ws/cnpj/{cnpj_limpo}"
        dados_publica = consultar_api(url_publica)
        
        # Cenário A: Temos a base da MinhaReceita e vamos enriquecer com a PublicaCNPJ
        if dados_publica and dados:
            estabelecimento = dados_publica.get("estabelecimento", {})
            
            if (not dados.get("email") or dados.get("email") in ["Não informado", ""]) and estabelecimento.get("email"):
                dados["email"] = estabelecimento.get("email")
            
            if (not dados.get("telefone_1") or dados.get("telefone_1") in ["0", "Não informado", ""]) and estabelecimento.get("telefone1"):
                dados["telefone_1"] = estabelecimento.get("telefone1")
                dados["ddd_telefone_1"] = estabelecimento.get("ddd1")

            if (not dados.get("telefone_2") or dados.get("telefone_2") in ["0", "Não informado", ""]) and estabelecimento.get("telefone2"):
                dados["telefone_2"] = estabelecimento.get("telefone2")
                dados["ddd_telefone_2"] = estabelecimento.get("ddd2")
                
            if (not dados.get("capital_social") or dados.get("capital_social") == 0) and dados_publica.get("capital_social"):
                dados["capital_social"] = dados_publica.get("capital_social")
                
        # Cenário B: A MinhaReceita falhou completamente, mas a PublicaCNPJ respondeu
        elif dados_publica and not dados:
            dados = dados_publica
            api_origem = "PublicaCNPJ"

    if not dados:
        if not modo_batch:
            print(f"Erro: Não foi possível obter dados do CNPJ {cnpj} em nenhuma das fontes.")
        return None

    if not modo_batch:
        if api_origem == "MinhaReceita":
            exibir_dados_minhareceita(dados)
        else:
            exibir_dados_publica(dados)
        print(f"\n--- FONTE PRINCIPAL DO LAYOUT: {api_origem} ---")
    
    return dados


# ==================== FUNÇÕES DE FORMATAÇÃO DE TELA ====================
def exibir_dados_minhareceita(data):
    try:
        capital_float = float(data.get("capital_social", 0))
        capital_social = f"R$ {capital_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        capital_social = "Não informado"

    comp = data.get("complemento")
    complemento_str = f" - {comp}" if comp and comp.strip() and "********" not in comp else ""

    print(f"NÚMERO DE INSCRIÇÃO: {data.get('cnpj')} - {data.get('identificador_matriz_filial_extenso', 'Matriz')}")
    print(f"DATA DE ABERTURA: {data.get('data_inicio_atividade')}")
    print(f"NOME EMPRESARIAL: {data.get('razao_social')}")
    print(f"NOME FANTASIA: {data.get('nome_fantasia') or '*********'}")
    print(f"PORTE: {data.get('porte', 'Não informado')}")
    print(f"CAPITAL SOCIAL: {capital_social}")
    print(f"CNAE PRINCIPAL: {data.get('cnae_fiscal')} - {data.get('cnae_fiscal_descricao')}")
    print(f"NATUREZA JURÍDICA: {data.get('codigo_natureza_juridica')} - {data.get('natureza_juridica')}")
    print(f"ENDEREÇO: {data.get('descricao_tipo_de_logradouro')} {data.get('logradouro')}, Nº {data.get('numero')}{complemento_str}")
    print(f"BAIRRO: {data.get('bairro')} | CEP: {data.get('cep')}")
    print(f"MUNICÍPIO: {data.get('municipio')} - {data.get('uf')}")
    print(f"E-MAIL: {data.get('email') or 'Não informado'}")
    
    tel1 = f"({data.get('ddd_telefone_1')}) {data.get('telefone_1')}" if data.get('telefone_1') and data.get('telefone_1') not in ['0', 'Não informado'] else "Não informado"
    print(f"TELEFONE 1: {tel1}")
    
    print(f"SITUAÇÃO CADASTRAL: {data.get('descricao_situacao_cadastral')} (desde {data.get('data_situacao_cadastral')})")

    print("\n--- CNAES SECUNDÁRIOS ---")
    cnaes_sec = data.get("cnaes_secundarios", [])
    if cnaes_sec:
        for cnae in cnaes_sec:
            print(f"• {cnae.get('codigo')} - {cnae.get('descricao')}")
    else:
        print("Nenhum mapeado.")

    print("\n--- QUADRO DE SÓCIOS E ADMINISTRADORES (QSA) ---")
    qsa = data.get("qsa", [])
    if qsa:
        for socio in qsa:
            print(f"• {socio.get('nome_socio')} | Cargo: {socio.get('qualificacao_socio')} (desde {socio.get('data_entrada_sociedade')})")
    else:
        print("Nenhum sócio listado.")


def exibir_dados_publica(data):
    est = data.get("estabelecimento", {})
    
    try:
        capital_float = float(data.get("capital_social", 0))
        capital_social = f"R$ {capital_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        capital_social = "Não informado"

    cnae_p_obj = data.get("cnae_activity_principal") or est.get("cnae_principal") or {}
    cnae_principal = f"{cnae_p_obj.get('id', 'Não mapeado')} - {cnae_p_obj.get('descricao', 'Não mapeado')}"

    print(f"NÚMERO DE INSCRIÇÃO: {est.get('cnpj')} - {est.get('tipo')}")
    print(f"DATA DE ABERTURA: {est.get('data_inicio_activity') or est.get('data_inicio_atividade')}")
    print(f"NOME EMPRESARIAL: {data.get('razao_social')}")
    print(f"NOME FANTASIA: {est.get('nome_fantasia') or '*********'}")
    print(f"PORTE: {data.get('porte', {}).get('descricao', 'Não informado')}")
    print(f"CAPITAL SOCIAL: {capital_social}")
    print(f"CNAE PRINCIPAL: {cnae_principal}")
    print(f"NATUREZA JURÍDICA: {data.get('natureza_juridica', {}).get('id')} - {data.get('natureza_juridica', {}).get('descricao')}")
    print(f"ENDEREÇO: {est.get('tipo_logradouro', '')} {est.get('logradouro', '')}, Nº {est.get('numero', '')} {est.get('complemento') or ''}")
    print(f"BAIRRO: {est.get('bairro')} | CEP: {est.get('cep')}")
    print(f"MUNICÍPIO: {est.get('cidade', {}).get('nome')} - {est.get('estado', {}).get('sigla')}")
    print(f"E-MAIL: {est.get('email') or 'Não informado'}")
    print(f"TELEFONE 1: ({est.get('ddd1')}) {est.get('telefone1')}" if est.get('telefone1') else "TELEFONE 1: Não informado")
    print(f"SITUAÇÃO CADASTRAL: {est.get('situacao_cadastral')} (desde {est.get('data_situacao_cadastral')})")

    print("\n--- CNAES SECUNDÁRIOS ---")
    cnaes_sec = est.get("cnaes_secundarios", [])
    if cnaes_sec:
        for cnae in cnaes_sec:
            print(f"• {cnae.get('codigo')} - {cnae.get('descricao')}")
    else:
        print("Nenhum mapeado.")

    print("\n--- QUADRO DE SÓCIOS E ADMINISTRADORES (QSA) ---")
    socios = data.get("socios", [])
    if socios:
        for socio in socios:
            cargo = socio.get("qualificacao_socio", {}).get("descricao", "Não informado")
            print(f"• {socio.get('nome')} | Cargo: {cargo} (desde {socio.get('data_entrada')})")
    else:
        print("Nenhum sócio listado.")


# ==================== ROTINA EM LOTE (BATCH MODE) ====================
def consultar_lote(arquivo_txt, saida_json=None):
    try:
        with open(arquivo_txt, 'r', encoding='utf-8') as f:
            cnpjs = [linha.strip() for linha in f if linha.strip()]
    except Exception as e:
        print(f"Erro ao abrir ou ler o arquivo de entrada: {e}")
        return
    
    print(f"Iniciando varredura de {len(cnpjs)} linhas (Delay ativo: {DELAY_ENTRE_REQUISICOES}s)...")
    print("-" * 60)
    
    resultados = []
    sucessos = 0
    
    for i, cnpj in enumerate(cnpjs, 1):
        if not cnpj_valido(cnpj):
            print(f"[{i}/{len(cnpjs)}] Ignorado: {cnpj} -> Matemático Inválido [✗]")
            resultados.append({"cnpj": cnpj, "sucesso": False, "erro": "CNPJ_INVALIDO", "dados": None})
            continue

        print(f"[{i}/{len(cnpjs)}] Requisitando: {cnpj}...", end="", flush=True)
        
        if i > 1:
            time.sleep(DELAY_ENTRE_REQUISICOES)
        
        dados = consultar_cnpj(cnpj, modo_batch=True)
        
        if dados:
            sucessos += 1
            resultados.append({"cnpj": cnpj, "sucesso": True, "dados": dados})
            print(" [✓ OK]")
        else:
            resultados.append({"cnpj": cnpj, "sucesso": False, "erro": "API_FAIL", "dados": None})
            print(" [✗ FALHA]")
    
    print("\n" + "=" * 60)
    print(f"RELATÓRIO FINAL: {sucessos}/{len(cnpjs)} processados com sucesso ({sucessos/len(cnpjs)*100:.1f}%)")
    
    if saida_json:
        try:
            with open(saida_json, 'w', encoding='utf-8') as f:
                json.dump(resultados, f, ensure_ascii=False, indent=2)
            print(f"Arquivo JSON consolidado salvo em: {saida_json}")
        except Exception as e:
            print(f"Erro ao tentar persistir o arquivo JSON: {e}")


# ==================== PONTO DE ENTRADA CLI ====================
if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] in ["--help", "-h"]:
        mostrar_help()
    
    if len(sys.argv) >= 2 and sys.argv[1] == "--lote":
        if len(sys.argv) < 3:
            print("Erro: Forneça o caminho do arquivo .txt contendo a lista.")
            print("Execute './cnpj_query.py --help' para ver a sintaxe correta.")
            sys.exit(1)
        
        arquivo = sys.argv[2]
        saida_json = None
        
        if len(sys.argv) >= 4 and sys.argv[3] == "--json":
            if len(sys.argv) >= 5:
                saida_json = sys.argv[4]
            else:
                print("Aviso: Nenhuma saída especificada para a flag --json. Gerando nome automático.")
                saida_json = f"{arquivo.rsplit('.', 1)[0]}_resultados.json"
        elif len(sys.argv) > 3 and sys.argv[3] != "--json":
            print(f"Aviso: Parâmetro '{sys.argv[3]}' desconhecido e ignorado. Use a sintaxe correta.")
        
        consultar_lote(arquivo, saida_json)
        
    elif len(sys.argv) >= 2:
        consultar_cnpj(sys.argv[1])
    else:
        mostrar_help()
