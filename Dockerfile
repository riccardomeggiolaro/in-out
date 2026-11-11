# syntax=docker/dockerfile:1
# ==============================================================
# In-Out - immagine Docker
# - Python + dipendenze (FastAPI, WeasyPrint, pycups, ...)
# - CUPS con driver Epson TM-T e Custom VKP80 / VKP80III
# - cifs-utils per la sync-folder (mount Samba)
# ==============================================================

ARG PYTHON_VERSION=3.12

# ---------- Stage 1: build delle dipendenze Python ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config \
        libcups2-dev libffi-dev libjpeg-dev libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
# pyinstaller/pyarmor servono solo per generare l'eseguibile, non a runtime
RUN grep -viE '^(pyinstaller|pyinstaller-hooks-contrib|pyarmor|altgraph)\b' /tmp/requirements.txt > /tmp/requirements.docker.txt \
    && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /tmp/requirements.docker.txt

# ---------- Stage 2: immagine finale ----------
FROM python:${PYTHON_VERSION}-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    TZ=Europe/Rome \
    IN_OUT_DOCKER=1 \
    IN_OUT_CONFIG_DIR=/etc/in-out

RUN apt-get update && apt-get install -y --no-install-recommends \
        cups cups-client cups-bsd cups-filters libcups2 libcupsimage2 \
        libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libcairo2 \
        libgdk-pixbuf-2.0-0 shared-mime-info fonts-dejavu-core fontconfig \
        libjpeg62-turbo libxml2 libxslt1.1 \
        libtk8.6 \
        cifs-utils iputils-ping tzdata ca-certificates procps tini \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

WORKDIR /opt/in-out

# Driver stampanti (solo amd64)
COPY printers-driver /opt/in-out/printers-driver
RUN set -eux; \
    if [ "$(dpkg --print-architecture)" = "amd64" ]; then \
        cd /opt/in-out/printers-driver/tmt-cups; \
        dpkg -i backend/pcs-3.6.0.0-1.amd64.deb filter/tmt-cups_1.1.0-1_amd64.deb backend/tmt-cups-backend-1.1.0.0-2.amd64.deb; \
        mkdir -p /usr/share/cups/model/EPSON && cp ppd/*.ppd /usr/share/cups/model/EPSON/; \
        for drv in VKP80 VKP80III; do \
            cd "/opt/in-out/printers-driver/${drv}_CUPSDrv-PKG"; \
            bash "${drv}_CUPSDrv.sh" </dev/null || echo "ATTENZIONE: installazione driver ${drv} fallita"; \
        done; \
        rm -rf /tmpDrv; \
    else \
        echo "Architettura non amd64: driver Epson/Custom non installati"; \
    fi

# CUPS: accesso remoto all'interfaccia web (come negli installer nativi)
RUN set -eux; \
    sed -i -e 's/^Listen localhost:631/Port 631/' \
           -e 's/^Browsing .*/Browsing On/' /etc/cups/cupsd.conf; \
    grep -q '^ServerAlias' /etc/cups/cupsd.conf || echo 'ServerAlias *' >> /etc/cups/cupsd.conf; \
    grep -q '^DefaultEncryption' /etc/cups/cupsd.conf || echo 'DefaultEncryption Never' >> /etc/cups/cupsd.conf; \
    awk '/^<Location \/(admin|admin\/conf|admin\/log)?>/{print; print "  Allow all"; next} \
         /^<Location \/>/{print; print "  Allow all"; next} {print}' /etc/cups/cupsd.conf > /tmp/cupsd.conf; \
    mv /tmp/cupsd.conf /etc/cups/cupsd.conf; \
    cp -a /etc/cups /etc/cups.default

# Codice applicativo
COPY . /opt/in-out
RUN rm -rf /opt/in-out/printers-driver \
    && mkdir -p /var/opt/in-out/pdf /var/opt/in-out/csv /var/opt/in-out/images /var/opt/in-out/backup /etc/in-out \
    && cp /opt/in-out/config.json /opt/in-out/config.default.json \
    && chmod +x /opt/in-out/docker/entrypoint.sh

VOLUME ["/etc/in-out", "/var/opt/in-out", "/etc/cups"]

EXPOSE 80 631

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import json,os,urllib.request;c=json.load(open(os.path.join(os.environ['IN_OUT_CONFIG_DIR'],'config.json')));urllib.request.urlopen('http://127.0.0.1:%s/docs'%c['app_api']['port'],timeout=4)" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/opt/in-out/docker/entrypoint.sh"]
CMD ["python", "main.py"]
