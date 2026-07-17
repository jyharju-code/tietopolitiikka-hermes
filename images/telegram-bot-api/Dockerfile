FROM ubuntu:24.04 AS builder

ARG TELEGRAM_BOT_API_COMMIT=adfd7f6a8e990272851777eeb3ae0def4216f161

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates clang cmake g++ git gperf libc++-dev libc++abi-dev \
       libssl-dev make zlib1g-dev \
    && git clone https://github.com/tdlib/telegram-bot-api.git /src \
    && cd /src \
    && git checkout "${TELEGRAM_BOT_API_COMMIT}" \
    && git submodule update --init --recursive \
    && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local \
    && cmake --build build --target install -j2

FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl libssl3 zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10002 --home /var/lib/telegram-bot-api telegram

COPY --from=builder /usr/local/bin/telegram-bot-api /usr/local/bin/telegram-bot-api

RUN install -d -o telegram -g telegram -m 0700 \
    /var/lib/telegram-bot-api /var/lib/telegram-bot-api/temp

USER telegram
ENTRYPOINT ["/usr/local/bin/telegram-bot-api"]
