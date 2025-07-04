@echo off
echo ========================================
echo 前端环境完全清理脚本
echo ========================================

cd front-end-pages

echo.
echo 1. 停止所有Node.js进程...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im npm.exe >nul 2>&1

echo.
echo 2. 强制删除node_modules（可能需要几分钟）...
if exist node_modules (
    echo 正在删除node_modules...
    rmdir /s /q node_modules >nul 2>&1
    if exist node_modules (
        echo 第一次删除失败，尝试使用PowerShell...
        powershell -Command "Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue" >nul 2>&1
    )
    if exist node_modules (
        echo 仍然存在，尝试逐个删除...
        for /d %%i in (node_modules\*) do (
            rmdir /s /q "%%i" >nul 2>&1
        )
        rmdir /s /q node_modules >nul 2>&1
    )
)

echo.
echo 3. 删除相关文件...
if exist package-lock.json (
    del package-lock.json
    echo ✓ 删除package-lock.json
)
if exist yarn.lock (
    del yarn.lock
    echo ✓ 删除yarn.lock
)
if exist .next (
    rmdir /s /q .next >nul 2>&1
    echo ✓ 删除.next目录
)

echo.
echo 4. 清理npm缓存...
npm cache clean --force >nul 2>&1

echo.
echo 5. 重置npm配置...
npm config delete registry >nul 2>&1
npm config set registry https://registry.npmjs.org/

echo.
echo ✅ 前端环境清理完成！
echo.
echo 现在可以重新安装依赖：
echo   cd front-end-pages
echo   npm install --legacy-peer-deps --no-optional
echo.
pause 