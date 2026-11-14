param(
    [string]$AndroidSdk = 'C:\AndroidSdk',
    [string]$KeyStore = 'C:\WatchProjects\WalletButtonRemap\debug.keystore'
)
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$buildTools = Join-Path $AndroidSdk 'build-tools\36.0.0'
$build = Join-Path $project 'build\flip'
New-Item -ItemType Directory -Force -Path $build | Out-Null
function Run-Checked([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Executable failed ($LASTEXITCODE)" }
}
Run-Checked 'python' @((Join-Path $PSScriptRoot 'generate_flip.py'))
Run-Checked 'python' @((Join-Path $PSScriptRoot 'preview_flip.py'))
Run-Checked 'python' @((Join-Path $PSScriptRoot 'validate.py'))
Run-Checked 'python' @((Join-Path $PSScriptRoot 'validate_touch.py'))
Run-Checked (Join-Path $buildTools 'aapt2.exe') @('compile','--dir',(Join-Path $project 'res'),'-o',(Join-Path $build 'res.zip'))
Run-Checked (Join-Path $buildTools 'aapt2.exe') @('link','-o',(Join-Path $build 'unsigned.apk'),'--manifest',(Join-Path $project 'AndroidManifest.xml'),'-I',(Join-Path $AndroidSdk 'platforms\android-35\android.jar'),'--min-sdk-version','34','--target-sdk-version','35',(Join-Path $build 'res.zip'))
Run-Checked (Join-Path $buildTools 'zipalign.exe') @('-f','4',(Join-Path $build 'unsigned.apk'),(Join-Path $build 'aligned.apk'))
Run-Checked (Join-Path $buildTools 'apksigner.bat') @('sign','--ks',$KeyStore,'--ks-key-alias','androiddebugkey','--ks-pass','pass:android','--key-pass','pass:android','--out',(Join-Path $project 'build\PaletteMeteo.apk'),(Join-Path $build 'aligned.apk'))
Run-Checked (Join-Path $buildTools 'apksigner.bat') @('verify','--verbose',(Join-Path $project 'build\PaletteMeteo.apk'))
Write-Output "Built and signed: $project\build\PaletteMeteo.apk"
