<p align="center">
  <img src="https://raw.githubusercontent.com/bressix/bressix/main/bressix_LABs_01.png" alt="bressix LABs" width="500"/>
</p>

# bressix-labs-workspace

> Engineering Research & Development Laboratory
>
> Laboratório de Pesquisa e Desenvolvimento em Engenharia

![Environment](https://img.shields.io/badge/Environment-Parrot%20OS%20%7C%20Linux-blueviolet)
![License](https://img.shields.io/badge/License-GPLv3-green)
![Status](https://img.shields.io/badge/Workspace-Active%20Research-orange)
![Security](https://img.shields.io/badge/Security-Sanitized-success)

---

## ⚠️ PROOF OF CONCEPT / EM DESENVOLVIMENTO

### English

This workspace acts as a centralized monorepo containing **experimental software, embedded prototypes, firmware source trees, hardware designs, and Proof of Concept (PoC) implementations** under active evolution by **bressix LABs**.

The contents within this repository are structured for:

* Technical research, prototyping, and security auditing.
* Reference implementations and hardware-software integration tests.
* Academic, laboratory, and internal benchmarking logic.

Unless explicitly documented otherwise inside specific subdirectories, **no asset within this workspace should be assumed to be a production-ready product**.

Architectures, pinning configurations, schemas, interfaces, APIs, and logic are subject to breaking changes without notice.

### Português

Este workspace atua como um monorepo centralizado contendo **software experimental, protótipos embarcados, árvores de firmware, designs de hardware e implementações de Prova de Conceito (PoC)** em evolução ativa pela **bressix LABs**.

O conteúdo deste repositório é estruturado para:

* Pesquisa técnica, prototipagem e auditorias de segurança.
* Implementações de referência e testes de integração hardware-software.
* Lógica acadêmica, laboratorial e benchmarks internos.

Salvo indicação explícita em contrário dentro de subdiretórios específicos, **nenhum ativo neste workspace deve ser considerado um produto pronto para produção**.

Arquiteturas, configurações de pinagem, esquemas, interfaces, APIs e lógicas estão sujeitos a alterações sem aviso prévio.

---

## ⚖️ DISCLAIMER / ISENÇÃO DE RESPONSABILIDADE

### English

**NO WARRANTY**

THIS WORKSPACE AND ALL CONTAINED SOFTWARE, FIRMWARE, HARDWARE DESIGNS, SCHEMATICS, AND OTHER ASSETS ARE PROVIDED **"AS IS"**, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, SECURITY, FUNCTIONALITY, RELIABILITY, OR HARDWARE SAFETY.

THE AUTHORS, CONTRIBUTORS, AND COPYRIGHT HOLDERS SHALL NOT BE LIABLE FOR ANY CLAIM, DAMAGE, LOSS OF DATA, DEVICE BRICKING, HARDWARE FAILURE, SECURITY INCIDENT, SERVICE INTERRUPTION, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE, FIRMWARE, HARDWARE DESIGNS, SCHEMATICS, OR THEIR USE.

OPERATING, COMPILING, FLASHING, MODIFYING, OR DEPLOYING ANY CODE OR DESIGN FROM THIS REPOSITORY IS ENTIRELY AT YOUR OWN RISK.

### Português

**SEM GARANTIAS**

ESTE WORKSPACE E TODOS OS SOFTWARES, FIRMWARES, PROJETOS DE HARDWARE, ESQUEMÁTICOS E DEMAIS ATIVOS CONTIDOS SÃO FORNECIDOS **"NO ESTADO EM QUE SE ENCONTRAM"**, SEM GARANTIAS DE QUALQUER NATUREZA, EXPRESSAS OU IMPLÍCITAS, INCLUINDO, MAS NÃO SE LIMITANDO A, GARANTIAS DE COMERCIALIZAÇÃO, ADEQUAÇÃO A UMA FINALIDADE ESPECÍFICA, NÃO VIOLAÇÃO, SEGURANÇA, FUNCIONALIDADE, CONFIABILIDADE OU INTEGRIDADE FÍSICA DO HARDWARE.

OS AUTORES, COLABORADORES E DETENTORES DOS DIREITOS AUTORAIS NÃO PODERÃO SER RESPONSABILIZADOS POR QUAISQUER RECLAMAÇÕES, DANOS, PERDA DE DADOS, INUTILIZAÇÃO DE DISPOSITIVOS (DEVICE BRICKING), FALHAS DE HARDWARE, INCIDENTES DE SEGURANÇA, INTERRUPÇÕES DE SERVIÇO OU OUTRAS RESPONSABILIDADES DECORRENTES DO USO, MAU USO OU IMPOSSIBILIDADE DE USO DESTES SOFTWARES, FIRMWARES, PROJETOS DE HARDWARE OU ESQUEMÁTICOS.

A EXECUÇÃO, COMPILAÇÃO, GRAVAÇÃO (FLASHING), MODIFICAÇÃO OU IMPLANTAÇÃO DE QUALQUER CÓDIGO OU DESIGN DESTE REPOSITÓRIO É DE INTEIRA RESPONSABILIDADE DO USUÁRIO.

---

## 🔐 SECURITY NOTICE / AVISO DE SEGURANÇA

### English

No private keys, cryptographic seeds, production certificates, active service tokens, customer credentials, or confidential corporate information are tracked within this repository.

All development workflows rely on repository sanitization practices, strict `.gitignore` policies, and isolated local environments.

Local engineering work should rely on detached configuration files, environment variables, or `.env` templates that are never committed to version control.

### Português

Nenhuma chave privada, semente criptográfica, certificado de produção, token ativo de serviço, credencial de cliente ou informação corporativa confidencial é rastreada dentro deste repositório.

Todos os fluxos de desenvolvimento utilizam práticas de higienização de repositório, políticas rígidas de `.gitignore` e ambientes locais isolados.

Trabalhos locais de engenharia devem utilizar arquivos de configuração desacoplados, variáveis de ambiente ou templates `.env` que nunca sejam enviados ao controle de versão.

---

## 🎯 Mission Statement

### English

bressix LABs is an independent engineering laboratory focused on hardware development, embedded systems, Linux customization, information security, PKI automation, infrastructure tooling, and applied research.

The objective is to document experiments, preserve technical knowledge, and share reference implementations that may be useful to the broader engineering community.

### Português

A bressix LABs é um laboratório independente de engenharia focado em desenvolvimento de hardware, sistemas embarcados, customização Linux, segurança da informação, automação PKI, ferramentas de infraestrutura e pesquisa aplicada.

O objetivo é documentar experimentos, preservar conhecimento técnico e compartilhar implementações de referência que possam ser úteis para a comunidade de engenharia.

---

## 🗂️ Workspace Architecture / Estrutura do Repositório

```text
bressix-labs-workspace/
├── 3D/                        # Functional 3D modeling and mechanical CAD assets.
├── audio/                     # Audio engineering, DSP experiments, and acoustic studies.
├── firmware/                  # Embedded firmware development (ESP32, CH552, AVR, RP2350).
├── hardware/                  # Schematics, PCB layouts, hardware analysis, and pin mapping.
├── system-hacking-n-tuning/   # Linux customization, system tuning, drivers, and platform optimization.
├── tls-n-automation-scripts/  # PKI tooling, infrastructure utilities, automation scripts, and API integrations.
│   ├── cnpj_query/            # Resilient multi-provider CNPJ acquisition engine.
│   ├── globalsign-atlas-api/  # Atlas API integration modules.
│   ├── globalsign-gcc-api/    # Legacy GCC API integration modules.
│   ├── ssl-tls-auditing/      # TLS auditing and compliance validation tools.
│   ├── tls-crt/               # X.509 certificate manipulation utilities.
│   ├── tls-discovery/         # TLS asset discovery and inventory automation.
│   └── tls-scripts/           # Core cryptographic and infrastructure helper scripts.
└── WIP/                       # Experimental and unclassified development sandbox.
```

---

## License

GNU General Public License v3.0 (GPL-3.0)

Copyright (C) 2026 bressix LABs

