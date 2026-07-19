@echo off
REM One-click run parity (PROJECT-GENESIS.md Tier 6 item 43): starts the app locally
REM and opens the browser, mirroring this project's entry in jarvis-launcher's
REM jarvis.config.json ("run app" action) so the launcher and this repo never drift.
REM This only launches the app on your machine - it never touches .streamlit/ or any
REM Streamlit Cloud deploy config, and the live production deploy is unaffected.
setlocal

set "ROOT=%~dp0"

start "Resume Job-Fit AI" /D "%ROOT%" cmd /k "set PYTHONIOENCODING=utf-8 && venv\Scripts\python -m streamlit run app.py"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline=(Get-Date).AddSeconds(30); while((Get-Date) -lt $deadline) { try { Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8501' -TimeoutSec 2 | Out-Null; break } catch { Start-Sleep -Milliseconds 500 } }; Start-Process 'http://localhost:8501'"

endlocal
