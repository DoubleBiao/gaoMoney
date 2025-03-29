# 要监控的股票代码列表
STOCKS_TO_MONITOR = [
    'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META',
    'NVDA', 'TSLA', 'AMD', 'INTC', 'NFLX'
]

# 价格变动预警阈值（百分比）
ALERT_THRESHOLD = 0.05

# 数据更新间隔（秒）
UPDATE_INTERVAL = 60

# 图表设置
CHART_SETTINGS = {
    'figure_size': (12, 6),
    'style': 'seaborn',
    'save_path': 'charts/'
}

# Server settings
SERVER = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False
}

# Market scanning settings
SCAN_SETTINGS = {
    'scan_time': '09:30',  # Daily scan time (EST)
    'volume_analysis_period': '3mo',  # Period for volume analysis
    'min_market_cap': 5e8,  # Minimum market cap in USD (500M)
    'min_price': 1.0,  # Minimum stock price
}

# Volume analysis settings
VOLUME_SETTINGS = {
    'peak_threshold': 2.0,  # Volume should be 2x the average
    'min_volume': 100000,  # Minimum daily volume
}

# Database settings
DATABASE = {
    'enabled': True,
    'type': 'sqlite',
    'path': 'stock_data.db'
}

# Logging settings
LOGGING = {
    'level': 'INFO',
    'file': 'stock_monitor.log',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Email settings
EMAIL = {
    'smtp_server': 'smtp.gmail.com',  # Gmail SMTP server
    'smtp_port': 587,
    'sender_email': 'your-email@gmail.com',  # Replace with your email
    'sender_password': 'your-app-password',  # Replace with your app password
    'recipient_email': 'recipient@example.com',  # Replace with recipient email
    'use_tls': True
} 