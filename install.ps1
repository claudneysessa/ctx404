$ErrorActionPreference = "Stop"

$archiveUrl = "https://github.com/claudneysessa/ctx404/archive/refs/heads/main.zip"
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("ctx404-" + [guid]::NewGuid().ToString("N"))
$archivePath = Join-Path $tempRoot "ctx404.zip"
$extractPath = Join-Path $tempRoot "source"

try {
    New-Item -ItemType Directory -Path $tempRoot | Out-Null
    Invoke-WebRequest -UseBasicParsing -Uri $archiveUrl -OutFile $archivePath
    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractPath
    $repositoryRoot = Get-ChildItem -LiteralPath $extractPath -Directory | Select-Object -First 1
    if (-not $repositoryRoot) {
        throw "CTX404 archive did not contain a repository directory."
    }
    & python (Join-Path $repositoryRoot.FullName "scripts\install.py") --force
    if ($LASTEXITCODE -ne 0) {
        throw "CTX404 installer exited with code $LASTEXITCODE."
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}
