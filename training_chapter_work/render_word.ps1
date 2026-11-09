$ErrorActionPreference='Stop'
$wa=New-Object -ComObject Word.Application
$wa.Visible=$false
$wa.DisplayAlerts=0
try {
    $wd=$wa.Documents.Open('C:\Users\25038\Desktop\新建文件夹\空间双臂机器人在轨高精度插拔操作仿真训练研究报告_第二章详细补充版.docx')
    $wd.Repaginate()
    foreach($toc in $wd.TablesOfContents){$toc.UpperHeadingLevel=1;$toc.LowerHeadingLevel=3;$toc.Update()}
    $wd.Repaginate()
    foreach($toc in $wd.TablesOfContents){$toc.UpdatePageNumbers()}
    $wd.Save()
    $wd.ExportAsFixedFormat('C:\Users\25038\Desktop\git\training_chapter_work\qa.pdf',17)
    Write-Output ('PAGES='+$wd.ComputeStatistics(2))
    $wd.Close(0)
} finally {$wa.Quit()}
