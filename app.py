import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・漆黒ネオン） ---
st.set_page_config(page_title="BLACK'S STABLE MONITOR", layout="wide")

# 🔥 自動更新（5分）
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; font-size: 1.5rem !important; }
    
    /* 表の文字をiPhoneで見やすく調整 */
    .stDataFrame { background-color: #111; border-radius: 10px; }
    
    /* 更新ボタン */
    div.stButton > button {
        background-color: #000 !important; color: #ff00ff !important;
        border: 2px solid #ff00ff !important; border-radius: 10px !important;
        font-weight: bold !important; width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション状態 ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. サイドバー ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])
st.sidebar.markdown('---')
st.sidebar.write("🛰️ 自動更新: ON (5min)")

# --- 4. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 鍵がないよ！")
    st.stop()

# --- 5. データ取得（小数第1位固定） ---
@st.cache_data(ttl=300)
def get_data(m_type):
    if m_type == "日本株 (JPN)":
        try:
            res_auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": REFRESH_TOKEN})
            headers = {"Authorization": f"Bearer {res_auth.json().get('idToken')}"}
            res_data = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
            df = pd.DataFrame(res_data.json().get("shorts", []))
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '比率(%)'})
            df['比率(%)'] = pd.to_numeric(df['比率(%)']).map(lambda x: f"{float(x):.1 - 1f}")
            return df.sort_values(by='比率(%)', ascending=False).head(30).reset_index(drop=True)
        except: return None
    else:
        # 米国株30選
        watch = ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "NVDA", "NFLX", "AMD", "GOOGL", "META", "AAPL", "AMZN", "MSFT", 
                 "MSTR", "UPST", "CVNA", "AI", "SOFI", "LCID", "RIVN", "HOOD", "AFRM", "PATH", "SNOW", "PLUG", "DKNG", "UBER", "ABNB"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率(%)": f"{float(info.get('shortPercentOfFloat', 0) * 100):.1f}"})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率(%)', ascending=False).reset_index(drop=True)

# --- 6. メイン表示 ---
c1, c2 = st.columns([0.7, 0.3])
with c1: st.title(f"🕶️ {market_type}")
with c2: 
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()

df_display = get_data(market_type)

if df_display is not None:
    st.subheader("🏆 TOP 30")
    # インデックスを1からにする
    df_display.index = df_display.index + 1
    # 💥 絶対に崩れないデータフレーム表示
    st.dataframe(df_display, use_container_width=True, height=450)

    st.markdown("---")
    # 下部の検索・コピーエリア
    search = st.text_input("🔍 コード直接入力 or 検索", value=st.session_state.selected_ticker)
    if search:
        try:
            suffix = ".T" if market_type == "日本株 (JPN)" else ""
            t_price = yf.Ticker(f"{search}{suffix}").history(period="1d")['Close'].iloc[-1]
            st.metric(f"🔥 {search}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
            # コピーボタン
            st.components.v1.html(f"""
                <button onclick="navigator.clipboard.writeText('{search}');this.innerText='✅OK'" style="
                    width: 100%; padding: 15px; background-color: #ff00ff; color: white;
                    border: none; border-radius: 12px; font-weight: bold; font-size: 18px;
                    box-shadow: 0 0 15px #ff00ff; cursor: pointer;">
                    📋 '{search}' をコピー
                </button>
            """, height=80)
        except: st.write("（データ取得中...）")

st.caption("Produced by Maria & BLACK")
