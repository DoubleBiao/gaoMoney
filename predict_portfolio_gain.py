import pandas as pd
from datetime import datetime
import argparse
from option_range import get_option_range, get_target_expiry
import pandas_market_calendars as mcal
import numpy as np
from etrade_options import get_market_instance, check_option_availability, get_atm_option_price, get_stock_price

def check_etrade_option_availability(market, symbol, target_date):
    """检查指定日期是否有可用的期权"""
    return check_option_availability(market, symbol, target_date)

def get_etrade_atm_option_price(market, symbol, target_date):
    """获取平值期权的价格"""
    return get_atm_option_price(market, symbol, target_date)

def predict_portfolio_gain(portfolio_df, target_date):
    """预测投资组合在上涨情况下的期权收益"""
    print(f"\n投资组合收益预测（到 {target_date}）")
    print("=" * 50)
    
    # 获取E*TRADE市场实例
    market = get_market_instance()
    if not market:
        print("无法获取E*TRADE市场实例，请检查配置和授权。")
        return
    
    # 获取基准指数的期权范围
    qqq_range = get_option_range('QQQ', target_date)
    soxx_range = get_option_range('SOXX', target_date)
    
    total_investment = 0
    total_gain = 0
    
    print("\n一、总体收益概览")
    print("-" * 20)
    
    # 计算每个股票的收益
    for _, row in portfolio_df.iterrows():
        symbol = row['symbol']
        shares = row['shares']
        benchmark = row['benchmark']
        adjustment = row['adjustment']
        call_options = row['call_options']
        
        if call_options == 0:
            continue
            
        # 获取当前价格和期权价格
        current_price = get_stock_price(market, symbol)
        if current_price is None:
            print(f"\n{symbol}:")
            print("  无法获取当前价格，跳过此股票")
            continue
            
        option_price = get_etrade_atm_option_price(market, symbol, target_date)
        if option_price is None:
            print(f"\n{symbol}:")
            print("  无法获取期权价格，跳过此股票")
            continue
        
        # 获取基准指数的上涨幅度
        if benchmark == 'QQQ':
            benchmark_range = qqq_range
            benchmark_rise = (benchmark_range[1] - benchmark_range[0]) / benchmark_range[0]
        else:  # SOXX
            benchmark_range = soxx_range
            benchmark_rise = (benchmark_range[1] - benchmark_range[0]) / benchmark_range[0]
        
        # 使用默认beta值1.0，因为E*TRADE API可能不提供beta值
        beta = 1.0
        expected_rise = benchmark_rise * beta
        
        # 计算期权收益
        option_value = current_price * (1 + expected_rise)
        option_gain = (option_value - current_price) * 100 * call_options  # 每份期权代表100股
        
        total_investment += option_price * 100 * call_options
        total_gain += option_gain
        
        print(f"\n{symbol}:")
        print(f"  1. 期权情况:")
        print(f"     - 期权数量: {call_options}份")
        print(f"     - 期权价格: ${option_price:.2f}")
        print(f"     - 投资金额: ${option_price * 100 * call_options:.2f}")
        print(f"  2. 收益分析:")
        print(f"     - Beta值: {beta:.2f}")
        print(f"     - 基准指数: {benchmark}")
        print(f"     - 基准上涨: {benchmark_rise*100:.1f}%")
        print(f"     - 预期上涨: {expected_rise*100:.1f}%")
        print(f"     - 预期价格: ${option_value:.2f}")
        print(f"     - 预期收益: ${option_gain:.2f}")
    
    print("\n二、总体收益分析")
    print("-" * 20)
    print(f"总投资金额：${total_investment:.2f}")
    print(f"预期总收益：${total_gain:.2f} ({total_gain/total_investment*100:.1f}%)")

def main():
    parser = argparse.ArgumentParser(description='预测投资组合在上涨情况下的期权收益')
    parser.add_argument('--portfolio', required=True, help='投资组合配置文件路径')
    parser.add_argument('--date', required=True, help='预测目标日期 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # 读取投资组合配置
    portfolio_df = pd.read_csv(args.portfolio)
    
    # 获取E*TRADE市场实例
    market = get_market_instance()
    if not market:
        print("无法获取E*TRADE市场实例，请检查配置和授权。")
        return
    
    # 检查期权可用性
    assert check_etrade_option_availability(market, 'QQQ', args.date), f"QQQ 在 {args.date} 没有可用的期权"
    assert check_etrade_option_availability(market, 'SOXX', args.date), f"SOXX 在 {args.date} 没有可用的期权"
    
    # 运行预测
    predict_portfolio_gain(portfolio_df, args.date)

if __name__ == '__main__':
    main() 