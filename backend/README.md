# Med Guardian Backend

FastAPI backend for disease prediction and health advisory system.

## Setup

1. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   **Note on Prophet:** If you encounter installation issues with Prophet (requires C++ build tools), try:
   ```bash
   pip install prophet --no-binary :all:
   ```
   Or follow the [Prophet installation guide](https://facebook.github.io/prophet/docs/installation.html).

3. **Configure environment:**
   ```bash
   cp env.example .env
   ```
   Edit `.env` and fill in:
   - `OPENAI_API_KEY` - For AI-generated advisories (optional, has fallback)
   - `GOOGLE_MAPS_API_KEY` - For map features (optional)
   - `MONGO_URI` - MongoDB connection string (optional, uses synthetic data if not set)
   - `REDIS_URL` - Redis connection string (optional)

4. **Run the server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

The API will be available at `http://localhost:8000`.

## API Endpoints

- `GET /api/trends/latest?city={city}&disease={disease}` - Get latest 30 days of trend data
- `GET /api/predict?city={city}&disease={disease}` - Get 30-day forecast
- `GET /api/advisory?city={city}&disease={disease}&aqi={aqi}&temp={temp}` - Get health advisory
- `GET /api/directions?origin_city={city1}&destination_city={city2}` - Get route directions
- `GET /api/stream?city={city}&disease={disease}` - SSE stream for real-time updates
- `GET /api/cities` - Get list of all available cities

## Optional: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

