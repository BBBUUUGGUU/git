from pathlib import Path
import pypdfium2 as pdf
w=Path(__file__).parent/'thesis_qa'
w.mkdir(exist_ok=True)
d=pdf.PdfDocument(r'C:\Users\25038\Desktop\新建文件夹\2021112938-华灵蕙-基于强化学习的机械臂高精度装配技术.pdf')
for n in [18,25,29,30,35,36,43,44,45,46,47]:
    d[n-1].render(scale=1.4).to_pil().save(w/f'page-{n}.png')
