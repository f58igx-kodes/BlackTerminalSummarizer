# Build stage
FROM python:3.9-slim AS builder
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Runtime stage
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /app/. /app/
RUN pip install --no-cache-dir gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
