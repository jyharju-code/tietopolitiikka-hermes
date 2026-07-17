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

COPY images/hermes/tietopolitiikka_ingest_hook.py /opt/hermes/tietopolitiikka_ingest_hook.py
COPY images/hermes/patch_telegram_adapter.py /tmp/patch_telegram_adapter.py

RUN /opt/hermes/.venv/bin/python /tmp/patch_telegram_adapter.py \
    && rm /tmp/patch_telegram_adapter.py \
    && chown root:root /opt/hermes/tietopolitiikka_ingest_hook.py \
    && chmod 0444 /opt/hermes/tietopolitiikka_ingest_hook.py
