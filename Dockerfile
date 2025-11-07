# Stage 1 — Frontend Build
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Stage 2 — Backend with FastAPI + Uvicorn
FROM python:3.11-slim AS backend

# A small cache-bust ARG so CI / Railway will perform a fresh build when we change the source
# Bump this value to force a full rebuild and avoid stale cached layers on remote builders
ARG CACHEBUST=2

WORKDIR /app

# Install build tools and common libs required by numeric packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    curl \
    ca-certificates \
    libssl-dev \
    libgomp1 \
    libblas-dev \
    liblapack-dev \
    libgfortran5 \
    libopenblas-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install production Python dependencies (smaller, avoids dev-only packages)
# We copy the prod file and also write it to requirements.txt to be defensive
COPY backend/requirements-prod.txt ./requirements-prod.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    cp requirements-prod.txt requirements.txt && \
    pip install --no-cache-dir -r requirements-prod.txt

# Copy backend code to /app/backend
COPY backend/ ./backend/

# Copy startup script so Railway or the Docker startCommand can run it.
COPY start-prod.sh ./start-prod.sh
RUN chmod +x ./start-prod.sh

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Change to backend directory for proper imports
WORKDIR /app/backend

# Run uvicorn (imports work because PYTHONPATH=/app allows importing backend.*)
# But we're in /app/backend so relative imports work too
CMD ["bash", "start-prod.sh"]

