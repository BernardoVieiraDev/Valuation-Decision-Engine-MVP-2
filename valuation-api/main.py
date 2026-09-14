from api.endpoints.assets import assets_routes
from api.endpoints.market import market_routes
from api.endpoints.valuation import valuation_routes
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(valuation_routes)
app.include_router(assets_routes)
app.include_router(market_routes)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Valuation API está ativa."}


# python -m uvicorn main:app --reload
# python -m uvicorn main:app --reload --port 8001

# Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

