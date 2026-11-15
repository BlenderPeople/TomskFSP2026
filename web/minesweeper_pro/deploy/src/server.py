#!/usr/bin/env python3
# server.py — T10 (HTTP-версия): «Сапёр-профи», 50 досок 9×9 по 10 мин, 25 с на доску.
#
# Два способа забрать флаг:
#   A) PPC — написать автопилот: propagation нулей + правила подмножеств, 50 досок подряд;
#   B) WEB — счёт приходит от клиента: POST /api/score принимает wins без серверной проверки,
#      после чего GET /api/flag отдаёт флаг. Сапёра решать не нужно.
#
# HTTP API (все ответы — JSON):
#   GET  /                      HTML-страница с полем (клик = открыть клетку)
#   GET  /healthz               {"ok": true}
#   POST /api/session           новая игра; Set-Cookie: sid=...; -> состояние доски 1
#   GET  /api/state             {"round","cells","remaining","time_left","wins"}
#   POST /api/open {"x","y"}    -> {"cells","remaining","round","wins","time_left"[,"cleared"][,"flag"]}
#   POST /api/score {"wins":N}  принимаёт счёт от клиента (см. пометку TODO ниже)
#   GET  /api/flag              флаг при wins >= ROUNDS
#
# cells[y][x]: -1 закрыто, 0..8 цифра. Мины не раскрываются никогда.
import json, os, random, secrets, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BOARD = 9
MINES = 10
ROUNDS = 50
TIME_PER = 25.0
SESSION_TTL = 3600.0

FLAG = "tomskfsp{FLAG}"
VARIANT = 1


def neighbors(x, y):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD and 0 <= ny < BOARD:
                yield nx, ny


def gen_board(seed):
    """Доска с гарантированным нулём в (3,3) и разрешимостью без угадывания.

    Разрешимость проверяется той же логикой, что должен применить участник:
    propagation нулей + правила подмножеств. Не сошлось — новая попытка.
    """
    for attempt in range(200):
        rng = random.Random(seed * 1000 + attempt)
        mines = set()
        while len(mines) < MINES:
            x, y = rng.randrange(BOARD), rng.randrange(BOARD)
            if (x, y) == (3, 3):
                continue
            mines.add((x, y))
        field = [[0] * BOARD for _ in range(BOARD)]
        for x, y in mines:
            field[y][x] = 9
        for y in range(BOARD):
            for x in range(BOARD):
                if field[y][x] == 9:
                    continue
                c = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < BOARD and 0 <= ny < BOARD and field[ny][nx] == 9:
                            c += 1
                field[y][x] = c
        if field[3][3] != 0:
            continue
        opened = [[False] * BOARD for _ in range(BOARD)]
        known_mines = set()
        safe = {(3, 3)}
        progress_total = 0
        ok = True
        while safe:
            x, y = safe.pop()
            if opened[y][x]:
                continue
            if field[y][x] == 9:
                ok = False
                break
            opened[y][x] = True
            progress_total += 1
            if field[y][x] == 0:
                for nx, ny in neighbors(x, y):
                    if not opened[ny][nx]:
                        safe.add((nx, ny))
            for yy in range(BOARD):
                for xx in range(BOARD):
                    v = field[yy][xx]
                    if v <= 0 or not opened[yy][xx]:
                        continue
                    closed = [(a, b) for a, b in neighbors(xx, yy) if not opened[b][a]]
                    fl = [c for c in closed if c in known_mines]
                    unk = [c for c in closed if c not in known_mines]
                    if unk and v - len(fl) == len(unk):
                        known_mines.update(unk)
                    elif unk and v == len(fl):
                        safe.update(unk)
        if ok and progress_total == BOARD * BOARD - MINES:
            return field
    raise RuntimeError("не удалось сгенерировать доску")


class Game:
    """Одна партия: 50 досок, состояние живёт на сервере, cookie — только идентификатор."""

    def __init__(self, variant):
        self.variant = variant
        self.round = 0
        self.wins = 0
        self.field = None
        self.opened = None
        self.deadline = 0.0
        self.dead = False
        self.done = False
        self.lock = threading.Lock()
        self.touched = time.time()
        self.start_round()

    def start_round(self):
        self.round += 1
        self.field = gen_board(self.variant * 10000 + self.round)
        self.opened = [[False] * BOARD for _ in range(BOARD)]
        self.deadline = time.time() + TIME_PER

    def visible(self):
        return [[-1 if not self.opened[y][x] else self.field[y][x]
                 for x in range(BOARD)] for y in range(BOARD)]

    def remaining(self):
        return sum(1 for y in range(BOARD) for x in range(BOARD)
                   if not self.opened[y][x] and self.field[y][x] != 9)

    def state(self, **extra):
        out = {"round": self.round, "cells": self.visible(), "remaining": self.remaining(),
               "time_left": round(max(0.0, self.deadline - time.time()), 2),
               "wins": self.wins, "rounds_total": ROUNDS}
        out.update(extra)
        return out

    def expired(self):
        return time.time() > self.deadline

    def open_cell(self, x, y):
        if self.field[y][x] == 9:
            self.dead = True
            return {"boom": True, "mine": [x, y], "round": self.round, "wins": self.wins}
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if self.opened[cy][cx]:
                continue
            self.opened[cy][cx] = True
            if self.field[cy][cx] == 0:
                for nx, ny in neighbors(cx, cy):
                    if not self.opened[ny][nx]:
                        stack.append((nx, ny))
        if self.remaining() > 0:
            return self.state()
        self.wins += 1
        if self.round >= ROUNDS:
            self.done = True
            return self.state(cleared=True, flag=FLAG)
        self.start_round()
        return self.state(cleared=True)


SESSIONS = {}
SESSIONS_LOCK = threading.Lock()
INDEX_HTML = ""


def get_game(sid):
    with SESSIONS_LOCK:
        g = SESSIONS.get(sid)
    return g


def prune():
    now = time.time()
    with SESSIONS_LOCK:
        for sid in [s for s, g in SESSIONS.items() if now - g.touched > SESSION_TTL]:
            SESSIONS.pop(sid, None)


class Handler(BaseHTTPRequestHandler):
    server_version = "MinesweeperPro/2.0"
    protocol_version = "HTTP/1.1"

    # --- утилиты ---
    def send_json(self, obj, code=200, headers=None):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, text, code=200):
        body = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def sid(self):
        raw = self.headers.get("Cookie", "")
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == "sid":
                return v
        return None

    def body_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # --- маршруты ---
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self.send_html(INDEX_HTML)

        if path == "/healthz":
            return self.send_json({"ok": True})

        if path == "/api/state":
            g = get_game(self.sid())
            if not g:
                return self.send_json({"error": "no session"}, 401)
            with g.lock:
                g.touched = time.time()
                if g.expired() and not g.dead and not g.done:
                    g.dead = True
                return self.send_json(g.state(dead=g.dead, done=g.done))

        if path == "/api/flag":
            g = get_game(self.sid())
            if not g:
                return self.send_json({"error": "no session"}, 401)
            with g.lock:
                if g.wins >= ROUNDS or g.done:
                    return self.send_json({"flag": FLAG, "wins": g.wins})
                return self.send_json({"error": "flag is locked", "wins": g.wins,
                                       "need": ROUNDS}, 403)

        return self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self.body_json()
        if data is None:
            return self.send_json({"error": "bad json"}, 400)
        prune()

        if path == "/api/session":
            variant = int(data.get("variant", VARIANT) or VARIANT)
            sid = secrets.token_urlsafe(16)
            g = Game(variant)
            with SESSIONS_LOCK:
                SESSIONS[sid] = g
            return self.send_json(g.state(), headers={"Set-Cookie": f"sid={sid}; Path=/; HttpOnly"})

        g = get_game(self.sid())
        if not g:
            return self.send_json({"error": "no session"}, 401)

        if path == "/api/open":
            x, y = data.get("x"), data.get("y")
            if not (isinstance(x, int) and isinstance(y, int) and 0 <= x < BOARD and 0 <= y < BOARD):
                return self.send_json({"error": "bad coords"}, 400)
            with g.lock:
                g.touched = time.time()
                if g.dead:
                    return self.send_json({"error": "run is over", "dead": True,
                                           "new_session": "/api/session"}, 409)
                if g.done:
                    return self.send_json(g.state(done=True, flag=FLAG))
                if g.expired():
                    g.dead = True
                    return self.send_json({"timeout": True, "round": g.round,
                                           "new_session": "/api/session"}, 409)
                return self.send_json(g.open_cell(x, y))

        if path == "/api/score":
            # TODO(перед релизом): сверять счёт с пройденными досками на сервере.
            # Пока счёт принимается от клиента — страница синхронизирует его после
            # каждой разминированной доски, чтобы прогресс не терялся при F5.
            try:
                wins = int(data.get("wins", 0))
            except (TypeError, ValueError):
                return self.send_json({"error": "bad wins"}, 400)
            with g.lock:
                g.touched = time.time()
                g.wins = wins
                unlocked = g.wins >= ROUNDS
                return self.send_json({"ok": True, "wins": g.wins,
                                       "flag_unlocked": unlocked})

        return self.send_json({"error": "not found"}, 404)


def load_flag():
    global FLAG, VARIANT
    key_file = os.environ.get("KEY_FILE")
    if os.environ.get("FLAG"):
        FLAG = os.environ["FLAG"]
    elif key_file and os.path.exists(key_file):
        data = json.load(open(key_file, encoding="utf-8"))
        FLAG = data.get("flag", FLAG)
        VARIANT = int(data.get("variant", VARIANT))
    if len(sys.argv) > 2:
        VARIANT = int(sys.argv[2])
    if len(sys.argv) > 3:
        FLAG = sys.argv[3]


def main():
    global INDEX_HTML
    load_flag()
    here = os.path.dirname(os.path.abspath(__file__))
    page = os.path.join(here, "index.html")
    if os.path.exists(page):
        INDEX_HTML = open(page, encoding="utf-8").read()
    else:
        INDEX_HTML = "<h1>Minesweeper Pro</h1><p>index.html не найден</p>"

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", "7777"))
    srv = ThreadingHTTPServer((host, port), Handler)
    srv.daemon_threads = True
    print(f"minesweeper-pro (http) variant={VARIANT} on {host}:{port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()