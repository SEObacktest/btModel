import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
import json
import csv
import io
import sys
from datetime import datetime
import backtrader as bt
from backtrader.feeds import GenericCSVData
import pandas as pd
um_futures_client = UMFutures()
BTCUSDT=um_futures_client.klines("BTCUSDT",'1d')
datetime_arr,open,close,high,low,volume=zip(*[
    (item[0],item[1],item[2],item[3],item[4],item[5])
    for item in BTCUSDT
])
datetime_arr=[datetime.fromtimestamp(item/1000).strftime('%Y-%m-%d') for item in datetime_arr]
d={"open":open,"close":close,"high":high,"low":low,"volume":volume}
df=pd.DataFrame(data=d,index=datetime_arr)
cerebro=bt.Cerebro()

print(df)







'''
import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
import io
import csv
from datetime import datetime

def get_binance_data():
    # Set up logging and client
    config_logging(logging, logging.DEBUG)
    um_futures_client = UMFutures()
    
    # Get data from Binance
    BTCUSDT = um_futures_client.klines("BTCUSDT", '1d')
    
    # Create StringIO buffer
    buffer = io.StringIO(newline='')
    csv_writer = csv.writer(buffer)
    
    # Write header
    csv_writer.writerow(["Date", "Open", "High", "Low", "Close", "Volume"])
    
    # Write data
    for data in BTCUSDT:
        # Convert timestamp to datetime string (Yahoo Finance format)
        date = datetime.fromtimestamp(data[0]/1000).strftime('%Y-%m-%d')
        row = [
            date,
            data[1],  # Open
            data[2],  # High
            data[3],  # Low
            data[4],  # Close
            data[5]   # Volume
        ]
        csv_writer.writerow(row)
    
    # Reset buffer position to start
    buffer.seek(0)
    return buffer

# Use with Backtrader
import backtrader as bt

class BinanceData(bt.feeds.GenericCSVData):
    params = (
        ('nullvalue', float('NaN')),
        ('dtformat', '%Y-%m-%d'),
        ('datetime', 0),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', -1),
    )

def main():
    cerebro = bt.Cerebro()
    
    # Get data buffer
    data_buffer = get_binance_data()
    
    # Feed the data to Backtrader
    data = BinanceData(
        dataname=data_buffer,
        fromdate=datetime(2020, 1, 1),
        todate=datetime(2024, 12, 31)
    )
    
    cerebro.adddata(data)
    
    # Add your strategy here
    # cerebro.addstrategy(YourStrategy)
    
    # Run the backtest
    result = cerebro.run()
    
    # Plot if needed
    # cerebro.plot()

if __name__ == '__main__':
    main()
'''