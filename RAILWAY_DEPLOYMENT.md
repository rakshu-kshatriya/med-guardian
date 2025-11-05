# 🚂 Railway.com Deployment Guide for Med-Guardian

Complete step-by-step guide to deploy Med-Guardian on Railway.com with MongoDB Atlas and optional Redis.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **MongoDB Atlas Account**: Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
3. **GitHub Repository**: Push your code to GitHub
4. **API Keys Ready**:
   - OpenAI API Key (optional, for AI advisories)
   - Google Maps API Key (optional, for map features)

## Step 1: Setup MongoDB Atlas

1. **Create MongoDB Atlas Account**
   - Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - Sign up for free tier (M0 cluster)

2. **Create Cluster**
   - Click "Build a Database"
   - Choose "M0 FREE" tier
   - Select a cloud provider and region (choose closest to Railway region)
   - Click "Create"

3. **Configure Database Access**
   - Go to "Database Access" → "Add New Database User"
   - Username: `medguardian` (or your choice)
   - Password: Generate secure password (save it!)
   - Database User Privileges: "Read and write to any database"
   - Click "Add User"

4. **Configure Network Access**
   - Go to "Network Access" → "Add IP Address"
   - Click "Allow Access from Anywhere" (or add Railway IPs)
   - Click "Confirm"

5. **Get Connection String**
   - Go to "Database" → "Connect"
   - Choose "Connect your application"
   - Copy the connection string
   - Replace `<password>` with your database user password
   - Replace `<dbname>` with `medguardian`
   - Example: `mongodb+srv://medguardian:yourpassword@cluster0.xxxxx.mongodb.net/medguardian?retryWrites=true&w=majority`

## Step 2: Deploy Backend to Railway

1. **Create New Project**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `med-guardian` repository

2. **Create Backend Service**
   - Click "New" → "Service"
   - Select your repository
   - Railway will auto-detect Python

3. **Configure Service Settings**
   - **Name**: `med-guardian-backend`
   - **Language**: Python
   - **Root Directory**: Leave empty (Railway uses root)
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Port**: Railway auto-assigns (use `$PORT` variable)

4. **Set Environment Variables**
   - Go to "Variables" tab
   - Add the following:

   ```
   PORT=8000
   BACKEND_PORT=8000
   MONGO_URI=mongodb+srv://medguardian:yourpassword@cluster0.xxxxx.mongodb.net/medguardian?retryWrites=true&w=majority
   OPENAI_API_KEY=sk-your-openai-key-here
   GOOGLE_MAPS_API_KEY=AIza-your-google-maps-key-here
   REDIS_URL=redis://default:password@redis.railway.internal:6379 (if using Railway Redis)
   ```

5. **Deploy**
   - Railway will automatically detect changes and deploy
   - Watch the logs in the "Deployments" tab
   - Wait for "Build successful"

6. **Get Backend URL**
   - Go to "Settings" → "Generate Domain"
   - Railway will provide a URL like: `med-guardian-backend-production.up.railway.app`
   - Copy this URL (you'll need it for frontend)

## Step 3: Deploy Frontend to Railway

1. **Create Frontend Service**
   - In the same project, click "New" → "Service"
   - Select your repository again

2. **Configure Service Settings**
   - **Name**: `med-guardian-frontend`
   - **Language**: Node.js
   - **Root Directory**: Leave empty
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Start Command**: `cd frontend && npm run start -- --port $PORT`
   - **Port**: Use `$PORT` variable

3. **Set Environment Variables**
   - Go to "Variables" tab
   - Add:
   ```
   PORT=3000
   VITE_API_URL=https://med-guardian-backend-production.up.railway.app
   VITE_GOOGLE_MAPS_API_KEY=AIza-your-google-maps-key-here
   ```

4. **Update Frontend API Configuration**
   - The frontend `api.js` already uses relative URLs in production
   - For Railway, you may need to set `VITE_API_URL` if using separate services

5. **Deploy**
   - Railway will build and deploy automatically
   - Check logs for build success

6. **Get Frontend URL**
   - Go to "Settings" → "Generate Domain"
   - Railway provides: `med-guardian-frontend-production.up.railway.app`

## Step 4: Optional - Add Redis Service

1. **Add Redis to Project**
   - Click "New" → "Database" → "Add Redis"
   - Railway will provision Redis instance
   - Get connection URL from "Variables" tab
   - Add `REDIS_URL` to backend service variables

## Step 5: Unified Deployment (Recommended)

Since we have a unified app (backend serves frontend), you can deploy as a single service:

1. **Create Single Service**
   - **Name**: `med-guardian`
   - **Language**: Python
   - **Build Command**: 
     ```bash
     cd frontend && npm install && npm run build && cd ..
     pip install -r backend/requirements.txt
     ```
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables** (same as backend above)

3. **Deploy**
   - Single unified service serving both frontend and backend

## Step 6: Configure Custom Domain (Optional)

1. **Add Custom Domain**
   - Go to service "Settings" → "Domains"
   - Click "Custom Domain"
   - Enter: `med-guardian.com`
   - Railway will provide DNS records
   - Update your DNS with provided records
   - Wait for SSL certificate (automatic)

## Step 7: Test Deployment

### Test Backend Health
```bash
curl https://your-railway-url.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00",
  "services": {
    "mongodb": true,
    "redis": false
  }
}
```

### Test API Endpoints
```bash
# Get cities
curl https://your-railway-url.railway.app/api/cities

# Get trends
curl "https://your-railway-url.railway.app/api/trends/latest?city=Bengaluru&disease=Dengue"

# Get prediction
curl "https://your-railway-url.railway.app/api/predict?city=Bengaluru&disease=Dengue"

# Get advisory
curl "https://your-railway-url.railway.app/api/advisory?city=Bengaluru&disease=Dengue&aqi=100&temp=25"
```

### Test Frontend
- Open your Railway URL in browser
- Verify dashboard loads
- Test city selection
- Verify charts render
- Check browser console for errors

## Environment Variables Checklist

### Backend Service Variables
```
PORT=8000
BACKEND_PORT=8000
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/medguardian?retryWrites=true&w=majority
OPENAI_API_KEY=sk-...
GOOGLE_MAPS_API_KEY=AIza...
REDIS_URL=redis://default:pass@redis.railway.internal:6379 (optional)
PYTHONUNBUFFERED=1
```

### Frontend Service Variables (if separate)
```
PORT=3000
VITE_API_URL=https://your-backend-url.railway.app
VITE_GOOGLE_MAPS_API_KEY=AIza...
```

## Troubleshooting

### Build Fails

**Prophet Installation Issues:**
- Railway uses Nixpacks which should handle Prophet
- If issues occur, check logs for C++ build tools
- Consider using `prophet --no-binary :all:` in requirements.txt

**Frontend Build Fails:**
- Check Node.js version (Railway auto-detects)
- Verify all dependencies in `package.json`
- Check build logs for specific errors

### Runtime Errors

**MongoDB Connection Failed:**
- Verify `MONGO_URI` is correct
- Check MongoDB Atlas network access allows Railway IPs
- Verify database user has correct permissions
- Check MongoDB Atlas logs

**Port Errors:**
- Always use `$PORT` environment variable
- Railway assigns port automatically
- Don't hardcode port numbers

**CORS Errors:**
- Backend already allows all origins (`allow_origins=["*"]`)
- If issues persist, check Railway proxy settings

### Database Issues

**No Data in MongoDB:**
- App uses synthetic data as fallback
- Check MongoDB connection in health endpoint
- Verify data is being saved (check MongoDB Atlas dashboard)

**Redis Connection Issues:**
- Redis is optional, app works without it
- Check Redis URL format
- Verify Railway Redis service is running

## Monitoring

### Railway Logs
- View real-time logs in Railway dashboard
- Check "Deployments" tab for build logs
- Monitor service health

### Health Check Endpoint
- Set up monitoring to hit `/health` endpoint
- Check `mongodb` and `redis` status in response
- Monitor response time

### MongoDB Atlas Monitoring
- Check MongoDB Atlas dashboard for connection metrics
- Monitor database size and operations
- Set up alerts for unusual activity

## Production Checklist

- [ ] MongoDB Atlas cluster created and configured
- [ ] Database user created with proper permissions
- [ ] Network access configured (allows Railway IPs)
- [ ] All environment variables set in Railway
- [ ] Backend service deployed and healthy
- [ ] Frontend service deployed (if separate) or unified service working
- [ ] Health check endpoint returns `status: "healthy"`
- [ ] API endpoints responding correctly
- [ ] Frontend loading and displaying data
- [ ] Real-time SSE stream working
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active
- [ ] Monitoring and alerts configured

## Cost Estimation

**Railway Free Tier:**
- $5 free credit per month
- 500 hours of usage
- Perfect for small projects

**MongoDB Atlas Free Tier:**
- M0 cluster (512MB storage)
- Free forever
- Suitable for development/small production

**Redis (Optional):**
- Railway Redis: Included in some plans
- Or use Upstash Redis (free tier available)

## Support

- Railway Docs: [docs.railway.app](https://docs.railway.app)
- MongoDB Atlas Docs: [docs.atlas.mongodb.com](https://docs.atlas.mongodb.com)
- Project Issues: Check GitHub repository

---

**Your Med-Guardian app is now live on Railway! 🎉**

Visit your Railway URL to see it in action: `https://your-app-name.railway.app`

