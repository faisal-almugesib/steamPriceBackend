import requests
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ITAD_API_KEY")  # Replace with your actual ITAD API key
steam_appid = '1245620'   # Elden Ring

# Step 1: Lookup ITAD game ID from Steam App ID
lookup_url = f"https://api.isthereanydeal.com/games/lookup/v1?key={api_key}&appid={steam_appid}"
lookup_response = requests.get(lookup_url)
lookup_response.raise_for_status()
game_id = lookup_response.json()["game"]["id"]

# Step 2: Fetch historical low prices from Steam shop
storelow_url = f"https://api.isthereanydeal.com/games/storelow/v2?key={api_key}&country=SA&shops=steam"
response = requests.post(storelow_url, json=[game_id])
response.raise_for_status()
data = response.json()

# Verify structure
print("Response structure:", data)

# Step 3: Find entry with matching game_id
matched_game = next((entry for entry in data if entry["id"] == game_id), None) #it stops as soon as it finds a match
if not matched_game or "lows" not in matched_game:
    print("No price history found for the specified game.")
    exit()

# Step 4: Process timestamps and group by month
monthly_prices = defaultdict(lambda: float('inf')) #create a dictionary and if you tried to access a month key that doesn't exist it returns infinity
for entry in matched_game["lows"]:
    ts = entry["timestamp"]
    dt = datetime.fromisoformat(ts)
    month_key = dt.strftime("%Y-%m")
    # Only update if the entry is from the same month
    if dt.month == int(month_key.split('-')[1]):
        monthly_prices[month_key] = min(monthly_prices[month_key], entry["price"]["amount"])

# Step 5: Prepare data for line chart
sorted_months = sorted(monthly_prices)
prices = [monthly_prices[m] for m in sorted_months]

# Step 6: Plot
plt.figure(figsize=(10, 5))
plt.plot(sorted_months, prices, marker='o', linestyle='-', color='green')
plt.xticks(rotation=45)
plt.title("Steam Monthly Lowest Prices")
plt.xlabel("Month")
plt.ylabel("Price (USD)")
plt.grid(True)
plt.tight_layout()
plt.show()
