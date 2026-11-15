#!/usr/bin/env python3
# gen.py — генератор варианта для omni_misc_atbash
# Параметры: <outdir> <variant> <flag>
import os, sys, zipfile, random, json, subprocess, tempfile, shutil
from PIL import Image

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

def make_cover_jpeg(path, seed, size=(640, 480)):
    rng = random.Random(seed)
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(size[1]):
        for x in range(size[0]):
            px[x, y] = (
                (x * 7 + rng.randrange(50)) % 256,
                (y * 3 + rng.randrange(50)) % 256,
                ((x ^ y) + rng.randrange(60)) % 256,
            )
    img.save(path, "JPEG", quality=92)

def main(outdir, variant, flag):
    random.seed(variant)
    os.makedirs(outdir, exist_ok=True)

    inner = flag.replace("tomskfsp{", "").replace("}", "")
    encrypted = atbash(inner)
    zip_pass = f"m1rr0r_key_{variant}"
    steghide_pass = "718"

    with tempfile.TemporaryDirectory() as td:
        cipher_path = os.path.join(td, "cipher.txt")
        with open(cipher_path, "w") as f:
            f.write(encrypted + "\n")

        pass_path = os.path.join(td, "password.txt")
        with open(pass_path, "w") as f:
            f.write(zip_pass + "\n")

        jpg_path = os.path.join(td, "image.jpg")
        make_cover_jpeg(jpg_path, 8000 + variant)
        run(["steghide", "embed", "-cf", jpg_path, "-ef", pass_path, "-p", steghide_pass, "-f", "-q"])

        flag_zip = os.path.join(td, "flag.zip")
        run(["zip", "-j", "-q", "-P", zip_pass, flag_zip, cipher_path])

        task_zip = os.path.join(td, "task.zip")
        with zipfile.ZipFile(task_zip, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(jpg_path, "image.jpg")
            z.write(flag_zip, "flag.zip")

        shutil.copy(task_zip, os.path.join(outdir, "task.zip"))

    with open(os.path.join(outdir, ".key.json"), "w") as f:
        json.dump({"flag": flag, "inner": inner, "atbash_encrypted": encrypted, "zip_password": zip_pass}, f, indent=2)

if __name__ == "__main__":
    outdir, variant, flag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    main(outdir, variant, flag)
    print(f"variant {variant}: omni_misc_atbash OK -> {flag}")
