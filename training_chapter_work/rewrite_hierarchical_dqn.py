"""Replace unimplemented residual-RL storyline with the verified DQN chain."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile
from hashlib import sha256
import json
import re
from lxml import etree
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

root=Path(r'C:\Users\25038\Desktop\新建文件夹')
work=Path(__file__).parent
source=root/'空间双臂机器人在轨高精度插拔操作仿真训练研究报告_DQN正文清理版.docx'
output=root/'空间双臂机器人在轨高精度插拔操作仿真训练研究报告_DQN分层控制重写版.docx'
source_hash=sha256(source.read_bytes()).hexdigest()
d=Document(source)
original_paras=list(d.paragraphs)
original_tables=[[c.text for row in t.rows for c in row.cells] for t in d.tables]

def find(prefix):
    matches=[p for p in d.paragraphs if p.text.startswith(prefix) and not p.style.name.lower().startswith('toc')]
    assert len(matches)==1,(prefix,len(matches))
    return matches[0]

def replace(p,text):
    assert not p._p.xpath('.//m:oMath'),p.text
    if p.runs:
        p.runs[0].text=text
        for r in p.runs[1:]:r.text=''
    else:p.add_run(text)
    return p

def remove(p):p._p.getparent().remove(p._p)
def setp(prefix,text):return replace(find(prefix),text)

bodypr=deepcopy(find('空间双臂机器人高精度插拔操作需要协调')._p.pPr)

def el(tag,**attrs):
    item=OxmlElement(tag)
    for key,val in attrs.items():item.set(qn(key),str(val))
    return item

def mr(text):
    r=el('m:r');t=el('m:t');t.text=text;r.append(t);return r

def box(tag,*parts):
    item=el(tag)
    for part in parts:item.append(mr(part) if isinstance(part,str) else deepcopy(part))
    return item

def sub(a,b):return box('m:sSub',box('m:e',a),box('m:sub',b))
def sup(a,b):return box('m:sSup',box('m:e',a),box('m:sup',b))
def ss(a,b,c):return box('m:sSubSup',box('m:e',a),box('m:sub',b),box('m:sup',c))

def before(anchor,text=None,parts=None):
    p=d.add_paragraph()
    p._p.insert(0,deepcopy(bodypr))
    if parts is not None:
        previous=anchor._p.getprevious()
        if previous is not None and previous.tag==qn('w:p'):
            Paragraph(previous,anchor._parent).paragraph_format.keep_with_next=True
        pf=p.paragraph_format
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        pf.first_line_indent=Pt(0);pf.space_before=Pt(5);pf.space_after=Pt(5)
        pf.line_spacing=Pt(22);pf.line_spacing_rule=WD_LINE_SPACING.AT_LEAST
        pr=p._p.get_or_add_pPr();pr.append(el('w:snapToGrid',**{'w:val':'0'}))
        ind=pr.get_or_add_ind()
        for name in ['firstLine','firstLineChars','left','leftChars','right','rightChars','hanging','hangingChars']:
            ind.set(qn('w:'+name),'0')
        mathp=el('m:oMathPara');mathp.append(box('m:oMath',*parts));p._p.append(mathp)
    else:
        r=p.add_run(text);r.font.name='Times New Roman';r.font.size=Pt(14)
        r._r.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
    p.paragraph_format.widow_control=True
    anchor._p.addprevious(p._p)
    return p

# Opening: describe actual decision/execution layers, not an unrealized algorithm.
setp('本章围绕基于DQN的',
     '本章首先介绍强化学习与DQN的基本原理，随后结合机器人运动学、动力学及导纳型控制理论，阐述底层运动执行与人为启发式规则的设计依据。在此基础上，建立面向插入任务的结构化状态表示、离散动作集合与奖励函数，说明DQN决策、动作映射和底层控制的衔接关系，并分析域随机化训练日志、设计独立装配测试。当前验证对象为插入过程，拔出动作及其性能需通过专门的任务设计与实验另行评估。')
setp('本章理论组织遵循',
     '启发式知识主要通过动作参数化、粗插入步长规则和奖励塑形参与学习过程。动作参数化给出末端调整方向与步长集合；粗插入规则根据轴向距离和径向误差调节推进量；奖励塑形对对准、接近与完成任务进行评价。DQN学习这些动作的执行顺序，底层控制器负责跟踪给定参考运动，两者构成决策与执行分离的控制架构。')

# Section 2.2: remove the invented independent heuristic action baseline.
setp('人为先验控制器承担',
     '人为启发式知识在本系统中体现为末端动作集合、分段粗插入步长、近孔对准条件与姿态保持规则。底层控制器依据参考位姿和当前运动状态生成关节控制量，DQN则在给定动作集合中学习调整方向与推进时机。本节先给出运动执行所需的模型与参数解释，再说明已有启发式规则的作用范围。')
setp('先验控制器的运动学与动力学基础','底层控制的运动学与动力学基础')
setp('代码中Kp、Kd和Md分别对应',
     '底层控制器以Kp、Kd和Md分别表示刚度、阻尼和虚拟质量参数，用于根据参考运动与当前状态的偏差计算运动响应。当前训练调用将外力输入forceI置为零，测得的末端力／力矩进入上层状态，但未在该调用链中形成测力驱动的导纳修正。因此，下文利用导纳型模型解释参数对跟踪动态的影响，现有训练数据不作为完整力反馈柔顺控制性能的验证。')
setp('在完整导纳实现中',
     '上述动力学关系用于解释底层执行模块，不决定上层动作选择。对于同一末端参考位置，不同刚度、阻尼与虚拟质量参数会形成不同的跟踪响应；DQN通过环境返回的下一状态和奖励评价动作效果。这种任务决策与运动执行的分工，使动作序列学习与底层参数设置能够分别研究。')
setp('先验动作生成与分阶段控制','对准约束与分阶段插入规则')
setp('人为先验动作可围绕',
     '插入操作的工程经验是先减小径向偏差，再逐步接近配合入口。本系统将这一经验落实为粗插入动作的步长调节规则，并通过奖励函数鼓励对准后的轴向推进。设轴孔径向误差为ρ、轴向剩余距离为dₓ：当目标距离较大时，粗插入动作采用较长步长；接近入口时逐步减小步长，并检查径向误差是否满足近孔推进条件。')
assert original_paras[104]._p.xpath('.//m:oMath')
remove(original_paras[104])
setp('其中sat表示幅值限制',
     '径向调整采用正、负两个方向的离散位移动作，具体方向由DQN选择。启发式规则并不独立生成整段对准与插入轨迹，而是在网络选定粗插入动作后确定本步推进量。因此，规则约束的是动作执行参数，DQN仍需通过交互学习合适的对准方向与推进时机。')

# Section 2.3: rewrite the method itself, including its actual mathematical interface.
setp('融合启发式控制策略与深度强化学习算法的残差深度强化学习算法',
     '启发式引导的DQN决策与底层运动控制方法')
setp('残差强化学习的核心是',
     '本节采用上层DQN决策、下层运动控制的分层架构。网络根据当前状态评价离散动作，环境依据动作字典与分段插入规则生成末端参考位移，底层控制器执行参考运动并返回新的观测。启发式规则作用于动作定义和执行步长，奖励塑形作用于动作价值学习；各模块共同构成面向插入任务的闭环交互过程。')
setp('启发式控制策略与深度强化学习算法的融合方法','离散动作决策与运动执行机制')
setp('现有10种动作包括',
     '现有10种动作包括1种精细插入、4种精细径向调整、4种粗略径向调整和1种自适应粗插入。神经网络选择的动作索引为0～9，训练入口加1后传入环境。环境中的action＝0分支不属于当前网络的10个输出；动作10在近孔条件未满足时也可能映射为零位移，但这是步长规则的结果，并非独立的网络停止动作。')
setp('插拔操作可采用',
     '上层与下层承担不同计算任务：DQN输出10个动作价值估计，动作选择模块据此产生一个离散索引；底层控制器接收由该索引生成的参考位置和姿态，并计算关节控制量。[4] 因此，网络不是直接回归关节力矩，也不是直接输出一个连续目标位置。本文所称分层是决策与执行的架构分工，不额外引入子目标策略或多层价值函数。')
setp('两种“补偿”也应明确区分',
     '动作集合与步长规则把工程知识写入可执行接口，奖励函数则评价动作对插入任务的贡献。前者影响当前动作如何执行，后者通过回报与价值更新影响后续动作选择。底层跟踪性能决定参考动作能否有效落实，因此分析学习结果时，还需同时关注动作选择、参考位移与实际位移之间的关系。')
setp('显式残差融合设计与现有实现边界','启发式动作映射与参考指令生成')
anchor=find('奖励函数与训练流程')
for i in range(123,127):remove(original_paras[i])
before(anchor,'令kₜ∈{0，…，9}为DQN选择的网络动作索引，环境动作编号为aₜ＝kₜ＋1。训练时按探索机制选择kₜ，独立评估时冻结参数并采用预定的动作选择规则。记G(aₜ，ρₜ，dₓ,ₜ)为动作字典及粗插入规则共同确定的局部位移增量。G的输出单位为长度，其符号与动作坐标系一致；动作10的步长随ρₜ和dₓ,ₜ变化，其他动作采用表2-1中的固定步长。')
before(anchor,'当前动作坐标系为左臂末端坐标系。局部位移通过本次决策时刻的末端旋转矩阵转换到世界坐标系；式中旋转矩阵的上标W表示世界坐标系，下标T表示左臂末端动作坐标系：')
before(anchor,parts=[ss('Δp','t','W'),' = ',ss('R','T,t','W'),' G(',sub('a','t'),', ',sub('ρ','t'),', ',sub('d','x,t'),')'])
before(anchor,'左臂参考位置由本次决策开始时计算得到的末端位置与所选动作增量相加得到；参考姿态取该时刻的末端姿态，并在本次动作的底层执行期间保持。相应关系为：')
before(anchor,parts=[sub('p','L,ref,t'),' = ',sub('p','L,t'),' + ',ss('Δp','t','W'),',    ',sub('R','L,ref,t'),' = ',sub('R','L,t')])
before(anchor,'这里的Δpₜ是本步任务动作的完整位移指令；当前左臂末端位置由关节状态经正运动学计算并结合基座位姿得到。参考点并非在上一次参考点上无限累计；下一次决策重新依据当前状态生成目标。受跟踪误差、接触和动力学响应影响，实际末端位移也不必严格等于指令位移，应通过执行前后的位置记录核对。')
before(anchor,'每次上层决策后，环境保持本次参考目标并执行50个底层控制循环，再获取下一状态与奖励。左臂执行模型控制器给出的运动跟踪指令；右臂最终关节力矩被替换为保持复位构型的PD项。按控制器内部的关节符号约定，可写为：')
before(anchor,parts=[sub('τ','R'),' = 1500(',sub('q','R,reset'),' − ',sub('q','R'),') − 100',sub('q̇','R')])
before(anchor,'上述右臂力矩在发送前还需按仿真接口进行关节符号转换。右臂控制目标是维持复位构型，而不是由DQN独立选择动作；姿态保持和构型保持也不意味着接触时不存在偏移。当前底层调用主要体现带刚度、阻尼与虚拟质量参数的运动跟踪，测得力／力矩作为上层状态信息使用。')
before(anchor,'由此，一次交互可概括为“读取状态—选择离散动作—应用步长规则—生成参考位姿—执行底层控制—计算奖励与终止条件”。这一接口把任务决策与关节运动计算分开，使网络在有限动作集合中学习插入顺序，同时保留对动作映射和控制参数的明确解释。')

# Keep actual reward statistics, but state the role of shaping precisely.
reward_anchor=find('当前训练流程按回合重置')
before(reward_anchor,'上述奖励属于面向插入任务的奖励塑形：径向误差下降项鼓励对准，分段轴向奖励鼓励在对准后接近目标，步数惩罚促使策略减少无效动作。奖励塑形不直接生成控制指令，也不构成安全约束。其权重改变会影响动作之间的价值排序，需通过相同任务分布下的独立训练与测试分析效果，不能仅依据奖励数值变大认定装配性能提高。')
setp('两组日志并非只改变单一因素',
     '两组日志并非只改变单一因素的严格消融实验，A组记录也未包含B组全部域参数字段。因此图2-1与图2-2应分别解读，不能仅以两条曲线的高低证明某种随机化配置或启发式规则更优。B组还应结合整体几何缩放、状态归一化范围、有效学习次数以及末端动作跟踪进行排查，相关因素目前属于待验证解释。')
setp('正式结论应由测试完成后的实际记录生成',
     '独立测试应记录成功数量、有效任务总数、完成时间、最终误差和失败原因，并按配合尺寸与初始偏差进行分组统计。为评价启发式规则与奖励塑形的作用，可分别设置固定粗插入步长、去除部分塑形项等对照配置，在其余条件一致的情况下重新训练，并使用同一冻结任务集评价。现有A、B组训练统计不能替代这些对照实验；当前独立100组测试的结果仍保持待测。')

# Remove residual-only literature and renumber the thesis source consistently.
remove(find('[3] Johannink'))
for p in d.paragraphs:
    # Same-length replacement preserves run formatting and fields.
    nodes=p._p.xpath('.//w:t')
    old=''.join(n.text or '' for n in nodes)
    new=old.replace('[4]','[3]')
    if new!=old:
        pos=0
        for n in nodes:
            length=len(n.text or '')
            n.text=new[pos:pos+length];pos+=length

# A freshly updated TOC will replace these cached entries in Word.
for p in list(d.paragraphs):
    if p.style.name.lower().startswith('toc') and '残差' in p.text:
        remove(p)

# Local formatting repair of pre-existing appendix/table inconsistencies.
ref_template=find('[2] Mnih')
ref_thesis=find('[3] 华灵蕙')
if ref_thesis._p.pPr is not None:ref_thesis._p.remove(ref_thesis._p.pPr)
ref_thesis._p.insert(0,deepcopy(ref_template._p.pPr))
for run in ref_thesis.runs:
    run.font.name='Times New Roman';run.font.size=Pt(10.5)
    run._r.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
source_par=find('A组日志：')
source_text=source_par.text.replace('A组日志：trainer/','A组日志：trainer/\n').replace('；B组日志：trainer/','；\nB组日志：trainer/\n').replace('。曲线与统计依据','。\n曲线与统计依据')
replace(source_par,source_text)
source_par.alignment=WD_ALIGN_PARAGRAPH.LEFT
for run in source_par.runs:run.font.size=Pt(10.5)
for table in d.tables:
    for row in table.rows:
        for cell in row.cells:
            if cell.text in ['独立精度要求；τ_eff=min(τ_req,0.75c)','＞90%（尚未验证）']:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.name='Times New Roman';run.font.size=Pt(10.5)
                        run._r.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
            elif cell.text=='include_domain_params_in_state':
                for para in cell.paragraphs:
                    for run in para.runs:run.font.size=Pt(9)

d.save(output)
assert sha256(source.read_bytes()).hexdigest()==source_hash
assert original_tables==[[c.text for row in t.rows for c in row.cells] for t in Document(output).tables]
with ZipFile(output) as z:
    content='\n'.join(''.join(etree.fromstring(z.read(n)).itertext()) for n in z.namelist() if n.startswith('word/') and n.endswith('.xml'))
    for term in ['残差','SAC','视觉','图像','视／力','视/力','u_H','u_R','β','Residual Reinforcement','Johannink','[4]']:
        assert term not in content,term

manifest={'source':str(source),'source_sha256':source_hash,'output':str(output),'tables_unchanged':True,'paragraphs':len(Document(output).paragraphs),'equations':len(Document(output).element.xpath('.//m:oMath'))}
(work/'hierarchical_dqn_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False))
