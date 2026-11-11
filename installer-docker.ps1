<#
==============================================================
 Installer Docker per In-Out su Windows (Docker Desktop + WSL2)

 Uso (PowerShell come Amministratore, dalla cartella del progetto):
     Set-ExecutionPolicy -Scope Process Bypass
     .\installer-docker.ps1

 Cosa fa:
   1. verifica/installa WSL2 e Docker Desktop (via winget)
   2. crea .env con cartelle dati locali e password CUPS casuale
   3. apre le porte nel firewall di Windows
   4. builda l'immagine e avvia il container
   5. (opzionale) installa usbipd-win per le porte seriali USB
==============================================================
#>
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Info($m)  { Write-Host "[INFO] $m" -ForegroundColor Green }
function Warn($m)  { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m)  { Write-Host "[ERROR] $m" -ForegroundColor Red; exit 1 }

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { Fail "Esegui PowerShell come Amministratore" }

# --- 1. WSL2 e Docker Desktop ---------------------------------
$wslOk = $false
try { wsl --status *> $null; $wslOk = ($LASTEXITCODE -eq 0) } catch {}
if (-not $wslOk) {
    Info "Installazione di WSL2..."
    wsl --install --no-distribution
    Warn "WSL2 installato: RIAVVIA il PC e rilancia questo script."
    exit 0
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Fail "winget non disponibile: installa Docker Desktop da https://www.docker.com/products/docker-desktop/ e rilancia lo script"
    }
    Info "Installazione di Docker Desktop..."
    winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    Warn "Docker Desktop installato: RIAVVIA il PC, apri Docker Desktop una volta (accetta i termini) e rilancia questo script."
    exit 0
}

Info "Attendo che Docker sia pronto..."
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    docker info *> $null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    if ($i -eq 0) {
        $dd = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dd) { Start-Process $dd }
    }
    Start-Sleep -Seconds 5
}
if (-not $ready) { Fail "Docker non risponde: apri Docker Desktop e rilancia lo script" }

# --- 2. File .env ---------------------------------------------
if (-not (Test-Path ".env")) {
    $chars = [char[]]"ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
    $cupsPassword = -join (1..12 | ForEach-Object { $chars | Get-Random })
    @"
# Generato da installer-docker.ps1
COMPOSE_FILE=docker-compose.yml;docker-compose.windows.yml
TZ=Europe/Rome

# Cartelle persistenti (relative alla cartella del progetto)
IN_OUT_CONFIG_DIR=./docker-data/config
IN_OUT_DATA_DIR=./docker-data/data
IN_OUT_CUPS_DIR=./docker-data/cups

# Porte pubblicate sul PC Windows
IN_OUT_HTTP_PORT=80
IN_OUT_CUPS_PORT=631

CUPS_ENABLED=1
CUPS_ADMIN_USER=admin
CUPS_ADMIN_PASSWORD=$cupsPassword
"@ | Set-Content -Path ".env" -Encoding ascii
    Info "Creato .env (password CUPS admin: $cupsPassword)"
} else {
    Info "Uso il file .env esistente"
}

$envMap = @{}
Get-Content ".env" | Where-Object { $_ -match '^\s*([A-Z_]+)=(.*)$' } | ForEach-Object { $envMap[$Matches[1]] = $Matches[2].Trim() }
$httpPort = if ($envMap["IN_OUT_HTTP_PORT"]) { $envMap["IN_OUT_HTTP_PORT"] } else { "80" }
$cupsPort = if ($envMap["IN_OUT_CUPS_PORT"]) { $envMap["IN_OUT_CUPS_PORT"] } else { "631" }

New-Item -ItemType Directory -Force -Path "docker-data\config","docker-data\data","docker-data\cups" | Out-Null

# --- 3. Firewall ----------------------------------------------
foreach ($rule in @(@{Name="In-Out HTTP"; Port=$httpPort}, @{Name="In-Out CUPS"; Port=$cupsPort})) {
    if (-not (Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName $rule.Name -Direction Inbound -Protocol TCP -LocalPort $rule.Port -Action Allow | Out-Null
        Info "Regola firewall creata: $($rule.Name) (TCP $($rule.Port))"
    }
}

# --- 4. Build e avvio -----------------------------------------
Info "Build dell'immagine e avvio del container (la prima volta richiede alcuni minuti)..."
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { Fail "docker compose non e' riuscito: controlla l'output sopra" }

Start-Sleep -Seconds 5
$running = docker inspect -f "{{.State.Running}}" in-out 2>$null
if ($running -ne "true") { Fail "Il container non risulta in esecuzione: docker compose logs" }

# --- 5. Porte seriali USB (opzionale) -------------------------
if (-not (Get-Command usbipd -ErrorAction SilentlyContinue)) {
    $answer = Read-Host "Installare usbipd-win per usare adattatori USB-seriale nel container? (s/n)"
    if ($answer -match '^[Ss]') {
        winget install -e --id dorssel.usbipd-win --accept-package-agreements --accept-source-agreements
        Warn "Per collegare un adattatore: usbipd list ; usbipd bind --busid <ID> ; usbipd attach --wsl --busid <ID> --auto-attach"
    }
}

Write-Host "========================================"
Write-Host "Installazione completata!"
Write-Host "========================================"
Write-Host "In-Out:  http://localhost:$httpPort/"
Write-Host "CUPS:    http://localhost:$cupsPort/  (credenziali nel file .env)"
Write-Host ""
Write-Host "Comandi utili (da questa cartella):"
Write-Host "  docker compose logs -f      log"
Write-Host "  docker compose restart      riavvio"
Write-Host "  docker compose down         stop"
Write-Host "  git pull; docker compose up -d --build   aggiornamento"
Write-Host ""
Write-Host "Per l'avvio automatico: Docker Desktop > Settings > General > 'Start Docker Desktop when you sign in'"
