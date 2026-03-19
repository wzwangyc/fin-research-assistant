@echo off
chcp 65001 >nul
echo ==================================================
echo 金融研报助手 - 快速启动
echo ==================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo [1/3] 初始化数据库...
python backend/app/sql/database.py
if %errorlevel% neq 0 (
    echo [错误] 数据库初始化失败
    pause
    exit /b 1
)

echo.
echo [2/3] 启动 Streamlit 前端...
echo 浏览器将自动打开 http://localhost:8501
echo 按 Ctrl+C 停止服务
echo.

cd frontend
streamlit run app.py

pause
