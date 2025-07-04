@echo off
echo ================================================
echo 智能客服机器人 - 前端服务启动脚本
echo ================================================

echo.
echo 检查环境...

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装或未加入环境变量
    echo 请先安装Node.js 16+
    pause
    exit /b 1
)

echo ✓ Node.js环境正常

REM 进入前端目录
cd front-end-pages

echo.
echo 安装依赖...
call npm install

echo.
echo 启动前端服务...
call npm run dev

pause 