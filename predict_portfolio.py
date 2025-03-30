import pandas as pd
from datetime import datetime
import argparse
from option_range import get_option_range, get_target_expiry, predict_drop_rate
from etrade_options import get_market_instance, check_option_availability, get_atm_option_price, get_stock_price

def predict_portfolio_scenarios(portfolio_df, target_date):
    """预测投资组合在不同市场情况下的表现"""
    print(f"\n投资组合策略评估报告")
    print(f"评估日期：{target_date}")
    print("=" * 60)
    
    # 获取E*TRADE市场实例
    market = get_market_instance()
    if not market:
        print("无法获取E*TRADE市场实例，请检查配置和授权。")
        return
    
    # 获取基准指数的涨跌幅预测
    qqq_range = get_option_range('QQQ', target_date)
    soxx_range = get_option_range('SOXX', target_date)
    
    # 打印基准指数预测
    print("\n基准指数预测")
    print("-" * 60)
    print(f"QQQ:")
    print(f"  预期涨幅：{qqq_range[2]:.1f}%")
    print(f"  预期跌幅：{qqq_range[3]:.1f}%")
    print(f"SOXX:")
    print(f"  预期涨幅：{soxx_range[2]:.1f}%")
    print(f"  预期跌幅：{soxx_range[3]:.1f}%")
    
    # 初始化结果统计
    total_opportunity_cost = 0  # 市场上涨时的机会成本
    total_price_difference = 0  # 市场下跌时的价格差收益
    total_option_cost = 0      # 期权总成本
    total_option_gain = 0      # 期权总收益
    
    # 计算每个股票的策略效果
    for _, row in portfolio_df.iterrows():
        symbol = row['symbol']
        shares = row['shares']
        benchmark = row['benchmark']
        adjustment = row['adjustment']
        options = row.get('options', 0)
        
        # 获取当前价格
        current_price = get_stock_price(market, symbol)
        if current_price is None:
            print(f"\n{symbol}: 无法获取当前价格，跳过此股票")
            continue
        
        # 计算卖出的股票数量
        sold_shares = shares * (1 - adjustment)
        
        # 计算市场上涨时的机会成本
        if benchmark == 'QQQ':
            benchmark_rise = qqq_range[2] / 100
        else:  # SOXX
            benchmark_rise = soxx_range[2] / 100
        
        opportunity_cost = sold_shares * current_price * benchmark_rise
        
        # 计算市场下跌时的价格差收益
        benchmark_drop = soxx_range[3] if benchmark == 'SOXX' else qqq_range[3]
        price_difference = sold_shares * current_price * (benchmark_drop / 100)
        
        # 计算期权成本和收益
        option_cost = 0
        option_gain = 0
        if options > 0:
            option_price = get_atm_option_price(market, symbol, target_date)
            if option_price is not None:
                option_cost = option_price * 100 * options
                option_gain = current_price * benchmark_rise * 100 * options
        
        # 累加总成本
        total_opportunity_cost += opportunity_cost
        total_price_difference += price_difference
        total_option_cost += option_cost
        total_option_gain += option_gain
        
        # 打印个股分析
        print(f"\n{symbol}:")
        print(f"  当前价格: ${current_price:.2f}")
        print(f"  卖出数量: {sold_shares:.1f}股")
        print(f"  基准指数: {benchmark}")
        print(f"  预期涨幅: {benchmark_rise*100:.1f}%")
        print(f"  预期跌幅: {benchmark_drop:.1f}%")
        print(f"  市场上涨时:")
        print(f"    - 机会成本: ${opportunity_cost:,.2f}")
        print(f"    - 期权收益: ${option_gain:,.2f}")
        print(f"    - 净损失: ${opportunity_cost - option_gain:,.2f}")
        print(f"  市场下跌时:")
        print(f"    - 价格差收益: ${price_difference:,.2f}")
        print(f"    - 期权损失: ${option_cost:,.2f}")
        print(f"    - 净收益: ${price_difference - option_cost:,.2f}")
    
    # 打印总体分析
    print("\n市场上涨情景分析")
    print("-" * 60)
    print(f"总机会成本：${total_opportunity_cost:,.2f}")
    print(f"总期权收益：${total_option_gain:,.2f}")
    print(f"净损失：${total_opportunity_cost - total_option_gain:,.2f}")
    
    print("\n市场下跌情景分析")
    print("-" * 60)
    print(f"总价格差收益：${total_price_difference:,.2f}")
    print(f"总期权损失：${total_option_cost:,.2f}")
    print(f"净收益：${total_price_difference - total_option_cost:,.2f}")

def main():
    parser = argparse.ArgumentParser(description='评估投资组合策略在不同市场情况下的表现')
    parser.add_argument('--portfolio', required=True, help='投资组合CSV文件路径')
    parser.add_argument('--date', required=True, help='评估日期 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    try:
        portfolio_df = pd.read_csv(args.portfolio)
        predict_portfolio_scenarios(portfolio_df, args.date)
    except Exception as e:
        print(f"错误：{str(e)}")

if __name__ == '__main__':
    main() 