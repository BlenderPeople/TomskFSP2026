---
title: "Захват трафика"
category: forensics
difficulty: medium
points: 200
flag_format: "tomskfsp{...}"
---

# Захват трафика

## Суть задачи

Дамп построен вокруг реального запроса к расписанию ТУСУР — `GET /faculties/fb`
(Host: timetable.tusur.ru), страница вшита по фактическому содержимому (список
групп ФБ по курсам, подвал на пр. Ленина, 40). Вокруг него расставлены 7 ловушек.
Два навыка: собрать TCP-потоки целиком и **валидировать кандидатов по источнику** —
настоящий флаг лежит в содержимом, отданном самим сайтом, ловушки — в служебных
полях и посторонних каналах.

## Решение

### Шаг 1: разведка запросов

```bash
tshark -r traffic.pcap -Y http -T fields -e http.request.method -e http.request.uri
# GET /faculties/fb
# GET /api/groups?faculty=fb
# GET /admin
# POST /api/feedback
```

### Шаг 2: собрать HTTP-поток целиком

```bash
tshark -r traffic.pcap -q -z follow,tcp,ascii,0
```

В одном keep-alive-соединении — четыре обмена. На странице `/faculties/fb`
видим HTML-комментарий перед подвалом:

```html
<!-- deploy note (do not remove): tomskfsp{...} -->
<!-- backup moved to api: /api/groups?faculty=fb -->
```

### Шаг 3: не забыть DNS и «приватный» канал

```bash
tshark -r traffic.pcap -Y "dns && dns.txt" -T fields -e dns.qry.name -e dns.txt
tshark -r traffic.pcap -q -z follow,tcp,ascii,1     # чат на :1337
```

### Шаг 4: валидация кандидатов

Всего в дампе 8 строк `tomskfsp{...}`:

| Кандидат | Канал | Вердикт |
|---|---|---|
| `tomskfsp{txt_backup_service_2026}` | DNS TXT `_export.timetable.tusur.ru` | ловушка: DNS-метаданные |
| `tomskfsp{export_session_hdr}` | заголовок `X-Export-Token` в ответе API | ловушка: заголовок, не контент |
| `tomskfsp{cache_hint_v2}` | поле JSON `_cache_hint` | ловушка: служебное поле |
| `tomskfsp{admin_panel_backup}` | комментарий в ответе `404 /admin` | ловушка: приманка для брута путей |
| `tomskfsp{temp_token_2026}` | поле `backup_token` в теле POST | ловушка: ввод пользователя |
| `tomskfsp{private_chat_only}` | TCP :1337 | ловушка: посторонний канал |
| `tomskfsp{new_flag_for_lab5}` | TCP :1337 | ловушка: посторонний канал |
| `tomskfsp{follow_the_tcp_stream}` | HTML-комментарий `deploy note` в ответе на `GET /faculties/fb` | **настоящий** |

Критерий: настоящий флаг — тот, что сайт сам отдаёт как **содержимое** своей
главной страницы (200 OK на основной запрос); остальное лежит в метаданных
(TXT, заголовки), служебных полях или вообще не в HTTP.

> **Флаг:** `tomskfsp{follow_the_tcp_stream}`

## Для преподавателя: автосбор кандидатов

`solve/solve.py` собирает всех кандидатов по каналам (scapy), классифицирует
по контексту и проверяет, что настоящий — именно в ответе на `/faculties/fb`,
а ловушек ровно 7.

## Вывод для студентов

TCP — это разговор, а не отдельные пакеты: смысл живёт в потоке. И второе:
похожих на флаг строк может быть много — источник решает. Заголовки, TXT-записи,
JSON-поля и «приватные чаты» — удобные места для приманок; контент, отданный
самим приложением на основной запрос, — то, что проверяем в первую очередь.
