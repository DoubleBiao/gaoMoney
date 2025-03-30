# Portfolio Risk Predictor Web Application

A Flask-based web application for portfolio risk prediction that enables users to dynamically adjust portfolio parameters and view risk prediction results in real-time.

## Features

- Interactive portfolio parameter editing (stock shares, benchmark indices, beta factors, option quantities)
- Real-time risk prediction updates
- Visual representation of prediction results through interactive charts
- Comprehensive market scenario analysis
- Support for both stock and option portfolio analysis

## Installation

1. Clone the repository and navigate to the predictor directory:
```bash
cd predictor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure E*TRADE API:
- Create a `config.json` file in the project root with valid API credentials
- File format:
```json
{
    "etrade": {
        "consumer_key": "YOUR_CONSUMER_KEY",
        "consumer_secret": "YOUR_CONSUMER_SECRET",
        "sandbox": false
    }
}
```

4. Prepare portfolio data:
- Create a `portfolio.csv` file in the project root
- Required columns: symbol, shares, benchmark, adjustment, options
- Example format:
```csv
symbol,shares,benchmark,adjustment,options
AAPL,100,SPY,1.2,10
GOOGL,50,QQQ,1.1,5
```

## Running the Application

Start the Flask application:
```bash
python app.py
```

Access the web interface at `http://127.0.0.1:8080`

## Usage Guide

1. Portfolio Management:
   - Click on table cells to edit portfolio parameters
   - Adjust stock shares, benchmark indices, and beta factors
   - Modify option quantities as needed

2. Risk Analysis:
   - The application provides three key metrics:
     - Total Return: Combined impact of stock and option positions
     - Stock Price Impact: Direct effect of market movements on stock value
     - Option Impact: Changes in option values under different scenarios

3. Market Scenarios:
   - Drop Scenario: Analysis of portfolio performance in bearish markets
   - Rise Scenario: Analysis of portfolio performance in bullish markets
   - Probability range: -120% to +120% market movement

4. Interactive Charts:
   - Hover over chart lines to view detailed values
   - Use the toolbar to zoom, pan, or download the chart
   - Toggle different metrics using the legend

## Project Structure

```
predictor/
├── app.py                    # Flask application main file
├── requirements.txt          # Project dependencies
├── models/                   # Prediction models
│   └── portfolio_predictor.py
├── templates/               # HTML templates
│   └── index.html
└── README.md               # Project documentation
```

## Security Notes

- Never commit API credentials or sensitive data
- Keep your `config.json` and portfolio data files private
- Use environment variables for production deployments

## Troubleshooting

1. API Connection Issues:
   - Verify API credentials in config.json
   - Ensure network connectivity
   - Check E*TRADE API service status

2. Data Display Problems:
   - Confirm CSV file format is correct
   - Verify all required columns are present
   - Check for valid numeric values in data fields 