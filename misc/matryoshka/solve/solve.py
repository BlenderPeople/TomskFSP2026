#!/usr/bin/env python3
"""Контрольное решение задачи 01 «Матрёшка».

Распаковывает public/message.txt (base64 -> base32 -> hex) и сверяет результат
с эталонной константой FLAG. Запускается командой python3 solve/solve.py.
"""
import base64
from pathlib import Path

FLAG = "tomskfsp{m4tr0shk4_3nc0d1ng}"

HERE = Path(__file__).resolve().parent


def main() -> int:
    expected = FLAG

    data = (HERE.parent / "public" / "message.txt").read_text().strip()

    layer2_b32 = base64.b64decode(data).decode()          # снимаем слой 3
    layer1_hex = base64.b32decode(layer2_b32).decode()    # снимаем слой 2
    recovered = bytes.fromhex(layer1_hex).decode()        # снимаем слой 1

    print(f"Восстановлено: {recovered}")
    if recovered != expected:
        print(f"ОШИБКА: ожидалось {expected}")
        return 1
    print("OK: флаг совпадает с эталонным FLAG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
