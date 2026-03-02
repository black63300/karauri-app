import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・上部鉄壁固定コックピット） ---
st.set_page_config(page_title="BLACK'S FINAL COCKPIT", layout="wide")

# 🔥 自動更新ステータス（5分 = 300秒）
st_autorefresh(interval=300 * 1000, key="auto_refresh_trigger")

st.markdown("""
    <style>
    /* 全体背景 */
    .stApp { background-color: #000000; color: #ffffff; }

    /* 📌 【最強】最初のコンテナ（操作エリア）を画面上部にガッチリ固定 */
    [data-testid="stVerticalBlock"] > div:first-child {
        position: sticky !important;
        top: 0;
        z-index: 999999;
        background-color: rgba(0, 0, 0, 0.95);
        border-bottom: 2px solid #ff00ff;
        padding: 10px 0;
    }

    /* 📱 縦3 / 横6 のタイル強制設定 */
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
        padding: 5px; text-align: center; border: 1.5px solid #444;
    }

    /* 入力窓の視認性確保 */
    input { color: #ffffff !important; background-color: #222 !important; border: 1px solid #ff00ff !important; }

    /* 選ぶボタンのネオン水色 */
    div.stButton > button {
        background-color: #111 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.65rem !important;
        height: 30px !important; width: 100% !important;
        box-shadow: 0 0 5px #00ffff !important;
    }
    
    /* 🔄 更新ボタンのデザイン */
    .reload-container button {
        background-color: #000 !important; color: #ff00ff !important;
        border: 2px solid #ff00ff !important; font-weight: bold !important;
        box-shadow: 0 0 10px #ff00ff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. 市場選択 (サイドバー) ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"], key="market_radio")

# --- 4. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 鍵がないよ！")
    st.stop()

# --- 5. 📌 【最重要】上部固定操作パネル ---
# このコンテナが画面の上に張り付いて、下のランキングだけが流れるよ！
sticky_header = st.container()
with sticky_header:
    # 検索窓（セッションと連動）
    search_val = st.text_input("🔍 銘柄ハック (選択中)", value=st.session_state.selected_ticker, key="main_search")
    
    # セッション更新の同期
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
        except:
            st.write("銘柄ハック中...")

# --- 6. データ取得エンジン (TOP 15限定) ---
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

# --- 7. ランキング表示 ---
df_top = get_data(market_type)

col_title, col_reload = st.columns([0.7, 0.3])
with col_title:
    st.subheader(f"🏆 {market_type} TOP 15")
with col_reload:
    # 🔄 手動更新ボタンを復活させたよ！
    st.markdown('<div class="reload-container">', unsafe_allow_html=True)
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if df_top is not None:
    # 6列ループ (CSSで縦3/横6に自動調整)
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
                # 🔥 ボタンを押した瞬間に再描画して上の窓に反映！
                if st.button("選ぶ", key=f"sel_{ticker}_{i+idx}_{market_type}"):
                    st.session_state.selected_ticker = str(ticker)
                    st.rerun()

st.sidebar.markdown('🛰️ 自動更新: <span style="color:#0f0;">ON (5m)</span>', unsafe_allow_html=True)
st.caption("Produced by Maria & BLACK")
