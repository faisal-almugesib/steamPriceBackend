from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from services import steam_api, price_history, discount_predictor

app = FastAPI(
    title="Steam Price Tracker API",
    description="API for tracking Steam game prices and predicting discounts",
    version="1.0.0"
)

# CORS for React frontend on Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://games-stats.vercel.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Steam Price Tracker API",
        "endpoints": {
            "/search": "Search for games",
            "/price-history/{game_id}": "Get price history for a game",
            "/predict-discount/{game_id}": "Predict next discount for a game",
            "/game-details/{game_id}": "Get detailed information about a game"
        }
    }

@app.get("/search")
async def search_games(query: str = Query(...)):
    return await steam_api.search_games(query)

@app.get("/price-history/{game_id}") 
async def get_price_history(game_id: str):
    return await price_history.get_price_history(game_id)


@app.get("/predict-discount/{game_id}")
async def predict_discount(game_id: str):
    history_obj = await price_history.get_price_history(game_id)
    prediction = await discount_predictor.predict_next_discount(history_obj['history'])
    return prediction

# @app.get("/game-name/{game_id}")
# async def get_game_name(game_id: str):
#     return {"game_name": await steam_api.get_game_name(game_id)}

@app.get("/game-details/{game_id}")
async def get_game_details_endpoint(game_id: str):
    try:
        return await steam_api.get_game_details(game_id)
    except Exception as e:
        return {"error": str(e)}