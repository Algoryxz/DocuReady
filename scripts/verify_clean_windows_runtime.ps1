# DocuReady Windows release qualification.
# Runs on a disposable Windows machine/VM. This script performs real install,
# launch, bundled-sidecar checks, and uninstall. It does not claim network isolation.
[CmdletBinding()]
param(
    [string]$SetupExe = "apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-Setup.exe",
    [string]$ZipArchive = "apps/desktop/out/make/zip/win32/x64/DocuReady-win32-x64-0.1.0.zip",
    [string]$LogFile = "docs/clean_machine_validation.log",
    [int]$LaunchTimeoutSeconds = 30
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Location).Path
$LogPath = Join-Path $RepoRoot $LogFile
$LogDir = Split-Path -Parent $LogPath
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
if (Test-Path $LogPath) { Remove-Item $LogPath -Force }

function Write-Log([string]$Message) {
    $line = "[$((Get-Date).ToString('s'))] $Message"
    Write-Host $line
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}
function Assert-File([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "$Label missing: $Path" }
}
function Find-AppExe([string]$Root) {
    $match = Get-ChildItem -LiteralPath $Root -Filter "DocuReady.exe" -File -Recurse |
        Where-Object { $_.FullName -notmatch '\\(uninstall|SquirrelTemp)\\' } |
        Select-Object -First 1
    if (-not $match) { throw "DocuReady.exe not found below $Root" }
    return $match.FullName
}
function Invoke-SidecarHealth([string]$SidecarExe, [string]$Workspace) {
    Assert-File $SidecarExe "Bundled sidecar"
    New-Item -ItemType Directory -Path $Workspace -Force | Out-Null
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $SidecarExe
    $psi.WorkingDirectory = Split-Path -Parent $SidecarExe
    $psi.UseShellExecute = $false
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.EnvironmentVariables["PATH"] = $env:PATH
    $psi.EnvironmentVariables["DOCUREADY_WORKSPACE_ROOT"] = $Workspace
    $proc = [System.Diagnostics.Process]::Start($psi)
    try {
        $proc.StandardInput.WriteLine('{"protocol":1,"id":"release-health","method":"health","params":{}}')
        $proc.StandardInput.Flush()
        $task = $proc.StandardOutput.ReadLineAsync()
        if (-not $task.Wait(30000)) { throw "Sidecar health handshake timed out." }
        $line = $task.Result
        if ([string]::IsNullOrWhiteSpace($line)) {
            $stderr = $proc.StandardError.ReadToEnd()
            throw "Sidecar exited without a health response. $stderr"
        }
        $response = $line | ConvertFrom-Json
        if (-not $response.ok) { throw "Sidecar health returned an error: $line" }
        if (-not $response.result.ocr_available -or -not $response.result.is_bundled) {
            throw "Bundled OCR unavailable. Health response: $line"
        }
        Write-Log "PASS: bundled sidecar health and OCR resource discovery. $line"
        $proc.StandardInput.WriteLine('{"protocol":1,"id":"release-shutdown","method":"shutdown","params":{}}')
        $proc.StandardInput.Flush()
        $proc.WaitForExit(5000) | Out-Null
    }
    finally {
        if (-not $proc.HasExited) { $proc.Kill(); $proc.WaitForExit() }
        $proc.Dispose()
    }
}
function Test-AppLaunch([string]$ExePath, [string]$Label) {
    $appDir = Split-Path -Parent $ExePath
    $proc = Start-Process -FilePath $ExePath -WorkingDirectory $appDir -PassThru
    try {
        $deadline = (Get-Date).AddSeconds($LaunchTimeoutSeconds)
        $windowReady = $false
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 500
            $proc.Refresh()
            if ($proc.HasExited) { throw "$Label exited during startup (exit code $($proc.ExitCode))." }
            if ($proc.MainWindowHandle -ne 0) { $windowReady = $true; break }
        }
        if (-not $windowReady) { throw "$Label process remained alive but no main window appeared within $LaunchTimeoutSeconds seconds." }
        Write-Log "PASS: $Label opened a visible main window (PID $($proc.Id))."
    }
    finally {
        if (-not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            $proc.WaitForExit(10000) | Out-Null
        }
        $proc.Dispose()
    }
}

$originalPath = $env:PATH
$installRoot = Join-Path $env:LOCALAPPDATA "DocuReady"
$portableRoot = Join-Path $env:TEMP ("DocuReady_Portable_" + [Guid]::NewGuid().ToString("N"))
$workspace = Join-Path $env:TEMP ("DocuReady_Release_" + [Guid]::NewGuid().ToString("N"))
$installedByThisRun = $false
$overallFailure = $null

try {
    Write-Log "DOCUREADY WINDOWS RELEASE QUALIFICATION START"
    $cleanPath = "$env:SystemRoot\System32;$env:SystemRoot;$env:SystemRoot\System32\Wbem;$env:SystemRoot\System32\WindowsPowerShell\v1.0"
    $env:PATH = $cleanPath
    Remove-Item Env:DOCUREADY_* -ErrorAction SilentlyContinue
    Remove-Item Env:TESSDATA_PREFIX -ErrorAction SilentlyContinue
    if (Get-Command python -ErrorAction SilentlyContinue) { throw "Host Python remains visible on scrubbed PATH." }
    if (Get-Command tesseract -ErrorAction SilentlyContinue) { throw "Host Tesseract remains visible on scrubbed PATH." }
    Write-Log "PASS: host Python and Tesseract are unavailable on scrubbed PATH."

    # Portable distribution: extraction, sidecar handshake, and actual UI launch.
    $zipPath = Join-Path $RepoRoot $ZipArchive
    Assert-File $zipPath "Portable ZIP"
    Write-Log "Portable ZIP SHA-256: $((Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash)"
    Expand-Archive -LiteralPath $zipPath -DestinationPath $portableRoot -Force
    $portableExe = Find-AppExe $portableRoot
    $portableDir = Split-Path -Parent $portableExe
    $portableSidecar = Join-Path $portableDir "resources\docuready_sidecar\docuready_sidecar.exe"
    Invoke-SidecarHealth $portableSidecar (Join-Path $workspace "portable")
    Test-AppLaunch $portableExe "Portable DocuReady"

    # Squirrel installer: install, verify installed app, launch, then uninstall.
    $setupPath = Join-Path $RepoRoot $SetupExe
    Assert-File $setupPath "Squirrel installer"
    Write-Log "Installer SHA-256: $((Get-FileHash -LiteralPath $setupPath -Algorithm SHA256).Hash)"
    if (Test-Path $installRoot) {
        throw "Existing $installRoot detected. Run this on a disposable Windows profile/VM."
    }
    $setup = Start-Process -FilePath $setupPath -ArgumentList "--silent" -Wait -PassThru
    Write-Log "Squirrel Setup.exe exit code: $($setup.ExitCode)"
    if ($setup.ExitCode -ne 0) { throw "Squirrel installer failed with exit code $($setup.ExitCode)." }
    $installedByThisRun = $true

    $updateExe = Join-Path $installRoot "Update.exe"
    Assert-File $updateExe "Squirrel Update.exe"
    $installedExe = Find-AppExe $installRoot
    $installedDir = Split-Path -Parent $installedExe
    $installedSidecar = Join-Path $installedDir "resources\docuready_sidecar\docuready_sidecar.exe"
    Invoke-SidecarHealth $installedSidecar (Join-Path $workspace "installed")
    Test-AppLaunch $installedExe "Installed DocuReady"

    & $updateExe --uninstall -s
    if ($LASTEXITCODE -ne 0) { throw "Squirrel uninstall failed with exit code $LASTEXITCODE." }
    Start-Sleep -Seconds 2
    if (Test-Path $installRoot) { throw "Squirrel uninstall left install directory behind: $installRoot" }
    $installedByThisRun = $false
    Write-Log "PASS: Squirrel install, installed UI launch, bundled sidecar, and uninstall."
    Write-Log "RESULT: PASS"
}
catch {
    $overallFailure = $_
    Write-Log "RESULT: FAIL — $($_.Exception.Message)"
}
finally {
    if ($installedByThisRun -and (Test-Path (Join-Path $installRoot "Update.exe"))) {
        try {
            & (Join-Path $installRoot "Update.exe") --uninstall -s
            Start-Sleep -Seconds 2
        } catch { Write-Log "WARNING: automatic uninstall cleanup failed: $_" }
    }
    if (Test-Path $portableRoot) { Remove-Item -LiteralPath $portableRoot -Recurse -Force -ErrorAction SilentlyContinue }
    if (Test-Path $workspace) { Remove-Item -LiteralPath $workspace -Recurse -Force -ErrorAction SilentlyContinue }
    $env:PATH = $originalPath
}
if ($overallFailure) { throw $overallFailure }
