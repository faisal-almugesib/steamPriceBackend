import httpx
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from collections import defaultdict

load_dotenv()

ITAD_API_KEY = os.getenv("ITAD_API_KEY")

async def get_price_history(game_id: str):
    print(f"Fetching price history for game ID: {game_id}")
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Lookup ITAD game ID from Steam App ID
            lookup_resp = await client.get(
                "https://api.isthereanydeal.com/games/lookup/v1",
                params={"key": ITAD_API_KEY, "appid": game_id}
            )
            lookup_data = lookup_resp.json()
            
            if "game" not in lookup_data:
                return {"title": game_id, "history": [], "lowest_price": None, "error": "Game not found."}

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
                return {"title": game_id, "history": [], "lowest_price": None, "error": "Price history not available."}

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
        return {"title": game_id, "history": [], "lowest_price": None, "error": str(e)}
