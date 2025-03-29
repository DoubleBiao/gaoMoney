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
            target = validate_date(target_date)
        elif weeks:
            target = current_date + timedelta(weeks=weeks)
        else:
            target = current_date + timedelta(weeks=3)
            
        # 获取期权到期日列表
        response = market.get_option_expire_dates(symbol, resp_format='json')
        
        if 'ExpirationDate' not in response:
            print(f"错误：股票 '{symbol}' 没有可用的期权数据。")
            sys.exit(1)
            
        expiry_dates = []
        for date_info in response['ExpirationDate']:
            expiry_date = datetime.strptime(date_info['date'], '%Y%m%d').strftime('%Y-%m-%d')
            expiry_dates.append(expiry_date)
            
        if not expiry_dates:
            print(f"错误：股票 '{symbol}' 没有可用的期权。")
            sys.exit(1)
            
        if target_date:
            if target_date not in expiry_dates:
                print(f"错误：{symbol} 在 {target_date} 没有可用的期权。")
                print(f"{symbol} 的可用期权日期：{', '.join(sorted(expiry_dates))}")
                sys.exit(1)
            return target_date
        else:
            # 找到大于等于目标日期的最近期权日期
            valid_dates = [d for d in expiry_dates if datetime.strptime(d, '%Y-%m-%d').date() >= target]
            if not valid_dates:
                print(f"错误：{symbol} 没有晚于目标日期 {target} 的期权。")
                print(f"{symbol} 的可用期权日期：{', '.join(sorted(expiry_dates))}")
                sys.exit(1)
            return min(valid_dates)
            
    except Exception as e:
        print(f"错误：获取期权日期时发生错误：{str(e)}")
        sys.exit(1)

def get_option_range(symbol, target_date):
    """获取期权的价格范围"""
    try:
        market = get_market_instance()
        if not market:
            print(f"错误：无法获取E*TRADE市场实例。")
            sys.exit(1)
            
        current_price = get_stock_price(market, symbol)
        if current_price is None:
            print(f"错误：无法获取股票 '{symbol}' 的当前价格。")
            sys.exit(1)
            
        # 转换目标日期为datetime对象
        target_date = datetime.strptime(target_date, '%Y-%m-%d')
        
        # 获取期权链
        response = market.get_option_chains(
            symbol,
            expiry_date=target_date,
            resp_format='json'
        )
        
        if 'OptionChainResponse' not in response:
            print(f"错误：无法获取股票 '{symbol}' 的期权链数据。")
            sys.exit(1)
            
        pairs = response['OptionChainResponse'].get('OptionPair', [])
        
        # 找到平值期权附近的期权对
        atm_pairs = []
        for pair in pairs:
            if 'Call' in pair and 'Put' in pair:
                strike = float(pair['Call']['strikePrice'])
                # 只关注当前价格±5%范围内的期权
                if abs(strike - current_price) <= current_price * 0.05:
                    atm_pairs.append(pair)
        
        if not atm_pairs:
            print(f"错误：无法找到股票 '{symbol}' 的平值期权。")
            sys.exit(1)
        
        # 计算天数
        days_to_expiry = (target_date.date() - get_current_market_date()).days
        
        # 计算平值期权附近的加权平均IV
        total_oi = 0
        weighted_iv = 0
        
        for pair in atm_pairs:
            # 计算未平仓量
            call_oi = int(pair['Call']['openInterest'])
            put_oi = int(pair['Put']['openInterest'])
            pair_oi = call_oi + put_oi
            
            # 更新总未平仓量
            total_oi += pair_oi
            
            # 计算加权隐含波动率
            call_iv = float(pair['Call']['OptionGreeks']['iv'])
            put_iv = float(pair['Put']['OptionGreeks']['iv'])
            pair_iv = (call_iv + put_iv) / 2
            weighted_iv += pair_iv * pair_oi
        
        # 使用加权平均的隐含波动率
        volatility = weighted_iv / total_oi if total_oi > 0 else 0
        
        # 使用1个标准差（68%置信区间）
        std_dev = current_price * volatility * np.sqrt(days_to_expiry / 365)
        lower_bound = current_price - std_dev
        upper_bound = current_price + std_dev
        
        return (lower_bound, upper_bound)
    except Exception as e:
        print(f"错误：计算期权范围时发生错误：{str(e)}")
        sys.exit(1)

def predict_drop_rate(symbol, target_date=None, weeks=None):
    """预测股票下跌率"""
    try:
        market = get_market_instance()
        if not market:
            print(f"错误：无法获取E*TRADE市场实例。")
            sys.exit(1)
            
        current_price = get_stock_price(market, symbol)
        if current_price is None:
            print(f"错误：无法获取股票 '{symbol}' 的当前价格。")
            sys.exit(1)
        
        # 如果没有指定日期，使用默认的3周
        if target_date is None:
            if weeks is None:
                weeks = 3
            target_date = (datetime.now() + timedelta(weeks=weeks)).strftime('%Y-%m-%d')
        
        # 转换目标日期为datetime对象
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d')
        
        # 获取期权链
        response = market.get_option_chains(
            symbol,
            expiry_date=target_date_obj,
            resp_format='json'
        )
        
        if 'OptionChainResponse' not in response:
            print(f"错误：无法获取股票 '{symbol}' 的期权链数据。")
            sys.exit(1)
            
        pairs = response['OptionChainResponse'].get('OptionPair', [])
        
        # 找到平值期权附近的期权对
        atm_pairs = []
        for pair in pairs:
            if 'Call' in pair and 'Put' in pair:
                strike = float(pair['Call']['strikePrice'])
                # 只关注当前价格±5%范围内的期权
                if abs(strike - current_price) <= current_price * 0.05:
                    atm_pairs.append(pair)
        
        if not atm_pairs:
            print(f"错误：无法找到股票 '{symbol}' 的平值期权。")
            sys.exit(1)
        
        # 计算天数
        days_to_expiry = (target_date_obj.date() - get_current_market_date()).days
        
        # 计算平值期权附近的加权平均IV
        total_oi = 0
        weighted_iv = 0
        
        for pair in atm_pairs:
            # 计算未平仓量
            call_oi = int(pair['Call']['openInterest'])
            put_oi = int(pair['Put']['openInterest'])
            pair_oi = call_oi + put_oi
            
            # 更新总未平仓量
            total_oi += pair_oi
            
            # 计算加权隐含波动率
            call_iv = float(pair['Call']['OptionGreeks']['iv'])
            put_iv = float(pair['Put']['OptionGreeks']['iv'])
            pair_iv = (call_iv + put_iv) / 2
            weighted_iv += pair_iv * pair_oi
        
        # 使用加权平均的隐含波动率
        volatility = weighted_iv / total_oi if total_oi > 0 else 0
        
        # 使用1个标准差（68%置信区间）
        std_dev = current_price * volatility * np.sqrt(days_to_expiry / 365)
        lower_bound = current_price - std_dev
        upper_bound = current_price + std_dev
        
        # 计算下跌率（使用百分比表示）
        drop_rate = ((current_price - lower_bound) / current_price) * 100
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'expiry': target_date,
            'days_to_expiry': days_to_expiry,
            'volatility': volatility,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'drop_rate': drop_rate,
            'total_oi': total_oi,
            'atm_pairs_count': len(atm_pairs)
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