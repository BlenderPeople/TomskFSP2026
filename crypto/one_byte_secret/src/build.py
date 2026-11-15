from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

import re
FLAG = 'tomskfsp{one_byte_is_not_a_secret}'
if not re.fullmatch(r'tomskfsp\{[a-z0-9_]{1,80}\}', FLAG):
    raise ValueError('Флаг должен иметь формат tomskfsp{...}: 1–80 строчных латинских букв, цифр или _ внутри скобок')

def update_docs():
    for doc in ('README.md', 'solve/writeup.md'):
        path = ROOT / doc
        if path.exists():
            path.write_text(re.sub(r'tomskfsp\{[a-z0-9_]+\}', lambda _: FLAG, path.read_text()))


message = b"PRIVATE NOTE / backup copy\nThe key was only one byte.\nRecovery token: %s\n" % FLAG.encode()
(ROOT/'public/note.hex').write_text(bytes(x ^ 0xA7 for x in message).hex() + '\n')
update_docs()
