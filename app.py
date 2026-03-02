import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・完全分割コックピット） ---
st.set_page_config(page_title="BLACK'S FINAL COCKPIT", layout="wide")

# 自動更新 (5分)
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    
    /* 📌 【最強の固定術】検索エリアを画面上部にガッチリ固定 */
    [data-testid="stVerticalBlock"] > div:first-child {
        position: fixed !important;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #000000;
        z-index: 10000;
        padding: 10px 15px;
        border-bottom: 2px solid #ff00ff;
        box-shadow: 0 5px 15px rgba(255, 0, 255, 0.4);
    }

    /* 📱 ランキングエリアが固定ヘッダーの下に隠れないように余白を作る */
    [data-testid="stVerticalBlock"] > div:nth-child(2) {
        margin-top: 230px !important;
    }
    
    /* 📱 縦3 / 横6 の強制タイル表示 */
    [data-testid="column"] {
        flex: 1 1 calc(33.333% - 10px) !important;
        min-width: calc(33.333% - 10px) !important;
    }
    @media (min-width: 600px) {
        [data-testid="column"] {
            flex: 1 1 calc(16.666% - 10px) !important;
            min-width: calc(16.666% - 10px) !important;
        }
    }
    
    .tile-item {
        background-color: #111; border-radius: 8px;
        padding: 5px; text-align: center; border: 1.5px solid #444;
    }

    /* 「選ぶ」ボタンのデザイン */
    div.stButton > button {
        background-color: #111 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.7rem !important;
        height: 32px !important; width: 100% !important;
        box-shadow: 0 0 5px #00ffff !important;
    }
    
    /* 入力窓の白紙バグ対策 */
    input { color: #ffffff !important; background-color: #222 !important; border: 1px solid #ff00ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション状態 ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. サイドバー (市場切り替え) ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"], key="market_radio")

# --- 4. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 鍵がないよ！")
    st.stop()

# --- 5. 📌 固定ヘッダー（検索・株価・コピー） ---
# ここが画面の上に張り付いて、ランキングだけが下を流れるよ！
header = st.container()
with header:
    # 検索窓（セッションと完全に連動）
    search_val = st.text_input("🔍 銘柄ハック (選択中)", value=st.session_state.selected_ticker, key="main_search")
    
    # 手動入力されたらセッションを更新
    if search_val != st.session_state.selected_ticker:
        st.session_state.selected_ticker = search_val

    if st.session_state.selected_ticker:
        try:
            suffix = ".T" if market_type == "日本株 (JPN)" else ""
            t_price = yf.Ticker(f"{st.session_state.selected_ticker}{suffix}").history(period="1d")['Close'].iloc[-1]
            c1, c2 = st.columns([0.4, 0.6])
            with c1:
                st.metric(f"🔥 {st.session_state.selected_ticker}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
            with c2:
                # コピーボタン
                st.components.v1.html(f"""
                    <button onclick="navigator.clipboard.writeText('{st.session_state.selected_ticker}');this.innerText='✅OK'" style="
                        width: 100%; height: 50px; background-color: #ff00ff; color: white;
                        border: none; border-radius: 10px; font-weight: bold; font-size: 18px;
                        box-shadow: 0 0 10px #ff00ff; cursor: pointer;">
                        📋 '{st.session_state.selected_ticker}' コピー
                    </button>
                """, height=65)
        except: st.write("銘柄ハック中...")
    else:
        st.write("ランキングから選ぶか、入力してね✨")

# --- 6. データ取得エンジン (TOP 15) ---
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
        watch = ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "NVDA", "NFLX", "AMD", "GOOGL", "META", "AAPL", "AMZN", "MSFT"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

# --- 7. ランキングエリア ---
df_top = get_data(market_type)

c_title, c_reload = st.columns([0.7, 0.3])
with c_title:
    st.subheader(f"🏆 {market_type} TOP 15")
with c_reload:
    # 🔄 エラー回避のためkindを削除
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()

if df_top is not None:
    # 6列ずつループ表示
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
                # 🔥 ボタンを押した瞬間に再起動して上に反映させるよ！
                if st.button("選ぶ", key=f"sel_{ticker}_{i+idx}"):
                    st.session_state.selected_ticker = str(ticker)
                    st.rerun()

st.caption("Produced by Maria & BLACK")
