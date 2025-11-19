# ------------------------------
# FRONTEND BUILDER
# ------------------------------
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps

COPY frontend/ ./
RUN npm run build


# ------------------------------
# BACKEND IMAGE
# ------------------------------
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies required for Prophet & scientific libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make \
    libssl-dev libgomp1 libblas-dev liblapack-dev libopenblas-dev libgfortran5 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY backend/ ./backend/

# Copy requirements FIRST, then install
COPY backend/requirements-prod.txt ./requirements.txt

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy prod start script
COPY start-prod.sh ./start-prod.sh
RUN chmod +x start-prod.sh

# Copy frontend built files
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["./start-prod.sh"]
