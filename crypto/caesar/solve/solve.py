#!/usr/bin/env python3
# solve.py — авторское решение для omni_crypto_caesar
import os, sys

def caesar_unshift(text, shift):
    result = []
    for ch in text:
        if 'a' <= ch <= 'z':
            result.append(chr((ord(ch) - ord('a') - shift) % 26 + ord('a')))
        elif 'A' <= ch <= 'Z':
            result.append(chr((ord(ch) - ord('A') - shift) % 26 + ord('A')))
        else:
            result.append(ch)
    return ''.join(result)

def solve(taskdir):
    with open(os.path.join(taskdir, "cipher.txt")) as f:
        encrypted = f.read().strip()
    
    shift = 19
    decrypted = caesar_unshift(encrypted, shift)
    return f"tomskfsp{{{decrypted}}}"

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    print("Flag:", solve(d))
