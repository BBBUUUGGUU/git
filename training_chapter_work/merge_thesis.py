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
source=folder/'空间双臂机器人在轨高精度插拔操作仿真训练研究报告_第二章详细补充版.docx'
out=folder/'空间双臂机器人在轨高精度插拔操作仿真训练研究报告_本科理论融合版.docx'
d=Document(source)
original=list(d.paragraphs)
bodypr=deepcopy(original[36]._p.pPr)
h3pr=deepcopy(original[57]._p.pPr)
added=[]

def el(tag, **attrs):
    x=OxmlElement(tag)
    for k,v in attrs.items(): x.set(qn(k),str(v))
    return x
def run(t):
    r=el('m:r'); z=el('m:t');z.text=t;r.append(z);return r
def box(tag,*parts):
    x=el(tag)
    for p in parts: x.append(run(p) if isinstance(p,str) else deepcopy(p))
    return x
def grp(*p):return box('m:box',box('m:e',*p))
def sub(a,b):return box('m:sSub',box('m:e',a),box('m:sub',b))
def sup(a,b):return box('m:sSup',box('m:e',a),box('m:sup',b))
def frac(a,b):return box('m:f',box('m:num',a),box('m:den',b))
def dot(a,double=False):
    x=el('m:acc'); pr=el('m:accPr');pr.append(el('m:chr',**{'m:val':'̈' if double else '̇'}));x.append(pr);x.append(box('m:e',a));return x
def sqrt(a):
    x=el('m:rad');pr=el('m:radPr');pr.append(el('m:degHide',**{'m:val':'1'}));x.append(pr);x.append(el('m:deg'));x.append(box('m:e',a));return x
def font(r,size=14):
    r.font.name='Times New Roman';r.font.size=Pt(size)
    r._r.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
def insert(anchor,text='',kind='body',parts=None):
    p=d.add_paragraph();p._p.insert(0,deepcopy(h3pr if kind=='h3' else bodypr))
    if kind=='h3':
        p.add_run(text);p.paragraph_format.keep_with_next=True
    elif kind=='eq':
        pf=p.paragraph_format;pf.first_line_indent=Pt(0);pf.space_before=Pt(5);pf.space_after=Pt(5)
        pf.line_spacing=Pt(22);pf.line_spacing_rule=WD_LINE_SPACING.AT_LEAST
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        pr=p._p.get_or_add_pPr();pr.append(el('w:snapToGrid',**{'w:val':'0'}))
        ind=pr.get_or_add_ind()
        for a in ['firstLine','firstLineChars','left','leftChars','right','rightChars','hanging','hangingChars']:ind.set(qn('w:'+a),'0')
        mp=el('m:oMathPara');mp.append(box('m:oMath',*parts));p._p.append(mp)
    else:
        font(p.add_run(text),11 if kind=='small' else 14)
        if kind=='small':
            p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=Pt(18)
    p.paragraph_format.widow_control=True
    anchor._p.addprevious(p._p);added.append(text)
    return p
def note(p,text):d.add_comment(p.runs[:1],text,author='理论整合说明',initials='整合')
def b(i,text):return insert(original[i],text)
def eq(i,*parts):return insert(original[i],kind='eq',parts=parts)

# Chapter lead: identify source and retain project evidence boundaries.
p=b(34,'本章理论部分结合本科毕业论文《基于强化学习的机械臂高精度装配技术》[4]进行扩充：将其第四章的强化学习推导纳入2.1节，将第二章的运动学与动力学、第三章的接触与柔顺控制理论纳入2.2节，并在2.3节说明从“学习决策＋底层控制”到显式残差融合的关系。通用理论经统一符号后使用，UR10的具体结构参数、控制器整定值和实验统计不直接移作空间双臂系统的参数与结果。')
note(p,'新增来源为用户提供的本科论文第二至四章。保留报告原有章节主线与训练数据，仅整合相关理论；本科论文实测结果不并入本项目统计。')

# Bellman expectation derivation, before the already-present optimal Q equation.
p=b(42,'为完整说明价值函数的递推过程，先考虑离散状态和动作下的固定策略评价。令π(a|s)为状态s下选择动作a的概率，P(s′|s,a)为状态转移概率，R(s,a,s′)为该转移的期望即时奖励。由Gₜ＝rₜ₊₁＋γGₜ₊₁，并对动作选择和下一状态分别取条件期望，可得到贝尔曼期望方程。[4，4.2节]')
note(p,'整合本科论文4.2节、原文第36—38页。原文“将上式相减”改为对一步奖励与折扣后续价值求和；补足策略和转移概率的角色。')
vp=sup('V','π'); qp=sup('Q','π')
eq(42,vp,'(s) = ',sub('∑','a'),' π(a|s)',sub('∑','s′'),' P(s′|s,a)[R(s,a,s′)+γ',vp,'(s′)]')
eq(42,qp,'(s,a) = ',sub('∑','s′'),' P(s′|s,a)[R(s,a,s′)+γ',vp,'(s′)]')
eq(42,vp,'(s) = ',sub('∑','a'),' π(a|s)',qp,'(s,a)')
b(42,'第一式回答“给定策略有多好”，第二式回答“先执行某个动作，再遵循该策略有多好”；第三式把动作价值按策略概率加权还原为状态价值。连续状态下应将对状态的求和替换为相应积分。奖励可能同时依赖下一状态，上述写法不要求将奖励简化成仅由当前状态决定的常数。')
b(42,'进一步将固定策略下的评价转为最优决策，在有限动作集合中选择使长期收益最大的动作。最优状态价值等于各动作最优价值的最大值，因此将下一状态的策略平均替换为最大化操作，即得到下述最优动作价值关系。该转换说明了为什么Q-learning与DQN的目标包含下一状态动作价值的最大值，而不是只比较当前一步奖励。')

# General TD before Q-learning discussion.
p=b(43,'当转移模型未知时，无法直接枚举上述期望，但可以使用交互样本估计更新目标。以固定策略的状态价值评价为例，TD(0)采用一步奖励和下一状态的当前估计构造目标：')
eq(43,sub('δ','t'),' = ',sub('r','t+1'),' + γV(',sub('s','t+1'),') − V(',sub('s','t'),')')
eq(43,'V(',sub('s','t'),') ← V(',sub('s','t'),') + α',sub('δ','t'))
b(43,'这里的TD误差统一定义为“目标减当前估计”。TD利用尚未完全准确的价值估计更新另一估计，称为自举；与等待整回合结束再使用完整回报的蒙特卡洛方法相比，它可以在每一步交互后更新。状态价值评价本身并不直接给出动作选择，Q-learning进一步学习动作价值，并用贪心目标进行策略改进。')

# DQN mechanism extension after standard target/loss.
p=b(53,'从表格更新到神经网络更新，改变的是价值函数的表示方式。网络共享参数θ，使不同状态的经验通过参数更新相互影响；相近状态是否得到合理泛化，仍取决于输入表征与训练样本，而不是使用神经网络后自动成立。在固定批次目标值的前提下，网络通过损失梯度更新参数：')
eq(53,'θ ← θ − η',sub('∇','θ'),'L(θ)')
b(53,'η是优化器学习率，与折扣因子γ的作用不同。Adam依据梯度的一阶与二阶矩估计调整各参数的更新尺度，并不自动调整γ，也不负责决定探索概率。学习率决定“每次改多少”，γ决定“未来收益看多远”，探索概率决定“采样时多大程度尝试非贪心动作”，三者必须分别配置。')
p=b(53,'经验回放与目标网络解决的问题也不同：经验回放对已采集转移随机抽样，降低小批量样本的时序相关性并复用数据；目标网络在若干次更新期间保持参数不变，减缓自举目标的快速漂移。两者有助于改善训练，但不构成非线性DQN必然收敛的证明。[4，4.3节]')
note(p,'依据本科论文4.3节、第39—40页重新组织。原文将“目标值在一段时间内保持稳定”接在经验回放之后，本次明确归于目标网络。修正原文4.4.3中容易混淆Adam、γ与探索概率的表述。')

# Add model foundations as a new same-level section before original admittance theory.
insert(original[57],'先验控制器的运动学与动力学基础',kind='h3')
p=b(57,'本科论文第二章从连杆坐标变换、雅可比矩阵和拉格朗日动力学建立控制模型。[4，第2章] 这些内容在本报告中用于解释末端动作如何转化为可执行运动。这里保留一般串联机械臂的建模方法，不照搬UR10的六关节D-H参数表；当前双臂模型的连杆、关节轴、质量和惯量应由对应URDF及场景配置确定。')
note(p,'新增2.2.1，将原导纳型柔顺控制理论顺延为2.2.2。论文使用UR10，报告当前左臂状态含7个关节，不将“6自由度冗余机械臂”说法带入本报告。')
b(57,'正运动学建立关节变量q与末端位姿之间的映射。采用改进D-H约定时，相邻坐标变换依次为绕前一连杆x轴旋转、沿该轴平移、绕当前z轴旋转和沿该轴平移。以R与T分别表示旋转和平移算子，四个参数为连杆扭角α、连杆长度a、关节角θ与关节偏距d：')
eq(57,sub('A','i'),' = ',sub('R','x'),'(',sub('α','i−1'),')',sub('T','x'),'(',sub('a','i−1'),')',sub('R','z'),'(',sub('θ','i'),')',sub('T','z'),'(',sub('d','i'),')')
eq(57,sub('T','0e'),'(q) = ',sub('A','1'),sub('A','2'),'⋯',sub('A','n'),sub('T','tool'))
b(57,'其中T₀ₑ表示末端坐标系在基坐标系下的位姿，Ttool为末端工具安装变换，n为该运动链的关节数。各变换均为4×4齐次矩阵，由3×3旋转矩阵R、三维位置p和末行[0，0，0，1]组成。改进D-H与标准D-H的坐标系约定不同，不能把某一约定的参数表与另一约定的乘法顺序混合使用。')
p=b(57,'双臂装配关注的不仅是每个末端的绝对位姿，还包括轴端相对于孔端的位姿。若T_WL和T_WR分别表示左、右末端在同一世界坐标系W下的位姿，则右末端坐标系下的左末端位姿为T_RL＝(T_WR)⁻¹T_WL。由此可统一定义相对位置和轴线夹角，并区分世界坐标系与工具坐标系中的动作方向。该相对变换是对本科单臂模型的双臂扩展说明，实际轴、孔参考帧需与object_tip和target_tip一致。')
note(p,'本科论文以单臂UR10为对象；此处相对位姿关系为面向双臂报告补充的通用运动学解释，不声称论文已完成空间双臂建模。')
b(57,'微分运动学通过雅可比矩阵J(q)建立关节速度与末端速度的关系。令vₑ为由线速度和角速度组成的六维向量，则：')
eq(57,sub('v','e'),' = J(q)',dot('q'),'，',dot(sub('v','e')),' = J(q)',dot('q',True),' + ',dot('J'),'(q)',dot('q'))
b(57,'当单臂具有7个关节时，J为6×7矩阵，通常不能直接求普通矩阵逆。理论上可用伪逆求取满足任务速度的关节速度，并利用零空间自由度处理关节限位等次级目标；接近奇异构型时还需考虑阻尼、限速或轨迹调整。这些是模型控制器需要处理的条件，不代表当前代码已实现全部措施。')
b(57,'动力学进一步描述实现上述运动所需的关节力矩。沿用本科论文的拉格朗日建模思路，令L＝T−U为系统动能与势能之差，将各连杆的平动和转动动能汇总后，可写成关节空间矩阵形式：')
eq(57,'M(q)',dot('q',True),' + C(q,',dot('q'),')',dot('q'),' + g(q) + ',sub('τ','f'),' = τ + ',sup('J','T'),'(q)',sub('F','ext'))
b(57,'M为惯性矩阵，Cq̇表示科里奥利力与离心力的组合项，g为重力项，τf为摩擦力矩，τ为执行器输入；本式Fext定义为环境作用于末端的六维力／力矩，因此右端取正号。若将力定义为机械臂作用于环境的反力，符号需相应改变。所有力、速度与雅可比必须采用一致坐标系，不能直接混用不同传感器坐标下的分量。')
b(57,'在固定基座、模型准确且外力已处理的理想条件下，逆动力学控制通过补偿M、C与g等项，使关节加速度跟随指定辅助输入。这解释了“任务空间参考—关节运动—驱动力矩”的执行链。但空间双臂系统若基座自由运动，需将基座状态与两臂关节共同纳入广义动力学模型，单臂固定基座方程只能作为局部基础；不能仅将重力项设为零就等同于完整在轨动力学。')

# Contact phases and architecture, immediately after the existing admittance heading.
p=b(58,'本科论文第三章把装配接触过程区分为自由运动、碰撞过渡和平稳接触三个阶段。[4，3.2节] 自由运动阶段主要控制末端位姿；接触发生时，环境约束使接触力快速变化；进入持续接触后，则需要同时考虑位置偏差与交互力。高定位精度并不意味着能在定位误差和刚性约束下完成柔顺装配，这正是引入力学反馈与柔顺模型的原因。')
note(p,'整合论文第20—23页接触阶段及控制架构理论。未复制论文的力响应曲线与仿真效果，以免与当前双臂实验混淆。')
b(58,'阻抗与导纳描述相同的力—运动动态关系，但实现时的输入和输出不同。力矩型阻抗控制通常根据运动偏差形成目标笛卡尔力，再通过雅可比转置等模型关系生成关节力矩；导纳型控制则把测得的外力偏差输入虚拟动力学模型，得到位置、速度或加速度修正，并交由运动跟踪内环执行。本科论文所称“基于位置的阻抗控制”在本章统一称为“导纳型柔顺控制”。')

# Scalar response theory inserted before prior action-generation subsection.
p=b(64,'为进一步解释参数的作用，将上述六维关系在采用对角参数、忽略轴间耦合的局部假设下投影到某一方向，记虚拟质量、阻尼和刚度为m、d、k。零初值下，对单方向质量—阻尼—刚度方程作拉普拉斯变换，可得到力偏差到位移修正的传递函数：')
eq(64,'Y(s) = ',frac('E(s)','ΔF(s)'),' = ',frac('1',grp('m',sup('s','2'),'+ds+k')))
eq(64,sub('ω','n'),' = ',sqrt(frac('k','m')),'，ζ = ',frac('d',grp('2',sqrt('mk'))),'，',sub('e','ss'),' = ',frac(sub('Δf','0'),'k'))
b(64,'这里s为拉普拉斯复变量，与强化学习状态符号不同；ωn为无阻尼自然频率，ζ为阻尼比，eₛₛ为恒定力偏差Δf₀下的稳态位移。相同外力下，增大k会减小柔顺位移；固定m、k时，增大d提高阻尼比，有助于抑制振荡，但过度阻尼会减慢响应；固定d、k时，增大m降低自然频率且同时降低阻尼比。因而“惯性越大越稳定”或“阻尼越大越好”都不是普遍结论。[4，原文3.4.4节]')
note(p,'整合论文第28—31页导纳传递函数、自然频率及阻尼比。保留理论关系，修正参数影响的绝对化表述；本报告不采用论文中特定UR10算例的参数倍率作为双臂推荐值。')
b(64,'上述ζ<1、ζ＝1、ζ>1分别对应理想二阶模型的欠阻尼、临界阻尼和过阻尼情形，仅用于局部参数分析。真实闭环还包含机器人跟踪内环、接触刚度、采样延迟和饱和限制，因此不能仅靠正定参数或一个阻尼比判定整个装配系统安全稳定。实际整定应先验证无接触跟踪，再测试受控接触，最后加入学习策略。')
b(64,'在完整导纳实现中，外环求得的是相对名义轨迹的柔顺修正ξ，跟踪内环接收xcmd＝xnom＋ξ；这与DQN为任务推进产生的参考增量处在不同层次。应分别保存名义轨迹、柔顺修正与学习修正，避免重复叠加。当前代码外力通路的实现边界已在上文说明，此处给出的是理论控制架构。')

# Fusion conceptual bridge, before existing residual design.
p=b(82,'本科论文4.4.1节采用“DQN决策子系统＋基于位置的阻抗控制子系统”的两层结构：前者决定下一步怎样调整，后者负责实现动作对应的运动响应。[4] 本报告在此基础上进一步区分三个层次：任务层选择对准或推进动作，参考层组合先验与学习修正，执行层跟踪参考并处理柔顺响应。这样能够说明各模块的职责，避免把DQN、导纳控制和残差控制当作同一种算法。')
note(p,'承接论文第42页的分层控制思想。论文中的分层DQN与导纳组合不直接等于显式残差强化学习；后续残差加法为本报告已有设计，仍标为待实现。')
b(82,'两种“补偿”也应明确区分：导纳补偿依据即时力偏差满足给定动力学关系；学习补偿依据累计奖励改善动作序列，解决仅靠局部规则难以处理的初始偏差和推进时机问题。若网络直接选择全部参考增量，则属于学习决策驱动的分层控制；只有保留独立先验项，并在同一物理量、同一坐标系和同一更新周期下叠加网络项，才构成本章讨论的显式残差融合。')

# Parameter connection to new theory.
p=b(104,'上述域随机化还可从导纳参数的角度解释。对某一平移或转动方向，设基准值为m₀、d₀、k₀，抽样倍率分别为λm、λd、λk，则自然频率与阻尼比相对基准值满足：')
eq(104,frac(sub('ω','n'),sub('ω','n0')),' = ',sqrt(frac(sub('λ','k'),sub('λ','m'))),'，',frac('ζ',sub('ζ','0')),' = ',frac(sub('λ','d'),sqrt(grp(sub('λ','m'),sub('λ','k')))))
b(104,'因此独立改变刚度、阻尼和虚拟质量会同时改变响应速度与阻尼特性，不能将各倍率当作互不影响的参数。位置刚度倍率和姿态刚度倍率应分别用于对应方向的λk。训练范围扩大前，可按上式筛查极端组合，并通过真实闭环试验确认可执行范围；该筛查只提供整定依据，不替代接触与安全验证。')

# Update hard-coded references to the shifted admittance subsection.
for r in original[43].runs:
    if '上式为最优动作价值' in r.text:r.text=r.text.replace('上式为最优动作价值','前述Q*公式为最优动作价值')
for t in d.tables:
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    if '2.2.1' in r.text:r.text=r.text.replace('2.2.1','2.2.2')

# Keep citation consistent and preserve existing references.
insert(original[141],'[4] 华灵蕙. 基于强化学习的机械臂高精度装配技术[D]. 哈尔滨工业大学本科毕业论文, 2025. 本章理论整合范围：第2章运动学与动力学、第3章接触与柔顺控制、第4章4.2—4.3节及4.4.1节分层控制框架。',kind='small')
insert(original[141],'理论整合说明：D-H变换统一为改进D-H约定；TD误差统一为“目标减估计”；经验回放与目标网络分别解释；导纳参数按质量、阻尼、刚度的物理角色统一。原论文的UR10结构参数、训练曲线、成功率和耗时未作为空间双臂实验结果引用。',kind='small')
d.save(out)
check=Document(out)
assert len(check.tables)==len(Document(source).tables)
assert len(check.inline_shapes)==len(Document(source).inline_shapes)
task=next(t for t in check.tables if len(t.rows)==101)
assert all(r.cells[-1].text=='待测' for r in task.rows[1:])
manifest={'output':str(out),'added_chars':sum(map(len,added)),'paragraphs':len(check.paragraphs),'math_count':len(check.element.xpath('.//m:oMath')),'tables':len(check.tables),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(w/'merge_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False))
