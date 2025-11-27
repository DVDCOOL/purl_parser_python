FROM python:3.13-slim

WORKDIR /app

# Copy and install requirements
COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

# Copy application code
COPY shared/ /app/shared/
COPY api/ /app/api/

WORKDIR /app/api

# Set Python path so it can find shared modules
ENV PYTHONPATH="/app/shared:${PYTHONPATH}"

# Use gunicorn instead of python for production
CMD ["gunicorn", "-k", "gevent", "-w", "4", "--worker-connections", "1000", "-b", "0.0.0.0:8080", "--timeout", "120", "main:app"]