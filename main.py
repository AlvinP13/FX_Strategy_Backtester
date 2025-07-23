import sys
import os
sys.path.append(os.path.abspath("C:/Users/alvin/Downloads/FX_Backtester")) # To be able to access all .py files in the main directory

from backtesting import Backtest # To run the backtest
from strategies.sma_crossover import optimize_sma_strategy
from strategies.ema_crossover import optimize_ema_strategy
from strategies.momentum import optimize_mm_strategy
from strategies.mean_reversion import optimize_mr_strategy
from strategies.momentum import combined_optimal_strategy
from strategies.momentum import combined_optimal_strategy1
import pandas as pd

# Data Menu _. Allow users to select currency pair
def data_menu():
    print('---------------------------------------------')
    print('                  DATA MENU                  ')
    print('---------------------------------------------')
    print('(1) EUR/USD')
    print('(2) USD/JPY')
    print('(3) GBP/USD')
    print('(4) USD/INR')
    print('(5) USD/ZAR')
    user2 = int(input("Enter menu number: "))
    fx_list = ["eurusd","usdjpy","gbpusd","usdinr","usdzar"]
    pair = fx_list[user2-1]
    return pair

# Tiem Menu -> Allow users to select Time Frame for Backtest
def time_menu():
    print('--------------------------------------------')
    print('               TIMEFRAME MENU               ')
    print('--------------------------------------------')
    print('(1) 1 Year')
    print('(2) 6 Months')
    print('(3) 5 Days')
    user3 = int(input("Enter menu number: "))
    time_list = ["1y","6mo","5d"]
    time = time_list[user3-1]
    if user3 in (1,2):
        interval = ""
    elif user3 == 3:
        interval = "m"
    return time,interval

# Dataframe Extraction
def df_extraction(pair,time,interval):
    df = pd.read_csv("C:/Users/alvin/Downloads/FX_Backtester/data/"+pair+"_"+time+interval) # Importing data
    
    # Ensure full UTC(Coordinated Universal Time) parsing and timezone awareness
    df['Date'] = pd.to_datetime(df['Date'], utc=True)

    # Set Date as the index
    df.set_index('Date', inplace=True)

    # Drop unused columns (reduces noise)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']] # Can drop Volume as it is =0 for FX trades
    return df

def output_tracker(pair,time,interval,df,optimize_strategy,strategy_no):
    if os.path.exists("C:/Users/alvin/Downloads/FX_Backtester/outputs/"+str(strategy_no)+"/"+pair+"_"+time+interval+"_results.html"):
        print("Outputs already exist")
        print("C:/Users/alvin/Downloads/FX_Backtester/outputs/"+str(strategy_no)+"/"+pair+"_"+time+interval+"_results.html")
        print("C:/Users/alvin/Downloads/FX_Backtester/metrics/"+str(strategy_no)+"_metrics.csv")
    else:
        strategy_class, best_params, net_ret = optimize_strategy(df,time) # Optimizing function from sma_crossover
        
        # cash -> initial capital in the portfolio
        # Brokers charge comissions in the form of per-trade comission (usually flat) or spreads.
        # commission -> transaction cost per trade (expressed as a proportion of trade value) -> generally 0.1%-0.2% 
        # spreads (not included by default) -> the difference between ask(buy) & bid(sell) price (i.e. Ask-Bid) -> e.g. spread = 0.0002 = 2 pips
        bt = Backtest(df,strategy_class,cash=10000,commission=0.0002, trade_on_close=True) 
        results = bt.run()
        print(results) # gives raw backtest data
        results.to_frame().T.to_csv("C:/Users/alvin/Downloads/FX_Backtester/metrics/"+str(strategy_no)+"_metrics.csv",mode="a",index=False)
        bt.plot(filename="C:/Users/alvin/Downloads/FX_Backtester/outputs/"+str(strategy_no)+"/"+pair+"_"+time+interval+"_results.html", open_browser=False)
    
# Main Menu
def main_menu():
    while True:
        print('---------------------------------------------')
        print('                  MAIN MENU                  ')
        print('---------------------------------------------')
        print('(1) SMA Crossover Strategy')
        print('(2) Momentum Strategy')
        print('(3) Mean Reversion Strategy')
        print('(4) EMA Crossover Strategy')
        print('(5) Exit')
        user1 = int(input("Enter menu number: "))
        
        if user1 == 1:
            print('----------------------------------------------')
            print('                SMA STRATEGIES                ')
            print('----------------------------------------------')
            print('(1) SMA1 - Optimized for Max. Net Return')
            print('(2) SMA2 - SMA + Momentum strategy Optimized for Max. Net Return')
            print('(3) Return to Main Menu')
            user5 = int(input("Enter menu number: "))
            if user5 == 1:
                pair = data_menu()
                time, interval = time_menu()
                df = df_extraction(pair, time, interval)
                
                # Running backtest
                output_tracker(pair,time,interval,df,optimize_sma_strategy,strategy_no="sma1")
                
            elif user5 == 2:
                pair = data_menu()
                time, interval = time_menu()
                df = df_extraction(pair, time, interval)
                
                # Running backtest
                output_tracker(pair,time,interval,df,combined_optimal_strategy,strategy_no="sma2")
                
            elif user5 == 3:
                continue
            else:
                print("Please enter a valid input")
                
        elif user1 == 2:
            print('-----------------------------------------------')
            print('              MOMENTUM STRATEGIES              ')
            print('-----------------------------------------------')
            print('(1) MM1 - Optimized for Max. Net Return')
            print('(2) MM2 - SMA + Momentum strategy Optimized for Max. Net Return')
            print('(3) Return to Main Menu')
            user6 = int(input("Enter menu number: "))
            if user6 == 1:
                pair = data_menu()
                time, interval = time_menu()
                df = df_extraction(pair, time, interval)
                
                # Running backtest
                output_tracker(pair,time,interval,df,optimize_mm_strategy,strategy_no="mm1")
                
            elif user6 == 2:
                pair = data_menu()
                time, interval = time_menu()
                df = df_extraction(pair, time, interval)
                
                # Running backtest
                output_tracker(pair,time,interval,df,combined_optimal_strategy,strategy_no="mm2")
                
            elif user6 == 3:
                continue
            else:
                print("Please enter a valid input")
                
        elif user1 == 3:
            print('-----------------------------------------------')
            print('           MEAN REVERSION STRATEGIES           ')
            print('-----------------------------------------------')
            print('(1) MR1 - Optimized for Max. Net Return')
            print('(2) Return to Main Menu')
            user7 = int(input("Enter menu number: "))
            if user7 == 1:
                pair = data_menu()
                time, interval = time_menu()
                df = df_extraction(pair, time, interval)
                
                # Running backtest
                output_tracker(pair,time,interval,df,optimize_mr_strategy,strategy_no="mr1")
                
            elif user7 == 2:
                continue
            else:
                print("Please enter a valid input")
                
        elif user1 == 4:
            print('----------------------------------------------')
            print('                EMA STRATEGIES                ')
            print('----------------------------------------------')
            print('(1) EMA1 - Optimized for Max. Net Return')
            print('(2) EMA2 - EMA + Momentum strategy Optimized for Max. Net Return')
            print('(4) Return to Main Menu')
            user8 = int(input("Enter menu number: "))
            if user8 == 1:
                pair = data_menu()
                time, interval = time_menu()
                df = df_extraction(pair, time, interval)
                
                # Running backtest
                output_tracker(pair,time,interval,df,optimize_ema_strategy,strategy_no="ema1")
                
            elif user8 == 2:
                pair = data_menu()
                time, interval = time_menu()
                df = df_extraction(pair, time, interval)
                
                # Running backtest
                output_tracker(pair,time,interval,df,combined_optimal_strategy1,strategy_no="ema2")
                
            elif user8 == 3:
                continue
            else:
                print("Please enter a valid input")
        else:
            break
            
main_menu()
