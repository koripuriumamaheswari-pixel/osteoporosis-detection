@echo off
echo ============================================
echo     Starting Spine Osteoporosis Project
echo ============================================

echo.
echo [1] Starting Django Server in the background...
start "Django Server" cmd.exe /c "python manage.py runserver"

echo waiting a few seconds for server to load...
timeout /t 3 /nobreak > nul

echo.
echo [2] Starting Public Online Link (Cloudflare)...
echo.
echo *************************************************************
echo LOOK FOR THE LINK THAT ENDS WITH  .trycloudflare.com 
echo COPY THAT LINK AND PASTE IT IN ANY BROWSER OR MOBILE!
echo *************************************************************
echo.
.\cloudflared.exe tunnel --url http://127.0.0.1:8000

pause
