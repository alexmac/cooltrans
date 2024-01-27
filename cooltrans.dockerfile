FROM public.ecr.aws/debian/debian:stable

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    ca-certificates \
    dumb-init \
    python3 \
    python3-pip \
    wget \
    && apt-get clean

RUN python3 -m pip install --break-system-packages -U pipenv
EXPOSE 8081

WORKDIR /usr/local/alexmac/cooltrans/
COPY Pipfile* ./
RUN pipenv install

COPY cooltrans ./cooltrans
COPY static ./static
COPY cooltrans_server.py ./

ENV PYTHONPATH=.

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD pipenv run python3 cooltrans_server.py
