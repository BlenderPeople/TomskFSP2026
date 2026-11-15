#!/usr/bin/env python3
"""Контрольное решение задачи 06 «Чёрный ящик».

Проверка 1 (динамика): запускаем public/crackme с эталонной константой FLAG —
должно напечататься ACCESS GRANTED.
Проверка 2 (статика): убеждаемся, что шифртекст (flag XOR 0xD2) пришит в код
в виде movabs-констант «stack string» — каждая 8-байтная порция присутствует
в бинарнике как непосредственный операнд.
"""
import subprocess
from pathlib import Path

FLAG = "tomskfsp{xor_is_not_encryption}"

HERE = Path(__file__).resolve().parent
XOR_KEY = 0xD2


def main() -> int:
    flag = FLAG
    binary = HERE.parent / "public" / "crackme"

    # 1) динамика: программа принимает флаг как ключ
    r = subprocess.run([str(binary), flag], capture_output=True, text=True)
    print(f"./crackme <flag> -> {r.stdout.strip()}")
    if "ACCESS GRANTED" not in r.stdout:
        print("ОШИБКА: бинарник не принял флаг")
        return 1

    # 2) статика: каждая 8-байтная константа stack string в коде
    enc = bytes(b ^ XOR_KEY for b in flag.encode())
    padded = enc.ljust((len(enc) + 7) // 8 * 8, bytes([XOR_KEY]))
    blob = binary.read_bytes()
    missing = [i for i in range(0, len(padded), 8)
               if padded[i:i + 8] not in blob]
    if missing:
        print(f"ОШИБКА: константы с байтами по смещениям {missing} не найдены")
        return 1
    print(f"stack string в коде: {len(padded) // 8} movabs-констант на месте "
          f"(XOR 0x{XOR_KEY:02x}, {len(flag)} байт флага)")
    print("OK: флаг совпадает с эталонным FLAG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
