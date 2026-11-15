#!/usr/bin/env python3
# solve.py — авторское решение T8: ext4 + SQLite WAL.
# Пути к флагу:
#  1) debugfs: dump /home/analyst/app.db-wal -> strings -> флаг в «удалённой» записи событий.
#  2) debugfs: lsdel / ls -d / rdump -> deleted_secret.txt: имя видно в ext4 (unlink в debugfs
#     оставляет inode в lsdel при неперезаписи), либо флаг прямо в свободных блоках (strings).
import sys, os, subprocess, tempfile, re, glob

def dbg(img, cmds):
    r = subprocess.run(["debugfs", "-w", "-f", "-", img],
                       input="\n".join(cmds) + "\n", capture_output=True, text=True)
    return r.stdout + r.stderr

def solve(img):
    flags = set()
    with tempfile.TemporaryDirectory() as td:
        # 1) WAL-путь
        wal = os.path.join(td, "app.db-wal")
        subprocess.run(["debugfs", "-R", f"dump /home/analyst/app.db-wal {wal}", img],
                       capture_output=True)
        data = open(wal, "rb").read()
        for m in re.finditer(rb"tomskfsp\{[^}]{1,80}\}", data):
            flags.add(m.group(0).decode())
        # 2) удалённый файл: lsdel + rdump инода
        out = dbg(img, ["lsdel", "ls -l /home/analyst"])
        # lsdel даёт "Inode N is marked in use..." или пусто; перебираем свободные блоки строками
        raw = open(img, "rb").read()
        for m in re.finditer(rb"tomskfsp\{[^}]{1,80}\}", raw):
            flags.add(m.group(0).decode())
    assert flags, "флаг не найден"
    for f in sorted(flags):
        print("[+] найден:", f)
    print("[+] Flag:", sorted(flags)[0])
    return sorted(flags)[0]

if __name__ == "__main__":
    img = sys.argv[1] if len(sys.argv) > 1 else "disk.img"
    solve(img)
