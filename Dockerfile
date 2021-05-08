FROM python:3.9.5-alpine

WORKDIR /app

RUN apk add --no-cache --virtual .build-deps gcc libc-dev libxslt-dev && apk add --no-cache libxslt && pip install lxml pyyaml aiohttp && apk del .build-deps

COPY requirements.txt .
RUN pip install -r requirements.txt

ADD main.py .

ENTRYPOINT [ "python", "./main.py" ]
