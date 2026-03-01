import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・iPhone物理タイル） ---
st.set_page_config(page_title="BLACK'S FULL MONITOR", layout="wide")

# 自動更新 (5分)
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; font-size: 1.5rem !important; }
    
    /* 📱 iPhone縦横対応・強制グリッドシステム */
    .grid-container {
        display: grid;
        gap: 8px;
        grid-template-columns: repeat(3, 1fr); /* デフォルト縦3列 */
        width: 100%;
        margin-bottom: 20px;
    }
    
    @media (min-width: 600px) {
        .grid-container {
            grid-template-columns: repeat(6, 1fr); /* 横画面なら6列 */
        }
    }
    
    .tile-box {
        background-color: #111;
        border-radius: 8px;
        padding: 6px;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 85px;
    }
    
    /* 更新ボタンのデザイン */
    .reload-btn button {
        background-color: #000 !important; color: #ff00ff !important;
        border: 2px solid #ff00ff !important; width: 100% !important;
        font-weight: bold !important; box-shadow: 0 0 10px #ff00ff !important;
    }
    
    /* 選ぶボタンのデザイン */
    .select-btn button {
        background-color: #222 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.7rem !important;
        height: 28px !important; padding: 0 !important; width: 100% !important;
        box-shadow: 0 0 5px #00ffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション & サイドバー ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])
st.sidebar.markdown('🛰️ 自動更新: <span style="color:#0f0;">ON</span>', unsafe_allow_html=True)

# --- 3. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 鍵がないよ！")
    st.stop()

# --- 4. コピー機能 ---
def copy_button(text):
    st.components.v1.html(f"""
        <button onclick="navigator.clipboard.writeText('{text}');this.innerText='✅OK'" style="
            width: 100%; padding: 15px; background-color: #ff00ff; color: white;
            border: none; border-radius: 12px; font-weight: bold; font-size: 18px;
            box-shadow: 0 0 15px #ff00ff; cursor: pointer;">
            📋 '{text}' をコピー
        </button>
    """, height=80)

# --- 5. データ取得 ---
@st.cache_data(ttl=300)
def get_full_data(m_type):
    if m_type == "日本株 (JPN)":
        try:
            res_auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": REFRESH_TOKEN})
            headers = {"Authorization": f"Bearer {res_auth.json().get('idToken')}"}
            res_data = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
            df = pd.DataFrame(res_data.json().get("shorts", []))
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '比率'})
            df['比率'] = pd.to_numeric(df['比率']).round(1)
            return df.sort_values(by='比率', ascending=False).head(30).reset_index(drop=True)
        except: return None
    else:
        # 🔥 米国株リストを30個に拡張
        watch = ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "NVDA", "NFLX", "AMD", "GOOGL", "META", "AAPL", "AMZN", "MSFT", 
                 "MSTR", "UPST", "CVNA", "AI", "SOFI", "LCID", "RIVN", "HOOD", "AFRM", "PATH", "SNOW", "PLUGS", "DKNG", "UBER", "ABNB"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).head(30).reset_index(drop=True)

# --- 6. 表示 ---
col_t, col_r = st.columns([0.6, 0.4])
with col_t:
    st.title(f"🕶️ {market_type}")
with col_r:
    st.markdown('<div class="reload-btn">', unsafe_allow_html=True)
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

df_top = get_full_data(market_type)

if df_top is not None:
    st.write("🏆 TOP30")
    # 🔥 物理グリッドコンテナの開始
    st.markdown('<div class="grid-container">', unsafe_allow_html=True)
    
    # 30位まで個別のタイルとして描画
    for i, row in df_top.iterrows():
        color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#555"
        
        # タイルの外枠をHTMLで描画
        st.markdown(f"""
            <div class="tile-box" style="border: 1.5px solid {color};">
                <div style="font-size:0.55rem; color:#888;">#{i+1}</div>
                <div style="font-weight:bold; font-size:0.9rem;">{row['コード']}</div>
                <div style="color:{color}; font-weight:bold; font-size:0.8rem;">{row['比率']}%</div>
            </div>
        """, unsafe_allow_html=True)
        
        # ボタンだけはStreamlitの機能を使う（連動させるため）
        st.markdown('<div class="select-btn">', unsafe_allow_html=True)
        if st.button("選ぶ", key=f"sel_{row['コード']}"):
            st.session_state.selected_ticker = str(row['コード'])
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True) # コンテナ終了

    st.markdown("---")
    search = st.text_input("🔍 選択中", value=st.session_state.selected_ticker)
    if search:
        try:
            suffix = ".T" if market_type == "日本株 (JPN)" else ""
            t_price = yf.Ticker(f"{search}{suffix}").history(period="1d")['Close'].iloc[-1]
            st.metric(f"🔥 {search}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
            copy_button(search)
        except: st.write("ハック中...")

st.caption("Produced by Maria & BLACK")
