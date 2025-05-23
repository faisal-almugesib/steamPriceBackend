import httpx
from fastapi import HTTPException
from datetime import datetime

STEAM_SEARCH_API = "https://store.steampowered.com/api/storesearch/"
STEAM_APP_DETAILS_API = "https://store.steampowered.com/api/appdetails"

async def search_games(query: str):
    params = {
        "term": query,
        "cc": "SA",
        "l": "en",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(STEAM_SEARCH_API, params=params)
        data = response.json()

    results = []
    for item in data.get("items", []):
        app_id = item.get("id")
        results.append({
            "id": app_id,
            "name": item.get("name"),
            "tiny_image": item.get("tiny_image"),
            "image": f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
        })

    return results

# async def get_game_name(game_id: int):
#     url = f"{STEAM_APP_DETAILS_API}?appids={game_id}"
#     try:
#         async with httpx.AsyncClient(timeout=15.0) as client:
#             response = await client.get(url)
#             response.raise_for_status()
#             data = response.json()
#             return data[str(game_id)]["data"]["name"]
#     except httpx.ConnectTimeout:
#         raise HTTPException(status_code=504, detail="Steam API connection timed out.")
#     except httpx.RequestError as exc:
#         raise HTTPException(status_code=503, detail=f"Steam API error: {exc}")
#     except Exception:
#         raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching game name.")

async def get_game_details(game_id: int):
    url = f"{STEAM_APP_DETAILS_API}?appids={game_id}&cc=US"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not data[str(game_id)]["success"]:
                raise HTTPException(status_code=404, detail="Game not found")
                
            game_data = data[str(game_id)]["data"]
            
            # Get release date
            release_date_str = game_data.get("release_date", {}).get("date", "")
            
            # Get genres
            genres = [genre["description"] for genre in game_data.get("genres", [])]
            
            # Get price and is_free status
            price_overview = game_data.get("price_overview", {})
            current_price = round(price_overview.get("final", 0) / 100, 2) if price_overview else 0
            is_free = game_data.get("is_free", False) or current_price == 0
            
            return {
                "description": game_data.get("short_description", "No description available"),
                "genres": genres,
                "price": current_price,
                "is_free": is_free,
                "release_date": release_date_str,
                "age": game_data.get("required_age", "0"),
                "developer": ", ".join(game_data.get("developers", ["Unknown"])),
                "publisher": ", ".join(game_data.get("publishers", ["Unknown"]))
            }
                
    except httpx.ConnectTimeout:
        raise HTTPException(status_code=504, detail="Steam API connection timed out.")
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"Steam API error: {exc}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred: {str(e)}")
