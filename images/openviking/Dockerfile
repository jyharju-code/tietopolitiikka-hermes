FROM python:3.12-slim-bookworm

ARG OPENVIKING_VERSION=0.4.10

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       gettext-base \
       git \
       libmagic1 \
       poppler-utils \
       tesseract-ocr \
       tesseract-ocr-fin \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "openviking==${OPENVIKING_VERSION}"

COPY images/openviking/entrypoint.sh /usr/local/bin/openviking-entrypoint

RUN chmod 0755 /usr/local/bin/openviking-entrypoint \
    && useradd --create-home --uid 10001 openviking \
    && mkdir -p /data /run/openviking \
    && chown -R openviking:openviking /data /run/openviking

USER openviking
WORKDIR /data

ENTRYPOINT ["/usr/local/bin/openviking-entrypoint"]
CMD ["openviking-server", "--host", "0.0.0.0", "--port", "1933", "--config", "/run/openviking/ov.conf"]
