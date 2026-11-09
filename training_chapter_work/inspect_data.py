from pathlib import Path
from docx import Document
import numpy as np
import json,sys,hashlib,shutil
sys.stdout.reconfigure(encoding='utf-8')
w=Path(__file__).parent
d=Document(w/'source.docx')
for i,p in enumerate(d.paragraphs):
    print(i,p.style.name,repr(p.text))
for i in [24,25,30]:
    if i<len(d.paragraphs):print('FORMAT',i,d.paragraphs[i]._p.xml[:2000])
root=Path(r'D:\BAI\Dual\0622\MulitRobotAssemble-copy\MulBotAsm')
summary=[]
for folder in sorted((root/'trainer').glob('training_logs*')):
    if not folder.is_dir():continue
    try:
        r=np.load(folder/'ep_rewards.npy',allow_pickle=False)
        s=np.load(folder/'successList.npy',allow_pickle=False)
        record=json.loads((folder/'random_offsets.json').read_text()) if (folder/'random_offsets.json').exists() else []
        x={'folder':folder.name,'n':len(r),'n_success':len(s),'success':int(s.sum()),'rate':float(s.mean()),'mean':float(r.mean()),'std':float(r.std()),'min':float(r.min()),'max':float(r.max()),'first50':float(r[:50].mean()),'last50':float(r[-50:].mean()),'last100_rate':float(s[-100:].mean()),'records':len(record),'fail':json.loads((folder/'fail_reasons.json').read_text())}
        if record:x['keys']=list(record[0].keys()); x['first_record']=record[0]
        if len(r)==len(s)==len(record):x['reward_match']=bool(np.allclose(r,[z['episode_reward'] for z in record]));x['success_match']=bool(np.array_equal(s,[int(z['success']) for z in record]))
        summary.append(x)
    except Exception as e:print('SKIP',folder.name,str(e))
(w/'stats.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
for x in summary:print(json.dumps({k:v for k,v in x.items() if k not in ['keys','first_record']},ensure_ascii=False))
names=['training_logs_10actions_adaptive_insert_30to5_200steps_800episodes','training_logs_10actions_random_kpkdmd_peg16to21_hole22_200steps_500episodes','training_logs_10actions_random_kpkdmd_peg18to21_hole22_uniform_200steps_1000episodes']
for name in names:
    folder=root/'trainer'/name
    dest=w/'data'/name;dest.mkdir(parents=True,exist_ok=True)
    for fn in ['ep_rewards.npy','successList.npy','fail_reasons.json','random_offsets.json']:
        if (folder/fn).exists():shutil.copy2(folder/fn,dest/fn)
    x=next(x for x in summary if x['folder']==name)
    print('DETAIL',name,json.dumps(x.get('first_record',{}),ensure_ascii=False))
