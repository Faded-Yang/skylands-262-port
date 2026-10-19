@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title 天穹群岛 26.3 - 浮岛世界
set "W=%~dp0"
set "PY=C:\Users\95959\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
set "PLAY=%W%work\run26\watch"
set "MODS=%W%work\run26\mods-stable"

echo ============================================================
echo   天穹群岛 26.3  --  浮岛世界启动器
echo ============================================================
echo   世界 : %PLAY%\saves\sky islands
echo   mods : %MODS%
echo.
echo   注意：不要同时开两个客户端（会抢 GPU 导致世界卡加载）
echo.

if not exist "%PY%" (
  echo [错误] 找不到 Python: "%PY%"
  goto :end
)
if not exist "%PLAY%\saves\sky islands\level.dat" (
  echo [错误] 找不到世界目录:
  echo        "%PLAY%\saves\sky islands"
  goto :end
)

echo 正在启动，请稍候（首次进世界要生成区块，约 1-2 分钟）...
echo.
"%PY%" "%W%tools\launch26\launch.py" --game-dir "%PLAY%" --mods "%MODS%" --timeout 14400 "--extra-game-arg=--quickPlaySingleplayer=sky islands"

echo.
echo 游戏已退出。

:end
echo.
echo 按任意键关闭此窗口...
pause >nul