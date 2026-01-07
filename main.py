from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "alive", "project": "asset-intelligence"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}

@app.get("/assets/{asset_id}")
def get_asset(asset_id: int):
    return {"asset_id": asset_id}

@app.get("/search")
def search(q: str = None, limit: int = 10):
    return {"query": q, "limit": limit}

