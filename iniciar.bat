@echo off
echo ========================================================
echo Iniciando Dashboard - Prodígia
echo ========================================================

echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo.
echo Iniciando servidor FastAPI na porta 8001...
echo Acesse no navegador: http://127.0.0.1:8001
echo.

uvicorn app.server:app --host 0.0.0.0 --port 8001 --reload
