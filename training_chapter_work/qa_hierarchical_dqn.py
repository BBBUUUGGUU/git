from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
import json
import pypdfium2 as pdfium
from docx import Document
from lxml import etree

w=Path(__file__).parent
m=json.loads((w/'hierarchical_dqn_manifest.json').read_text(encoding='utf-8'))
src=Path(m['source']);out=Path(m['output'])
assert sha256(src.read_bytes()).hexdigest()==m['source_sha256']
a,b=Document(src),Document(out)
assert [[c.text for row in t.rows for c in row.cells] for t in a.tables]==[[c.text for row in t.rows for c in row.cells] for t in b.tables]
with ZipFile(out) as z:
    txt='\n'.join(''.join(etree.fromstring(z.read(n)).itertext()) for n in z.namelist() if n.startswith('word/') and n.endswith('.xml'))
    for term in ['残差','SAC','视觉','图像','视／力','视/力','u_H','u_R','β','Residual Reinforcement','Johannink','[4]']:
        assert term not in txt,term
    assert 'comments.xml' not in ' '.join(z.namelist())
with ZipFile(src) as zs,ZipFile(out) as zo:
    media_before=sorted(sha256(zs.read(n)).hexdigest() for n in zs.namelist() if n.startswith('word/media/'))
    media_after=sorted(sha256(zo.read(n)).hexdigest() for n in zo.namelist() if n.startswith('word/media/'))
    assert media_before==media_after
pages=w/'hierarchical_dqn_pages';pages.mkdir(exist_ok=True)
pdf=pdfium.PdfDocument(w/'hierarchical_dqn.pdf')
for i,page in enumerate(pdf):
    page.render(scale=1.4).to_pil().save(pages/f'page-{i+1}.png')
print(json.dumps({'pages':len(pdf),'math':len(b.element.xpath('.//m:oMath')),'tables':len(b.tables),'media_unchanged':True,'source_unchanged':True,'forbidden_terms':0},ensure_ascii=False))
