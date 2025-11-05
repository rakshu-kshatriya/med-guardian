# 🧬 Med Guardian

A comprehensive disease prediction and health advisory system for Indian cities. Built with FastAPI backend and React frontend, unified into a single web application with automatic HTTPS via Caddy.

## Project Structure

```
med-guardian/
├── backend/          # FastAPI backend
├── frontend/         # React + Vite frontend
├── Dockerfile        # Multi-stage Docker build
├── docker-compose.yml # Docker Compose configuration
└── Caddyfile        # Caddy reverse proxy configuration
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) Domain name for production (e.g., med-guardian.com)

### Run Locally with Docker

```bash
# Build and start all services
docker compose up --build

# Or run in detached mode
docker compose up -d --build
```

Then open **http://localhost** in your browser.

The application will be available at:
- **Local:** http://localhost
- **Production:** https://med-guardian.com (after domain configuration)

### Development Mode (Without Docker)

If you prefer to run frontend and backend separately for development:

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env and fill in OPENAI_API_KEY and GOOGLE_MAPS_API_KEY (optional)

# Run the server
uvicorn main:app --reload --port 8000
```

**Note on Prophet:** If you encounter installation issues with Prophet (requires C++ build tools), try:
```bash
pip install prophet --no-binary :all:
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000` (with API proxy to backend).

## 🌐 Deploy to Production

1. **Point your domain to your server:**
   - Set A record for `med-guardian.com` and `www.med-guardian.com` to your server IP

2. **On your server, run:**
   ```bash
   # Clone the repository
   git clone <your-repo-url>
   cd med-guardian
   
   # Start services
   docker compose up -d --build
   ```

3. **Caddy will automatically:**
   - Issue SSL certificates via Let's Encrypt
   - Renew certificates automatically
   - Enable HTTPS with security headers

4. **Access your application:**
   - Production: https://med-guardian.com
   - All API routes work under `/api/...`

## Features

### Backend API

- **GET /api/trends/latest** - Get latest 30 days of disease trend data
- **GET /api/predict** - Get 30-day disease forecast using Prophet
- **GET /api/advisory** - Get AI-generated health advisory
- **GET /api/directions** - Get route directions between cities
- **GET /api/stream** - SSE endpoint for real-time updates
- **GET /api/cities** - Get list of all available cities

### Frontend Dashboard

- **Prediction Chart** - Interactive chart showing historical and predicted disease trends
- **AI Advisory** - Health advisories with reasoning and precautions
- **City Route Planner** - Interactive map for route planning between cities
- **Real-time Updates** - SSE integration for live data updates

## Configuration

### Backend Environment Variables

Create `backend/.env` file:
- `OPENAI_API_KEY` - For AI-generated advisories (optional, has fallback)
- `GOOGLE_MAPS_API_KEY` - For map features (optional)
- `MONGO_URI` - MongoDB connection string (optional, uses synthetic data if not set)
- `REDIS_URL` - Redis connection string (optional)

### Frontend Environment Variables

Create `frontend/.env.local` file:
- `VITE_GOOGLE_MAPS_API_KEY` - Google Maps API key for map features

## Technology Stack

### Backend
- FastAPI
- Prophet (time series forecasting)
- OpenAI API (for health advisories)
- Pandas, NumPy, Scikit-learn

### Frontend
- React 18
- Vite
- Tailwind CSS
- Recharts (data visualization)
- Google Maps API

### Infrastructure
- Docker & Docker Compose
- Caddy (automatic HTTPS)
- Multi-stage builds for optimization

## Docker Commands

```bash
# Build and start
docker compose up --build

# Start in background
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild specific service
docker compose build app
docker compose up -d
```

## Development

### Local Development (Without Docker)

See "Development Mode" section above for running frontend and backend separately.

### Production Build

The Dockerfile automatically builds the frontend and serves it from the backend. No manual build step needed when using Docker.

## Troubleshooting

### Prophet Installation Issues

Prophet requires C++ build tools. On Windows, install Visual Studio Build Tools. On Linux/Mac, install build-essential/cmake.

If issues persist:
```bash
pip install prophet --no-binary :all:
```

### Port Already in Use

If port 8000 or 3000 is already in use, you can change them:
- Backend: Modify the port in the uvicorn command
- Frontend: Modify `vite.config.js`

## License

MIT License

