# Legacy 150-run ablation driver (superseded by the 2x2x2 factorial; kept for
# history -- see README.md). Paths are resolved for the released layout; the
# frozen Run_Ablation_150.lisp still loads actr7.x/ and Spreadsheet/ relative to
# the working directory, so reproduce/Setup-Layout.ps1 bridges those junctions.
param(
    [string]$RepoRoot,
    [string]$SpreadsheetDir,
    [string]$ActrHome
)
$ErrorActionPreference = "Stop"

if (-not $RepoRoot)       { $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path }
if (-not $SpreadsheetDir) { $SpreadsheetDir = Join-Path $RepoRoot "models\spreadsheet_excel" }
if (-not $ActrHome)       { $ActrHome = if ($env:EVISITOR_ACTR_HOME) { $env:EVISITOR_ACTR_HOME } else { Join-Path $RepoRoot "actr7.x" } }

& (Join-Path $RepoRoot "reproduce\Setup-Layout.ps1") -RepoRoot $RepoRoot -SpreadsheetDir $SpreadsheetDir -ActrHome $ActrHome

$logDir = Join-Path $RepoRoot "reproduce_output\ablation_150"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

Set-Location $RepoRoot
& sbcl --noinform --non-interactive --load "Spreadsheet\Run_Ablation_150.lisp" *> (Join-Path $logDir "ablation_150_formula_latest.combined.log")
