import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ設定 ---
st.set_page_config(page_title="BLACK'S PRO MONITOR", layout="wide")

# --- 2. サイドバー (市場切り替えはここ！) ---
# ここで選んだら、Mariaが即座にランキングを書き換えるよ！
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"], key="market_choice")

# --- 3. セッション管理 ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 4. CSS (デザイン & 検索窓の「上部固定」) ---
st.markdown("""
    <style>
    /* 全体背景 */
    .stApp { background-color: #000000; color: #ffffff; }
    
    /* 📌 画面の最初の要素（検索エリア）を「上に張り付ける」 */
    [data-testid="stVerticalBlock"] > div:first-child {
        position: sticky;
        top: 0;
        z-index: 1000;
        background-color: rgba(0, 0, 0, 0.95);
        border-bottom: 2px solid #ff00ff;
        padding: 10px;
    }
    
    /* 📱 縦3 / 横6 の可変タイル */
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
    
    /* タイルデザイン */
    .tile-item {
        background-color: #111; border-radius: 8px;
        padding: 4px; text-align: center; margin-bottom: 2px;
    }
    
    /* 入力窓の文字を見やすく */
    input { color: #ffffff !important; background-color: #222 !important; border: 1px solid #ff00ff !important; }
    
    /* 選ぶボタン */
    div.stButton > button {
        background-color: #111 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.6rem !important;
        height: 28px !important; line-height: 28px !important; width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. データ取得エンジン (TOP 15限定) ---
@st.cache_data(ttl=300)
def get_data(m_type):
    if m_type == "日本株 (JPN)":
        try:
            res_auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": st.secrets["JQUANTS_REFRESH_TOKEN"]})
            headers = {"Authorization": f"Bearer {res_auth.json().get('idToken')}"}
            res_data = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
            df = pd.DataFrame(res_data.json().get("shorts", []))
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '比率'})
            df['比率'] = pd.to_numeric(df['比率']).round(1)
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

# --- 6. UIエリア ---

# A. FIXED HEADER (検索窓 & 情報)
# このコンテナがCSSで上に固定されるよ！
header_area = st.container()
with header_area:
    search_input = st.text_input("🔍 銘柄ハック (選択中)", value=st.session_state.selected_ticker, key="main_search")
    
    if search_input:
        try:
            suffix = ".T" if market_type == "日本株 (JPN)" else ""
            t_price = yf.Ticker(f"{search_input}{suffix}").history(period="1d")['Close'].iloc[-1]
            c1, c2 = st.columns([0.4, 0.6])
            with c1:
                st.metric(f"🔥 {search_input}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
            with c2:
                # コピーボタン
                st.components.v1.html(f"""
                    <button onclick="navigator.clipboard.writeText('{search_input}');this.innerText='✅OK'" style="
                        width: 100%; height: 50px; background-color: #ff00ff; color: white;
                        border: none; border-radius: 10px; font-weight: bold; font-size: 16px;
                        box-shadow: 0 0 10px #ff00ff; cursor: pointer;">
                        📋 '{search_input}' コピー
                    </button>
                """, height=60)
        except:
            st.write("銘柄ハック中...")
    else:
        st.write("ランキングから選ぶか、入力してね✨")

# B. MAIN CONTENT (ランキング)
st_autorefresh(interval=300 * 1000, key="datarefresh")

df_top = get_data(market_type)

col_title, col_reload = st.columns([0.7, 0.3])
with col_title:
    st.subheader(f"🏆 {market_type} TOP 15")
with col_reload:
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()

if df_top is not None:
    # 6列ずつ表示 (縦3/横6はCSSで自動制御)
    for i in range(0, len(df_top), 6):
        cols = st.columns(6)
        row_slice = df_top.iloc[i:i+6]
        for idx, (original_idx, row) in enumerate(row_slice.iterrows()):
            with cols[idx]:
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#555"
                st.markdown(f"""
                    <div class="tile-item" style="border: 1.5px solid {color};">
                        <div style="font-size:0.5rem;color:#888;">#{idx+1 if i==0 else i+idx+1}</div>
                        <div style="font-weight:bold;font-size:0.8rem;">{row['コード']}</div>
                        <div style="color:{color};font-weight:bold;font-size:0.7rem;">{row['比率']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("選ぶ", key=f"sel_{row['コード']}"):
                    st.session_state.selected_ticker = str(row['コード'])
                    st.rerun()

st.caption("Produced by Maria & BLACK")
