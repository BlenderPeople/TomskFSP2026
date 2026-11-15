FROM debian:bookworm-slim AS client
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*
COPY deploy/argus_link.c /src/argus_link.c
RUN mkdir -p /out && gcc -O2 -Wall -Wextra -fstack-protector-strong -pie -fPIE -fvisibility=hidden -fno-asynchronous-unwind-tables -fno-unwind-tables -fno-ident -Wl,-z,relro,-z,now -o /out/argus-link /src/argus_link.c && strip /out/argus-link

FROM python:3.12-slim AS server
COPY deploy/server.py /server.py
ENV PORT=23231
CMD ["python", "/server.py"]
