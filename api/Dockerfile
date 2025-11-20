FROM python:3.13-slim

WORKDIR /app

COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

COPY shared/ /app/shared/
COPY api/ /app/api/

WORKDIR /app/api

ENV PYTHONPATH="/app/shared:${PYTHONPATH}"
CMD ["python", "main.py"]