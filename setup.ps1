# Instalação do Mercado Livre Tracker
Write-Host "🚀 Instalando Mercado Livre Tracker..." -ForegroundColor Cyan

# 1. Instala dependências Python
Write-Host "`n📦 Instalando dependências..." -ForegroundColor Yellow
uv pip install httpx lxml cssselect playwright win10toast

# 2. Instala navegador do Playwright
Write-Host "`n🌐 Instalando Chromium..." -ForegroundColor Yellow
uv run python -m playwright install chromium

# 3. Cria arquivo products.txt de exemplo
if (-not (Test-Path "products.txt")) {
    Write-Host "`n📝 Criando products.txt de exemplo..." -ForegroundColor Yellow
    @"
# Adicione seus links do Mercado Livre abaixo (um por linha)
# Exemplo:
# https://www.mercadolivre.com.br/produto-exemplo/p/MLB12345678
"@ | Out-File -FilePath products.txt -Encoding UTF8
}

# 4. Cria pasta data
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
}

# 5. Instala tarefa agendada
Write-Host "`n📅 Instalando tarefa agendada..." -ForegroundColor Yellow
uv run python -m src.install_service install

Write-Host "`n✅ Instalação concluída!" -ForegroundColor Green
Write-Host "📌 Adicione seus links em products.txt"
Write-Host "📊 Gere o dashboard: uv run python -m src.dashboard"
Write-Host "📋 Verifique a tarefa: uv run python -m src.install_service check"
