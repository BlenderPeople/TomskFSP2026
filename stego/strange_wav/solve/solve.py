#!/usr/bin/env python3
"""Разбор WAV «Странный WAV на сервере» (Stegano, 500).

Слои:
  1. QR-код на спектрограмме — даёт пароль к архиву.
  2. ZIP в оверлее после чанка data и его копия в бите 8 16-битных отсчётов.

Зависимости: только стандартная библиотека. Для автоматического чтения QR
нужен opencv-python (cv2); иначе передайте ключ через --key.
"""
from __future__ import annotations

import argparse
import io
import struct
import sys
import wave
import zipfile
from pathlib import Path

FLAG_RE = __import__("re").compile(r"tomskfsp\{[^}]+\}")


def read_wav(path: Path):
    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.getnframes()
        raw = wf.readframes(frames)
    if channels != 1 or width != 2:
        raise SystemExit(f"ожидался mono/16-bit WAV, получено channels={channels}, width={width}")
    samples = struct.unpack("<%dH" % frames, raw)
    return rate, frames, raw, samples


def find_zip(blob: bytes) -> bytes | None:
    start = blob.find(b"PK\x03\x04")
    if start < 0:
        return None
    end = blob.rfind(b"PK\x05\x06")
    if end < 0:
        return None
    end += 22
    if end > len(blob):
        return None
    return blob[start:end]


def extract_overlay(path: Path):
    data = path.read_bytes()
    pos = 12
    while pos + 8 <= len(data):
        chunk_id = data[pos : pos + 4]
        size = struct.unpack("<I", data[pos + 4 : pos + 8])[0]
        body = pos + 8
        if chunk_id == b"data":
            end = body + size
            return data, body, size, data[end:]
        pos = body + size + (size & 1)
    raise SystemExit("в WAV не найден чанк data")


def extract_lsb(samples):
    # Бит 8 — младший бит старшего байта 16-битного отсчёта (little-endian).
    bits = [(sample >> 8) & 1 for sample in samples]
    out = bytearray()
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for bit in bits[i : i + 8]:
            byte = (byte << 1) | bit
        out.append(byte)
    return bytes(out)


def decode_qr(path: Path) -> str | None:
    try:
        import cv2  # type: ignore
    except ImportError:
        return None
    image = cv2.imread(str(path))
    if image is None:
        return None
    data, _, _ = cv2.QRCodeDetector().detectAndDecode(image)
    return data or None


def main() -> int:
    parser = argparse.ArgumentParser(description="Извлечь и расшифровать ZIP из rock_me.wav")
    parser.add_argument("wav", type=Path, help="public/rock_me.wav")
    parser.add_argument("--key", help="строка из QR-кода")
    parser.add_argument("--out", type=Path, default=Path("flag.zip"))
    args = parser.parse_args()

    rate, frames, raw, samples = read_wav(args.wav)
    file_size = args.wav.stat().st_size
    data, data_off, data_len, overlay = extract_overlay(args.wav)
    print(f"[+] RIFF/WAVE: {file_size} байт, {rate} Гц, 1 канал, 16 бит")
    print(f"[+] data: {data_len} байт (с {data_off}); оверлей: {len(overlay)} байт")

    overlay_zip = find_zip(overlay)
    if overlay_zip is None:
        raise SystemExit("в оверлее не найден ZIP")
    print(f"[+] ZIP в оверлее: {len(overlay_zip)} байт, файл {args.wav.name}")

    lsb_zip = find_zip(extract_lsb(samples))
    if lsb_zip is None:
        print("[!] ZIP в LSB не найден")
    else:
        same = "совпадает с оверлеем" if lsb_zip == overlay_zip else "отличается от оверлея"
        print(f"[+] ZIP в LSB (бит 8): {len(lsb_zip)} байт, {same}")

    args.out.write_bytes(overlay_zip)
    archive = zipfile.ZipFile(io.BytesIO(overlay_zip))
    print("[+] Содержимое архива: " + ", ".join(archive.namelist()))

    key = args.key
    if not key:
        qr_path = Path(__file__).resolve().parent.parent / "sources" / "qr_reference_full.png"
        key = decode_qr(qr_path) if qr_path.exists() else None
        if key:
            print(f"[+] Ключ прочитан из QR: {key}")
        else:
            print("[-] Ключ не задан и QR не прочитан. Передайте --key или установите opencv-python")
            return 2

    try:
        payload = archive.read("flag.txt", pwd=key.encode())
    except RuntimeError:
        print("[-] Пароль не подошёл")
        return 1
    print("[+] Пароль подошёл, CRC32 совпал")
    text = payload.decode("utf-8", "replace")
    match = FLAG_RE.search(text)
    if not match:
        print("[-] Флаг не найден в flag.txt")
        return 1
    print(f"[!] Флаг: {match.group(0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
