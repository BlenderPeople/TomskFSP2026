from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

import re
FLAG = 'tomskfsp{v1sual_x0r_explanat10n}'
if not re.fullmatch(r'tomskfsp\{[a-z0-9_]{1,80}\}', FLAG):
    raise ValueError('Флаг должен иметь формат tomskfsp{...}: 1–80 строчных латинских букв, цифр или _ внутри скобок')

def update_docs():
    for doc in ('README.md', 'solve/writeup.md'):
        path = ROOT / doc
        if path.exists():
            path.write_text(re.sub(r'tomskfsp\{[a-z0-9_]+\}', lambda _: FLAG, path.read_text()))


import os
from PIL import Image, ImageDraw, ImageFont, ImageChops
W,H = 1600,700
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
if not Path(font_path).exists():
    font_path = '/usr/share/fonts/TTF/DejaVuSansMono.ttf'
font = ImageFont.truetype(font_path, 52)
small = ImageFont.truetype(font_path, 28)
first = Image.new('RGB',(W,H),'black')
d = ImageDraw.Draw(first)
d.rectangle((65,60,W-65,H-60),outline=(40,130,170),width=4)
d.text((100,95),'FRAME 01 / proof sheet',font=small,fill=(90,130,150))
second = Image.new('RGB',(W,H),'black')
d = ImageDraw.Draw(second)
flag = FLAG
while d.textbbox((0,0),flag,font=font)[2] > W - 180:
    font = ImageFont.truetype(font_path, font.size - 1)
box = d.textbbox((0,0),flag,font=font)
d.text(((W-(box[2]-box[0]))//2,310),flag,font=font,fill='white')
mask = os.urandom(W*H*3)
for name, image in [('frame-a.png',first),('frame-b.png',second)]:
    raw = image.tobytes()
    encrypted = bytes(a ^ b for a,b in zip(raw,mask))
    Image.frombytes('RGB',(W,H),encrypted).save(ROOT/'public'/name)
# Expected visual proof is kept only for the author.
combined = bytes(a ^ b for a,b in zip(first.tobytes(),second.tobytes()))
Image.frombytes('RGB',(W,H),combined).save(ROOT/'solve/expected-result.png')
update_docs()
