$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskConfig = Join-Path $taskRoot '.env.graphhacks'
if (Test-Path -LiteralPath $taskConfig) {
    Write-Output 'Existing .env.graphhacks preserved.'
    exit 0
}
$taskTemplate = Get-Content -LiteralPath (Join-Path $taskRoot '.env.graphhacks.example') -Raw
$taskDbPassword = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
$taskGraphPassword = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
$taskTemplate = $taskTemplate.Replace('POSTGRES_PASSWORD=GENERATE_ME', "POSTGRES_PASSWORD=$taskDbPassword").Replace('FALKORDB_PASSWORD=GENERATE_ME', "FALKORDB_PASSWORD=$taskGraphPassword")
Set-Content -LiteralPath $taskConfig -Value $taskTemplate -Encoding utf8
Write-Output 'Created private .env.graphhacks with generated database credentials. Live model calls are disabled.'
