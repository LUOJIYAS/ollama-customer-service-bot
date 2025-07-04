@echo off
echo ================================================
echo 智能客服机器人 - 后端服务启动脚本
echo ================================================

echo.
echo 检查环境...

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未加入环境变量
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✓ Python环境正常

REM 进入后端目录
cd back-end-pages

echo.
echo 安装依赖...
pip install -r ../requirements.txt

echo.
echo 启动后端服务...
python start.py

pause 