import pyetrade
import json
import webbrowser
import os
from datetime import datetime

def load_config():
    """Load E*TRADE API configuration"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return {
            'consumer_key': config['etrade']['consumer_key'],
            'consumer_secret': config['etrade']['consumer_secret'],
            'environment': 'PROD' if not config['etrade']['sandbox'] else 'SANDBOX'
        }
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        return None

def save_tokens(tokens):
    """Save access tokens"""
    with open('etrade_tokens.json', 'w') as f:
        json.dump(tokens, f)

def load_tokens():
    """Load saved access tokens"""
    try:
        with open('etrade_tokens.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def get_verification_code():
    """Get verification code from user input"""
    print("\nPlease enter the verification code from E*TRADE:")
    verification_code = input().strip()
    return verification_code

def get_market_instance():
    """Get E*TRADE market instance"""
    config = load_config()
    tokens = load_tokens()
    
    if tokens is None:
        print("\nNo saved tokens found, starting new authorization...")
        oauth = pyetrade.ETradeOAuth(
            config['consumer_key'],
            config['consumer_secret']
        )
        
        print("\nAuthorization steps:")
        print("1. Getting request token...")
        tokens = oauth.get_request_token()
        
        print("\n2. Please complete authorization in your browser:")
        print("   a) Make sure you're logged into your E*TRADE account")
        print("   b) Visit this authorization URL:")
        auth_url = tokens.replace('&oauth_token_secret', '')
        print(f"   {auth_url}")
        
        # Open browser automatically
        webbrowser.open(auth_url)
        
        print("\n3. Please enter the verification code:")
        verification_code = get_verification_code()
        
        try:
            tokens = oauth.get_access_token(verification_code)
            save_tokens(tokens)
        except Exception as e:
            print(f"\nError getting access token: {str(e)}")
            return None
    
    try:
        market = pyetrade.ETradeMarket(
            config['consumer_key'],
            config['consumer_secret'],
            tokens['oauth_token'],
            tokens['oauth_token_secret'],
            dev=(config['environment'] != 'PROD')
        )
        return market
    except Exception as e:
        print(f"\nError creating market instance: {str(e)}")
        if os.path.exists('etrade_tokens.json'):
            os.remove('etrade_tokens.json')
        return None

def get_stock_price(market, symbol):
    """Get current stock price"""
    try:
        response = market.get_quote([symbol], resp_format='json')
        if 'QuoteResponse' in response and 'QuoteData' in response['QuoteResponse']:
            quote = response['QuoteResponse']['QuoteData'][0]
            if 'All' in quote:
                return float(quote['All'].get('lastTrade', 0))
    except Exception as e:
        print(f"获取{symbol}价格时出错: {str(e)}")
    return None

def get_option_expiry_dates(market, symbol):
    """Get list of option expiry dates"""
    try:
        response = market.get_option_expire_date(symbol, resp_format='json')
        if 'OptionExpireDateResponse' in response:
            dates = []
            for date in response['OptionExpireDateResponse'].get('ExpirationDate', []):
                expiry = datetime(
                    year=date['year'],
                    month=date['month'],
                    day=date['day']
                )
                dates.append(expiry.strftime('%Y-%m-%d'))
            return dates
    except Exception as e:
        print(f"获取{symbol}期权到期日时出错: {str(e)}")
    return []

def get_atm_option_price(market, symbol, target_date):
    """Get at-the-money option price"""
    try:
        # Get current stock price
        current_price = get_stock_price(market, symbol)
        if not current_price:
            return None
            
        # Convert target date to datetime object
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d')
        
        # Get option chain
        response = market.get_option_chains(
            symbol,
            expiry_date=target_date,
            resp_format='json'
        )
        
        if 'OptionChainResponse' not in response:
            return None
            
        pairs = response['OptionChainResponse'].get('OptionPair', [])
        
        # Find the closest strike price to current price
        closest_strike = None
        closest_option = None
        min_diff = float('inf')
        
        for pair in pairs:
            if 'Call' in pair:
                strike = float(pair['Call']['strikePrice'])
                diff = abs(strike - current_price)
                if diff < min_diff:
                    min_diff = diff
                    closest_strike = strike
                    closest_option = pair['Call']
        
        if closest_option:
            # Get bid and ask prices
            try:
                bid = float(closest_option.get('bid', 0))
                ask = float(closest_option.get('ask', 0))
                volume = int(closest_option.get('volume', 0))
            except (ValueError, TypeError):
                bid = 0
                ask = 0
                volume = 0
            
            # Print option information
            print(f"\nSelected option information:")
            print(f"Current price: ${current_price:.2f}")
            print(f"Selected strike: ${closest_strike:.2f}")
            print(f"Bid: ${bid:.2f}")
            print(f"Ask: ${ask:.2f}")
            print(f"Volume: {volume}")
            
            # Return average of bid and ask
            if bid > 0 and ask > 0:
                return (bid + ask) / 2
            elif bid > 0:
                return bid
            elif ask > 0:
                return ask
            
    except Exception as e:
        print(f"获取{symbol}期权价格时出错: {str(e)}")
    return None

def check_option_availability(market, symbol, target_date):
    """Check if options are available for the target date"""
    dates = get_option_expiry_dates(market, symbol)
    return target_date in dates

def get_stock_beta(market, symbol):
    """Get stock beta value"""
    try:
        # Get stock information
        response = market.get_quote([symbol], resp_format='json')
        if 'QuoteResponse' in response and 'QuoteData' in response['QuoteResponse']:
            quote = response['QuoteResponse']['QuoteData'][0]
            if 'All' in quote:
                beta = float(quote['All'].get('beta', 1.0))
                return beta
    except Exception as e:
        print(f"Warning: Error getting beta for {symbol}: {str(e)}, using default value 1.0")
    return 1.0 