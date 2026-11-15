#!/usr/bin/env python3
# gen.py — генератор варианта для omni_forensic_http_auth
# Параметры: <outdir> <variant> <flag>
import os, sys, random, json
from scapy.all import Ether, IP, TCP, UDP, DNS, DNSQR, Raw, wrpcap

def main(outdir, variant, flag):
    random.seed(variant)
    os.makedirs(outdir, exist_ok=True)

    client = "192.168.1.45"
    server = "203.0.113.10"
    sport = 45000 + variant
    dport = 80

    login_data = f"username=admin&password=SuperSecret{variant}&submit=Login"
    http_post = (
        f"POST /login.php HTTP/1.1\r\n"
        f"Host: internal.corp.local\r\n"
        f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
        f"Content-Type: application/x-www-form-urlencoded\r\n"
        f"Content-Length: {len(login_data)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
        f"{login_data}"
    ).encode()

    http_resp_body = (
        f"<html><body><h1>Welcome, admin!</h1>"
        f"<p>Your flag: {flag}</p></body></html>\r\n"
    )
    http_resp = (
        f"HTTP/1.1 200 OK\r\n"
        f"Content-Type: text/html; charset=utf-8\r\n"
        f"Server: Apache/2.4.41 (Ubuntu)\r\n"
        f"Content-Length: {len(http_resp_body)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
        f"{http_resp_body}"
    ).encode()

    c_seq = 1000
    s_seq = 5000
    mac_c = "02:11:22:33:44:55"
    mac_s = "02:66:77:88:99:aa"

    pkts = [
        # Немного фонового DNS-шума
        Ether(src=mac_c, dst=mac_s) / IP(src=client, dst="8.8.8.8") / UDP(sport=53100, dport=53) / DNS(rd=1, qd=DNSQR(qname="internal.corp.local")),
        # TCP 3-way handshake
        Ether(src=mac_c, dst=mac_s) / IP(src=client, dst=server) / TCP(sport=sport, dport=dport, flags="S", seq=c_seq),
        Ether(src=mac_s, dst=mac_c) / IP(src=server, dst=client) / TCP(sport=dport, dport=sport, flags="SA", seq=s_seq, ack=c_seq + 1),
        Ether(src=mac_c, dst=mac_s) / IP(src=client, dst=server) / TCP(sport=sport, dport=dport, flags="A", seq=c_seq + 1, ack=s_seq + 1),
        # HTTP POST /login.php
        Ether(src=mac_c, dst=mac_s) / IP(src=client, dst=server) / TCP(sport=sport, dport=dport, flags="PA", seq=c_seq + 1, ack=s_seq + 1) / Raw(load=http_post),
        # ACK + HTTP 200 OK
        Ether(src=mac_s, dst=mac_c) / IP(src=server, dst=client) / TCP(sport=dport, dport=sport, flags="PA", seq=s_seq + 1, ack=c_seq + 1 + len(http_post)) / Raw(load=http_resp),
        # TCP teardown
        Ether(src=mac_c, dst=mac_s) / IP(src=client, dst=server) / TCP(sport=sport, dport=dport, flags="FA", seq=c_seq + 1 + len(http_post), ack=s_seq + 1 + len(http_resp)),
        Ether(src=mac_s, dst=mac_c) / IP(src=server, dst=client) / TCP(sport=dport, dport=sport, flags="FA", seq=s_seq + 1 + len(http_resp), ack=c_seq + 2 + len(http_post)),
    ]
    t = 1731400000.0
    for p in pkts:
        p.time = t
        t += 0.01

    pcap_path = os.path.join(outdir, "http_auth_challenge.pcap")
    wrpcap(pcap_path, pkts)

    with open(os.path.join(outdir, ".key.json"), "w") as f:
        json.dump({"flag": flag, "login_data": login_data}, f, indent=2)

if __name__ == "__main__":
    outdir, variant, flag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    main(outdir, variant, flag)
    print(f"variant {variant}: omni_forensic_http_auth OK -> {flag}")
