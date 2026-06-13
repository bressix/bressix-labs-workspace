<p align="center">
  <img src="https://raw.githubusercontent.com/bressix/bressix/main/bressix_LABs_01.png" alt="bressix LABs" width="500"/>
</p>

# bressix-labs-workspace

> ⚠️ **WORK IN PROGRESS / EM CONSTRUÇÃO**
>
> **EN:** This workspace is currently undergoing structural setup. Repository architecture, documentation, and security sanitization are being pushed incrementally as time permits. Code modules will be available soon.
> 
> **PT-BR:** Este workspace está em fase de estruturação inicial. A arquitetura dos repositórios, documentação e a higienização de segurança estão sendo subidas gradualmente conforme disponibilidade de tempo. Os módulos de código estarão disponíveis em breve.

<details>
<summary>🇺🇸 English Version (Click to expand)</summary>

Centralized development workspace for **bressix LABs**. This repository unifies our core operational modules, automation scripts, device modifications, and hardware laboratory environments organized by engineering disciplines.

## Workspace Structure

* ### [3D/](./3D/)
    Mechanical designs, structural enclosures, parametric modeling using OpenSCAD and FreeCAD, and functional 3D printing assets.
* ### [audio/](./audio/)
    Audio studies — Digital Signal Processing (DSP), DACs, advanced sound server routing (PipeWire/ALSA), audio hardware patches, acoustic tuning, enclosures, drivers, and crossover networks.
* ### [firmware/](./firmware/)
    Pure microcontroller software and low-level logical development (CH552, ESP32, AVR, etc.).
    * `bressix-DIV/`: Adaptation of BruceFirmware leveraging the hardware capabilities of the ESP32-DIV (cifertech).
    * `diy-mood-weather/`: Telemetry firmware for local environment and atmospheric nodes.
    * `esp32-cftv-tool/`: Utility firmware for network diagnosis and CCTV deployment support.
    * `pid-temp-arduino/`: Closed-loop Proportional-Integral-Derivative thermal controller.
* ### [hardware/](./hardware/)
    Schematics, pinout layouts, I2C/SPI bus mapping, and raw hardware architecture specs.
    * `bressix-DIV/`: Hardware redesign and analysis of the ESP32-DIV (cifertech).
    * `diy-mood-weather/`: Board schematics and sensor bus layouts for telemetry and local environmental nodes.
    * `esp32-cftv-tool/`: Hardware schematics and pinout design for network diagnosis and CCTV deployment support.
    * `pid-temp-arduino/`: Shield layout and pin mapping for the closed-loop PID thermal controller.
* ### [system-hacking-n-tuning/](./system-hacking-n-tuning/)
    OS deep tuning, embedded Linux customization, bootloader modifications, kernels, and driver patches.
    * `chromebook4-samsung/`: Debian Stable performance optimizations, zRAM fine-tuning, and stable desktop environment setup.
    * `pineapple-termidor-mod/`: Custom system images based on wifi-pineapple-cloner (xchwarze) tailored to run on a TP-Link TL-WDR4300 (N750).
    * `positivo-duo-q432a/`: OS-level automation scripts for native hardware sensor and accelerometer integration.
* ### [tls-n-automation-scripts/](./tls-n-automation-scripts/)
    Infrastructure automation, advanced cryptographic utilities, PKI management, and automated corporate data auditing.
    * `cnpj_query/`: Resilient local CNPJ validation and multi-API fallback parsing tool ecosystem.
    * `globalsign-atlas-api/`: Backend integration modules for GlobalSign's modern Atlas API ecosystem.
    * `globalsign-gcc-api/`: Integration scripts and logic interacting with GlobalSign's legacy GCC API.
    * `ssl-tls-auditing/`: Advanced ciphersuite scanning, validation chain compliance, and verification scripts.
    * `tls-crt/`: Toolsets for manipulating, extracting, validating, and converting X.509 certificates and keys.
    * `tls-discovery/`: Automation routines for network-wide TLS/SSL credential scanning and asset identification.
    * `tls-scripts/`: Core cryptographic helpers, validation triggers, and tactical infrastructure playbooks.
* ### [WIP/](./WIP/)
    Generic playground for experimental work in progress, memory dumps, raw reversing notes, and unclassified test scripts.

---
</details>

<details>
<summary>🇧🇷 Versão em Português (Clique para expandir)</summary>

Workspace centralizado de desenvolvimento da **bressix LABs**. Este repositório unifica nossos módulos operacionais, scripts de automação, modificações de sistemas e laboratórios de engenharia organizados de forma modular por disciplinas tecnológicas.

## Estrutura do Workspace

* ### [3D/](./3D/)
    Designs mecânicos, cases estruturais, modelagens parametrizadas em OpenSCAD e FreeCAD e peças para impressão 3D funcional.
* ### [audio/](./audio/)
    Estudo do áudio - Processamento digital de sinal (DSP), DAC, roteamento avançado de servidores de som (PipeWire/ALSA), patches para hardware de áudio, tunagem acústica, caixas, drivers e divisores de frequência.
* ### [firmware/](./firmware/)
    Códigos nativos para microcontroladores e desenvolvimento lógico de baixo nível (CH552, ESP32, AVR, etc.).
    * `bressix-DIV/`: Adaptação do BruceFirmware para utilizar o poder de hardware do ESP32-DIV (cifertech).
    * `diy-mood-weather/`: Firmware de telemetria e gerenciamento de nodes ambientais locais.
    * `esp32-cftv-tool/`: Firmware utilitário para diagnóstico de redes e apoio à infraestrutura de CFTV.
    * `pid-temp-arduino/`: Controlador térmico em malha fechada utilizando algoritmo Proporcional-Integral-Derivativo.
* ### [hardware/](./hardware/)
    Esquemas elétricos, diagramas de pinagem, mapeamento de barramentos (I2C/SPI) e especificações físicas de placas.
    * `bressix-DIV/`: Releitura do hardware do ESP32-DIV (cifertech).
    * `diy-mood-weather/`: Hardware de telemetria e pinagem de barramentos de sensores do node ambiental local.
    * `esp32-cftv-tool/`: Hardware utilitário para diagnóstico de redes e apoio à infraestrutura de CFTV.
    * `pid-temp-arduino/`: Esquema de conexões e mapeamento de pinos do controlador térmico em malha fechada PID.
* ### [system-hacking-n-tuning/](./system-hacking-n-tuning/)
    Modificações profundas de sistemas operacionais, customização de firmwares baseados em Linux, kernels e patches de drivers.
    * `chromebook4-samsung/`: Otimizações de desempenho para Debian Stable, ajustes finos de zRAM e setup de ambiente gráfico estável.
    * `pineapple-termidor-mod/`: Imagens customizadas com base wifi-pineapple-cloner (xchwarze) para rodar em um TP-Link TL-WDR4300 (N750).
    * `positivo-duo-q432a/`: Automações em nível de sistema para tratamento nativo de sensores e acelerômetro do hardware.
* ### [tls-n-automation-scripts/](./tls-n-automation-scripts/)
    Automações de infraestrutura, utilitários criptográficos avançados, gerenciamento de PKI e auditoria automatizada de dados corporativos.
    * `cnpj_query/`: Ecossistema do consultador resiliente com validação algorítmica local e fallback inteligente de APIs.
    * `globalsign-atlas-api/`: Módulos de integração e consumo estruturado da API moderna Atlas da GlobalSign.
    * `globalsign-gcc-api/`: Scripts de integração com as APIs legadas do sistema GCC da GlobalSign.
    * `ssl-tls-auditing/`: Varredura avançada de ciphersuites, checagem de cadeias de certificação e scripts de compliance.
    * `tls-crt/`: Utilitários para manipulação, extração, validação e conversão de chaves e certificados X.509.
    * `tls-discovery/`: Rotinas de automação para varredura de ativos e descoberta de credenciais TLS/SSL na rede.
    * `tls-scripts/`: Auxiliares criptográficos centrais, gatilhos de validação e playbooks táticos de infraestrutura.
* ### [WIP/](./WIP/)
    Laboratório genérico para projetos em andamento (Work In Progress), dumps de memórias, rascunhos rápidos e testes não classificados.

---
</details>

## Security Policy / Política de Segurança
No private keys, production certificates, passwords, or active API tokens are stored within this repository. Local development environments must rely on `.env` files or isolated header files built from the provided `*.example` configurations.

*Nenhuma chave privada, certificado de produção, senhas ou tokens ativos de API são armazenados neste repositório. Ambientes locais de desenvolvimento devem utilizar arquivos `.env` ou headers isolados baseados nas estruturas de exemplo `*.example` fornecidas.*
