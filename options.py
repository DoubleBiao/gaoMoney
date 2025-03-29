import yfinance as yf

# Specify the stock ticker symbol
ticker_symbol = 'AAPL'  # Example for Apple Inc.

# Create a Ticker object
ticker = yf.Ticker(ticker_symbol)

# Get the list of expiration dates for options
exp_dates = ticker.options

start_date = "2006-08-01"
end_date = "2009-06-30"

print(ticker.options)


# Initialize total open interest for puts and calls
total_put_oi = 0
total_call_oi = 0

# Iterate through all expiration dates and accumulate open interest
for date in exp_dates:
    options = ticker.option_chain(date)
    puts = options.puts
    calls = options.calls

    total_put_oi += puts['openInterest'].sum()
    total_call_oi += calls['openInterest'].sum()

# Calculate the Put/Call open interest ratio
put_call_oi_ratio = total_put_oi / total_call_oi if total_call_oi != 0 else 0

print(f"Put/Call Open Interest Ratio: {put_call_oi_ratio:.2f}")