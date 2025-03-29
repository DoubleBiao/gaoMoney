# Portfolio Risk Prediction System

A Python tool that predicts potential losses in your stock portfolio based on options market data.

## Quick Start

1. **Configure your portfolio** in `portfolio.csv`:
```csv
symbol,shares,benchmark,adjustment
TSLA,68,QQQ,0.5
GOOGL,123,QQQ,0.5
AMD,40,SOXX,1.0
UBER,100,QQQ,1.0
```

2. **Run prediction**:
```bash
python predict_portfolio_loss.py --portfolio portfolio.csv --date YYYY-MM-DD
```

Required arguments:
- `--portfolio`: Path to your portfolio configuration file (CSV format)
- `--date`: Target prediction date (must be a valid options expiration date)

## How It Works

- Uses options data to predict potential market declines
- Calculates individual stock risks based on their Beta values
- Adjusts risk exposure using adjustment factors (0.5 or 1.0)
- Aggregates risks across the portfolio

## Requirements
- Python 3.x
- pandas
- yfinance
- pandas_market_calendars

## Note
- Target date must be a valid options expiration date
- Results are for reference only
