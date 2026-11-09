from pathlib import Path
from copy import deepcopy
import json,re,sys
from docx import Document
from docx.shared import Pt,Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_BREAK,WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
sys.stdout.reconfigure(encoding='utf-8')
w=Path(__file__).parent
out=Path(r'C:\Users\25038\Desktop\新建文件夹\空间双臂机器人在轨高精度插拔操作仿真训练研究报告_第二章详细补充版.docx')
d=Document(w/'source.docx');old=list(d.paragraphs)
bodypr=deepcopy(old[29]._p.pPr)
headings={1:deepcopy(old[28]._p.pPr),2:deepcopy(old[31]._p.pPr),3:deepcopy(old[34]._p.pPr),4:deepcopy(old[40]._p.pPr),5:deepcopy(old[42]._p.pPr)}
for p in old[28:]:p._p.getparent().remove(p._p)
width=8312
fig_no=0;table_no=0;eq_no=0

def elem(tag,attrs={}):
    e=OxmlElement(tag)
    for k,v in attrs.items():e.set(qn(k),str(v))
    return e

def mathrun(text):
    r=elem('m:r');t=elem('m:t');t.text=text;r.append(t);return r

def box(tag,parts):
    b=elem(tag)
    for part in parts:b.append(mathrun(part) if isinstance(part,str) else deepcopy(part))
    return b

def sub(base,index):return box('m:sSub',[box('m:e',[base]),box('m:sub',[index])])
def sup(base,index):return box('m:sSup',[box('m:e',[base]),box('m:sup',[index])])
def dot(base,double=False):
    a=elem('m:acc');pr=elem('m:accPr');pr.append(elem('m:chr',{'m:val':'\u0308' if double else '\u0307'}));a.append(pr);a.append(box('m:e',[base]));return a
def frac(a,b):return box('m:f',[box('m:num',[a]),box('m:den',[b])])
def group(*parts):return box('m:box',[box('m:e',parts)])

def equation_parts(i):
    st=sub('s','t');at=sub('a','t');rt=sub('r','t+1');sp=sub('s','t+1');gt=sub('G','t')
    md=sub('M','d');dd=sub('D','d');kd=sub('K','d');ed=dot('e');edd=dot('e',True)
    defs={
    1:[gt,' = ',rt,' + γ',sub('r','t+2'),' + ',sup('γ','2'),sub('r','t+3'),' + ⋯'],
    2:[sup('V','π'),'(s) = ',sub('E','π'),'[',gt,' | ',st,'=s]，',sup('Q','π'),'(s,a) = ',sub('E','π'),'[',gt,' | ',st,'=s，',at,'=a]'],
    3:[sup('Q','*'),'(s,a) = E[',rt,' + γ ',sub('max',"a′"),' ',sup('Q','*'),'(',sp,',a′) | s,a]'],
    4:[sub('δ','t'),' = ',rt,' + γ ',sub('max','a′'),' Q(',sp,',a′) − Q(',st,',',at,')'],
    5:['Q(',st,',',at,') ← Q(',st,',',at,') + α',sub('δ','t')],
    6:[sub('y','i'),' = ',sub('r','i'),' + γ(1−',sub('d','i'),') ',sub('max','a′'),' Q(',sup(sub('s','i'),'′'),',a′；',sup('θ','−'),')'],
    7:['L(θ) = ',frac('1','B'),' ',sub('∑','i'),' ',sup(group('[',sub('y','i'),' − Q(',sub('s','i'),',',sub('a','i'),'；θ)]'),'2')],
    8:[md,' ',edd,' + ',dd,' ',ed,' + ',kd,' e = ΔF'],
    9:['E = ',frac('1','2'),sup(ed,'T'),md,' ',dot('e'),' + ',frac('1','2'),sup('e','T'),kd,' e，',dot('E'),' = −',sup(dot('e'),'T'),dd,' ',dot('e'),' ≤ 0'],
    10:[sub('u','H,⊥'),' = sat(−',sub('k','h'),sub('e','⊥'),'，',sub('u','⊥,max'),')'],
    11:[sub('p','ref,t+1'),' = ',sub('p','t'),' + ',sub('Π','U'),'[',sub('u','H'),'(',sub('s','t'),') + β',sub('u','R'),'(',sub('s','t'),',',sub('a','t'),')]'],
    12:[sub('r','base'),' = 2500Δρ + ',sub('r','a'),' + 200 max(0,0.003−ρ)'],
    13:['                  + 20 min(h,0.020) − 8ρ − 0.02'],
    14:['成功率 = ',frac(sub('N','success'),sub('N','valid')),' × 100%'],
    15:['平均成功用时 = ',frac('成功任务实际仿真用时之和',sub('N','success'))],
    }
    return defs[i]

def font(r,size=14,bold=False,face='宋体'):
    r.font.name='Times New Roman';r.font.size=Pt(size);r.bold=bold
    r._r.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),face)

def para(text='',kind='body',level=0):
    p=d.add_paragraph()
    if level:
        p._p.insert(0,deepcopy(headings[level]));p.paragraph_format.keep_with_next=True
        if level==1:p.paragraph_format.page_break_before=True
        p.add_run(text)
    else:
        p._p.insert(0,deepcopy(bodypr));font(p.add_run(text))
        p.paragraph_format.widow_control=True
    if kind in ['caption','small','equation','plot']:
        pf=p.paragraph_format;pf.first_line_indent=Pt(0);pf.space_before=Pt(4);pf.space_after=Pt(4)
        pf.line_spacing=Pt(18);pf.line_spacing_rule=WD_LINE_SPACING.AT_LEAST
        p._p.get_or_add_pPr().append(elem('w:snapToGrid',{'w:val':'0'}))
        ind=p._p.get_or_add_pPr().get_or_add_ind()
        for a in ['firstLine','firstLineChars','left','leftChars','right','rightChars','hanging','hangingChars']:ind.set(qn('w:'+a),'0')
        if kind in ['caption','equation','plot']:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:font(r,12 if kind=='caption' else 11)
        if kind=='caption':pf.keep_with_next=True
    return p

def note(p,text):d.add_comment(p.runs[:1],text,author='编写与核验说明',initials='核验')

def table(title,headers,rows,widths=None,fontsize=10.5):
    global table_no
    table_no+=1
    para(f'表2-{table_no}  {title}','caption')
    n=len(headers)
    widths=widths or ([width//n]*(n-1)+[width-(width//n)*(n-1)])
    assert sum(widths)==width
    t=d.add_table(rows=1,cols=n);t.alignment=WD_TABLE_ALIGNMENT.LEFT;t.autofit=False
    pr=t._tbl.tblPr
    for tag in ['w:tblW','w:tblInd','w:tblCellMar','w:tblBorders','w:tblLayout']:
        x=pr.find(qn(tag))
        if x is not None:pr.remove(x)
    pr.append(elem('w:tblW',{'w:type':'dxa','w:w':width}))
    pr.append(elem('w:tblInd',{'w:type':'dxa','w:w':100}))
    pr.append(elem('w:tblLayout',{'w:type':'fixed'}))
    mar=elem('w:tblCellMar')
    for side,val in [('top',65),('bottom',65),('left',100),('right',100)]:mar.append(elem('w:'+side,{'w:w':val,'w:type':'dxa'}))
    pr.append(mar)
    borders=elem('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:borders.append(elem('w:'+side,{'w:val':'single','w:sz':'4','w:color':'777777'}))
    pr.append(borders)
    for gc,cw in zip(t._tbl.tblGrid.gridCol_lst,widths):gc.set(qn('w:w'),str(cw))
    for ri,vals in enumerate([headers]+rows):
        row=t.rows[0] if ri==0 else t.add_row()
        row._tr.get_or_add_trPr().append(elem('w:cantSplit'))
        if ri==0:row._tr.get_or_add_trPr().append(elem('w:tblHeader'))
        for ci,(cell,val,cw) in enumerate(zip(row.cells,vals,widths)):
            cell.width=Twips(cw);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcw=cell._tc.get_or_add_tcPr().find(qn('w:tcW'));tcw.set(qn('w:w'),str(cw));tcw.set(qn('w:type'),'dxa')
            p=cell.paragraphs[0];pf=p.paragraph_format
            pf.first_line_indent=Pt(0);pf.left_indent=Pt(0);pf.right_indent=Pt(0);pf.space_before=Pt(0);pf.space_after=Pt(0);pf.line_spacing=Pt(15);pf.keep_with_next=(ri==0)
            p._p.get_or_add_pPr().append(elem('w:snapToGrid',{'w:val':'0'}))
            ind=p._p.get_or_add_pPr().get_or_add_ind()
            for a in ['firstLine','firstLineChars','left','leftChars','right','rightChars','hanging','hangingChars']:ind.set(qn('w:'+a),'0')
            p.alignment=WD_ALIGN_PARAGRAPH.CENTER if ri==0 or n>=6 else WD_ALIGN_PARAGRAPH.LEFT
            font(p.add_run(str(val)),fontsize,ri==0)
            if ri==0:cell._tc.get_or_add_tcPr().append(elem('w:shd',{'w:fill':'EEEEEE'}))
    p=para('','small');p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=Pt(3)
    return t

tables={}
tables['actions']=('现有DQN离散动作及环境映射',['环境动作','含义','参考位移'],[
['1','精细插入','末端局部−Z方向，5 mm'],['2、3','精细径向调整','末端局部X方向，±1 mm'],['4、5','精细径向调整','末端局部Y方向，±1 mm'],['6、7','粗略径向调整','末端局部X方向，±10 mm'],['8、9','粗略径向调整','末端局部Y方向，±10 mm'],['10','自适应粗插入','末端局部−Z方向，0～30 mm']], [1100,2450,4762])
tables['network']=('网络与训练更新参数（现有入口）',['参数','取值','含义及口径'],[
['状态/动作维度','22 / 10','16维观测＋6维域参数；10种动作'],['隐藏层/激活','128、128 / ReLU','两层全连接隐藏层'],['learning_rate','0.0005','Adam学习率'],['reward_decay','0.95','折扣因子γ'],['memory_size','10000','回放容量，按转移条目计'],['batch_size','64','每次学习抽取样本数'],['replace_target_iter','300','按学习更新次数同步目标网络'],['epsilon初值/上限','0 / 0.9','代码中为贪心动作概率'],['e_greedy_increment','0.0004','每次学习后递增贪心概率'],['训练回合','500（计划）','实际完成量以日志条数为准'],['learn触发条件','step>100且step%5=0','step每回合重新计数'],['损失/优化器','MSE / Adam','实现差异见2.1.2'],['随机种子','NumPy 42；Torch 2','当前代码；不等于仿真全部确定性'],['模型保存','训练循环结束后','中途日志不保证有对应权重'],['日志保存','每回合结束后','奖励、成功、随机化与失败原因']],[2250,1900,4162])
tables['motion']=('动作、控制与终止参数（现有入口）',['参数','配置值','作用'],[
['dt','0.005 s','控制器积分时间步；需核对仿真步长'],['action_steps','50','每个决策动作执行的内循环步数'],['linear_step','1 mm','精细径向位移'],['coarse_linear_scale','10','粗径向步长为10 mm'],['insertion_step','5 mm','精细插入参考位移'],['coarse_insertion_step','30 mm','粗插入步长上限'],['adaptive_coarse_insertion','True','开启分段粗插入步长'],['coarse_insert_alignment_gate','1.5 mm','近入口粗插入允许条件'],['pre_insert_distance','30 mm','计算插入深度的参考距离'],['max_steps','200','每回合决策步数上限'],['max_align_error','60 mm','径向越界终止阈值'],['最大深度/后退量','20 / 50 mm','过深与轴向后退终止边界'],['最小成功深度','8 mm','当前几何代理深度判据'],['force_limit','80（配置）','当前终止分支未据此执行限力'],['reset_preposition_steps','500','物理偏差预定位过程步数'],['action_frame','left_ee','动作在左末端坐标系表达'],['control_mode','admittance','配置标签；实际通路见2.2.1'],['Kp基准对角项','180×3；80×3','分别为位置和姿态刚度'],['Kd/Md基准','4Kp / 1.2Kp','分别为阻尼和虚拟质量配置'],['右臂关节PD','1500 / 100','比例与速度阻尼系数'],['verbose/debug_interval','True / 20','输出开关与打印间隔']],[2750,1800,3762])
tables['domain']=('域随机化参数与精度判据（现有入口）',['参数','取值或范围','含义'],[
['random_xy_min/max','10 / 25 mm','径向偏差半径的均匀抽样边界'],['偏差方位角','0～2π','方位均匀抽样；非面积均匀分布'],['randomize_physical_reset','True','通过物理预定位施加偏移'],['randomize_controller_gains','True','启用增益与虚拟质量随机化'],['kp_linear_scale_range','0.75～1.25','位置刚度缩放倍率'],['kp_angular_scale_range','0.85～1.15','姿态刚度缩放倍率'],['kd_scale_range','0.80～1.20','阻尼倍率'],['md_scale_range','0.80～1.20','虚拟质量倍率'],['randomize_geometry','True','启用轴对象几何缩放'],['peg_diameter_choices','16、17、18、19、20、21 mm','当前离散抽样集合'],['peg_diameter_range','16～21 mm','连续回退抽样/归一化范围'],['nominal_peg_diameter','18 mm','轴几何缩放基准'],['fixed_hole_diameter','22 mm','固定孔径参数；未缩放孔对象'],['实际单边间隙c','0.5～3.0 mm','(22 mm−轴径)/2'],['hole_clearance_range','0.5～2.0 mm','当前归一化范围，非实际抽样范围'],['peg_length_axis','x','径向缩放模式的轴向定义'],['scale_peg_length','True','当前整体缩放，长度也改变'],['include_domain_params_in_state','True','追加6维域参数'],['success_alignment_limit','clip(0.75c,0.35,1.20) mm','派生精度阈值，不是独立抽样'],['模型与参考帧','见正文','场景对象/URDF/帧需一致']],[2800,2500,3012])
tables['results']=('已保存训练日志统计（非独立测试）',['记录组','回合数','成功数','训练成功比例','均值奖励','失败构成'],[
['A：自适应插入','800','260','32.5%','79.30','超时477；过深51；越界12'],['B：多参数随机化','192','0','0%','−87.27','超时169；越界23']],[1550,650,650,1300,900,3262])
tables['test_protocol']=('100组独立装配测试的四类初始化设计',['因素类别','随机化定义','实施状态'],[
['几何尺寸','轴径六档等概率；孔径22 mm固定','沿用既有参数接口，核对实际缩放'],['初始位置误差','半径10～25 mm；角度0～360°','需记录实际预定位偏差'],['控制参数','Kp平移/转动、Kd、Md四个倍率','沿用既有随机化接口'],['精度要求','τ_req∈{0.35,0.50,1.00} mm','新增独立要求；τ_eff=min(τ_req,0.75c)']],[1550,3300,3462])
tasks=json.loads((w/'test_tasks_100.json').read_text(encoding='utf-8'))
rows=[]
for z in tasks:
    eff=min(z['tolerance_mm'],.75*(22-z['peg_mm'])/2)
    rows.append([f"{z['id']:03d}",str(z['peg_mm']),f"{z['rho_mm']:.2f}",f"{z['angle_deg']:.1f}",f"{z['kl']:.2f}/{z['ka']:.2f}",f"{z['kd']:.2f}/{z['md']:.2f}",f"{z['tolerance_mm']:.2f}/{eff:.3f}",'待测'])
tables['tasks100']=('100组随机初始化任务（预生成方案，全部未执行）',['编号','轴径\nmm','偏差ρ\nmm','角度\n°','Kp倍率\n位置/姿态','倍率\nKd/Md','精度mm\n要求/有效','结果'],rows,[700,700,800,700,1600,1450,1562,800])
tables['test_results']=('独立100组装配测试结果登记表',['统计项目','填写规则','本次状态'],[
['计划任务数量','100组','已列出输入方案'],['有效执行数量','以有效运行记录计','未执行'],['成功数量','同时满足几何与安全条件','待测'],['总体成功率','成功数/有效组数×100%','待测'],['候选成功率目标','90%（尚未验证）','不作为已取得结果'],['平均/中位成功用时','仅对成功组使用仿真时间戳','待测'],['最终径向误差','记录均值、中位数与分位数','待测'],['接触峰值力/力矩','由连续记录计算','待测'],['失败原因分布','超时、越界、过深、限力等','待测'],['异常运行数量','通信/模型异常单独登记','待测']],[2200,3400,2712])

for line in (w/'chapter.txt').read_text(encoding='utf-8').splitlines():
    if not line:continue
    if line.startswith('#'):
        h,text=line.split(' ',1);p=para(text,level=len(h))
        if len(h)==1:note(p,'按用户要求补写第二章，保留封面与第一章。参数依据本次代码快照；现有实现、拟设计残差融合与实测训练日志分别标识。')
    elif line.startswith('[[eq:'):
        eq_no+=1;p=para('','equation');p.paragraph_format.keep_together=True
        mp=elem('m:oMathPara');mppr=elem('m:oMathParaPr');mppr.append(elem('m:jc',{'m:val':'center'}));mp.append(mppr)
        om=box('m:oMath',equation_parts(eq_no));mp.append(om);p._p.append(mp)
    elif line.startswith('[[table:'):
        key=line[8:-2];title,headers,rows,widths=tables[key];table(title,headers,rows,widths)
    elif line.startswith('[[plot:'):
        num=int(line[7:-2]);p=para('','plot');p.paragraph_format.keep_with_next=True
        p.runs[0].add_picture(str(w/f'training_curve_{num}.png'),width=Twips(width))
        p._p.xpath('.//wp:docPr')[0].set('descr',f'真实训练日志第{num}组奖励和50回合窗口成功比例')
        p=para(f'图2-{num}  '+('A组800回合自适应插入训练曲线' if num==1 else 'B组192回合多参数随机化训练曲线'),'caption');p.paragraph_format.keep_with_next=False
    elif line=='[[refs]]':
        p=para('本章参考文献与数据来源','small');font(p.runs[0],12,True);p.paragraph_format.keep_with_next=True
        refs=[
        '[1] Sutton R S, Barto A G. Reinforcement Learning: An Introduction. 2nd ed. MIT Press, 2018. https://mitpress.mit.edu/9780262039246/reinforcement-learning/',
        '[2] Mnih V, et al. Human-level control through deep reinforcement learning. Nature, 2015, 518: 529–533. https://doi.org/10.1038/nature14236',
        '[3] Johannink T, et al. Residual Reinforcement Learning for Robot Control. arXiv:1812.03201. https://arxiv.org/abs/1812.03201',
        '代码依据：MulBotAsm/trainer/dqn_train3.py；envs/DSAE1.py；envs/DualSpaceArmController.py；algorithm/dqn_model.py。本章参数按2026年8月31日读取的版本核对；未修改项目代码或启动仿真。',
        'A组日志：trainer/training_logs_10actions_adaptive_insert_30to5_200steps_800episodes；B组日志：trainer/training_logs_10actions_random_kpkdmd_peg16to21_hole22_200steps_500episodes。曲线与统计依据各目录的ep_rewards.npy、successList.npy、random_offsets.json、fail_reasons.json快照。',
        '输入计划：表2-7的100组参数由NumPy default_rng(20260831)生成；结果栏全部待测，不能作为成功率、接触力或完成时间的实验凭证。'
        ]
        for t in refs:para(t,'small')
    else:
        p=para(line)
        if line.startswith('代码中Kp'):note(p,'核对DSAE1._control_both_arms与DualSpaceArmController.AdmittanceController：forceI为零，当前getAqt2生效调用未传入he。避免误写为已完成真实外力偏差闭环验证。')
        if line.startswith('当前envStep实际'):note(p,'保留用户要求的残差算法章节，但正文将显式相加公式标为设计方案。现有源码中没有该相加融合结构，也没有对应独立性能验证。')
        if line.startswith('本次没有完成独立'):note(p,'90%来自用户提出的目标/疑问，不能填为实测成功率。表2-7仅为100组随机输入方案。')

d.save(out)
# Structural checks only; visual QA is performed using Word export afterward.
check=Document(out)
text='\n'.join(p.text for p in check.paragraphs)
assert '2.1' not in text[:10]
chapter=text[text.index('空间双臂机器人高精度插拔操作高效学习',text.index('高精度插拔操作任务高拟真仿真场景建模')+1):]
assert len(tables['tasks100'][2])==100
assert len(check.comments)>=4
print(out)
print('Chapter source chars',len((w/'chapter.txt').read_text(encoding='utf-8')),'tables',table_no,'equations',eq_no)
