#!/usr/bin/env python3
# gen.py — T8: ext4-образ без монтирования.
# Внутри образа:
#   /home/analyst/notes.txt          — живой файл с «логами» (подсказка про sqlite)
#   /home/analyst/app.db             — живая SQLite-база: таблица events, мусорные записи
#   /home/analyst/deleted_secret.txt — СОЗДАЁТСЯ и УДАЛЯЕТСЯ (флаг) — дампится debugfs из
#                                      свободных блоков... Надёжнее: кладём файл, потом
#                                      удаляем через debugfs unlink (inode остаётся в journal).
# Практичный вариант: файл с флагом кладём, снимаем «слепок» (raw копия блоков файла через
# debugfs dump в байты), удаляем, но В SQLite WAL оставляем копию флага в остаточных данных.
# Событие в app.db: INSERT с'письмо' — но в WAL-файле остаётся *полностью* страница с флагом.
# Итог: solve через debugfs rdump + strings по WAL.
import os, sys, json, subprocess, sqlite3, shutil, tempfile

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd} failed: {r.stderr[:300]}")
    return r.stdout

def main(outdir, variant, flag):
    os.makedirs(outdir, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        fsimg = os.path.join(td, "fs.img")
        # 1) создать ext4 образ 32 МБ
        run(["mkfs.ext4", "-q", "-F", "-b", "1024", "-N", "128", fsimg, "32768"])
        # 2) заполнить через debugfs (без монтирования — не нужен root!)
        def dbg(*args):
            return run(["debugfs", "-w", "-f", "-", fsimg], input="\n".join(args) + "\n")
        dbg("mkdir /home", "cd /home", "mkdir analyst")
        home = "/home/analyst"
        notes = ("=== Analyst journal ===\n"
                 "Смена 04-06: аномалий нет.\n"
                 "Смена 07-11: подозрительный процесс appd; БД в app.db.\n"
                 "Примечание: срочно удалить deleted_secret.txt (чувствительное).\n")
        npath = os.path.join(td, "notes.txt")
        with open(npath, "w") as f:
            f.write(notes)
        # 3) sqlite база: events + таблица messages с флагом, потом WAL-файл с "удалённой" страницей
        dbpath = os.path.join(td, "app.db")
        walpath = dbpath + "-wal"
        con = sqlite3.connect(dbpath)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("CREATE TABLE events(id INTEGER PRIMARY KEY, ts TEXT, msg TEXT)")
        for i in range(40):
            con.execute("INSERT INTO events(ts,msg) VALUES (?,?)",
                        (f"2026-11-{(i%28)+1:02d} 1{i%10}:{i%60:02d}", f"routine check #{i} ok"))
        con.commit()
        # «удалённая» запись: вставили флаг, закоммитили в WAL, удалили, checkpoint не обязателен
        con.execute("INSERT INTO events(ts,msg) VALUES ('2026-11-12 03:14', ?)", (flag,))
        con.commit()
        con.execute("DELETE FROM events WHERE ts='2026-11-12 03:14'")
        con.commit()
        # ВАЖНО: не делаем wal_checkpoint(TRUNCATE) — тогда флаг остаётся в app.db-wal
        # но close() может чекпоинтить; скопируем db+wal ДО close
        shutil.copy(dbpath, os.path.join(td, "app_copy.db"))
        if os.path.exists(walpath):
            shutil.copy(walpath, os.path.join(td, "app_copy.db-wal"))
        con.close()
        # проверяем, что флаг остался в WAL-копии
        wal_data = open(os.path.join(td, "app_copy.db-wal"), "rb").read()
        assert flag.encode() in wal_data, "флаг не остался в WAL"
        # 4) deleted_secret.txt: создаём, дампим содержимое, удаляем запись из директории
        dpath = os.path.join(td, "deleted_secret.txt")
        with open(dpath, "w") as f:
            f.write(flag + "\n")
        # копия содержимого для самопроверки "остаточных данных"
        del_content = open(dpath, "rb").read()
        # 5) заливаем файлы в образ через debugfs write
        dbg("cd " + home,
            f"write {npath} notes.txt",
            f"write {os.path.join(td, 'app_copy.db')} app.db",
            f"write {os.path.join(td, 'app_copy.db-wal')} app.db-wal",
            f"write {dpath} deleted_secret.txt")
        # 6) удаляем deleted_secret.txt (unlink) — блоки остаются свободными
        dbg("cd " + home, "rm deleted_secret.txt")
        # 7) самопроверка: dump живых файлов (dump требует файловый путь, не /dev/stdout)
        out_notes = os.path.join(td, "notes_out.txt")
        run(["debugfs", "-R", f"dump {home}/notes.txt {out_notes}", fsimg], input="")
        assert "appd" in open(out_notes).read()
        # 8) кладём образ в outdir
        shutil.copy(fsimg, os.path.join(outdir, "disk.img"))
    with open(f"{outdir}/.key.json", "w") as f:
        json.dump({"flag": flag}, f)
    # финальная проверка: флаг находим и в WAL-страницах образа, и в свободных блоках
    raw = open(f"{outdir}/disk.img", "rb").read()
    assert flag.encode() in raw, "флаг не найден в raw образе"
    print(f"variant {variant}: OK, flag present in image (WAL + freespace)")

if __name__ == "__main__":
    outdir, variant, flag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    main(outdir, variant, flag)
