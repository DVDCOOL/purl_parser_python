FROM python:3.13-slim

WORKDIR /app

COPY inputer/requirements.txt /app/inputer/requirements.txt
RUN pip install --no-cache-dir -r /app/inputer/requirements.txt

COPY shared/ /app/shared/
COPY inputer/ /app/inputer/



WORKDIR /app/inputer

ENV PYTHONPATH="/app/shared:${PYTHONPATH}"

CMD ["python", "inputer.py"]