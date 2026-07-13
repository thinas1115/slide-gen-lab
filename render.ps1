# PPTXを1枚ずつPNGにエクスポートする (PowerPoint COM使用)
# -Width: 出力幅px(既定1600。AI目視のToken節約には800推奨)
# -Slides: 対象スライド番号のカンマ区切り(例 "3,11,14")。省略時は全枚
param(
    [Parameter(Mandatory = $true)][string]$PptxPath,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [int]$Width = 1600,
    [string]$Slides = ""
)
$ErrorActionPreference = "Stop"
$PptxPath = (Resolve-Path $PptxPath).Path
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Force $OutDir | Out-Null }
$OutDir = (Resolve-Path $OutDir).Path
$Height = [int]($Width * 9 / 16)
$targets = @()
if ($Slides -ne "") { $targets = $Slides -split "," | ForEach-Object { [int]$_ } }
if ($targets.Count -eq 0) {
    Get-ChildItem $OutDir -Filter "slide_*.png" | Remove-Item -Force
}

$pp = New-Object -ComObject PowerPoint.Application
try {
    # Open(FileName, ReadOnly, Untitled, WithWindow)
    $pres = $pp.Presentations.Open($PptxPath, [Microsoft.Office.Core.MsoTriState]::msoTrue,
        [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    $i = 0
    $n = 0
    foreach ($slide in $pres.Slides) {
        $i++
        if ($targets.Count -gt 0 -and $targets -notcontains $i) { continue }
        $out = Join-Path $OutDir ("slide_{0:d2}.png" -f $i)
        $slide.Export($out, "PNG", $Width, $Height)
        $n++
    }
    $pres.Close()
    Write-Output "exported $n slide(s) to $OutDir (${Width}x${Height})"
}
finally {
    $pp.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($pp) | Out-Null
}
