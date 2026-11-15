#!/usr/bin/env python3
"""Задача 02 «Письмо Цезаря»: флаг внутри английского письма,
зашифрованного шифром Цезаря (сдвиг 11). Регистр сохраняется,
не-буквы не шифруются. Флаг вшит константой FLAG.
"""
from pathlib import Path

FLAG = "tomskfsp{caesar_fails_again}"

DIST = Path(__file__).resolve().parents[1] / "public"
SHIFT = 11

PLAINTEXT = f"""Dear Misha,

I hope your first semester at the university is going well.
Our information security lecturer told us a legend about an old
roman general who sent his love letters with a secret shift.
I decided to try the very same trick. If you can read this line,
you already know the answer.

My secret phrase for our club entrance is written below:

{FLAG}

Remember: he moved every letter by the same number of positions.
See you at the lab on Friday!

Yours,
Anya
"""


def caesar(text: str, k: int) -> str:
    out = []
    for c in text:
        if "a" <= c <= "z":
            out.append(chr((ord(c) - ord("a") + k) % 26 + ord("a")))
        elif "A" <= c <= "Z":
            out.append(chr((ord(c) - ord("A") + k) % 26 + ord("A")))
        else:
            out.append(c)
    return "".join(out)


def main() -> None:
    cipher = caesar(PLAINTEXT, SHIFT)
    DIST.mkdir(exist_ok=True)
    (DIST / "letter.txt").write_text(cipher, encoding="utf-8")
    print(f"flag = {FLAG}")
    print(f"public/letter.txt: шифр Цезаря, сдвиг {SHIFT}, {len(cipher)} символов")


if __name__ == "__main__":
    main()
