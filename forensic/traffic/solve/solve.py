#!/usr/bin/env python3
"""Контрольное решение задачи 05 «Захват трафика».

Собираем всех кандидатов на флаг по каналам (DNS TXT, HTTP-заголовки,
JSON, HTML-комментарии, тело POST, чат :1337), классифицируем по контексту
и проверяем: настоящий флаг — только тот, что в HTML-ответе на
GET /faculties/fb (комментарий deploy note); остальные 7 — ловушки.
"""
import re
from pathlib import Path

from scapy.all import DNS, IP, TCP, UDP, rdpcap

PREFIX = "tomskfsp"
FLAG = "tomskfsp{follow_the_tcp_stream}"

HERE = Path(__file__).resolve().parent

CHANNEL_MARKERS = [                      # (маркер рядом с кандидатом, канал)
    ("deploy note", "HTTP 200 GET /faculties/fb (HTML-комментарий страницы)"),
    ("X-Export-Token", "HTTP-заголовок X-Export-Token"),
    ("_cache_hint", "поле JSON _cache_hint"),
    ("nothing here", "HTTP 404 /admin (HTML-комментарий)"),
    ("backup_token", "тело POST /api/feedback"),
]


def classify(context: bytes, stream: str) -> str:
    for marker, label in CHANNEL_MARKERS:
        if marker.encode() in context:
            return label
    return stream


def main() -> int:
    expected = FLAG
    prefix = PREFIX
    pat = re.compile(re.escape(prefix.encode()) + rb"\{[^}\s]+\}")

    pkts = rdpcap(str(HERE.parent / "public" / "traffic.pcap"))

    found = {}                                    # флаг -> канал
    for p in pkts:
        if UDP in p and DNS in p:
            for m in pat.finditer(bytes(p[DNS])):
                found[m.group().decode()] = "DNS TXT-запись"
        elif TCP in p and bytes(p[TCP].payload):
            t = p[TCP]
            stream = f"{p[IP].src}:{t.sport} -> {p[IP].dst}:{t.dport}"
            label = stream
            if t.dport == 1337 or t.sport == 1337:
                label = "TCP :1337 («приватный чат»)"
            data = bytes(t.payload)
            for m in pat.finditer(data):
                ctx = data[max(0, m.start() - 80):m.start()]
                found[m.group().decode()] = classify(ctx, label)

    real_channel = None
    for flag, channel in sorted(found.items(), key=lambda kv: kv[1]):
        mark = "НАСТОЯЩИЙ" if flag == expected else "ловушка"
        print(f"[{mark:8}] {flag:45} <- {channel}")
        if flag == expected:
            real_channel = channel

    traps = len(found) - (1 if expected in found else 0)
    print(f"\nитого кандидатов: {len(found)} (ловушек: {traps})")

    if real_channel != "HTTP 200 GET /faculties/fb (HTML-комментарий страницы)":
        print(f"ОШИБКА: настоящий флаг найден не там, где задумано ({real_channel})")
        return 1
    if traps != 7:
        print(f"ОШИБКА: ожидалось 7 ловушек, найдено {traps}")
        return 1
    print("OK: настоящий флаг совпадает с эталонным FLAG, все ловушки на месте")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
