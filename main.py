from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from services import steam_api, price_history, discount_predictor

#Query used for declaring and validating query parameters.

#when we run the backend FastAPI automatically creates front end page built using SwaggerUI to test our endpoints
app = FastAPI()

# CORS for React frontend on localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # we allow an app running on this url to access our backend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search")
#query is the parameter with a hint that it is a string, then we called Query on it for validation the triple dots means that the parameter is required
#we are calling another async code that's why we need async with await
async def search_games(query: str = Query(...)):
    return await steam_api.search_games(query)

@app.get("/price-history/{game_id}") 
#here the game_id is a path variable no need for validation using Query since we will get the game ID when the user clicks on it
async def get_price_history(game_id: str):
    return await price_history.get_price_history(game_id)


@app.get("/predict-discount/{game_id}")
async def predict_discount(game_id: str):
    history_obj = await price_history.get_price_history(game_id)
    prediction = await discount_predictor.predict_next_discount(history_obj['history'])
    return {"game_id": game_id, "prediction": prediction}