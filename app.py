import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・漆黒ネオン） ---
st.set_page_config(page_title="BLACK'S GLOBAL MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; }
    .stMetric { background-color: #111111; border: 1px solid #ff00ff; border-radius: 10px; padding: 10px; }
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

# --- 4. データ取得関数 ---
def get_us_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        short_ratio = info.get('shortPercentOfFloat', 0) * 100
        hist = ticker.history(period="2d")
        if not hist.empty:
            last_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            change = ((last_price - prev_close) / prev_close) * 100
            return {"price": last_price, "change": f"{change:+.2f}%", "short": short_ratio, "name": info.get('longName', ticker_symbol)}
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
st.title(f"🕶️ {market_type} MONITOR")

if market_type == "日本株 (JPN)":
    df_jp = get_jp_data()
    search_jp = st.text_input("銘柄コード（4桁）", "7203")
    if df_jp is not None and search_jp:
        target = df_jp[df_jp['コード'].str.contains(search_jp)].copy()
        if not target.empty:
            ticker = yf.Ticker(f"{search_jp}.T")
            hist = ticker.history(period="2d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                c1, c2 = st.columns(2)
                c1.metric("🔥 現在値", f"¥{price:,.1f}", f"{change:+.2f}%")
                c2.metric("💀 空売り比率", f"{target.iloc[0]['空売り比率(%)']}%")
                st.line_chart(ticker.history(period="1mo")['Close'])
                
                # 🔥 日本株：一番確実なWebトップへ
                st.markdown(f'<a href="https://site0.sbisec.co.jp/ETGate/" target="_blank" style="text-decoration: none;"><div style="width:100%; padding:20px; background-color:#0041ff; color:white; border-radius:15px; text-align:center; font-weight:bold; border:2px solid #00ffff; box-shadow: 0 0 15px #00ffff;">SBI証券で取引する (別タブで開く) 📱💥</div></a>', unsafe_allow_html=True)
else:
    search_us = st.text_input("ティッカー（例: TSLA）", "TSLA").upper()
    if search_us:
        data_us = get_us_data(search_us)
        if data_us:
            st.subheader(f"🔥 {data_us['name']}")
            c1, c2 = st.columns(2)
            c1.metric("🔥 現在値", f"${data_us['price']:,.2f}", data_us['change'])
            short_color = "#ff00ff" if data_us['short'] > 15 else "#ffffff"
            c2.markdown(f"### 💀 空売り比率\n<h2 style='color:{short_color};'>{data_us['short']:.2f}%</h2>", unsafe_allow_html=True)
            st.line_chart(yf.Ticker(search_us).history(period="1mo")['Close'])
            
            # 🔥 米国株：真っ白回避！SBI米国株トップページへ
            sbi_us_url = "https://site0.sbisec.co.jp/ETGate/?_ControlID=WPLETmgR001Control&_PageID=WPLETmgR001Mdtl20&_DataAreaID=W6&_ActionID=DefaultAID&get_corp_info=dom&cat1=market&cat2=none"
            st.markdown(f'<a href="{sbi_us_url}" target="_blank" style="text-decoration: none;"><div style="width:100%; padding:20px; background-color:#400080; color:white; border-radius:15px; text-align:center; font-weight:bold; border:2px solid #ff00ff; box-shadow: 0 0 15px #ff00ff;">SBI米国株注文ページへ (別タブで開く) 🦅⚡️</div></a>', unsafe_allow_html=True)

st.caption("Produced by Maria & BLACK")
