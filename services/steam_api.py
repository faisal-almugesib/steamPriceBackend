import httpx

STEAM_SEARCH_API = "https://store.steampowered.com/api/storesearch/"

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
        results.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "image": item.get("tiny_image")
        })

    return results
