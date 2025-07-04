@echo off
echo ========================================
echo 智能客服机器人系统检查
echo ========================================

echo.
echo 1. 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未加入PATH
    echo 请安装Python 3.8+并添加到系统PATH
    goto :error
)

echo.
echo 2. 检查Python依赖...
cd back-end-pages
python -c "import fastapi, chromadb, loguru, httpx; print('✓ Python依赖检查通过')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python依赖缺失
    echo 正在安装依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        goto :error
    )
)

echo.
echo 3. 检查Ollama服务...
python check_ollama.py
if %errorlevel% neq 0 (
    echo ❌ Ollama服务检查失败
    goto :error
)

echo.
echo 4. 检查Node.js环境...
cd ..\front-end-pages
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js未安装
    echo 请安装Node.js 16+
    goto :error
)

npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm未安装
    goto :error
)

echo ✓ Node.js环境正常

echo.
echo 5. 检查前端依赖...
if not exist node_modules (
    echo 前端依赖未安装，尝试安装...
    call ..\setup_frontend.bat
)

if not exist node_modules (
    echo ❌ 前端依赖安装失败
    goto :error
)

echo ✓ 前端依赖检查通过

echo.
echo ========================================
echo ✅ 系统检查完成！所有组件就绪
echo.
echo 📋 系统信息:
echo   - Python: 已安装并配置
echo   - Ollama: 服务运行正常
echo   - Node.js: 已安装并配置
echo   - 依赖: 全部安装完成
echo.
echo 🚀 现在可以运行: start_all.bat
echo ========================================
goto :end

:error
echo.
echo ========================================
echo ❌ 系统检查失败！
echo 请解决上述问题后重新运行此脚本
echo ========================================

:end
cd ..
pause 