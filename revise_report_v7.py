from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


SOURCE = Path(r"C:\Users\25038\Desktop\新建文件夹\空间双臂机器人在轨高精度插拔操作仿真训练研究报告_DQN分层控制修订版6_训练规划与迁移验收补充.docx")
OUTPUT = Path(r"C:\Users\25038\Desktop\新建文件夹\空间双臂机器人在轨高精度插拔操作仿真训练研究报告_DQN分层控制修订版7_孔对象缩放方案调整.docx")


OLD_GEOMETRY = (
    "当前几何随机化由轴径离散抽样与轴对象整体缩放实现。轴径从16～21 mm六个档位中等概率抽取，"
    "孔径固定为22 mm；环境根据轴径与18 mm标称值的比例缩放轴对象，且scale_peg_length为True，"
    "因此轴长也随整体缩放改变。单边间隙按固定孔径与当前轴径计算。随机化的实际效果需通过场景中"
    "的physical_peg_scaled等标志位确认，孔对象当前不缩放，并应保存几何版本用于后续追溯。末端参考"
    "帧为object_tip和target_tip，基准位姿设为[0, 0, 0.5, 0, 0, 0, 1]。"
)

NEW_GEOMETRY = (
    "几何随机化包括轴径离散抽样和孔对象等比例缩放两个相互独立的部分。轴径从16～21 mm六个档位中"
    "等概率抽取；孔径以22 mm为标称尺寸，并随孔对象整体缩放系数变化。单边间隙由当前轴径与当前孔径"
    "共同决定，而不是固定孔径下的单一变量。scale_peg_length为True时轴对象沿三个方向整体缩放，轴长"
    "随缩放系数改变。几何随机化的实际效果应通过场景中的physical_peg_scaled和physical_hole_scaled"
    "等标志位确认，并保存轴、孔实际尺寸和几何版本，用于后续训练与测试追溯。末端参考帧为object_tip"
    "和target_tip，基准位姿设为[0, 0, 0.5, 0, 0, 0, 1]。"
)

REMOVE_NOTE = (
    "注：B组日志目录名称中的“500episodes”为计划回合数，本次快照实际包含192条回合记录，"
    "表2-5按日志数组的实际长度统计。"
)


def replace_text_keep_paragraph_format(paragraph, text: str):
    p_pr = paragraph._p.pPr
    for child in list(paragraph._p):
        if child is not p_pr:
            paragraph._p.remove(child)
    paragraph.add_run(text)


doc = Document(SOURCE)

geometry_matches = [p for p in doc.paragraphs if p.text == OLD_GEOMETRY]
if len(geometry_matches) != 1:
    raise RuntimeError(f"Expected one geometry paragraph, found {len(geometry_matches)}")
replace_text_keep_paragraph_format(geometry_matches[0], NEW_GEOMETRY)

note_matches = [p for p in doc.paragraphs if p.text == REMOVE_NOTE]
if len(note_matches) != 1:
    raise RuntimeError(f"Expected one B-group note, found {len(note_matches)}")
note_element = note_matches[0]._p
note_element.getparent().remove(note_element)

settings = doc.settings._element
update_fields = settings.find(qn("w:updateFields"))
if update_fields is None:
    update_fields = OxmlElement("w:updateFields")
    settings.append(update_fields)
update_fields.set(qn("w:val"), "true")

doc.save(OUTPUT)
print(OUTPUT)
