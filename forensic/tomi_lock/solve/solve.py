#!/usr/bin/env python3
"""Сборка ZIP из ICMP-туннеля в дампе «Шлюз Томи».

Задание: Forensics, 250 баллов. Зависимостей нет — только стандартная библиотека.
"""
from __future__ import annotations

import argparse
import io
import re
import struct
import sys
import zipfile
from pathlib import Path

TARGET = "195.208.10.42"
FLAG_RE = re.compile(r"tomskfsp\{[^}]+\}")


def read_pcap(path: Path):
    """Читает классический pcap (linktype Ethernet) и возвращает список пакетов."""
    data = path.read_bytes()
    if len(data) < 24:
        raise ValueError("файл короче заголовка pcap")
    magic = data[:4]
    if magic == b"\xd4\xc3\xb2\xa1":
        endian = "<"
    elif magic == b"\xa1\xb2\xc3\xd4":
        endian = ">"
    else:
        raise ValueError(f"неизвестная сигнатура pcap: {magic.hex()}")
    linktype = struct.unpack(endian + "I", data[20:24])[0]
    if linktype != 1:
        raise ValueError(f"ожидался Ethernet (linktype=1), получено {linktype}")

    packets = []
    offset = 24
    while offset + 16 <= len(data):
        _, _, incl_len, _ = struct.unpack(endian + "IIII", data[offset : offset + 16])
        offset += 16
        frame = data[offset : offset + incl_len]
        offset += incl_len
        if len(frame) < 34 or frame[12:14] != b"\x08\x00":
            continue
        ihl = (frame[14] & 0x0F) * 4
        if ihl < 20 or len(frame) < 14 + ihl + 8:
            continue
        if frame[23] != 1:  # ICMP
            continue
        ip = frame[14 : 14 + ihl]
        src = ".".join(map(str, ip[12:16]))
        dst = ".".join(map(str, ip[16:20]))
        icmp = frame[14 + ihl :]
        icmp_type = icmp[0]
        seq = struct.unpack(">H", icmp[6:8])[0]
        packets.append(
            {"src": src, "dst": dst, "type": icmp_type, "seq": seq, "payload": icmp[8:]}
        )
    return packets


def build_zip(packets):
    selected = [p for p in packets if p["dst"] == TARGET and p["type"] == 8]
    if not selected:
        raise SystemExit(f"не найдено ни одного echo-request на {TARGET}")

    arrival = [p["seq"] for p in selected]
    ordered = sorted(selected, key=lambda p: p["seq"])
    blob = b"".join(p["payload"] for p in ordered)
    if not blob.startswith(b"PK\x03\x04"):
        raise SystemExit("склеенные данные не начинаются с сигнатуры ZIP")

    try:
        archive = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile as exc:
        raise SystemExit(f"не удалось открыть ZIP: {exc}") from exc
    return selected, arrival, ordered, blob, archive


def main() -> int:
    parser = argparse.ArgumentParser(description="Извлечь ZIP из ICMP-туннеля")
    parser.add_argument("pcap", type=Path, help="дамп tomsk_traffic.pcap")
    parser.add_argument("-o", "--out", type=Path, default=Path("leaked.zip"))
    parser.add_argument("--flag", action="store_true", help="найти и напечатать флаг")
    args = parser.parse_args()

    packets = read_pcap(args.pcap)
    selected, arrival, ordered, blob, archive = build_zip(packets)

    print(f"[+] ICMP-пакетов в дампе: {len(packets)}")
    print(f"[+] Исходящих echo-request на {TARGET}: {len(selected)}")
    print("[+] Порядок прихода seq: " + ", ".join(map(str, arrival)))
    inversions = [
        (a, b)
        for a, b in zip(arrival, arrival[1:])
        if b < a
    ]
    for a, b in inversions:
        print(f"[!] seq={a} пришёл раньше seq={b} — сортируем по icmp.seq")
    sizes = sorted({len(p["payload"]) for p in selected})
    print(f"[+] Размеры блоков: {', '.join(map(str, sizes))} байт; всего {len(blob)} байт")

    args.out.write_bytes(blob)
    print(f"[+] Архив собран: {args.out} ({len(blob)} байт)")
    print("[+] Файлы: " + ", ".join(archive.namelist()))

    if args.flag:
        for name in archive.namelist():
            text = archive.read(name).decode("utf-8", "replace")
            match = FLAG_RE.search(text)
            if match:
                print(f"[!] Флаг: {match.group(0)}")
                return 0
        print("[-] Флаг в архиве не найден", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
