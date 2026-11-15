#!/usr/bin/env python3
# solve.py — авторское решение T7: извлечение флага из covert channel.
# Основной канал — DNS: QNAME вида c<idx>.<hex-chunk>.exfil.example.com.
# Дополнительные каналы (если основной «подрезали») — ICMP id/seq и TCP sport.
import sys, os, json
from scapy.all import rdpcap, DNS, DNSQR, ICMP, TCP, IP

def solve_dns(pkts):
    chunks = {}
    for p in pkts:
        if p.haslayer(DNS) and p[DNS].qr == 0 and p.haslayer(DNSQR):
            qn = p[DNSQR].qname.decode()
            if qn.endswith("exfil.example.com."):
                parts = qn.split(".")
                chunks[int(parts[0][1:])] = bytes.fromhex(parts[1])
    if not chunks:
        return None
    return b"".join(chunks[k] for k in sorted(chunks)).decode().rstrip("\x00")

def solve_icmp(pkts):
    data = {}
    for p in pkts:
        if p.haslayer(ICMP) and p[ICMP].type == 8 and p[IP].src == "10.66.13.37":
            data[p[ICMP].id >> 8] = bytes([p[ICMP].id & 0xFF, p[ICMP].seq & 0xFF])
    if not data:
        return None
    return b"".join(data[k] for k in sorted(data)).decode().rstrip("\x00")

def solve_tcp(pkts):
    data = {}
    for p in pkts:
        if p.haslayer(TCP) and p[IP].src == "10.66.13.37" and int(p[TCP].flags) == 0x02:
            sport = p[TCP].sport
            data[sport & 0xFF] = (sport >> 8) & 0xFF
    if not data:
        return None
    return bytes(data[k] for k in sorted(data)).decode().rstrip("\x00")

def main(taskdir):
    pkts = rdpcap(os.path.join(taskdir, "capture.pcap"))
    results = []
    for name, fn in (("DNS", solve_dns), ("ICMP", solve_icmp), ("TCP", solve_tcp)):
        f = fn(pkts)
        if f:
            results.append((name, f))
            print(f"[{name}] {f}")
    assert results, "ни один канал не дал флага"
    flags = {f for _, f in results}
    assert len(flags) == 1, f"каналы противоречат друг другу: {flags}"
    flag = flags.pop()
    assert flag.startswith("tomskfsp{")
    print("[+] Flag:", flag)
    return flag

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
