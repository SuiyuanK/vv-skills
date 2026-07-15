param(
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir
$TemplateDir = Join-Path $SkillDir "plan-template"
$PlanDir = Join-Path $ProjectRoot "plan"

New-Item -ItemType Directory -Path $PlanDir -Force | Out-Null

$copied = 0
$names = @(
    "project-overview.md",
    "progress.md",
    "notes.md",
    "outline.md",
    "stage-gates.md"
)

foreach ($name in $names) {
    $src = Join-Path $TemplateDir $name
    $dst = Join-Path $PlanDir $name

    if (-not (Test-Path -LiteralPath $src)) {
        Write-Host "[WARN] template missing: $src"
        continue
    }

    if (Test-Path -LiteralPath $dst) {
        Write-Host "[SKIP] exists: $dst"
    } else {
        Copy-Item -LiteralPath $src -Destination $dst
        Write-Host "[ADD]  $dst"
        $copied += 1
    }
}

Write-Host "[DONE] plan bootstrap finished. files_copied=$copied plan_dir=$PlanDir"
