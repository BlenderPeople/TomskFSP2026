#!/usr/bin/env python3
# gen.py — генератор варианта для omni_crypto_caesar
# Параметры: <outdir> <variant> <flag>
import os, sys, random

def caesar_shift(text, shift):
    result = []
    for ch in text:
        if 'a' <= ch <= 'z':
            result.append(chr((ord(ch) - ord('a') + shift) % 26 + ord('a')))
        elif 'A' <= ch <= 'Z':
            result.append(chr((ord(ch) - ord('A') + shift) % 26 + ord('A')))
        else:
            result.append(ch)
    return ''.join(result)

def main(outdir, variant, flag):
    random.seed(variant)
    os.makedirs(outdir, exist_ok=True)
    
    shift = 19
    inner = flag.replace("tomskfsp{", "").replace("}", "")
    encrypted = caesar_shift(inner, shift)
    
    with open(f"{outdir}/cipher.txt", "w") as f:
        f.write(encrypted + "\n")
    
    import json
    with open(f"{outdir}/.key.json", "w") as f:
        json.dump({"flag": flag, "inner": inner, "shift": shift, "encrypted": encrypted}, f, indent=2)

if __name__ == "__main__":
    outdir, variant, flag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    main(outdir, variant, flag)
    print(f"variant {variant}: omni_crypto_caesar OK -> {flag}")
