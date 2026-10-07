Write-Host " === CodeChef Auto-Solver Quick Launcher ===\ -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
 Write-Host \[!] Python not found. Please install Python 3.10+ from python.org\ -ForegroundColor Red
 pause
 exit
}
if (-not (Test-Path \auto_solve.py\)) {
 Write-Host \[1/3] Downloading auto_solve.py...\ -ForegroundColor Yellow
 Invoke-WebRequest -Uri \https://raw.githubusercontent.com/manibrahmamkurakula/CodeChef_auto_Solver/main/auto_solve.py\ -OutFile \auto_solve.py\
}
if (-not (Test-Path \solutions_database.json\)) {
 Write-Host \[2/3] Downloading solutions_database.json...\ -ForegroundColor Yellow
 Invoke-WebRequest -Uri \https://raw.githubusercontent.com/manibrahmamkurakula/CodeChef_auto_Solver/main/solutions_database.json\ -OutFile \solutions_database.json\
}
Write-Host \[3/3] Setting up browser dependencies...\ -ForegroundColor Yellow
pip install playwright python-dotenv --quiet
playwright install chromium
Write-Host \
[OK] Launching Solver... Login when the browser opens!\ -ForegroundColor Green
python auto_solve.py
