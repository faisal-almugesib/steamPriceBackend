import httpx
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from collections import defaultdict

load_dotenv()

ITAD_API_KEY = os.getenv("ITAD_API_KEY")

SAMPLE_NOTE = "Sample data \u2014 live price API unavailable"


async def _steam_title(game_id: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://store.steampowered.com/api/appdetails",
                params={"appids": game_id, "cc": "US"},
            )
            entry = resp.json().get(str(game_id), {})
            if entry.get("success"):
                return entry["data"].get("name", f"Game {game_id}")
    except Exception:
        pass
    return f"Game {game_id}"


def _sample_history(game_id: str):
    # Deterministic per game so refreshes look stable
    rng = random.Random(int(game_id) if str(game_id).isdigit() else hash(game_id))
    base = rng.choice([59.99, 49.99, 39.99, 29.99])
    today = datetime.now()
    history = []
    lowest = {"price": float("inf"), "store": "Steam", "date": None}
    for i in range(17, -1, -1):
        month = (today - timedelta(days=30 * i)).strftime("%Y-%m")
        if i % 6 in (1, 2):
            price = round(base * rng.choice([0.5, 0.6, 0.67, 0.75]), 2)
        else:
            price = base
        history.append({"date": month, "price": price, "store": "Steam"})
        if price < lowest["price"]:
            lowest = {"price": price, "store": "Steam", "date": month}
    return history, lowest


async def _fallback_response(game_id: str):
    history, lowest = _sample_history(game_id)
    return {
        "title": await _steam_title(game_id),
        "history": history,
        "lowest_price": lowest,
        "fallback": True,
        "note": SAMPLE_NOTE,
    }

async def get_price_history(game_id: str):
    print(f"Fetching price history for game ID: {game_id}")
    if not ITAD_API_KEY:
        print("ITAD_API_KEY not set - returning sample price history")
        return await _fallback_response(game_id)
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Lookup ITAD game ID from Steam App ID
            lookup_resp = await client.get(
                "https://api.isthereanydeal.com/games/lookup/v1",
                params={"key": ITAD_API_KEY, "appid": game_id}
            )
            lookup_data = lookup_resp.json()
            
            if "game" not in lookup_data:
                return await _fallback_response(game_id)

            itad_game_id = lookup_data["game"]["id"]

            # Step 2: Fetch historical low prices
            storelow_resp = await client.post(
                "https://api.isthereanydeal.com/games/storelow/v2",
                params={"key": ITAD_API_KEY, "country": "SA", "shops": "steam"}, #the parameters are not affecting the output
                json=[itad_game_id]
            )
            storelow_data = storelow_resp.json()
            print("Storelow API Response:", storelow_data)

            # Step 3: Find entry with matching game_id
            matched_game = next((entry for entry in storelow_data if entry["id"] == itad_game_id), None)  #it stops as soon as it finds a match
            if not matched_game or "lows" not in matched_game:
                return await _fallback_response(game_id)

            print("Matched game data:", matched_game)
            print("Number of price points:", len(matched_game["lows"]))

            # Step 4: Process timestamps and group by month
            monthly_prices = defaultdict(list)  # List of (price, store) tuples
            lowest_price = {"price": float('inf'), "store": None, "date": None}

            print("Processing price history...")
            
            for entry in matched_game["lows"]:
                ts = entry["timestamp"]
                dt = datetime.fromisoformat(ts).replace(tzinfo=None)
                month_key = dt.strftime("%Y-%m")
                price = entry["price"]["amount"]
                store_name = entry["shop"]["name"]
                
                # Only update if the entry is from the same month
                if dt.month == int(month_key.split('-')[1]):
                    monthly_prices[month_key].append((price, store_name))
                    # Update lowest price if this price is lower
                    if price < lowest_price["price"]:
                        lowest_price = {
                            "price": price,
                            "store": store_name,
                            "date": month_key
                        }
                    print(f"Added price point: {month_key} - {price} from {store_name}")

            print(f"Found {len(monthly_prices)} months of data")

            # Step 5: Create regular history and lowest price history
            deduped_history = []
            for month, prices in sorted(monthly_prices.items()):
                # Find the lowest price and its store for this month
                lowest_price_month = min(prices, key=lambda x: x[0]) #prices is a tuble of (price, store) so that's why we specify the compare to be on x[0]
                deduped_history.append({
                    "date": month,
                    "price": lowest_price_month[0],
                    "store": lowest_price_month[1]
                })

            return {
                "title": lookup_data["game"].get("title", game_id),
                "history": deduped_history,
                "lowest_price": lowest_price
            }

    except Exception as e:
        print(f"Price history API failed ({e}) - returning sample data")
        return await _fallback_response(game_id)
