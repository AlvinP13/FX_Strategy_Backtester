from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np
from joblib import Parallel, delayed
import itertools

# Declaring threshold values (scaled according to time period)
y1_threshold = 0.02  # % change w.r.t. recent price required to enter/exit a trade
mo6_threshold = 0.01
days5_threshold = 0.002
threshold_list = [y1_threshold, mo6_threshold, days5_threshold]

# Calculating SMA indicator values
def SMA(values, period):
    weights = np.ones(period) / period  
    sma = np.convolve(values, weights, mode='valid') 
    return np.concatenate([np.full(period - 1, np.nan), sma])

# Calculating EMA indicator values
def EMA(values, period):
    ema = np.full(len(values), np.nan) # Creates a numpy array filled with NaN
    alpha = 2 / (period + 1) 
    ema[period - 1] = np.mean(values[:period]) # Formula for calculating MA on a rolling basis
    
    # initial EMA value = NaN 
    for i in range(period, len(values)):
        ema[i] = alpha * values[i] + (1 - alpha) * ema[i - 1] # Standard formula for EMA -> alpha*current_price + (1-alpha)*past_ema
    return ema

# Calculating momentum indicator values
def momentum(values, period):
    s = pd.Series(values)
    momentum_series = (s - s.shift(period)) / s.shift(period)  # .shift() allows us to calculate values across a rolling time window
    return momentum_series.to_numpy()  # converting to NumPy for self.I() compatibility

def optimize_mm_strategy(df, time):
    net_return = -np.inf
    best_params = None

    # Setting threshold based on input time period
    if time == "1y":
        threshold = threshold_list[0]
    elif time == "6mo":
        threshold = threshold_list[1]
    else:
        threshold = threshold_list[2]

    # MM1 -> Finding the optimal time window for momentum-based Strategy that results in the highest net return
    for window in range(3, 20):
        class CustomMM(Strategy):
            def init(self):
                self.momentum_indicator = self.I(momentum, self.data.Close, window)
                self.sma_slow = self.I(SMA, self.data.Close, slow)

            def next(self):
                if np.isnan(self.momentum_indicator[-2]) or np.isnan(self.momentum_indicator[-1]):  # avoid NaNs
                    return

                # Sequential logic: close existing position first before entering reverse trade (to avoid mis-judging momentum shifts)
                if self.position.is_long and self.momentum_indicator[-2] >= threshold and self.momentum_indicator[-1] < threshold:
                    self.position.close()  # Close long if momentum crosses below threshold
                elif self.position.is_short and self.momentum_indicator[-2] <= -threshold and self.momentum_indicator[-1] > -threshold:
                    self.position.close()  # Close short if momentum crosses above -threshold

                elif not self.position:
                    if self.momentum_indicator[-2] < threshold and self.momentum_indicator[-1] >= threshold:
                        self.buy()  # Enter long if momentum crosses above threshold
                    elif self.momentum_indicator[-2] > -threshold and self.momentum_indicator[-1] <= -threshold:
                        self.sell()  # Enter short if momentum crosses below -threshold

        cash = 10000
        bt = Backtest(df, CustomMM, cash=cash, commission=0.0002)
        stats = bt.run()
        current_return = (stats["Equity Final [$]"] - cash) / cash

        if current_return > net_return:
            net_return = current_return
            best_params = window

    # Final optimal window MMStrategy implementation -> to be passed into main module
    class MMStrategy1(Strategy):
        def init(self):
            print("Using optimized parameter -> Time window:", best_params)
            self.momentum_optimal = self.I(momentum, self.data.Close, best_params)

        def next(self):
            if np.isnan(self.momentum_optimal[-2]) or np.isnan(self.momentum_optimal[-1]):  # avoid NaNs
                return

            # Sequential logic: close existing position first
            if self.position.is_long and self.momentum_optimal[-2] >= threshold and self.momentum_optimal[-1] < threshold:
                self.position.close()
            elif self.position.is_short and self.momentum_optimal[-2] <= -threshold and self.momentum_optimal[-1] > -threshold:
                self.position.close()

            elif not self.position:
                if self.momentum_optimal[-2] < threshold and self.momentum_optimal[-1] >= threshold:
                    self.buy()
                elif self.momentum_optimal[-2] > -threshold and self.momentum_optimal[-1] <= -threshold:
                    self.sell()

    return MMStrategy1, best_params, net_return

# MM2 Strategy
def evaluate_combined_strategy(df, momentum_window, sma_window, momentum_threshold):
    class CustomCombined(Strategy):
        def init(self):
            self.mm_indicator = self.I(momentum, self.data.Close, momentum_window)
            self.sma_indicator = self.I(SMA, self.data.Close, sma_window)

        def next(self):
            if np.isnan(self.mm_indicator[-2]) or np.isnan(self.mm_indicator[-1]) or np.isnan(self.sma_indicator[-1]):
                return
            elif self.position.is_long and self.mm_indicator[-2] >= momentum_threshold and self.mm_indicator[-1] < momentum_threshold:
                self.position.close()
            elif self.position.is_short and self.mm_indicator[-2] <= -momentum_threshold and self.mm_indicator[-1] > -momentum_threshold:
                self.position.close()
            elif not self.position:
                if (self.mm_indicator[-2] < momentum_threshold and self.mm_indicator[-1] >= momentum_threshold) and self.data.Close > self.sma_indicator[-1]:
                    self.buy()
                elif (self.mm_indicator[-2] > -momentum_threshold and self.mm_indicator[-1] <= -momentum_threshold) and self.data.Close > self.sma_indicator[-1]:
                    self.sell()

    bt = Backtest(df, CustomCombined, cash=10000, commission=0.0002)
    stats = bt.run()
    net_return = (stats["Equity Final [$]"] - 10000) / 10000
    return momentum_window, sma_window, momentum_threshold, net_return

def combined_optimal_strategy(df, time):
    # --- Define parameter space ---
    momentum_windows = range(5, 21)
    sma_windows = range(6, 50)
    thresholds = np.arange(0.005, 0.03, 0.0025)

    param_grid = [
        (m, s, t)
        for m in momentum_windows
        for s in sma_windows if s > m
        for t in thresholds
    ]

    # --- Run parallel jobs ---
    results = Parallel(n_jobs=-1, backend='loky')(
        delayed(evaluate_combined_strategy)(df, m, s, t)
        for (m, s, t) in param_grid
    )

    # --- Select best parameters ---
    best_m, best_s, best_t, best_ret = max(results, key=lambda x: x[3])
    best_params = [best_m, best_s, best_t]

    # --- Final strategy class using best parameters ---
    class CombinedStrategy1(Strategy):
        def init(self):
            self.mm_indicator = self.I(momentum, self.data.Close, best_params[0])
            self.sma_indicator = self.I(SMA, self.data.Close, best_params[1])

        def next(self):
            if np.isnan(self.mm_indicator[-2]) or np.isnan(self.mm_indicator[-1]) or np.isnan(self.sma_indicator[-1]):
                return
            elif self.position.is_long and self.mm_indicator[-2] >= best_params[2] and self.mm_indicator[-1] < best_params[2]:
                self.position.close()
            elif self.position.is_short and self.mm_indicator[-2] <= -best_params[2] and self.mm_indicator[-1] > -best_params[2]:
                self.position.close()
            elif not self.position:
                if (self.mm_indicator[-2] < best_params[2] and self.mm_indicator[-1] >= best_params[2]) and self.data.Close > self.sma_indicator[-1]:
                    self.buy()
                elif (self.mm_indicator[-2] > -best_params[2] and self.mm_indicator[-1] <= -best_params[2]) and self.data.Close > self.sma_indicator[-1]:
                    self.sell()

    return CombinedStrategy1, best_params, best_ret

###########################################################################################################################################

# MM3 Strategy
def evaluate_combined_strategy1(df, momentum_window, ema_window, momentum_threshold):
    class CustomCombined1(Strategy):
        def init(self):
            self.mm_indicator = self.I(momentum, self.data.Close, momentum_window)
            self.ema_indicator = self.I(EMA, self.data.Close, ema_window)

        def next(self):
            if np.isnan(self.mm_indicator[-2]) or np.isnan(self.mm_indicator[-1]) or np.isnan(self.ema_indicator[-1]):
                return
            elif self.position.is_long and self.mm_indicator[-2] >= momentum_threshold and self.mm_indicator[-1] < momentum_threshold:
                self.position.close()
            elif self.position.is_short and self.mm_indicator[-2] <= -momentum_threshold and self.mm_indicator[-1] > -momentum_threshold:
                self.position.close()
            elif not self.position:
                if (self.mm_indicator[-2] < momentum_threshold and self.mm_indicator[-1] >= momentum_threshold) and self.data.Close > self.ema_indicator[-1]:
                    self.buy()
                elif (self.mm_indicator[-2] > -momentum_threshold and self.mm_indicator[-1] <= -momentum_threshold) and self.data.Close > self.ema_indicator[-1]:
                    self.sell()

    bt = Backtest(df, CustomCombined1, cash=10000, commission=0.0002)
    stats = bt.run()
    net_return = (stats["Equity Final [$]"] - 10000) / 10000
    return momentum_window, ema_window, momentum_threshold, net_return

def combined_optimal_strategy1(df, time):
    # --- Define parameter space ---
    momentum_windows = range(5, 21)
    ema_windows = range(6, 50)
    thresholds = np.arange(0.005, 0.03, 0.0025)

    param_grid = [
        (m, e, t)
        for m in momentum_windows
        for e in ema_windows if e > m
        for t in thresholds
    ]

    # --- Run parallel jobs ---
    results = Parallel(n_jobs=-1, backend='loky')(
        delayed(evaluate_combined_strategy)(df, m, e, t)
        for (m, e, t) in param_grid
    )

    # --- Select best parameters ---
    best_m, best_e, best_t, best_ret = max(results, key=lambda x: x[3])
    best_params = [best_m, best_e, best_t]

    # --- Final strategy class using best parameters ---
    class CombinedStrategy2(Strategy):
        def init(self):
            self.mm_indicator = self.I(momentum, self.data.Close, best_params[0])
            self.ema_indicator = self.I(EMA, self.data.Close, best_params[1])

        def next(self):
            if np.isnan(self.mm_indicator[-2]) or np.isnan(self.mm_indicator[-1]) or np.isnan(self.ema_indicator[-1]):
                return
            elif self.position.is_long and self.mm_indicator[-2] >= best_params[2] and self.mm_indicator[-1] < best_params[2]:
                self.position.close()
            elif self.position.is_short and self.mm_indicator[-2] <= -best_params[2] and self.mm_indicator[-1] > -best_params[2]:
                self.position.close()
            elif not self.position:
                if (self.mm_indicator[-2] < best_params[2] and self.mm_indicator[-1] >= best_params[2]) and self.data.Close > self.ema_indicator[-1]:
                    self.buy()
                elif (self.mm_indicator[-2] > -best_params[2] and self.mm_indicator[-1] <= -best_params[2]) and self.data.Close > self.ema_indicator[-1]:
                    self.sell()

    return CombinedStrategy2, best_params, best_ret