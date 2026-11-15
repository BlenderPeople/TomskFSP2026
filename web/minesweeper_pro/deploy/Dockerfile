FROM python:3.12-slim

RUN useradd --create-home --shell /usr/sbin/nologin ctf

WORKDIR /app

COPY src/server.py /app/server.py
COPY src/index.html /app/index.html
COPY task_1/.key.json /app/.key.json

USER ctf

ENV HOST=0.0.0.0 \
    PORT=7777 \
    KEY_FILE=/app/.key.json \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 7777

HEALTHCHECK --interval=10s --timeout=3s --start-period=3s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('127.0.0.1', 7777), 2); s.close()" || exit 1

CMD ["python", "-u", "/app/server.py"]
