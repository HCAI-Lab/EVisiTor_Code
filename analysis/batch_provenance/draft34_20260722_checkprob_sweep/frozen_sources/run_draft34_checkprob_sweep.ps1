# Formula-check-probability sweep, visual search disabled (cell 011), tasks
# 1-10 executed and tasks 3-10 scored.  11 conditions from 0.0 to 1.0 in steps
# of 0.1, 142 runs each, on the de-duplicated model build.
param(
    [string]$BatchRoot = "G:\ACT-RModels\Spreadsheet\logs\draft34_20260722_checkprob_sweep",
    [string]$SeedFile = "G:\ACT-RModels\Spreadsheet\logs\draft34_20260722_dedup_factorial\seed_list.txt",
    [string]$ModelSource = "New_Error (3-5-2-TCP-7-21-2026).lisp",
    [int]$Runs = 142,
    [int]$MaxConcurrent = 12,
    [int]$StopAfterTask = 10,
    [int]$DynamicSpaceMB = 4096
)

$ErrorActionPreference = "Stop"
Set-Location "G:\ACT-RModels"
if (-not (Test-Path $SeedFile)) { throw "Seed file missing: $SeedFile" }
if (Test-Path $BatchRoot) { throw "Output root already exists: $BatchRoot" }

New-Item -ItemType Directory -Path $BatchRoot | Out-Null
$frozenDir = Join-Path $BatchRoot "frozen_sources"
New-Item -ItemType Directory -Path $frozenDir | Out-Null
$sourceFiles = @(
    (Join-Path "G:\ACT-RModels\Spreadsheet" $ModelSource),
    "G:\ACT-RModels\Spreadsheet\fucntion_new_tcp.lisp",
    "G:\ACT-RModels\Spreadsheet\Ablation_support.lisp",
    "G:\ACT-RModels\Spreadsheet\running_model_v4.lisp",
    "G:\ACT-RModels\Spreadsheet\Complete_error_model_tcp.lisp",
    "G:\ACT-RModels\Spreadsheet\Visicon_generator_V3.lisp",
    "G:\ACT-RModels\Spreadsheet\Run_CheckProb_Shard.lisp",
    "G:\ACT-RModels\Spreadsheet\Ablation_NoVisual_CheckProb.lisp",
    "G:\ACT-RModels\Spreadsheet\run_draft34_checkprob_sweep.ps1",
    $SeedFile
)
$hashes = [ordered]@{}
foreach ($source in $sourceFiles) {
    if (-not (Test-Path -LiteralPath $source)) { throw "Source missing: $source" }
    Copy-Item -LiteralPath $source -Destination $frozenDir
    $hashes[(Split-Path $source -Leaf)] = (Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash.ToLowerInvariant()
}

$probs = 0..10 | ForEach-Object { $_ / 10.0 }
$design = [ordered]@{
    created_at = (Get-Date).ToString("s")
    model_source = $ModelSource
    cell_code = "011"
    visual_search = $false
    formula_lookback = $true
    error_correction = $true
    runs_per_condition = $Runs
    stop_after_task = $StopAfterTask
    scored_tasks = @(3, 4, 5, 6, 7, 8, 9, 10)
    unscored_state_building_tasks = @(1, 2)
    check_probabilities = $probs
    formula_typo_rate = 0.034
    word_typo_rate = 0.063
    purpose = "parameter fit: check probability minimizing RMSE on tasks 3-10"
    source_sha256 = $hashes
}
$design | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $BatchRoot "design_manifest.json")

$work = @()
foreach ($p in $probs) {
    $tag = "{0:D3}" -f [int][math]::Round(100 * $p)
    $work += @{
        name = "check_$tag"; prob = $p
        root = Join-Path $BatchRoot "check_prob_$tag"
    }
}

$logDir = Join-Path $BatchRoot "console_logs"
New-Item -ItemType Directory -Path $logDir | Out-Null
$running = @()
$done = @()
$queue = [System.Collections.Queue]::new()
foreach ($w in $work) { $queue.Enqueue($w) }

while ($queue.Count -or $running.Count) {
    while ($queue.Count -and $running.Count -lt $MaxConcurrent) {
        $w = $queue.Dequeue()
        if (Test-Path $w.root) { throw "Output already exists: $($w.root)" }
        $env:CELL_SOURCE = "Ablation_NoVisual_CheckProb.lisp"
        $env:CELL_CODE = "011"
        $env:SEED_FILE = $SeedFile
        $env:SEED_START = "1"
        $env:SEED_COUNT = "$Runs"
        $env:BATCH_ROOT = ($w.root -replace "\\", "/") + "/"
        $env:SPREADSHEET_ABLATION_BASE_MODEL = $ModelSource
        $env:STOP_AFTER_TASK = "$StopAfterTask"
        $env:FORMULA_CHECK_PROB = [string]::Format(
            [Globalization.CultureInfo]::InvariantCulture, "{0:0.000}", $w.prob)
        $p = Start-Process -FilePath "sbcl" -PassThru -NoNewWindow `
            -WorkingDirectory "G:\ACT-RModels" `
            -ArgumentList "--dynamic-space-size", "$DynamicSpaceMB", "--noinform", "--non-interactive", "--load", "Spreadsheet/Run_CheckProb_Shard.lisp" `
            -RedirectStandardOutput (Join-Path $logDir "$($w.name)_console.txt") `
            -RedirectStandardError (Join-Path $logDir "$($w.name)_err.txt")
        $running += @{ proc = $p; work = $w; started = Get-Date }
        Write-Host "Launched $($w.name) prob=$($env:FORMULA_CHECK_PROB) pid=$($p.Id)"
    }
    Start-Sleep -Seconds 10
    $still = @()
    foreach ($r in $running) {
        if ($r.proc.HasExited) {
            $done += @{ name = $r.work.name; exit = $r.proc.ExitCode }
            Write-Host "Finished $($r.work.name) exit=$($r.proc.ExitCode)"
        } else { $still += $r }
    }
    $running = $still
}

$failed = @($done | Where-Object { $_.exit -ne 0 })
if ($failed.Count) {
    $failed | ForEach-Object { Write-Host "FAILED $($_.name) exit=$($_.exit)" }
    exit 1
}
Write-Host "All 11 check-probability conditions completed."
