import streamlit as st
import pandas as pd
import yfinance as yf

# Set up Streamlit app config
st.set_page_config(page_title="Market Breadth Dashboard", layout="wide")

# Load stock list
@st.cache_data
def load_stock_list():
    try:
        df = pd.read_csv("stock_list.csv")
        st.write("Loaded stock list:", df.head())  # Debug
        return df.dropna(subset=["symbol", "sector"])
    except Exception as e:
        st.error(f"Failed to load stock list: {e}")
        return pd.DataFrame()

stock_df = load_stock_list()

if stock_df.empty:
    st.warning("Stock list is empty or failed to load.")
    st.stop()

symbols = stock_df["symbol"].tolist()
st.write("Stock symbols:", symbols)  # Debug

# Fetch price data
@st.cache_data
def fetch_price_data(symbols):
    try:
        data = yf.download(symbols, period="3mo", interval="1d", group_by="ticker", threads=True)
        st.write("Raw downloaded data:", data.head())  # Debug

        # Handle MultiIndex
        if isinstance(data.columns, pd.MultiIndex) and 'Adj Close' not in data.columns:
            adj_close = pd.DataFrame({symbol: data[symbol]["Adj Close"] for symbol in symbols if symbol in data.columns.levels[0]})
        else:
            adj_close = data["Adj Close"]

        return adj_close
    except Exception as e:
        st.error(f"Failed to fetch price data: {e}")
        return pd.DataFrame()

price_data = fetch_price_data([symbol + ".NS" for symbol in symbols])

if price_data.empty:
    st.warning("No price data available.")
    st.stop()

st.write("Adjusted close price data:", price_data.head())  # Debug

# Add any more logic here (like VCP pattern, percentage filters, etc.)

st.success("Data loaded successfully.")
