#!/usr/bin/env python3
# gen.py — генератор варианта для omni_reverse_xor
# Параметры: <outdir> <variant> <flag>
import os, sys, random, json, subprocess

def main(outdir, variant, flag):
    random.seed(variant)
    os.makedirs(outdir, exist_ok=True)

    inner = flag.replace("tomskfsp{", "").replace("}", "")
    key = 0x42
    encrypted = bytes(b ^ key for b in inner.encode())

    hex_bytes = ", ".join(f"0x{b:02x}" for b in encrypted)
    c_code = f'''#include <stdio.h>
#include <string.h>

unsigned char secret[] = {{{hex_bytes}}};
const size_t secret_len = sizeof(secret);

int check_password(const char *input) {{
    if (strlen(input) != secret_len) return 0;
    for (size_t i = 0; i < secret_len; i++) {{
        if (((unsigned char)input[i] ^ 0x{key:02x}) != secret[i]) return 0;
    }}
    return 1;
}}

int main(void) {{
    char input[128];
    printf("Enter password: ");
    if (!fgets(input, sizeof(input), stdin)) return 1;
    input[strcspn(input, "\\n")] = 0;
    if (check_password(input)) {{
        printf("Access granted! Flag: tomskfsp{{%s}}\\n", input);
        return 0;
    }}
    printf("Access denied\\n");
    return 1;
}}
'''
    c_path = os.path.join(outdir, "hidden_flag.c")
    bin_path = os.path.join(outdir, "hidden_flag")
    with open(c_path, "w") as f:
        f.write(c_code)

    r = subprocess.run(["gcc", "-O2", "-o", bin_path, c_path], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gcc failed: {r.stderr}")

    with open(os.path.join(outdir, ".key.json"), "w") as f:
        json.dump({"flag": flag, "inner": inner, "key": hex(key), "encrypted": list(encrypted)}, f, indent=2)

if __name__ == "__main__":
    outdir, variant, flag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    main(outdir, variant, flag)
    print(f"variant {variant}: omni_reverse_xor OK -> {flag}")
