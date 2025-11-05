# Real-Time Stream Testing Guide

## How to Test the `/api/stream` Endpoint

The SSE (Server-Sent Events) stream is now integrated into the PredictionChart component. Here's how to test it:

### 1. Visual Testing in the Browser

1. **Start the application:**
   ```bash
   # Backend
   cd backend
   uvicorn main:app --reload --port 8000

   # Frontend (in another terminal)
   cd frontend
   npm run dev
   ```

2. **Open the browser console** (F12 → Console tab)

3. **Select a city and disease** in the dashboard

4. **Watch for console logs:**
   - `🔌 Setting up SSE stream for: { city, disease }`
   - `✅ Stream connected: { city, disease }`
   - `📊 Stream update received: { cases, timestamp, ... }`
   - `📈 Updating chart with stream data: { ... }`

5. **Observe the chart:**
   - The chart will update every 10 seconds with new data
   - The "Current Cases" KPI card shows a green "Live" indicator
   - A status indicator shows "Real-time updates active" with last update time
   - The chart line will animate as new data points are added/updated

### 2. Direct API Testing

You can also test the stream endpoint directly:

**Using curl:**
```bash
curl -N "http://localhost:8000/api/stream?city=Bengaluru&disease=Dengue"
```

**Using browser:**
Open in a new tab:
```
http://localhost:8000/api/stream?city=Bengaluru&disease=Dengue
```

You should see events like:
```
event: update
data: {"timestamp":"2025-01-15T10:30:00","city":"Bengaluru","disease":"Dengue","cases":145,"avg_temp":26.5,"real_time_aqi":78.3}

event: update
data: {"timestamp":"2025-01-15T10:30:10","city":"Bengaluru","disease":"Dengue","cases":150,"avg_temp":26.8,"real_time_aqi":79.1}
```

### 3. What You Should See

**In the Chart:**
- The blue "Historical Cases" line updates in real-time
- The current day's data point moves up/down as new cases arrive
- KPI cards update: Current Cases, 7-Day Average, and Trend

**In the Console:**
- Connection logs when the stream starts
- Update logs every 10 seconds showing new data
- Error logs if the connection fails

**Visual Indicators:**
- Green pulsing dot next to "Current Cases" = Live stream active
- "Real-time updates active" status message
- Last update timestamp

### 4. Troubleshooting

**Stream not connecting?**
- Check browser console for errors
- Verify backend is running on port 8000
- Check CORS settings (should allow all origins in unified mode)

**No updates appearing?**
- Wait 10 seconds (update interval)
- Check browser console for stream errors
- Verify the city name matches exactly (case-sensitive)

**Chart not updating?**
- Check React DevTools to see if state is updating
- Verify the data structure matches expected format
- Check for JavaScript errors in console

### 5. Testing Different Scenarios

**Change City:**
- Select a different city → Stream reconnects automatically
- Old connection closes, new one opens
- Chart updates with new city data

**Change Disease:**
- Select a different disease → Stream updates
- New data appears with disease-specific values

**Network Issues:**
- Disconnect internet → Stream errors appear in console
- Reconnect → Stream should automatically reconnect (if EventSource supports it)

## Technical Details

### Stream Format
The backend sends SSE events in this format:
```
event: update
data: {"timestamp":"...","city":"...","disease":"...","cases":123,"avg_temp":25.0,"real_time_aqi":80.0}
```

### Update Frequency
- Default: Every 10 seconds
- Configurable in `backend/main.py` (change `await asyncio.sleep(10)`)

### Data Flow
1. Component mounts → Fetches initial prediction data
2. Stream connects → EventSource created
3. Updates arrive → Chart data updated
4. KPIs recalculated → UI re-renders
5. Cleanup on unmount → Stream closes

### Performance
- Chart updates are smooth (Recharts handles re-renders efficiently)
- Only the latest data point is updated (not entire dataset)
- Console logging can be disabled in production by removing `console.log` statements

