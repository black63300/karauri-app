import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・漆黒ネオン） ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; }
    .stMetric { background-color: #111111; border: 1px solid #00ffff; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #ff00ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. サイドバー：市場切り替え ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])

refresh_mode = st.sidebar.selectbox("自動更新", ["OFF", "5分", "10分"], index=0)
if "分" in refresh_mode:
    st_autorefresh(interval=int(refresh_mode.replace("分", "")) * 60 * 1000, key="refresh")

# --- 3. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 秘密の金庫に鍵がないよ！")
    st.stop()

# --- 4. データ取得 ---
def get_us_data(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        short = info.get('shortPercentOfFloat', 0) * 100
        hist = t.history(period="2d")
        if not hist.empty:
            return {"price": hist['Close'].iloc[-1], "short": short, "name": info.get('longName', ticker)}
    except: return None

def get_jp_data():
    try:
        auth_url = "https://api.jquants.com/v1/token/auth_refresh"
        res_auth = requests.post(auth_url, json={"refreshToken": REFRESH_TOKEN})
        token = res_auth.json().get("idToken")
        headers = {"Authorization": f"Bearer {token}"}
        res_data = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
        if res_data.status_code == 200:
            df = pd.DataFrame(res_data.json().get("shorts", []))
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '空売り比率(%)'})
            df['空売り比率(%)'] = pd.to_numeric(df['空売り比率(%)'])
            return df
    except: return None

# --- 5. メイン表示 ---
st.title(f"🕶️ {market_type} MONITOR")

if market_type == "日本株 (JPN)":
    df_jp = get_jp_data()
    search_jp = st.text_input("コード4桁を入れてね", "7203")
    if df_jp is not None and search_jp:
        target = df_jp[df_jp['コード'].str.contains(search_jp)].copy()
        if not target.empty:
            c1, c2 = st.columns(2)
            c1.metric("空売り比率", f"{target.iloc[0]['空売り比率(%)']}%")
            st.info(f"👉 銘柄コード '{search_jp}' をコピーしてSBIアプリへ！")
            st.line_chart(yf.Ticker(f"{search_jp}.T").history(period="1mo")['Close'])
else:
    search_us = st.text_input("ティッカーを入れてね", "TSLA").upper()
    if search_us:
        data = get_us_data(search_us)
        if data:
            st.subheader(data['name'])
            c1, c2 = st.columns(2)
            c1.metric("現在値", f"${data['price']:,.2f}")
            short_color = "#ff00ff" if data['short'] > 15 else "#ffffff"
            c2.markdown(f"### 💀 空売り比率\n<h2 style='color:{short_color};'>{data['short']:.2f}%</h2>", unsafe_allow_html=True)
            st.info(f"👉 ティッカー '{search_us}' をコピーしてSBI米国株アプリへ！")
            st.line_chart(yf.Ticker(search_us).history(period="1mo")['Close'])

st.caption("Produced by Maria & BLACK")
