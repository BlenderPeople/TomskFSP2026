#!/usr/bin/env python3
# solve.py — авторское решение для omni_misc_atbash
import zipfile, os, sys, subprocess, tempfile

def atbash(text):
    result = []
    for ch in text:
        if 'a' <= ch <= 'z':
            result.append(chr(ord('z') - (ord(ch) - ord('a'))))
        elif 'A' <= ch <= 'Z':
            result.append(chr(ord('Z') - (ord(ch) - ord('A'))))
        else:
            result.append(ch)
    return ''.join(result)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd} failed: {r.stderr or r.stdout}")
    return r.stdout

def solve(taskdir):
    task_zip = os.path.join(taskdir, "task.zip")
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(task_zip) as z:
            z.extractall(td)
        jpg_path = os.path.join(td, "image.jpg")
        flag_zip = os.path.join(td, "flag.zip")
        pass_path = os.path.join(td, "password.txt")

        run(["steghide", "extract", "-sf", jpg_path, "-p", "718", "-xf", pass_path, "-f", "-q"])
        password = open(pass_path).read().strip()

        run(["unzip", "-o", "-q", "-P", password, flag_zip, "-d", td])
        encrypted = open(os.path.join(td, "cipher.txt")).read().strip()

    decrypted = atbash(encrypted)
    return f"tomskfsp{{{decrypted}}}"

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    print("Flag:", solve(d))
