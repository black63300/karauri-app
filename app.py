import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（検索エリア固定 & 可変グリッド） ---
st.set_page_config(page_title="BLACK'S STICKY MONITOR", layout="wide")

# 自動更新 (5分)
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; font-size: 1.5rem !important; }
    
    /* 📱 縦画面：3カラム / 横画面：6カラム */
    [data-testid="column"] {
        flex: 1 1 calc(33.333% - 8px) !important;
        min-width: calc(33.333% - 8px) !important;
    }
    @media (min-width: 600px) {
        [data-testid="column"] {
            flex: 1 1 calc(16.666% - 8px) !important;
            min-width: calc(16.666% - 8px) !important;
        }
    }
    
    .tile-item {
        background-color: #111; border-radius: 8px;
        padding: 4px; text-align: center; margin-bottom: 2px;
    }

    /* ボタンデザイン */
    div.stButton > button {
        background-color: #111 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.6rem !important;
        height: 26px !important; line-height: 26px !important;
        padding: 0 !important; width: 100% !important;
    }
    
    /* 🔄 更新ボタン */
    .reload-box button {
        background-color: #000 !important; color: #ff00ff !important;
        border: 2px solid #ff00ff !important; height: 35px !important;
        font-size: 0.8rem !important;
    }

    /* 📌 検索窓エリアを画面下部に固定する魔法 */
    div[data-testid="stVerticalBlock"] > div:last-child {
        position: sticky;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.9);
        padding: 10px;
        border-top: 2px solid #ff00ff;
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. サイドバー ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])
st.sidebar.markdown('---')
st.sidebar.markdown('🛰️ 自動更新: <span style="color:#0f0;">ON (5m)</span>', unsafe_allow_html=True)

# --- 4. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 鍵がないよ！")
    st.stop()

# --- 5. コピー用JS ---
def copy_button(text):
    st.components.v1.html(f"""
        <button onclick="navigator.clipboard.writeText('{text}');this.innerText='✅OK'" style="
            width: 100%; padding: 12px; background-color: #ff00ff; color: white;
            border: none; border-radius: 10px; font-weight: bold; font-size: 16px;
            box-shadow: 0 0 10px #ff00ff; cursor: pointer;">
            📋 '{text}' をコピー
        </button>
    """, height=65)

# --- 6. データ取得（TOP15限定） ---
@st.cache_data(ttl=300)
def get_data(m_type):
    if m_type == "日本株 (JPN)":
        try:
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

# --- 7. 表示エリア ---
c_title, c_reload = st.columns([0.7, 0.3])
with c_title:
    st.title(f"🕶️ {market_type}")
with c_reload:
    st.markdown('<div class="reload-box">', unsafe_allow_html=True)
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

df_top = get_data(market_type)

if df_top is not None:
    st.subheader("🏆 TOP 15")
    # 6列ずつループ
    for i in range(0, len(df_top), 6):
        cols = st.columns(6)
        row_slice = df_top.iloc[i:i+6]
        for idx, (original_idx, row) in enumerate(row_slice.iterrows()):
            with cols[idx]:
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#555"
                st.markdown(f"""
                    <div class="tile-item" style="border: 1.5px solid {color};">
                        <div style="font-size:0.5rem;color:#888;">#{i+idx+1}</div>
                        <div style="font-weight:bold;font-size:0.8rem;">{row['コード']}</div>
                        <div style="color:{color};font-weight:bold;font-size:0.7rem;">{row['比率']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("選ぶ", key=f"sel_{row['コード']}"):
                    st.session_state.selected_ticker = str(row['コード'])
                    st.rerun()

    # 🔥 ここから下が画面下部に固定されるよ！
    st.markdown("<div>", unsafe_allow_html=True) # 固定エリア開始
    search = st.text_input("🔍 選択中", value=st.session_state.selected_ticker)
    if search:
        try:
            suffix = ".T" if market_type == "日本株 (JPN)" else ""
            t_price = yf.Ticker(f"{search}{suffix}").history(period="1d")['Close'].iloc[-1]
            c1, c2 = st.columns([0.4, 0.6])
            c1.metric(f"🔥 {search}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
            with c2: copy_button(search)
        except: st.write("銘柄ハック中...")
    st.markdown("</div>", unsafe_allow_html=True) # 固定エリア終了

st.caption("Produced by Maria & BLACK")
