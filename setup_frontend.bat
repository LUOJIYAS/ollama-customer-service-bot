@echo off
echo ========================================
echo 前端环境设置脚本
echo ========================================

cd front-end-pages

echo.
echo 清理现有环境...
if exist node_modules (
    echo 删除现有node_modules...
    rmdir /s /q node_modules
)
if exist package-lock.json (
    echo 删除package-lock.json...
    del package-lock.json
)

echo.
echo 设置npm配置...
npm config set registry https://registry.npmjs.org/
npm config set strict-ssl false

echo.
echo 尝试安装依赖（方法1：标准安装）...
npm install
if %errorlevel% equ 0 (
    echo ✓ 依赖安装成功！
    goto :success
)

echo.
echo 尝试安装依赖（方法2：使用legacy-peer-deps）...
npm install --legacy-peer-deps
if %errorlevel% equ 0 (
    echo ✓ 依赖安装成功！
    goto :success
)

echo.
echo 尝试安装依赖（方法3：逐个安装核心依赖）...
npm install next@14.0.4 react@^18.2.0 react-dom@^18.2.0 --save
npm install typescript@^5.3.3 @types/node@^20.10.5 @types/react@^18.2.45 @types/react-dom@^18.2.18 --save-dev
npm install antd@^5.12.8 @ant-design/icons@^5.2.6 --save
npm install axios@^1.6.2 react-markdown@^9.0.1 --save

if %errorlevel% equ 0 (
    echo ✓ 核心依赖安装成功！
    goto :success
)

echo.
echo ❌ 所有安装方法都失败了
echo 请手动安装依赖或检查网络连接
goto :end

:success
echo.
echo ========================================
echo ✓ 前端环境设置完成！
echo 现在可以运行: npm run dev
echo ========================================

:end
pause 