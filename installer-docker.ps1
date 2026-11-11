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

# --- 5. Dispositivi USB nel container (seriali, ecc.) ---------
Write-Host ""
Write-Host "Dispositivi USB da passare al container (adattatori USB-seriale, lettori, ...):"
Write-Host "  [T] tutti, tranne quelli che Windows usa come tastiera, mouse, touch, rete, Bluetooth (consigliato)"
Write-Host "  [S] solo dispositivi specifici (VID:PID)"
Write-Host "  [N] nessuno"
$mode = (Read-Host "Scelta [T/S/N]").Trim().ToUpper()
if ($mode -eq "") { $mode = "T" }
if ($mode -eq "T" -or $mode -eq "S") {
    if (-not (Get-Command usbipd -ErrorAction SilentlyContinue)) {
        Info "Installazione di usbipd-win..."
        winget install -e --id dorssel.usbipd-win --accept-package-agreements --accept-source-agreements
        $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    }
    if (-not (Get-Command usbipd -ErrorAction SilentlyContinue)) {
        Warn "usbipd non trovato: riapri PowerShell come Amministratore e rilancia lo script"
    } else {
        usbipd list
        if ($mode -eq "T") {
            $usbArgs = "-All"
            $exclude = (Read-Host "VID:PID da NON passare mai, separati da virgola (invio = nessuno)").Trim()
            if ($exclude) { $usbArgs += " -Exclude $exclude" }
        } else {
            $ids = ""
            while ($ids -notmatch '^[0-9a-fA-F]{4}:[0-9a-fA-F]{4}([ ,;]+[0-9a-fA-F]{4}:[0-9a-fA-F]{4})*$') {
                $ids = (Read-Host "VID:PID dei dispositivi, separati da virgola (es. 0403:6001)").Trim()
            }
            $usbArgs = "-HardwareIds $ids"
        }

        # Operazione pianificata: passa i dispositivi a ogni accesso e quando vengono ricollegati
        Unregister-ScheduledTask -TaskName "In-Out USB seriale" -Confirm:$false -ErrorAction SilentlyContinue
        $taskName = "In-Out USB"
        $script = Join-Path $PSScriptRoot "docker\windows-usb-attach.ps1"
        $action = New-ScheduledTaskAction -Execute "powershell.exe" `
            -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`" $usbArgs"
        $trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
        $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
        $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
        Start-ScheduledTask -TaskName $taskName
        Info "Operazione pianificata '$taskName' creata e avviata ($usbArgs)"

        Start-Sleep -Seconds 30
        $devs = docker exec in-out sh -c "ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null"
        if ($devs) {
            Info "Seriali visibili nel container: $devs (usa questi nomi nella configurazione di pese/RFID)"
        } else {
            Warn "Nessuna seriale ancora visibile nel container. Controlla docker-data\usb-attach.log e riprova tra poco con:"
            Warn "  docker exec in-out ls /dev/ttyUSB* /dev/ttyACM*"
        }
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
