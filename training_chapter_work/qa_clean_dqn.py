from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image, ImageChops
root=Path(r'C:\Users\25038\Desktop\git\training_chapter_work')
out=root/'clean_dqn_pages';out.mkdir(exist_ok=True)
pdf=pdfium.PdfDocument(root/'clean_dqn.pdf')
changed=[]
for i,page in enumerate(pdf):
    im=page.render(scale=1.4).to_pil().convert('RGB')
    im.save(out/f'page-{i+1}.png')
    prev=Image.open(root/'no_sac_pages'/f'page-{i+1}.png').convert('RGB')
    if im.size!=prev.size or ImageChops.difference(im,prev).getbbox():changed.append(i+1)
print('Pages changed from previously reviewed render:',changed)
