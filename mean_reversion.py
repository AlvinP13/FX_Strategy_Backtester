from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np

# Declaring threshold values (scaled according to time period)
y1_threshold = 2.5  # The Z-score required to trigger a trade
mo6_threshold = 1.75
days5_threshold = 1.5
threshold_list = [y1_threshold, mo6_threshold, days5_threshold]

# Calculating indicator values
def z_scores(values, period):
    s = pd.Series(values)
    sma = s.rolling(period).mean() # Find the SMA (treated as the "mean" value here) on a rolling basis
    std = s.rolling(period).std() # Find standard deviation of close prices on a rolling basis
    z = (s - sma) / std # Formula to calculate Z-scores
    return z.to_numpy()

# NOTE: Tried sequential -> Too inactive and was constantly making negative returns (only very slightly positive profits which are eaten up by commissions)
# Stricter threshold helps
# waiting till price returns to 0 tends to perform better than exiting earlier

# MR1 strategy optimization
def optimize_mr_strategy(df, time):
    net_return = -np.inf
    best_params = None
    
    if time == "1y":
        threshold = threshold_list[0]
    elif time == "6mo":
        threshold = threshold_list[1]
    else:
        threshold = threshold_list[2]

    # MR1 -> Finding the optimal time window for mean reversion-based Strategy that results in the highest net return
    for window in range(3, 20):
        class MeanReversion1(Strategy):
            def init(self):
                self.z = self.I(z_scores, self.data.Close, window)

            def next(self):
                if np.isnan(self.z[-1]):  # avoid NaNs
                    return

                # Exit a long trade when price is closer to the mean (i.e. price is returning to the expected average value -> no more gains)
                if self.position.is_long and self.z[-1] >= 0:
                    self.position.close()
                    self.sell()
                # Exit a short trade when price is closer to the mean (i.e. price is returning to the expected average value -> no more gains)
                elif self.position.is_short and self.z[-1] <= 0:
                    self.position.close()
                    self.buy()

                # Entering trades when there are significant deviations from mean value
                elif not self.position:
                    if self.z[-1] > threshold:
                        self.buy()
                    elif self.z[-1] < -threshold:
                        self.sell()

        cash = 10000
        bt = Backtest(df, MeanReversion1, cash=cash, commission=0.0002)
        stats = bt.run()
        current_return = (stats["Equity Final [$]"] - cash) / cash

        if current_return > net_return:
            net_return = current_return
            best_params = window

    # Final optimal window MRStrategy implementation -> to be passed into main module
    class MRStrategy1(Strategy):
        def init(self):
            print("Using optimized parameter -> Time window:", best_params)
            self.z_optimal = self.I(z_scores, self.data.Close, best_params)

        def next(self):
            if np.isnan(self.z_optimal[-1]):  # avoid NaNs
                return

            # Exit a long trade when price is closer to the mean (i.e. price is returning to the expected average value -> no more gains)
            if self.position.is_long and self.z_optimal[-1] >= 0:
                self.position.close()
                self.sell()
            # Exit a short trade when price is closer to the mean (i.e. price is returning to the expected average value -> no more gains)
            elif self.position.is_short and self.z_optimal[-1] <= 0:
                self.position.close()
                self.buy()

            # Entering trades when there are significant deviations from mean value
            elif not self.position:
                if self.z_optimal[-1] > threshold:
                    self.buy()
                elif self.z_optimal[-1] < -threshold:
                    self.sell()

    return MRStrategy1, best_params, net_return