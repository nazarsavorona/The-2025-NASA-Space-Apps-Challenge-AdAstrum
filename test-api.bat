@echo off
REM Simple API test using PowerShell Invoke-RestMethod

echo ============================================================
echo Testing AdAstrum API
echo ============================================================
echo.

echo [1/3] Testing Health Endpoint...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:8000/' -Method GET; Write-Host 'SUCCESS:' $response.message -ForegroundColor Green } catch { Write-Host 'FAILED:' $_.Exception.Message -ForegroundColor Red }"
echo.

echo [2/3] Testing Prediction Endpoint...
powershell -Command "$body = @{ format = 'kepler'; data = @(@{ koi_period = 10.5; koi_prad = 2.5; koi_teq = 500; koi_insol = 100; koi_steff = 5500; koi_slogg = 4.5; koi_srad = 1.0 }); hyperparams = @{} } | ConvertTo-Json -Depth 10; try { $response = Invoke-RestMethod -Uri 'http://localhost:8000/api/predict/' -Method POST -Body $body -ContentType 'application/json'; Write-Host 'SUCCESS!' -ForegroundColor Green; Write-Host '  Status:' $response.status; Write-Host '  Predictions:' $response.predictions.Count; Write-Host '  Class:' $response.predictions[0].predicted_class; Write-Host '  Confidence:' ([math]::Round($response.predictions[0].predicted_confidence, 3)) } catch { Write-Host 'FAILED:' $_.Exception.Message -ForegroundColor Red; if ($_.ErrorDetails) { Write-Host $_.ErrorDetails.Message -ForegroundColor Yellow } }"
echo.

echo [3/3] API Documentation
echo Interactive API docs available at:
echo   http://localhost:8000/docs
echo   http://localhost:8000/redoc
echo.

echo ============================================================
echo To view logs: logs.bat
echo To stop: stop-dev.bat
echo ============================================================
pause
