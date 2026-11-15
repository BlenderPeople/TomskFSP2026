#!/usr/bin/env python3
# solve.py — авторское решение для omni_forensic_http_auth
import os, sys, re
from scapy.all import *

def solve(taskdir):
    pcap_path = os.path.join(taskdir, "http_auth_challenge.pcap")
    packets = rdpcap(pcap_path)
    
    for pkt in packets:
        if pkt.haslayer(Raw):
            load = pkt[Raw].load.decode('latin-1', errors='replace')
            if 'tomskfsp{' in load:
                match = re.search(r'tomskfsp\{[^}]+\}', load)
                if match:
                    return match.group(0)
    
    raise ValueError("Флаг не найден в pcap")

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    print("Flag:", solve(d))
