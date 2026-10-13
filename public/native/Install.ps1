$ErrorActionPreference = 'Stop'
$pyRoot = Join-Path $env:APPDATA 'pyRevit'
if (!(Test-Path $pyRoot)) { throw 'Install pyRevit for your Revit version first, then run this installer again.' }
$destination = Join-Path $pyRoot 'Extensions\LITHICNativeHandoff.extension\LITHIC.tab\Native.panel\AFKC Handoff.pushbutton'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
foreach ($name in @('script.py', 'contract.py', 'authoring.py', 'drawings.py', 'afkc-source.json', 'bundle.yaml')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $destination $name) -Force
}
Write-Host 'Installed LITHIC > Native > AFKC Handoff. Reload pyRevit or restart Revit.'
Read-Host 'Press Enter to close'
