"""Make three local terminology edits; preserve source, tables and equations."""
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

from docx import Document


WORK = Path(__file__).resolve().parent
SOURCE = Path('C:/Users/25038/Desktop/新建文件夹/空间双臂机器人在轨高精度插拔操作仿真训练研究报告_DQN分层控制重写版.docx')
OUTPUT = SOURCE.with_name('空间双臂机器人在轨高精度插拔操作仿真训练研究报告_DQN分层控制修订版.docx')


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    source_hash = sha256(SOURCE.read_bytes()).hexdigest()
    doc = Document(SOURCE)
    changes = []

    def replace_once(index, old, new):
        paragraph = doc.paragraphs[index]
        before = paragraph.text
        assert before.count(old) == 1, (index, old)
        for run in paragraph.runs:
            if old in run.text:
                run.text = run.text.replace(old, new, 1)
                break
        else:
            raise AssertionError(f'Replacement crosses runs: {index}')
        assert paragraph.text == before.replace(old, new, 1)
        changes.append({'paragraph_index': index, 'before': before, 'after': paragraph.text})

    replace_once(
        33,
        '仅依赖固定控制规则，则难以兼顾不同初始偏差、配合尺寸和控制参数下的操作需求。',
        '仅依赖固定控制规则，则难以兼顾初始偏差、轴孔配合间隙以及底层控制器刚度、阻尼与虚拟质量参数变化下的操作需求。',
    )
    replace_once(
        141,
        '本节以当前训练入口的实参为准，不将被注释的旧参数或环境构造函数的默认值混入同一配置。',
        '本节以当前训练入口的实参为准，不将被注释的旧参数或环境构造函数的默认值混入同一配置。控制器参数在每回合复位时按设定范围随机抽样；DQN学习率与折扣因子采用表2-2中的固定值，不参与上述随机化。',
    )
    replace_once(
        150,
        '上述域随机化还可从导纳参数的角度解释。',
        '上述控制器参数随机化可从导纳型模型的角度解释。',
    )

    doc.save(OUTPUT)
    original = Document(SOURCE)
    result = Document(OUTPUT)
    table_text = lambda d: [[[c.text for c in row.cells] for row in t.rows] for t in d.tables]
    assert table_text(original) == table_text(result)
    assert len(original.element.xpath('.//m:oMath')) == len(result.element.xpath('.//m:oMath'))
    modified_indices = {item['paragraph_index'] for item in changes}
    assert len(original.paragraphs) == len(result.paragraphs)
    for i, (before, after) in enumerate(zip(original.paragraphs, result.paragraphs)):
        if i not in modified_indices:
            assert before._p.xml == after._p.xml, i
    with ZipFile(SOURCE) as before, ZipFile(OUTPUT) as after:
        media = lambda z: sorted(sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/'))
        assert media(before) == media(after)
    assert sha256(SOURCE.read_bytes()).hexdigest() == source_hash
    manifest = {
        'source': str(SOURCE), 'output': str(OUTPUT), 'source_sha256': source_hash,
        'changes': changes, 'tables_unchanged': True, 'math_unchanged': True,
        'figures_unchanged': True, 'source_unchanged': True,
    }
    (WORK / 'controller_terms_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
