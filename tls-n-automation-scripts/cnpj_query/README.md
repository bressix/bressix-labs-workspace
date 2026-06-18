<p align="center">
  <img src="https://raw.githubusercontent.com/bressix/bressix/main/bressix_LABs_01.png" alt="bressix LABs" width="500"/>
</p>

# cnpj_query

> Resilient CNPJ Lookup Engine
>
> Validação algorítmica local, consulta resiliente e enriquecimento corporativo através de múltiplas fontes de dados.

---

## ⚠️ WORK IN PROGRESS / EM CONSTRUÇÃO

**EN:** New providers, normalization layers, response adapters, local cache engines and export modules are continuously being integrated.

**PT-BR:** Novos provedores, camadas de normalização, adaptadores de resposta, mecanismos de cache local e módulos de exportação estão sendo incorporados continuamente.

---

<details>
<summary>🇺🇸 English Version (Click to expand)</summary>

## Overview

cnpj_query is a resilient corporate information retrieval engine designed to perform Brazilian CNPJ validation and company data acquisition using multiple public data providers.

Unlike traditional single-source implementations, the project validates CNPJ identifiers locally before consuming network resources and automatically switches between providers when incomplete datasets, service outages or rate limits are encountered.

The architecture was originally developed to support PKI operations, TLS certificate issuance workflows, compliance validation routines and corporate onboarding processes.

---

## Core Capabilities

* Mathematical CNPJ validation performed locally.
* Multi-provider architecture.
* Intelligent API fallback mechanism.
* Automatic data enrichment across providers.
* Structured JSON data export.
* Batch processing support.
* Exponential backoff handling for HTTP 429 responses.
* Custom User-Agent implementation following API consumption best practices.
* Resilient operation under provider degradation scenarios.

---

## Processing Flow

```text
Input CNPJ
     │
     ▼
Local Mathematical Validation
     │
     ▼
Primary Provider (MinhaReceita)
     │
     ▼
Response Evaluation
     │
     ▼
Secondary Provider (PublicaCNPJ)
     │
     ▼
Data Enrichment & Merge
     │
     ▼
Structured Output
```

---

## Main Features

### Local Validation Layer

Performs full CNPJ verification digit validation before any network communication occurs.

Benefits:

* Reduces unnecessary API consumption.
* Eliminates invalid requests.
* Improves overall performance.

### Intelligent Provider Fallback

Primary source:

* MinhaReceita

Fallback source:

* PublicaCNPJ

If critical contact fields are missing or unavailable, the engine automatically attempts enrichment using secondary providers.

### Batch Processing

Supports large-scale consultation operations using text files containing one CNPJ per line.

Capabilities:

* Automatic delay management.
* Success/failure tracking.
* Consolidated JSON export.
* Invalid CNPJ filtering.

### Network Resilience

Implemented mechanisms include:

* HTTP error classification.
* Exponential retry strategy.
* Rate-limit mitigation.
* Timeout controls.
* Graceful failure handling.

---

## Example Usage

Single query:

```bash
./cnpj_query.py 53020152000112
```

Batch mode:

```bash
./cnpj_query.py --lote empresas.txt
```

Batch mode with JSON export:

```bash
./cnpj_query.py --lote empresas.txt --json resultado.json
```

---

## Potential Applications

* PKI customer verification.
* TLS/SSL certificate enrollment.
* CRM enrichment.
* Corporate onboarding.
* Compliance validation.
* Business intelligence workflows.
* Infrastructure asset correlation.
* Corporate data auditing.

---

</details>

<details>
<summary>🇧🇷 Versão em Português (Clique para expandir)</summary>

## Visão Geral

O cnpj_query é um mecanismo resiliente para consulta e validação de dados corporativos brasileiros utilizando múltiplas fontes públicas de informação.

Diferentemente de implementações dependentes de um único provedor, o projeto realiza validação matemática local do CNPJ antes do consumo de recursos de rede e alterna automaticamente entre provedores quando encontra indisponibilidades, limitações ou respostas incompletas.

A arquitetura foi originalmente desenvolvida para apoiar operações de PKI, emissão de certificados digitais, validações de compliance e processos corporativos de onboarding.

---

## Capacidades Principais

* Validação matemática local de CNPJ.
* Arquitetura multi-provedor.
* Mecanismo inteligente de fallback.
* Enriquecimento automático de dados.
* Exportação estruturada em JSON.
* Processamento em lote.
* Backoff exponencial para tratamento de rate limits.
* User-Agent customizado seguindo boas práticas de integração.
* Operação resiliente diante de falhas dos provedores.

---

## Fluxo de Processamento

```text
CNPJ Informado
      │
      ▼
Validação Matemática Local
      │
      ▼
Provedor Primário (MinhaReceita)
      │
      ▼
Avaliação da Resposta
      │
      ▼
Provedor Secundário (PublicaCNPJ)
      │
      ▼
Mesclagem e Enriquecimento
      │
      ▼
Resultado Estruturado
```

---

## Funcionalidades

### Camada de Validação Local

Executa a validação completa dos dígitos verificadores antes de qualquer consulta externa.

Benefícios:

* Redução do consumo de APIs.
* Eliminação de consultas inválidas.
* Melhor desempenho geral.

### Fallback Inteligente

Fonte principal:

* MinhaReceita

Fonte secundária:

* PublicaCNPJ

Caso informações críticas estejam ausentes, o sistema realiza enriquecimento automático utilizando fontes complementares.

### Processamento em Lote

Permite consultas massivas a partir de arquivos texto contendo um CNPJ por linha.

Recursos:

* Controle automático de delay.
* Rastreamento de sucesso e falha.
* Exportação consolidada em JSON.
* Filtragem de CNPJs inválidos.

### Resiliência de Rede

Mecanismos implementados:

* Classificação de erros HTTP.
* Estratégia de retry exponencial.
* Mitigação de rate limiting.
* Controle de timeout.
* Tratamento seguro de falhas.

---

## Exemplos de Uso

Consulta única:

```bash
./cnpj_query.py 53020152000112
```

Consulta em lote:

```bash
./cnpj_query.py --lote empresas.txt
```

Consulta em lote com exportação JSON:

```bash
./cnpj_query.py --lote empresas.txt --json resultado.json
```

---

## Aplicações

* Validação para emissão de certificados digitais.
* Fluxos de onboarding corporativo.
* Auditoria de dados empresariais.
* Integrações CRM e ERP.
* Compliance corporativo.
* Processos de PKI.
* Automações de infraestrutura.
* Inteligência operacional.

---

</details>

## Security Policy / Política de Segurança

No private keys, production certificates, passwords, or active API tokens are stored within this repository.

Local environments must rely on isolated configuration files, environment variables or `.env` files.

*Nenhuma chave privada, certificado de produção, senha ou token ativo é armazenado neste repositório.*

*Ambientes locais devem utilizar variáveis de ambiente, arquivos de configuração isolados ou arquivos `.env`.*

---

## License

GNU General Public License v3.0 (GPL-3.0)

---

## Author

**Thiago Bressani**
bressix LABs

GitHub: https://github.com/bressix

