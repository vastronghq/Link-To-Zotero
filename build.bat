@echo off
setlocal

:: 设置生成的压缩包名称
set PLUGIN_NAME=Link2Zotero.zip

:: 插件目录（发现只要压缩包移动到插件目录即可，不用非得在软件中安装）
set TARGET_DIR=D:\Portable\Calibre Portable\Calibre Settings\plugins

:: 获取进程名称（用于结束进程）
set PROCESS_NAME=calibre.exe

:: 设置起始位置，防止我的便携版在C盘生成东西
set WORKING_DIRECTORY=D:\Portable\Calibre Portable

:: 设置Calibre可执行文件名称
set CALIBRE_EXE=calibre-portable.exe

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

echo [1/5] Cleaning old plugin package...
if exist %PLUGIN_NAME% del %PLUGIN_NAME%

echo [2/5] Packaging plugin files...
:: 使用 tar 命令压缩文件
:: -a 代表自动处理压缩格式
:: -c 代表创建
:: -f 代表指定文件名
tar -a -c -f %PLUGIN_NAME% __init__.py main.py plugin-import-name-Link2Zotero.txt images final_js_template.js single_book_js_template.js

echo [3/5] Moving plugin to Calibre plugins directory...
if not exist "%TARGET_DIR%" (
    echo Warning: Target directory does not exist!
    :: echo Creating directory: %TARGET_DIR%
    :: mkdir "%TARGET_DIR%"
)

if exist %PLUGIN_NAME% (
    move /Y %PLUGIN_NAME% "%TARGET_DIR%\"
    echo Successfully moved to: %TARGET_DIR%\
) else (
    echo Error: Plugin package was not created!
    exit /b 1
)


echo [4/5] Closing Calibre if it's running...
:: 首先尝试优雅关闭
wmic process where name="%PROCESS_NAME%" call terminate >nul 2>&1
timeout /t 5 /nobreak >nul

:: 如果优雅关闭失败，再强制关闭
:: /F 强制终止, /IM 指定映像名称, 2>nul 隐藏报错（如果没运行也不会报错）
tasklist | findstr /i "%PROCESS_NAME%" >nul
if %errorlevel%==0 (
    echo Calibre did not close gracefully, forcing close...
    taskkill /F /IM %PROCESS_NAME% 2>nul
    timeout /t 2 /nobreak >nul
)

echo Restarting Calibre...
pushd %WORKING_DIRECTORY%
start "" %CALIBRE_EXE%
popd

echo [5/5] Packaging complete!
echo ---------------------------------------
echo Plugin location: %TARGET_DIR%\%PLUGIN_NAME%
echo Tip: You can now load the plugin from file in Calibre.