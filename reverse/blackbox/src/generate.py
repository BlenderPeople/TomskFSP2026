#!/usr/bin/env python3
"""Задача 06 «Чёрный ящик»: сборка ELF-crackme (вариант «stack string»).

Принцип: шифртекст flag XOR 0xD2 пришит прямо в код — не в .rodata, а в виде
64-битных констант, загружаемых на стек инструкциями movabs («stack string»,
так делает малварь, чтобы скрыть строки от strings). При запуске программа
снимает XOR и сравнивает с аргументом через strcmp.

Благодаря этому задача решается полностью «браузерно»: dogbolt.org показывает
псевдокод с константами и ключом 0xD2, а CyberChef
(From Hex -> Swap Endianness(8) -> XOR(0xD2)) собирает флаг без терминала.
Флаг вшит константой FLAG.

Требует gcc (сборка выполняется на машине преподавателя при генерации).
"""
import subprocess
from pathlib import Path

FLAG = "tomskfsp{xor_is_not_encryption}"

TASK = Path(__file__).resolve().parents[1]
DIST = TASK / "public"
SOLUTION = TASK / "src"
XOR_KEY = 0xD2          # ключ подобран так, что шифртекст не-ASCII:
CHUNK = 8               # strings на бинарнике ничего не находит

C_TEMPLATE = """/* Сгенерировано src/generate.py - справочник для преподавателя. */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

int main(int argc, char **argv)
{{
    unsigned char buf[64] = {{0}};
    const size_t n = {n};                 /* длина флага */

    /* stack string: шифртекст (flag XOR 0x{hexkey}) пришит в код константами */
    {stores}

    for (size_t i = 0; i < n; i++)
        buf[i] ^= 0x{hexkey};
    buf[n] = '\\0';

    if (argc < 2) {{
        printf("usage: %s <key>\\n", argv[0]);
        return 1;
    }}
    if (strcmp((const char *)argv[1], (const char *)buf) == 0) {{
        printf("ACCESS GRANTED\\n");
        return 0;
    }}
    printf("ACCESS DENIED\\n");
    return 1;
}}
"""


def main() -> None:
    flag = FLAG
    enc = bytes(b ^ XOR_KEY for b in flag.encode())

    padded = enc.ljust((len(enc) + CHUNK - 1) // CHUNK * CHUNK, bytes([XOR_KEY]))
    chunks = [int.from_bytes(padded[i:i + CHUNK], "little")
              for i in range(0, len(padded), CHUNK)]

    stores = "\n    ".join(
        f'*(uint64_t *)(buf + {i * CHUNK:2}) = 0x{c:016X}ULL;'
        for i, c in enumerate(chunks))
    src = C_TEMPLATE.format(n=len(flag), hexkey=f"{XOR_KEY:02x}", stores=stores)

    DIST.mkdir(exist_ok=True)
    src_path = SOLUTION / "crackme.c"
    src_path.write_text(src, encoding="utf-8")

    subprocess.run(["gcc", "-O0", "-o", str(DIST / "crackme"), str(src_path)],
                   check=True)

    chef_hex = "".join(f"{c:016X}" for c in chunks)
    print(f"flag = {flag}")
    print(f"public/crackme: gcc -O0, stack string из {len(chunks)} констант "
          f"(movabs), XOR 0x{XOR_KEY:02x}")
    print(f"cyberchef: hex-строка констант = {chef_hex} "
          f"(From Hex -> Swap Endianness 8 -> XOR {XOR_KEY:02x})")


if __name__ == "__main__":
    main()
