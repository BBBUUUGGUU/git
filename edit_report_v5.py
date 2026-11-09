from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


SOURCE = Path(r"C:\Users\25038\Desktop\新建文件夹\空间双臂机器人在轨高精度插拔操作仿真训练研究报告_DQN分层控制修订版5好的.docx")
OUTPUT = Path(r"C:\Users\25038\Desktop\新建文件夹\空间双臂机器人在轨高精度插拔操作仿真训练研究报告_DQN分层控制修订版6_训练规划与迁移验收补充.docx")


def find_paragraph(doc: Document, exact: str):
    matches = [p for p in doc.paragraphs if p.text == exact]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one paragraph for {exact!r}, found {len(matches)}")
    return matches[0]


def replace_paragraph_text(paragraph, text: str, bold: bool = False):
    p_pr = paragraph._p.pPr
    for child in list(paragraph._p):
        if child is not p_pr:
            paragraph._p.remove(child)
    run = paragraph.add_run(text)
    run.bold = bold
    return paragraph


def clone_paragraph_after(anchor, template, text: str):
    new_p = deepcopy(template._p)
    anchor._p.addnext(new_p)
    from docx.text.paragraph import Paragraph

    paragraph = Paragraph(new_p, anchor._parent)
    replace_paragraph_text(paragraph, text)
    return paragraph


def move_paragraph_after_element(paragraph, element):
    element.addnext(paragraph._p)
    return paragraph


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def keep_row_together(row):
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    tr_pr.append(cant_split)


def shade_cell(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=55, start=65, bottom=55, end=65):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def format_cell(cell, text: str, *, bold=False, size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = align
    paragraph.paragraph_format.first_line_indent = Pt(0)
    paragraph.paragraph_format.left_indent = Pt(0)
    paragraph.paragraph_format.right_indent = Pt(0)
    p_pr = paragraph._p.get_or_add_pPr()
    ind = p_pr.find(qn("w:ind"))
    if ind is None:
        ind = OxmlElement("w:ind")
        p_pr.append(ind)
    ind.set(qn("w:firstLine"), "0")
    ind.set(qn("w:left"), "0")
    ind.set(qn("w:right"), "0")
    for attr in ("firstLineChars", "leftChars", "rightChars"):
        key = qn(f"w:{attr}")
        if key in ind.attrib:
            del ind.attrib[key]
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(size)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_margins(cell)


def set_table_widths(table, widths):
    table.autofit = False
    for row in table.rows:
        for idx, width in enumerate(widths):
            row.cells[idx].width = width


def build_table(doc, rows, widths, *, shade_planning_column=None):
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_widths(table, widths)
    for r_idx, values in enumerate(rows):
        keep_row_together(table.rows[r_idx])
        for c_idx, value in enumerate(values):
            format_cell(
                table.rows[r_idx].cells[c_idx],
                value,
                bold=(r_idx == 0),
                size=8.0 if len(rows[0]) >= 6 else 8.5,
                align=WD_ALIGN_PARAGRAPH.LEFT if (r_idx > 0 and c_idx == 1) else WD_ALIGN_PARAGRAPH.CENTER,
            )
            if r_idx == 0:
                shade_cell(table.rows[r_idx].cells[c_idx], "D9E2F3")
            elif shade_planning_column is not None and c_idx == shade_planning_column:
                shade_cell(table.rows[r_idx].cells[c_idx], "FFF2CC")
    set_repeat_table_header(table.rows[0])
    return table


def format_body_paragraph(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for run in paragraph.runs:
        run.font.name = "Times New Roman"
        run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
        run.font.size = Pt(10.5)


def format_caption(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Pt(0)
    for run in paragraph.runs:
        run.font.name = "Times New Roman"
        run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
        run.font.size = Pt(10.5)


def remove_force_limit_clause(paragraph):
    remove = False
    for child in list(paragraph._p):
        texts = child.xpath(".//w:t/text()") if child.tag == qn("w:r") else []
        if any("、接触力超过" in text for text in texts):
            remove = True
        if remove:
            paragraph._p.remove(child)
    paragraph.add_run("。")


def copy_cell_layout_and_set_text(source_cell, target_cell, text: str):
    """Reuse a neighboring cell's exact Word layout so narrow numeric cells do not wrap."""
    target_tc = target_cell._tc
    source_tc = source_cell._tc
    target_tc.replace(target_tc.tcPr, deepcopy(source_tc.tcPr))
    for child in list(target_tc):
        if child.tag == qn("w:p"):
            target_tc.remove(child)
    new_p = deepcopy(source_tc.p_lst[0])
    text_nodes = new_p.xpath(".//w:t")
    if not text_nodes:
        raise RuntimeError("Source cell paragraph has no text node")
    text_nodes[0].text = text
    for extra in text_nodes[1:]:
        extra.text = ""
    target_tc.append(new_p)


doc = Document(SOURCE)

# Capture stable references before adding content.
p34 = find_paragraph(doc, "本章首先介绍强化学习与DQN的基本原理，随后建立空间双臂机器人的运动学与动力学模型，通过导纳控制，实现末端位姿变化向关节空间映射。在此基础上，实现启发式知识通过动作参数化、分段插入规则与奖励塑形嵌入DQN学习框架的具体方式，给出面向插入任务的状态表示、离散动作集合与奖励函数设计。最后，进行强化学习训练并评估泛化能力")
p35 = find_paragraph(doc, "本章从强化学习理论出发，依次建立机器人运动执行模型，再给出启发式知识与DQN决策的融合方法，最后通过训练日志与装配测试验证学习效果。具体内容如下：2.1节阐述DQN算法的基本原理；2.2节建立运动学、动力学与导纳控制模型，为底层执行提供依据；2.3节在此基础上给出动作映射、步长规则、奖励函数的设计，并完成参数配置、日志分析与测试方案")
p94 = find_paragraph(doc, "由图3-1可知，机械臂与目标物体接触时有如下三个阶段，其中位置变化如图3-1 (a)所示，力变化过程如图3-1 (b)所示：")
p102 = find_paragraph(doc, "图3-1  机械臂接触过程")
p158 = find_paragraph(doc, "回合成功终止条件：径向误差满足精度阈值且插入深度\xa0\xa0mm，奖励\xa0；回合终止失败条件：插入深度超过20 mm（−60）、径向误差超过60 mm（−40）、轴向后退超过50 mm（−40）、达到200步上限（）、接触力超过80 N（−100）")
p159 = find_paragraph(doc, "安全约束通过终止条件与负奖励实现。力超限阈值设为80 N，当接触力超过该阈值时回合立即终止并给予−100惩罚，优先级高于其他失败条件。关节限位、碰撞监测等安全条件同样在每步检测，触发即终止。")
p167 = find_paragraph(doc, "当前几何随机化包括轴径离散抽样和孔的等比例缩放两个独立部分。轴径从16～21 mm六个档位中等概率抽取，孔径随孔对象整体缩放系数变化。单边间隙由轴径与当前孔径共同决定，并非固定孔径下的单一变量。scale_peg_length为True时调用整体缩放，轴长随缩放系数改变。几何随机化的实际效果需通过场景中physical_peg_scaled等标志位确认对象缩放是否成功，并保存几何版本用于后续追溯。末端参考帧为object_tip和target_tip，基准位姿设为[0, 0, 0.5, 0, 0, 0, 1]。")
p174 = find_paragraph(doc, "表2-5  已保存训练日志统计（非独立测试）")
p177 = find_paragraph(doc, "图2-1  A组800回合自适应插入训练曲线")
p178 = find_paragraph(doc, "图2-1给出了A组逐回合累计奖励及50回合滑动均值，同时绘制相同窗口内的训练成功比例。累计奖励前50回合均值为−65.57，末50回合为135.88，说明该次训练在后期能够获得更多有利的阶段奖励；前100回合没有成功，末100回合成功42次，表明学习过程出现了任务完成能力，但距离稳定高成功率仍有明显差距。")
p181 = find_paragraph(doc, "图2-2  B组192回合多参数随机化训练曲线")
p183 = find_paragraph(doc, "两组日志并非只改变单一因素的严格消融实验，A组记录也未包含B组全部域参数字段。因此图2-1与图2-2应分别解读，不能仅以两条曲线的高低证明某种随机化配置或启发式规则更优。B组还应结合整体几何缩放、状态归一化范围、有效学习次数以及末端动作跟踪进行排查，相关因素目前属于待验证解释。")
p184 = find_paragraph(doc, "奖励曲线的纵轴为每回合各步奖励之和，既受动作质量影响，也受回合长度和奖励系数影响。图中的50回合均值从第50回合开始计算，不填造前49回合的窗口值；窗口成功比例只用于描述训练趋势。当前日志未保存可用于本报告的连续损失历史、完整接触峰值和可靠仿真操作时间，不补画这些指标，也不以决策步数直接替代实测完成时间。")
p186_template = find_paragraph(doc, "100组独立任务的随机初始化方案")
p190 = find_paragraph(doc, "表2-6  100组独立装配测试的四类初始化设计")
p193 = find_paragraph(doc, "表2-7  100组随机初始化任务（预生成方案，全部未执行）")
p195_template = find_paragraph(doc, "成功率与结果统计口径")
p199 = find_paragraph(doc, "项目技术指标规定仿真场景任务成功率应大于90%。当前尚未完成冻结策略下的独立100组仿真测试，因此表中实测指标保持待测。只有当100组任务全部有效执行且成功数不少于91组时，观察成功率才满足“大于90%”的项目指标；有限样本结果仍不构成对任意场景成功概率的保证。若出现零成功，平均成功用时应记为不适用，不能填写为零秒。")
p200 = find_paragraph(doc, "表2-8  独立100组装配测试结果登记表")
p202 = find_paragraph(doc, "独立测试应记录成功数量、有效任务总数、完成时间、最终误差和失败原因，并按配合尺寸与初始偏差进行分组统计。为评价启发式规则与奖励塑形的作用，可分别设置固定粗插入步长、去除部分塑形项等对照配置，在其余条件一致的情况下重新训练，并使用同一冻结任务集评价。现有A、B组训练统计不能替代这些对照实验；当前独立100组测试的结果仍保持待测。")
p207 = find_paragraph(doc, "代码依据：MulBotAsm/trainer/dqn_train3.py；envs/DSAE1.py；envs/DualSpaceArmController.py；algorithm/dqn_model.py。本章参数按2026年8月31日读取的版本核对；未修改项目代码或启动仿真。")
p208 = find_paragraph(doc, "A组日志：trainer/\ntraining_logs_10actions_adaptive_insert_30to5_200steps_800episodes；\nB组日志：trainer/\ntraining_logs_10actions_random_kpkdmd_peg16to21_hole22_200steps_500episodes。\n曲线与统计依据各目录的ep_rewards.npy、successList.npy、random_offsets.json、fail_reasons.json快照。")
p209 = find_paragraph(doc, "输入计划：表2-7的100组参数由NumPy default_rng(20260831)生成；结果栏全部待测，不能作为成功率、接触力或完成时间的实验凭证。")

table6 = doc.tables[6]
table7 = doc.tables[7]
table9 = doc.tables[9]

# Correct overstatements and code/document inconsistencies.
replace_paragraph_text(
    p34,
    "本章首先介绍强化学习与DQN的基本原理，随后建立空间双臂机器人的运动学与动力学模型，并以导纳型模型说明底层运动响应。在此基础上，说明启发式知识通过动作参数化、分段插入规则与奖励塑形嵌入DQN学习框架的具体方式，给出面向插入任务的状态表示、离散动作集合与奖励函数设计。最后，分析已保存的训练日志，并设计冻结策略下的泛化与迁移测试方案。",
)
replace_paragraph_text(
    p35,
    "本章从强化学习理论出发，依次建立机器人运动执行模型，再给出启发式知识与DQN决策的融合方法，最后通过训练日志分析现有学习表现，并给出独立装配与迁移测试方案。具体内容如下：2.1节阐述DQN算法的基本原理；2.2节建立运动学、动力学与导纳控制模型，为底层执行提供依据；2.3节在此基础上给出动作映射、步长规则和奖励函数设计，并完成参数配置、日志分析与测试方案设计。",
)
replace_paragraph_text(p94, "由图2-2可知，机械臂与目标物体接触时可分为三个阶段，其中位置变化如图2-2（a）所示，力变化过程如图2-2（b）所示：")
replace_paragraph_text(p102, "图2-2  机械臂接触过程")
remove_force_limit_clause(p158)
replace_paragraph_text(
    p159,
    "当前实现的失败终止分支包括插入过深、径向越界、轴向后退和达到步数上限。force_limit＝80仅为已保存的配置项，现有奖励与终止函数没有读取该值，既有日志中的失败原因也不能解释为已经完成限力验证。若后续装配或迁移测试将峰值接触力作为安全判据，应先实现连续测力记录、超限终止及异常追溯，并在测试前冻结阈值和代码版本；在此之前，80 N只能作为待实现的安全设计值。",
)
replace_paragraph_text(
    p167,
    "当前几何随机化由轴径离散抽样与轴对象整体缩放实现。轴径从16～21 mm六个档位中等概率抽取，孔径固定为22 mm；环境根据轴径与18 mm标称值的比例缩放轴对象，且scale_peg_length为True，因此轴长也随整体缩放改变。单边间隙按固定孔径与当前轴径计算。随机化的实际效果需通过场景中的physical_peg_scaled等标志位确认，孔对象当前不缩放，并应保存几何版本用于后续追溯。末端参考帧为object_tip和target_tip，基准位姿设为[0, 0, 0.5, 0, 0, 0, 1]。",
)

# Make figure numbering unique within Chapter 2.
replace_paragraph_text(p177, "图2-3  A组800回合自适应插入训练曲线")
replace_paragraph_text(
    p178,
    "图2-3给出了A组逐回合累计奖励及50回合滑动均值，同时绘制相同窗口内的训练成功比例。累计奖励前50回合均值为−65.57，末50回合为135.88，说明该次训练在后期能够获得更多有利的阶段奖励；前100回合没有成功，末100回合成功42次，表明学习过程出现了任务完成能力，但距离稳定高成功率仍有明显差距。",
)
replace_paragraph_text(p181, "图2-4  B组192回合多参数随机化训练曲线")
replace_paragraph_text(
    p183,
    "两组日志并非只改变单一因素的严格消融实验，A组记录也未包含B组全部域参数字段。因此图2-3与图2-4应分别解读，不能仅以两条曲线的高低证明某种随机化配置或启发式规则更优。B组还应结合轴对象整体缩放、状态归一化范围、有效学习次数以及末端动作跟踪进行排查，相关因素目前属于待验证解释。",
)

# Correct B group snapshot length and document why the folder name is misleading.
copy_cell_layout_and_set_text(table6.rows[1].cells[1], table6.rows[2].cells[1], "192")
note_b = doc.add_paragraph()
note_b.style = p184.style
replace_paragraph_text(note_b, "注：B组日志目录名称中的“500episodes”为计划回合数，本次快照实际包含192条回合记录，表2-5按日志数组的实际长度统计。")
note_b.paragraph_format.first_line_indent = Pt(0)
note_b.paragraph_format.space_before = Pt(0)
note_b.paragraph_format.space_after = Pt(3)
for run in note_b.runs:
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(9)
table6._tbl.addnext(note_b._p)

# Add a staged training plan. These are explicit planning gates, not fabricated results.
training_heading = clone_paragraph_after(p184, p186_template, "后续训练阶段与通过门槛")
training_intro = clone_paragraph_after(
    training_heading,
    p184,
    "为便于后续训练和实测数据补充，后续工作采用“分阶段训练—冻结验证—满足门槛后扩展随机化范围”的推进方式。表2-6中的回合预算和成功率均为训练规划值，不是当前已经获得的实验结果。训练成功率用于判断学习趋势，冻结策略验证结果用于决定是否进入下一阶段，二者不得混用。各阶段验证应采用独立于训练数据的固定种子；最终迁移测试任务不得参与模型选择或参数调整。",
)
format_body_paragraph(training_intro)
training_caption = clone_paragraph_after(training_intro, p190, "表2-6  后续训练阶段与通过门槛（规划值，待实测替换）")
format_caption(training_caption)
training_rows = [
    ["阶段", "训练条件", "建议新增回合", "近100回合训练门槛", "独立冻结验证门槛", "数据性质"],
    ["基础稳定", "固定几何尺寸与控制器增益；初始偏差10～15 mm", "500", "连续2个窗口≥60%", "≥55%", "规划值"],
    ["偏差扩展", "偏差范围依次扩展至10～20 mm和10～25 mm", "800", "连续2个窗口≥75%", "≥70%", "规划值"],
    ["单因素随机化", "几何尺寸与柔顺控制器增益分别随机化", "各800", "连续2个窗口≥80%", "各配置≥75%", "规划值"],
    ["联合随机化", "启用表2-4所列全部随机化范围", "1500", "连续2个窗口≥88%", "≥85%", "规划值"],
    ["迁移适配", "在目标域验证集上适配；最终测试集不参与调参", "500～1000", "连续2个窗口≥93%", "预验证≥90%", "规划值"],
]
training_table = build_table(
    doc,
    training_rows,
    [Inches(0.65), Inches(1.75), Inches(0.70), Inches(1.15), Inches(1.15), Inches(0.65)],
    shade_planning_column=5,
)
training_caption._p.addnext(training_table._tbl)
training_note = doc.add_paragraph()
training_note.style = p184.style
replace_paragraph_text(
    training_note,
    "不同难度阶段不设置统一的绝对累计奖励阈值，因为回合长度、随机化范围和奖励项会改变奖励尺度。每一阶段仅在相同配置下比较100回合滑动平均奖励，并同时检查成功率和失败原因。当成功率满足表中门槛、连续窗口奖励无持续下降且超时比例明显降低时，方可进入下一阶段；未达到门槛时应如实延长训练或检查状态归一化、动作执行和奖励设计，不得以规划值替代实测结果。",
)
format_body_paragraph(training_note)
training_table._tbl.addnext(training_note._p)

# Renumber subsequent tables after inserting Table 2-6.
replace_paragraph_text(p190, "表2-7  100组独立装配测试的四类初始化设计")
replace_paragraph_text(p193, "表2-8  100组随机初始化任务（预生成方案，全部未执行）")
replace_paragraph_text(p200, "表2-9  独立100组装配与迁移测试结果登记表")
format_caption(p190)
format_caption(p193)
format_caption(p200)

# Clarify that precision requirements are planned evaluation inputs, not existing training inputs.
format_cell(table7.rows[4].cells[2], "拟新增评估输入；现有训练入口未实现独立τ_req", size=8.5)

# Formal target values and still-empty measured values are placed in separate columns.
table9.add_column(Inches(0.85))
result_rows = [
    ["统计项目", "计算口径", "规划/验收值（非实测）", "实测值"],
    ["计划任务数量", "固定随机种子预生成", "100组", "已生成输入"],
    ["有效执行数量", "完成初始化并获得有效终止记录", "100组", "待测"],
    ["成功数量", "同时满足径向、深度及已实现安全条件", "验收≥91组；内部目标≥95组", "待测"],
    ["失败数量", "有效执行但未满足成功条件", "验收≤9组；内部目标≤5组", "待测"],
    ["总体成功率", "成功数/有效组数×100%", "验收＞90%；内部目标≥95%", "待测"],
    ["平均/中位成功用时", "仅对成功任务使用仿真时间戳", "未规定，不预填", "待测"],
    ["最终径向误差", "逐组核对对应τ_eff，并报告分布", "每个成功任务均≤τ_eff", "待测"],
    ["接触峰值力/力矩", "仅在连续记录与限力终止均启用后统计", "当前不预填数值", "待测"],
    ["失败原因分布", "超时、越界、过深等类别之和应等于失败数", "总数≤9", "待测"],
    ["异常运行数量", "通信或模型异常保留编号并单列", "正式验收目标为0", "待测"],
]
for r_idx, values in enumerate(result_rows):
    for c_idx, value in enumerate(values):
        format_cell(
            table9.rows[r_idx].cells[c_idx],
            value,
            bold=(r_idx == 0),
            size=8.2,
            align=WD_ALIGN_PARAGRAPH.LEFT if (r_idx > 0 and c_idx == 1) else WD_ALIGN_PARAGRAPH.CENTER,
        )
        if r_idx == 0:
            shade_cell(table9.rows[r_idx].cells[c_idx], "D9E2F3")
        elif c_idx == 2:
            shade_cell(table9.rows[r_idx].cells[c_idx], "FFF2CC")
    keep_row_together(table9.rows[r_idx])
set_repeat_table_header(table9.rows[0])
set_table_widths(table9, [Inches(1.05), Inches(2.05), Inches(1.75), Inches(0.85)])
table9.alignment = WD_TABLE_ALIGNMENT.CENTER

replace_paragraph_text(
    p199,
    "项目技术指标规定最终迁移后的仿真场景任务成功率应大于90%。本报告将正式验收设置为100组一次性冻结策略测试：全部任务有效执行时，成功不少于91组方满足指标；为预留随机波动和边界工况余量，训练计划采用95组成功（95%）作为内部目标。91组和95组分别是验收门槛与规划目标，不是当前实测结果。有限样本结果仍不构成对任意场景成功概率的保证；若出现零成功，平均成功用时应记为不适用，不能填写为零秒。",
)

# Add the real transfer-fine-tuning snapshot and the final frozen-test requirement.
migration_heading = clone_paragraph_after(p202, p195_template, "迁移微调记录与最终验收要求")
migration_intro = clone_paragraph_after(
    migration_heading,
    p202,
    "本报告所称迁移，是指将源域训练得到的网络权重部署到具有明确参数差异的目标仿真场景。若部署后继续更新网络参数，应称为迁移微调；只有在网络参数冻结后，使用未参与训练和调参的任务集进行测试，所得结果才可作为独立迁移性能。源域与目标域的几何尺寸、初始偏差、柔顺控制器增益和判据版本均应保存。",
)
format_body_paragraph(migration_intro)
migration_actual = clone_paragraph_after(
    migration_intro,
    p202,
    "项目目录中已有一组迁移初始化后的继续训练记录：训练脚本加载A组800回合模型权重，并在多参数随机化环境中继续更新网络100回合。该记录属于迁移微调日志，不是冻结策略的独立迁移测试。",
)
format_body_paragraph(migration_actual)
migration_caption = clone_paragraph_after(migration_actual, p174, "表2-10  迁移初始化后继续训练日志统计（实测训练数据，非独立测试）")
format_caption(migration_caption)
migration_rows = [
    ["源模型", "微调回合", "成功数", "训练成功比例", "均值奖励", "失败构成"],
    ["A组800回合权重", "100", "0", "0%", "−145.32", "越界66；超时34"],
]
migration_table = build_table(
    doc,
    migration_rows,
    [Inches(1.25), Inches(0.75), Inches(0.65), Inches(1.00), Inches(0.85), Inches(1.45)],
)
migration_caption._p.addnext(migration_table._tbl)
migration_analysis = doc.add_paragraph()
migration_analysis.style = p202.style
replace_paragraph_text(
    migration_analysis,
    "该100回合记录的平均奖励为−145.32，成功数为0，失败由越界66次和超时34次构成。前20回合与末20回合平均奖励分别为−174.94和−74.22，说明阶段奖励有所改善，但完整任务仍未成功，不能据此声称迁移已达到90%以上。最终迁移验收沿用表2-9口径：完成必要适配后冻结模型，在100组未参与调参的目标域任务上一次性测试，观察成功率应大于90%（至少91组成功），内部计划目标为95组成功；正式日志生成前，实测结果继续保持“待测”。",
)
format_body_paragraph(migration_analysis)
migration_table._tbl.addnext(migration_analysis._p)

# Update source notes and table references.
replace_paragraph_text(
    p207,
    "代码依据：MulBotAsm/trainer/dqn_train3.py、dqn_train3_transfer.py；envs/DSAE1.py；envs/DualSpaceArmController.py；algorithm/dqn_model.py。本章参数与日志按2026年9月2日读取的版本核对；未修改项目代码或启动新的仿真。",
)
replace_paragraph_text(
    p208,
    "A组日志：trainer/training_logs_10actions_adaptive_insert_30to5_200steps_800episodes；B组日志：trainer/training_logs_10actions_random_kpkdmd_peg16to21_hole22_200steps_500episodes；C组迁移微调日志：trainer/training_logs_10actions_transfer_from_adaptive_30to5_peg16to21_hole22_200steps_100episodes。统计依据各目录的ep_rewards.npy、successList.npy、random_offsets.json和fail_reasons.json快照；C组还依据dqn_train3_transfer.py确认训练期间持续更新网络。",
)
replace_paragraph_text(
    p209,
    "输入计划：表2-8的100组参数由NumPy default_rng(20260831)生成；逐任务结果栏全部待测，不能作为成功率、接触力或完成时间的实验凭证。表2-6和表2-9中的数值为训练规划或验收门槛，亦不作为已取得结果。",
)

# Apply consistent body/caption formatting to changed paragraphs.
for paragraph in [p34, p35, p94, p159, p167, p178, p183, p199, p207, p208, p209]:
    format_body_paragraph(paragraph)
for paragraph in [p102, p174, p177, p181]:
    format_caption(paragraph)

# Ask Word to refresh fields on open; native Word will also update the TOC in a second pass.
settings = doc.settings._element
update_fields = settings.find(qn("w:updateFields"))
if update_fields is None:
    update_fields = OxmlElement("w:updateFields")
    settings.append(update_fields)
update_fields.set(qn("w:val"), "true")

doc.save(OUTPUT)
print(OUTPUT)
