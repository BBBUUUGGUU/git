from docx import Document
from pathlib import Path
p=Path(r'C:\Users\25038\Desktop\新建文件夹\空间双臂机器人在轨高精度插拔操作多任务迁移测试研究报告_补写版.docx')
d=Document(p)
for para in d.paragraphs:
    if para.text.startswith('跨场景差异化设置包括'):
        for r in para.runs:
            r.text=r.text.replace('，测试时应记录实际几何状态。','。')
    if para.text.startswith('结果应同时给出最终径向误差'):
        para.runs[0].text='测试结果应报告最终径向误差分布、深度达标比例及各阈值下成功率。现有成功条件未约束姿态角误差，不能据此认定六维位姿精度达标。拔出任务还需定义初始嵌入状态、退出动作和脱离判据，其性能不能由插入训练记录代替。'
        for r in para.runs[1:]:r.text=''
    if len(para.text)>80 and not para.style.name.startswith('toc'):
        para.paragraph_format.widow_control=True
d.save(p)
