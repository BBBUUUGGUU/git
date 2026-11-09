param([string]$InputDoc,[string]$OutputPdf)
$ErrorActionPreference='Stop'
$app=New-Object -ComObject Word.Application
$app.Visible=$false
$app.DisplayAlerts=0
try {
    $doc=$app.Documents.Open($InputDoc)
    $doc.Repaginate()
    foreach($toc in $doc.TablesOfContents){$toc.Update()}
    $doc.Repaginate()
    foreach($toc in $doc.TablesOfContents){$toc.UpdatePageNumbers()}
    $doc.Save()
    $doc.ExportAsFixedFormat($OutputPdf,17)
    Write-Output ('PAGES='+$doc.ComputeStatistics(2))
    $doc.Close(0)
} finally {$app.Quit()}
