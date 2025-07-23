from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import numpy as np

# This function computes the rolling mean internally and immediately returns the final output as a NumPy array -> can be directly passed to .I()
def SMA(values, period):
    weights = np.ones(period) / period  # equal weights
    sma = np.convolve(values, weights, mode='valid')  # np.convolve() applies the weights as a sliding window dot product across values (mode='valid' -> output only starts once the full window fits into the input)
    return np.concatenate([np.full(period - 1, np.nan), sma])  # first period - 1 SMA values don’t exist (not enough data) -> sub. with NaN

# Issue: Some crossovers are ignored by the default function as the SMA values are equal or nearly equal -> Smaller timeframes are more prone to this
# Solution: Define a tolerant crossover function that checks multiple recent bars with a small buffer (tolerance) to catch subtle or flat crossovers
def tolerant_crossover_buy(a, b, tol=1e-6):
    for i in range(1, 3):  # look back 2 bars
        if not np.isnan(a[-i - 1]) and not np.isnan(b[-i - 1]) and not np.isnan(a[-i]) and not np.isnan(b[-i]):
            if a[-i - 1] <= b[-i - 1] + tol and a[-i] > b[-i] + tol:
                return True
    return False

def tolerant_crossover_sell(a, b, tol=1e-6):
    for i in range(1, 3):  # look back 2 bars
        if not np.isnan(a[-i - 1]) and not np.isnan(b[-i - 1]) and not np.isnan(a[-i]) and not np.isnan(b[-i]):
            if a[-i - 1] >= b[-i - 1] - tol and a[-i] < b[-i] - tol:
                return True
    return False

# Function to find the best-performing SMA crossover strategy based on net return
def optimize_sma_strategy(df, time):
    # Initializing parameters
    net_return = -np.inf
    best_params = None

    # SMA1 -> Finding the optimal fast & slow time windows for SMA Strategy that result in the highest net return [fast->(3,19)/slow->(fast+1,59)]
    for fast in range(3, 20):
        for slow in range(fast + 1, 60):
            class CustomSMA(Strategy):
                def init(self):  # This function initializes the indicators we need to run the crossover strategy on (i.e. calculates SMA values) -> Only run once to obtain the indicator values
                    self.sma_fast = self.I(SMA, self.data.Close, fast)  # self.I() -> Provides backtesting engine with the required indicators
                    self.sma_slow = self.I(SMA, self.data.Close, slow)

                def next(self):  # This function runs on every new bar of data to evaluate and execute trading logic
                    if time == "5d":
                        # If holding a long position and the fast SMA crosses below the slow SMA, reverse to a short
                        if self.position.is_long and tolerant_crossover_sell(self.sma_fast, self.sma_slow):
                            self.position.close()
                            self.sell()  
                        # If holding a short position and the fast SMA crosses above the slow SMA, reverse to a long
                        elif self.position.is_short and tolerant_crossover_buy(self.sma_fast, self.sma_slow):
                            self.position.close()
                            self.buy()
                        # If no position is currently open, enter based on crossover signals
                        elif not self.position:
                            if tolerant_crossover_buy(self.sma_fasft, self.sma_slow):
                                self.buy()  # Enter long if fast SMA crosses above slow SMA
                            elif tolerant_crossover_sell(self.sma_fast, self.sma_slow):
                                self.sell()  # Enter short if fast SMA crosses below slow SMA
                    else:
                        # If holding a long position and a downward crossover occurs, reverse to a short
                        if self.position.is_long and crossover(self.sma_slow, self.sma_fast):
                            self.position.close()
                            self.sell()
                        # If holding a short position and an upward crossover occurs, reverse to a long
                        elif self.position.is_short and crossover(self.sma_fast, self.sma_slow):
                            self.position.close()
                            self.buy()
                        # If no position is currently open, enter based on crossover signals
                        elif not self.position:
                            if crossover(self.sma_fast, self.sma_slow):
                                self.buy()  # Enter long on upward SMA crossover
                            elif crossover(self.sma_slow, self.sma_fast):
                                self.sell()  # Enter short on downward SMA crossover

            # Backtesting given pair of fast & slow windows
            cash = 10000
            bt = Backtest(df, CustomSMA, cash=cash, commission=0.0002, trade_on_close=True)
            stats = bt.run()
            current_return = (stats['Equity Final [$]'] - cash) / cash  # Checking net return

            if current_return > net_return:  # Keeping best parameters so far
                net_return = current_return
                best_params = (fast, slow)

    # Final optimal window SMA1 Strategy implementation -> to be passed into main module
    class SMACrossover1(Strategy):
        def init(self):
            print("Using optimized parameters -> Fast:", best_params[0], "Slow:", best_params[1])
            self.sma_optimalfast = self.I(SMA, self.data.Close, best_params[0])
            self.sma_optimalslow = self.I(SMA, self.data.Close, best_params[1])

        def next(self):
            if time == "5d":
                if self.position.is_long and tolerant_crossover_sell(self.sma_optimalfast, self.sma_optimalslow):
                    self.position.close()
                    self.sell()  # Close long & open short
                elif self.position.is_short and tolerant_crossover_buy(self.sma_optimalfast, self.sma_optimalslow):
                    self.position.close()
                    self.buy()   # Close short & open long
                elif not self.position:
                    if tolerant_crossover_buy(self.sma_optimalfast, self.sma_optimalslow):
                        self.buy()
                    elif tolerant_crossover_sell(self.sma_optimalfast, self.sma_optimalslow):
                        self.sell()
            else:
                if self.position.is_long and crossover(self.sma_optimalslow, self.sma_optimalfast):
                    self.position.close()
                    self.sell()
                elif self.position.is_short and crossover(self.sma_optimalfast, self.sma_optimalslow):
                    self.position.close()
                    self.buy()
                elif not self.position:
                    if crossover(self.sma_optimalfast, self.sma_optimalslow):
                        self.buy()
                    elif crossover(self.sma_optimalslow, self.sma_optimalfast):
                        self.sell()

    return SMACrossover1, best_params, net_return
