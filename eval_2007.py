import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Define the time range
start_date = "2006-08-01"
end_date = "2009-06-30"

# Download S&P 500 data
sp500_data = yf.download("^GSPC", start=start_date, end=end_date)

# Display the first few rows of the data
print(sp500_data.head())

# Plot the data
plt.figure(figsize=(14, 7))
plt.plot(sp500_data.index, sp500_data['Close'], label="S&P 500")
plt.title("S&P 500 Performance (2007-2008)")
plt.xlabel("Date")
plt.ylabel("Close Price")
plt.legend()
plt.grid(True)
plt.show()