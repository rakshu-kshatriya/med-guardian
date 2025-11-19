# Med Guardian — Backend (FastAPI)

A production-ready backend for real-time disease monitoring, trend generation, forecasting, and AI-assisted health advisories.

This backend is fully **Railway-safe**:
- Works even with **no MongoDB**
- Works even with **no Redis**
- Works even with **no NewsAPI / Twitter API**
- Uses **synthetic fallback data**
- Never crashes due to missing APIs
- Fully compatible with your Dockerfile & GitHub CI workflow

---

# 🚀 Features

### ✔ Real-time synthetic trends  
### ✔ Forecasting (Prophet → Regression → Synthetic fallback)  
### ✔ AI health advisory (OpenAI optional, has fallback)  
### ✔ SSE live stream endpoints  
### ✔ Fully offline-safe  
### ✔ Railway auto-deploy compatible  

---

# 📦 Installation (Local Development)

## 1️⃣ Create virtual environment
```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
