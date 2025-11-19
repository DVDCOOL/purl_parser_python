FROM python:3.13-slim

WORKDIR /app

COPY indexer/requirements.txt /app/indexer/requirements.txt
RUN pip install --no-cache-dir -r /app/indexer/requirements.txt

COPY shared/ /app/shared/
COPY indexer/ /app/indexer/



WORKDIR /app/indexer

ENV PYTHONPATH="/app/shared:${PYTHONPATH}"

CMD ["python", "indexer.py"]