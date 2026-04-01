import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env file automatically

UNSPLASH_KEY = os.getenv('UNSPLASH_KEY')

def fetch_unsplash_assets(query: str, count: int = 50):
    response = requests.get(
        "https://api.unsplash.com/search/photos",
        params={
            "query": query,
            "per_page": count
        },
        headers={
            "Authorization": f"Client-ID {os.getenv('UNSPLASH_KEY')}"
        }
    )
    
    assets = response.json()["results"]
    
    governance_requests = []
    for asset in assets:
        governance_requests.append({
            "asset_id": asset["id"],
            "asset_url": asset["urls"]["small"],
            "generated_tags": [
                tag["title"] for tag in asset.get("tags", [])
            ],
            "source_cms": "unsplash",
            "callback_url": "http://localhost:8000/callback"
        })
    
    return governance_requests


if __name__ == "__main__":
    assets = fetch_unsplash_assets("running shoes athletic", count=30)
    
    # Save to file for inspection
    with open("test_assets.json", "w") as f:
        json.dump(assets, f, indent=2)
    
    print(f"Fetched {len(assets)} assets")
    print(f"Sample asset:")
    print(json.dumps(assets[0], indent=2))