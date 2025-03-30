import pandas as pd
from datetime import datetime
import argparse
from etrade_options import get_market_instance, get_atm_option_price, get_stock_price

def evaluate_option_costs(portfolio_df, target_date):
    """评估期权成本和风险"""
    print(f"\n💰 期权成本评估报告")
    print(f"📅 评估日期：{target_date}")
    print("=" * 60)
    
    # 获取E*TRADE市场实例
    market = get_market_instance()
    if not market:
        print("无法获取E*TRADE市场实例，请检查配置和授权。")
        return
    
    # 初始化结果统计
    total_cost = 0
    option_results = []
    
    # 计算每个期权的成本和杠杆率
    for _, row in portfolio_df.iterrows():
        symbol = row['symbol']
        shares = row['shares']
        options = row.get('options', 0)
        
        if options == 0:
            continue
            
        # 获取当前价格
        current_price = get_stock_price(market, symbol)
        if current_price is None:
            print(f"\n⚠️ {symbol}: 无法获取当前价格，跳过此股票")
            continue
        
        # 获取期权价格
        option_price = get_atm_option_price(market, symbol, target_date)
        if option_price is None:
            print(f"\n⚠️ {symbol}: 无法获取期权价格，跳过此股票")
            continue
        
        # 计算期权成本
        option_cost = option_price * 100 * options
        total_cost += option_cost
        
        # 计算杠杆率
        # 杠杆率 = 控制的名义价值 / 期权成本
        # 名义价值 = 当前价格 * 100 * 期权数量
        nominal_value = current_price * 100 * options
        leverage = nominal_value / option_cost
        
        # 计算风险收益比
        # 风险收益比 = 期权成本 / 名义价值
        risk_reward = option_cost / nominal_value
        
        # 保存结果
        option_results.append({
            'symbol': symbol,
            'current_price': current_price,
            'option_price': option_price,
            'options': options,
            'option_cost': option_cost,
            'nominal_value': nominal_value,
            'leverage': leverage,
            'risk_reward': risk_reward
        })
    
    # 打印报告
    print("\n📊 期权成本分析")
    print("-" * 60)
    print(f"总期权成本：${total_cost:,.2f}")
    
    print("\n📈 杠杆率分析")
    print("-" * 60)
    for result in sorted(option_results, key=lambda x: x['leverage'], reverse=True):
        print(f"\n{result['symbol']}:")
        print(f"  当前价格: ${result['current_price']:.2f}")
        print(f"  期权价格: ${result['option_price']:.2f}")
        print(f"  期权数量: {result['options']}份")
        print(f"  期权成本: ${result['option_cost']:,.2f}")
        print(f"  名义价值: ${result['nominal_value']:,.2f}")
        print(f"  杠杆率: {result['leverage']:.2f}x")
        print(f"  风险收益比: {result['risk_reward']:.2%}")
    
    # 计算总体风险收益比
    total_nominal_value = sum(result['nominal_value'] for result in option_results)
    total_risk_reward = total_cost / total_nominal_value if total_nominal_value > 0 else 0
    
    print("\n📉 总体风险分析")
    print("-" * 60)
    print(f"总名义价值：${total_nominal_value:,.2f}")
    print(f"总期权成本：${total_cost:,.2f}")
    print(f"总体风险收益比：{total_risk_reward:.2%}")
    
    # 计算最大损失
    max_loss = total_cost  # 期权最大损失就是期权成本
    print(f"最大可能损失：${max_loss:,.2f}")

def main():
    parser = argparse.ArgumentParser(description='评估期权成本和风险')
    parser.add_argument('--portfolio', required=True, help='投资组合CSV文件路径')
    parser.add_argument('--date', required=True, help='评估日期 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    try:
        portfolio_df = pd.read_csv(args.portfolio)
        evaluate_option_costs(portfolio_df, args.date)
    except Exception as e:
        print(f"错误：{str(e)}")

if __name__ == '__main__':
    main() 