@echo off
:: =================================================================
:: Calibre 插件调试自动化工具 (适用于便携版)
:: 使用流程：1. 修改代码 -> 2. 保存 -> 3. 运行此脚本 -> 4. 插件自动打包到配置的插件目录，并以调试模式启动GUI -> 5. 关闭终端或GUI结束本次调试
:: =================================================================

:: [环境变量] 确保插件装入便携版配置目录
:: 重要：设置变量时不要加引号，即使路径有空格
set CALIBRE_CONFIG_DIRECTORY=D:\Portable\Calibre Portable\Calibre Settings

echo [STEP 1/2] 正在打包插件到便携版配置目录...
"D:\Portable\Calibre Portable\Calibre\calibre-customize.exe" -b .

echo [STEP 2/2] 以调试模式启动GUI (实时捕获 print 输出)
echo ---------------------------------------------------------------
echo 提示: 在 Calibre 界面操作插件，在此窗口查看日志。
echo ---------------------------------------------------------------
"D:\Portable\Calibre Portable\Calibre\calibre-debug.exe" -g
