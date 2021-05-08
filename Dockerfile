FROM python:3.9.5-alpine

WORKDIR /app

RUN apk add --no-cache --virtual .build-deps gcc libc-dev libxslt-dev && apk add --no-cache libxslt

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN apk del .build-deps

ADD main.py .

ENTRYPOINT [ "python", "./main.py" ]
