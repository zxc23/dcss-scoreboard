FROM python:3.6-alpine

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY requirements-postgres.txt requirements-postgres.txt
# libpq & rsync remain installed -- everything else is just for building psycopg2
RUN apk add --no-cache libpq rsync postgresql-dev gcc python3-dev musl-dev \
  && pip3 install -r requirements-postgres.txt \
  && apk del postgresql-dev gcc python3-dev musl-dev


VOLUME ["/scoreboard"]
WORKDIR /scoreboard
ENTRYPOINT /scoreboard/loader.py --database postgres --urlbase ''
