import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用） ---
st.set_page_config(page_title="BLACK'S GLOBAL MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; }
    .stMetric { background-color: #111111; border: 1px solid #ff00ff; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. サイドバー ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])

# --- 3. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 秘密の金庫に鍵がないよ！")
    st.stop()

# --- 4. データ取得 ---
def get_us_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        short_ratio = info.get('shortPercentOfFloat', 0) * 100
        hist = ticker.history(period="2d")
        if not hist.empty:
            return {"price": hist['Close'].iloc[-1], "short": short_ratio, "name": info.get('longName', ticker_symbol)}
        return None
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
        return None
    except: return None

# --- 5. メイン表示 ---
st.title(f"🕶️ {market_type}")

if market_type == "日本株 (JPN)":
    df_jp = get_jp_data()
    search_jp = st.text_input("コード4桁", "7203")
    if df_jp is not None:
        target = df_jp[df_jp['コード'].str.contains(search_jp)].copy()
        if not target.empty:
            st.metric("空売り比率", f"{target.iloc[0]['空売り比率(%)']}%")
            # 🔥 日本株：超シンプルなテキストリンク
            st.write("---")
            st.markdown(f"### [🔗 ここをタップしてSBI証券を開く](https://site0.sbisec.co.jp/ETGate/)")
else:
    search_us = st.text_input("ティッカー", "TSLA").upper()
    data_us = get_us_data(search_us)
    if data_us:
        st.subheader(data_us['name'])
        st.metric("株価", f"${data_us['price']:,.2f}")
        st.metric("空売り比率", f"{data_us['short']:.2f}%")
        # 🔥 米国株：超シンプルなテキストリンク
        st.write("---")
        # ログイン画面へ直接飛ばすリンクだよ
        st.markdown(f"### [🔗 ここをタップしてSBI米国株注文へ](https://site0.sbisec.co.jp/ETGate/?_ControlID=WPLETmgR001Control&_PageID=WPLETmgR001Mdtl20&_DataAreaID=W6&_ActionID=DefaultAID&get_corp_info=dom&cat1=market&cat2=none)")

st.caption("Produced by Maria & BLACK")
