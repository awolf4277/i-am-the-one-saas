Write-Host ""
Write-Host "Starting I AM THE ONE / WOLF OS local stack..." -ForegroundColor Green
Write-Host "Backend:  http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "Frontend: http://127.0.0.1:5175" -ForegroundColor Cyan
Write-Host ""

Start-Process powershell -ArgumentList '-NoExit', '-Command', '
cd "X:\i-am-the-one-saas\backend";
.\.venv\Scripts\activate;
$env:CORS_ORIGINS="http://127.0.0.1:5175,http://localhost:5175,http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:5180,http://localhost:5180";
python -m flask --app wsgi run --host 127.0.0.1 --port 5000
'

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList '-NoExit', '-Command', '
cd "X:\i-am-the-one-saas\frontend";
Set-Content .env.local "VITE_BACKEND_URL=http://127.0.0.1:5000";
npx vite --host 127.0.0.1 --port 5175 --strictPort
'

Start-Sleep -Seconds 3

Start-Process "http://127.0.0.1:5175/"
