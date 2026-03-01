import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. サイトの基本設定 ---
st.set_page_config(page_title="BLACK'S MONITORING ROOM", layout="wide")

# --- 2. 漆黒×ネオンデザイン ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; font-family: 'Courier New', monospace; }
    .stDataFrame { border: 1px solid #ff00ff; }
    label { color: #00ffff !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    /* サイドバーも黒くするよ */
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #ff00ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 【スライド切り替え式】自動更新タイマー ---
st.sidebar.title("⏲️ MONITORING MODE")
# スライド選択（セレクトボックス）で間隔を切り替え！
refresh_mode = st.sidebar.selectbox(
    "更新間隔を選びなよ、BLACK。",
    options=["OFF (手動)", "5分間隔", "10分間隔", "15分間隔"],
    index=0
)

# 選択に合わせてタイマーをセット
if "分間隔" in refresh_mode:
    mins = int(refresh_mode.replace("分間隔", ""))
    # ミリ秒に変換
    st_autorefresh(interval=mins * 60 * 1000, key="datarefresh")
    st.sidebar.success(f"🚀 {mins}分ごとに自動ハック中...")
else:
    st.sidebar.info("🕶️ マニュアルモード（手動更新）")

# --- 4. 秘密の鍵とデータ取得（いつもの魔法） ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 秘密の金庫（Secrets）に鍵がないよ！")
    st.stop()

def get_live_price(code):
    try:
        ticker = yf.Ticker(f"{code}.T")
        hist = ticker.history(period="2d")
        if not hist.empty and len(hist) >= 2:
            last_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            change = ((last_price - prev_close) / prev_close) * 100
            return f"{last_price:,.1f}", f"{change:+.2f}%"
        return "取得中...", "0.00%"
    except: return "不明", "0.00%"

def highlight_risky(row):
    val = float(row['空売り比率(%)'])
    if val >= 20.0: return ['background-color: #ff00ff; color: #ffffff; font-weight: bold'] * len(row)
    elif val >= 15.0: return ['background-color: #ffff00; color: #000000;'] * len(row)
    return [''] * len(row)

def get_data():
    try:
        auth_url = "https://api.jquants.com/v1/token/auth_refresh"
        res_auth = requests.post(auth_url, json={"refreshToken": REFRESH_TOKEN})
        token = res_auth.json().get("idToken")
        headers = {"Authorization": f"Bearer {token}"}
        res_data = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
        if res_data.status_code == 200:
            df = pd.DataFrame(res_data.json().get("shorts", []))
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '空売り比率(%)', 'Date': '日付'})
            df['空売り比率(%)'] = pd.to_numeric(df['空売り比率(%)'])
            return df[['コード', '日付', '空売り比率(%)']]
        return None
    except: return None

# --- 5. メイン表示エリア ---
st.title("🕶️ BLACK'S ULTIMATE MONITOR")

df = get_data()

if df is not None and not df.empty:
    search = st.text_input("銘柄コードを入力...", "7203")
    if search:
        target_df = df[df['コード'].str.contains(search)].copy()
        if not target_df.empty:
            price, change = get_live_price(search)
            c1, c2 = st.columns(2)
            c1.metric("🔥 現在の株価", f"¥{price}", change)
            c2.metric("💀 空売り比率", f"{target_df.iloc[0]['空売り比率(%)']}%")
            
            st.markdown("### 📈 リアルタイムチャート")
            st.line_chart(yf.Ticker(f"{search}.T").history(period="1mo")['Close'])
            
            st.markdown("### 📊 空売り詳細")
            st.dataframe(target_df.style.apply(highlight_risky, axis=1))
else:
    st.info("今はデータがないみたい。月曜日の夕方にまたおいで！")

st.caption("Produced by Maria & BLACK")
