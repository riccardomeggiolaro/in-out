<#
 Passa i dispositivi USB al container in-out (Docker Desktop su Windows, via usbipd-win).
 Avviato all'accesso dall'operazione pianificata "In-Out USB" creata da installer-docker.ps1.

 Modalita':
   -All                      tutti i dispositivi USB collegati, TRANNE quelli che Windows
                             usa come tastiera, mouse, touch/HID, rete o Bluetooth
                             (passarli al container li toglierebbe a Windows)
   -HardwareIds 0403:6001    solo i dispositivi indicati (VID:PID, separati da virgola)
   -Exclude 046d:c52b        VID:PID da non passare mai (in aggiunta alle esclusioni automatiche)

 Ogni 15 secondi controlla i dispositivi: quelli nuovi o ricollegati vengono passati
 al container automaticamente. Carica anche i driver USB-seriale (FTDI, CH341, CP210x,
 PL2303, CDC-ACM) nel kernel di WSL2, dove sono moduli non caricati di default:
 senza di essi /dev/ttyUSB0 non viene creato. Log in docker-data\usb-attach.log.

 Uso manuale:  .\docker\windows-usb-attach.ps1 -All
#>
param(
    [switch]$All,
    [string]$HardwareIds = "",
    [string]$Exclude = ""
)

$logFile = Join-Path $PSScriptRoot "..\docker-data\usb-attach.log"
function Log($m) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m"
    try { Add-Content -Path $logFile -Value $line } catch {}
}

function Parse-Ids($text) {
    @($text -split '[,; ]+' | Where-Object { $_ -match '^[0-9a-fA-F]{4}:[0-9a-fA-F]{4}$' } | ForEach-Object { $_.ToLower() })
}

$wanted = Parse-Ids $HardwareIds
$excluded = Parse-Ids $Exclude
if (-not $All -and $wanted.Count -eq 0) {
    Log "nessun dispositivo indicato: usa -All oppure -HardwareIds"
    exit 1
}

# Classi Windows da non togliere mai al PC
$protectedClasses = @("Keyboard", "Mouse", "HIDClass", "Net", "Bluetooth")

function Get-ProtectedIds {
    $ids = @{}
    Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
        Where-Object { $protectedClasses -contains $_.Class } |
        ForEach-Object {
            if ($_.InstanceId -match 'VID_([0-9A-F]{4})&PID_([0-9A-F]{4})') {
                $ids["$($Matches[1]):$($Matches[2])".ToLower()] = $_.FriendlyName
            }
        }
    return $ids
}

# Carica i driver USB-seriale nel kernel di WSL2 (namespace della VM di Docker Desktop)
$helperImage = "alpine:3.20"
function Load-SerialDrivers {
    $out = docker run --rm --privileged --pid=host $helperImage nsenter -t 1 -m -u -n -i sh -c "modprobe -a usbserial ftdi_sio ch341 cp210x pl2303 cdc_acm 2>&1; echo ok" 2>&1
    Log "driver USB-seriale: $out"
}

Log "avvio (modalita': $(if ($All) { 'tutti' } else { $wanted -join ',' }); esclusi: $($excluded -join ','))"
$skipLogged = @{}
$driversLoaded = $false

while ($true) {
    # Docker Desktop (e quindi WSL2) deve essere in esecuzione
    docker info *> $null
    if ($LASTEXITCODE -ne 0) { $driversLoaded = $false; Start-Sleep -Seconds 10; continue }
    # Al primo avvio e dopo ogni riavvio di Docker Desktop i moduli vanno ricaricati
    if (-not $driversLoaded) { Load-SerialDrivers; $driversLoaded = $true }

    try {
        $state = (usbipd state | Out-String) | ConvertFrom-Json
    } catch {
        Log "usbipd state non riuscito: $_"
        Start-Sleep -Seconds 15; continue
    }
    $protected = if ($All) { Get-ProtectedIds } else { @{} }

    foreach ($dev in $state.Devices) {
        if (-not $dev.BusId) { continue }                 # non collegato fisicamente
        if ($dev.ClientIPAddress) { continue }            # gia' passato al container
        if ($dev.InstanceId -notmatch 'VID_([0-9A-F]{4})&PID_([0-9A-F]{4})') { continue }
        $id = "$($Matches[1]):$($Matches[2])".ToLower()

        $reason = $null
        if ($excluded -contains $id) { $reason = "escluso" }
        elseif (-not $All -and $wanted -notcontains $id) { continue }
        elseif ($All -and $protected.ContainsKey($id)) { $reason = "usato da Windows ($($protected[$id]))" }
        if ($reason) {
            if (-not $skipLogged.ContainsKey($id)) { Log "salto $id $($dev.Description): $reason"; $skipLogged[$id] = $true }
            continue
        }

        if (-not $dev.PersistedGuid) {
            $out = usbipd bind --busid $dev.BusId 2>&1
            Log "bind $id $($dev.Description) [$($dev.BusId)]: $out"
        }
        $out = usbipd attach --wsl --busid $dev.BusId 2>&1
        Log "attach $id $($dev.Description) [$($dev.BusId)]: $(if ($LASTEXITCODE -eq 0) { 'ok' } else { $out })"
        $attached = $true
    }
    # Un nuovo dispositivo puo' richiedere un driver non ancora caricato
    if ($attached) { Load-SerialDrivers; $attached = $false }
    Start-Sleep -Seconds 15
}
