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

# Hugo builds the tietopolitiikka test site. It belongs in the image rather
# than downloaded onto the data volume at runtime: a volume copy is invisible
# to a fresh deployment, pins no version anywhere in source, and would have to
# live in an agent-writable directory. Putting that directory on PATH would let
# anything able to write there shadow curl, git or python3, which is a poor
# trade for an agent that reads untrusted documents all day. /usr/local/bin is
# root owned and already on PATH for both login and non-login shells.
ARG HUGO_VERSION=0.164.0
RUN curl -fsSL -o /tmp/hugo.tar.gz \
      "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz" \
    && tar -xzf /tmp/hugo.tar.gz -C /usr/local/bin hugo \
    && rm /tmp/hugo.tar.gz \
    && chown root:root /usr/local/bin/hugo \
    && chmod 0755 /usr/local/bin/hugo \
    && hugo version

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

# Wrangler publishes the draft site. Pinned and installed into the image for
# the same reason as Hugo: an npx download at publish time resolves whatever
# version happens to be current, and would land in a directory the agent can
# write.
ARG WRANGLER_VERSION=4.112.0
RUN npm install -g --no-fund --no-audit "wrangler@${WRANGLER_VERSION}" \
    && npm cache clean --force \
    && wrangler --version

# The agent's publish path. Root owned so the agent can run it but not change
# which project it targets.
COPY images/hermes/publish-site /usr/local/bin/publish-site
RUN chown root:root /usr/local/bin/publish-site \
    && chmod 0755 /usr/local/bin/publish-site \
    && bash -n /usr/local/bin/publish-site

COPY images/hermes/tietopolitiikka_ingest_hook.py /opt/hermes/tietopolitiikka_ingest_hook.py
COPY images/hermes/patch_telegram_adapter.py /tmp/patch_telegram_adapter.py
COPY images/hermes/patch_openviking_resource_tool.py /tmp/patch_openviking_resource_tool.py

RUN /opt/hermes/.venv/bin/python /tmp/patch_telegram_adapter.py \
    && /opt/hermes/.venv/bin/python /tmp/patch_openviking_resource_tool.py \
    && rm /tmp/patch_telegram_adapter.py /tmp/patch_openviking_resource_tool.py \
    && chown root:root /opt/hermes/tietopolitiikka_ingest_hook.py \
    && chmod 0444 /opt/hermes/tietopolitiikka_ingest_hook.py
