from coinbase.rest import RESTClient
import logging
from json import dumps
import requests
import time
import json

print("Script starting...")

try:
    # Format the API key with the organization path
    api_key = "organizations/bc7d2bbb-543b-444f-8c0d-1a6d7e398904/apiKeys/9b9a1f24-fe97-4f79-a5ef-cff7dc63b7ce"
    
    # The secret key should include the PEM headers and proper line breaks
    api_secret = """-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIGHSNVa2yE/QmpKiFBG0oljNwEoe86vk6b8wvQp53UeQoAoGCCqGSM49
AwEHoUQDQgAEFMSZc12JIn9/9vIa/i7/kZhiQO0rNW4XdvLjDGKZLNBklN87a1EZ
o052oJpo0Z9piMVlSzTepFTaqK+PDF6Rnw==
-----END EC PRIVATE KEY-----"""

    # Initialize client
    client = RESTClient(api_key=api_key, api_secret=api_secret)
    print("Client initialized!")

    # Just try to list accounts
    print("\nFetching accounts...")
    accounts = client.get_accounts()
    print("Success! Found accounts:")
    for account in accounts.accounts:
        print(f"- {account.name}: {account.available_balance.value} {account.available_balance.currency}")

except Exception as e:
    print(f"\nError:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    exit()

def fetch_products():
    method = "GET"
    request_path = "/products"
    timestamp = str(int(time.time()))
    
    # Create the signature
    signature = create_signature(API_SECRET, timestamp, method, request_path)

    # Set headers
    headers = {
        "CB-ACCESS-KEY": API_KEY,
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

    # Make the request
    response = requests.get(f"{BASE_URL}{request_path}", headers=headers)
    
    if response.status_code == 200:
        return response.json()  # Return the parsed JSON response
    else:
        print(f"Error fetching products: {response.status_code} - {response.text}")
        return None

def place_market_order(product_id, size):
    method = "POST"
    request_path = "/orders"
    timestamp = str(int(time.time()))
    
    body = json.dumps({
        "type": "market",
        "side": "buy",  # or "sell"
        "product_id": product_id,
        "size": size
    })
    
    # Create the signature
    signature = create_signature(API_SECRET, timestamp, method, request_path, body)

    # Set headers
    headers = {
        "CB-ACCESS-KEY": API_KEY,
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

    # Make the request
    response = requests.post(f"{BASE_URL}{request_path}", headers=headers, data=body)
    
    if response.status_code == 201:
        return response.json()  # Return the parsed JSON response
    else:
        print(f"Error placing order: {response.status_code} - {response.text}")
        return None

def main():
    print("Fetching available products...")
    products = fetch_products()
    
    if products:
        print("Available Products:")
        for product in products:
            print(f"- {product['id']}: {product['display_name']}")

        # Example: Place a market order for a specific product
        product_id = "BTC-USD"  # Replace with the desired product ID
        size = 0.001  # Replace with the desired size
        print(f"\nPlacing market order for {size} of {product_id}...")
        order_response = place_market_order(product_id, size)
        print("Order Response:", order_response)

if __name__ == "__main__":
    main()