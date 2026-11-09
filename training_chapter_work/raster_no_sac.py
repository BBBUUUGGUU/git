from pathlib import Path
import pypdfium2 as pdfium
root=Path(r'C:\Users\25038\Desktop\git\training_chapter_work')
out=root/'no_sac_pages'
out.mkdir(exist_ok=True)
pdf=pdfium.PdfDocument(root/'no_sac.pdf')
for i,page in enumerate(pdf):
    page.render(scale=1.4).to_pil().save(out/f'page-{i+1}.png')
print(len(pdf))
