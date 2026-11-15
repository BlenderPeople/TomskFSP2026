#!/usr/bin/env python3
# solve.py — авторское решение для omni_forensic_stegify
import os, sys, subprocess, tempfile

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd} failed: {r.stderr or r.stdout}")
    return r.stdout

def solve(taskdir):
    dd_path = os.path.join(taskdir, "forensic_image.dd")
    if not os.path.isfile(dd_path):
        raise FileNotFoundError(dd_path)

    with tempfile.TemporaryDirectory() as td:
        jpg_path = os.path.join(td, "steghide_image.jpg")
        zip_path = os.path.join(td, "flag.zip")
        pass_path = os.path.join(td, "password.txt")

        run(["debugfs", "-R", f"dump /Pictures/steghide_image.jpg {jpg_path}", dd_path])
        run(["debugfs", "-R", f"dump /Documents/flag.zip {zip_path}", dd_path])
        run(["steghide", "extract", "-sf", jpg_path, "-p", "123", "-xf", pass_path, "-f", "-q"])

        password = open(pass_path).read().strip()
        run(["unzip", "-o", "-q", "-P", password, zip_path, "-d", td])
        secret_path = os.path.join(td, "secret.txt")
        return open(secret_path).read().strip()

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    print("Flag:", solve(d))
