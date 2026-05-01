@echo off
cd /d %~dp0

echo Iniciando SaaS de Curriculos...
uvicorn app:app --reload --port 8002

pause