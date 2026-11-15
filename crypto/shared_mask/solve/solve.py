from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
from PIL import Image
import sys
a = Image.open(ROOT / "public/frame-a.png").convert("RGB")
b = Image.open(ROOT / "public/frame-b.png").convert("RGB")
assert a.size == b.size
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "solve/result.png"
Image.frombytes("RGB", a.size, bytes(x ^ y for x, y in zip(a.tobytes(), b.tobytes()))).save(out)
print(out)
