# 🚀 Quick Start: Deploy to Railway in 5 Minutes

## Prerequisites
- GitHub account with code pushed
- Railway account (free tier available)
- MongoDB Atlas account (free tier available)

## Step 1: Setup MongoDB Atlas (2 minutes)

1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create free cluster (M0)
3. Create database user (username: `medguardian`, generate password)
4. Network Access → Allow from anywhere
5. Get connection string: `mongodb+srv://medguardian:PASSWORD@cluster0.xxxxx.mongodb.net/medguardian?retryWrites=true&w=majority`

## Step 2: Deploy to Railway (3 minutes)

1. **Create Project:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `med-guardian` repository

2. **Configure Service:**
   - Railway auto-detects Python
   - **Build Command**: `cd frontend && npm install && npm run build && cd .. && pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables:**
   - Go to "Variables" tab
   - Add:
     ```
     PORT=8000
     MONGO_URI=mongodb+srv://medguardian:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/medguardian?retryWrites=true&w=majority
     OPENAI_API_KEY=sk-your-key-here (optional)
     GOOGLE_MAPS_API_KEY=AIza-your-key-here (optional)
     ```

4. **Deploy:**
   - Railway automatically deploys
   - Wait for "Build successful"
   - Get your URL from "Settings" → "Generate Domain"

## Step 3: Test

```bash
# Health check
curl https://your-app.railway.app/health

# API test
curl "https://your-app.railway.app/api/cities"
```

## Done! 🎉

Your app is live at: `https://your-app.railway.app`

For detailed instructions, see [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)

