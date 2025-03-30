# Portfolio Risk Prediction System

A Python tool that predicts potential losses in your stock portfolio based on options market data using E*TRADE API.

## Quick Start

1. **Configure E*TRADE API**:
   - Create an E*TRADE developer account at https://developer.etrade.com
   - Create a new application to get your API keys
   - Create a `config.json` file in the project root:
   ```json
   {
     "etrade": {
       "consumer_key": "YOUR_CONSUMER_KEY",
       "consumer_secret": "YOUR_CONSUMER_SECRET",
       "sandbox": false
     }
   }
   ```
   - Run the test program to authorize:
   ```bash
   python etrade_test.py
   ```
   - Follow the authorization steps in the browser
   - The access token will be saved in `etrade_tokens.json`

2. **Configure your portfolio** in `portfolio.csv`:
```csv
symbol,shares,benchmark,adjustment,options
TSLA,68,QQQ,0.5,1
GOOGL,123,QQQ,0.5,1
AMD,40,SOXX,1.0,1
UBER,100,QQQ,1.0,0
```

Columns:
- `symbol`: Stock symbol (e.g., TSLA, GOOGL)
- `shares`: Number of shares
- `benchmark`: Benchmark index (QQQ or SOXX)
- `adjustment`: Risk adjustment factor (0.5 or 1.0)
- `options`: Number of options contracts (0 for no options)

3. **Run prediction**:
```bash
python predict_portfolio.py --portfolio portfolio.csv --date YYYY-MM-DD
```

Required arguments:
- `--portfolio`: Path to your portfolio configuration file (CSV format)
- `--date`: Target prediction date (must be a valid options expiration date)

## How It Works

- Uses E*TRADE API to fetch real-time options data
- Calculates volatility based on ATM options and open interest
- Predicts potential market declines using 68% confidence interval
- Adjusts risk exposure using adjustment factors (0.5 or 1.0)
- Aggregates risks across the portfolio

## Requirements
- Python 3.x
- pandas
- pandas_market_calendars
- E*TRADE API credentials

## Note
- Target date must be a valid options expiration date
- Results are for reference only
- Keep your API credentials secure and never commit them to version control
