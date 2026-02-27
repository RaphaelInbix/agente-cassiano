# daily_update.ps1
# Dispara a atualizacao da Curadoria Inbix no Render.
# Agendar via Task Scheduler do Windows as 9:30 (horario de Brasilia).
#
# Uso manual: powershell -ExecutionPolicy Bypass -File daily_update.ps1
#
# Para agendar automaticamente, execute como admin:
#   $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-ExecutionPolicy Bypass -File "C:\Users\rapha\Desktop\agente cassiano\scripts\daily_update.ps1"'
#   $trigger = New-ScheduledTaskTrigger -Daily -At 9:30AM
#   Register-ScheduledTask -TaskName "CuradoriaInbixDailyUpdate" -Action $action -Trigger $trigger -Description "Atualiza curadoria diariamente as 9:30 BRT"

$API_BASE = "https://agente-cassiano.onrender.com"
$LOG_FILE = "$PSScriptRoot\..\logs\daily_update.log"

function Log($msg) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $msg" | Tee-Object -FilePath $LOG_FILE -Append
}

Log "=== Iniciando atualizacao diaria ==="

# 1. Acorda o servidor (cold start do Render pode levar 30-60s)
Log "Acordando servidor (health check)..."
try {
    $health = Invoke-WebRequest -Uri "$API_BASE/api/health" -TimeoutSec 90 -UseBasicParsing
    Log "Servidor respondeu: $($health.StatusCode)"
} catch {
    Log "Health check falhou: $($_.Exception.Message). Tentando prosseguir..."
}

# 2. Aguarda estabilizar
Start-Sleep -Seconds 5

# 3. Dispara a atualizacao
Log "Disparando POST /api/atualizar..."
try {
    $response = Invoke-WebRequest -Uri "$API_BASE/api/atualizar" -Method POST -TimeoutSec 120 -UseBasicParsing
    Log "Resposta: $($response.StatusCode) - $($response.Content)"
} catch {
    Log "ERRO ao atualizar: $($_.Exception.Message)"
    exit 1
}

# 4. Aguarda pipeline finalizar (polling por ate 5 minutos)
$maxWait = 300
$elapsed = 0
$interval = 10

while ($elapsed -lt $maxWait) {
    Start-Sleep -Seconds $interval
    $elapsed += $interval
    try {
        $status = Invoke-RestMethod -Uri "$API_BASE/api/status" -TimeoutSec 30
        Log "Status: $($status.status) - $($status.detail)"
        if ($status.status -eq "done" -or $status.status -eq "error") {
            break
        }
    } catch {
        Log "Erro ao verificar status: $($_.Exception.Message)"
    }
}

if ($elapsed -ge $maxWait) {
    Log "TIMEOUT: Pipeline nao completou em $maxWait segundos"
} else {
    Log "Pipeline finalizado!"
}

Log "=== Fim ==="
