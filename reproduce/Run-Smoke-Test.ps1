<#
Run-Smoke-Test.ps1  --  prove the ACT-R + spreadsheet-model toolchain runs in
                        the released layout by executing a short slice of ONE
                        factorial cell.

This is NOT a full reproduction (the reported factorial is 8 cells x 142 runs);
it is a fast end-to-end check that a reviewer can run after installing ACT-R.
It writes a few runs into  reproduce_output\smoke_cell<CELL>\  and prints where.

Requires: Windows, SBCL on PATH, ACT-R 7.x (see Setup-Layout.ps1 / REPRODUCE.md),
and Microsoft Excel available for the spreadsheet interface.
#>
param(
    [string]$RepoRoot,
    [ValidateSet("000","100","010","001","110","101","011","111")]
    [string]$Cell = "000",
    [int]$Runs = 3,
    [string]$ModelSource = "New_Error (3-5-2-TCP-7-21-2026).lisp"
)
$ErrorActionPreference = "Stop"
if (-not $RepoRoot) { $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }

# Bridge the layout / verify ACT-R.
& (Join-Path $PSScriptRoot "Setup-Layout.ps1") -RepoRoot $RepoRoot

$cells = @{
    "000" = "Ablation_Perfect.lisp";               "100" = "Ablation_Visual_Search_Only.lisp"
    "010" = "Ablation_Batched_Formula_Typing.lisp"; "001" = "Ablation_Correction_Checking.lisp"
    "110" = "Ablation_Visual_Plus_Batched.lisp";    "101" = "Ablation_Visual_Plus_Checking.lisp"
    "011" = "Ablation_Batched_Plus_Checking.lisp";  "111" = "Ablation_Full_Realistic.lisp"
}

$seedFile = Join-Path $RepoRoot "analysis\batch_provenance\draft36_check090_factorial\seed_list.txt"
if (-not (Test-Path -LiteralPath $seedFile)) { throw "Seed list missing: $seedFile" }
$outRoot = Join-Path $RepoRoot ("reproduce_output\smoke_cell{0}" -f $Cell)
if (Test-Path -LiteralPath $outRoot) { Remove-Item -Recurse -Force -LiteralPath $outRoot }
New-Item -ItemType Directory -Path $outRoot -Force | Out-Null

# Only the vars the frozen shard driver actually reads.  Selecting the reported
# per-token-formula-check build is done ENTIRELY by SPREADSHEET_ABLATION_BASE_MODEL;
# its default fallback is the older build (see REPRODUCE.md, "reproduction trap").
$env:CELL_SOURCE = $cells[$Cell]
$env:CELL_CODE   = $Cell
$env:SEED_FILE   = $seedFile
$env:SEED_START  = "1"
$env:SEED_COUNT  = "$Runs"
$env:BATCH_ROOT  = ($outRoot -replace "\\", "/") + "/"
$env:SPREADSHEET_ABLATION_BASE_MODEL = $ModelSource
$env:ACTR_RECOMPILE = "1"    # smoke run: compile FASLs once (safe, single process)

Write-Host "Smoke: cell $Cell ($($cells[$Cell])), $Runs runs, base = $ModelSource"
Push-Location $RepoRoot
try {
    & sbcl --dynamic-space-size 4096 --noinform --non-interactive --load "Spreadsheet/Run_Ablation_2x2x2_Shard.lisp"
    if ($LASTEXITCODE -ne 0) { throw "sbcl exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
Write-Host ""
Write-Host "Smoke run OK. Output: $outRoot"
Write-Host "Check $outRoot\batch_summary.csv for per-run completion times."
