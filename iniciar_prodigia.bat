@echo off
title Servidor Prodigia
echo ==========================================
echo Iniciando o Servidor da Prodigia...
echo ==========================================
echo O painel estara disponivel em: http://localhost:8000
echo.
set PYTHONPATH=.
.venv\Scripts\uvicorn.exe app.server:app --port 8000 --reload
pause
