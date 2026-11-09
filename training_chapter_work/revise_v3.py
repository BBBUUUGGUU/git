from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import json, hashlib

w=Path(__file__).parent
folder=Path(r'C:\Users\25038\Desktop\新建文件夹')
source=folder/'空间双臂机器人在轨高精度插拔操作仿真训练研究报告_本科理论融合版.docx'
draft=w/'v3_revised_with_comments.docx'
out=folder/'空间双臂机器人在轨高精度插拔操作仿真训练研究报告_附件v3要求修订版.docx'
d=Document(source)

def find(prefix):
    for p in d.paragraphs:
        if p.text.strip().startswith(prefix): return p
    raise ValueError(prefix)
def remove(p): p._p.getparent().remove(p._p)
def el(tag, **attrs):
    x=OxmlElement(tag)
    for k,v in attrs.items():x.set(qn(k),str(v))
    return x
def mr(t):
    r=el('m:r');z=el('m:t');z.text=t;r.append(z);return r
def box(tag,*parts):
    x=el(tag)
    for part in parts:x.append(mr(part) if isinstance(part,str) else deepcopy(part))
    return x
def sub(a,b):return box('m:sSub',box('m:e',a),box('m:sub',b))
def sup(a,b):return box('m:sSup',box('m:e',a),box('m:sup',b))
def frac(a,b):return box('m:f',box('m:num',a),box('m:den',b))
def grp(*p):return box('m:box',box('m:e',*p))
def font(r,size=14):
    r.font.name='Times New Roman';r.font.size=Pt(size)
    r._r.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')

bodypr=deepcopy(find('空间双臂机器人插拔操作同时涉及')._p.pPr)
h3pr=deepcopy(find('DQN算法')._p.pPr)
h4pr=deepcopy(find('状态表示与离散动作')._p.pPr)

def before(anchor,text='',kind='body',parts=None):
    p=d.add_paragraph()
    p._p.insert(0,deepcopy({'body':bodypr,'h3':h3pr,'h4':h4pr}.get(kind,bodypr)))
    if kind in ('h3','h4'):
        p.add_run(text);p.paragraph_format.keep_with_next=True
    elif kind=='eq':
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        pf=p.paragraph_format;pf.first_line_indent=Pt(0);pf.space_before=Pt(5);pf.space_after=Pt(5)
        pf.line_spacing=Pt(22);pf.line_spacing_rule=WD_LINE_SPACING.AT_LEAST
        pr=p._p.get_or_add_pPr();pr.append(el('w:snapToGrid',**{'w:val':'0'}))
        ind=pr.get_or_add_ind()
        for a in ['firstLine','firstLineChars','left','leftChars','right','rightChars','hanging','hangingChars']:ind.set(qn('w:'+a),'0')
        op=el('m:oMathPara');op.append(box('m:oMath',*parts));p._p.append(op)
    else:font(p.add_run(text))
    p.paragraph_format.widow_control=True
    anchor._p.addprevious(p._p)
    return p
def eq(anchor,*parts):return before(anchor,kind='eq',parts=parts)
def replace_para(p,text):
    for r in list(p.runs):r._r.getparent().remove(r._r)
    font(p.add_run(text));return p

# Formal chapter opening: remove all editing-process language.
replace_para(find('空间双臂机器人插拔操作同时涉及'),
'空间双臂机器人高精度插拔操作同时涉及末端相对位姿调整、视觉与力觉信息感知、接触约束处理以及动作序列决策。直接采用深度强化学习生成底层控制量，需要在高维状态与动作空间中进行大量探索；仅依赖固定规则又难以适应初始偏差、配合尺寸、传感误差和控制参数的变化。针对上述问题，本章采用“启发式控制提供可执行基线、深度强化学习学习环境相关修正、底层控制器实现运动与柔顺响应”的研究思路，建立面向空间双臂机器人高精度插拔操作的高效学习方法。')
replace_para(find('本章的实现依据'),
'按照项目研究任务，本章的方法目标是形成支持视／力融合感知和高维连续动作输出的残差深度强化学习方案。首先介绍强化学习、DQN和SAC的基本原理；随后结合运动学、动力学与导纳型柔顺控制设计启发式策略；在此基础上构建启发式控制量与学习控制量融合的残差策略，并给出状态、动作、奖励、随机化和测试方法。当前软件已完成结构化状态输入、离散动作DQN及部分域随机化训练，可作为方法链路的阶段性验证；视觉编码、连续动作SAC和显式残差叠加仍属于后续实现内容。')
replace_para(find('本章理论部分结合'),
'本章理论组织遵循“决策理论—机器人模型—柔顺执行—残差学习—训练测试”的逻辑。强化学习部分说明策略优化依据；运动学与动力学部分建立动作执行的模型基础；导纳控制部分规定接触响应；残差强化学习部分明确启发式控制与学习修正的融合关系。通用理论采用统一符号表述，不将单臂模型参数或其他实验统计直接作为空间双臂系统的参数与结果。')

# Normalize source-oriented prose into formal report prose while retaining citations.
formal_replacements={
'为完整说明价值函数的递推过程':'为完整说明价值函数的递推过程',
'本科论文第二章从连杆坐标变换、雅可比矩阵和拉格朗日动力学建立控制模型。':'机械臂控制模型可由连杆坐标变换、雅可比矩阵和拉格朗日动力学建立。',
'正运动学建立关节变量q与末端位姿之间的映射。':'正运动学建立关节变量q与末端位姿之间的映射。',
'双臂装配关注的不仅是每个末端的绝对位姿':'双臂装配关注的不仅是每个末端的绝对位姿',
'动力学进一步描述实现上述运动所需的关节力矩。沿用本科论文的拉格朗日建模思路，':'动力学进一步描述实现上述运动所需的关节力矩。采用拉格朗日建模思路，',
'本科论文第三章把装配接触过程区分为':'机械臂装配接触过程可区分为',
'阻抗与导纳描述相同的力—运动动态关系':'阻抗与导纳描述相同的力—运动动态关系',
'本科论文4.4.1节采用':'插拔操作可采用',
}
for p in list(d.paragraphs):
    t=p.text
    for old,new in formal_replacements.items():
        if t.startswith(old):
            nt=new+t[len(old):]
            nt=nt.replace('[4，第2章] ','[4] ').replace('[4，3.2节] ','[4] ').replace('[4，4.2节]','[4]').replace('[4，4.3节]','[4]').replace('[4，原文3.4.4节]','[4]')
            replace_para(p,nt);break

# Add SAC as the continuous-action target algorithm before the heuristic-control section.
anchor=find('空间双臂机器人插拔任务的人为启发式控制策略设计')
before(anchor,'SAC连续动作深度强化学习算法',kind='h3')
before(anchor,'附件v3提出空间机械臂操作具有高维连续动作特征，并选用软演员—评论家算法（Soft Actor-Critic，SAC）学习操作策略。SAC是一种离策略演员—评论家算法：策略网络πφ(a|s)输出连续动作分布，两个动作价值网络Qθ1与Qθ2评价状态—动作对，目标网络提供相对平稳的自举目标。与只能从有限动作集合中选择动作的DQN相比，SAC能够直接表示末端位置、姿态、速度或关节控制量等有界连续动作。[5]')
before(anchor,'SAC采用最大熵强化学习目标，在最大化累计奖励的同时提高策略熵。策略熵反映动作分布的不确定性，温度系数α用于平衡任务奖励和随机探索，其目标可写为：')
eq(anchor,'J(π) = ',sub('E','π'),grp('[',sub('∑','t'),sup('γ','t'),grp('r(',sub('s','t'),',',sub('a','t'),') + αH(π(·|',sub('s','t'),'))'),']'))
before(anchor,'α较大时策略更加重视动作多样性，α较小时更接近只优化奖励的常规强化学习。α可以固定，也可以通过目标熵自动调整；目标熵、动作缩放和奖励量级共同影响训练，因此不能脱离动作维度直接照搬其他任务的α。')
before(anchor,'对于回放池中的转移(s，a，r，s′，d)，采用两个评论家网络抑制价值高估。令a′由当前策略在s′处采样，d表示真实终止标志，软Q目标为：')
eq(anchor,'y = r + γ(1−d)[',sub('min','j=1,2'),sub('Q','θ̄j'),'(s′,a′) − αlog',sub('π','φ'),'(a′|s′)]')
eq(anchor,sub('L','Q'),'(',sub('θ','j'),') = ',sub('E','D'),grp('[',sup(grp(sub('Q','θj'),'(s,a)−y'),'2'),']'))
before(anchor,'策略网络在提高评论家给出的动作价值的同时保留适当熵，其损失可写为下式；梯度通过重参数化动作a=fφ(ε；s)计算，其中ε为与策略参数无关的随机噪声：')
eq(anchor,sub('L','π'),'(φ) = ',sub('E','s∼D,ε'),grp('[αlog',sub('π','φ'),'(a|s) − ',sub('min','j=1,2'),sub('Q','θj'),'(s,a)]'))
eq(anchor,sub('θ̄','j'),' ← τ',sub('θ','j'),' + (1−τ)',sub('θ̄','j'))
before(anchor,'最后一式为目标评论家网络的软更新，τ通常取远小于1的正数。SAC仍使用经验回放，但策略、评论家和温度参数分别优化。训练时应分别记录评论家损失、策略损失、温度系数、策略熵和回合奖励，不能只凭奖励曲线判断所有网络均已稳定。')
before(anchor,'面向视／力融合的状态可写为s＝[φI(I)，w，Δx，q，q̇，z]：φI(I)为手眼图像的低维特征，w为六维力／力矩，Δx为轴孔相对位姿，q与q̇为关节状态，z为任务与域参数。图像编码器可使用卷积网络，但输入维数、归一化方式和训练数据必须随实现一并确定。若当前阶段未接入图像，则不能将22维结构化状态称为已经实现视／力融合。')
before(anchor,'连续动作建议在末端参考层定义为a＝[Δp，Δω]或相应速度指令，并按各方向独立限幅。平移量与转动量具有不同单位，需要分别归一化和缩放；动作经安全投影后再与启发式控制量融合。若改用关节速度或关节力矩，必须同步调整动作边界、底层接口和安全监督，不能只替换策略网络输出维度。')

# Rename the fusion section and add the target SAC residual scheme before training parameters.
replace_para(find('融合启发式控制策略的DQN算法'),'启发式控制策略与深度强化学习算法的融合方法')
anchor=find('训练参数')
before(anchor,'面向视／力融合连续动作的残差SAC方案',kind='h4')
before(anchor,'项目目标方案将启发式控制策略uH(s)作为基线，将SAC策略输出uRL(s)作为连续残差，并在同一末端参考层进行融合。为避免学习策略破坏基本操作逻辑，残差输出先按平移、转动方向分别缩放，再经过动作边界、安全约束和阶段门控：')
eq(anchor,sub('u','cmd'),' = ',sub('Π','safe'),grp('(',sub('u','H'),'(s) + β(s)⊙',sub('S','a'),sub('u','RL'),'(s)',')'))
before(anchor,'Sa为不同动作分量的尺度矩阵，β(s)为随操作阶段变化的残差权限，⊙表示逐元素乘法，Πsafe表示限位、限速、接触力约束和碰撞约束构成的安全投影。靠近阶段可由启发式策略主导；进入接触与精细调整阶段后逐步增加学习修正权限。该表达式属于目标实现，不代表仅用DQN选择一个位移动作就已完成显式残差SAC。')
before(anchor,'训练状态应同时保存名义轨迹、启发式输出、原始残差、缩放后残差、最终控制指令和安全投影触发原因，以便判断性能提升来自学习修正还是安全层截断。消融测试至少包含启发式基线、无启发式SAC、残差SAC三组，并在相同随机任务集和随机种子上比较成功率、完成时间、最终误差、峰值接触力和安全终止次数。')
before(anchor,'SAC训练参数包括策略／评论家学习率、折扣因子γ、回放池容量、批量大小、软更新系数τ、温度系数α或目标熵、每次环境交互后的梯度更新次数、随机探索步数、动作尺度与残差系数β。附件v3未给出这些参数的最终数值，当前DQN配置也不能直接替代SAC配置；因此应在SAC实现后按“固定场景调通—接触安全验证—单因素随机化—联合随机化”的顺序确定，并冻结版本与日志。')

# Formal implementation/result boundary and project metric.
for p in d.paragraphs:
    if p.text.startswith('本节采用读取时保存的日志快照'):
        replace_para(p,'本节分析当前DQN阶段性实现保存的日志快照，不重新运行训练。选取A组800回合自适应插入记录和B组192回合多参数随机化记录，分别检查奖励、成功标志、随机化参数与失败原因的一致性。该结果用于验证离散动作训练链路，不用于评价尚未实现的视／力融合连续动作残差SAC。')
    elif '“90%”仅作为用户提出的候选目标' in p.text:
        replace_para(p,'附件v3规定仿真场景任务成功率应大于90%。当前尚未完成冻结策略下的独立100组仿真测试，因此表中实测指标保持待测。只有当100组任务全部有效执行且成功数不少于91组时，观察成功率才满足“大于90%”的项目指标；有限样本结果仍不构成对任意场景成功概率的保证。若出现零成功，平均成功用时应记为不适用，不能填写为零秒。')

for t in d.tables:
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    if '候选成功率目标' in r.text:r.text=r.text.replace('候选成功率目标','项目成功率指标')
                    if '90%（尚未验证）' in r.text:r.text=r.text.replace('90%（尚未验证）','>90%（项目指标，尚未验证）')

# Remove editorial notes from the source list, keep proper academic citations, and add SAC primary source.
for p in list(d.paragraphs):
    if p.text.startswith('理论整合说明：'): remove(p)
ref_anchor=find('代码依据：')
before(ref_anchor,'[5] Haarnoja T, Zhou A, Abbeel P, Levine S. Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor[C]//Proceedings of the 35th International Conference on Machine Learning. PMLR, 2018, 80: 1861–1870. https://proceedings.mlr.press/v80/haarnoja18b.html')

d.save(draft)
manifest={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'draft':str(draft),'output':str(out),'paragraphs':len(Document(draft).paragraphs),'math':len(Document(draft).element.xpath('.//m:oMath'))}
(w/'v3_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False))
