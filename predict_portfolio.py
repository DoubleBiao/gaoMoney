import pandas as pd
from datetime import datetime
import argparse
from option_range import get_option_range, get_target_expiry, predict_drop_rate
from etrade_options import get_market_instance, check_option_availability, get_atm_option_price, get_stock_price, get_stock_beta
import sys
import json

def plot_scenarios(drop_probs, drop_results, rise_probs, rise_results):
    """Generate JavaScript chart data for HTML report"""
    # Prepare drop scenario data (negative x values)
    drop_x = [-p for p in reversed(drop_probs)]
    drop_total = list(reversed(drop_results['total_gain']))
    drop_price = list(reversed(drop_results['price_diff']))
    drop_option = [-l for l in reversed(drop_results['option_loss'])]  # 将期权损失转换为负值
    
    # Add 0 point to both drop and rise data
    drop_x.append(0)
    drop_total.append(0)
    drop_price.append(0)
    drop_option.append(0)
    
    # Prepare rise scenario data (positive x values)
    rise_x = [0] + rise_probs
    rise_total = [0] + [-l for l in rise_results['total_loss']]
    rise_price = [0] + [-c for c in rise_results['opportunity_cost']]
    rise_option = [0] + [g for g in rise_results['option_gain']]
    
    # Create traces for Plotly
    traces = [
        # Drop scenario traces
        {
            'x': drop_x,
            'y': drop_total,
            'name': 'Total Return',
            'type': 'scatter',
            'line': {'color': 'blue', 'width': 2}
        },
        {
            'x': drop_x,
            'y': drop_price,
            'name': 'Stock Price Impact',
            'type': 'scatter',
            'line': {'color': 'green', 'width': 2, 'dash': 'dash'}
        },
        {
            'x': drop_x,
            'y': drop_option,
            'name': 'Option Impact',
            'type': 'scatter',
            'line': {'color': 'red', 'width': 2, 'dash': 'dash'}
        },
        # Rise scenario traces
        {
            'x': rise_x,
            'y': rise_total,
            'name': 'Total Return',
            'type': 'scatter',
            'line': {'color': 'blue', 'width': 2},
            'showlegend': False
        },
        {
            'x': rise_x,
            'y': rise_price,
            'name': 'Stock Price Impact',
            'type': 'scatter',
            'line': {'color': 'green', 'width': 2, 'dash': 'dash'},
            'showlegend': False
        },
        {
            'x': rise_x,
            'y': rise_option,
            'name': 'Option Impact',
            'type': 'scatter',
            'line': {'color': 'red', 'width': 2, 'dash': 'dash'},
            'showlegend': False
        }
    ]
    
    # Calculate y-axis range
    all_y_values = drop_total + drop_price + drop_option + rise_total + rise_price + rise_option
    max_y = max(all_y_values)
    min_y = min(all_y_values)
    y_range = max_y - min_y
    
    # Create layout
    layout = {
        'title': {
            'text': 'Portfolio Performance Analysis',
            'font': {'size': 24}
        },
        'xaxis': {
            'title': 'Market Change (%)',
            'gridcolor': '#eee',
            'zerolinecolor': '#000',
            'zerolinewidth': 2,
            'tickfont': {'size': 12},
            'titlefont': {'size': 14},
            'range': [-120, 120],
            'dtick': 20,
            'showgrid': True
        },
        'yaxis': {
            'title': 'Amount ($)',
            'gridcolor': '#eee',
            'zerolinecolor': '#000',
            'zerolinewidth': 2,
            'tickfont': {'size': 12},
            'titlefont': {'size': 14},
            'range': [min_y - y_range * 0.1, max_y + y_range * 0.1],
            'showgrid': True
        },
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'showlegend': True,
        'legend': {
            'x': 0.02,
            'y': 0.98,
            'bgcolor': 'rgba(255, 255, 255, 0.8)',
            'bordercolor': '#ddd',
            'borderwidth': 1,
            'font': {'size': 12}
        },
        'annotations': [
            {
                'x': -60,
                'y': max_y - y_range * 0.1,
                'text': 'Drop Scenario',
                'showarrow': False,
                'font': {'size': 14}
            },
            {
                'x': 60,
                'y': max_y - y_range * 0.1,
                'text': 'Rise Scenario',
                'showarrow': False,
                'font': {'size': 14}
            }
        ],
        'margin': {
            'l': 80,
            'r': 50,
            't': 100,
            'b': 80
        },
        'shapes': [
            {
                'type': 'line',
                'x0': 0,
                'y0': min_y - y_range * 0.1,
                'x1': 0,
                'y1': max_y + y_range * 0.1,
                'line': {
                    'color': '#000',
                    'width': 2
                }
            }
        ]
    }
    
    return {'traces': traces, 'layout': layout}

def predict_portfolio_scenarios(portfolio_df, target_date):
    """预测投资组合在不同市场情况下的表现"""
    print("\n=== 开始投资组合分析 ===")
    print("1. 连接E*TRADE API...")
    
    # 获取E*TRADE市场实例
    market = get_market_instance()
    if not market:
        print("错误：无法获取E*TRADE市场实例，请检查配置和授权。")
        return
    
    print("2. 获取基准指数预测...")
    # 获取基准指数的涨跌幅预测
    qqq_range = get_option_range('QQQ', target_date)
    soxx_range = get_option_range('SOXX', target_date)
    print("基准指数预测完成")
    
    # 定义不同概率水平的分析
    drop_probabilities = [1.20, 1.10, 0.90, 0.80, 0.75, 0.50, 0.25, 0.00]
    rise_probabilities = [1.20, 1.10, 0.90, 0.80, 0.75, 0.50, 0.25, 0.00]
    
    # 初始化结果统计
    drop_results = {
        'total_gain': [0] * len(drop_probabilities),
        'price_diff': [0] * len(drop_probabilities),
        'option_loss': [0] * len(drop_probabilities)
    }
    rise_results = {
        'total_loss': [0] * len(rise_probabilities),
        'opportunity_cost': [0] * len(rise_probabilities),
        'option_gain': [0] * len(rise_probabilities)
    }
    
    print("\n3. 开始分析个股...")
    # 计算每个股票的策略效果
    total_stocks = len(portfolio_df)
    for idx, (_, row) in enumerate(portfolio_df.iterrows(), 1):
        symbol = row['symbol']
        print(f"\n分析 {symbol} ({idx}/{total_stocks})")
        print("-" * 50)
        
        shares = row['shares']
        benchmark = row['benchmark']
        adjustment = row['adjustment']
        options = row.get('options', 0)
        
        # 获取当前价格
        current_price = get_stock_price(market, symbol)
        if current_price is None:
            print(f"警告：无法获取 {symbol} 的当前价格，跳过此股票")
            continue
            
        # 获取个股的beta值
        print(f"计算Beta值...")
        beta = get_stock_beta(market, symbol)
        print(f"Beta值: {beta:.2f}")
        
        # 计算卖出的股票数量
        sold_shares = shares * (1 - adjustment)
        
        # 计算期权成本和收益
        option_cost = 0
        option_gain = 0
        if options > 0:
            print(f"获取期权价格...")
            option_price = get_atm_option_price(market, symbol, target_date)
            if option_price is not None:
                option_cost = option_price * 100 * options
                print(f"期权价格: ${option_price:.2f}")
        
        print("\n分析下跌情景:")
        # 计算不同概率水平的下跌分析
        for i, prob in enumerate(drop_probabilities):
            print(f"估算 {prob*100:.0f}% 下跌情况...")
            # 计算该概率下的跌幅
            benchmark_drop = soxx_range[3] if benchmark == 'SOXX' else qqq_range[3]
            adjusted_drop = (benchmark_drop / 100) * beta * prob
            price_difference = sold_shares * current_price * adjusted_drop
            
            # 计算期权损失（假设期权损失与跌幅成正比）
            adjusted_option_cost = option_cost * prob
            
            # 计算净收益
            net_gain = price_difference - adjusted_option_cost
            
            # 累加结果
            drop_results['total_gain'][i] += net_gain
            drop_results['price_diff'][i] += price_difference
            drop_results['option_loss'][i] += adjusted_option_cost
        
        print("\n分析上涨情景:")
        # 计算不同概率水平的上涨分析
        for i, prob in enumerate(rise_probabilities):
            print(f"估算 {prob*100:.0f}% 上涨情况...")
            # 计算该概率下的涨幅
            benchmark_rise = soxx_range[2] if benchmark == 'SOXX' else qqq_range[2]
            adjusted_rise = (benchmark_rise / 100) * beta * prob
            opportunity_cost = sold_shares * current_price * adjusted_rise
            
            # 计算期权收益
            adjusted_option_gain = current_price * adjusted_rise * 100 * options
            
            # 计算净损失
            net_loss = opportunity_cost - adjusted_option_gain
            
            # 累加结果
            rise_results['total_loss'][i] += net_loss
            rise_results['opportunity_cost'][i] += opportunity_cost
            rise_results['option_gain'][i] += adjusted_option_gain
    
    print("\n4. 生成分析图表...")
    # 绘制图表
    plot_data = plot_scenarios(
        [p * 100 for p in drop_probabilities],
        drop_results,
        [p * 100 for p in rise_probabilities],
        rise_results
    )
    print("分析图表生成完成")
    
    print("\n5. 生成HTML报告...")
    # 生成HTML报告
    generate_html_report(
        target_date,
        qqq_range,
        soxx_range,
        portfolio_df,
        drop_probabilities,
        rise_probabilities,
        drop_results,
        rise_results
    )
    
    print("\n=== 分析完成 ===")
    print("报告已保存为 portfolio_analysis.html")

def predict_stock_range(symbol, benchmark, current_price, expiry_date, market):
    """预测个股的价格范围"""
    try:
        # 获取基准指数的涨跌幅
        benchmark_range = get_option_range(benchmark, expiry_date)
        benchmark_rise_rate = benchmark_range[2]
        benchmark_drop_rate = benchmark_range[3]
        
        # 获取个股的beta值
        beta = get_stock_beta(market, symbol)
        
        # 使用beta值调整涨跌幅
        rise_rate = benchmark_rise_rate * beta
        drop_rate = benchmark_drop_rate * beta
        
        return [
            current_price * (1 - drop_rate/100),
            current_price * (1 + rise_rate/100),
            rise_rate,
            drop_rate
        ]
    except Exception as e:
        print(f"错误：预测{symbol}价格范围时发生错误：{str(e)}")
        sys.exit(1)

def get_stock_beta(market, symbol):
    """获取个股的beta值"""
    try:
        # 使用E*TRADE API获取股票信息
        response = market.get_quote([symbol], resp_format='json')
        if 'QuoteResponse' in response and 'QuoteData' in response['QuoteResponse']:
            quote = response['QuoteResponse']['QuoteData'][0]
            if 'All' in quote:
                beta = float(quote['All'].get('beta', 1.0))
                
                # 确保beta值在合理范围内（0.5-2.0）
                beta = max(0.5, min(2.0, beta))
                
                return beta
    except Exception as e:
        print(f"警告：获取{symbol}的beta值时发生错误：{str(e)}，使用默认值1.0")
    return 1.0

def to_json(obj):
    """Convert object to JSON string"""
    return json.dumps(obj, ensure_ascii=False)

def generate_html_report(target_date, qqq_range, soxx_range, portfolio_df, drop_probabilities, rise_probabilities, drop_results, rise_results):
    """Generate HTML format portfolio analysis report"""
    # Get chart data
    plot_data = plot_scenarios(
        [p * 100 for p in drop_probabilities],
        drop_results,
        [p * 100 for p in rise_probabilities],
        rise_results
    )
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Portfolio Strategy Evaluation Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .section {{ margin-bottom: 30px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ padding: 8px; text-align: right; border: 1px solid #ddd; }}
            th {{ background-color: #f5f5f5; }}
            .chart {{ text-align: center; margin: 20px 0; height: 600px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Portfolio Strategy Evaluation Report</h1>
                <p>Evaluation Date: {target_date}</p>
            </div>
            
            <div class="section">
                <h2>Benchmark Index Predictions</h2>
                <table>
                    <tr>
                        <th>Index</th>
                        <th>Rise Rate</th>
                        <th>Drop Rate</th>
                    </tr>
                    <tr>
                        <td>QQQ</td>
                        <td>{qqq_range[2]:.1f}%</td>
                        <td>{qqq_range[3]:.1f}%</td>
                    </tr>
                    <tr>
                        <td>SOXX</td>
                        <td>{soxx_range[2]:.1f}%</td>
                        <td>{soxx_range[3]:.1f}%</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Portfolio Composition</h2>
                {generate_portfolio_table(portfolio_df)}
            </div>
            
            <div class="section">
                <h2>Stock Analysis</h2>
                {generate_stock_analysis_table(portfolio_df)}
            </div>
            
            <div class="section">
                <h2>Market Scenario Analysis</h2>
                <div id="scenarioChart" class="chart"></div>
                
                <h3>Market Rise Scenario Analysis</h3>
                <table>
                    <tr>
                        <th>Probability</th>
                        <th>Total Opportunity Cost</th>
                        <th>Total Option Gain</th>
                        <th>Net Loss</th>
                    </tr>
                    {generate_rise_analysis_rows(rise_probabilities, rise_results)}
                </table>
                
                <h3>Market Drop Scenario Analysis</h3>
                <table>
                    <tr>
                        <th>Probability</th>
                        <th>Total Price Difference</th>
                        <th>Total Option Loss</th>
                        <th>Net Gain</th>
                    </tr>
                    {generate_drop_analysis_rows(drop_probabilities, drop_results)}
                </table>
            </div>
        </div>
        
        <script>
            const traces = {to_json(plot_data['traces'])};
            const layout = {to_json(plot_data['layout'])};
            Plotly.newPlot('scenarioChart', traces, layout);
        </script>
    </body>
    </html>
    """
    
    with open('portfolio_analysis.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def generate_portfolio_table(portfolio_df):
    """生成投资组合信息表格的HTML内容"""
    html = """
    <table>
        <tr>
            <th>Stock</th>
            <th>Shares</th>
            <th>Benchmark</th>
            <th>Adjustment</th>
            <th>Options</th>
        </tr>
    """
    
    for _, row in portfolio_df.iterrows():
        html += f"""
        <tr>
            <td>{row['symbol']}</td>
            <td>{row['shares']}</td>
            <td>{row['benchmark']}</td>
            <td>{row['adjustment']*100:.0f}%</td>
            <td>{row.get('options', 0)}</td>
        </tr>
        """
    
    html += "</table>"
    return html

def generate_stock_analysis_table(portfolio_df):
    """生成个股分析表格的HTML内容"""
    market = get_market_instance()
    if not market:
        return "<p>Unable to get market data</p>"
    
    html = "<table><tr><th>Stock</th><th>Current Price</th><th>Shares Sold</th><th>Benchmark</th><th>Beta</th></tr>"
    
    for _, row in portfolio_df.iterrows():
        symbol = row['symbol']
        shares = row['shares']
        benchmark = row['benchmark']
        adjustment = row['adjustment']
        
        current_price = get_stock_price(market, symbol)
        if current_price is None:
            continue
            
        beta = get_stock_beta(market, symbol)
        sold_shares = shares * (1 - adjustment)
        
        html += f"""
        <tr>
            <td>{symbol}</td>
            <td>${current_price:.2f}</td>
            <td>{sold_shares:.1f}</td>
            <td>{benchmark}</td>
            <td>{beta:.2f}</td>
        </tr>
        """
    
    html += "</table>"
    return html

def generate_rise_analysis_rows(probabilities, results):
    """生成上涨分析表格行的HTML内容"""
    html = ""
    for i, prob in enumerate(probabilities):
        html += f"""
        <tr>
            <td>{prob*100:.0f}%</td>
            <td>${results['opportunity_cost'][i]:,.2f}</td>
            <td>${results['option_gain'][i]:,.2f}</td>
            <td>${results['total_loss'][i]:,.2f}</td>
        </tr>
        """
    return html

def generate_drop_analysis_rows(probabilities, results):
    """生成下跌分析表格行的HTML内容"""
    html = ""
    for i, prob in enumerate(probabilities):
        html += f"""
        <tr>
            <td>{prob*100:.0f}%</td>
            <td>${results['price_diff'][i]:,.2f}</td>
            <td>${results['option_loss'][i]:,.2f}</td>
            <td>${results['total_gain'][i]:,.2f}</td>
        </tr>
        """
    return html

def main():
    parser = argparse.ArgumentParser(description='评估投资组合策略在不同市场情况下的表现')
    parser.add_argument('--portfolio', required=True, help='投资组合CSV文件路径')
    parser.add_argument('--date', required=True, help='目标日期 (YYYY-MM-DD)')
    args = parser.parse_args()

    try:
        # 读取投资组合数据
        portfolio_df = pd.read_csv(args.portfolio)
        
        # 预测投资组合在不同市场情况下的表现
        predict_portfolio_scenarios(portfolio_df, args.date)
        
    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 