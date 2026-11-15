#!/usr/bin/env python3
# gen.py — T10: генерирует .key.json с флагом для варианта (сам сервер — общий src/server.py,
# флаг передаётся аргументом при запуске; solve доказывает проходимость автопилотом).
import os, sys, json

def main(outdir, variant, flag):
    os.makedirs(outdir, exist_ok=True)
    with open(f"{outdir}/.key.json", "w") as f:
        json.dump({"flag": flag, "variant": variant}, f)
    # самопроверка: генератор досок выдаёт 50 досок без ошибок
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "deploy", "src")))
    from server import gen_board, BOARD, MINES
    for r in range(1, 51):
        field = gen_board(variant * 10000 + r)
        mines = sum(1 for row in field for v in row if v == 9)
        assert mines == MINES
        assert field[3][3] == 0, f"старт (3,3) не ноль на доске {r}"
    print(f"variant {variant}: 50 boards OK")

if __name__ == "__main__":
    outdir, variant, flag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    main(outdir, variant, flag)
