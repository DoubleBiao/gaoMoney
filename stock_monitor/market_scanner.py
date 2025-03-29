import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from config import SCAN_SETTINGS, VOLUME_SETTINGS

class MarketScanner:
    def __init__(self):
        self.settings = SCAN_SETTINGS
        self.volume_settings = VOLUME_SETTINGS
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('stock_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('MarketScanner')

    def get_all_stocks(self):
        """Get list of all stocks from major indices"""
        # For now, we'll use a predefined list of major stocks
        # In the future, this could be expanded to fetch from multiple sources
        indices = ['^GSPC', '^DJI', '^IXIC', '^RUT']  # S&P 500, Dow Jones, NASDAQ, Russell 2000
        stocks = set()
        
        for index in indices:
            try:
                ticker = yf.Ticker(index)
                # Get constituents of the index
                # Note: This is a simplified version. In production, you'd want to use
                # a more reliable source for index constituents
                stocks.update(ticker.info.get('components', []))
            except Exception as e:
                self.logger.error(f"Error fetching stocks from {index}: {str(e)}")
        
        return list(stocks)

    def analyze_volume(self, symbol):
        """Analyze if a stock's volume is at a peak"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=self.settings['volume_analysis_period'])
            
            if hist.empty:
                return False
            
            # Calculate average volume
            avg_volume = hist['Volume'].mean()
            latest_volume = hist['Volume'].iloc[-1]
            
            # Check if latest volume meets criteria
            is_peak = (
                latest_volume > avg_volume * self.volume_settings['peak_threshold'] and
                latest_volume > self.volume_settings['min_volume']
            )
            
            return is_peak
            
        except Exception as e:
            self.logger.error(f"Error analyzing volume for {symbol}: {str(e)}")
            return False

    def scan_market(self):
        """Scan the market for stocks of interest"""
        self.logger.info("Starting market scan...")
        
        stocks = self.get_all_stocks()
        stocks_of_interest = []
        
        for symbol in stocks:
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                
                # Basic filtering
                if (info.get('marketCap', 0) < self.settings['min_market_cap'] or
                    info.get('regularMarketPrice', 0) < self.settings['min_price']):
                    continue
                
                # Volume analysis
                if self.analyze_volume(symbol):
                    stocks_of_interest.append({
                        'symbol': symbol,
                        'name': info.get('longName', ''),
                        'price': info.get('regularMarketPrice', 0),
                        'volume': info.get('regularMarketVolume', 0),
                        'market_cap': info.get('marketCap', 0)
                    })
                    
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        self.logger.info(f"Found {len(stocks_of_interest)} stocks of interest")
        return stocks_of_interest

    def save_results(self, stocks_of_interest):
        """Save scan results to database"""
        try:
            df = pd.DataFrame(stocks_of_interest)
            df['scan_date'] = datetime.now()
            df.to_csv('scan_results.csv', index=False)
            self.logger.info("Scan results saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving scan results: {str(e)}") 