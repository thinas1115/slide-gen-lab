# PPTXを1枚ずつPNGにエクスポートする (PowerPoint COM使用)
param(
    [Parameter(Mandatory = $true)][string]$PptxPath,
    [Parameter(Mandatory = $true)][string]$OutDir
)
$ErrorActionPreference = "Stop"
$PptxPath = (Resolve-Path $PptxPath).Path
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Force $OutDir | Out-Null }
$OutDir = (Resolve-Path $OutDir).Path
Get-ChildItem $OutDir -Filter "slide_*.png" | Remove-Item -Force

$pp = New-Object -ComObject PowerPoint.Application
try {
    # Open(FileName, ReadOnly, Untitled, WithWindow)
    $pres = $pp.Presentations.Open($PptxPath, [Microsoft.Office.Core.MsoTriState]::msoTrue,
        [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    $i = 0
    foreach ($slide in $pres.Slides) {
        $i++
        $out = Join-Path $OutDir ("slide_{0:d2}.png" -f $i)
        $slide.Export($out, "PNG", 1600, 900)
    }
    $pres.Close()
    Write-Output "exported $i slides to $OutDir"
}
finally {
    $pp.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($pp) | Out-Null
}
