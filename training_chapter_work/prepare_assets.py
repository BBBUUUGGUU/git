import json,sys,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.stdout.reconfigure(encoding='utf-8')
w=Path(__file__).parent
names=['training_logs_10actions_adaptive_insert_30to5_200steps_800episodes','training_logs_10actions_random_kpkdmd_peg16to21_hole22_200steps_500episodes']
font=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',28)
small=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',24)
for j,name in enumerate(names):
    root=w/'data'/name
    r=np.load(root/'ep_rewards.npy',allow_pickle=False);s=np.load(root/'successList.npy',allow_pickle=False)
    records=json.loads((root/'random_offsets.json').read_text())
    assert len(r)==len(s)==len(records)
    assert np.allclose(r,[z['episode_reward'] for z in records])
    assert np.array_equal(s,[z['success'] for z in records])
    x=np.arange(1,len(r)+1);window=50
    im=Image.new('RGB',(1600,1000),'white');draw=ImageDraw.Draw(im)
    for panel,(top,bottom,lo,hi,title) in enumerate([(90,450,float(np.floor(r.min()/50)*50),float(np.ceil(r.max()/50)*50),'累计奖励'),(590,885,0,100,'50回合窗口成功比例（%）')]):
        left,right=140,1530
        xy=lambda a,b:(left+(a-1)/max(len(r)-1,1)*(right-left),bottom-(b-lo)/(hi-lo)*(bottom-top))
        draw.text((left,top-50),title,font=font,fill='#222222')
        for val in np.linspace(lo,hi,5):
            yy=xy(1,val)[1];draw.line((left,yy,right,yy),fill='#dddddd',width=1);draw.text((left-90,yy-17),f'{val:.0f}',font=small,fill='#444444')
        draw.line((left,top,left,bottom,right,bottom),fill='#444444',width=2)
        for ep in np.linspace(1,len(r),5).astype(int):
            xx=xy(ep,lo)[0];draw.text((xx-25,bottom+15),str(ep),font=small,fill='#444444')
        if panel==0:
            draw.line([xy(a,b) for a,b in zip(x,r)],fill='#bcc2ca',width=2)
            y=np.convolve(r,np.ones(window)/window,'valid')
            draw.text((left+400,top-50),'灰线：单回合奖励    蓝线：50回合滑动均值',font=small,fill='#173d65')
        else:y=100*np.convolve(s,np.ones(window)/window,'valid')
        draw.line([xy(a,b) for a,b in zip(x[window-1:],y)],fill='#173d65',width=5)
    draw.text((490,955),'训练回合（按日志顺序，1起始）',font=font,fill='#222222')
    im.save(w/f'training_curve_{j+1}.png')
    print(name,'N',len(r),'success',int(s.sum()),'first100',float(r[:100].mean()),'last100',float(r[-100:].mean()),'first100_success',float(s[:100].mean()),'last100_success',float(s[-100:].mean()))
rng=np.random.default_rng(20260831)
tasks=[]
for i in range(100):
    z={'id':i+1,'peg_mm':int(rng.choice([16,17,18,19,20,21])),'rho_mm':float(rng.uniform(10,25)),'angle_deg':float(rng.uniform(0,360)),'kl':float(rng.uniform(.75,1.25)),'ka':float(rng.uniform(.85,1.15)),'kd':float(rng.uniform(.8,1.2)),'md':float(rng.uniform(.8,1.2)),'tolerance_mm':float(rng.choice([.35,.50,1.00])),'status':'未执行'}
    tasks.append(z)
(w/'test_tasks_100.json').write_text(json.dumps(tasks,ensure_ascii=False,indent=2),encoding='utf-8')
root=Path(r'D:\BAI\Dual\0622\MulitRobotAssemble-copy\MulBotAsm')
manifest={}
for f in ['trainer/dqn_train3.py','envs/DSAE1.py','envs/DualSpaceArmController.py','algorithm/dqn_model.py']:
    src=root/f;dst=w/'code_snapshot'/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    manifest[f]=hashlib.sha256(dst.read_bytes()).hexdigest()
(w/'code_hashes.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
