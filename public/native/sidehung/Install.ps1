$ErrorActionPreference = 'Stop'
$pyRoot = Join-Path $env:APPDATA 'pyRevit'
if (!(Test-Path -LiteralPath $pyRoot)) { throw 'Install pyRevit before running this installer.' }
$destination = Join-Path $pyRoot 'Extensions\LITHICNativeHandoff.extension\LITHIC.tab\Native.panel\Side-Hung Window Handoff.pushbutton'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
foreach ($name in @('script.py','desktop_contract.py','fixed_contract.py','authoring.py','build_closed.py','corner_math.py','build_native.py','wrap_hosted.py','material_controls.py','export_builder.py','definition.json','source.json','hinge-reference.json','bundle.yaml')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $destination $name) -Force
}
Write-Host 'Installed LITHIC > Native > Side-Hung Window Handoff. Reload pyRevit or restart Revit.'
Read-Host 'Press Enter to close'
