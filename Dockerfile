# Stage 1 — Frontend Build
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2 — Backend Build
FROM python:3.11-slim AS backend

ARG CACHEBUST=2

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make \
    libssl-dev libgomp1 libblas-dev liblapack-dev libopenblas-dev libgfortran5 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies first
COPY backend/requirements-prod.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy frontend output
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copy start script
COPY start-prod.sh ./start-prod.sh
RUN chmod +x ./start-prod.sh

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# Start script

CMD ["bash", "/app/start-prod.sh"]
