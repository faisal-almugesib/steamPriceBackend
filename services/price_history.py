from datetime import datetime, timedelta
import random

async def get_price_history(game_id: str):
    today = datetime.today()
    history = []
    lowest_price = float('inf')
    for i in range(12):
        date = today - timedelta(days=i*30)
        price = round(random.uniform(5, 60), 2)
        history.append({"date": date.strftime("%Y-%m-%d"), "price": price})
        if price < lowest_price:
            lowest_price = price

    return {
        "game_id": game_id,
        "history": history[::-1],  # Oldest to newest
        "lowest_price_last_12_months": lowest_price
    }