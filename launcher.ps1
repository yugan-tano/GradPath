$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeRoot = Join-Path $projectRoot ".runtime"
$embeddedPython = Join-Path $runtimeRoot "python\python.exe"
$logDirectory = Join-Path $projectRoot "data\logs"
$logPath = Join-Path $logDirectory "startup.log"

function Test-PythonCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$PrefixArgs = @()
    )

    try {
        & $Command @PrefixArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Find-Python {
    if ($env:BAOYAN_PYTHON -and (Test-PythonCommand -Command $env:BAOYAN_PYTHON)) {
        return [pscustomobject]@{ Command = $env:BAOYAN_PYTHON; Args = @() }
    }

    if ((Test-Path -LiteralPath $embeddedPython) -and (Test-PythonCommand -Command $embeddedPython)) {
        return [pscustomobject]@{ Command = $embeddedPython; Args = @() }
    }

    foreach ($name in @("python3", "python")) {
        $resolved = Get-Command $name -ErrorAction SilentlyContinue
        if ($resolved -and (Test-PythonCommand -Command $resolved.Source)) {
            return [pscustomobject]@{ Command = $resolved.Source; Args = @() }
        }
    }

    $py = Get-Command "py" -ErrorAction SilentlyContinue
    if ($py -and (Test-PythonCommand -Command $py.Source -PrefixArgs @("-3"))) {
        return [pscustomobject]@{ Command = $py.Source; Args = @("-3") }
    }

    return $null
}

function Install-EmbeddedPython {
    if (-not [Environment]::Is64BitOperatingSystem) {
        throw "Python 3 was not found. The automatic runtime currently requires 64-bit Windows. Please install Python 3.9 or later."
    }

    $version = "3.11.9"
    $archive = Join-Path $runtimeRoot "python-$version-embed-amd64.zip"
    $downloadUrl = "https://www.python.org/ftp/python/$version/python-$version-embed-amd64.zip"
    $pythonDirectory = Split-Path -Parent $embeddedPython

    New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null
    $archiveReady = (Test-Path -LiteralPath $archive) -and ((Get-Item -LiteralPath $archive).Length -gt 1MB)
    if (-not $archiveReady) {
        Write-Host "[Startup] Python was not found. Downloading the private project runtime (first run only)..."
        $curl = Get-Command "curl.exe" -ErrorAction SilentlyContinue
        if ($curl) {
            & $curl.Source --ssl-no-revoke --fail --location --retry 2 --output $archive $downloadUrl
            $archiveReady = ($LASTEXITCODE -eq 0) -and (Test-Path -LiteralPath $archive) -and ((Get-Item -LiteralPath $archive).Length -gt 1MB)
        }
        if (-not $archiveReady) {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -UseBasicParsing -Uri $downloadUrl -OutFile $archive
        }
    }

    if (Test-Path -LiteralPath $pythonDirectory) {
        Remove-Item -LiteralPath $pythonDirectory -Recurse -Force
    }
    Expand-Archive -LiteralPath $archive -DestinationPath $pythonDirectory -Force
    Remove-Item -LiteralPath $archive -Force

    if (-not (Test-PythonCommand -Command $embeddedPython)) {
        throw "The private project runtime could not be installed. Check the network and retry, or install Python 3.9 or later."
    }
}

function Enable-EmbeddedProjectImports {
    $pathFile = Get-ChildItem -LiteralPath (Split-Path -Parent $embeddedPython) -Filter "python*._pth" | Select-Object -First 1
    if (-not $pathFile) {
        throw "The private Python runtime path configuration is missing. Delete .runtime and retry."
    }
    $projectEntry = "..\.."
    $entries = Get-Content -LiteralPath $pathFile.FullName
    if ($entries -notcontains $projectEntry) {
        Add-Content -LiteralPath $pathFile.FullName -Value $projectEntry -Encoding ascii
    }
}

try {
    $python = Find-Python
    if (-not $python) {
        Install-EmbeddedPython
        $python = [pscustomobject]@{ Command = $embeddedPython; Args = @() }
    }
    if ($python.Command -eq $embeddedPython) {
        Enable-EmbeddedProjectImports
    }

    New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
    Set-Location -LiteralPath $projectRoot
    if ($null -eq $env:BAOYAN_OPEN_BROWSER) {
        $env:BAOYAN_OPEN_BROWSER = "1"
    }
    $env:PYTHONIOENCODING = "utf-8"

    "===== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') STARTUP =====" | Tee-Object -FilePath $logPath
    "Python: $($python.Command)" | Tee-Object -FilePath $logPath -Append
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $python.Command @($python.Args) -u app.py | Tee-Object -FilePath $logPath -Append
    $applicationExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorAction
    if ($applicationExitCode -ne 0) {
        throw "The application exited with code $applicationExitCode. Details: $logPath"
    }
}
catch {
    $message = "[Startup failed] $($_.Exception.Message)"
    Write-Host $message -ForegroundColor Red
    New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
    $message | Out-File -LiteralPath $logPath -Encoding Unicode
    Write-Host "Log: $logPath"
    Read-Host "Press Enter to close"
    exit 1
}
