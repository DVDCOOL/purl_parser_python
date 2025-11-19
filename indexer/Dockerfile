FROM python:3.13-slim

WORKDIR /app

COPY shared/ /app/shared/
COPY indexer/ /app/indexer/

RUN pip install --no-cache-dir -r /app/indexer/requirements.txt

WORKDIR /app/indexer

ENV PYTHONPATH="/app/shared:${PYTHONPATH}"

CMD ["python", "indexer.py"]