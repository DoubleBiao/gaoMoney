import pandas_market_calendars as mcal
from datetime import datetime, timedelta
import pytz
import logging

class MarketCalendar:
    def __init__(self):
        self.nyse = mcal.get_calendar('NYSE')
        self.logger = logging.getLogger('MarketCalendar')

    def is_market_open(self):
        """Check if the market is open today"""
        try:
            # Get today's date in NY timezone
            ny_tz = pytz.timezone('America/New_York')
            today = datetime.now(ny_tz).date()
            
            # Get market schedule for today
            schedule = self.nyse.schedule(start_date=today, end_date=today)
            
            # If schedule is empty, market is closed
            if schedule.empty:
                self.logger.info(f"Market is closed on {today}")
                return False
            
            # Check if today is a market holiday
            if today in self.nyse.holidays().holidays:
                self.logger.info(f"Market is closed for holiday on {today}")
                return False
            
            self.logger.info(f"Market is open on {today}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking market status: {str(e)}")
            return False

    def get_next_market_open(self):
        """Get the next market open date"""
        try:
            ny_tz = pytz.timezone('America/New_York')
            today = datetime.now(ny_tz).date()
            
            # Get schedule for next 30 days
            schedule = self.nyse.schedule(start_date=today, end_date=today + timedelta(days=30))
            
            if not schedule.empty:
                next_open = schedule.index[0].date()
                self.logger.info(f"Next market open date: {next_open}")
                return next_open
            else:
                self.logger.warning("Could not determine next market open date")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting next market open date: {str(e)}")
            return None 