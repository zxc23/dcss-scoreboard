FROM python:3.5-alpine

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

VOLUME ["/scoreboard"]
WORKDIR /scoreboard
ENTRYPOINT /scoreboard/loader.py --database sqlite --urlbase '' --download-logfiles --download-servers cpo
