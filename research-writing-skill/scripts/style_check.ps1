param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $FilePath)) {
    Write-Host "File not found: $FilePath"
    exit 1
}

function Show-Matches {
    param(
        [string]$Title,
        [string]$Pattern
    )

    Write-Host ""
    Write-Host $Title

    $matches = Select-String -Path $FilePath -Pattern $Pattern
    if ($null -eq $matches) {
        Write-Host "OK"
    } else {
        foreach ($m in $matches) {
            Write-Host ("{0}:{1}" -f $m.LineNumber, $m.Line)
        }
    }
}

Write-Host ("Checking: {0}" -f $FilePath)

$bannedChineseTransitions = '\u9996\u5148|\u5176\u6b21|\u6700\u540e|\u6b64\u5916|\u53e6\u5916|\u63a5\u4e0b\u6765|\u503c\u5f97\u6ce8\u610f\u7684\u662f|\u9700\u8981\u6307\u51fa\u7684\u662f|\u91cd\u8981\u7684\u662f|\u5fc5\u987b\u5f3a\u8c03\u7684\u662f'
$subjectiveFirstPerson = '\u6211\u8ba4\u4e3a|\u6211\u89c9\u5f97|\u6211\u4e2a\u4eba(\u8ba4\u4e3a|\u770b\u6cd5)|\u6211\u7684\u7814\u7a76|in my opinion|i believe'
$processLeakage = '\u5b9e\u9a8c\u76ee\u7684|\u8868\u4f4d|\u56fe\u4f4d|\u56de\u586b\u6a21\u677f|\u8ba8\u8bba\u63d0\u793a|\u8bf4\u660e\uff1a\u672c\u7ae0\u8282\u4e3a\u7ed3\u679c\u5360\u4f4d\u7248\u672c|\u8bf7\u7528\u6237|\u7528\u6237\u66ff\u6362|\u5199\u4f5c\u8981\u6c42|\u4fee\u6539\u8981\u6c42'

Show-Matches "[1] Unnecessary bold markers (** or __):" '\*\*|__'
Show-Matches "[2] List lines (body prose should use lists cautiously):" '^\s*([-*+]\s+|[0-9]+\.\s+)'
Show-Matches "[3] Banned transition/emphasis phrases:" $bannedChineseTransitions
Show-Matches "[4] Banned English transition/emphasis phrases:" 'first and foremost|to begin with|moreover|furthermore|last but not least|it is worth noting that|importantly'
Show-Matches "[5] Subjective first-person phrases:" $subjectiveFirstPerson
Show-Matches "[5b] Process or user-instruction text leaked into body:" $processLeakage

Write-Host ""
Write-Host "[6] Consecutive non-empty lines (manual paragraph-spacing review):"

$lines = Get-Content -LiteralPath $FilePath -Encoding UTF8
for ($i = 1; $i -lt $lines.Count; $i++) {
    $prev = $lines[$i - 1]
    $curr = $lines[$i]

    $isCandidate = (
        $prev -notmatch '^\s*$' -and
        $curr -notmatch '^\s*$' -and
        $prev -notmatch '^\s*```' -and
        $curr -notmatch '^\s*```' -and
        $prev -notmatch '^\s*[#>\-]' -and
        $curr -notmatch '^\s*[#>\-]' -and
        $prev -notmatch '^\s*[0-9]+\.' -and
        $curr -notmatch '^\s*[0-9]+\.'
    )

    if ($isCandidate) {
        Write-Host ("{0}:{1}" -f $i, $prev)
        Write-Host ("{0}:{1}" -f ($i + 1), $curr)
        Write-Host "---"
    }
}

Write-Host ""
Write-Host "Done."
