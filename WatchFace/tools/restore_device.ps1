# Restore the exact original values observed before the optional ambient test.
$ErrorActionPreference = 'Stop'
$adb = 'C:\AndroidSdk\platform-tools\adb.exe'
& $adb shell dumpsys battery reset
if ($LASTEXITCODE -ne 0) { throw 'Watch not connected: battery reset not completed.' }
foreach ($key in @('ambient_enabled', 'ambient_force_when_docked')) {
    & $adb shell settings put global $key 0
    if ($LASTEXITCODE -ne 0) { throw "Failed to restore $key" }
}
& $adb shell input keyevent KEYCODE_WAKEUP
& $adb shell input keyevent KEYCODE_HOME
& $adb shell dumpsys battery
& $adb shell settings get global ambient_enabled
& $adb shell settings get global ambient_force_when_docked
