@echo off
chcp 65001 >nul
title IE_Agent 本地服务器  --  关闭此窗口即停止服务

REM ===========================================================
REM  IE_Agent 一键启动器（健壮版）
REM  双击运行；浏览器会自动打开 http://localhost:8501
REM  使用期间不要关闭这个黑色窗口（关闭=停止服务）
REM ===========================================================

echo.
echo   [1/3] 清理旧的服务器实例（避免端口冲突 / 旧代码残留）...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*streamlit*' } | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {} }" >nul 2>&1

cd /d "%~dp0app"
set KMP_DUPLICATE_LIB_OK=TRUE

echo   [2/3] 启动服务器（首次需加载模型，约 10-30 秒，请耐心等）...
echo   [3/3] 稍候浏览器会自动打开  http://localhost:8501
echo.
echo   ============================================================
echo     ★ 使用期间不要关闭这个黑色窗口（关闭 = 停止服务）★
echo   ============================================================
echo.

"D:\python\python.exe" -m streamlit run streamlit_project_app.py --server.port 8501

echo.
echo   服务器已停止。按任意键关闭本窗口。
pause >nul
