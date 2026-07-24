<#
Setup-Layout.ps1  --  bridge the released repo layout to what the frozen
                      Lisp drivers expect, without editing any hashed source.

The frozen shard drivers (models/spreadsheet_excel/Run_Ablation_2x2x2_Shard.lisp,
Run_CheckProb_Shard.lisp) load
    (load "actr7.x/load-act-r.lisp")
    (load "Spreadsheet/Complete_error_model_tcp.lisp")
relative to the process working directory, using the ORIGINAL monorepo layout
(a flat "Spreadsheet\" folder and a sibling "actr7.x\").  In this release the
models live under models/spreadsheet_excel/ and ACT-R is not bundled.

This script creates two directory junctions at the repo root so those relative
loads resolve, and verifies that ACT-R 7.x is available.  It is idempotent and
needs no administrator rights (directory junctions do not).

    ACT-R is NOT included (it is ~tens of MB and separately licensed).  Get it
    from  https://github.com/asmaloney/ACT-R   (or the CMU distribution at
    http://act-r.psy.cmu.edu/software/) and either unpack it to  <repo>\actr7.x
    or point EVISITOR_ACTR_HOME at the folder that contains load-act-r.lisp.
#>
param(
    [string]$RepoRoot,
    [string]$SpreadsheetDir,
    [string]$ActrHome
)
$ErrorActionPreference = "Stop"

if (-not $RepoRoot)        { $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
if (-not $SpreadsheetDir)  { $SpreadsheetDir = Join-Path $RepoRoot "models\spreadsheet_excel" }
if (-not $ActrHome) {
    $ActrHome = if ($env:EVISITOR_ACTR_HOME) { $env:EVISITOR_ACTR_HOME } else { Join-Path $RepoRoot "actr7.x" }
}

function Set-DirLink {
    param([string]$Link, [string]$Target)
    if (-not (Test-Path -LiteralPath $Target)) { throw "Link target does not exist: $Target" }
    if (Test-Path -LiteralPath $Link) {
        $item = Get-Item -LiteralPath $Link -Force
        if ($item.LinkType) {
            Write-Host "ok: $Link already links to $($item.Target)"
        } else {
            Write-Host "ok: $Link already exists (real directory) -- leaving as is"
        }
        return
    }
    New-Item -ItemType Junction -Path $Link -Target $Target | Out-Null
    Write-Host "linked: $Link -> $Target"
}

# 1. ACT-R runtime must be provided by the user.
if (-not (Test-Path -LiteralPath (Join-Path $ActrHome "load-act-r.lisp"))) {
    throw @"
ACT-R 7.x not found.  Looked for load-act-r.lisp under:
    $ActrHome

Download ACT-R 7.x from  https://github.com/asmaloney/ACT-R  and either
  * unpack it to   $RepoRoot\actr7.x   (so $RepoRoot\actr7.x\load-act-r.lisp exists), or
  * set the environment variable EVISITOR_ACTR_HOME to the ACT-R folder.
See REPRODUCE.md.
"@
}

# 2. Bridge the two relative paths the frozen drivers expect.
Set-DirLink -Link (Join-Path $RepoRoot "Spreadsheet") -Target $SpreadsheetDir
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot "actr7.x"))) {
    Set-DirLink -Link (Join-Path $RepoRoot "actr7.x") -Target $ActrHome
}

Write-Host ""
Write-Host "Layout ready. Working directory for model runs: $RepoRoot"
Write-Host "  Spreadsheet/ -> $SpreadsheetDir"
Write-Host "  actr7.x/     -> $ActrHome"
