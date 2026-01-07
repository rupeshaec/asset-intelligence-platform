from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "alive", "project": "asset-intelligence"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}