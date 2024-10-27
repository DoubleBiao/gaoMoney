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

# def normalize(s):
#     return (s - np.mean(s))/np.std(s)

def window_normalize(s, ws = 5):
    #kernel is window differece. It minus the current value to the mean value in the window
    # kernel = np.zeros(ws, dtype=np.float32)
    # kernel[int(ws/2)] = 1
    # kernel = kernel - np.ones(ws, dtype=np.float32)/ws
    # output = np.convolve(s, kernel, mode='same')

    # pad_len = int(ws/2)
    # pad_s = np.concatenate((np.ones(pad_len)*s[0], s, np.ones(pad_len)*s[-1]))
    # res = np.zeros(s.size, dtype=np.float32)
    # for i in range(len(s)):
    #     shift_i = i + pad_len
    #     res[i] = pad_s[shift_i] / np.mean(pad_s[shift_i - pad_len : shift_i + pad_len])

    pad_s = np.concatenate((np.ones(ws - 1)*s[0], s))
    res = np.zeros(s.size, dtype=np.float32)
    for i in range(len(s)):
        shift_i = i + ws
        res[i] = pad_s[shift_i - 1] / np.mean(pad_s[shift_i - ws : shift_i])
    return res

    # return s

def parse_arg():
    parser = argparse.ArgumentParser(description='Evaluate the relevance between two stocks?')
    parser.add_argument('--start-date', '-s', type=str, default=datetime.today().date().strftime("%Y-%m-%d"))
    parser.add_argument('--span-in-yr', '-sy', type=int, default=30)
    parser.add_argument('--span-in-month', '-sm', type=int, default=0)
    parser.add_argument('--smoth-window-size', '-ws', type=int, default=30)
    

    parser.add_argument('--stock', '-st', metavar='string', type=str, default="^GSPC")
    args = parser.parse_args()
    
    return args


args = parse_arg()
span = args.span_in_yr*365 if args.span_in_month == 0 else args.span_in_month*30

stk = get_data_before(args.stock, args.start_date, span)


#crop invalid convolution part
v = window_normalize(stk['Volume'].values, args.smoth_window_size)
#align stock value range to volume
s = stk['Close'].values

assert(v.size == s.size)
x = np.array(range(s.size))

# Create the first plot
fig, ax1 = plt.subplots()

# Plot the first curve on the primary y-axis
ax1.plot(x, s, 'g-', label="S")  # 'g-' for green solid line
ax1.set_xlabel('X-axis')
ax1.set_ylabel('close price', color='g')    # Set the label color for y1
ax1.tick_params(axis='y', labelcolor='g') # Set the tick color for y1

# Create the secondary y-axis
ax2 = ax1.twinx()

# # Plot the second curve on the secondary y-axis
ax2.bar(x, v, alpha=0.6, label="V")  # 'b-' for blue solid line
ax2.set_ylabel('volume', color='b')    # Set the label color for y2
ax2.tick_params(axis='y', labelcolor='b')   # Set the tick color for y2

# Optional: Add legends for clarity
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
plt.show()