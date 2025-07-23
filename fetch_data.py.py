import yfinance as yf
import pandas as pd

# Creating the ticker object for the 5 currency pairs
fx1 = yf.Ticker("EURUSD=X") #Euro-US Dollar
fx2 = yf.Ticker("USDJPY=X") #US Dollar-Japanese Yen
fx3 = yf.Ticker("GBPUSD=X") #British Pound-US Dollar
fx4 = yf.Ticker("USDINR=X") #US Dollar-Indian Rupee
fx5 = yf.Ticker("USDZAR=X") #US Dollar-South African Rand

# Intervals - specifies the frequency of the data points within the time period
day1 = "1d"
min15 = "15m" #only works with shorter time periods 

# Time Periods - defines the total length of historical data to download
days5 = "5d"
months6 = "6mo"
year1 = "1y"

def fetch_and_save_fx(pair,filename,interval,period):
    data = pair.history(interval=interval, period=period) # Downloading historical FX data from Yahoo Finance
    data.dropna(subset="Close") # FX trades don't occur on weekends/holidays -> remove these datapoints to avoid confusion/false signals
    if period == "5d":
        data = data.reset_index().rename(columns={"Datetime": "Date"})
    data.to_csv(filename) # uploading data to CSV file
    
# Calling function -> 1 Year Timeframe
fetch_and_save_fx(fx1,"eurusd_1y",day1,year1)
fetch_and_save_fx(fx2,"usdjpy_1y",day1,year1)
fetch_and_save_fx(fx3,"gbpusd_1y",day1,year1)
fetch_and_save_fx(fx4,"usdinr_1y",day1,year1)
fetch_and_save_fx(fx5,"usdzar_1y",day1,year1)

# Calling function -> 6 months Timeframe
fetch_and_save_fx(fx1,"eurusd_6mo",day1,months6)
fetch_and_save_fx(fx2,"usdjpy_6mo",day1,months6)
fetch_and_save_fx(fx3,"gbpusd_6mo",day1,months6)
fetch_and_save_fx(fx4,"usdinr_6mo",day1,months6)
fetch_and_save_fx(fx5,"usdzar_6mo",day1,months6)

# Calling function -> 5 days Timeframe (Time interval of 1 minute)
fetch_and_save_fx(fx1,"eurusd_5dm",min15,days5)
fetch_and_save_fx(fx2,"usdjpy_5dm",min15,days5)
fetch_and_save_fx(fx3,"gbpusd_5dm",min15,days5)
fetch_and_save_fx(fx4,"usdinr_5dm",min15,days5)
fetch_and_save_fx(fx5,"usdzar_5dm",min15,days5)