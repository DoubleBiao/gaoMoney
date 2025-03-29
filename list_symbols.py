import requests
import time

# Replace with your Polygon.io API key
api_key = "dU6vcNnWfb1wMSz_K0ZuPjbHA8teYzPM"

# Base URL for the Polygon.io API with placeholders for dynamic ranges
base_url = f"https://api.polygon.io/v3/reference/tickers?limit=1000&apiKey={api_key}"

# Define a list of ticker prefixes (A-Z) to loop through
ticker_prefixes = [chr(i) for i in range(ord('A'), ord('Z') + 1)]

# Initialize a list to hold all the tickers
all_tickers = []

fp = open("res.txt","w")
# Loop through the ticker prefixes
for prefix in ticker_prefixes:
    # Fetch symbols between current prefix and the next letter
    url = f"{base_url}&ticker.gte={prefix}&ticker.lt={chr(ord(prefix) + 1)}"
    
    while url:
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            tickers = data['results']  # Get the tickers from the response
            all_tickers.extend(tickers)  # Add tickers to the overall list
            
            # Print the current batch of tickers
            for ticker in tickers:
                # print(ticker['ticker'], ticker['name'])
                fp.write(ticker['ticker'] + "\n")
            
            # Check if there is a next URL for pagination
            url = data.get('next_url')

            if url:
                url += f"&apiKey={api_key}"
                print(url)
            time.sleep(30)
        else:
            print(f"Failed to retrieve data for range {prefix}: {response.status_code}")
            break
    

fp.close()

# Print total number of tickers retrieved
print(f"Total number of tickers retrieved: {len(all_tickers)}")

