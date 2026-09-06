@echo off
echo.
echo =============================================
echo     Система управления театром - VKR_MAIN
echo =============================================
echo.
echo Доступные варианты запуска:
echo.
echo 1. Запустить только API-сервер
echo 2. Запустить только основное приложение
echo 3. Запустить оба компонента (в новых окнах)
echo.
set /p choice="Выберите действие (1-3): "

if "%choice%"=="1" (
    echo Запуск API-сервера...
    start cmd /k "cd /d %~dp0 && python start_api.py"
) else if "%choice%"=="2" (
    echo Запуск основного приложения...
    cd /d %~dp0 && python start_app.py
) else if "%choice%"=="3" (
    echo Запуск API-сервера...
    start cmd /k "cd /d %~dp0 && python start_api.py"
    timeout /t 3 /nobreak >nul
    echo Запуск основного приложения...
    start cmd /k "cd /d %~dp0 && python start_app.py"
) else (
    echo Неверный выбор. Пожалуйста, выберите 1, 2 или 3.
)