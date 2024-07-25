import requests

def list_coingecko_symbols():
    """List available trading pairs from CoinGecko API"""
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'usd'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()

        print("Available Cryptocurrencies:")
        for coin in data:
            print(coin['id'])  # You can use 'symbol' for shorter names

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

# Call the function to list symbols
list_coingecko_symbols()
