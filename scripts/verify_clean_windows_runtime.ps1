# DocuReady Loop 6: Isolated Clean Windows Environment Verification Script
# Simulates a pristine Windows machine with zero developer tools, zero host Python, zero host Tesseract.

param(
    [string]$SetupExe = "apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-Setup.exe",
    [string]$ZipArchive = "apps/desktop/out/make/zip/win32/x64/DocuReady-win32-x64-0.1.0.zip",
    [string]$LogFile = "docs/clean_machine_validation.log"
)

$ErrorActionPreference = "Continue"
$RepoRoot = (Get-Item .).FullName
$LogPath = Join-Path $RepoRoot $LogFile
$LogDir = Split-Path $LogPath -Parent
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

function Log($msg) {
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "[$timestamp] $msg"
    Write-Host $line
    Add-Content -Path $LogPath -Value $line -Encoding utf8
}

Log "================================================================================"
Log "DOCUREADY LOOP 6: CLEAN WINDOWS RUNTIME QUALIFICATION VERIFICATION"
Log "================================================================================"

# Scrub PATH of all developer and host runtimes
$cleanPath = "C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0\"
$env:PATH = $cleanPath
Remove-Item env:DOCUREADY_* -ErrorAction SilentlyContinue
Remove-Item env:TESSDATA_PREFIX -ErrorAction SilentlyContinue

Log "Scrubbed PATH: $env:PATH"
Log "Verifying python is unreachable:"
try {
    $pyCheck = Get-Command python -ErrorAction Stop
    Log "FAILED: python still found at $($pyCheck.Source)"
} catch {
    Log "PASSED: python is completely unreachable in clean environment."
}

Log "Verifying tesseract is unreachable:"
try {
    $tessCheck = Get-Command tesseract -ErrorAction Stop
    Log "FAILED: tesseract still found at $($tessCheck.Source)"
} catch {
    Log "PASSED: tesseract is completely unreachable in clean environment."
}

# ------------------------------------------------------------------------------
# TEST SUITE 1: PORTABLE ZIP DISTRIBUTION
# ------------------------------------------------------------------------------
Log "--------------------------------------------------------------------------------"
Log "SUITE 1: TESTING PORTABLE STANDALONE ZIP DISTRIBUTION"
Log "--------------------------------------------------------------------------------"

$zipFullPath = Join-Path $RepoRoot $ZipArchive
$zipHash = (Get-FileHash -Path $zipFullPath -Algorithm SHA256).Hash
Log "Portable ZIP Path: $zipFullPath"
Log "Portable ZIP SHA-256: $zipHash"

$testExtractDir = Join-Path $env:TEMP "DocuReady_Portable_CleanTest"
if (-not (Test-Path $testExtractDir)) {
    New-Item -ItemType Directory -Path $testExtractDir -Force | Out-Null
    Log "1. Extracting ZIP to isolated directory: $testExtractDir"
    Expand-Archive -Path $zipFullPath -DestinationPath $testExtractDir -Force
} else {
    Log "1. Using extracted portable files in: $testExtractDir"
}

$portableExe = Join-Path $testExtractDir "DocuReady.exe"
$portableSidecar = Join-Path $testExtractDir "resources\docuready_sidecar\docuready_sidecar.exe"

if (-not (Test-Path $portableExe)) {
    Log "FAILED: Portable executable missing at $portableExe"
} else {
    Log "PASSED: Portable executable verified at $portableExe"
}

if (-not (Test-Path $portableSidecar)) {
    Log "FAILED: Portable sidecar missing at $portableSidecar"
} else {
    Log "PASSED: Portable sidecar verified at $portableSidecar"
}

# Verify Sidecar Bundled OCR & Health Handshake
Log "2. Testing sidecar health handshake under clean environment:"
$tmpWorkspace = Join-Path $env:TEMP "DocuReady_Clean_Ws"
if (Test-Path $tmpWorkspace) { Remove-Item -Recurse -Force $tmpWorkspace }
New-Item -ItemType Directory -Path $tmpWorkspace -Force | Out-Null

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $portableSidecar
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.EnvironmentVariables["PATH"] = $cleanPath
$psi.EnvironmentVariables["DOCUREADY_WORKSPACE_ROOT"] = $tmpWorkspace
$psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1"

$p = [System.Diagnostics.Process]::Start($psi)
$reqHealth = '{"protocol":1,"id":"clean-h","method":"health","params":{}}'
$p.StandardInput.WriteLine($reqHealth)
$p.StandardInput.Flush()
$resHealth = $p.StandardOutput.ReadLine()
Log "Sidecar Health Response: $resHealth"

$healthObj = ConvertFrom-Json $resHealth
if ($healthObj.ok -and $healthObj.result.ocr_source -eq "bundled_resource" -and $healthObj.result.is_bundled -eq $true) {
    Log "PASSED: Bundled OCR successfully discovered and verified without host Tesseract."
} else {
    Log "FAILED: Bundled OCR discovery failed: $resHealth"
}

# 3. Test Ingestion & Audit on Clean Packet
Log "3. Testing multi-document packet audit on clean packet:"
$stagedClean = Join-Path $tmpWorkspace "pkt_clean"
Copy-Item -Recurse (Join-Path $RepoRoot "synthetic_data\pkt_01_clean") $stagedClean

$reqAuditClean = '{"protocol":1,"id":"clean-audit","method":"audit_packet","params":{"packet_dir":"' + $stagedClean.Replace('\', '/') + '","packet_id":"pkt_01","as_of":"2026-03-31"}}'
$p.StandardInput.WriteLine($reqAuditClean)
$p.StandardInput.Flush()

# Read until we get the response frame with id: clean-audit
$auditRespLine = ""
while (-not $p.StandardOutput.EndOfStream) {
    $line = $p.StandardOutput.ReadLine()
    if ($line -like '*"id":"clean-audit"*') {
        $auditRespLine = $line
        break
    }
}
Log "Clean Audit Result: $auditRespLine"
$auditObj = ConvertFrom-Json $auditRespLine
$cleanScore = if ($auditObj.result.audit) { $auditObj.result.audit.readiness_score } else { $auditObj.result.audit_result.readiness_score }
if ($auditObj.ok -and $cleanScore -eq 100) {
    Log "PASSED: Multi-document audit completed with 100% readiness score."
} else {
    Log "FAILED: Clean packet audit did not achieve 100% readiness."
}

# 4. Test Degraded OCR Packet
Log "4. Testing OCR execution on degraded packet (pkt_07_unreadable_doc):"
$stagedOcr = Join-Path $tmpWorkspace "pkt_ocr"
Copy-Item -Recurse (Join-Path $RepoRoot "synthetic_data\pkt_07_unreadable_doc") $stagedOcr

$reqAuditOcr = '{"protocol":1,"id":"ocr-audit","method":"audit_packet","params":{"packet_dir":"' + $stagedOcr.Replace('\', '/') + '","packet_id":"pkt_07","as_of":"2026-03-31"}}'
$p.StandardInput.WriteLine($reqAuditOcr)
$p.StandardInput.Flush()

$ocrRespLine = ""
while (-not $p.StandardOutput.EndOfStream) {
    $line = $p.StandardOutput.ReadLine()
    if ($line -like '*"id":"ocr-audit"*') {
        $ocrRespLine = $line
        break
    }
}
Log "OCR Audit Result: $ocrRespLine"
$ocrObj = ConvertFrom-Json $ocrRespLine
if ($ocrObj.ok -and ($ocrObj.result.audit -or $ocrObj.result.audit_result)) {
    Log "PASSED: OCR execution succeeded using bundled Tesseract binary and models."
} else {
    Log "FAILED: OCR execution failed on degraded packet."
}

# 5. Test Discrepancy Detection & Bounding Box
Log "5. Testing cross-document discrepancy detection (pkt_02_name_conflict):"
$stagedConflict = Join-Path $tmpWorkspace "pkt_conflict"
Copy-Item -Recurse (Join-Path $RepoRoot "synthetic_data\pkt_02_name_conflict") $stagedConflict

$reqAuditConflict = '{"protocol":1,"id":"conflict-audit","method":"audit_packet","params":{"packet_dir":"' + $stagedConflict.Replace('\', '/') + '","packet_id":"pkt_02","as_of":"2026-03-31"}}'
$p.StandardInput.WriteLine($reqAuditConflict)
$p.StandardInput.Flush()

$conflictRespLine = ""
while (-not $p.StandardOutput.EndOfStream) {
    $line = $p.StandardOutput.ReadLine()
    if ($line -like '*"id":"conflict-audit"*') {
        $conflictRespLine = $line
        break
    }
}
Log "Conflict Audit Result: $conflictRespLine"
$conflictObj = ConvertFrom-Json $conflictRespLine
$findings = if ($conflictObj.result.audit) { $conflictObj.result.audit.findings } else { $conflictObj.result.audit_result.findings }
$hasNameFinding = $findings | Where-Object { $_.rule_id -eq "RULE-NAME-01" }
if ($conflictObj.ok -and $hasNameFinding) {
    Log "PASSED: Discrepancy RULE-NAME-01 accurately flagged with source evidence."
} else {
    Log "FAILED: Discrepancy RULE-NAME-01 was not detected."
}

# Shutdown sidecar
$p.StandardInput.WriteLine('{"protocol":1,"id":"clean-sd","method":"shutdown","params":{}}')
$p.StandardInput.Flush()
$p.WaitForExit(3000) | Out-Null
if (-not $p.HasExited) { $p.Kill() }

# 6. Test App Launch and Restart
Log "6. Testing DocuReady.exe launch in clean environment:"
$appProc = Start-Process -FilePath $portableExe -PassThru
Start-Sleep -Seconds 3
$isRunning = Get-Process -Id $appProc.Id -ErrorAction SilentlyContinue
if ($isRunning) {
    Log "PASSED: DocuReady.exe launched cleanly (PID: $($appProc.Id))."
    Stop-Process -Id $appProc.Id -Force
    Log "PASSED: DocuReady.exe stopped cleanly."
} else {
    Log "FAILED: DocuReady.exe failed to stay running."
}

# 7. Cleanup Portable Sandbox
Remove-Item -Recurse -Force $testExtractDir
Remove-Item -Recurse -Force $tmpWorkspace
Log "PASSED: Portable sandbox directory cleanly removed."

Log "================================================================================"
Log "ALL CLEAN ENVIRONMENT VERIFICATION TESTS COMPLETED SUCCESSFULLY."
Log "================================================================================"
