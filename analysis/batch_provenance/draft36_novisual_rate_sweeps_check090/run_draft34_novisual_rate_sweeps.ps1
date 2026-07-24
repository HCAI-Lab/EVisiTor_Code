# Error-rate sweeps with visual search disabled (cell 011: V=0, B=1, C=1), run
# on the de-duplicated model build.  Two independent one-factor-at-a-time
# sweeps, 142 runs each, same archived seed sequence as the factorial:
#   formula rate 0-5%, word rate held at 6.3%
#   word rate    0-5%, formula rate held at 3.4%
param(
    [string]$BatchRoot = "G:\ACT-RModels\Spreadsheet\logs\draft34_20260722_novisual_rate_sweeps",
    [string]$SeedFile = "G:\ACT-RModels\Spreadsheet\logs\draft34_20260722_dedup_factorial\seed_list.txt",
    [string]$ModelSource = "New_Error (3-5-2-TCP-7-21-2026).lisp",
    [int]$Runs = 142,
    [int]$MaxConcurrent = 12,
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
    "G:\ACT-RModels\Spreadsheet\Run_Ablation_2x2x2_Shard.lisp",
    "G:\ACT-RModels\Spreadsheet\Ablation_NoVisual_Rates.lisp",
    "G:\ACT-RModels\Spreadsheet\run_draft34_novisual_rate_sweeps.ps1",
    $SeedFile
)
$hashes = [ordered]@{}
foreach ($source in $sourceFiles) {
    if (-not (Test-Path -LiteralPath $source)) { throw "Source missing: $source" }
    Copy-Item -LiteralPath $source -Destination $frozenDir
    $hashes[(Split-Path $source -Leaf)] = (Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash.ToLowerInvariant()
}
$design = [ordered]@{
    created_at = (Get-Date).ToString("s")
    model_source = $ModelSource
    cell_code = "011"
    visual_search = $false
    formula_lookback = $true
    error_correction = $true
    runs_per_condition = $Runs
    power = 0.99
    alpha = 0.05
    sidedness = "two-tailed"
    cohens_d = 0.5
    rates_pct = @(0, 1, 2, 3, 4, 5)
    formula_sweep_fixed_word_rate = 0.063
    word_sweep_fixed_formula_rate = 0.034
    source_sha256 = $hashes
}
$design | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $BatchRoot "design_manifest.json")

$rates = 0..5 | ForEach-Object { $_ / 100.0 }
$work = @()
foreach ($rate in $rates) {
    $tag = "{0:D3}" -f [int][math]::Round(1000 * $rate)
    $work += @{
        name = "formula_$tag"; formula = $rate; word = 0.063
        root = Join-Path $BatchRoot "formula_rate_$tag"
    }
    $work += @{
        name = "word_$tag"; formula = 0.034; word = $rate
        root = Join-Path $BatchRoot "word_rate_$tag"
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
        $env:CELL_SOURCE = "Ablation_NoVisual_Rates.lisp"
        $env:CELL_CODE = "011"
        $env:SEED_FILE = $SeedFile
        $env:SEED_START = "1"
        $env:SEED_COUNT = "$Runs"
        $env:BATCH_ROOT = ($w.root -replace "\\", "/") + "/"
        $env:SPREADSHEET_ABLATION_BASE_MODEL = $ModelSource
        $env:FORMULA_TYPO_RATE = [string]::Format(
            [Globalization.CultureInfo]::InvariantCulture, "{0:0.000}", $w.formula)
        $env:WORD_TYPO_RATE = [string]::Format(
            [Globalization.CultureInfo]::InvariantCulture, "{0:0.000}", $w.word)
        $p = Start-Process -FilePath "sbcl" -PassThru -NoNewWindow `
            -WorkingDirectory "G:\ACT-RModels" `
            -ArgumentList "--dynamic-space-size", "$DynamicSpaceMB", "--noinform", "--non-interactive", "--load", "Spreadsheet/Run_Ablation_2x2x2_Shard.lisp" `
            -RedirectStandardOutput (Join-Path $logDir "$($w.name)_console.txt") `
            -RedirectStandardError (Join-Path $logDir "$($w.name)_err.txt")
        $running += @{ proc = $p; work = $w; started = Get-Date }
        Write-Host "Launched $($w.name) pid=$($p.Id)"
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
Write-Host "All 12 no-visual-search error-rate conditions completed."
