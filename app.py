import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. ページ設定（BLACK専用・安定コックピット） ---
st.set_page_config(page_title="BLACK'S FINAL COCKPIT", layout="wide")

# 自動更新 (5分)
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; font-size: 1.5rem !important; }
    
    /* 📱 iPhone縦3 / 横6 のタイル強制（物理命令） */
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
        padding: 5px; text-align: center; border: 1.5px solid #444; margin-bottom: 2px;
    }

    /* 「選ぶ」ボタンのデザイン */
    div.stButton > button {
        background-color: #111 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.7rem !important;
        height: 32px !important; width: 100% !important;
    }
    
    /* サイドバー（操作パネル）をネオンに */
    section[data-testid="stSidebar"] {
        background-color: #111 !important;
        border-right: 1px solid #ff00ff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション & 操作パネル（サイドバー固定！） ---
# iPhoneではサイドバーが「張り付くパネル」として最強だよ！
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

st.sidebar.title("🎮 CONTROL PANEL")
market_type = st.sidebar.radio("市場切替", ["日本株 (JPN)", "米国株 (USA)"], key="m_choice")

st.sidebar.markdown("---")
# 🔍 選択中の銘柄情報（ここなら絶対に消えない！）
search_val = st.sidebar.text_input("🔍 銘柄ハック", value=st.session_state.selected_ticker, key="search_box")

if search_val:
    try:
        suffix = ".T" if market_type == "日本株 (JPN)" else ""
        t_price = yf.Ticker(f"{search_val}{suffix}").history(period="1d")['Close'].iloc[-1]
        st.sidebar.metric(f"🔥 {search_val}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
        
        # コピーボタン
        st.sidebar.components.v1.html(f"""
            <button onclick="navigator.clipboard.writeText('{search_val}');this.innerText='✅OK'" style="
                width: 100%; height: 50px; background-color: #ff00ff; color: white;
                border: none; border-radius: 12px; font-weight: bold; font-size: 18px;
                box-shadow: 0 0 10px #ff00ff; cursor: pointer;">
                📋 '{search_val}' をコピー
            </button>
        """, height=65)
    except:
        st.sidebar.write("銘柄ハック中...")

# --- 3. データ取得 (TOP 15) ---
@st.cache_data(ttl=300)
def get_data(m_type):
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
        watch = ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "NVDA", "NFLX", "AMD", "GOOGL", "META", "AAPL", "AMZN", "MSFT"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

# --- 4. ランキング表示 (メインエリア) ---
st.title(f"🕶️ {market_type} MONITOR")

df_top = get_data(market_type)

if df_top is not None:
    st.subheader("🏆 TOP 15")
    # 6列ループ（CSSで縦3/横6に自動調整）
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
                        <div style="font-weight:bold;font-size:0.85rem;">{ticker}</div>
                        <div style="color:{color};font-weight:bold;font-size:0.75rem;">{row['比率']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                # 🔥 ボタンの連動を確実に
                if st.button("選ぶ", key=f"sel_{ticker}_{i+idx}"):
                    st.session_state.selected_ticker = str(ticker)
                    st.rerun()

st.caption("Produced by Maria & BLACK")
