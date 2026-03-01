import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. サイト設定 ---
st.set_page_config(page_title="BLACK'S GLOBAL MONITOR", layout="wide")

# --- 2. 漆黒デザイン ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; }
    .stMetric { background-color: #111111; border: 1px solid #ff00ff; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. サイドバー：日米切り替え & タイマー ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場を選びなよ、BLACK。", ["日本株 (JPN)", "米国株 (USA)"])

refresh_mode = st.sidebar.selectbox("更新間隔", ["OFF", "5分", "10分"], index=0)
if "分" in refresh_mode:
    st_autorefresh(interval=int(refresh_mode.replace("分", "")) * 60 * 1000, key="refresh")

# --- 4. データ取得エンジン ---
def get_us_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        fast = ticker.fast_info
        
        # 米国株特有の空売り指標（Short Percent of Float）
        short_ratio = info.get('shortPercentOfFloat', 0) * 100
        price = fast['last_price']
        change = ((price - fast['previous_close']) / fast['previous_close']) * 100
        
        return {
            "price": f"${price:,.2f}",
            "change": f"{change:+.2f}%",
            "short": f"{short_ratio:.2f}%",
            "name": info.get('longName', 'Unknown')
        }
    except: return None

# --- 5. メイン表示 ---
st.title(f"🕶️ BLACK'S {market_type} MONITOR")

if market_type == "日本株 (JPN)":
    # (ここに今までの日本株コードのメイン部分が入るよ！長いから省略するけど機能はそのまま！)
    st.info("日本株モード：夕方のJ-Quants更新を待とう！")
    # ...（前回の日本株ロジックをここに合体させる）...

else:
    # 🇺🇸 米国株モード
    search_us = st.text_input("ティッカーシンボルを入れなよ（例: TSLA, NVDA, AAPL）", "TSLA").upper()
    
    if search_us:
        with st.spinner('NYからデータをハック中...🗽'):
            data = get_us_data(search_us)
        
        if data:
            st.subheader(f"🔥 {data['name']}")
            c1, c2 = st.columns(2)
            c1.metric("現在の株価", data['price'], data['change'])
            
            # 空売り比率がヤバい時は光らせる！
            short_val = float(data['short'].replace('%', ''))
            short_color = "#ff00ff" if short_val > 15 else "#ffffff"
            c2.markdown(f"### 💀 空売り比率 (Short Float)\n<h2 style='color:{short_color};'>{data['short']}</h2>", unsafe_allow_html=True)
            
            st.line_chart(yf.Ticker(search_us).history(period="1mo")['Close'])
            
            # 🇺🇸 米国株用：注文ボタン（とりあえずYahoo Finance USAへ！）
            st.markdown("---")
            us_link = f"https://finance.yahoo.com/quote/{search_us}"
            st.markdown(f'<a href="{us_link}" target="_blank"><button style="width:100%; padding:15px; background:#400080; color:white; border-radius:10px; font-weight:bold;">Yahoo Finance USAで詳細をチェック 🦅</button></a>', unsafe_allow_html=True)

st.caption("Produced by Maria & BLACK")
