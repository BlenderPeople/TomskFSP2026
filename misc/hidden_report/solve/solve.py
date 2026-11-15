from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
import subprocess
text = subprocess.run(["pdftotext", str(ROOT / "public/lab6.pdf"), "-"], check=True, capture_output=True, text=True).stdout
flag = re.search(r"tomskfsp\{[a-z0-9_]+\}", text)
if not flag:
    raise SystemExit("Флаг не найден")
print(flag.group())
