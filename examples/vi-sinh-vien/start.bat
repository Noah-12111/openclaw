@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================
echo       VI SINH VIEN - QUAN LY THU CHI
echo ==========================================
node --version >nul 2>&1
if errorlevel 1 (
  echo Chua tim thay Node.js. Hay cai Node.js tu https://nodejs.org/
  pause
  exit /b 1
)
npm.cmd run check
if errorlevel 1 (
  echo Kiem tra ma nguon that bai. Hay xem loi phia tren.
  pause
  exit /b 1
)
npm.cmd test
if errorlevel 1 (
  echo Kiem thu that bai. Hay xem loi phia tren.
  pause
  exit /b 1
)
npm.cmd start
pause
