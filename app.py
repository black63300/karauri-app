import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用） ---
st.set_page_config(page_title="BLACK'S GLOBAL RANKING", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; }
    .stMetric { background-color: #111111; border: 1px solid #00ffff; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #ff00ff; }
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

# --- 4. データ取得エンジン ---
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
    # BLACKが気になりそうな主要・爆益銘柄リスト
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
st.title(f"🕶️ {market_type} MONITOR")

if market_type == "日本株 (JPN)":
    df_jp = get_jp_data()
    if df_jp is not None:
        st.subheader("🏆 日本株 空売り比率 TOP30")
        top_30_jp = df_jp.sort_values(by='空売り比率(%)', ascending=False).head(30)
        st.dataframe(top_30_jp.style.apply(highlight_risky, axis=1), use_container_width=True)
else:
    with st.spinner('NYのデータをハック中...🗽'):
        df_us = get_us_ranking()
    if not df_us.empty:
        st.subheader("🇺🇸 米国株 監視リスト・ランキング")
        top_us = df_us.sort_values(by='空売り比率(%)', ascending=False)
        st.dataframe(top_us.style.apply(highlight_risky, axis=1), use_container_width=True)
        
        st.write("---")
        search_us = st.text_input("個別ティッカー検索", "TSLA").upper()
        if search_us:
            t_info = yf.Ticker(search_us).info
            st.metric(f"🔥 {search_us}", f"{t_info.get('shortPercentOfFloat', 0)*100:.2f}%")
            st.line_chart(yf.Ticker(search_us).history(period="1mo")['Close'])

st.caption("Produced by Maria & BLACK")
