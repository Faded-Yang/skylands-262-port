$ErrorActionPreference='Continue'
$base='work\refs\repos'
New-Item -ItemType Directory -Force -Path $base | Out-Null
$repos=@(
  @('fabric-docs','https://github.com/FabricMC/fabric-docs.git'),
  @('neoforged-documentation','https://github.com/neoforged/documentation.git'),
  @('fabricators-create','https://github.com/Fabricators-of-Create/Create.git'),
  @('create-wiki','https://github.com/Creators-of-Create/wiki.git'),
  @('yan-mc-mod-dev','https://github.com/yan-mc/minecraft-mod-dev.git')
)
foreach($r in $repos){
  $name=$r[0]; $url=$r[1]; $dest=Join-Path $base $name
  if(Test-Path $dest){ Write-Output "$name exists"; continue }
  Write-Output "cloning $name ..."
  $p=Start-Process -FilePath git -ArgumentList @('clone','--depth','1',$url,$dest) -NoNewWindow -PassThru
  if(-not $p.WaitForExit(240000)){ $p.Kill(); Write-Output "$name TIMEOUT" } else { Write-Output "$name exit=$($p.ExitCode)" }
}
Get-ChildItem $base -Directory | ForEach-Object { $_.Name + ' entries=' + (Get-ChildItem $_.FullName -Force | Measure-Object).Count }