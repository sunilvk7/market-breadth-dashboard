import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px

st.set_page_config(page_title=\"Market Breadth Dashboard\", layout=\"wide\")

st.title(\"📊 NSE Market Breadth Dashboard by Sector\")

@st.cache_data
def load_stock_list():
    df = pd.read_csv(\"nse_stock_list.csv\")
    return df.dropna(subset=['symbol', 'sector'])

stock_df = load_stock_list()

today = datetime.today()
start_date = today - timedelta(days=365)
ma_periods = [20, 50, 200]

@st.cache_data(show_spinner=True)
def fetch_data(ticker):
    data = yf.download(ticker + \".NS\", start=start_date, end=today)
    return data[['Close']]

def check_above_ma(data, period):
    data[f\"MA_{period}\"] = data['Close'].rolling(period).mean()
    return data['Close'].iloc[-1] > data[f\"MA_{period}\"].iloc[-1]

results = []
st.info(\"Fetching and analyzing stock data... this may take a few minutes on first run.\")

for _, row in stock_df.iterrows():
    symbol = row['symbol']
    sector = row['sector']
    try:
        data = fetch_data(symbol)
        record = {\"symbol\": symbol, \"sector\": sector}
        for ma in ma_periods:
            record[f\"above_{ma}\"] = check_above_ma(data.copy(), ma)
        results.append(record)
    except Exception as e:
        st.warning(f\"Error processing {symbol}: {e}\")

result_df = pd.DataFrame(results)

breadth = result_df.groupby(\"sector\").agg({
    \"above_20\": \"mean\",
    \"above_50\": \"mean\",
    \"above_200\": \"mean\"
}).reset_index()
breadth[[\"above_20\", \"above_50\", \"above_200\"]] *= 100

selected_ma = st.sidebar.selectbox(\"Select MA Period\", [20, 50, 200])

st.subheader(f\"% of Stocks Above {selected_ma} MA by Sector\")
fig = px.bar(breadth.sort_values(f\"above_{selected_ma}\", ascending=False),
             x=\"sector\", y=f\"above_{selected_ma}\",
             labels={f\"above_{selected_ma}\": \"% Above MA\"},
             title=f\"% of Stocks Above {selected_ma} MA by Sector\",
             text_auto='.2f')

fig.update_layout(xaxis_title=\"Sector\", yaxis_title=\"% Stocks Above MA\", height=600)
st.plotly_chart(fig, use_container_width=True)

with st.expander(\"📄 Show Raw Sector Breadth Data\"):
    st.dataframe(breadth, use_container_width=True)

st.download_button(\"📥 Download Breadth Data as CSV\", data=breadth.to_csv(index=False), file_name=\"nse_sector_breadth.csv\")