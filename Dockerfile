FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend-src/package*.json ./
RUN npm ci
COPY frontend-src/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=frontend-builder /app/frontend/dist ./frontend-src/dist
COPY orgmind/ ./orgmind/

# Create non-root user
RUN useradd -m -u 1000 easywiki && chown -R easywiki:easywiki /app
USER easywiki

ENV ORGMIND_DB_PATH=/data/easywiki.db
ENV ORGMIND_PORT=8080

VOLUME /data
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "uvicorn", "orgmind.main_sqlite:app", "--host", "0.0.0.0", "--port", "8080"]
