import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import argparse
from scipy.signal import correlate
import numpy as np 

import matplotlib.pyplot as plt

def get_data_before(stock, end_date_str, span):
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days = span)
    start_date_str = start_date.strftime("%Y-%m-%d")


    # Use the Ticker module to get the S&P 500 data
    s = yf.Ticker(stock)

    # Get historical market data
    return s.history(start = start_date_str, end = end_date_str)

def normalize(s):
    return (s - np.mean(s))/np.std(s)

def parse_arg():
    parser = argparse.ArgumentParser(description='Evaluate the relevance between two stocks?')
    parser.add_argument('--start-date', '-s', type=str, default=datetime.today().date().strftime("%Y-%m-%d"))
    parser.add_argument('--span-in-yr', '-sy', type=int, default=30)
    parser.add_argument('--span-in-month', '-sm', type=int, default=0)
    

    parser.add_argument('--stock1', '-s1', metavar='string', type=str, default="^GSPC")
    parser.add_argument('--stock2', '-s2', metavar='string', type=str, default="^IXIC")

    parser.add_argument('--time-window', '-tw', type=int, default=10)


    args = parser.parse_args()
    
    return args

args = parse_arg()
span = args.span_in_yr*365 if args.span_in_month == 0 else args.span_in_month*30

s1 = get_data_before(args.stock1, args.start_date, span)['Close'].values
s1 = normalize(s1)

s2 = get_data_before(args.stock2, args.start_date, span)['Close'].values
s2 = normalize(s2)


print(s1.shape)

res = correlate(s1, s2)/s1.shape[0]
mid = int(res.shape[0]/2)

print(res[mid - args.time_window: mid + args.time_window+1])
print("max: ", max(res), "when:", np.argmax(res) - mid)

plt.plot(s1, label = args.stock1)
plt.plot(s2, label = args.stock2)
plt.legend()
plt.show()
