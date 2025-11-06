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

WORKDIR /app

# Install build tools and common libs required by numeric packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    curl \
    libssl-dev \
    libgomp1 \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    libgfortran5 \
    libopenblas-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install production Python dependencies (smaller, avoids dev-only packages)
COPY backend/requirements-prod.txt ./requirements-prod.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements-prod.txt

# Copy backend code to /app/backend
COPY backend/ ./backend/

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
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

