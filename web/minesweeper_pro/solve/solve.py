#!/usr/bin/env python3
"""Авторское решение для «Minesweeper Pro» (HTTP-версия).

Поддерживает два режима:
  --mode ppc (по умолчанию): честный автопилот (50 досок через /api/session и /api/open)
  --mode web: эксплуатация клиентского доверия (POST /api/score -> GET /api/flag)
"""
import argparse
import http.cookiejar
import json
import time
import urllib.request

BOARD = 9


def neighbors(x, y):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD and 0 <= ny < BOARD:
                yield nx, ny


class Client:
    def __init__(self, base_url):
        self.base = base_url.rstrip("/")
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj)
        )

    def req(self, path, data=None):
        body = json.dumps(data).encode() if data is not None else None
        headers = {"Content-Type": "application/json"} if data is not None else {}
        r = urllib.request.Request(self.base + path, data=body, headers=headers)
        with self.opener.open(r, timeout=15) as resp:
            return json.loads(resp.read().decode())


def solve_web(base_url):
    c = Client(base_url)
    c.req("/api/session", {"variant": 1})
    res = c.req("/api/score", {"wins": 50})
    assert res.get("flag_unlocked"), res
    flag_resp = c.req("/api/flag")
    return flag_resp["flag"], flag_resp.get("wins", 50)


def solve_ppc(base_url):
    c = Client(base_url)
    state = c.req("/api/session", {"variant": 1})
    flag = None
    rounds_done = 0

    while flag is None:
        rounds_done = state["round"]
        visible = state["cells"]
        known_mines = set()
        safe = {(3, 3)}
        deadline = time.time() + state.get("time_left", 25)

        while True:
            if time.time() > deadline:
                raise RuntimeError(f"timeout on board {rounds_done}")

            changed = True
            while changed:
                changed = False
                for yy in range(BOARD):
                    for xx in range(BOARD):
                        v = visible[yy][xx]
                        if v <= 0:
                            continue
                        closed = [
                            (nx2, ny2)
                            for nx2, ny2 in neighbors(xx, yy)
                            if visible[ny2][nx2] == -1
                        ]
                        flags_here = [p for p in closed if p in known_mines]
                        unknown = [p for p in closed if p not in known_mines]
                        if unknown and v - len(flags_here) == len(unknown):
                            if set(unknown) - known_mines:
                                known_mines.update(unknown)
                                changed = True
                        elif unknown and v == len(flags_here):
                            if set(unknown) - safe:
                                safe.update(unknown)
                                changed = True

            if not safe:
                best, best_risk = None, 2.0
                for yy in range(BOARD):
                    for xx in range(BOARD):
                        if visible[yy][xx] == -1 and (xx, yy) not in known_mines:
                            risk_sum, cnt = 0.0, 0
                            for nx2, ny2 in neighbors(xx, yy):
                                v = visible[ny2][nx2]
                                if v > 0:
                                    closed = [
                                        (a, b)
                                        for a, b in neighbors(nx2, ny2)
                                        if visible[b][a] == -1
                                    ]
                                    fl = len([p for p in closed if p in known_mines])
                                    unk = len(closed) - fl
                                    if unk > 0:
                                        risk_sum += max(0, v - fl) / unk
                                        cnt += 1
                            risk = risk_sum / cnt if cnt else 0.5
                            if risk < best_risk:
                                best, best_risk = (xx, yy), risk
                assert best, "no moves left"
                safe.add(best)

            x, y = safe.pop()
            if visible[y][x] != -1:
                continue

            resp = c.req("/api/open", {"x": x, "y": y})
            if resp.get("boom"):
                raise RuntimeError(f"boom on board {rounds_done}: {resp}")
            if resp.get("timeout"):
                raise RuntimeError(f"timeout on board {rounds_done}")

            if "flag" in resp:
                flag = resp["flag"]
                break

            visible = resp["cells"]
            if resp.get("cleared"):
                state = resp
                break

    return flag, rounds_done


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("url", nargs="?", default="http://127.0.0.1:7777")
    p.add_argument("--mode", choices=("web", "ppc"), default="web")
    args = p.parse_args()

    flag, rounds = (
        solve_web(args.url) if args.mode == "web" else solve_ppc(args.url)
    )
    print(f"[+] {rounds} досок пройдено ({args.mode})")
    print("[+] Flag:", flag)
