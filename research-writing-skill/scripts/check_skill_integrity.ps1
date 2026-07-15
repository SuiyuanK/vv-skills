param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"
$failures = New-Object System.Collections.Generic.List[string]

function Add-Failure {
    param([string]$Message)
    $failures.Add($Message) | Out-Null
}

function Assert-File {
    param([string]$RelativePath)
    $path = Join-Path $Root $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        Add-Failure "Missing file: $RelativePath"
    }
}

function Assert-Contains {
    param(
        [string]$RelativePath,
        [string]$Pattern,
        [string]$Label
    )
    $path = Join-Path $Root $RelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        Add-Failure "Cannot inspect missing file: $RelativePath"
        return
    }
    $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
    if ($text -notmatch $Pattern) {
        Add-Failure "$RelativePath missing: $Label"
    }
}

$requiredFiles = @(
    "skills/paper-orchestration/SKILL.md",
    "skills/evidence-driven-writing/SKILL.md",
    "skills/evidence-driven-writing/references/gpr-introduction-example.md",
    "skills/experiment-results-planning/SKILL.md",
    "scripts/research_quality_gate.ps1"
)

foreach ($file in $requiredFiles) {
    Assert-File $file
}

$frontmatter = @{
    "skills/paper-orchestration/SKILL.md" = "name:\s*paper-orchestration"
    "skills/evidence-driven-writing/SKILL.md" = "name:\s*evidence-driven-writing"
    "skills/experiment-results-planning/SKILL.md" = "name:\s*experiment-results-planning"
}

foreach ($entry in $frontmatter.GetEnumerator()) {
    Assert-Contains $entry.Key $entry.Value "valid skill frontmatter"
    Assert-Contains $entry.Key "description:\s*Use when" "CSO-style trigger description"
}

Assert-Contains "skills/using-research-writing/SKILL.md" "paper-orchestration" "orchestration route"
Assert-Contains "skills/using-research-writing/SKILL.md" "capability-use audit" "capability-use audit gate"
Assert-Contains "skills/using-research-writing/SKILL.md" "paper-orchestration.*writing-chapters|quality" "medium/full-paper trigger"
Assert-Contains "skills/using-research-writing/SKILL.md" "paper-orchestration.*shape=box" "DOT flow includes orchestration"

Assert-Contains "skills/writing-chapters/SKILL.md" "evidence-driven-writing" "evidence-driven chapter routing"
Assert-Contains "skills/writing-chapters/SKILL.md" "输入.*输出|input-to-output" "methodology input-to-output flow"
Assert-Contains "skills/writing-chapters/SKILL.md" "正文污染|contamination firewall" "body contamination firewall"
Assert-Contains "skills/writing-chapters/SKILL.md" "contamination firewall|user requirements" "user-request exclusion rule"

Assert-Contains "skills/literature-review/SKILL.md" "证据.*论点|evidence.*claim" "evidence-claim mapping"
Assert-Contains "skills/literature-review/SKILL.md" "citation slot|引用位置" "citation placement planning"

Assert-Contains "skills/figures-python/SKILL.md" "data manifest|数据清单" "figure data manifest"
Assert-Contains "skills/figures-python/SKILL.md" "mock|模拟|synthetic" "mock data boundary"

Assert-Contains "skills/verification/SKILL.md" "check_skill_integrity\.ps1" "skill integrity verification"
Assert-Contains "skills/verification/SKILL.md" "research_quality_gate\.ps1" "manuscript quality gate verification"

Assert-Contains "SKILL.md" "paper-orchestration" "main skill list includes orchestration"
Assert-Contains "SKILL.md" "evidence-driven-writing" "main skill list includes evidence-driven writing"
Assert-Contains "SKILL.md" "experiment-results-planning" "main skill list includes experiment planning"
Assert-Contains "AGENTS.md" "paper-orchestration" "agent guide mentions orchestration"
Assert-Contains "CLAUDE.md" "paper-orchestration" "Claude guide mentions orchestration"
Assert-Contains "README.md" "paper-orchestration" "Chinese README mentions orchestration"
Assert-Contains "README_EN.md" "paper-orchestration" "English README mentions orchestration"
Assert-Contains "README.md" "research_quality_gate\.ps1" "Chinese README mentions quality gate"
Assert-Contains "README_EN.md" "research_quality_gate\.ps1" "English README mentions quality gate"
Assert-Contains "AGENTS.md" "research_quality_gate\.ps1" "agent guide mentions quality gate"
Assert-Contains "CLAUDE.md" "research_quality_gate\.ps1" "Claude guide mentions quality gate"

Assert-Contains "plan-template/project-overview.md" "task-packets" "plan template includes task packets"
Assert-Contains "plan-template/project-overview.md" "evidence-map\.md" "plan template includes evidence map"
Assert-Contains "plan-template/progress.md" "Capability-use audit" "progress template includes capability-use audit"
Assert-Contains "plan-template/stage-gates.md" "D0" "stage gates include experiment protocol gate"
Assert-Contains "plan-template/stage-gates.md" "D5" "stage gates include peer review gate"

Assert-Contains "skills/literature-review/SKILL.md" "--format json" "literature docs use supported JSON flag"
Assert-Contains "skills/literature-review/SKILL.md" "--output refs\.bib" "literature docs use supported output flag"
Assert-Contains "skills/paper-orchestration/SKILL.md" "plan/task-packets" "orchestration requires persistent task packets"
Assert-Contains "skills/paper-orchestration/SKILL.md" "Validation commands" "task packet includes validation commands"

Assert-Contains ".claude-plugin/plugin.json" '"version":\s*"3\.1\.0"' "Claude plugin version matches current skill"
Assert-Contains ".cursor-plugin/plugin.json" '"version":\s*"3\.1\.0"' "Cursor plugin version matches current skill"
Assert-Contains "CHANGELOG.md" "\[3\.1\.0\]" "changelog contains current version"
Assert-Contains "README.md" "3\.1\.0" "Chinese README version current"
Assert-Contains "README_EN.md" "Version:\s*3\.1\.0" "English README version current"

if ($failures.Count -gt 0) {
    Write-Host "Skill integrity check failed:"
    foreach ($failure in $failures) {
        Write-Host " - $failure"
    }
    exit 1
}

Write-Host "Skill integrity check passed."
