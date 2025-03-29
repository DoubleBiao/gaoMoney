import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import warnings
import argparse

# Set Chinese font
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS system
plt.rcParams['axes.unicode_minus'] = False  # Fix minus sign display

# Suppress specific warnings
warnings.filterwarnings('ignore', category=UserWarning)

def calculate_variation_score(ratio):
    """
    Calculate a variation score that measures the volatility of the ratio
    Higher score indicates higher volatility
    """
    # Calculate basic statistics
    mean_ratio = ratio.mean()
    std_ratio = ratio.std()
    current_ratio = ratio.iloc[-1]
    
    # 1. Coefficient of Variation (normalized to 0-100)
    cv = (std_ratio / mean_ratio) * 100
    
    # 2. Current deviation from mean (in standard deviations)
    deviation = abs((current_ratio - mean_ratio) / std_ratio)
    
    # 3. Recent volatility (last 20 days)
    recent_volatility = ratio.tail(20).std() / ratio.tail(20).mean() * 100
    
    # 4. Trend strength (using linear regression)
    x = np.arange(len(ratio))
    slope, _ = np.polyfit(x, ratio.values, 1)
    trend_strength = abs(slope * len(ratio) / mean_ratio) * 100
    
    # Combine all factors into a single score
    # Weights can be adjusted based on importance
    score = (
        0.4 * cv +           # Coefficient of variation
        0.3 * deviation +    # Current deviation
        0.2 * recent_volatility +  # Recent volatility
        0.1 * trend_strength  # Trend strength
    )
    
    return {
        'score': score,
        'cv': cv,
        'deviation': deviation,
        'recent_volatility': recent_volatility,
        'trend_strength': trend_strength
    }

def calculate_beta(returns1, returns2):
    """
    Calculate beta between two return series
    """
    # Calculate covariance and variance
    covariance = returns1.cov(returns2)
    variance = returns2.var()
    
    # Calculate beta
    beta = covariance / variance
    return beta

def calculate_returns(price_series):
    """
    Calculate daily returns from price series
    """
    return price_series.pct_change().dropna()

def get_stock_data(symbols, period='6mo'):
    """
    Get data for multiple stocks simultaneously
    """
    try:
        # Use download method to get data for multiple stocks
        data = yf.download(symbols, period=period, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            # If multiple stocks, return closing prices
            return data['Close']
        else:
            # If single stock, create DataFrame
            return pd.DataFrame({symbols: data['Close']})
    except Exception as e:
        print(f"Failed to get data: {str(e)}")
        return None

def analyze_stock(symbol, benchmark="SOXX", period='6mo'):
    """
    Analyze a stock's beta and other metrics relative to the benchmark
    """
    try:
        print(f"Fetching data for {symbol} and {benchmark}...")
        # Get data for both stocks
        data = get_stock_data([symbol, benchmark], period)
        
        if data is None or data.empty:
            raise ValueError(f"Failed to get stock data")
        
        # Calculate returns
        returns = calculate_returns(data)
        
        # Calculate beta
        beta = calculate_beta(returns[symbol], returns[benchmark])
        
        # Calculate additional metrics
        stock_volatility = returns[symbol].std() * np.sqrt(252)  # Annualized volatility
        benchmark_volatility = returns[benchmark].std() * np.sqrt(252)
        correlation = returns[symbol].corr(returns[benchmark])
        
        # Calculate excess returns
        excess_returns = returns[symbol] - returns[benchmark]
        excess_return_mean = excess_returns.mean() * 252  # Annualized
        excess_return_std = excess_returns.std() * np.sqrt(252)
        
        # Calculate information ratio
        information_ratio = excess_return_mean / excess_return_std
        
        # Calculate worst case scenarios
        worst_daily_drop = returns[symbol].min()
        worst_weekly_drop = returns[symbol].rolling(5).sum().min()
        worst_monthly_drop = returns[symbol].rolling(21).sum().min()
        
        # Calculate expected drop given benchmark drop
        expected_drop_5pct = beta * -0.05  # Expected drop if benchmark drops 5%
        confidence_interval = 1.96 * excess_return_std  # 95% confidence interval
        
        return {
            'beta': beta,
            'stock_volatility': stock_volatility,
            'benchmark_volatility': benchmark_volatility,
            'correlation': correlation,
            'excess_return_mean': excess_return_mean,
            'excess_return_std': excess_return_std,
            'information_ratio': information_ratio,
            'worst_daily_drop': worst_daily_drop,
            'worst_weekly_drop': worst_weekly_drop,
            'worst_monthly_drop': worst_monthly_drop,
            'expected_drop_5pct': expected_drop_5pct,
            'confidence_interval': confidence_interval
        }
    except Exception as e:
        print(f"Error analyzing stock: {str(e)}")
        return None

def plot_analysis(data, symbol, benchmark="SOXX"):
    """
    Plot the analysis results
    """
    if data is None:
        return
        
    plt.figure(figsize=(12, 6))
    
    # Create a bar chart of key metrics
    metrics = ['Beta', 'Volatility', 'Correlation', 'Information Ratio']
    values = [
        data['beta'],
        data['stock_volatility'],
        data['correlation'],
        data['information_ratio']
    ]
    
    plt.bar(metrics, values)
    plt.title(f'{symbol} Analysis Relative to {benchmark}')
    plt.ylabel('Value')
    plt.grid(True, axis='y')
    
    # Add value labels on top of bars
    for i, v in enumerate(values):
        plt.text(i, v, f'{v:.2f}', ha='center', va='bottom')
    
    plt.savefig('stock_analysis.png')
    plt.close()

def get_beta(symbol):
    """获取股票的beta值"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        if info and 'beta' in info:
            return info['beta']
        return None
    except Exception:
        return None

def analyze_stock_ratio(symbol):
    """分析股票的各项指标"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        if not info:
            return None
            
        result = {
            'symbol': symbol,
            'beta': info.get('beta', None),
            'pe_ratio': info.get('forwardPE', None),
            'market_cap': info.get('marketCap', None),
            'dividend_yield': info.get('dividendYield', None),
            'volume': info.get('volume', None),
            'avg_volume': info.get('averageVolume', None)
        }
        
        return result
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(description='分析股票相对于基准的比率')
    parser.add_argument('--symbol', type=str, help='股票代码', required=True)
    parser.add_argument('--benchmark', type=str, help='基准指数', default='QQQ')
    args = parser.parse_args()
    
    result = analyze_stock_ratio(args.symbol)
    print(result)

if __name__ == "__main__":
    main() 