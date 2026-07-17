ARG HERMES_BASE_IMAGE
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
COPY images/hermes/patch_whatsapp_adapter.py /tmp/patch_whatsapp_adapter.py

RUN /opt/hermes/.venv/bin/python /tmp/patch_whatsapp_adapter.py \
    && rm /tmp/patch_whatsapp_adapter.py \
    && chown root:root /opt/hermes/tietopolitiikka_ingest_hook.py \
    && chmod 0444 /opt/hermes/tietopolitiikka_ingest_hook.py
