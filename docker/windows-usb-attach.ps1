<#
 Collega un adattatore USB-seriale al container in-out (Docker Desktop su Windows).
 Avviato all'accesso dall'operazione pianificata "In-Out USB seriale" creata da
 installer-docker.ps1. Attende che Docker sia pronto e mantiene l'adattatore
 collegato a WSL2 (anche se viene scollegato e ricollegato).

 Uso manuale:  .\docker\windows-usb-attach.ps1 -HardwareId 0403:6001
#>
param(
    [Parameter(Mandatory = $true)][string]$HardwareId
)

$logFile = Join-Path $PSScriptRoot "..\docker-data\usb-attach.log"
function Log($m) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m"
    try { Add-Content -Path $logFile -Value $line } catch {}
}

Log "avvio (hardware-id $HardwareId)"
while ($true) {
    # Attende che Docker Desktop (e quindi WSL2) sia in esecuzione
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        Start-Sleep -Seconds 10
        continue
    }
    Log "collego l'adattatore a WSL"
    # --auto-attach resta in esecuzione e ricollega il dispositivo se viene staccato
    $out = usbipd attach --wsl --hardware-id $HardwareId --auto-attach 2>&1
    Log "usbipd terminato: $out"
    Start-Sleep -Seconds 10
}
