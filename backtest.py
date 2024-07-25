import tkinter as tk
from tkinter import messagebox
import ccxt
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# Paths to the folders containing CSV files
ETH_DATA_FOLDER = r'C:\Users\Admin\Desktop\tradingbot (1)\1h ohlc data\eth_usdt_swap'
BTC_DATA_FOLDER = r'C:\Users\Admin\Desktop\tradingbot (1)\1h ohlc data\btc_usdt_swap'

# Parameters for trading strategy
Z_SCORE_THRESHOLD = 1.5
BTC_SIZE = 1  # Size of BTC contract for each trade
ETH_SIZE = 1  # Size of ETH contract for each trade

def load_data(folder_path):
    """Load and combine CSV files from a folder."""
    data_frames = []
    for file_name in sorted(os.listdir(folder_path)):
        if file_name.endswith('.csv'):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)
            if 'open_time' in df.columns:
                df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
                df = df[['open', 'high', 'low', 'close', 'volume']]
            else:
                return pd.DataFrame()
            data_frames.append(df)
    if not data_frames:
        raise ValueError("No valid data files found.")
    return pd.concat(data_frames)

def compute_z_score(spread):
    """Compute the Z-score of the spread."""
    return (spread - spread.mean()) / spread.std()

def backtest_strategy(btc_data, eth_data):
    """Backtest the pair trading strategy."""
    combined_df = btc_data[['close']].rename(columns={'close': 'btc_close'})
    combined_df = combined_df.join(eth_data[['close']].rename(columns={'close': 'eth_close'}))
    
    combined_df['spread'] = combined_df['btc_close'] - combined_df['eth_close']
    combined_df['z_score'] = compute_z_score(combined_df['spread'])
    
    combined_df['long_entry'] = combined_df['z_score'] < -Z_SCORE_THRESHOLD
    combined_df['short_entry'] = combined_df['z_score'] > Z_SCORE_THRESHOLD
    combined_df['exit_signal'] = abs(combined_df['z_score']) < Z_SCORE_THRESHOLD
    
    capital = 1000
    btc_position = 0
    eth_position = 0
    entry_price_btc = 0
    entry_price_eth = 0
    
    trades = []
    
    for index, row in combined_df.iterrows():
        if row['long_entry']:
            if btc_position == 0 and eth_position == 0:
                btc_position = BTC_SIZE
                eth_position = ETH_SIZE
                entry_price_btc = row['btc_close']
                entry_price_eth = row['eth_close']
                trades.append({'timestamp': index, 'type': 'long', 'btc_entry': entry_price_btc, 'eth_entry': entry_price_eth})
        elif row['short_entry']:
            if btc_position == 0 and eth_position == 0:
                btc_position = -BTC_SIZE
                eth_position = -ETH_SIZE
                entry_price_btc = row['btc_close']
                entry_price_eth = row['eth_close']
                trades.append({'timestamp': index, 'type': 'short', 'btc_entry': entry_price_btc, 'eth_entry': entry_price_eth})
        elif row['exit_signal']:
            if btc_position != 0 or eth_position != 0:
                if btc_position > 0:
                    capital += (row['btc_close'] - entry_price_btc) * btc_position
                elif btc_position < 0:
                    capital += (entry_price_btc - row['btc_close']) * -btc_position
                
                if eth_position > 0:
                    capital += (row['eth_close'] - entry_price_eth) * eth_position
                elif eth_position < 0:
                    capital += (entry_price_eth - row['eth_close']) * -eth_position
                
                trades.append({'timestamp': index, 'type': 'exit', 'btc_exit': row['btc_close'], 'eth_exit': row['eth_close']})
                btc_position = 0
                eth_position = 0
    
    return capital, trades, combined_df

def start_backtest():
    btc_data = load_data(BTC_DATA_FOLDER)
    eth_data = load_data(ETH_DATA_FOLDER)

    if btc_data.empty or eth_data.empty:
        raise ValueError("No data loaded. Please check the CSV files.")

    final_capital, trades, combined_df = backtest_strategy(btc_data, eth_data)

    print(f"Starting Capital: $1000")
    print(f"Final Capital: ${final_capital:.2f}")
    print(f"Net Profit: ${final_capital - 1000:.2f}")

    trades_df = pd.DataFrame(trades)
    trades_df.to_csv('trades_log.csv', index=False)

    # Plot results
    plt.figure(figsize=(14, 10))

    # Plot BTC and ETH closing prices
    plt.subplot(3, 1, 1)
    plt.plot(combined_df.index, combined_df['btc_close'], label='BTC Close', color='blue')
    plt.plot(combined_df.index, combined_df['eth_close'], label='ETH Close', color='orange')
    plt.title('BTC and ETH Closing Prices')
    plt.legend()

    # Plot spread
    plt.subplot(3, 1, 2)
    plt.plot(combined_df.index, combined_df['spread'], label='Spread', color='green')
    plt.axhline(0, color='black', linestyle='--')
    plt.title('Spread')
    plt.legend()

    # Plot Z-score with entry and exit points
    plt.subplot(3, 1, 3)
    plt.plot(combined_df.index, combined_df['z_score'], label='Z-Score', color='red')
    plt.axhline(-Z_SCORE_THRESHOLD, color='blue', linestyle='--', label='Long Entry Threshold')
    plt.axhline(Z_SCORE_THRESHOLD, color='blue', linestyle='--', label='Short Entry Threshold')
    plt.title('Z-Score')

    # Mark trades on the Z-score plot
    for trade in trades:
        if trade['type'] == 'long':
            plt.axvline(trade['timestamp'], color='green', linestyle='--', label='Long Entry')
        elif trade['type'] == 'short':
            plt.axvline(trade['timestamp'], color='red', linestyle='--', label='Short Entry')
        elif trade['type'] == 'exit':
            plt.axvline(trade['timestamp'], color='black', linestyle='--', label='Exit')

    plt.legend()

    plt.tight_layout()
    plt.show()

def start_real_trading(api_key, secret_key, exchange_name):
    exchange_class = getattr(ccxt, exchange_name)
    exchange = exchange_class({
        'apiKey': api_key,
        'secret': secret_key,
    })

    # Implement real trading logic here using the exchange object
    # For example, fetching market data, placing orders, etc.
    print(f"Connected to {exchange_name} with API key {api_key}")

def on_start_button_click():
    api_key = api_key_entry.get()
    secret_key = secret_key_entry.get()
    exchange_name = exchange_var.get()

    if not api_key or not secret_key or not exchange_name:
        messagebox.showerror("Error", "Please fill in all fields")
        return

    start_real_trading(api_key, secret_key, exchange_name)

# Create the main window
root = tk.Tk()
root.title("Trading Bot")

# Create and place the labels and entry fields
tk.Label(root, text="API Key").grid(row=0, column=0)
api_key_entry = tk.Entry(root)
api_key_entry.grid(row=0, column=1)

tk.Label(root, text="Secret Key").grid(row=1, column=0)
secret_key_entry = tk.Entry(root)
secret_key_entry.grid(row=1, column=1)

# Create and place the radio buttons for exchange selection
exchange_var = tk.StringVar(value="binance")

tk.Label(root, text="Exchange Name").grid(row=2, column=0)
tk.Radiobutton(root, text="Binance", variable=exchange_var, value="binance").grid(row=2, column=1, sticky='w')
tk.Radiobutton(root, text="Bybit", variable=exchange_var, value="bybit").grid(row=3, column=1, sticky='w')
tk.Radiobutton(root, text="OKX", variable=exchange_var, value="okx").grid(row=4, column=1, sticky='w')

# Create and place the buttons
start_button = tk.Button(root, text="Start Trading", command=on_start_button_click)
start_button.grid(row=5, column=0, columnspan=2)

backtest_button = tk.Button(root, text="Backtest Strategy", command=start_backtest)
backtest_button.grid(row=6, column=0, columnspan=2)

# Run the main loop
root.mainloop()