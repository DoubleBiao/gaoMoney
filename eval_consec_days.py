import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import argparse

def get_data_before(stock, end_date_str, span):
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days = span)
    start_date_str = start_date.strftime("%Y-%m-%d")


    # Use the Ticker module to get the S&P 500 data
    sp500 = yf.Ticker(stock)

    # Get historical market data
    return sp500.history(start = start_date_str, end = end_date_str)

# def get_diff_pct_data_before(end_date_str, span):
#     return get_data_before(end_date_str, span)['Close'].pct_change()*100
    
#     return diff_series.values[1:]

# def get_diff_data_before(end_date_str, span):
#     return get_data_before(end_date_str, span)['Close'].diff()
    
#     return diff_series.values[1:]

# check the possible P(A|B) = P(AB)/P(B),
# B: for all data in the time-window, B_policy is true
# A: for the data right next to the time window, A_policy is true
class SlideWindow:
    def __init__(self, window_size, A_policy, B_policy):
        self.m_ws = window_size
        self.m_ap = A_policy
        self.m_bp = B_policy

    def window_end(self, data):
        # same fashion as C++ end() in [Start, End)
        return data.size - self.m_ws
    
    def B_hold(self, data, p):
        return all([self.m_bp(x) for x in data[p: p + self.m_ws]])
    
    def A_hold(self, data, p):
        return self.m_ap(data[p+self.m_ws])
    
    def A_freq(self, data):
        return sum(self.A_hold(data, i) for i in range(self.window_end(data)))

    def B_freq(self, data):
        return sum(self.B_hold(data, i) for i in range(self.window_end(data)))
    
    def AB_freq(self, data):
        return sum(self.A_hold(data, i) and self.B_hold(data, i) 
                for i in range(self.window_end(data)))
    
    def __call__(self, data):
        print("compuate P(A|B) = P(AB)/P(B)")
        Af = self.A_freq(data)
        Bf=  self.B_freq(data)
        ABf = self.AB_freq(data)
        print("A frequency: ", Af)
        print("B frequency: ", Bf)
        print("AB frequency: ", ABf)

        if Bf == 0:
            print("did not find any situation B(consecutive happen in {} days)".format(self.m_ws))
        else:
            print("P(A|B) = {}%".format(ABf*100.0 / Bf))

# check the possible P(A|B) = P(AB)/P(B),
# B: for the firt time-window, B_policy is true
# B: for the the next window, A_policy is true
class DualWindows(SlideWindow):
    def window_end(self, data):
        # same fashion as C++ end() in [Start, End)
        return data.size - 2*self.m_ws
    
    def B_hold(self, data, p):
        return self.m_bp(data[p: p + self.m_ws])
    
    def A_hold(self, data, p):
        return self.m_ap(data[p: p + 2*self.m_ws])

def parse_arg():
    parser = argparse.ArgumentParser(description='what would happen if consecutive drops has happened?')
    parser.add_argument('--start-date', '-s', type=str, default=datetime.today().date().strftime("%Y-%m-%d"))
    parser.add_argument('--span-in-yr', '-sy', type=int, default=30)
    parser.add_argument('--consecutive-days', '-c', type=int, default=5)

    parser.add_argument('--stocks', '-st', metavar='string', type=str, nargs='+', default=["^GSPC"])


    args = parser.parse_args()
    
    return args

def check_stock(stock, args):
    print("=================================================================================================")
    print("check stock ", stock)

    print("")
    data = get_data_before(stock, args.start_date, args.span_in_yr*365)
    print("length of data:", data.size)

    print("when consective drop happens, the probability that rise the next day rise")
    rise = lambda x: x > 0
    drop = lambda x: x <= 0
    SlideWindow(args.consecutive_days, rise, drop)((data['Close'].pct_change()*100).values[1:])
    
    print("")
    print("when consective drop happens, the probability that marcket price come back after the same days")
    rise_back = lambda vec: sum(vec) > 0
    all_drop = lambda vec: all([x <= 0 for x in vec])
    DualWindows(args.consecutive_days, rise_back, all_drop)(data['Close'].diff().values[1:])

    print("")
    print("when there is a huge drop, the probability that rise the next day rise")
    rise = lambda vec: vec[args.consecutive_days] > vec[args.consecutive_days - 1]
    huge_drop = lambda vec: (vec[-1] - vec[0])/vec[0] < -0.05
    DualWindows(args.consecutive_days, rise, huge_drop)(data['Close'].values)

    print("")
    print("when there is a huge drop, the probability that marcket price come back after the same days")
    rise_back = lambda vec: vec[-1] > vec[0]
    huge_drop = lambda vec: (vec[-1] - vec[0])/vec[0] < -0.05
    DualWindows(args.consecutive_days, rise_back, huge_drop)(data['Close'].values[1:])

    print("")
    print("when there is a huge drop, the probability that gain after the same days")
    rise = lambda vec: vec[-1] > vec[args.consecutive_days-1]
    huge_drop = lambda vec: (vec[-1] - vec[0])/vec[0] < -0.05
    DualWindows(args.consecutive_days, rise, huge_drop)(data['Close'].values[1:])

if __name__ == "__main__":
    args = parse_arg()

    print("what happened if market drop in {} consecutive days, the record check {} years starting from {}".format(
        args.consecutive_days, args.span_in_yr, args.start_date
    ))
    
    for s in args.stocks:
        check_stock(s, args)


