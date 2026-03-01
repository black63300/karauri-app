import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用） ---
st.set_page_config(page_title="BLACK'S RANKING MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; }
    .stMetric { background-color: #111111; border: 1px solid #00ffff; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #ff00ff; }
    /* ボタンをネオン風に */
    .stButton > button {
        background-color: #000000; color: #ff00ff; border: 2px solid #ff00ff;
        border-radius: 10px; font-weight: bold; box-shadow: 0 0 10px #ff00ff;
    }
    .stButton > button:hover { background-color: #ff00ff; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. サイドバー設定 ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])

refresh_mode = st.sidebar.selectbox("自動更新（バックグラウンド）", ["OFF", "5分", "10分"], index=0)
if "分" in refresh_mode:
    st_autorefresh(interval=int(refresh_mode.replace("分", "")) * 60 * 1000, key="refresh")

# --- 3. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 秘密の金庫に鍵がないよ！")
    st.stop()

# --- 4. データ取得エンジン ---
@st.cache_data(ttl=300) # 5分間はキャッシュして高速化
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
        return None
    except: return None

def get_us_ranking():
    watch_list = ["TSLA", "NVDA", "AAPL", "AMZN", "META", "GOOGL", "MSFT", "AMD", "NFLX", "GME", "AMC", "PLTR", "COIN", "MARA", "RIOT"]
    data = []
    for ticker in watch_list:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            short = info.get('shortPercentOfFloat', 0) * 100
            data.append({"ティッカー": ticker, "空売り比率(%)": round(short, 2), "銘柄名": info.get('longName', ticker)})
        except: continue
    return pd.DataFrame(data)

def highlight_risky(row):
    val = float(row['空売り比率(%)'])
    if val >= 20.0: return ['background-color: #ff00ff; color: #ffffff; font-weight: bold'] * len(row)
    elif val >= 10.0: return ['background-color: #ffff00; color: #000000;'] * len(row)
    return [''] * len(row)

# --- 5. メイン表示 ---
col_h1, col_btn = st.columns([0.8, 0.2])
with col_h1:
    st.title(f"🕶️ {market_type} MONITOR")
with col_btn:
    # 🔥 手動更新ボタン
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()

if market_type == "日本株 (JPN)":
    df_jp = get_jp_data()
    if df_jp is not None:
        st.subheader("🏆 日本株 空売り比率 TOP30")
        top_30_jp = df_jp.sort_values(by='空売り比率(%)', ascending=False).head(30)
        st.dataframe(top_30_jp.style.apply(highlight_risky, axis=1), use_container_width=True)
else:
    with st.spinner('NY市場をハック中...🗽'):
        df_us = get_us_ranking()
    if not df_us.empty:
        st.subheader("🇺🇸 米国株 監視ランキング")
        top_us = df_us.sort_values(by='空売り比率(%)', ascending=False)
        st.dataframe(top_us.style.apply(highlight_risky, axis=1), use_container_width=True)

st.caption("Produced by Maria & BLACK")
