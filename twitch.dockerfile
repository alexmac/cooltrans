FROM public.ecr.aws/debian/debian:unstable

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    ca-certificates \
    dumb-init \
    ffmpeg \
    jq \
    python3 \
    python3-pip \
    wget \
    && apt-get clean

RUN python3 -m pip install --break-system-packages -U awscli

WORKDIR /usr/local/alexmac/cooltrans/
COPY twitch.sh ./

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD bash -xe twitch.sh
