"""Validate edited DOCX and render native Word export for page review."""
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from lxml import etree
from PIL import Image
import pypdfium2 as pdfium


WORK = Path(__file__).resolve().parent
manifest = json.loads((WORK / 'controller_terms_manifest.json').read_text(encoding='utf-8'))
source, output = Path(manifest['source']), Path(manifest['output'])
assert sha256(source.read_bytes()).hexdigest() == manifest['source_sha256']
before, after = Document(source), Document(output)
table_text = lambda doc: [[[c.text for c in row.cells] for row in table.rows] for table in doc.tables]
assert table_text(before) == table_text(after)
assert len(before.element.xpath('.//m:oMath')) == len(after.element.xpath('.//m:oMath')) == 29
for change in manifest['changes']:
    assert change['after'] in [p.text for p in after.paragraphs]
with ZipFile(source) as zs, ZipFile(output) as zo:
    media = lambda z: sorted(sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
    assert media(zs) == media(zo)
    text = '\n'.join(''.join(etree.fromstring(zo.read(n)).itertext()) for n in zo.namelist() if n.startswith('word/') and n.endswith('.xml'))
    for forbidden in ['残差', 'SAC', '视觉', '图像', '视／力', '视/力', 'u_H', 'u_R', 'β', '阻尼不足则导致响应迟缓']:
        assert forbidden not in text, forbidden

pages = WORK / 'controller_terms_pages'
pages.mkdir(exist_ok=True)
pdf = pdfium.PdfDocument(WORK / 'controller_terms.pdf')
identical, changed = [], []
for i in range(len(pdf)):
    page = pdf[i]
    bitmap = page.render(scale=1.4)
    image = bitmap.to_pil()
    image.save(pages / f'page-{i + 1}.png')
    old_page = WORK / 'hierarchical_dqn_pages' / f'page-{i + 1}.png'
    same = False
    if old_page.exists():
        with Image.open(old_page) as original_image:
            same = original_image.size == image.size and original_image.convert('RGB').tobytes() == image.convert('RGB').tobytes()
    (identical if same else changed).append(i + 1)
    image.close()
    bitmap.close()
    page.close()

report = {
    'pages': len(pdf), 'tables': len(after.tables), 'math': 29,
    'source_unchanged': True, 'tables_unchanged': True, 'figures_unchanged': True,
    'forbidden_terms': 0, 'pixel_identical_pages': identical, 'changed_pages': changed,
}
pdf.close()
(WORK / 'controller_terms_qa.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
