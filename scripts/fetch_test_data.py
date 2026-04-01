from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()
UNSPLASH_KEY = os.getenv('UNSPLASH_KEY')

def fetch_unsplash_assets(query: str, count: int = 30):
    response = requests.get(
        "https://api.unsplash.com/search/photos",
        params={
            "query": query,
            "per_page": count
        },
        headers={
            "Authorization": f"Client-ID {UNSPLASH_KEY}"
        }
    )
    
    assets = response.json()["results"]
    
    governance_requests = []
    for asset in assets:
        
        # Build tags from available fields
        tags = []
        
        # From explicit tags if present
        if asset.get("tags"):
            tags += [tag["title"] for tag in asset["tags"]]
        
        # From description words if tags empty
        if not tags and asset.get("description"):
            tags = asset["description"].lower().split()[:8]
        
        # From alt_description as fallback
        if not tags and asset.get("alt_description"):
            tags = asset["alt_description"].lower().split()[:8]
        
        # From query as last resort
        if not tags:
            tags = query.lower().split()

        governance_requests.append({
            "asset_id": asset["id"],
            "asset_url": asset["urls"]["small"],
            "description": asset.get("alt_description", ""),
            "generated_tags": tags,
            "source_cms": "unsplash",
            "callback_url": "http://localhost:8000/callback"
        })
    
    return governance_requests


if __name__ == "__main__":
    assets = fetch_unsplash_assets("running shoes athletic", count=30)
    
    with open("test_assets.json", "w") as f:
        json.dump(assets, f, indent=2)
    
    print(f"Fetched {len(assets)} assets\n")
    
    # Print summary of all assets
    for i, asset in enumerate(assets):
        print(f"{i+1}. {asset['asset_id']} | "
              f"tags: {asset['generated_tags'][:3]}")