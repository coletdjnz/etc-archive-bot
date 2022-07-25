FROM python:3.8-slim

WORKDIR /bot

COPY requirements.txt bot ./

RUN pip install -r ./requirements.txt \
&& mkdir /config

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
