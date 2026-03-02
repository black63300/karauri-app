import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（検索エリア上部固定 & 漆黒ネオン） ---
st.set_page_config(page_title="BLACK'S TOP-FIX MONITOR", layout="wide")

# 自動更新 (5分)
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    /* 全体背景と上部の余白（固定ヘッダー分） */
    .stApp { 
        background-color: #000000; 
        color: #ffffff; 
        padding-top: 220px !important; 
    }
    
    /* 📌 画面上部に検索エリアを固定する最強設定 */
    [data-testid="stHeader"] {
        display: none; /* 標準ヘッダーを消してスペース確保 */
    }
    
    .sticky-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 220px;
        background-color: #000000;
        border-bottom: 2px solid #ff00ff;
        padding: 10px 15px;
        z-index: 9999;
        box-shadow: 0 5px 15px rgba(255, 0, 255, 0.3);
    }
    
    /* 入力窓の文字が見えないバグ対策 */
    input {
        color: #ffffff !important;
        background-color: #222 !important;
        border: 1px solid #ff00ff !important;
    }
    
    /* 📱 縦3 / 横6 のタイル設定 */
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
        height: 28px !important; line-height: 28px !important; width: 100% !important;
    }
    
    .reload-box button {
        background-color: #000 !important; color: #ff00ff !important;
        border: 2px solid #ff00ff !important; height: 35px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. 市場選択（サイドバー） ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])
st.sidebar.write("🛰️ 自動更新: ON (5min)")

# --- 4. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.sidebar.error("🔑 鍵がないよ！")
    st.stop()

# --- 5. 📌 固定ヘッダーエリア (常に画面上に張り付く) ---
# この中身をHTMLタグで囲んで固定化するよ
st.markdown('<div class="sticky-header">', unsafe_allow_html=True)

# 検索窓
search = st.text_input("🔍 選択中 (直接入力もOK)", value=st.session_state.selected_ticker, key="main_search")

if search:
    try:
        suffix = ".T" if market_type == "日本株 (JPN)" else ""
        t_price = yf.Ticker(f"{search}{suffix}").history(period="1d")['Close'].iloc[-1]
        
        c1, c2 = st.columns([0.4, 0.6])
        with c1:
            st.metric(f"🔥 {search}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
        with c2:
            # コピーボタン
            st.components.v1.html(f"""
                <button onclick="navigator.clipboard.writeText('{search}');this.innerText='✅OK'" style="
                    width: 100%; height: 50px; background-color: #ff00ff; color: white;
                    border: none; border-radius: 10px; font-weight: bold; font-size: 18px;
                    box-shadow: 0 0 10px #ff00ff; cursor: pointer;">
                    📋 '{search}' コピー
                </button>
            """, height=60)
    except:
        st.write("銘柄を確認中...")
else:
    st.write("ランキングから選ぶか、入力してね✨")

st.markdown('</div>', unsafe_allow_html=True) # ヘッダー終了

# --- 6. データ取得 (TOP 15) ---
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
        # 米国株 厳選15
        watch = ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "NVDA", "NFLX", "AMD", "GOOGL", "META", "AAPL", "AMZN", "MSFT"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

# --- 7. メイン表示 (ランキングエリア) ---
col_t, col_r = st.columns([0.7, 0.3])
with col_t:
    st.subheader(f"🏆 {market_type} TOP 15")
with col_r:
    st.markdown('<div class="reload-box">', unsafe_allow_html=True)
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

df_top = get_data(market_type)

if df_top is not None:
    # 6列ずつループ表示 (CSSで縦3/横6に可変)
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

st.caption("Produced by Maria & BLACK")
