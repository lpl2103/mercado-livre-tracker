# 📊 Mercado Livre Price Tracker

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Monitor de preços inteligente para produtos do Mercado Livre. Coleta preços automaticamente, salva histórico e gera dashboard interativo com gráficos. Notifica quando o preço cai ou as parcelas aumentam.

<p align="center">
  <img src="https://img.shields.io/badge/Status-Stable-brightgreen" alt="Status">
  <img src="https://img.shields.io/badge/Plataforma-Windows-blue" alt="Windows">
</p>

---

## ✨ Funcionalidades

- 🔍 **Coleta automática** de preço, parcelas e frete
- 📊 **Dashboard HTML** com gráficos interativos (Chart.js)
- 🌓 **Tema claro/escuro** (persiste no navegador)
- 📱 **Responsivo** - funciona no celular
- 📈 **Histórico de preços** salvo em JSON
- 🔔 **Notificações** Windows + Email quando o preço cai
- 📦 **Multi-produto** - monitore quantos quiser
- ⏰ **Execução automática** via tarefa agendada do Windows
- 🚀 **Inicia com o sistema** (modo silencioso)

---

## 🛠️ Stack

| Tecnologia | Uso |
|------------|-----|
| Python 3.11+ | Linguagem principal |
| Playwright | Navegador headless anti-detecção |
| lxml + CSSSelect | Parse HTML |
| httpx | Requisições HTTP (fallback) |
| Chart.js | Gráficos interativos |
| win10toast | Notificações nativas do Windows |

---

## 📋 Pré-requisitos

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **uv** - Gerenciador de pacotes rápido
- **Windows 10/11** (para notificações nativas)
- **Git** (opcional, para clonar)

### Instalar uv

```powershell
pip install uv
```

## 🚀 Instalação
### 1. Clone o projeto

```powershell
git clone https://github.com/lpl2103/mercado-livre-tracker.git
cd mercado-livre-tracker
```
### 2. Execute o setup automático
```powershell
.\setup.ps1
```

O setup instala todas as dependências, o navegador Chromium e cria os arquivos necessários.

### 3. Adicione seus produtos

Edite o arquivo products.txt com os links dos produtos que deseja monitorar:
text

\# Um link por linha - linhas com # são comentários

\ # Caixa de som JBL
\ https://www.mercadolivre.com.br/caixa-de-som-bluetooth-jbl-xtreme-5-preta/up/MLBU4052365012

\ # Tênis Olympikus
\ https://www.mercadolivre.com.br/tenis-olympikus-corre-5/p/MLB12345678

### 4. Teste manualmente
```powershell
uv run python -m src.scheduler
```

Deixe rodar por alguns ciclos (Ctrl+C para parar) para gerar os primeiros dados.
### 5. Gere o dashboard
```powershell
uv run python -m src.dashboard
start data/dashboard.html
```

### 6. Instale como serviço (inicia com Windows)
```powershell
uv run python -m src.install_service install
```

## 📖 Uso
Comandos principais
Comando	Descrição
uv run python -m src.scheduler	Inicia o monitor manualmente
uv run python -m src.dashboard	Gera o dashboard HTML
uv run python -m src.install_service install	Instala tarefa agendada
uv run python -m src.install_service uninstall	Remove tarefa agendada
uv run python -m src.install_service check	Verifica status da tarefa
uv run python -m src.install_service run	Inicia a tarefa agora
Dashboard

Abra data/dashboard.html no navegador para ver:

    📈 Gráfico de preço - evolução ao longo do tempo

    📊 Gráfico de parcelas - variação da quantidade

    🔄 Dropdown para alternar entre produtos

    📋 Tabela histórica com todas as coletas

    🌙 Botão de tema claro/escuro

# Notificações

O tracker envia notificações quando:

    💰 O preço diminui

    📊 A quantidade de parcelas aumenta

Para configurar email, edite o scheduler.py:
```python
email_config={
    "from": "seuemail@gmail.com",
    "to": "destinatario@gmail.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "seuemail@gmail.com",
    "password": "sua-senha-app"
}
```

## 📁 Estrutura do Projeto
```text

mercado-livre-tracker/
├── 📄 pyproject.toml          # Dependências e metadados
├── 📄 setup.ps1               # Script de instalação automática
├── 📄 products.txt            # Links dos produtos (você edita)
├── 📄 README.md               # Este arquivo
├── 📁 src/
│   ├── 🕷️ crawler.py           # Extração de dados (Playwright)
│   ├── 💾 storage.py           # Persistência em JSON
│   ├── 🔔 notifier.py          # Notificações Windows + Email
│   ├── ⏰ scheduler.py         # Loop principal (30 min)
│   ├── 📊 dashboard.py         # Gerador de relatório HTML
│   └── ⚙️ install_service.py   # Tarefa agendada do Windows
└── 📁 data/
    ├── 📊 products.json        # Banco de dados (histórico)
    └── 📄 dashboard.html       # Relatório gerado
```

## ⚙️ Configuração Avançada
Intervalo de coleta

Edite scheduler.py:
```python

scheduler = TrackerScheduler.from_file(
    filepath=Path("products.txt"),
    interval_minutes=30,
)
```

# Modo silencioso (sem janela)

O install_service.py já usa pythonw.exe por padrão.
Múltiplos produtos

Adicione quantos links quiser em products.txt. O dashboard mostra todos no dropdown.
🐛 Troubleshooting
Problema	Solução
ModuleNotFoundError	Execute uv pip install -e .
Verificação do ML	Abra o link no navegador e resolva o captcha manualmente
Preço errado	Verifique se o produto usa o layout padrão do ML
Tarefa não inicia	Execute como Administrador

# 📄 Licença

MIT © 2026
<p align="center"> <sub>Feito com ❤️ e muito ☕</sub> </p>
