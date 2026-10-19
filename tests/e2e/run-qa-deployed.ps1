<#
.SYNOPSIS
    QUICKPATCH — Ejecutor de Colecciones Postman E2E contra QA Desplegado (SCRUM-395)
.DESCRIPTION
    Ejecuta las colecciones Postman oficiales directamente contra el ambiente
    real de QA (https://qa.quickpatch.internal/api) utilizando Newman con TLS insecure.
    Exporta evidencias en JSON y texto para trazabilidad y registro de defectos.
#>

[CmdletBinding()]
param (
    [string]$BaseUrl = "https://qa.quickpatch.internal/api",
    [string]$EvidenciasDir = "$PSScriptRoot/evidencias"
)

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " QUICKPATCH — EJECUCIÓN E2E CONTRA QA DESPLEGADO (VM2)" -ForegroundColor Cyan
Write-Host " Base URL: $BaseUrl" -ForegroundColor Yellow
Write-Host " Evidencias: $EvidenciasDir" -ForegroundColor Yellow
Write-Host "================================================================================"

if (-not (Test-Path $EvidenciasDir)) {
    New-Item -ItemType Directory -Path $EvidenciasDir -Force | Out-Null
}

# Verificar resolución de red
Write-Host "[1/3] Verificando conectividad hacia $BaseUrl..." -ForegroundColor Gray
try {
    $ping = Test-NetConnection -ComputerName "qa.quickpatch.internal" -Port 443 -WarningAction SilentlyContinue
    if (-not $ping.TcpTestSucceeded) {
        Write-Warning "No se pudo establecer conexión TCP con qa.quickpatch.internal en puerto 443."
        Write-Warning "Por favor verifica que estés conectado a la VPN y que el archivo hosts contenga: 10.43.100.168 qa.quickpatch.internal"
    } else {
        Write-Host " Conexión exitosa a QA (Puerto 443 abierto)." -ForegroundColor Green
    }
} catch {
    Write-Warning "Error validando red: $_"
}

$collections = @(
    @{ Name = "MVP Sprint 4"; File = "quickpatch-mvp.postman_collection.json"; Prefix = "qa-mvp" },
    @{ Name = "SCRUM-81/90/93 Incremento Técnico"; File = "scrum-incremento-tecnico.postman_collection.json"; Prefix = "qa-scrum-81-90-93" },
    @{ Name = "SCRUM-56 Registro Técnico"; File = "scrum-56-registro-tecnico.postman_collection.json"; Prefix = "qa-scrum-56" },
    @{ Name = "SCRUM-84 Seguimiento Estados"; File = "scrum-84-seguimiento-estado.postman_collection.json"; Prefix = "qa-scrum-84" },
    @{ Name = "SCRUM-99 Equipo Proveedor"; File = "scrum-99-equipo-proveedor.postman_collection.json"; Prefix = "qa-scrum-99" },
    @{ Name = "SCRUM-108 Aprobación Técnicos"; File = "scrum-108-aprobacion-rechazo.postman_collection.json"; Prefix = "qa-scrum-108" },
    @{ Name = "SCRUM-111 Suspensión Técnicos"; File = "scrum-111-suspension-tecnico.postman_collection.json"; Prefix = "qa-scrum-111" },
    @{ Name = "SCRUM-78 Motor Matching"; File = "scrum-78-motor-matching.postman_collection.json"; Prefix = "qa-scrum-78" }
)

Write-Host "`n[2/3] Ejecutando colecciones Newman..." -ForegroundColor Cyan

$resumen = @()

foreach ($col in $collections) {
    $colPath = Join-Path $PSScriptRoot $col.File
    $jsonExport = Join-Path $EvidenciasDir "$($col.Prefix)-evidence.json"
    $txtExport = Join-Path $EvidenciasDir "$($col.Prefix)-cli.txt"

    if (-not (Test-Path $colPath)) {
        Write-Warning "Colección no encontrada: $colPath"
        continue
    }

    Write-Host "`n------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host " Ejecutando: $($col.Name)" -ForegroundColor Yellow
    Write-Host " Archivo: $($col.File)" -ForegroundColor DarkGray
    Write-Host "------------------------------------------------------------"

    $cmd = "newman run `"$colPath`" --env-var `"baseUrl=$BaseUrl`" --insecure -r cli,json --reporter-json-export `"$jsonExport`""
    
    # Ejecutar newman
    $output = Invoke-Expression $cmd 2>&1
    $output | Out-File -FilePath $txtExport -Encoding utf8
    $output | ForEach-Object { Write-Host $_ }

    $passed = $LASTEXITCODE -eq 0
    $resumen += [PSCustomObject]@{
        Suite = $col.Name
        Resultado = if ($passed) { "PASS" } else { "FAIL (Revisar Defectos)" }
        JSON = $jsonExport
    }
}

Write-Host "`n[3/3] Resumen de Ejecución contra QA Desplegado:" -ForegroundColor Cyan
$resumen | Format-Table -AutoSize
Write-Host "`nEvidencias JSON exportadas exitosamente en: $EvidenciasDir" -ForegroundColor Green
