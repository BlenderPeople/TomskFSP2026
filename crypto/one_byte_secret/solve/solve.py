from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
data = bytes.fromhex((ROOT / "public/note.hex").read_text())
for key in range(256):
    plain = bytes(b ^ key for b in data)
    flag = re.search(rb"tomskfsp\{[a-z0-9_]+\}", plain)
    if flag:
        print(flag.group().decode())
        break
else:
    raise SystemExit("Флаг не найден")
