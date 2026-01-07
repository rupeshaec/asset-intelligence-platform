from fastapi import FastAPI
from typing import Optional

app = FastAPI(title="Asset Intelligence Platform")

# Mock database
assets_db = [
    {"id": 1, "name": "hero-banner.jpg", "type": "image", "tags": ["hero", "homepage"]},
    {"id": 2, "name": "product-guide.pdf", "type": "document", "tags": ["product", "guide"]},
]

@app.get("/")
def root():
    return {"status": "alive", "project": "asset-intelligence"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}

@app.get("/assets")
def list_assets(type: Optional[str] = None, limit: int = 10):
    """List all assets, optionally filtered by type"""
    results = assets_db
    if type:
        results = [a for a in results if a["type"] == type]
    return {"assets": results[:limit], "count": len(results)}

@app.get("/assets/{asset_id}")
def get_asset(asset_id: int):
    """Get a single asset by ID"""
    for asset in assets_db:
        if asset["id"] == asset_id:
            return asset
    return {"error": "Asset not found"}