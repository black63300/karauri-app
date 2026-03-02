import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. ページ設定 & デザイン ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide", initial_sidebar_state="collapsed")

# 5分ごとに自動更新
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1, h2, h3 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; }
    
    /* カードのデザイン */
    .tile-item {
        background: rgba(20, 20, 20, 0.8);
        border-radius: 10px; padding: 8px; text-align: center;
        border: 1.5px solid #444; transition: 0.3s;
    }
    .tile-item:hover { transform: scale(1.05); border-color: #00ffff !important; }

    /* 市場切り替えボタンの特殊スタイル */
    div[data-testid="stHorizontalBlock"] .stButton > button {
        height: 50px !important; font-size: 1.2rem !important; font-weight: bold !important;
        border-radius: 15px !important;
    }

    /* 固定フッターエリア */
    .sticky-footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: rgba(0, 0, 0, 0.95); border-top: 2px solid #ff00ff;
        padding: 15px; z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 ---
if 'market_type' not in st.session_state:
    st.session_state.market_type = "日本株 (JPN)"
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. 市場切り替えボタン（メインエリア最上部） ---
st.write("### 🚀 SELECT MARKET")
m_col1, m_col2 = st.columns(2)

with m_col1:
    # 日本株が選ばれてる時はネオンピンク、そうじゃない時はグレー
    jpn_style = "primary" if st.session_state.market_type == "日本株 (JPN)" else "secondary"
    if st.button("🇯🇵 JAPAN (JPN)", use_container_width=True, type=jpn_style):
        st.session_state.market_type = "日本株 (JPN)"
        st.rerun()

with m_col2:
    usa_style = "primary" if st.session_state.market_type == "米国株 (USA)" else "secondary"
    if st.button("🇺🇸 USA (USA)", use_container_width=True, type=usa_style):
        st.session_state.market_type = "米国株 (USA)"
        st.rerun()

st.markdown("---")

# --- 4. データ取得関数 ---
@st.cache_data(ttl=300)
def get_data(m_type):
    if m_type == "日本株 (JPN)":
        try:
            REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
            res_auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": REFRESH_TOKEN})
            headers = {"Authorization": f"Bearer {res_auth.json().get('idToken')}"}
            res_data = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
            df = pd.DataFrame(res_data.json().get("shorts", []))
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '比率'})
            df['比率'] = pd.to_numeric(df['比率']).round(1)
            return df.sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)
        except: return None
    else:
        watch = ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "NVDA", "NFLX", "AMD", "GOOGL", "META", "AAPL", "AMZN", "MSFT"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

# --- 5. 表示エリア ---
market_now = st.session_state.market_type
df_top = get_data(market_now)

if df_top is not None:
    st.subheader(f"🏆 {market_now} SHORT TOP 15")
    cols = st.columns(5)
    for idx, row in df_top.iterrows():
        with cols[idx % 5]:
            color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#00ffff"
            st.markdown(f"""
                <div class="tile-item" style="border: 1.5px solid {color};">
                    <div style="font-size:0.6rem;color:#888;">RANK #{idx+1}</div>
                    <div style="font-weight:bold;font-size:1.1rem;">{row['コード']}</div>
                    <div style="color:{color};font-weight:bold;font-size:0.9rem;">{row['比率']}%</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("SELECT", key=f"btn_{row['コード']}"):
                st.session_state.selected_ticker = str(row['コード'])
                st.rerun()

# --- 6. 画面下部固定（検索 & 詳細） ---
st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="sticky-footer">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([0.2, 0.4, 0.4])
    with f_col1:
        search = st.text_input("🔍 TARGET", value=st.session_state.selected_ticker, label_visibility="collapsed")
    if search:
        try:
            suffix = ".T" if market_now == "日本株 (JPN)" else ""
            t_price = yf.Ticker(f"{search}{suffix}").history(period="1d")['Close'].iloc[-1]
            with f_col2:
                st.metric(f"🔥 {search}", f"{'¥' if suffix else '$'}{float(t_price):,.1f}")
            with f_col3:
                st.components.v1.html(f"""
                    <button onclick="navigator.clipboard.writeText('{search}');this.innerText='COPIED!'" style="
                        width: 100%; height: 40px; background: linear-gradient(45deg, #ff00ff, #00ffff);
                        color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">
                        📋 '{search}' をコピー
                    </button>
                """, height=45)
        except: st.write("銘柄ハック中...")
    st.markdown('</div>', unsafe_allow_html=True)

st.caption(f"Produced by Maria & BLACK | {datetime.datetime.now().strftime('%H:%M:%S')}")
