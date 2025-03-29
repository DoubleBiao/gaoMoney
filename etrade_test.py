import pyetrade
import configparser
import json
from datetime import datetime, timedelta
import webbrowser
import os

def load_config():
    config = configparser.ConfigParser()
    config.read('etrade_config.ini')
    return {
        'consumer_key': config['API']['CONSUMER_KEY'],
        'consumer_secret': config['API']['CONSUMER_SECRET'],
        'environment': config['API']['ENVIRONMENT']
    }

def save_tokens(tokens):
    with open('etrade_tokens.json', 'w') as f:
        json.dump(tokens, f)

def load_tokens():
    try:
        with open('etrade_tokens.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def get_market_instance(config):
    # 尝试加载保存的令牌
    tokens = load_tokens()
    
    if tokens is None:
        print("\n未找到保存的令牌，需要进行新的授权...")
        # 创建OAuth会话
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
        print("\n   是否要自动在浏览器中打开此URL？(y/n)")
        if input().lower() == 'y':
            webbrowser.open(auth_url)
        
        print("\n3. 在完成授权后，您将看到一个验证码。")
        print("   请将该验证码复制并粘贴到这里：")
        verification_code = input("验证码: ").strip()
        
        print("\n4. 正在使用验证码获取访问令牌...")
        try:
            tokens = oauth.get_access_token(verification_code)
            print("成功获取访问令牌！")
            # 保存令牌以供将来使用
            save_tokens(tokens)
        except Exception as e:
            print(f"\n获取访问令牌时出错: {str(e)}")
            print("请确保验证码正确，并且在有效期内使用。")
            return None
    else:
        print("\n使用保存的访问令牌...")

    # 创建市场实例
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
        # 如果令牌过期，删除保存的令牌文件
        if os.path.exists('etrade_tokens.json'):
            os.remove('etrade_tokens.json')
        print("令牌可能已过期，请重新运行程序进行授权。")
        return None

def print_option_chain(pairs, current_price):
    # 打印表头
    print("\n期权链数据")
    print(f"{'看涨期权':^30} {'执行价':^10} {'看跌期权':^30}")
    print(f"{'买/量':^15}{'卖/量':^15} {' ':^10} {'买/量':^15}{'卖/量':^15}")
    print("-" * 70)
    
    # 创建一个字典来存储每个执行价的看涨和看跌期权数据
    options_by_strike = {}
    
    # 整理数据
    for pair in pairs:
        if 'Call' in pair and 'Put' in pair:
            strike_price = float(pair['Call']['strikePrice'])
            # 只显示当前价格上下10美元范围内的期权
            if current_price - 10 <= strike_price <= current_price + 10:
                call_data = pair['Call']
                put_data = pair['Put']
                
                options_by_strike[strike_price] = {
                    'call': {
                        'bid': call_data.get('bid', 'N/A'),
                        'ask': call_data.get('ask', 'N/A'),
                        'volume': call_data.get('volume', 0)
                    },
                    'put': {
                        'bid': put_data.get('bid', 'N/A'),
                        'ask': put_data.get('ask', 'N/A'),
                        'volume': put_data.get('volume', 0)
                    }
                }
    
    # 按执行价排序并打印
    for strike in sorted(options_by_strike.keys()):
        data = options_by_strike[strike]
        call = data['call']
        put = data['put']
        
        # 格式化数据，保留两位小数
        call_bid = f"{call['bid']:.2f}/{call['volume']}" if call['bid'] != 'N/A' else "N/A"
        call_ask = f"{call['ask']:.2f}/{call['volume']}" if call['ask'] != 'N/A' else "N/A"
        put_bid = f"{put['bid']:.2f}/{put['volume']}" if put['bid'] != 'N/A' else "N/A"
        put_ask = f"{put['ask']:.2f}/{put['volume']}" if put['ask'] != 'N/A' else "N/A"
        
        # 高亮显示接近当前价格的行
        if abs(strike - current_price) < 0.5:
            print("\033[7m", end='')  # 反转颜色作为高亮
            
        print(f"{call_bid:^15}{call_ask:^15} {strike:^10.2f} {put_bid:^15}{put_ask:^15}")
        
        if abs(strike - current_price) < 0.5:
            print("\033[0m", end='')  # 恢复正常颜色

def test_market_api(market):
    print("\n获取实时市场数据测试")
    print("=" * 50)

    # 测试获取股票报价
    print("\n1. 测试获取股票报价")
    symbols = ['AAPL', 'TSLA', 'GOOGL', 'AMD']
    current_price = None
    try:
        response = market.get_quote(symbols, resp_format='json')
        print(f"\n以下是{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}的实时报价：")
        if 'QuoteResponse' in response and 'QuoteData' in response['QuoteResponse']:
            for quote in response['QuoteResponse']['QuoteData']:
                if 'Product' in quote and 'All' in quote:
                    symbol = quote['Product']['symbol']
                    price = quote['All'].get('lastTrade', 'N/A')
                    volume = quote['All'].get('volume', 'N/A')
                    print(f"\n{symbol}:")
                    print(f"  当前价格: ${price}")
                    print(f"  成交量: {volume}")
                    print(f"  报价时间: {quote.get('dateTime', 'N/A')}")
                    if symbol == 'AMD':
                        current_price = float(price) if price != 'N/A' else None
    except Exception as e:
        print(f"获取股票报价时出错: {str(e)}")
        if "401" in str(e):
            print("令牌已过期，请删除 etrade_tokens.json 文件并重新运行程序进行授权。")
            return

    # 测试获取期权到期日
    print("\n2. 测试获取AMD期权到期日")
    try:
        response = market.get_option_expire_date('AMD', resp_format='json')
        print("\n可用的期权到期日：")
        if 'OptionExpireDateResponse' in response:
            expiry_dates = response['OptionExpireDateResponse'].get('ExpirationDate', [])
            for date in expiry_dates:
                print(f"  {date.get('year')}-{date.get('month')}-{date.get('day')} ({date.get('expiryType', 'STANDARD')})")
            
            # 使用第一个月度期权到期日来获取期权链
            monthly_expiry = None
            for date in expiry_dates:
                if date.get('expiryType') == 'MONTHLY':
                    monthly_expiry = date
                    break
            
            if monthly_expiry:
                # 测试获取期权链
                print("\n3. 测试获取AMD期权链")
                try:
                    expiry_date = datetime(
                        year=monthly_expiry['year'],
                        month=monthly_expiry['month'],
                        day=monthly_expiry['day']
                    )
                    response = market.get_option_chains(
                        'AMD',
                        expiry_date=expiry_date,
                        resp_format='json'
                    )
                    print(f"\nAMD期权链 (到期日: {expiry_date.strftime('%Y-%m-%d')}, 当前价格: ${current_price})")
                    if 'OptionChainResponse' in response:
                        pairs = response['OptionChainResponse'].get('OptionPair', [])
                        # 添加调试信息
                        print("\n调试信息 - 第一个期权对的数据结构：")
                        if pairs:
                            print(json.dumps(pairs[0], indent=2))
                        if pairs and current_price:
                            print_option_chain(pairs, current_price)
                        else:
                            print("未找到期权数据")
                except Exception as e:
                    print(f"获取期权链时出错: {str(e)}")
            else:
                print("\n未找到月度期权到期日，跳过期权链测试。")
    except Exception as e:
        print(f"获取期权到期日时出错: {str(e)}")

def main():
    # 加载配置
    config = load_config()
    
    print(f"\n正在连接E*TRADE API ({config['environment']}环境)...")
    
    # 获取市场实例
    market = get_market_instance(config)
    if market:
        # 测试市场API
        test_market_api(market)

if __name__ == "__main__":
    main() 