---
title: "Письмо Цезаря"
category: crypto
difficulty: easy
points: 100
flag_format: "tomskfsp{...}"
---

# Письмо Цезаря

## Суть задачи

Классический шифр Цезаря: ключей всего 25, поэтому задача решается либо полным
перебором с проверкой читаемости, либо частотным анализом (в английском тексте
самая частая буква — `E`, на неё и подстраиваем сдвиг).

## Решение

### Шаг 1: перебор всех сдвигов

```python
cipher = open("letter.txt").read()

def unshift(text, k):
    out = []
    for c in text:
        if "a" <= c <= "z":
            out.append(chr((ord(c) - ord("a") - k) % 26 + ord("a")))
        elif "A" <= c <= "Z":
            out.append(chr((ord(c) - ord("A") - k) % 26 + ord("A")))
        else:
            out.append(c)
    return "".join(out)

for k in range(1, 26):
    plain = unshift(cipher, k)
    if "tomskfsp{" in plain:          # флаг-маркер мгновенно указывает верный сдвиг
        print(f"shift={k}\n{plain}")
        break
```

Верный сдвиг — **11** (то есть шифрование было ROT11). Среди расшифрованного
текста находим строку с флагом.

### Шаг 2 (альтернатива): частотный анализ

```python
from collections import Counter
freq = Counter(c.lower() for c in cipher if c.isalpha())
most_common = freq.most_common(1)[0][0]
k = (ord(most_common) - ord("e")) % 26   # самая частая буква шифртекста = E открытого
```

> **Флаг:** `tomskfsp{caesar_fails_again}`

## Вывод для студентов

Пространство ключей в 25 вариантов не выдерживает никакого перебора — любая
моноалфавитная замена ломается по частотам. Отсюда рост к полиалфавитным
шифрам (Виженер) и дальше к машинной криптографии.
