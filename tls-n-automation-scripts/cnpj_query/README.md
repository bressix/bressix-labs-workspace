<p align="center">
  <img src="https://raw.githubusercontent.com/bressix/bressix/main/bressix_LABs_01.png" alt="bressix LABs" width="500"/>
</p>

# cnpj_query

> Resilient CNPJ Lookup Engine
>
> Validação algorítmica local, consulta resiliente, enriquecimento corporativo e processamento em lote utilizando múltiplas fontes públicas de dados.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![License](https://img.shields.io/badge/License-GPLv3-green)
![Status](https://img.shields.io/badge/Status-Active%20Development-orange)
![API](https://img.shields.io/badge/API-Multi--Provider-red)

---

## ⚠️ PROOF OF CONCEPT / EM DESENVOLVIMENTO

### English

This repository contains experimental software, research artifacts, and Proof of Concept (PoC) implementations developed as part of the **bressix LABs** ecosystem.

The project is intended for research, technical validation, experimentation, and reference implementations.

This repository must not be considered production-ready software.

Features, interfaces, APIs, and behaviors may change without notice.

### Português

Este repositório contém software experimental, artefatos de pesquisa e implementações de Prova de Conceito (PoC) desenvolvidos como parte do ecossistema **bressix LABs**.

O projeto é destinado à pesquisa, validação técnica, experimentação e implementações de referência.

Este repositório não deve ser considerado software pronto para produção.

Funcionalidades, interfaces, APIs e comportamentos podem ser alterados sem aviso prévio.

---

## ⚖️ DISCLAIMER / ISENÇÃO DE RESPONSABILIDADE

### English

**NO WARRANTY**

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

THE AUTHORS, CONTRIBUTORS, AND COPYRIGHT HOLDERS SHALL NOT BE LIABLE FOR ANY CLAIM, DAMAGE, LOSS OF DATA, SECURITY INCIDENT, SERVICE INTERRUPTION, OR OTHER LIABILITY ARISING FROM THE USE OR MISUSE OF THIS SOFTWARE.

USE OF THIS SOFTWARE IS ENTIRELY AT YOUR OWN RISK.

### Português

**SEM GARANTIAS**

ESTE SOFTWARE É FORNECIDO "NO ESTADO EM QUE SE ENCONTRA", SEM GARANTIAS DE QUALQUER NATUREZA.

OS AUTORES, COLABORADORES E DETENTORES DOS DIREITOS AUTORAIS NÃO PODERÃO SER RESPONSABILIZADOS POR DANOS, PERDA DE DADOS, INCIDENTES DE SEGURANÇA OU OUTRAS RESPONSABILIDADES DECORRENTES DO USO OU MAU USO DESTE SOFTWARE.

A UTILIZAÇÃO DESTE SOFTWARE É DE INTEIRA RESPONSABILIDADE DO USUÁRIO.

---

## 🔐 SECURITY NOTICE / AVISO DE SEGURANÇA

### English

No private keys, production certificates, active API tokens, passwords, customer information, or confidential corporate data are intentionally stored within this repository.

### Português

Nenhuma chave privada, certificado de produção, token ativo de API, senha, dado de cliente ou informação corporativa confidencial é armazenada intencionalmente neste repositório.

---

<details>
<summary>🇺🇸 English Version (Click to expand)</summary>

## Overview

**cnpj_query** is a resilient corporate information retrieval engine designed to validate Brazilian CNPJ identifiers locally and retrieve company information from multiple public providers.

The engine minimizes unnecessary network traffic through mathematical validation and automatically enriches returned data using multiple data sources when required.

---

## Features

* Local mathematical CNPJ validation
* Multi-provider architecture
* Intelligent fallback mechanism
* Automatic data enrichment
* Batch processing support
* JSON export support
* HTTP 429 exponential backoff
* Custom User-Agent
* Pure Python implementation
* No external dependencies

---

## Supported Providers

### Primary Provider

* MinhaReceita

### Secondary Provider

* PublicaCNPJ

Returned datasets are automatically evaluated and merged when enrichment opportunities are detected.

---

## Processing Flow

```text
Input CNPJ
     │
     ▼
Local Validation
     │
     ▼
MinhaReceita
     │
     ▼
Response Evaluation
     │
     ▼
PublicaCNPJ Fallback
     │
     ▼
Data Enrichment
     │
     ▼
Structured Output
```

## Usage

Single lookup:

```bash
./cnpj_query.py 53020152000112
```

Help:

```bash
./cnpj_query.py --help
```

## Batch Mode

Input file:

```text
53020152000112
12.345.678/0001-99
```

Execution:

```bash
./cnpj_query.py --lote empresas.txt
```

JSON export:

```bash
./cnpj_query.py --lote empresas.txt --json resultados.json
```

---

## Typical Applications

* PKI customer validation
* TLS enrollment workflows
* Corporate onboarding
* CRM enrichment
* Compliance validation
* Business intelligence pipelines

</details>

<details>
<summary>🇧🇷 Versão em Português (Clique para expandir)</summary>

## Visão Geral

O **cnpj_query** é um mecanismo resiliente para consulta e validação de dados corporativos brasileiros utilizando múltiplas fontes públicas de informação.

O sistema realiza validação matemática local antes de qualquer consulta externa e utiliza enriquecimento inteligente de dados através de múltiplos provedores.

---

## Funcionalidades

* Validação matemática local de CNPJ
* Arquitetura multi-provedor
* Fallback inteligente entre APIs
* Enriquecimento automático de dados
* Processamento em lote
* Exportação JSON
* Backoff exponencial para HTTP 429
* User-Agent customizado
* Implementação pura em Python
* Sem dependências externas

---

## Provedores Suportados

### Fonte Primária

* MinhaReceita

### Fonte Secundária

* PublicaCNPJ

Os dados retornados são avaliados automaticamente e enriquecidos quando necessário.

---

## Fluxo de Processamento

```text
CNPJ Informado
      │
      ▼
Validação Matemática
      │
      ▼
MinhaReceita
      │
      ▼
Validação da Resposta
      │
      ▼
Fallback PublicaCNPJ
      │
      ▼
Enriquecimento
      │
      ▼
Resultado Estruturado
```

## Exemplos de Uso

Consulta única:

```bash
./cnpj_query.py 53020152000112
```

Ajuda:

```bash
./cnpj_query.py --help
```

## Processamento em Lote

Arquivo de entrada:

```text
53020152000112
12.345.678/0001-99
```

Execução:

```bash
./cnpj_query.py --lote empresas.txt
```

Exportação JSON:

```bash
./cnpj_query.py --lote empresas.txt --json resultados.json
```

---

## Aplicações

* Validação para certificados digitais
* Processos de PKI
* Onboarding corporativo
* Enriquecimento de CRM
* Compliance
* Inteligência operacional

</details>

---

## 🗺️ Roadmap

### Planned

* Additional providers
* Local cache support
* CSV export
* Response normalization layer
* Structured logging
* Provider abstraction modules

---

## License

GNU General Public License v3.0 (GPL-3.0)

Copyright (C) 2026 bressix LABs

GitHub: https://github.com/bressix

