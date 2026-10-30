param([string[]]$Classes, [string]$Filter = "")
$ErrorActionPreference = "SilentlyContinue"
$M = "$env:APPDATA\.minecraft"
$J = "$M\versions\26.3\26.3.jar"
$JP = "$M\runtime\java-runtime-epsilon\bin\javap.exe"
$cp = @(
  $J,
  "$M\libraries\com\mojang\datafixerupper\10.0.21\datafixerupper-10.0.21.jar",
  "$M\libraries\org\joml\joml\1.10.9\joml-1.10.9.jar",
  "$M\libraries\com\mojang\brigadier\1.3.11\brigadier-1.3.11.jar",
  "$M\libraries\org\jspecify\jspecify\1.0.0\jspecify-1.0.0.jar",
  "$M\libraries\it\unimi\dsi\fastutil\8.5.18\fastutil-8.5.18.jar",
  "C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\aero-port\libs26\create-fly-26.2-6.0.9-2-26.3-patched.jar",
  "C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\aero-port\libs26\fabric-api-0.163.0+26.3.jar"
) -join ';'
$flat = @()
foreach ($x in $Classes) { $flat += ($x -split '[,; ]+') | Where-Object { $_ } }
foreach ($c in $flat) {
  Write-Host "===== $c ====="
  $out = & $JP -cp $cp $c 2>&1
  if ($Filter) { $out | Select-String -Pattern $Filter } else { $out }
}
