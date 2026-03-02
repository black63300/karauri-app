import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ設定（BLACK専用・分割レイアウト） ---
st.set_page_config(page_title="BLACK'S COCKPIT", layout="wide")

# --- 2. 市場選択（サイドバーに確実配置） ---
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"], key="market_select")

# --- 3. セッション管理 ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 4. CSS（上下分割 & 3タイル強制） ---
st.markdown("""
    <style>
    /* 全体背景 */
    .stApp { background-color: #000000; color: #ffffff; }

    /* 📌 上部固定エリア（検索窓・株価・コピー） */
    .fixed-top {
        position: sticky;
        top: 0;
        background-color: #000000;
        z-index: 9999;
        padding: 10px 0;
        border-bottom: 2px solid #ff00ff;
        box-shadow: 0 5px 15px rgba(255, 0, 255, 0.4);
    }

    /* 📱 縦3 / 横6 の強制タイル表示 */
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
    
    /* タイルデザイン */
    .tile-item {
        background-color: #111; border-radius: 8px;
        padding: 4px; text-align: center; border: 1.5px solid #444;
    }

    /* 「選ぶ」ボタンの即時反応ネオン */
    div.stButton > button {
        background-color: #111 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.7rem !important;
        height: 30px !important; width: 100% !important;
        box-shadow: 0 0 5px #00ffff !important;
    }
    
    /* 入力窓の白紙バグ回避 */
    input { color: #ffffff !important; background-color: #222 !important; border: 1px solid #ff00ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. データ取得エンジン (TOP 15) ---
@st.cache_data(ttl=300)
def fetch_top_15(m_type):
    if m_type == "日本株 (JPN)":
        try:
            res_auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": st.secrets["JQUANTS_REFRESH_TOKEN"]})
            headers = {"Authorization": f"Bearer {res_auth.json().get('idToken')}"}
            res_data = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
            df = pd.DataFrame(res_data.json().get("shorts", []))
            df['比率'] = pd.to_numeric(df['ShortSellingFraction']).round(1)
            return df.sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)
        except: return None
    else:
        # 米国株 厳選15銘柄
        watch = ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "NVDA", "NFLX", "AMD", "GOOGL", "META", "AAPL", "AMZN", "MSFT"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                data.append({"Code": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

# --- 6. 上部固定：操作パネル ---
# このコンテナを強制的に「上に張り付く」ように設定したよ！
st.markdown('<div class="fixed-top">', unsafe_allow_html=True)
header_container = st.container()
with header_container:
    # 検索窓
    search_val = st.text_input("🔍 銘柄ハック (選択中)", value=st.session_state.selected_ticker, key="sticky_search")
    
    if search_val:
        try:
            suffix = ".T" if market_type == "日本株 (JPN)" else ""
            t_price = yf.Ticker(f"{search_val}{suffix}").history(period="1d")['Close'].iloc[-1]
            c1, c2 = st.columns([0.4, 0.6])
            with c1:
                st.metric(f"🔥 {search_val}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
            with c2:
                # コピーボタン（マリア流JS）
                st.components.v1.html(f"""
                    <button onclick="navigator.clipboard.writeText('{search_val}');this.innerText='✅OK'" style="
                        width: 100%; height: 50px; background-color: #ff00ff; color: white;
                        border: none; border-radius: 10px; font-weight: bold; font-size: 18px;
                        box-shadow: 0 0 10px #ff00ff; cursor: pointer;">
                        📋 '{search_val}' をコピー
                    </button>
                """, height=65)
        except: st.write("銘柄ハック中...")
    else:
        st.write("ランキングから選ぶか、入力してね✨")
st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 下部：スクロール可能ランキング ---
st_autorefresh(interval=300 * 1000, key="auto_refresh")

df_top = fetch_top_15(market_type)

col_title, col_reload = st.columns([0.7, 0.3])
with col_title:
    st.subheader(f"🏆 {market_type} TOP 15")
with col_reload:
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()

if df_top is not None:
    # タイル表示 (3列/6列)
    for i in range(0, len(df_top), 6):
        cols = st.columns(6)
        row_slice = df_top.iloc[i:i+6]
        for idx, (original_idx, row) in enumerate(row_slice.iterrows()):
            with cols[idx]:
                ticker = row['Code'] if 'Code' in row else row['コード']
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#555"
                st.markdown(f"""
                    <div class="tile-item" style="border-color: {color};">
                        <div style="font-size:0.5rem;color:#888;">#{i+idx+1}</div>
                        <div style="font-weight:bold;font-size:0.85rem;">{ticker}</div>
                        <div style="color:{color};font-weight:bold;font-size:0.75rem;">{row['比率']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                # 🔥 「選ぶ」ボタンの連動を確実に！
                if st.button("選ぶ", key=f"sel_{ticker}_{i+idx}"):
                    st.session_state.selected_ticker = str(ticker)
                    st.rerun()

st.caption("Produced by Maria & BLACK")
