# Build stage
FROM python:3.8-slim AS builder
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.8-slim
WORKDIR /app
COPY --from=builder /app/. /app/
RUN pip install --no-cache-dir gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
