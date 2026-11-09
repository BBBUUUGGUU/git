from pathlib import Path
from docx import Document
from zipfile import ZipFile

root=Path(r'C:\Users\25038\Desktop\新建文件夹')
src=root/'空间双臂机器人在轨高精度插拔操作仿真训练研究报告_附件v3要求修订版.docx'
out=root/'空间双臂机器人在轨高精度插拔操作仿真训练研究报告_删除SAC版.docx'
d=Document(src)
paras=list(d.paragraphs)
remove=set(range(72,86)) | set(range(149,155)) | {206}
assert paras[72].text=='SAC连续动作深度强化学习算法'
assert paras[149].text=='面向视／力融合连续动作的残差SAC方案'
def replace(p,text):
    runs=p.runs
    if runs:
        runs[0].text=text
        for r in runs[1:]: r.text=''
    else: p.add_run(text)
replace(paras[35], '本章围绕基于DQN的空间双臂机器人插拔操作学习方法展开。首先介绍强化学习与DQN的基本原理；随后结合运动学、动力学与导纳型柔顺控制设计启发式策略；在此基础上讨论启发式控制与DQN决策的融合方法，并给出状态、动作、奖励、随机化和测试方法。当前软件采用结构化状态输入与离散动作DQN，已开展部分域随机化训练；显式残差叠加作为方法设计单独讨论，不将其表述为现有程序已经完成的功能。')
replace(paras[171], '本节分析当前DQN实现保存的日志快照。选取A组800回合自适应插入记录和B组192回合多参数随机化记录，分别检查奖励、成功标志、随机化参数与失败原因的一致性。训练结果用于分析现有离散动作策略的学习表现。')
for i,p in enumerate(paras):
    if i in remove or (p.style.name.lower().startswith('toc') and 'SAC' in p.text):
        p._p.getparent().remove(p._p)
d.save(out)
with ZipFile(out) as z:
    for name in z.namelist():
        if name.startswith('word/') and name.endswith('.xml'):
            text=z.read(name).decode('utf-8')
            assert 'SAC' not in text and 'Haarnoja' not in text and 'Soft Actor' not in text, name
print(out)
