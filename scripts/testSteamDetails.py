import requests

def get_game_details(appid, country_code='US', language='en'):
    details_url = f"https://store.steampowered.com/api/appdetails"
    params = {
        'appids': appid,
        'cc': country_code,
        'l': language,
    }
    
    response = requests.get(details_url, params=params)
    data = response.json()
    
    if not data.get(str(appid), {}).get('success'):
        print(f"Failed to fetch details for appid: {appid}")
        return
    
    game_data = data[str(appid)]['data']
    print(game_data)
    
    description = game_data.get('short_description', 'No description available')
    release_date = game_data.get('release_date', {}).get('date', 'Unknown release date')
    developers = ', '.join(game_data.get('developers', [])) or 'Unknown developer'
    publishers = ', '.join(game_data.get('publishers', [])) or 'Unknown publisher'
    
    genres_list = game_data.get('genres', [])
    genres = ', '.join([genre.get('description', '') for genre in genres_list]) if genres_list else 'Unknown genres'
    
    price_overview = game_data.get('price_overview')
    if price_overview:
        price = f"{price_overview.get('final_formatted')} (Discount: {price_overview.get('discount_percent')}%)"
    else:
        price = "Free or price info unavailable"
    
    print("\nGame Details:")
    print(f"Description: {description}")
    print(f"Release Date: {release_date}")
    print(f"Developer(s): {developers}")
    print(f"Publisher(s): {publishers}")
    print(f"Genres: {genres}")
    print(f"Price: {price}")

# Example usage with a fixed appid
example_appid = 3241660  # Replace with the Steam appid you want to test
get_game_details(example_appid)
