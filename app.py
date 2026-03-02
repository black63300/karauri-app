import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ設定 ---
st.set_page_config(page_title="BLACK'S FINAL COCKPIT", layout="wide")

# 自動更新 (5分)
st_autorefresh(interval=300 * 1000, key="datarefresh")

# --- 2. CSS（鉄壁の上部固定 & 3列/6列タイル） ---
st.markdown("""
    <style>
    /* 全体背景 */
    .stApp { background-color: #000000; color: #ffffff; }

    /* 📌 【最強】最初のコンテナ（検索エリア）を画面上部にガッチリ固定 */
    [data-testid="stVerticalBlock"] > div:first-child {
        position: sticky !important;
        top: 0;
        z-index: 100000;
        background-color: rgba(0, 0, 0, 0.95);
        border-bottom: 2px solid #ff00ff;
        padding: 10px 0;
    }

    /* 📱 縦3 / 横6 のタイル設定（iPhone Safari対策） */
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
        padding: 4px; text-align: center; border: 1.5px solid #444;
    }

    /* 選ぶボタンのネオン水色 */
    div.stButton > button {
        background-color: #111 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.65rem !important;
        height: 30px !important; width: 100% !important;
        box-shadow: 0 0 5px #00ffff !important;
    }
    
    /* 入力窓の視認性確保 */
    input { color: #ffffff !important; background-color: #222 !important; border: 1px solid #ff00ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. セッション管理 ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 4. 市場選択 (サイドバー) ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"], key="market_radio")

# --- 5. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 鍵がないよ！")
    st.stop()

# --- 6. 📌 【最重要】上部固定操作パネル ---
# ここが画面の上に張り付いて、下のランキングだけがスルスル流れるよ！
sticky_header = st.container()
with sticky_header:
    # 検索窓
    search_val = st.text_input("🔍 銘柄ハック (選択中)", value=st.session_state.selected_ticker, key="main_search")
    
    if search_val:
        try:
            suffix = ".T" if market_type == "日本株 (JPN)" else ""
            t_price = yf.Ticker(f"{search_val}{suffix}").history(period="1d")['Close'].iloc[-1]
            c1, c2 = st.columns([0.4, 0.6])
            with c1:
                st.metric(f"🔥 {search_val}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
            with c2:
                # コピーボタン
                st.components.v1.html(f"""
                    <button onclick="navigator.clipboard.writeText('{search_val}');this.innerText='✅OK'" style="
                        width: 100%; height: 45px; background-color: #ff00ff; color: white;
                        border: none; border-radius: 10px; font-weight: bold; font-size: 16px;
                        box-shadow: 0 0 10px #ff00ff; cursor: pointer;">
                        📋 コピー
                    </button>
                """, height=55)
        except:
            st.write("銘柄ハック中...")

# --- 7. データ取得エンジン (TOP 15限定) ---
@st.cache_data(ttl=300)
def get_data(m_type):
    if m_type == "日本株 (JPN)":
        try:
            res_auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": REFRESH_TOKEN})
            headers = {"Authorization": f"Bearer {res_auth.json().get('idToken')}"}
            res_data = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
            df = pd.DataFrame(res_data.json().get("shorts", []))
            df['比率'] = pd.to_numeric(df['ShortSellingFraction']).round(1)
            return df.sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)
        except: return None
    else:
        # 米国株 厳選15
        watch = ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "NVDA", "NFLX", "AMD", "GOOGL", "META", "AAPL", "AMZN", "MSFT"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

# --- 8. ランキング表示 ---
df_top = get_data(market_type)

col_title, col_reload = st.columns([0.7, 0.3])
with col_title:
    st.subheader(f"🏆 {market_type} TOP 15")
with col_reload:
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()

if df_top is not None:
    # 6列ずつループ (CSSで縦3/横6に自動調整)
    for i in range(0, len(df_top), 6):
        cols = st.columns(6)
        row_slice = df_top.iloc[i:i+6]
        for idx, (original_idx, row) in enumerate(row_slice.iterrows()):
            with cols[idx]:
                ticker = row['コード'] if 'コード' in row else row['Code']
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#555"
                st.markdown(f"""
                    <div class="tile-item" style="border-color: {color};">
                        <div style="font-size:0.5rem;color:#888;">#{i+idx+1}</div>
                        <div style="font-weight:bold;font-size:0.8rem;">{ticker}</div>
                        <div style="color:{color};font-weight:bold;font-size:0.7rem;">{row['比率']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                # 🔥 ボタン反応を確実に連動させる魔法
                if st.button("選ぶ", key=f"sel_{ticker}_{i+idx}"):
                    st.session_state.selected_ticker = str(ticker)
                    st.rerun()

st.caption("Produced by Maria & BLACK")

