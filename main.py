from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Asset Intelligence Platform")

# Models
class AssetCreate(BaseModel):
    name: str
    type: str
    tags: Optional[List[str]] = []

class Asset(BaseModel):
    id: int
    name: str
    type: str
    tags: List[str]

# Mock database
assets_db: List[dict] = [
    {"id": 1, "name": "hero-banner.jpg", "type": "image", "tags": ["hero", "homepage"]},
    {"id": 2, "name": "product-guide.pdf", "type": "document", "tags": ["product", "guide"]},
]

@app.get("/")
def root():
    return {"status": "alive", "project": "asset-intelligence"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}

@app.get("/assets", response_model=dict)
def list_assets(type: Optional[str] = None, limit: int = 10):
    results = assets_db
    if type:
        results = [a for a in results if a["type"] == type]
    return {"assets": results[:limit], "count": len(results)}

@app.get("/assets/{asset_id}")
def get_asset(asset_id: int):
    for asset in assets_db:
        if asset["id"] == asset_id:
            return asset
    raise HTTPException(status_code=404, detail="Asset not found")

@app.post("/assets", response_model=Asset)
def create_asset(asset: AssetCreate):
    new_asset = {
        "id": len(assets_db) + 1,
        "name": asset.name,
        "type": asset.type,
        "tags": asset.tags
    }
    assets_db.append(new_asset)
    return new_asset