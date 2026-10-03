@echo off
setlocal EnableExtensions

set "IMAGE=edokope/cafetera-under-backend:latest"
set "NAME=cafeteraUnder"
set "MEMORY_LIMIT=512m"
set "ENV_FILE=%~dp0.env-cafetera-under"

cd /d "%~dp0.."

if not exist "%ENV_FILE%" (
  echo Falta %ENV_FILE%
  exit /b 1
)
if not exist "secrets\firebase.json" (
  echo Falta secrets\firebase.json en %CD%
  exit /b 1
)

set "OLD_IMAGE_ID="
docker inspect "%NAME%" >nul 2>&1
if not errorlevel 1 (
  for /f "usebackq delims=" %%I in (`docker inspect "%NAME%" --format "{{.Image}}"`) do set "OLD_IMAGE_ID=%%I"
)

docker pull "%IMAGE%"
if errorlevel 1 exit /b 1

docker rm -f "%NAME%" >nul 2>&1

docker run -d --name "%NAME%" --restart unless-stopped --memory="%MEMORY_LIMIT%" --env-file "%ENV_FILE%" -v "%CD%\secrets\firebase.json:/run/secrets/firebase.json:ro" "%IMAGE%"
if errorlevel 1 exit /b 1

set "NEW_IMAGE_ID="
for /f "usebackq delims=" %%I in (`docker inspect "%NAME%" --format "{{.Image}}"`) do set "NEW_IMAGE_ID=%%I"

if defined OLD_IMAGE_ID if /I not "%OLD_IMAGE_ID%"=="%NEW_IMAGE_ID%" (
  docker rmi "%OLD_IMAGE_ID%" >nul 2>&1
)

echo Deploy OK: %NAME% en marcha. Se conecta al broker MQTT y no abre puertos.
exit /b 0
