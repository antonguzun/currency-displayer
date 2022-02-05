FROM python:3.9-alpine3.12

COPY requirements.txt requirements.txt

RUN apk add --no-cache \
        postgresql \
        make \
    && apk add --no-cache --virtual .build-deps \
        python3-dev \
        postgresql-dev \
        build-base \
        libffi-dev \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

RUN mkdir -p /code
COPY migrations /code/migrations
COPY src /code/src
COPY tests /code/test
WORKDIR /code
CMD ["gunicorn", "src.app:app_factory", "--bind", "0.0.0.0:8000", "--workers", "1", "--worker-class", "aiohttp.GunicornUVLoopWebWorker"]
