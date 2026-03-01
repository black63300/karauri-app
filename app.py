import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・漆黒ネオン） ---
st.set_page_config(page_title="BLACK'S COPY MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; }
    .stMetric { background-color: #111111; border: 1px solid #00ffff; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #ff00ff; }
    /* コピーボタン専用のデザイン */
    .copy-btn {
        background-color: #ff00ff; color: white; border: none;
        padding: 10px 20px; border-radius: 5px; font-weight: bold;
        cursor: pointer; box-shadow: 0 0 10px #ff00ff; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. サイドバー設定 ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])

# --- 3. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 秘密の金庫に鍵がないよ！")
    st.stop()

# --- 4. コピー用JavaScriptの魔法 ---
def copy_to_clipboard(text):
    # ワンタップでクリップボードにコピーするJSを埋め込むよ
    st.components.v1.html(f"""
        <button class="copy-btn" onclick="navigator.clipboard.writeText('{text}')">
            📋 '{text}' をワンタップコピー！
        </button>
        <style>
            .copy-btn {{
                background-color: #ff00ff; color: white; border: none;
                padding: 15px; border-radius: 10px; font-weight: bold;
                width: 100%; font-size: 18px; box-shadow: 0 0 15px #ff00ff;
            }}
        </style>
    """, height=70)

# --- 5. データ取得エンジン ---
@st.cache_data(ttl=300)
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
            short = t.info.get('shortPercentOfFloat', 0) * 100
            data.append({"ティッカー": ticker, "空売り比率(%)": round(short, 2)})
        except: continue
    return pd.DataFrame(data)

# --- 6. メイン表示 ---
st.title(f"🕶️ {market_type} MONITOR")

if market_type == "日本株 (JPN)":
    df_jp = get_jp_data()
    if df_jp is not None:
        st.subheader("🏆 空売り比率 TOP30")
        top_30 = df_jp.sort_values(by='空売り比率(%)', ascending=False).head(30)
        st.dataframe(top_30, use_container_width=True)
        
        st.write("---")
        copy_target = st.text_input("コピーしたい銘柄コードを入れて！", "7203")
        copy_to_clipboard(copy_target) # 🔥 ここでコピーボタンを表示

else:
    df_us = get_us_ranking()
    if not df_us.empty:
        st.subheader("🇺🇸 米国株 監視ランキング")
        top_us = df_us.sort_values(by='空売り比率(%)', ascending=False)
        st.dataframe(top_us, use_container_width=True)
        
        st.write("---")
        copy_target_us = st.text_input("コピーしたいティッカーを入れて！", "TSLA").upper()
        copy_to_clipboard(copy_target_us) # 🔥 ここでコピーボタンを表示

st.caption("Produced by Maria & BLACK")
