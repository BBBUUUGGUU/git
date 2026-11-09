import zipfile
from pathlib import Path

from docx import Document


path = Path(r"C:\Users\25038\Desktop\新建文件夹\空间双臂机器人在轨高精度插拔操作仿真训练研究报告_DQN分层控制修订版7_孔对象缩放方案调整.docx")
doc = Document(path)
all_text = "\n".join(p.text for p in doc.paragraphs)
print("paragraphs", len(doc.paragraphs), "tables", len(doc.tables))
print("old_note", all_text.count("500episodes”为计划回合数"))
print("old_hole_status", all_text.count("孔对象当前不缩放"))
print("new_hole_design", all_text.count("孔对象等比例缩放"))
print("tracked", len(doc._element.xpath(".//w:ins")), len(doc._element.xpath(".//w:del")))
print("pending_tasks", sum(row.cells[-1].text == "待测" for row in doc.tables[9].rows[1:]))
with zipfile.ZipFile(path) as archive:
    print("zip_test", archive.testzip())
