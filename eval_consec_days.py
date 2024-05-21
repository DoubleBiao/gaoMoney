import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_data_before(end_date_str, span):
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days = span)
    start_date_str = start_date.strftime("%Y-%m-%d")


    # Use the Ticker module to get the S&P 500 data
    sp500 = yf.Ticker("^GSPC")

    # Get historical market data
    return sp500.history(start = start_date_str, end = end_date_str)

def get_diff_pct_data_before(end_date_str, span):
    return get_data_before(end_date_str, span)['Close'].pct_change()*100
    
    return diff_series.values[1:]

def get_diff_data_before(end_date_str, span):
    return get_data_before(end_date_str, span)['Close'].diff()
    
    return diff_series.values[1:]

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
        return self.m_ap(data[p: p + self.m_ws])

if __name__ == "__main__":
    import sys
    data = get_diff_pct_data_before(sys.argv[1], int(sys.argv[2])*365)
    print("length of data:", data.size)

    print("when consective drop happens, the probability that the next day rise")
    rise = lambda x: x > 0
    drop = lambda x: x <= 0
    SlideWindow(int(sys.argv[3]), rise, drop)(data)
    
    print("")
    print("")
    print("")
    print("when consective drop happens, the probability that marcket price come back after the same days")
    data2 = get_diff_data_before(sys.argv[1], int(sys.argv[2])*365)
    rise_back = lambda vec: vec[-1] > vec[0]
    all_drop = lambda vec: all([x <= 0 for x in vec])
    DualWindows(int(sys.argv[3]), rise_back, all_drop)(data)
