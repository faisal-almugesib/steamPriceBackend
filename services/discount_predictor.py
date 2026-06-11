import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("models/gemini-1.5-flash", generation_config={"temperature": 0})

FALLBACK_NOTE = "Sample estimate \u2014 AI prediction API unavailable"


def _fallback_prediction(current_price, original_price, lowest_price, avg_price):
    # Simple statistical estimate: next seasonal sale in ~2 months,
    # priced near the historical low
    predicted_price = round(max(lowest_price, min(current_price, avg_price) * 0.75), 2)
    return {
        "predicted_price": predicted_price,
        "predicted_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
        "old_price": current_price,
        "original_price": original_price,
        "confidence": "Low",
        "fallback": True,
        "note": FALLBACK_NOTE,
    }

async def predict_next_discount(price_history: list[dict]):
    print("Received price history:", price_history)
    
    # Validate input data
    if not price_history:
        print("No price history provided")
        return {
            "predicted_price": 0,
            "predicted_date": "Unknown",
            "old_price": 0,
            "original_price": 0,
            "confidence": "Low - No data provided"
        }

    # Validate each entry has required fields
    valid_entries = []
    for entry in price_history:
        if all(key in entry for key in ["date", "price", "store"]):
            valid_entries.append(entry)
        else:
            print(f"Invalid entry found: {entry}")

    if len(valid_entries) < 3:
        print(f"Insufficient valid entries: {len(valid_entries)}")
        return {
            "predicted_price": 0,
            "predicted_date": "Unknown",
            "old_price": 0,
            "original_price": 0,
            "confidence": "Low - Insufficient data"
        }

    # Sort history by date to ensure chronological order
    sorted_history = sorted(valid_entries, key=lambda x: x["date"])
    print("Sorted history:", sorted_history)
    
    # Calculate some basic statistics
    current_price = sorted_history[-1]["price"]
    highest_price = max(entry["price"] for entry in sorted_history)
    original_price = highest_price  # Use highest price as original price
    lowest_price = min(entry["price"] for entry in sorted_history)
    avg_price = sum(entry["price"] for entry in sorted_history) / len(sorted_history)
    
    # Count how many different stores we have data from
    unique_stores = len(set(entry["store"] for entry in sorted_history))

    if model is None:
        print("GEMINI_API_KEY not set - returning statistical sample prediction")
        return _fallback_prediction(current_price, original_price, lowest_price, avg_price)
    
    print(f"Statistics:")
    print(f"- Current price: ${current_price:.2f}")
    print(f"- Original price (highest): ${original_price:.2f}")
    print(f"- Lowest price: ${lowest_price:.2f}")
    print(f"- Average price: ${avg_price:.2f}")
    print(f"- Unique stores: {unique_stores}")

    prompt = (
        "You are a game price analysis expert. Given the historical price data below for a game, "
        "analyze the pricing patterns and predict when the next significant price drop might occur and what the price will be. "
        "Consider the following:\n"
        f"- Current price: ${current_price:.2f}\n"
        f"- Original price (highest): ${original_price:.2f}\n"
        f"- Lowest historical price: ${lowest_price:.2f}\n"
        f"- Average price: ${avg_price:.2f}\n"
        f"- Number of different stores: {unique_stores}\n\n"
        "Price history (chronological order):\n"
    )

    for entry in sorted_history:
        date = entry["date"]
        price = entry["price"]
        store = entry["store"]
        prompt += f"- {date}: ${price:.2f} at {store}\n"

    prompt += (
        "\nBased on this data, predict:\n"
        "1. When the next significant price drop might occur (format: YYYY-MM-DD)\n"
        "2. The expected price in USD (just the number, no $ symbol)\n"
        "3. Your confidence level in this prediction (High/Medium/Low)\n\n"
        "Format your response as: 'DATE:YYYY-MM-DD,PRICE:XX.XX,CONFIDENCE:LEVEL'"
    )

    print("Sending prompt to Gemini:", prompt)

    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        print("Received response from Gemini:", result)
        
        if result == "Unknown":
            return {
                "predicted_price": 0,
                "predicted_date": "Unknown",
                "old_price": current_price,
                "original_price": original_price,
                "confidence": "Low - Unable to make prediction"
            }
        
        # Extract the prediction line from the response
        prediction_line = None
        for line in result.split('\n'):
            if line.startswith('DATE:'):
                prediction_line = line
                break
        
        if not prediction_line:
            return {
                "predicted_price": 0,
                "predicted_date": "Unknown",
                "old_price": current_price,
                "original_price": original_price,
                "confidence": "Low - Invalid response format"
            }
        
        # Parse the prediction line
        try:
            parts = dict(part.split(":") for part in prediction_line.split(","))
            return {
                "predicted_price": float(parts["PRICE"]),
                "predicted_date": parts["DATE"],
                "old_price": current_price,
                "original_price": original_price,
                "confidence": parts["CONFIDENCE"]
            }
        except (ValueError, KeyError) as e:
            print("Error parsing prediction:", str(e))
            return _fallback_prediction(current_price, original_price, lowest_price, avg_price)
            
    except Exception as e:
        print(f"Prediction API failed ({e}) - returning statistical sample prediction")
        return _fallback_prediction(current_price, original_price, lowest_price, avg_price)
