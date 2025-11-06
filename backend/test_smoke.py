from fastapi.testclient import TestClient
from backend.main import app
import json

client = TestClient(app)
resp = client.get('/api/news_trends?city=Chennai&disease=flu&limit=5')
print('status_code:', resp.status_code)
print(json.dumps(resp.json(), indent=2))
