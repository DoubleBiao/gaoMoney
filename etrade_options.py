import pyetrade
import configparser
import json
from datetime import datetime, timedelta
import os

def load_config():
    """加载E*TRADE API配置"""
    config = configparser.ConfigParser()
    config.read('etrade_config.ini')
    return {
        'consumer_key': config['API']['CONSUMER_KEY'],
        'consumer_secret': config['API']['CONSUMER_SECRET'],
        'environment': config['API']['ENVIRONMENT']
    }

def save_tokens(tokens):
    """保存访问令牌"""
    with open('etrade_tokens.json', 'w') as f:
        json.dump(tokens, f)

def load_tokens():
    """加载保存的访问令牌"""
    try:
        with open('etrade_tokens.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def get_market_instance():
    """获取E*TRADE市场实例"""
    config = load_config()
    tokens = load_tokens()
    
    if tokens is None:
        print("\n未找到保存的令牌，需要进行新的授权...")
        oauth = pyetrade.ETradeOAuth(
            config['consumer_key'],
            config['consumer_secret']
        )
        
        print("\n授权步骤：")
        print("1. 首先，我们需要获取请求令牌...")
        tokens = oauth.get_request_token()
        
        print("\n2. 现在，您需要在浏览器中完成授权。")
        print("   请按照以下步骤操作：")
        print("   a) 确保您已经登录了E*TRADE账户")
        print("   b) 访问以下授权URL：")
        auth_url = tokens.replace('&oauth_token_secret', '')
        print(f"   {auth_url}")
        
        print("\n3. 在完成授权后，您将看到一个验证码。")
        print("   请将该验证码复制并粘贴到这里：")
        verification_code = input("验证码: ").strip()
        
        try:
            tokens = oauth.get_access_token(verification_code)
            save_tokens(tokens)
        except Exception as e:
            print(f"\n获取访问令牌时出错: {str(e)}")
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
        print(f"\n创建市场实例时出错: {str(e)}")
        if os.path.exists('etrade_tokens.json'):
            os.remove('etrade_tokens.json')
        return None

def get_stock_price(market, symbol):
    """获取股票当前价格"""
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
    """获取期权到期日列表"""
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
    """获取平值期权价格"""
    try:
        # 获取当前股价
        current_price = get_stock_price(market, symbol)
        if not current_price:
            return None
            
        # 转换目标日期为datetime对象
        target_date = datetime.strptime(target_date, '%Y-%m-%d')
        
        # 获取期权链
        response = market.get_option_chains(
            symbol,
            expiry_date=target_date,
            resp_format='json'
        )
        
        if 'OptionChainResponse' not in response:
            return None
            
        pairs = response['OptionChainResponse'].get('OptionPair', [])
        
        # 找到最接近当前价格的看涨期权
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
            # 打印期权信息
            print(f"\n选择的期权信息:")
            print(f"当前价格: ${current_price:.2f}")
            print(f"选择的行权价: ${closest_strike:.2f}")
            print(f"Bid: ${closest_option['bid']:.2f}")
            print(f"Ask: ${closest_option['ask']:.2f}")
            print(f"Volume: {closest_option['volume']}")
            
            # 返回bid和ask的平均值
            bid = float(closest_option['bid'])
            ask = float(closest_option['ask'])
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
    """检查指定日期是否有可用的期权"""
    dates = get_option_expiry_dates(market, symbol)
    return target_date in dates 