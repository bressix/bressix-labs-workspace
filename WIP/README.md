<p align="center">
  <img src="https://raw.githubusercontent.com/bressix/bressix/main/bressix_LABs_01.png" alt="bressix LABs" width="500"/>
</p>

# bressix-labs-workspace

> Engineering Research & Development Laboratory
>
> Laboratório de Pesquisa e Desenvolvimento em Engenharia

![Environment](https://img.shields.io/badge/Environment-Parrot%20OS%20%7C%20Linux-blueviolet)
![Status](https://img.shields.io/badge/Status-Active%20Research-orange)
![License](https://img.shields.io/badge/License-GPLv3-green)
![Security](https://img.shields.io/badge/Security-Sanitized-success)

---

*As versões em PT-BR estão disponíveis nos blocos expansíveis de cada seção.*

## Proof of Concept / Em Desenvolvimento

This repository is the main engineering workspace for **bressix LABs**.

Here you'll find projects at different stages of development. Some are production-ready and actively maintained, while others are early prototypes, experiments, or ongoing research. That diversity is intentional and reflects how we approach engineering.

We believe good engineering evolves through iteration. Ideas are tested, designs are refined, and documentation grows alongside the project. Rather than waiting for everything to be perfect, we prefer to share our work as it evolves.

Not every repository follows the same structure, contains the same level of documentation, or has the same degree of maturity. Each project is documented according to its own complexity and current stage of development.

The purpose of this workspace is to build, document, and share engineering projects as they evolve.

<details>
<summary><strong>PT-BR</strong></summary>

Este repositório é o principal ambiente de engenharia da **bressix LABs**.

Aqui você encontrará projetos em diferentes estágios de desenvolvimento. Alguns estão prontos para uso e são mantidos ativamente, enquanto outros ainda são protótipos, experimentos ou pesquisas em andamento. Essa diversidade é intencional e reflete a forma como fazemos engenharia.

Acreditamos que boa engenharia evolui por meio da iteração. Ideias são testadas, projetos são refinados e a documentação cresce junto com o próprio desenvolvimento. Em vez de esperar que tudo esteja perfeito, preferimos compartilhar nosso trabalho à medida que ele evolui.

Nem todos os repositórios seguem a mesma estrutura, possuem o mesmo nível de documentação ou apresentam o mesmo grau de maturidade. Cada projeto é documentado de acordo com sua complexidade e seu estágio de desenvolvimento.

O propósito deste workspace é construir, documentar e compartilhar projetos de engenharia à medida que evoluem.

</details>

## Disclaimer

#### NO WARRANTY

THIS WORKSPACE, INCLUDING ALL SOFTWARE, FIRMWARE, HARDWARE DESIGNS, SCHEMATICS, AND OTHER ASSETS, IS PROVIDED **"AS IS"**, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, SECURITY, FUNCTIONALITY, RELIABILITY, OR HARDWARE SAFETY.

THE AUTHORS, CONTRIBUTORS, AND COPYRIGHT HOLDERS SHALL NOT BE LIABLE FOR ANY CLAIM, DAMAGES, LOSS OF DATA, DEVICE BRICKING, HARDWARE FAILURE, SECURITY INCIDENT, SERVICE INTERRUPTION, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THIS WORKSPACE OR THE USE OF ANY SOFTWARE, FIRMWARE, HARDWARE DESIGN, SCHEMATIC, OR OTHER ASSET PROVIDED HEREIN.

USING, COMPILING, FLASHING, MODIFYING, OR DEPLOYING ANY CODE, FIRMWARE, HARDWARE DESIGN, OR OTHER ASSET FROM THIS REPOSITORY IS ENTIRELY AT YOUR OWN RISK.

THIS DISCLAIMER APPLIES TO THE ENTIRE WORKSPACE UNLESS A SPECIFIC PROJECT EXPLICITLY STATES OTHERWISE.

<details>
<summary><strong>PT-BR</strong></summary>

#### SEM GARANTIAS

ESTE WORKSPACE, INCLUINDO TODOS OS SOFTWARES, FIRMWARES, PROJETOS DE HARDWARE, ESQUEMÁTICOS E DEMAIS ATIVOS, É FORNECIDO **"NO ESTADO EM QUE SE ENCONTRA"**, SEM GARANTIAS DE QUALQUER NATUREZA, EXPRESSAS OU IMPLÍCITAS, INCLUINDO, MAS NÃO SE LIMITANDO A, GARANTIAS DE COMERCIALIZAÇÃO, ADEQUAÇÃO A UMA FINALIDADE ESPECÍFICA, NÃO VIOLAÇÃO, SEGURANÇA, FUNCIONALIDADE, CONFIABILIDADE OU INTEGRIDADE FÍSICA DO HARDWARE.

OS AUTORES, COLABORADORES E DETENTORES DOS DIREITOS AUTORAIS NÃO PODERÃO SER RESPONSABILIZADOS POR QUAISQUER RECLAMAÇÕES, DANOS, PERDA DE DADOS, INUTILIZAÇÃO DE DISPOSITIVOS (DEVICE BRICKING), FALHAS DE HARDWARE, INCIDENTES DE SEGURANÇA, INTERRUPÇÕES DE SERVIÇO OU OUTRAS RESPONSABILIDADES DECORRENTES DO USO DESTE WORKSPACE OU DE QUALQUER SOFTWARE, FIRMWARE, PROJETO DE HARDWARE, ESQUEMÁTICO OU OUTRO ATIVO DISPONIBILIZADO NESTE REPOSITÓRIO.

O USO, A COMPILAÇÃO, A GRAVAÇÃO (FLASHING), A MODIFICAÇÃO OU A IMPLANTAÇÃO DE QUALQUER CÓDIGO, FIRMWARE, PROJETO DE HARDWARE OU OUTRO ATIVO DESTE REPOSITÓRIO É DE INTEIRA RESPONSABILIDADE DO USUÁRIO.

ESTA ISENÇÃO DE RESPONSABILIDADE APLICA-SE A TODO O WORKSPACE, EXCETO QUANDO UM PROJETO ESPECÍFICO DECLARAR EXPRESSAMENTE O CONTRÁRIO.

</details>

## Security Notice

No private keys, cryptographic seeds, production certificates, active service tokens, customer credentials, or confidential corporate information are stored or tracked within this repository.

Development workflows follow repository sanitization practices, strict `.gitignore` policies, and isolated local environments to prevent accidental disclosure of sensitive information.

Local engineering activities should rely on detached configuration files, environment variables, or `.env` templates that are never committed to version control.

Repositories may intentionally include placeholder files, sample certificates, mock credentials, or template configurations for demonstration purposes. Such artifacts are non-functional and intended solely for development, testing, or documentation.

<details>
<summary><strong>PT-BR</strong></summary>

Nenhuma chave privada, semente criptográfica, certificado de produção, token ativo de serviço, credencial de cliente ou informação corporativa confidencial é armazenada ou rastreada neste repositório.

Os fluxos de desenvolvimento seguem práticas de higienização do repositório, políticas rigorosas de `.gitignore` e ambientes locais isolados para reduzir o risco de exposição acidental de informações sensíveis.

As atividades locais de engenharia devem utilizar arquivos de configuração desacoplados, variáveis de ambiente ou templates `.env` que nunca sejam enviados ao controle de versão.

Os repositórios podem conter arquivos de exemplo, certificados fictícios, credenciais simuladas ou configurações modelo destinados exclusivamente à demonstração, desenvolvimento, testes ou documentação. Esses artefatos não são funcionais e não representam credenciais reais.

</details>

## Mission Statement

bressix LABs exists to advance engineering through practical research, experimentation, and open documentation.

Our work spans multiple disciplines—including hardware, embedded systems, Linux, information security, PKI, automation, infrastructure, and applied research—but the mission remains the same: building practical solutions, documenting technical decisions, and sharing knowledge that others can study, reproduce, and extend.

We believe engineering knowledge becomes more valuable when it is documented, reproducible, and shared.

<details>
<summary><strong>PT-BR</strong></summary>

A bressix LABs existe para promover a engenharia por meio de pesquisa prática, experimentação e documentação aberta.

Nosso trabalho abrange diversas áreas — incluindo hardware, sistemas embarcados, Linux, segurança da informação, PKI, automação, infraestrutura e pesquisa aplicada — mas a missão permanece a mesma: desenvolver soluções práticas, documentar decisões técnicas e compartilhar conhecimento para que outras pessoas possam estudá-lo, reproduzi-lo e expandi-lo.

Acreditamos que o conhecimento de engenharia se torna mais valioso quando é documentado, reproduzível e compartilhado.

</details>

## Engineering Values

The projects in this workspace are diverse, but they are usually guided by the same engineering values.

- Simplicity is preferred over unnecessary complexity.
- Technical decisions are documented, not just their outcomes.
- Projects are shared as they evolve.
- Engineering history is preserved whenever it provides context or future value.
- Structure exists to support engineering, never the other way around.
- Practical solutions come before elegant abstractions.

These values are descriptive rather than prescriptive. They reflect the experience accumulated across different projects, not a checklist applied to every repository.

<details>
<summary><strong>PT-BR</strong></summary>

Os projetos deste workspace são bastante diferentes entre si, mas normalmente são guiados pelos mesmos valores de engenharia.

- Preferimos simplicidade à complexidade desnecessária.
- Documentamos decisões técnicas, não apenas seus resultados.
- Compartilhamos projetos à medida que evoluem.
- Preservamos o histórico de engenharia sempre que ele agrega contexto ou valor futuro.
- A estrutura existe para servir à engenharia, nunca o contrário.
- Soluções práticas vêm antes de abstrações elegantes.

Esses valores são descritivos, não prescritivos. Eles refletem a experiência acumulada em diferentes projetos, e não um checklist aplicado a todos os repositórios.

</details>

## Engineering Philosophy

We believe engineering is an iterative process.

Projects rarely begin as complete platforms. Most start as small experiments, evolve through practical use, and mature one decision at a time.

We strive to keep repositories as simple as possible, documentation proportional to each project's complexity, and engineering decisions easy to understand.

Nothing in this workspace exists simply because "every project should have one." Every component, document, script, and directory should exist because it serves a practical purpose.

<details>
<summary><strong>PT-BR</strong></summary>

Acreditamos que engenharia é um processo iterativo.

Projetos raramente nascem como plataformas completas. A maioria começa como pequenos experimentos, evolui por meio do uso prático e amadurece uma decisão de cada vez.

Buscamos manter os repositórios tão simples quanto possível, a documentação proporcional à complexidade de cada projeto e as decisões de engenharia fáceis de compreender.

Nada neste workspace existe apenas porque "todo projeto deveria ter". Cada componente, documento, script e diretório deve existir porque possui um propósito prático.

</details>

## Workspace Architecture

The workspace is organized by engineering domain rather than by technology or programming language. Each directory groups projects with similar objectives, allowing both the projects and the workspace to evolve naturally as new ideas, technologies, and research emerge.

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

The structure is intentionally simple and may evolve as projects mature or new engineering domains are introduced.

<details>
<summary><strong>PT-BR</strong></summary>

O workspace é organizado por domínio de engenharia, e não por tecnologia ou linguagem de programação. Cada diretório reúne projetos com objetivos semelhantes, permitindo que tanto os projetos quanto o próprio workspace evoluam naturalmente à medida que novas ideias, tecnologias e pesquisas surgem.

A estrutura é intencionalmente simples e pode evoluir conforme os projetos amadurecem ou novos domínios de engenharia sejam incorporados.

</details>

## License

This workspace is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

Unless explicitly stated otherwise within an individual project, all source code, documentation, hardware designs, schematics, and other assets are distributed under the terms of the GPL-3.0.

See the [`LICENSE`](LICENSE) file for the complete license text.

<details>
<summary><strong>PT-BR</strong></summary>

Este workspace está licenciado sob a **GNU General Public License v3.0 (GPL-3.0)**.

Salvo indicação explícita em contrário dentro de um projeto específico, todo o código-fonte, documentação, projetos de hardware, esquemáticos e demais ativos são distribuídos sob os termos da GPL-3.0.

Consulte o arquivo [`LICENSE`](LICENSE) para o texto completo da licença.

</details>

---

Copyright (C) 2026 **bressix LABs**
