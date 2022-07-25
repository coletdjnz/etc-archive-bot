FROM python:3.8-slim

WORKDIR /bot

RUN pip install --no-cache-dir -r requirements.txt \
&& mkdir /config

COPY bot ./
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
