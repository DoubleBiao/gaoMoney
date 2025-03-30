import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import pandas_market_calendars as mcal
import warnings
import sys
from etrade_options import get_market_instance, get_stock_price

# Suppress all warnings
warnings.filterwarnings('ignore')

def get_current_market_date():
    """获取当前市场交易日"""
    nyse = mcal.get_calendar('NYSE')
    today = datetime.now().date()
    schedule = nyse.schedule(start_date=today - timedelta(days=10), end_date=today)
    return schedule.index[-1].date()

def validate_date(date_str):
    """验证日期格式和有效性"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        current_date = get_current_market_date()
        assert date >= current_date, f"目标日期 {date_str} 不能早于当前日期 {current_date}"
        return date
    except ValueError:
        print(f"错误：无效的日期格式 '{date_str}'。请使用 YYYY-MM-DD 格式。")
        sys.exit(1)
    except AssertionError as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

def get_target_expiry(symbol, target_date=None, weeks=None):
    """获取目标到期日"""
    try:
        market = get_market_instance()
        if not market:
            print(f"错误：无法获取E*TRADE市场实例。")
            sys.exit(1)
            
        # 获取当前日期
        current_date = get_current_market_date()
        
        # 如果指定了target_date，验证它
        if target_date:
            if isinstance(target_date, str):
                target = validate_date(target_date)
            else:
                target = target_date
        elif weeks:
            target = current_date + timedelta(weeks=weeks)
        else:
            print(f"错误：必须指定target_date或weeks参数。")
            sys.exit(1)
            
        # 获取可用的期权到期日
        dates = market.get_option_expire_date(symbol, resp_format='json')
        if 'OptionExpireDateResponse' not in dates:
            print(f"错误：无法获取{symbol}的期权到期日。")
            sys.exit(1)
            
        # 找到最接近目标日期的到期日
        closest_date = None
        min_diff = float('inf')
        
        for date in dates['OptionExpireDateResponse'].get('ExpirationDate', []):
            expiry = datetime(year=date['year'], month=date['month'], day=date['day']).date()
            if expiry >= target:
                diff = (expiry - target).days
                if diff < min_diff:
                    min_diff = diff
                    closest_date = expiry
                    
        if not closest_date:
            print(f"错误：找不到{symbol}在{target}之后的期权到期日。")
            sys.exit(1)
            
        return closest_date.strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"错误：获取目标到期日时发生错误：{str(e)}")
        sys.exit(1)

def get_option_range(symbol, expiry_date):
    """获取期权价格范围"""
    try:
        market = get_market_instance()
        if not market:
            print(f"错误：无法获取E*TRADE市场实例。")
            sys.exit(1)
            
        # 获取当前价格
        current_price = get_stock_price(market, symbol)
        if not current_price:
            print(f"错误：无法获取{symbol}的当前价格。")
            sys.exit(1)
            
        # 如果expiry_date是字符串，转换为datetime
        if isinstance(expiry_date, str):
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d')
            
        # 获取期权链
        response = market.get_option_chains(
            symbol,
            expiry_date=expiry_date,
            resp_format='json'
        )
        
        if 'OptionChainResponse' not in response:
            print(f"错误：无法获取{symbol}的期权链。")
            sys.exit(1)
            
        # 计算期权范围
        pairs = response['OptionChainResponse'].get('OptionPair', [])
        atm_pairs = []
        
        # 找到平值期权对
        for pair in pairs:
            if 'Call' in pair and 'Put' in pair:
                strike = float(pair['Call']['strikePrice'])
                # 找到最接近当前价格的行权价
                if abs(strike - current_price) <= 1:
                    # 获取看涨和看跌期权的中间价格
                    call_bid = float(pair['Call'].get('bid', 0))
                    call_ask = float(pair['Call'].get('ask', 0))
                    put_bid = float(pair['Put'].get('bid', 0))
                    put_ask = float(pair['Put'].get('ask', 0))
                    
                    # 使用中间价格
                    call_price = (call_bid + call_ask) / 2 if call_bid > 0 and call_ask > 0 else 0
                    put_price = (put_bid + put_ask) / 2 if put_bid > 0 and put_ask > 0 else 0
                    
                    # 计算跨式期权组合的价格
                    straddle_price = call_price + put_price
                    
                    print(f"平值期权对 - 行权价: {strike}, Call价格: {call_price:.2f}, Put价格: {put_price:.2f}, 跨式组合价格: {straddle_price:.2f}")
                    
                    atm_pairs.append({
                        'strike': strike,
                        'straddle_price': straddle_price
                    })
        
        if not atm_pairs:
            print(f"错误：无法获取{symbol}的平值期权数据。")
            sys.exit(1)
            
        # 计算平均跨式期权组合价格
        avg_straddle_price = sum(pair['straddle_price'] for pair in atm_pairs) / len(atm_pairs)
        
        # 计算预期波动范围（使用85%的跨式期权组合价格）
        expected_move = avg_straddle_price * 0.85
        
        # 计算涨跌幅
        rate = (expected_move / current_price) * 100
        
        return [current_price - expected_move, current_price + expected_move, rate, rate]
        
    except Exception as e:
        print(f"错误：计算期权范围时发生错误：{str(e)}")
        sys.exit(1)

def predict_drop_rate(symbol, target_date=None, weeks=None):
    """预测下跌率"""
    try:
        market = get_market_instance()
        if not market:
            print(f"错误：无法获取E*TRADE市场实例。")
            sys.exit(1)
            
        # 获取目标到期日
        expiry_date = get_target_expiry(symbol, target_date, weeks)
        
        # 获取当前价格
        current_price = get_stock_price(market, symbol)
        if current_price is None:
            print(f"错误：无法获取 {symbol} 的当前价格。")
            sys.exit(1)
            
        # 获取期权链
        option_chain = market.get_option_chain(
            symbol,
            expiry_date.strftime('%Y%m%d'),
            option_category='ALL',
            chain_type='PUTS'
        )
        
        if not option_chain:
            print(f"错误：无法获取 {symbol} 的期权链。")
            sys.exit(1)
            
        # 计算下跌率
        strike_prices = [float(opt['strikePrice']) for opt in option_chain]
        min_strike = min(strike_prices)
        drop_rate = ((current_price - min_strike) / current_price) * 100
        
        return {
            'drop_rate': drop_rate,
            'min_strike': min_strike,
            'current_price': current_price
        }
        
    except Exception as e:
        print(f"错误：预测下跌率时发生错误：{str(e)}")
        sys.exit(1)

def print_prediction(result):
    """打印预测结果"""
    print(f"\n{result['symbol']} 预测结果（到 {result['expiry']}）")
    print("=" * 50)
    print(f"当前价格：${result['current_price']:.2f}")
    print(f"到期天数：{result['days_to_expiry']}天")
    print(f"波动率：{result['volatility']*100:.1f}%")
    print(f"价格范围：${result['lower_bound']:.2f} - ${result['upper_bound']:.2f}")
    print(f"预期下跌：{result['drop_rate']:.1f}%")
    print(f"平值期权数量：{result['atm_pairs_count']}")
    print(f"总未平仓量：{result['total_oi']:,}")

def main():
    parser = argparse.ArgumentParser(description='预测股票期权价格范围')
    parser.add_argument('--symbol', required=True, help='股票代码')
    parser.add_argument('--date', help='目标日期 (YYYY-MM-DD)')
    parser.add_argument('--weeks', type=int, help='目标周数')
    
    args = parser.parse_args()
    
    result = predict_drop_rate(args.symbol, args.date, args.weeks)
    print_prediction(result)

if __name__ == '__main__':
    main() 