from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
p=Path(r'C:\Users\25038\Desktop\新建文件夹\空间双臂机器人在轨高精度插拔操作仿真训练研究报告_附件v3要求修订版.docx')
d=Document(p)
repls={
'附件v3提出空间机械臂操作具有高维连续动作特征':'按照项目研究目标，空间机械臂操作具有高维连续动作特征',
'本科论文所称“基于位置的阻抗控制”在本章统一称为“导纳型柔顺控制”。':'以力偏差为输入、以运动修正为输出的基于位置实现，在本章统一称为“导纳型柔顺控制”。',
'[4，原文3.4.4节]':'[4]',
'[4，4.3节]':'[4]',
'附件v3未给出这些参数的最终数值':'项目研究任务尚未规定这些参数的最终数值',
'附件v3规定仿真场景任务成功率应大于90%':'项目技术指标规定仿真场景任务成功率应大于90%',
'[4] 华灵蕙. 基于强化学习的机械臂高精度装配技术[D]. 哈尔滨工业大学本科毕业论文, 2025. 本章理论整合范围：第2章运动学与动力学、第3章接触与柔顺控制、第4章4.2—4.3节及4.4.1节分层控制框架。':'[4] 华灵蕙. 基于强化学习的机械臂高精度装配技术[D]. 哈尔滨工业大学, 2025.',
}
for para in d.paragraphs:
    t=para.text
    nt=t
    for a,b in repls.items():nt=nt.replace(a,b)
    if nt!=t:
        for r in list(para.runs):r._r.getparent().remove(r._r)
        r=para.add_run(nt);r.font.name='Times New Roman';r.font.size=Pt(14)
        r._r.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
for table in d.tables:
    for row in table.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                if '新增独立要求' in para.text:
                    para.text = para.text.replace('新增独立要求', '独立精度要求')
                if para.text.strip() == '90%（尚未验证）':
                    para.text = '＞90%（尚未验证）'
d.save(p)
