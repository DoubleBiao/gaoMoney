import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import schedule
import time
import logging
from config import SCAN_SETTINGS, LOGGING, STOCKS_TO_MONITOR, ALERT_THRESHOLD
from market_scanner import MarketScanner
from email_sender import EmailSender
from market_calendar import MarketCalendar
from models import db, StockScan, MarketStatus
from flask import Flask

class StockMonitor:
    def __init__(self):
        self.scanner = MarketScanner()
        self.email_sender = EmailSender()
        self.market_calendar = MarketCalendar()
        self.setup_logging()
        self.setup_database()
        self.stocks = STOCKS_TO_MONITOR
        self.alert_threshold = ALERT_THRESHOLD
        self.price_history = {}
        self.volume_history = {}
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, LOGGING['level']),
            format=LOGGING['format'],
            handlers=[
                logging.FileHandler(LOGGING['file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('StockMonitor')

    def setup_database(self):
        """Setup database connection"""
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock_monitor.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        
        with app.app_context():
            db.create_all()
            self.logger.info("Database initialized")

    def save_market_status(self, is_open, next_open_date=None, message=""):
        """Save market status to database"""
        with db.app.app_context():
            status = MarketStatus(
                is_open=is_open,
                next_open_date=next_open_date,
                message=message
            )
            db.session.add(status)
            db.session.commit()

    def save_scan_results(self, stocks_data):
        """Save scan results to database"""
        with db.app.app_context():
            for stock in stocks_data:
                scan = StockScan(
                    symbol=stock['symbol'],
                    name=stock['name'],
                    price=stock['price'],
                    volume=stock['volume'],
                    market_cap=stock['market_cap'],
                    volume_ratio=stock.get('volume_ratio', 1.0)
                )
                db.session.add(scan)
            db.session.commit()

    def run_scan(self):
        """Run market scan and save results"""
        # Check if market is open
        is_open = self.market_calendar.is_market_open()
        next_open = self.market_calendar.get_next_market_open()
        
        # Save market status
        self.save_market_status(
            is_open=is_open,
            next_open_date=next_open,
            message=f"Market scan completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        if not is_open:
            self.logger.info("Skipping scan - market is closed")
            return

        self.logger.info("Starting market scan...")
        stocks_of_interest = self.scanner.scan_market()
        
        if stocks_of_interest:
            self.logger.info(f"Found {len(stocks_of_interest)} stocks of interest")
            self.save_scan_results(stocks_of_interest)
        else:
            self.logger.info("No stocks of interest found")
        
        self.logger.info("Scan completed")

    def run(self):
        """Main monitoring loop"""
        self.logger.info("Starting Stock Monitor...")
        
        # Run initial scan
        self.run_scan()
        
        # Schedule scans every 10 minutes
        schedule.every(10).minutes.do(self.run_scan)
        
        # Keep the script running
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying

    def fetch_current_data(self):
        """Fetch current stock data"""
        for symbol in self.stocks:
            try:
                stock = yf.Ticker(symbol)
                current_data = stock.history(period='1d')
                if not current_data.empty:
                    self.price_history[symbol] = current_data['Close'].iloc[-1]
                    self.volume_history[symbol] = current_data['Volume'].iloc[-1]
            except Exception as e:
                print(f"Error fetching data for {symbol}: {str(e)}")
    
    def check_alerts(self):
        """Check if price changes trigger alerts"""
        for symbol in self.stocks:
            if symbol in self.price_history:
                current_price = self.price_history[symbol]
                # Add price comparison logic here
                print(f"{symbol} current price: {current_price:.2f}")
    
    def generate_report(self):
        """Generate market report"""
        report = pd.DataFrame({
            'Symbol': self.stocks,
            'Price': [self.price_history.get(s, 'N/A') for s in self.stocks],
            'Volume': [self.volume_history.get(s, 'N/A') for s in self.stocks]
        })
        return report
    
    def plot_price_changes(self):
        """Plot price change charts"""
        plt.figure(figsize=(12, 6))
        for symbol in self.stocks:
            if symbol in self.price_history:
                plt.plot(self.price_history[symbol], label=symbol)
        plt.title('Stock Price Changes')
        plt.legend()
        plt.savefig('price_changes.png')
        plt.close()

def main():
    monitor = StockMonitor()
    monitor.run()

if __name__ == "__main__":
    main() 