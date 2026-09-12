@echo off
echo ==========================================
echo Encerrando Servidor da Prodigia (Porta 8000)...
echo ==========================================
FOR /F "tokens=5" %%a IN ('netstat -aon ^| findstr ":8000 " ^| find "LISTENING"') DO (
    echo Fechando processo PID: %%a
    taskkill /F /PID %%a
)
echo.
echo Servidor encerrado com sucesso!
pause
