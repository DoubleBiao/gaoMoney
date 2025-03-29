import argparse
import yfinance as yf
from datetime import datetime
from option_range import predict_drop_rate
from stock_ratio import get_beta
import pandas as pd

def check_option_availability(symbol, target_date):
    """检查指定日期是否有期权"""
    stock = yf.Ticker(symbol)
    expiry_dates = stock.options
    return target_date in expiry_dates

def predict_portfolio_loss(portfolio_df, target_date):
    """预测投资组合损失"""
    # 检查基准股票的期权可用性
    assert check_option_availability('QQQ', target_date), f"QQQ 在 {target_date} 没有可用的期权"
    assert check_option_availability('SOXX', target_date), f"SOXX 在 {target_date} 没有可用的期权"
    
    # 获取基准股票的下跌率
    qqq_drop = predict_drop_rate('QQQ', target_date)
    soxx_drop = predict_drop_rate('SOXX', target_date)
    
    # 获取每只股票的beta值和创建投资组合字典
    portfolio_with_beta = {}
    for _, row in portfolio_df.iterrows():
        symbol = row['symbol']
        beta = get_beta(symbol)
        assert beta is not None, f"无法获取 {symbol} 的beta值"
        portfolio_with_beta[symbol] = {
            'shares': row['shares'],
            'beta': beta,
            'benchmark': row['benchmark'],
            'adjustment': row['adjustment']
        }
    
    # 获取实时价格
    total_value = 0
    for symbol, data in portfolio_with_beta.items():
        stock = yf.Ticker(symbol)
        current_price = stock.info['regularMarketPrice']
        assert current_price is not None, f"无法获取 {symbol} 的当前价格"
        data['current_price'] = current_price
        # 应用调整系数
        adjusted_shares = data['shares'] * data['adjustment']
        data['adjusted_shares'] = adjusted_shares
        data['cost_basis'] = current_price * adjusted_shares
        total_value += data['cost_basis']
    
    # 计算预期损失
    total_loss = 0
    for symbol, data in portfolio_with_beta.items():
        # 根据基准选择下跌率
        benchmark_drop = soxx_drop['drop_rate'] if data['benchmark'] == 'SOXX' else qqq_drop['drop_rate']
        
        # 计算预期下跌率
        expected_drop = benchmark_drop * data['beta']
        expected_price = data['current_price'] * (1 + expected_drop/100)
        expected_loss = (expected_price - data['current_price']) * data['adjusted_shares']
        
        data['expected_drop'] = expected_drop
        data['expected_price'] = expected_price
        data['expected_loss'] = expected_loss
        data['benchmark_drop'] = benchmark_drop
        total_loss += expected_loss
    
    # 打印结果
    print(f"\n投资组合风险预测（到 {target_date}）")
    print("=" * 50)
    
    print("\n一、总体风险概览")
    print("-" * 20)
    print(f"总投资金额：${total_value:,.2f}")
    print(f"预期总损失：${total_loss:,.2f} ({total_loss/total_value*100:.1f}%)")
    
    print("\n二、损失贡献分布")
    print("-" * 20)
    print(f"{'股票':<6} {'现价':>10} -> {'预测价':>10} {'预期跌幅':>10} {'预期损失':>12} {'损失占比':>10}")
    print("-" * 65)
    
    sorted_stocks = sorted(portfolio_with_beta.items(), key=lambda x: abs(x[1]['expected_loss']), reverse=True)
    for symbol, data in sorted_stocks:
        print(f"{symbol:<6} ${data['current_price']:>9.2f} -> ${data['expected_price']:>9.2f} "
              f"{data['expected_drop']:>9.1f}% ${data['expected_loss']:>11.2f} "
              f"{data['expected_loss']/total_loss*100:>9.1f}%")
    
    print("\n三、个股详细分析")
    print("-" * 20)
    
    for symbol, data in sorted_stocks:
        print(f"\n{symbol}:")
        print("  1. 持仓情况:")
        print(f"     - 持股数量: {data['shares']}股")
        print(f"     - 调整系数: {data['adjustment']:.2f}")
        print(f"     - 调整后股数: {data['adjusted_shares']:.1f}股")
        print(f"     - 成本价: ${data['current_price']:.2f}")
        print(f"     - 现价: ${data['current_price']:.2f}")
        print(f"     - 成本基础: ${data['cost_basis']:,.2f}")
        print(f"     - 当前市值: ${data['cost_basis']:,.2f}")
        print(f"     - 未实现盈亏: ${0:,.2f} (0.0%)")
        print("  2. 风险分析:")
        print(f"     - Beta值: {data['beta']:.2f}")
        print(f"     - 基准指数: {data['benchmark']}")
        print(f"     - 基准下跌: {data['benchmark_drop']:.1f}%")
        print(f"     - 预期下跌: {data['expected_drop']:.1f}%")
        print(f"     - 预期价格: ${data['expected_price']:.2f}")
        print(f"     - 预期损失: ${data['expected_loss']:,.2f}")
        print(f"     - 损失贡献: {data['expected_loss']/total_loss*100:.1f}%")

def main():
    parser = argparse.ArgumentParser(description='预测投资组合损失')
    parser.add_argument('--date', type=str, required=True, help='预测日期 (YYYY-MM-DD)')
    parser.add_argument('--portfolio', type=str, required=True, help='投资组合文件路径 (CSV格式)')
    args = parser.parse_args()
    
    # 读取投资组合
    try:
        portfolio_df = pd.read_csv(args.portfolio)
        # 清理数据
        portfolio_df['benchmark'] = portfolio_df['benchmark'].str.strip()
        assert all(col in portfolio_df.columns for col in ['symbol', 'shares', 'benchmark', 'adjustment']), \
            "CSV文件必须包含 'symbol', 'shares', 'benchmark' 和 'adjustment' 列"
        assert all(benchmark in ['QQQ', 'SOXX'] for benchmark in portfolio_df['benchmark']), \
            "benchmark 列只能包含 'QQQ' 或 'SOXX'"
        assert all(0 <= adj <= 1 for adj in portfolio_df['adjustment']), \
            "adjustment 列的值必须在 0 到 1 之间"
    except Exception as e:
        print(f"错误：无法读取投资组合文件：{str(e)}")
        return
    
    predict_portfolio_loss(portfolio_df, args.date)

if __name__ == "__main__":
    main() 