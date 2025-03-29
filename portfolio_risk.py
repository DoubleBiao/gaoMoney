from stock_ratio import analyze_stock_ratio
import yfinance as yf

class Portfolio:
    def __init__(self, positions=None):
        """
        初始化投资组合
        positions: 字典，包含每个股票的持仓信息
        例如：{
            'AMBA': {'shares': 700, 'price': 50.61, 'benchmark': 'SOXX'},
            'UBER': {'shares': 100, 'price': 72.72, 'benchmark': 'QQQ'},
        }
        """
        self.positions = positions or {}
        self.total_value = sum(pos['shares'] * pos['price'] 
                             for pos in self.positions.values())
    
    def get_total_value(self):
        """获取投资组合总价值"""
        return self.total_value

def analyze_portfolio_risk(portfolio, qqq_drop_pct, soxx_drop_pct):
    """分析投资组合风险"""
    total_value = portfolio.get_total_value()
    total_loss = 0
    stocks = []
    
    for symbol, position in portfolio.positions.items():
        current_value = position['shares'] * position['price']
        # 根据基准指数确定使用哪个下跌率
        drop_pct = soxx_drop_pct if position['benchmark'] == 'SOXX' else qqq_drop_pct
        expected_loss = current_value * (drop_pct / 100)
        total_loss += expected_loss
        
        stocks.append({
            'symbol': symbol,
            'shares': position['shares'],
            'current_price': position['price'],
            'current_value': current_value,
            'expected_loss': expected_loss,
            'benchmark': position['benchmark']
        })
    
    return {
        'total_value': total_value,
        'total_loss': total_loss,
        'loss_percentage': (total_loss / total_value * 100),
        'stocks': stocks
    }

def main():
    # 示例投资组合
    example_portfolio = {
        'AMBA': {'shares': 700, 'price': 50.61, 'benchmark': 'SOXX'},
        'UBER': {'shares': 100, 'price': 72.72, 'benchmark': 'QQQ'},
        'AMD': {'shares': 40, 'price': 103.22, 'benchmark': 'SOXX'},
        'GOOGL': {'shares': 123, 'price': 154.33, 'benchmark': 'QQQ'},
        'TSLA': {'shares': 68, 'price': 263.55, 'benchmark': 'QQQ'}
    }
    portfolio = Portfolio(example_portfolio)
    result = analyze_portfolio_risk(portfolio, -5.8, -8.6)  # 示例下跌率
    print(result)

if __name__ == "__main__":
    main() 