FROM public.ecr.aws/docker/library/debian:unstable-slim

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    ca-certificates \
    dumb-init \
    ffmpeg \
    python3 \
    python3-venv \
    wget \
    && apt-get clean

RUN wget -qO- https://astral.sh/uv/install.sh | sh
RUN mv /root/.local/bin/uv* /usr/local/bin/
EXPOSE 8081

WORKDIR /usr/local/alexmac/cooltrans/
COPY pyproject.toml* ./
RUN uv venv && uv sync

COPY cooltrans ./cooltrans
COPY static ./static
COPY cooltrans_server.py ./

ENV PYTHONPATH=.

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD uv run cooltrans_server.py
