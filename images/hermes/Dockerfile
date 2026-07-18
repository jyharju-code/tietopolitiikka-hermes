ARG HERMES_BASE_IMAGE=nousresearch/hermes-agent@sha256:62ba776214e3df3d4c2b8ed21cc857fbaa918f6dc07089a528553bc26af300c0
FROM ${HERMES_BASE_IMAGE}

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       poppler-utils \
       tesseract-ocr \
       tesseract-ocr-fin \
    && rm -rf /var/lib/apt/lists/* \
    && uv pip install --python /opt/hermes/.venv/bin/python \
       beautifulsoup4 \
       openpyxl \
       pypdf \
       pytesseract \
       python-docx \
       python-pptx

# The agent's terminal tool runs commands through a login shell, and a login
# shell resets PATH to the system default. That hides /opt/hermes/.venv, so
# `python3` resolves to /usr/bin/python3 and every document library installed
# above becomes invisible. It surfaces as ModuleNotFoundError the moment the
# agent tries to read an attachment it was just asked about. Put the
# virtualenv back on PATH for login shells so the interpreter is the same one
# whichever way a command is spawned.
RUN install -d -m 0755 /etc/profile.d \
    && printf 'PATH=/opt/hermes/.venv/bin:$PATH\nexport PATH\n' > /etc/profile.d/10-hermes-venv.sh \
    && chmod 0644 /etc/profile.d/10-hermes-venv.sh

COPY images/hermes/tietopolitiikka_ingest_hook.py /opt/hermes/tietopolitiikka_ingest_hook.py
COPY images/hermes/patch_telegram_adapter.py /tmp/patch_telegram_adapter.py
COPY images/hermes/patch_openviking_resource_tool.py /tmp/patch_openviking_resource_tool.py

RUN /opt/hermes/.venv/bin/python /tmp/patch_telegram_adapter.py \
    && /opt/hermes/.venv/bin/python /tmp/patch_openviking_resource_tool.py \
    && rm /tmp/patch_telegram_adapter.py /tmp/patch_openviking_resource_tool.py \
    && chown root:root /opt/hermes/tietopolitiikka_ingest_hook.py \
    && chmod 0444 /opt/hermes/tietopolitiikka_ingest_hook.py
