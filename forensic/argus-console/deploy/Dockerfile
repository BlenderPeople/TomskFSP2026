FROM debian:bookworm-slim AS build
ARG FLAG
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev python3 && rm -rf /var/lib/apt/lists/*
COPY deploy/argus_auth.c /src/argus_auth.c
COPY deploy/genartifacts.py /genartifacts.py
RUN test -n "${FLAG}" \
    && mkdir -p /out && gcc -O2 -Wall -Wextra -fstack-protector-strong -D_FORTIFY_SOURCE=2 -pie -fPIE -o /out/argus-auth /src/argus_auth.c && strip /out/argus-auth \
    && python3 /genartifacts.py /home/archive/artifacts 120 "${FLAG}" 20181030

FROM python:3.12-slim AS web
RUN pip install --no-cache-dir bcrypt==4.2.1 \
    && apt-get update && apt-get install -y --no-install-recommends \
       tree file less diffutils xxd bsdmainutils binutils gzip tar util-linux \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -u 11000 -M -s /usr/sbin/nologin flagreader \
    && useradd -u 11001 -M -d /home/user -s /bin/bash user
COPY --from=build /out/argus-auth /bin/argus-auth
COPY --from=build /home /home
COPY --from=build /etc/argus /etc/argus
COPY --from=build /var/lib/argus /var/lib/argus
COPY --from=build /var/log/argus /var/log/argus
COPY --from=build /opt/argus /opt/argus
COPY deploy/console.py /app/console.py
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod 700 /app /app/console.py /entrypoint.sh \
    && chown flagreader:flagreader /var/lib/argus/flag /bin/argus-auth \
    && chmod 0400 /var/lib/argus/flag && chmod 4755 /bin/argus-auth \
    && chown -R user:user /home/user \
    && chmod 0755 /home /home/archive /home/user /home/operator-000 /etc/argus /opt/argus /var/lib/argus /var/log/argus \
    && chmod -R a-w /home/archive /home/user /home/operator-000 /etc/argus /opt/argus /var/log/argus \
    && chmod 0555 /home/archive/artifacts \
    && find /home/archive/artifacts -type d -exec chmod 555 {} + \
    && find /home/archive/artifacts -type f -exec chmod 444 {} + \
    && chmod 0444 /etc/argus/archive.conf /opt/argus/manifest.txt /var/log/argus/restore.log \
    && chown root:root /home /home/archive /home/operator-000 /etc/argus /opt/argus /var/lib/argus /var/log/argus
USER root
ENV PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin
ENTRYPOINT ["/entrypoint.sh"]

FROM python:3.12-slim AS edge
COPY deploy/edge.py /app/edge.py
USER 11002:11002
ENTRYPOINT ["python3", "/app/edge.py"]
