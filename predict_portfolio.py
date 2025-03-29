import pandas as pd
from datetime import datetime
import argparse
from option_range import get_option_range, get_target_expiry, predict_drop_rate
from etrade_options import get_market_instance, check_option_availability, get_atm_option_price, get_stock_price

def predict_portfolio_scenarios(portfolio_df, target_date):
    """预测投资组合在不同市场情况下的表现"""
    print(f"\n📊 投资组合情景分析报告")
    print(f"📅 预测日期：{target_date}")
    print("=" * 60)
    
    # 获取E*TRADE市场实例
    market = get_market_instance()
    if not market:
        print("无法获取E*TRADE市场实例，请检查配置和授权。")
        return
    
    # 获取基准指数的涨跌幅预测
    qqq_range = get_option_range('QQQ', target_date)
    soxx_range = get_option_range('SOXX', target_date)
    qqq_drop = predict_drop_rate('QQQ', target_date)
    soxx_drop = predict_drop_rate('SOXX', target_date)
    
    # 初始化结果统计
    total_investment = 0
    total_gain = 0
    total_loss = 0
    stock_results = []
    
    # 计算每个股票的预期收益和损失
    for _, row in portfolio_df.iterrows():
        symbol = row['symbol']
        shares = row['shares']
        benchmark = row['benchmark']
        adjustment = row['adjustment']
        options = row.get('options', 0)
        
        # 获取当前价格
        current_price = get_stock_price(market, symbol)
        if current_price is None:
            print(f"\n⚠️ {symbol}: 无法获取当前价格，跳过此股票")
            continue
        
        # 计算股票部分的预期损失
        benchmark_drop = soxx_drop['drop_rate'] if benchmark == 'SOXX' else qqq_drop['drop_rate']
        adjusted_shares = shares * adjustment
        stock_value = current_price * adjusted_shares
        expected_loss = stock_value * (benchmark_drop / 100)
        
        # 如果有期权，计算期权部分的预期收益
        option_investment = 0
        option_gain = 0
        if options > 0:
            option_price = get_atm_option_price(market, symbol, target_date)
            if option_price is not None:
                option_investment = option_price * 100 * options
                total_investment += option_investment
                
                # 计算期权收益
                if benchmark == 'QQQ':
                    benchmark_rise = (qqq_range[1] - qqq_range[0]) / qqq_range[0]
                else:  # SOXX
                    benchmark_rise = (soxx_range[1] - soxx_range[0]) / soxx_range[0]
                
                expected_rise = benchmark_rise
                option_value = current_price * (1 + expected_rise)
                option_gain = (option_value - current_price) * 100 * options
                total_gain += option_gain
        
        total_loss += expected_loss
        
        # 保存个股结果
        stock_results.append({
            'symbol': symbol,
            'current_price': current_price,
            'shares': shares,
            'adjusted_shares': adjusted_shares,
            'stock_value': stock_value,
            'benchmark': benchmark,
            'expected_loss': expected_loss,
            'expected_loss_pct': benchmark_drop,
            'options': options,
            'option_investment': option_investment,
            'option_gain': option_gain,
            'option_gain_pct': (option_gain / option_investment * 100) if option_investment > 0 else 0
        })
    
    # 打印报告
    print("\n📈 乐观情景（市场上涨）")
    print("-" * 60)
    print(f"总投资金额（期权）：${total_investment:,.2f}")
    if total_investment > 0:
        print(f"预期总收益：${total_gain:,.2f} ({total_gain/total_investment*100:.1f}% ROI)")
    else:
        print("预期总收益：$0.00 (0.0% ROI)")
    print(f"\n基准指数预期涨幅：")
    print(f"QQQ: {(qqq_range[1] - qqq_range[0]) / qqq_range[0] * 100:.1f}%")
    print(f"SOXX: {(soxx_range[1] - soxx_range[0]) / soxx_range[0] * 100:.1f}%")
    
    print("\n📉 悲观情景（市场下跌）")
    print("-" * 60)
    total_stock_value = sum(result['stock_value'] for result in stock_results)
    print(f"总持仓市值：${total_stock_value:,.2f}")
    print(f"预期总损失：${abs(total_loss):,.2f} ({abs(total_loss/total_stock_value*100):.1f}% 跌幅)")
    print(f"\n基准指数预期跌幅：")
    print(f"QQQ: {qqq_drop['drop_rate']:.1f}%")
    print(f"SOXX: {soxx_drop['drop_rate']:.1f}%")
    
    print("\n📊 个股分析")
    print("-" * 60)
    
    for result in sorted(stock_results, key=lambda x: abs(x['option_gain'] if x['options'] > 0 else x['expected_loss']), reverse=True):
        print(f"\n{result['symbol']}:")
        print(f"  当前价格: ${result['current_price']:.2f}")
        print(f"  持股数量: {result['shares']}股 (调整后: {result['adjusted_shares']:.1f}股)")
        print(f"  持仓市值: ${result['stock_value']:,.2f}")
        print(f"  基准指数: {result['benchmark']}")
        
        if result['options'] > 0:
            print(f"  期权策略:")
            print(f"    - 期权数量: {result['options']}份")
            print(f"    - 投资金额: ${result['option_investment']:,.2f}")
            print(f"    - 预期收益: ${result['option_gain']:,.2f} ({result['option_gain_pct']:.1f}%)")
        
        print(f"  下跌风险:")
        print(f"    - 预期跌幅: {result['expected_loss_pct']:.1f}%")
        print(f"    - 预期损失: ${abs(result['expected_loss']):,.2f}")

def main():
    parser = argparse.ArgumentParser(description='预测投资组合在不同市场情况下的表现')
    parser.add_argument('--portfolio', required=True, help='投资组合配置文件路径')
    parser.add_argument('--date', required=True, help='预测目标日期 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # 读取投资组合配置
    portfolio_df = pd.read_csv(args.portfolio)
    
    # 运行预测
    predict_portfolio_scenarios(portfolio_df, args.date)

if __name__ == '__main__':
    main() 