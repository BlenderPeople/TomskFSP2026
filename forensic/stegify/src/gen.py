#!/usr/bin/env python3
# gen.py — генератор варианта для omni_forensic_stegify
# Параметры: <outdir> <variant> <flag>
import os, sys, random, json, subprocess, tempfile, shutil
from PIL import Image

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
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
                (x * 3 + rng.randrange(40)) % 256,
                (y * 5 + rng.randrange(40)) % 256,
                ((x + y) * 2 + rng.randrange(60)) % 256,
            )
    img.save(path, "JPEG", quality=92)

def main(outdir, variant, flag):
    random.seed(variant)
    os.makedirs(outdir, exist_ok=True)

    inner = flag.replace("tomskfsp{", "").replace("}", "")
    password = "whatareyoudoingthere"
    steghide_pass = "123"

    with tempfile.TemporaryDirectory() as td:
        pass_path = os.path.join(td, "password.txt")
        with open(pass_path, "w") as f:
            f.write(password + "\n")

        jpg_path = os.path.join(td, "steghide_image.jpg")
        make_cover_jpeg(jpg_path, 7000 + variant)
        run(["steghide", "embed", "-cf", jpg_path, "-ef", pass_path, "-p", steghide_pass, "-f", "-q"])

        secret_path = os.path.join(td, "secret.txt")
        with open(secret_path, "w") as f:
            f.write(flag + "\n")

        zip_path = os.path.join(td, "flag.zip")
        run(["zip", "-j", "-q", "-P", password, zip_path, secret_path])

        dl_path = os.path.join(td, "readme.txt")
        with open(dl_path, "w") as f:
            f.write("Personal backup archive. Passphrase stored safely.\n")

        img_path = os.path.join(td, "forensic_image.dd")
        run(["mkfs.ext4", "-q", "-F", "-b", "1024", "-N", "128", img_path, "4096"])
        dbg_cmds = "\n".join([
            "mkdir /Documents",
            "mkdir /Pictures",
            "mkdir /Downloads",
            f"write {zip_path} /Documents/flag.zip",
            f"write {jpg_path} /Pictures/steghide_image.jpg",
            f"write {dl_path} /Downloads/readme.txt",
        ]) + "\n"
        run(["debugfs", "-w", "-f", "-", img_path], input=dbg_cmds)

        shutil.copy(img_path, os.path.join(outdir, "forensic_image.dd"))

    with open(os.path.join(outdir, ".key.json"), "w") as f:
        json.dump({"flag": flag, "inner": inner, "password": password}, f, indent=2)

if __name__ == "__main__":
    outdir, variant, flag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    main(outdir, variant, flag)
    print(f"variant {variant}: omni_forensic_stegify OK -> {flag}")
