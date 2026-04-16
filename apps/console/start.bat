@echo off
chcp 65001 >nul
echo ================================
echo   VCE Console 启动脚本
echo ================================
echo.

:: 检查 node_modules
if not exist "node_modules" (
    echo [1/2] 正在安装依赖...
    call npm install
    if errorlevel 1 (
        echo 依赖安装失败！
        pause
        exit /b 1
    )
    echo.
)

:: 启动开发服务器
echo [2/2] 启动开发服务器 (端口 3000)...
echo API 代理目标: http://localhost:8000
echo.
call npm run dev
