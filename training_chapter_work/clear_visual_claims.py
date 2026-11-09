from pathlib import Path
from docx import Document
from zipfile import ZipFile
from lxml import etree
root=Path(r'C:\Users\25038\Desktop\新建文件夹')
src=root/'空间双臂机器人在轨高精度插拔操作仿真训练研究报告_删除SAC版.docx'
out=root/'空间双臂机器人在轨高精度插拔操作仿真训练研究报告_DQN正文清理版.docx'
d=Document(src)
changes=0
for p in d.paragraphs:
    new=None
    if p.text.startswith('空间双臂机器人高精度插拔操作同时涉及'):
        new='空间双臂机器人高精度插拔操作需要协调末端相对位置调整、姿态保持与动作序列决策。若直接通过强化学习探索底层关节控制，学习过程需同时处理运动执行与任务决策，增加探索难度；仅依赖固定控制规则，则难以兼顾不同初始偏差、配合尺寸和控制参数下的操作需求。针对上述问题，本章采用上层学习决策与底层运动控制相结合的方法，由深度Q网络选择末端位移调整动作，结合人为启发式规则约束推进过程，并由底层控制器执行参考运动。'
    elif '图像输入可以使用卷积结构' in p.text:
        new='当状态变量连续或组合数量较大时，逐项存储Q表不再实用。深度Q网络以参数化函数Q(s,a；θ)近似动作价值，一次前向计算得到有限动作集合中各动作的价值估计。网络结构应与输入形式匹配：本项目采用结构化数值状态作为输入，通过全连接网络估计各离散动作的价值，并据此选择末端位移调整动作。[2]'
    if new:
        assert p.runs
        p.runs[0].text=new
        for r in p.runs[1:]:r.text=''
        changes+=1
assert changes==2
d.save(out)
with ZipFile(out) as z:
    text=''.join(''.join(etree.fromstring(z.read(n)).itertext()) for n in z.namelist() if n.startswith('word/') and n.endswith('.xml'))
    for term in ['SAC','视觉','图像','视／力','视/力','连续动作输出','视觉编码']:
        assert term not in text,term
assert [[c.text for row in t.rows for c in row.cells] for t in Document(src).tables]==[[c.text for row in t.rows for c in row.cells] for t in d.tables]
print('Changed 2 paragraphs; no SAC/vision claims; tables unchanged')
