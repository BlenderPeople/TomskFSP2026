#!/usr/bin/env python3
"""Контрольное решение задачи 02 «Письмо Цезаря»: полный перебор 25 сдвигов,
поиск строки с флагом, сверка с эталонной константой FLAG.
"""
from pathlib import Path

PREFIX = "tomskfsp"
FLAG = "tomskfsp{caesar_fails_again}"

HERE = Path(__file__).resolve().parent


def unshift(text: str, k: int) -> str:
    out = []
    for c in text:
        if "a" <= c <= "z":
            out.append(chr((ord(c) - ord("a") - k) % 26 + ord("a")))
        elif "A" <= c <= "Z":
            out.append(chr((ord(c) - ord("A") - k) % 26 + ord("A")))
        else:
            out.append(c)
    return "".join(out)


def main() -> int:
    expected = FLAG
    prefix = PREFIX

    cipher = (HERE.parent / "public" / "letter.txt").read_text()

    for k in range(1, 26):
        plain = unshift(cipher, k)
        for line in plain.splitlines():
            if line.strip().startswith(prefix + "{"):
                print(f"Сдвиг {k}: {line.strip()}")
                if line.strip() == expected:
                    print("OK: флаг совпадает с эталонным FLAG")
                    return 0
    print("ОШИБКА: флаг не найден")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
