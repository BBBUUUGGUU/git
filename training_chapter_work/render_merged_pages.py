from pathlib import Path
import pypdfium2 as pdf
import json
w=Path(__file__).parent
o=w/'merged_pages';o.mkdir(exist_ok=True)
d=pdf.PdfDocument(w/'merged_qa.pdf')
texts=[]
for i,p in enumerate(d):
    p.render(scale=1.4).to_pil().save(o/f'page-{i+1}.png')
    texts.append(p.get_textpage().get_text_range())
(w/'merged_page_text.json').write_text(json.dumps(texts,ensure_ascii=False,indent=2),encoding='utf-8')
print(len(d))
