import sys
import os
import json
from etrade_options import get_market_instance, get_stock_price, get_stock_beta

def save_tokens(tokens):
    """Save access tokens to file"""
    with open('etrade_tokens.json', 'w') as f:
        json.dump(tokens, f)
    print("Access tokens have been updated in etrade_tokens.json")

def test_etrade_connection():
    print("Testing E*TRADE API connection...")
    
    # Get market instance
    market = get_market_instance()
    if not market:
        print("Failed to get market instance. Please check your config.json and make sure you have valid credentials.")
        return False
    
    # Try to get AAPL price
    print("\nQuerying AAPL price...")
    price = get_stock_price(market, "AAPL")
    
    if price:
        print(f"Success! AAPL current price: ${price:.2f}")
        
        # Test beta calculation
        print("\nTesting beta calculation...")
        beta = get_stock_beta(market, "AAPL", "SPY")
        print(f"AAPL beta relative to SPY: {beta:.2f}")
        
        return True
    else:
        print("Failed to get AAPL price. Please check your API connection and permissions.")
        return False

if __name__ == "__main__":
    # Ensure we're in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # If tokens are provided as command line argument, save them
    if len(sys.argv) > 1:
        try:
            tokens = json.loads(sys.argv[1])
            save_tokens(tokens)
            print("Access tokens have been updated successfully")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format for tokens")
            sys.exit(1)
    
    success = test_etrade_connection()
    sys.exit(0 if success else 1) 