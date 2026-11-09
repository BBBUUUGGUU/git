from pathlib import Path
import pypdfium2 as pdf
from PIL import Image,ImageChops
import sys,json
sys.stdout.reconfigure(encoding='utf-8')
w=Path(__file__).parent
out=w/'pages';out.mkdir(exist_ok=True)
d=pdf.PdfDocument(w/'qa.pdf')
texts=[]
for i,p in enumerate(d):
    im=p.render(scale=1.4).to_pil();im.save(out/f'page-{i+1}.png')
    text=p.get_textpage().get_text_range();texts.append(text)
    print(i+1,len(text),repr(text[:100]),repr(text[-100:]))
(w/'page_text.json').write_text(json.dumps(texts,ensure_ascii=False,indent=2),encoding='utf-8')
print('total',len(d))
