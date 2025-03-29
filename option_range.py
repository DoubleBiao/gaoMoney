import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import pandas_market_calendars as mcal
import warnings
import sys

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

def get_target_expiry(ticker, target_date=None, weeks=None):
    """获取目标到期日"""
    try:
        stock = yf.Ticker(ticker)
        # 验证股票是否存在
        if not stock.info:
            print(f"错误：股票代码 '{ticker}' 不存在或无法获取数据。")
            sys.exit(1)
            
        expiry_dates = stock.options
        if not expiry_dates:
            print(f"错误：股票 '{ticker}' 没有可用的期权数据。")
            sys.exit(1)
        
        if target_date:
            target = validate_date(target_date)
            # 对所有股票，如果指定日期没有期权，直接断言失败
            if target_date not in expiry_dates:
                print(f"错误：{ticker} 在 {target_date} 没有可用的期权。")
                print(f"{ticker} 的可用期权日期：{', '.join(sorted(expiry_dates))}")
                sys.exit(1)
            return target_date
        elif weeks:
            current_date = get_current_market_date()
            target = current_date + timedelta(weeks=weeks)
            # 找到大于等于目标日期的最近期权日期
            valid_dates = [d for d in expiry_dates if datetime.strptime(d, '%Y-%m-%d').date() >= target]
            if not valid_dates:
                print(f"错误：{ticker} 没有晚于目标日期 {target} 的期权。")
                print(f"{ticker} 的可用期权日期：{', '.join(sorted(expiry_dates))}")
                sys.exit(1)
            return min(valid_dates)
        else:
            current_date = get_current_market_date()
            target = current_date + timedelta(weeks=3)
            # 找到大于等于目标日期的最近期权日期
            valid_dates = [d for d in expiry_dates if datetime.strptime(d, '%Y-%m-%d').date() >= target]
            if not valid_dates:
                print(f"错误：{ticker} 没有晚于目标日期 {target} 的期权。")
                print(f"{ticker} 的可用期权日期：{', '.join(sorted(expiry_dates))}")
                sys.exit(1)
            return min(valid_dates)
    except Exception as e:
        print(f"错误：获取期权日期时发生错误：{str(e)}")
        sys.exit(1)

def predict_drop_rate(symbol, target_date=None, weeks=None):
    """预测股票下跌率"""
    try:
        stock = yf.Ticker(symbol)
        if not stock.info or 'regularMarketPrice' not in stock.info:
            print(f"错误：无法获取股票 '{symbol}' 的当前价格。")
            sys.exit(1)
            
        current_price = stock.info['regularMarketPrice']
        expiry = get_target_expiry(symbol, target_date, weeks)
        
        # 获取期权链
        options = stock.option_chain(expiry)
        if not options:
            print(f"错误：无法获取股票 '{symbol}' 的期权链数据。")
            sys.exit(1)
        
        calls = options.calls
        puts = options.puts
        
        # 计算天数
        current_date = get_current_market_date()
        if weeks:
            target_date = current_date + timedelta(weeks=weeks)
            days_to_expiry = (target_date - current_date).days
        else:
            days_to_expiry = (datetime.strptime(expiry, '%Y-%m-%d').date() - current_date).days
        
        # 使用平值期权的隐含波动率
        # 获取接近当前价格的多个期权
        calls = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:3]]
        puts = puts.iloc[(puts['strike'] - current_price).abs().argsort()[:3]]
        
        # 过滤掉无效的隐含波动率
        valid_call_ivs = calls[calls['impliedVolatility'] > 0]['impliedVolatility'].tolist()
        valid_put_ivs = puts[puts['impliedVolatility'] > 0]['impliedVolatility'].tolist()
        
        if not valid_call_ivs or not valid_put_ivs:
            print(f"错误：无法获取股票 '{symbol}' 的有效隐含波动率数据。")
            sys.exit(1)
        
        # 使用有效隐含波动率的平均值
        avg_iv = (sum(valid_call_ivs) / len(valid_call_ivs) + sum(valid_put_ivs) / len(valid_put_ivs)) / 2
        
        # 计算80%概率的下跌区间，考虑时间跨度
        sigma = avg_iv * np.sqrt(days_to_expiry/252)  # 年化调整
        lower_bound = current_price * np.exp(-sigma * 0.842)  # 使用0.842作为80%置信区间的z值
        drop_rate = (lower_bound/current_price - 1) * 100
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'expiry_date': expiry,
            'days_to_expiry': days_to_expiry,
            'implied_volatility': avg_iv,
            'drop_rate': drop_rate,
            'lower_bound': lower_bound
        }
    except Exception as e:
        print(f"错误：预测下跌率时发生错误：{str(e)}")
        sys.exit(1)

def print_prediction(result):
    """打印预测结果"""
    print(f"\n{result['symbol']} 下跌率预测（到 {result['expiry_date']}）：")
    print(f"当前价格：${result['current_price']:.2f}")
    print(f"剩余天数：{result['days_to_expiry']}天")
    print(f"隐含波动率：{result['implied_volatility']*100:.1f}%")
    print(f"预期最大下跌：{result['drop_rate']:.1f}%")
    print(f"预期最低价格：${result['lower_bound']:.2f}")

def main():
    parser = argparse.ArgumentParser(description='预测股票下跌率')
    parser.add_argument('--symbol', type=str, help='股票代码', required=True)
    parser.add_argument('--weeks', type=int, help='预测周数', default=None)
    parser.add_argument('--date', type=str, help='目标日期 (YYYY-MM-DD)', default=None)
    args = parser.parse_args()
    
    result = predict_drop_rate(args.symbol, args.date, args.weeks)
    print_prediction(result)

if __name__ == "__main__":
    main() 