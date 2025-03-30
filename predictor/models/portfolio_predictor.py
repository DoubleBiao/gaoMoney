import pandas as pd
import numpy as np
from datetime import datetime
import requests
import json
import os
import sys
from flask import Flask

# 使用相对路径导入
sys.path.append('..')
import etrade_options
import option_range
from etrade_options import get_market_instance, get_stock_price, get_stock_beta, get_atm_option_price
from option_range import get_option_range, get_target_expiry

class PortfolioPredictor:
    def __init__(self, portfolio_data, target_date):
        self.portfolio_data = portfolio_data
        self.target_date = target_date
        # 确保在正确的目录中
        os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.market = get_market_instance()
        if not self.market:
            raise Exception("无法连接到E*TRADE API")
        
    def _load_config(self):
        with open('config.json', 'r') as f:
            return json.load(f)
    
    def predict(self):
        try:
            # 获取基准指数预测
            benchmark_predictions = self._get_benchmark_predictions()
            
            # 获取股票分析数据
            stock_analysis = []
            portfolio_risk = []
            
            # 将列表转换为DataFrame
            portfolio_df = pd.DataFrame(self.portfolio_data)
            
            # 过滤掉AAPL
            portfolio_df = portfolio_df[portfolio_df['symbol'] != 'AAPL']
            
            for _, row in portfolio_df.iterrows():
                symbol = row['symbol']
                shares = row['shares']
                benchmark = row['benchmark']
                adjustment = row['adjustment']
                options = row.get('options', 0)
                
                # 获取当前价格和beta值
                current_price = get_stock_price(self.market, symbol)
                beta = get_stock_beta(self.market, symbol)
                
                if not current_price:
                    raise Exception(f"无法获取{symbol}的当前价格")
                
                # 添加到股票分析列表
                stock_analysis.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'shares': shares,
                    'shares_sold': shares * (1 - adjustment),
                    'benchmark': benchmark,
                    'beta': beta
                })
                
                # 添加到风险分析列表
                portfolio_risk.append({
                    'symbol': symbol,
                    'shares': shares,
                    'benchmark': benchmark,
                    'options': options,
                    'rise_rate': benchmark_predictions[benchmark]['rise'],
                    'drop_rate': benchmark_predictions[benchmark]['drop']
                })
            
            # 生成市场情景分析
            scenarios = self._generate_market_scenarios(portfolio_risk, stock_analysis)
            
            return {
                'benchmark_predictions': benchmark_predictions,
                'stock_analysis': stock_analysis,
                'market_scenarios': scenarios,
                'evaluation_date': datetime.now().strftime('%Y-%m-%d')
            }
        except Exception as e:
            raise Exception(f"预测过程中发生错误：{str(e)}")
    
    def _get_benchmark_predictions(self):
        """从E*TRADE获取基准指数的预测"""
        try:
            # 只获取QQQ和SOXX的期权范围预测
            qqq_range = get_option_range('QQQ', self.target_date)
            soxx_range = get_option_range('SOXX', self.target_date)
            
            return {
                'QQQ': {
                    'rise': qqq_range[2] / 100,  # 转换为小数
                    'drop': qqq_range[3] / 100   # 转换为小数
                },
                'SOXX': {
                    'rise': soxx_range[2] / 100,  # 转换为小数
                    'drop': soxx_range[3] / 100   # 转换为小数
                }
            }
        except Exception as e:
            raise Exception(f"获取基准指数预测失败：{str(e)}")
    
    def _generate_market_scenarios(self, portfolio_risk, stock_analysis):
        """生成市场情景分析"""
        probabilities = [120, 110, 100, 90, 80, 75, 50, 25, 0]
        
        rise_scenarios = []
        drop_scenarios = []
        
        # 获取基准指数预测
        benchmark_predictions = self._get_benchmark_predictions()
        
        # 预先获取所有股票的期权价格
        option_info = {}
        for stock in stock_analysis:
            try:
                symbol = stock['symbol']
                current_price = stock['current_price']
                # 获取平值期权价格，如果失败则跳过
                option_price = get_atm_option_price(self.market, symbol, self.target_date)
                if option_price:
                    # 使用中间价作为期权价格
                    option_info[symbol] = {
                        'current_price': option_price,  # 当前期权价格
                        'strike_price': round(current_price)  # 使用当前股价的整数值作为行权价
                    }
                    print(f"成功获取{symbol}期权信息: 当前价格={current_price}, 期权价格={option_price}")
            except Exception as e:
                print(f"获取{symbol}期权信息时出错: {str(e)}")
                continue
        
        for prob in probabilities:
            factor = prob / 100.0
            
            # 初始化场景结果
            rise_result = {
                'probability': prob,
                'opportunity_cost': 0,
                'option_gain': 0,
                'net_loss': 0
            }
            
            drop_result = {
                'probability': prob,
                'price_difference': 0,
                'option_gain': 0,
                'net_gain': 0
            }
            
            # 计算每个股票在当前概率下的结果
            for stock in stock_analysis:
                symbol = stock['symbol']
                benchmark = benchmark_predictions[stock['benchmark']]
                beta = stock['beta']
                current_price = stock['current_price']
                shares_sold = stock['shares_sold']
                
                if symbol not in option_info:
                    print(f"跳过{symbol}的期权计算，因为没有找到期权信息")
                    continue
                    
                current_option_price = option_info[symbol]['current_price']
                strike_price = option_info[symbol]['strike_price']
                
                # 计算上涨情况
                rise_rate = benchmark['rise'] * beta * factor
                opportunity_cost = shares_sold * current_price * rise_rate
                
                # 计算期权到期收益（上涨情况）
                if current_option_price:
                    # 上涨时，股价增加rise_rate
                    expected_rise_price = current_price * (1 + rise_rate)
                    # 期权收益 = (到期价值 - 当前期权价格) x 100
                    # 到期价值 = max(0, 股价 - 行权价)
                    option_gain = (max(0, expected_rise_price - strike_price) - current_option_price) * 100
                    rise_result['option_gain'] += option_gain
                
                rise_result['opportunity_cost'] += opportunity_cost
                rise_result['net_loss'] += opportunity_cost - (option_gain if current_option_price else 0)
                
                # 计算下跌情况
                drop_rate = benchmark['drop'] * beta * factor
                price_difference = shares_sold * current_price * drop_rate
                
                # 计算期权到期收益（下跌情况）
                if current_option_price:
                    # 下跌时，股价减少drop_rate
                    expected_drop_price = current_price * (1 - drop_rate)
                    # 期权收益 = (到期价值 - 当前期权价格) x 100
                    # 到期价值 = max(0, 股价 - 行权价)
                    option_gain = (max(0, expected_drop_price - strike_price) - current_option_price) * 100
                    drop_result['option_gain'] += option_gain
                
                drop_result['price_difference'] += price_difference
                # 在下跌情况下，净收益 = 价格差异 + 期权收益（因为期权收益已经是负数了）
                drop_result['net_gain'] += price_difference + (option_gain if current_option_price else 0)
            
            rise_scenarios.append(rise_result)
            drop_scenarios.append(drop_result)
        
        # 准备绘图数据
        plot_data = {
            'drop_probs': probabilities,
            'drop_results': {
                'total_gain': [s['net_gain'] for s in drop_scenarios],  # 下跌情况下的总回报就是net_gain
                'price_diff': [s['price_difference'] for s in drop_scenarios],  # 股价影响保持不变
                'option_impact': [s['option_gain'] for s in drop_scenarios]  # 期权影响就是option_gain（负值）
            },
            'rise_probs': probabilities,
            'rise_results': {
                'total_loss': [-s['net_loss'] for s in rise_scenarios],  # 上涨情况下的总回报是net_loss的负值
                'opportunity_cost': [-s['opportunity_cost'] for s in rise_scenarios],  # 股价影响是机会成本的负值
                'option_impact': [s['option_gain'] for s in rise_scenarios]  # 期权影响就是option_gain（正值）
            }
        }
        
        return {
            'rise_scenarios': rise_scenarios,
            'drop_scenarios': drop_scenarios,
            'plot_data': plot_data
        } 