#!/usr/bin/env python3
"""Задача 01 «Матрёшка»: флаг упаковывается в три слоя кодирования.

Слой 1 (внутренний): флаг -> hex-строка
Слой 2: hex-строка -> base32
Слой 3 (внешний): base32-строка -> base64

Итог кладётся в public/message.txt. Флаг вшит константой FLAG.
"""
import base64
from pathlib import Path

FLAG = "tomskfsp{m4tr0shk4_3nc0d1ng}"

DIST = Path(__file__).resolve().parents[1] / "public"


def main() -> None:
    flag = FLAG

    layer1_hex = flag.encode("utf-8").hex()          # слой 1: hex
    layer2_b32 = base64.b32encode(layer1_hex.encode()).decode()   # слой 2: base32
    layer3_b64 = base64.b64encode(layer2_b32.encode()).decode()   # слой 3: base64

    DIST.mkdir(exist_ok=True)
    (DIST / "message.txt").write_text(layer3_b64 + "\n", encoding="utf-8")

    print(f"flag = {flag}")
    print(f"public/message.txt: {len(layer3_b64)} символов base64")


if __name__ == "__main__":
    main()
