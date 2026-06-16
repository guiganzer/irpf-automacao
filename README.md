---

# 🤖 RPA - Automação IRPF 2026 (Visão Computacional)

Um robô de automação de processos (RPA) de superfície projetado para interagir com o aplicativo desktop do IRPF 2026 da Receita Federal Brasileira. Construído em Python, o sistema combina simulação de hardware e visão computacional para gerar, em lote e de forma desassistida, declarações e recibos em PDF.

O projeto foca em alta resiliência, utilizando padrões de engenharia como **Self-Healing** (auto-cura em caso de travamentos da JVM), **Resume State** (retomada de onde parou em caso de queda de energia) e isolamento de threads entre a Interface Gráfica (GUI) e o *Worker* de automação.

---

## ✨ Principais Funcionalidades

* **Extração Automática de Base:** Lógica de *web scraping* embutida (via BeautifulSoup) para converter relatórios locais HTML do IRPF em listas de processamento `.txt` limpas, validando previamente se a declaração possui recibo gerado.
* **Visão Computacional (OpenCV):** Navegação baseada em *Template Matching* multi-monitor e multi-escala, garantindo que o robô encontre botões dinâmicos independentemente de onde a janela renderize.
* **Lógica de Retomada (Resumability):** Antes de iniciar qualquer interação de UI, o sistema verifica o disco. Se a declaração ou recibo do contribuinte já existir no diretório de saída, o robô pula o registro silenciosamente, economizando tempo e evitando duplicidade.
* **Self-Healing & Proteção contra Poison Pill:** Limite de falhas configurável por CPF/Nome. Se a interface Java travar, o processo é encerrado de forma forçada na raiz do SO (`taskkill` na árvore do processo) e reiniciado automaticamente, retomando do ponto exato da quebra.
* **Interface Gráfica (GUI):** Painel de controle desenvolvido em `Tkinter` com injeção de logs em tempo real, permitindo a configuração visual de caminhos de rede e diretórios de saída.
* **Persistência de Configurações:** Parâmetros globais salvos automaticamente em um arquivo `config.json`.

---

## 🛠️ Stack Tecnológica

* **Python 3.13+**
* **OpenCV (`opencv-python-headless`)**: Engine de visão computacional.
* **PyAutoGUI / Pynput / PyGetWindow**: Controladores de I/O de hardware e API do Windows.
* **BeautifulSoup4**: *Parser* de relatórios HTML.
* **Pydantic**: Tipagem rigorosa para classes de modelo (*Visual Assets*).
* **MSS**: Captura de tela nativa de ultra-baixa latência.
* **Tkinter**: *Framework* nativo para a Interface Gráfica.


## 📂 Estrutura do Projeto
```text
/
├── assets/                       # Assets visuais obrigatórios e TXT de saída
│   ├── transmitidas.html         # Relatório base de nomes (input opcional do usuário)
│   ├── transmitidas.txt          # Relatório base de nomes processado pelo BeautifulSoup4
│   └── imprimir.png              # Template do radio button de impressão
|   └── titulo_recibos.png        # Template de cabeçalho da janela de recibos
|   └── botao_ok_ativo.png        # Botão OK em status ativo
|   └── botao_ok_bloqueado.png    # Botão OK em status bloqueado
├── gui.py                        # Entrypoint e Thread da Interface (Main)
├── rpa_pipeline.py               # Orquestrador do Loop e Regras de Negócio
├── config_manager.py             # Manipulação do arquivo JSON de estado
├── vision.py                     # Motor matemático do OpenCV
├── models.py                     # Contratos de dados (Pydantic)
├── hardware.py                   # Isolamento das libs de mouse/teclado
├── app_manager.py                # Gerência do ciclo de vida de Processos do SO
├── html_processor.py             # Limpeza e extração de dados
└── build.py                      # Script de empacotamento com PyInstaller
```

## ⚙️ Instalação e Execução (Modo Desenvolvedor)

Clone o repositório, entre na pasta, e configure seu ambiente virtual:

1. Inicialize um ambiente virtual 
`uv venv && uv init`
2. Ative o ambiente criado (no windows)
```text
.\.venv\Scripts\activate.ps1  [powershell]
.venv\Scripts\activate        [cmd]
```
2. Instale as dependências:
`uv sync`
3. Execute o orquestrador:
`python gui.py`

---

## 📦 Build para Produção (Executável)

Para compilar o projeto em um executável `.exe` independente (Standalone), sem exigir a instalação do Python na máquina do cliente final, utilize o script de build fornecido:

`python build.py`

**Instruções de Deploy:**
O artefato final será gerado na pasta `dist/`. Para entregar a solução, você deve garantir que a pasta `assets` seja enviada no mesmo diretório do arquivo `.exe`. A arquitetura do sistema bloqueia a execução e gera um alerta caso a pasta de referências visuais não seja encontrada em tempo de execução.

---

## ⚠️ Avisos Importantes de Infraestrutura

* **Escala do Windows (DPI):** Sistemas baseados em OCR e *Template Matching* sofrem interferência direta da escala de exibição do Windows. A máquina onde o robô rodar deve estar configurada com **Escala e Layout em 100%**.
* **Sessão Ativa:** Por interagir com chamadas de hardware de baixo nível (Mouse/Teclado), o robô exige uma sessão de usuário ativa (desbloqueada) no Windows. Para execuções em Máquinas Virtuais (VMs), configure o *Auto-Login* e utilize ferramentas como VNC Server rodando como serviço para monitoramento desassistido.