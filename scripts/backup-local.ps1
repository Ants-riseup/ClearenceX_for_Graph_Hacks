$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupPath = Join-Path $projectRoot "output/private-backups/$stamp"
New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
docker compose --env-file .env.graphhacks stop frontend api
if ($LASTEXITCODE -ne 0) { throw 'Could not pause application writers.' }
try {
    docker compose --env-file .env.graphhacks exec -T postgres pg_dump -U clearancex -d clearancex -Fc -f /tmp/clearancex-backup.dump
    if ($LASTEXITCODE -ne 0) { throw 'Database backup failed.' }
    docker compose --env-file .env.graphhacks cp postgres:/tmp/clearancex-backup.dump "$backupPath/postgres.dump"
    if ($LASTEXITCODE -ne 0) { throw 'Database copy failed.' }
    docker compose --env-file .env.graphhacks exec -T falkordb sh -c 'export REDISCLI_AUTH=$FALKORDB_PASSWORD; redis-cli --raw SAVE | grep -qx OK'
    if ($LASTEXITCODE -ne 0) { throw 'Graph snapshot failed.' }
    docker compose --env-file .env.graphhacks cp falkordb:/var/lib/falkordb/data/dump.rdb "$backupPath/graph.rdb"
    if ($LASTEXITCODE -ne 0) { throw 'Graph copy failed.' }
    docker compose --env-file .env.graphhacks cp api:/data/uploads "$backupPath/uploads"
    if ($LASTEXITCODE -ne 0) { throw 'Private PDF backup failed.' }
    [ordered]@{ created = (Get-Date).ToString('o'); consistency = 'API writers paused'; secrets = 'Keep backups private; authentication and private PDFs included.' } | ConvertTo-Json | Set-Content -LiteralPath "$backupPath/manifest.json"
    Write-Output "Backup completed in output/private-backups/$stamp. Keep it private."
} finally {
    docker compose --env-file .env.graphhacks up -d api frontend
}
