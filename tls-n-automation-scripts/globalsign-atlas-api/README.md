<p align="center">
  <img src="https://raw.githubusercontent.com/bressix/bressix/main/bressix_LABs_01.png" alt="bressix LABs" width="500"/>
</p>

# globalsign-atlas-api

> PKI Automation Toolkit for GlobalSign Atlas API
>
> Automação de ciclo de vida de certificados TLS/mTLS utilizando a API GlobalSign Atlas.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-GPLv3-green)
![Status](https://img.shields.io/badge/Status-Active%20Development-orange)
![API](https://img.shields.io/badge/API-GlobalSign%20Atlas-red)

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

No private keys, production certificates, active API credentials, customer assets, cryptographic seeds, or confidential corporate information are intentionally stored within this repository.

Authentication material must always be supplied through isolated local configuration files, environment variables, or secure secret management solutions.

### Português

Nenhuma chave privada, certificado de produção, credencial ativa de API, ativo de cliente, semente criptográfica ou informação corporativa confidencial é armazenada intencionalmente neste repositório.

Materiais de autenticação devem sempre ser fornecidos através de configurações locais isoladas, variáveis de ambiente ou soluções seguras de gerenciamento de segredos.

---

<details>
<summary>🇺🇸 English Version (Click to expand)</summary>

## Overview

`globalsign-atlas-api` is a modular Python toolkit designed to interact with the GlobalSign Atlas Certificate Management API.

The project focuses on automating Certificate Lifecycle Management (CLM) operations including authentication, certificate profile discovery, domain validation workflows, certificate issuance processes, and certificate retrieval operations.

The architecture separates authentication, API communication, validation workflows, and certificate operations into reusable modules intended for infrastructure automation and PKI engineering environments.

> 🤝 **Acknowledgement**
>
> This project is independently developed by **bressix LABs**.
>
> Testing, validation activities, and access to non-production Atlas environments have benefited from collaboration and technical support provided by Keysec.

---

## Project Scope

Current development efforts focus on:

* Atlas API authentication workflows
* Certificate profile discovery
* Domain validation checks
* CSR submission automation
* Certificate retrieval workflows
* Reusable PKI automation primitives

This project is not intended to replace enterprise CLM platforms and should be considered an automation toolkit and reference implementation.

---

## Core Capabilities

* Modular authentication layer
* mTLS client authentication support
* API Key authentication support
* Certificate profile queries
* Domain validation checks
* CSR submission workflows
* Automated certificate retrieval
* Structured local configuration
* Infrastructure automation support

---

## Reference Architecture

```text
globalsign-atlas-api/
│
├── auth/
├── atlas_client/
├── certificate_profiles/
├── domain_validation/
├── issuance/
├── retrieval/
├── examples/
└── docs/
```

---

## Security Model

The project is designed around the principle that private keys remain under local operator control whenever possible.

The repository intentionally excludes:

* Private keys
* Production certificates
* Customer assets
* Active API credentials

Authentication materials must be provided through isolated local configuration.

---

## Processing Flow

```text
Local Key & CSR Generation
            │
            ▼
mTLS Authentication
(Client Certificate + API Key)
            │
            ▼
GlobalSign Atlas Gateway
            │
            ▼
┌───────────┴───────────┐
│                       │
▼                       ▼
Domain Validation   Profile Discovery
│                       │
└───────────┬───────────┘
            │
            ▼
Certificate Issuance
            │
            ▼
Certificate Retrieval
            │
            ▼
Secure Local Storage
```

---

## Typical Applications

* TLS certificate automation
* mTLS deployments
* PKI lifecycle automation
* Enterprise certificate operations
* Infrastructure as Code (IaC)
* Compliance workflows
* Internal certificate inventory systems

</details>

---

<details>
<summary>🇧🇷 Versão em Português (Clique para expandir)</summary>

## Visão Geral

O `globalsign-atlas-api` é um toolkit modular em Python desenvolvido para integração com a API de gerenciamento de certificados GlobalSign Atlas.

O projeto concentra-se na automação de operações de Certificate Lifecycle Management (CLM), incluindo autenticação, descoberta de perfis de certificados, validações de domínio, emissão de certificados e processos de recuperação de certificados.

A arquitetura separa autenticação, comunicação com API, validações e operações de certificados em módulos reutilizáveis voltados para automação de infraestrutura e ambientes de engenharia PKI.

> 🤝 **Reconhecimento**
>
> Este projeto é desenvolvido de forma independente pela **bressix LABs**.
>
> Atividades de teste, validação e acesso a ambientes Atlas não produtivos contam com colaboração e suporte técnico da Keysec.

---

## Escopo do Projeto

Os esforços atuais de desenvolvimento concentram-se em:

* Fluxos de autenticação Atlas API
* Descoberta de perfis de certificados
* Verificações de validação de domínio
* Automação de envio de CSR
* Recuperação de certificados
* Componentes reutilizáveis para automação PKI

Este projeto não tem o objetivo de substituir plataformas corporativas de CLM, devendo ser entendido como um toolkit de automação e implementação de referência.

---

## Capacidades Principais

* Camada modular de autenticação
* Suporte a autenticação mTLS
* Suporte a autenticação por API Key
* Consulta de perfis de certificados
* Verificação de validação de domínios
* Fluxos de envio de CSR
* Recuperação automatizada de certificados
* Configuração estruturada local
* Integração com automações de infraestrutura

---

## Arquitetura de Referência

```text
globalsign-atlas-api/
│
├── auth/
├── atlas_client/
├── certificate_profiles/
├── domain_validation/
├── issuance/
├── retrieval/
├── examples/
└── docs/
```

---

## Modelo de Segurança

O projeto foi concebido seguindo o princípio de que chaves privadas devem permanecer sob controle local do operador sempre que possível.

O repositório exclui intencionalmente:

* Chaves privadas
* Certificados de produção
* Ativos de clientes
* Credenciais ativas de API

Materiais de autenticação devem ser fornecidos através de configurações locais isoladas.

---

## Fluxo de Processamento

```text
Geração Local de Chave e CSR
             │
             ▼
Autenticação mTLS
(Certificado Cliente + API Key)
             │
             ▼
Gateway GlobalSign Atlas
             │
             ▼
┌────────────┴────────────┐
│                         │
▼                         ▼
Validação de Domínio   Descoberta de Perfis
│                         │
└────────────┬────────────┘
             │
             ▼
Emissão de Certificado
             │
             ▼
Recuperação do Certificado
             │
             ▼
Armazenamento Seguro Local
```

---

## Aplicações Típicas

* Automação de certificados TLS
* Ambientes mTLS
* Automação de ciclo de vida PKI
* Operações corporativas de certificados
* Infraestrutura como Código (IaC)
* Processos de compliance
* Inventário interno de certificados

</details>

---

## 🗺️ Roadmap

### Planned

* Certificate lifecycle automation
* Automated renewal workflows
* Domain validation monitoring
* Certificate inventory reporting
* Structured logging
* Batch issuance support
* Atlas API abstraction layer
* Local certificate database integration

---

## License

GNU General Public License v3.0 (GPL-3.0)

Copyright (C) 2026 bressix LABs

GitHub: https://github.com/bressix


