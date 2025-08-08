
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="Market Breadth Dashboard", layout="wide")

@st.cache_data
def load_stock_list():
    df = pd.read_csv("nse_stock_list.csv")
    return df.dropna(subset=['symbol', 'sector'])

@st.cache_data
def fetch_price_data(symbols):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=250)
    data = yf.download(symbols, start=start_date, end=end_date)
   if 'Adj Close' not in data.columns and isinstance(data.columns, pd.MultiIndex):
    adj_close_data = data.loc[:, pd.IndexSlice[:, 'Adj Close']]
    adj_close_data.columns = [col[0] for col in adj_close_data.columns]  # flatten
    return adj_close_data
elif 'Adj Close' in data.columns:
    return data['Adj Close']
else:
    st.error("Price data could not be retrieved. Check ticker symbols or try again later.")
    return pd.DataFrame()


stock_df = load_stock_list()
symbols = stock_df['symbol'].tolist()
price_data = fetch_price_data([symbol + ".NS" for symbol in symbols])

# Filter out stocks with insufficient data
price_data = price_data.dropna(axis=1, thresh=150)

latest_prices = price_data.iloc[-1]
sma_20 = price_data.rolling(window=20).mean().iloc[-1]
sma_50 = price_data.rolling(window=50).mean().iloc[-1]
sma_200 = price_data.rolling(window=200).mean().iloc[-1]

result_df = pd.DataFrame({
    "symbol": [col.replace(".NS", "") for col in price_data.columns],
    "latest_price": latest_prices.values,
    "sma_20": sma_20.values,
    "sma_50": sma_50.values,
    "sma_200": sma_200.values,
})

result_df["above_20"] = result_df["latest_price"] > result_df["sma_20"]
result_df["above_50"] = result_df["latest_price"] > result_df["sma_50"]
result_df["above_200"] = result_df["latest_price"] > result_df["sma_200"]

# Convert to int to prevent aggregation errors
result_df["above_20"] = result_df["above_20"].astype(int)
result_df["above_50"] = result_df["above_50"].astype(int)
result_df["above_200"] = result_df["above_200"].astype(int)

result_df = result_df.merge(stock_df, on="symbol", how="left")

# Sector-wise breadth
breadth = result_df.groupby("sector").agg({
    "above_20": "mean",
    "above_50": "mean",
    "above_200": "mean"
}).reset_index()

st.title("📊 Market Breadth Dashboard (NSE)")
st.write("Market breadth based on how many stocks are above their 20, 50, and 200 day SMAs.")

st.subheader("Overall Breadth")
col1, col2, col3 = st.columns(3)
col1.metric("Above 20 SMA", f"{result_df['above_20'].mean():.2%}")
col2.metric("Above 50 SMA", f"{result_df['above_50'].mean():.2%}")
col3.metric("Above 200 SMA", f"{result_df['above_200'].mean():.2%}")

st.subheader("Sector-wise Breadth")
st.dataframe(breadth)

st.subheader("Detailed Stock View")
st.dataframe(result_df[["symbol", "sector", "latest_price", "sma_20", "sma_50", "sma_200", "above_20", "above_50", "above_200"]])
