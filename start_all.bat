@echo off
echo ========================================
echo 智能客服机器人启动脚本
echo 基于Ollama 0.9.3 API
echo ========================================

echo.
echo 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo Python未安装或未加入PATH，请先安装Python
    pause
    exit /b 1
)

echo.
echo 检查Ollama服务...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] Ollama服务未运行，请确保Ollama已启动
    echo 你可以运行：ollama serve
    echo.
)

echo.
echo 检查所需模型...
echo 对话模型: deepseek-r1:latest
echo 嵌入模型: modelscope.cn/Qwen/Qwen3-Embedding-8B-GGUF:latest
echo.
echo 如果模型未安装，请运行:
echo ollama pull deepseek-r1:latest
echo ollama pull modelscope.cn/Qwen/Qwen3-Embedding-8B-GGUF:latest
echo.

echo 启动后端服务...
cd back-end-pages
start "智能客服后端" cmd /k "echo 后端服务启动中... && python main.py"

echo.
echo 等待后端服务启动...
timeout /t 5 /nobreak

echo.
echo 检查前端依赖...
cd ..\front-end-pages
if not exist node_modules (
    echo 前端依赖未安装，尝试安装...
    npm install --registry https://registry.npmjs.org
    if %errorlevel% neq 0 (
        echo [警告] npm安装失败，请手动运行: npm install
        echo 或者尝试: npm install --legacy-peer-deps
    )
)

echo.
echo 启动前端服务...
start "智能客服前端" cmd /k "echo 前端服务启动中... && npm run dev"

echo.
echo ========================================
echo 服务启动完成！
echo.
echo 后端API: http://localhost:8000
echo 前端界面: http://localhost:3000
echo API文档: http://localhost:8000/docs
echo.
echo 按任意键退出启动脚本...
echo ========================================
pause 