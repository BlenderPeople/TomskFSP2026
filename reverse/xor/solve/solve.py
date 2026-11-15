#!/usr/bin/env python3
# solve.py — авторское решение для omni_reverse_xor (разбор ELF64 секции данных)
import os, sys, struct

def extract_secret_from_elf(elf_bytes):
    if elf_bytes[:4] != b"\x7fELF" or elf_bytes[4] != 2 or elf_bytes[5] != 1:
        raise ValueError("Ожидается 64-bit little-endian ELF")
    e_shoff = struct.unpack_from("<Q", elf_bytes, 40)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", elf_bytes, 58)

    sections = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh = struct.unpack_from("<IIQQQQIIQQ", elf_bytes, off)
        sections.append({
            "name_off": sh[0], "type": sh[1], "flags": sh[2],
            "addr": sh[3], "offset": sh[4], "size": sh[5],
            "link": sh[6], "entsize": sh[9],
        })

    for sec in sections:
        if sec["type"] == 2:  # SHT_SYMTAB
            strtab = sections[sec["link"]]
            strs = elf_bytes[strtab["offset"]:strtab["offset"] + strtab["size"]]
            entsize = sec["entsize"] or 24
            count = sec["size"] // entsize
            for i in range(count):
                soff = sec["offset"] + i * entsize
                st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack_from("<IBBHQQ", elf_bytes, soff)
                end = strs.find(b"\x00", st_name)
                name = strs[st_name:end].decode("ascii", errors="replace")
                if name == "secret" and st_shndx < len(sections):
                    target_sec = sections[st_shndx]
                    file_off = target_sec["offset"] + (st_value - target_sec["addr"])
                    return elf_bytes[file_off:file_off + st_size]
    raise ValueError("Символ secret не найден в ELF")

def solve(taskdir):
    bin_path = os.path.join(taskdir, "hidden_flag")
    elf_bytes = open(bin_path, "rb").read()
    encrypted = extract_secret_from_elf(elf_bytes)
    key = 0x42
    decrypted = bytes(b ^ key for b in encrypted).decode()
    return f"tomskfsp{{{decrypted}}}"

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    print("Flag:", solve(d))
