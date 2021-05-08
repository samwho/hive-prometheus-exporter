FROM python:3.9.5-alpine

WORKDIR /app

COPY requirements.txt .
RUN apk add --no-cache --virtual .build-deps gcc libc-dev libxslt-dev && apk add --no-cache libxslt && pip install -r requirements.txt && apk del .build-deps
ADD main.py .

ENTRYPOINT [ "python", "./main.py" ]
