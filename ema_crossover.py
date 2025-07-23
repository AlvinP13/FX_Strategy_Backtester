from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import numpy as np

# This function calculates the EMA indicator values
def EMA(values, period):
    ema = np.full(len(values), np.nan) # Creates a numpy array filled with NaN
    alpha = 2 / (period + 1) 
    ema[period - 1] = np.mean(values[:period]) # Formula for calculating MA on a rolling basis
    
    # initial EMA value = NaN 
    for i in range(period, len(values)):
        ema[i] = alpha * values[i] + (1 - alpha) * ema[i - 1] # Standard formula for EMA -> alpha*current_price + (1-alpha)*past_ema
    return ema
            
def optimize_ema_strategy(df, time):
    net_return = -np.inf
    best_params = None

    for fast in range(3, 20):
        for slow in range(fast + 1, 60):
            class CustomEMA(Strategy):
                def init(self):  
                    self.ema_fast = self.I(EMA, self.data.Close, fast)  
                    self.ema_slow = self.I(EMA, self.data.Close, slow)

                def next(self): 
                        if self.position.is_long and crossover(self.ema_slow, self.ema_fast):
                            self.position.close()
                            self.sell()
                        elif self.position.is_short and crossover(self.ema_fast, self.ema_slow):
                            self.position.close()
                            self.buy()
                        elif not self.position:
                            if crossover(self.ema_fast, self.ema_slow):
                                self.buy()  
                            elif crossover(self.ema_slow, self.ema_fast):
                                self.sell()  

            cash = 10000
            bt = Backtest(df, CustomEMA, cash=cash, commission=0.0002, trade_on_close=True)
            stats = bt.run()
            current_return = (stats['Equity Final [$]'] - cash) / cash 

            if current_return > net_return:  
                net_return = current_return
                best_params = (fast, slow)                     

    # Final optimal window SMA Strategy implementation -> to be passed into main module
    class EMACrossover1(Strategy):
        def init(self):
            print("Using optimized parameters -> Fast:", best_params[0], "Slow:", best_params[1])
            self.ema_optimalfast = self.I(EMA, self.data.Close, best_params[0])
            self.ema_optimalslow = self.I(EMA, self.data.Close, best_params[1])

        def next(self):
                if self.position.is_long and crossover(self.ema_optimalslow, self.ema_optimalfast):
                    self.position.close()
                    self.sell()
                elif self.position.is_short and crossover(self.ema_optimalfast, self.ema_optimalslow):
                    self.position.close()
                    self.buy()
                elif not self.position:
                    if crossover(self.ema_optimalfast, self.ema_optimalslow):
                        self.buy()
                    elif crossover(self.ema_optimalslow, self.ema_optimalfast):
                        self.sell()

    return EMACrossover1, best_params, net_return