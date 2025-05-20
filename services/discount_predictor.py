import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("models/gemini-1.5-flash")  # or "models/gemini-1.5-flash"

async def predict_next_discount(price_history: list[dict]):
    if not price_history or len(price_history) < 3:
        return "Unknown"

    prompt = (
        "Given the historical Steam price data below for a game, "
        "estimate when the next discount might happen. "
        "If there is not enough data to make a prediction, respond with 'Unknown'.\n\n"
        "Price history:\n"
    )

    for entry in price_history:
        date = entry.get("date", "unknown date")
        price = entry.get("price", "unknown price")
        prompt += f"- {date}: {price}\n"

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"
