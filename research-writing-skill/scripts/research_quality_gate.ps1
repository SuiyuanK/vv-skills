param(
    [string]$ProjectPath,
    [switch]$Submission,
    [switch]$SelfTest
)

$ErrorActionPreference = "Stop"
$failures = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

function Add-Failure {
    param([string]$Message)
    $failures.Add($Message) | Out-Null
}

function Add-Warning {
    param([string]$Message)
    $warnings.Add($Message) | Out-Null
}

function Get-TextIfExists {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    }
    return $null
}

function Count-Regex {
    param(
        [string]$Text,
        [string]$Pattern
    )
    if ([string]::IsNullOrWhiteSpace($Text)) {
        return 0
    }
    return ([regex]::Matches($Text, $Pattern)).Count
}

function Get-ChapterArchitectureSpecs {
    param([string]$Root)

    $architecturePath = Join-Path $Root "plan/chapter-architecture.md"
    $specs = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $architecturePath)) {
        return $specs
    }

    foreach ($line in Get-Content -LiteralPath $architecturePath -Encoding UTF8) {
        if ($line -match '^\s*-\s*(chapters/[^\s|]+\.md)(.*)$') {
            $rel = $matches[1]
            $rest = $matches[2]
            $minChars = 0
            if ($rest -match 'min_chars=(\d+)') {
                $minChars = [int]$matches[1]
            }
            $specs.Add([pscustomobject]@{
                Rel = $rel
                MinChars = $minChars
                AgentRequired = ($rest -match 'agent=required')
                PlaceholdersAllowed = ($rest -match 'placeholders=yes')
            }) | Out-Null
        }
    }

    return $specs
}

function Get-ProseParagraphCount {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return 0
    }

    $paragraphs = [regex]::Split($Text, "(\r?\n\s*){2,}") | Where-Object {
        $p = $_.Trim()
        $p.Length -gt 80 -and
        $p -notmatch '^\s*#' -and
        $p -notmatch '^\s*[-*+]\s+' -and
        $p -notmatch '^\s*\|' -and
        $p -notmatch '^```'
    }
    return @($paragraphs).Count
}

$introFiles = @(
    "chapters/01_Introduction.md",
    "chapters/01-introduction.md",
    "chapters/02_Introduction.md",
    "chapters/02-introduction.md"
)

$relatedFiles = @(
    "chapters/02-related-work.md",
    "chapters/03_Related_Work.md",
    "chapters/03-related-work.md"
)

$citationPattern = '\uFF08[^\uFF09]*(19|20)\d{2}[^\uFF09]*\uFF09|\([A-Z][^)]*(19|20)\d{2}[^)]*\)|\[[A-Za-z]+-?\d+\]'
$listPattern = '(?m)^\s*([-*+]\s+|\d+\.\s+)'
$processPattern = '\u8bf4\u660e\uff1a|\u5b9e\u9a8c\u76ee\u7684|\u8868\u4f4d|\u56fe\u4f4d|\u56de\u586b\u6a21\u677f|\u8ba8\u8bba\u63d0\u793a|\u8bf7\u7528\u6237|\u7528\u6237\u66ff\u6362|\u5199\u4f5c\u8981\u6c42|\u4fee\u6539\u8981\u6c42|this section is a template|discussion prompt|fill later'
$placeholderPattern = '\u5f85\u56de\u586b|\u5f85\u5b9e\u9a8c\u56de\u586b|\u5f85\u771f\u5b9e\u5b9e\u9a8c\u66ff\u6362|\u516c\u5f0f\u5360\u4f4d|\u7b97\u6cd5\u5360\u4f4d|TODO|TBD'
$resultOverclaimPattern = '\u5b9e\u9a8c\u7ed3\u679c\u8868\u660e|results show|verified'

if ($SelfTest) {
    $sample = [string]::Concat(
        [char]0x5b9e, [char]0x9a8c, [char]0x76ee, [char]0x7684,
        "`n",
        [char]0x56de, [char]0x586b, [char]0x6a21, [char]0x677f,
        "`n[",
        [char]0x5f85, [char]0x56de, [char]0x586b,
        "-F1]"
    )
    $processHits = Count-Regex $sample $processPattern
    $placeholderHits = Count-Regex $sample $placeholderPattern
    if ($processHits -ne 2) {
        Add-Failure "SelfTest expected 2 process hits, got $processHits."
    }
    if ($placeholderHits -ne 1) {
        Add-Failure "SelfTest expected 1 placeholder hit, got $placeholderHits."
    }
    if ($failures.Count -gt 0) {
        Write-Host "Research quality gate self-test failed:"
        foreach ($failure in $failures) {
            Write-Host " - $failure"
        }
        exit 1
    }
    Write-Host "Research quality gate self-test passed."
    exit 0
}

if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
    throw "ProjectPath is required unless -SelfTest is used."
}

$root = (Resolve-Path -LiteralPath $ProjectPath).Path

$chaptersPath = Join-Path $root "chapters"
if (-not (Test-Path -LiteralPath $chaptersPath)) {
    Add-Failure "Missing chapters directory: $chaptersPath"
}

$chapterSpecs = Get-ChapterArchitectureSpecs $root
if ($chapterSpecs.Count -gt 0) {
    if (-not (Test-Path -LiteralPath $chaptersPath)) {
        Add-Failure "Chapter architecture exists but chapters directory is missing."
    } else {
        $expected = @($chapterSpecs | ForEach-Object { $_.Rel })
        $actual = @(Get-ChildItem -LiteralPath $chaptersPath -Filter "*.md" | ForEach-Object { "chapters/$($_.Name)" })

        foreach ($rel in $expected) {
            if ($actual -notcontains $rel) {
                Add-Failure "Chapter architecture requires missing file: $rel"
            }
        }

        foreach ($rel in $actual) {
            if ($expected -notcontains $rel) {
                Add-Failure "Unexpected chapter file not listed in plan/chapter-architecture.md: $rel"
            }
        }

        $provenanceText = Get-TextIfExists (Join-Path $root "plan/chapter-agent-provenance.md")
        foreach ($spec in $chapterSpecs) {
            $filePath = Join-Path $root $spec.Rel
            if (-not (Test-Path -LiteralPath $filePath)) {
                continue
            }

            $text = Get-Content -LiteralPath $filePath -Raw -Encoding UTF8
            $charCount = ($text -replace '\s', '').Length
            if ($spec.MinChars -gt 0 -and $charCount -lt $spec.MinChars) {
                Add-Failure "$($spec.Rel) has $charCount non-whitespace characters; required min_chars=$($spec.MinChars)."
            }

            $provenancePattern = "(?m)^.*" + [regex]::Escape($spec.Rel) + ".*status=ACCEPTED.*$"
            if ($spec.AgentRequired -and ([string]::IsNullOrWhiteSpace($provenanceText) -or $provenanceText -notmatch $provenancePattern)) {
                Add-Failure "$($spec.Rel) requires an accepted chapter agent provenance entry."
            }

            $isReferenceLike = $spec.Rel -match 'References|Bibliography'
            $isAbstractLike = $spec.Rel -match 'Abstract'
            $listLines = Count-Regex $text $listPattern
            if (-not $isReferenceLike -and $listLines -gt 3) {
                Add-Failure "$($spec.Rel) has $listLines list-like line/s; full-paper chapters must be prose-led."
            }

            $paragraphCount = Get-ProseParagraphCount $text
            if (-not $isReferenceLike -and -not $isAbstractLike -and $paragraphCount -lt 6) {
                Add-Failure "$($spec.Rel) has only $paragraphCount substantial prose paragraph/s."
            }

            $placeholderHitsInFile = Count-Regex $text $placeholderPattern
            if (-not $spec.PlaceholdersAllowed -and $placeholderHitsInFile -gt 0) {
                Add-Failure "$($spec.Rel) contains unresolved placeholder/s but chapter architecture sets placeholders=no."
            }
        }
    }
}

$allChapterText = ""
$allProjectText = ""
$allNonChapterText = ""
if (Test-Path -LiteralPath $chaptersPath) {
    foreach ($file in Get-ChildItem -LiteralPath $chaptersPath -Filter "*.md") {
        $text = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
        $allChapterText += "`n" + $text
        $allProjectText += "`n" + $text

        $processHits = Count-Regex $text $processPattern
        if ($processHits -gt 0) {
            Add-Failure "$($file.Name) contains process/user-instruction language ($processHits hit/s)."
        }

        $listLines = Count-Regex $text $listPattern
        if ($listLines -gt 12) {
            Add-Warning "$($file.Name) has many list lines ($listLines); verify this is not report-style prose."
        }
    }
}

foreach ($dir in @("tables", "figures", "plan")) {
    $path = Join-Path $root $dir
    if (Test-Path -LiteralPath $path) {
        foreach ($file in Get-ChildItem -LiteralPath $path -Recurse -File -Include "*.md", "*.csv", "*.json") {
            $text = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
            $allProjectText += "`n" + $text
            $allNonChapterText += "`n" + $text
        }
    }
}

foreach ($rel in $introFiles) {
    $text = Get-TextIfExists (Join-Path $root $rel)
    if ($null -ne $text) {
        $count = Count-Regex $text $citationPattern
        if ($count -lt 5) {
            Add-Failure "$rel has only $count citation-like marker/s; Introduction requires literature-grounded claims."
        }
    }
}

foreach ($rel in $relatedFiles) {
    $text = Get-TextIfExists (Join-Path $root $rel)
    if ($null -ne $text) {
        $count = Count-Regex $text $citationPattern
        if ($count -lt 8) {
            Add-Failure "$rel has only $count citation-like marker/s; Related Work requires evidence synthesis."
        }
    }
}

$evidenceMapExists =
    (Test-Path -LiteralPath (Join-Path $root "refs/evidence-map.md")) -or
    (Test-Path -LiteralPath (Join-Path $root "plan/evidence-map.md"))
if (-not $evidenceMapExists) {
    Add-Failure "Missing evidence map: expected refs/evidence-map.md or plan/evidence-map.md."
}

$hasResults = $false
if (Test-Path -LiteralPath $chaptersPath) {
    $hasResults = $null -ne (Get-ChildItem -LiteralPath $chaptersPath -Filter "*.md" | Where-Object { $_.Name -match "Results|results|06_" })
}
if ($hasResults) {
    $requiredResultArtifacts = @(
        "plan/experiment-protocol.md",
        "plan/review/method-experiment-traceability.md",
        "tables/table-schema.md",
        "figures/data-manifest.md"
    )
    foreach ($artifact in $requiredResultArtifacts) {
        if (-not (Test-Path -LiteralPath (Join-Path $root $artifact))) {
            Add-Failure "Results section exists but $artifact is missing."
        }
    }

    $overclaimHits = Count-Regex $allChapterText $resultOverclaimPattern
    if ($overclaimHits -gt 0 -and (Count-Regex $allProjectText 'mock_|synthetic_|PLANNING DATA') -gt 0) {
        Add-Failure "Results text contains real-result language while mock/synthetic planning data is present."
    }
}

$mockFiles = Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^(mock_|synthetic_)' }
foreach ($mockFile in $mockFiles) {
    $mockText = Get-Content -LiteralPath $mockFile.FullName -Raw -Encoding UTF8
    if ($mockText -notmatch 'PLANNING DATA - replace before submission') {
        Add-Failure "Mock/synthetic file lacks required planning-data marker: $($mockFile.FullName)"
    }
}

$chapterPlaceholders = Count-Regex $allChapterText $placeholderPattern
$nonChapterPlaceholders = Count-Regex $allNonChapterText $placeholderPattern
$placeholders = $chapterPlaceholders + $nonChapterPlaceholders
if ($placeholders -gt 0) {
    if ($Submission) {
        Add-Failure "Submission mode forbids unresolved placeholders; found $placeholders."
    } else {
        if ($chapterPlaceholders -gt 0) {
            Add-Warning "Chapter drafts contain $chapterPlaceholders unresolved placeholder/s."
        }
        if ($nonChapterPlaceholders -gt 0) {
            Add-Warning "Planning artifacts contain $nonChapterPlaceholders placeholder/s."
        }
    }
}

if ($warnings.Count -gt 0) {
    Write-Host "Warnings:"
    foreach ($warning in $warnings) {
        Write-Host " - $warning"
    }
}

if ($failures.Count -gt 0) {
    Write-Host "Research quality gate failed:"
    foreach ($failure in $failures) {
        Write-Host " - $failure"
    }
    exit 1
}

Write-Host "Research quality gate passed."
