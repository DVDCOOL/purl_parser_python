FROM python:3.13-slim

WORKDIR /app

COPY spider/requirements.txt /app/spider/requirements.txt
RUN pip install --no-cache-dir -r /app/spider/requirements.txt

COPY shared/ /app/shared/
COPY spider/ /app/spider/

WORKDIR /app/spider

ENV PYTHONPATH="/app/shared:${PYTHONPATH}"

CMD ["python", "spider.py"]