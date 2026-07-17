FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend-src/package*.json ./
RUN npm ci
COPY frontend-src/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./frontend-src/dist

# Copy backend
COPY orgmind/ ./orgmind/

# Environment
ENV ORGMIND_DB_PATH=/data/easywiki.db
ENV ORGMIND_HOST=0.0.0.0
ENV ORGMIND_PORT=8080

# Volume for database
VOLUME /data

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "orgmind.main_sqlite:app", "--host", "0.0.0.0", "--port", "8080"]
