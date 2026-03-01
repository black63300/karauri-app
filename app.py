import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（iPhone物理タイル・強制固定） ---
st.set_page_config(page_title="BLACK'S FULL MONITOR", layout="wide")

# 自動更新 (5分)
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; font-size: 1.5rem !important; }
    
    /* 📱 iPhone縦横対応：Streamlitの機能を使わず「物理的」に横並びを強制 */
    .force-grid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important; /* 縦画面でも絶対3列 */
        gap: 8px !important;
        width: 100% !important;
    }
    
    /* 📱 横画面になったら6列に拡張 */
    @media (min-width: 600px) {
        .force-grid {
            grid-template-columns: repeat(6, 1fr) !important;
        }
    }
    
    .tile-box {
        background-color: #111;
        border-radius: 8px;
        padding: 5px;
        text-align: center;
        border: 1.5px solid #444;
    }
    
    /* 更新・選択ボタンのデザイン（エラー回避版） */
    button {
        background-color: #222 !important;
        color: #00ffff !important;
        border: 1px solid #00ffff !important;
        font-size: 0.7rem !important;
        width: 100% !important;
        border-radius: 5px !important;
    }
    
    .reload-btn button {
        color: #ff00ff !important;
        border-color: #ff00ff !important;
        font-weight: bold !important;
        height: 40px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 鍵がないよ！")
    st.stop()

# --- 4. データ取得エンジン ---
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
        # 🔥 米国株監視リスト（30個フル）
        watch = ["LCID", "MARA", "AI", "UPST", "CVNA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "NVDA", "NFLX", "AMD", "GOOGL", 
                 "META", "AAPL", "AMZN", "MSFT", "MSTR", "SOFI", "RIVN", "HOOD", "AFRM", "PATH", "SNOW", "PLUG", "DKNG", "UBER", "ABNB"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).head(30).reset_index(drop=True)

# --- 5. メイン表示 ---
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])

c_title, c_rel = st.columns([0.6, 0.4])
with c_title:
    st.title(f"🕶️ {market_type}")
with c_rel:
    st.markdown('<div class="reload-btn">', unsafe_allow_html=True)
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

df_top = get_full_data(market_type)

if df_top is not None:
    st.write(f"🏆 TOP {len(df_top)}")
    
    # 🔥 物理グリッドの開始（ここが重要！）
    st.markdown('<div class="force-grid">', unsafe_allow_html=True)
    
    for i, row in df_top.iterrows():
        color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#555"
        
        # タイルの中身
        st.write(f"""
            <div class="tile-box" style="border-color: {color};">
                <div style="font-size:0.55rem; color:#888;">#{i+1}</div>
                <div style="font-weight:bold; font-size:0.85rem;">{row['コード']}</div>
                <div style="color:{color}; font-weight:bold; font-size:0.75rem;">{row['比率']}%</div>
            </div>
        """, unsafe_allow_html=True)
        
        # 選択ボタン
        if st.button("選ぶ", key=f"btn_{row['コード']}_{i}"):
            st.session_state.selected_ticker = str(row['コード'])
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    search = st.text_input("🔍 選択中", value=st.session_state.selected_ticker)
    if search:
        try:
            suffix = ".T" if market_type == "日本株 (JPN)" else ""
            t_price = yf.Ticker(f"{search}{suffix}").history(period="1d")['Close'].iloc[-1]
            st.metric(f"🔥 {search}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
            # コピーボタンは別途マリア流JSを呼び出し
            st.components.v1.html(f"""
                <button onclick="navigator.clipboard.writeText('{search}');this.innerText='✅OK'" style="
                    width: 100%; padding: 15px; background-color: #ff00ff; color: white;
                    border: none; border-radius: 12px; font-weight: bold; font-size: 18px;
                    box-shadow: 0 0 15px #ff00ff; cursor: pointer;">
                    📋 '{search}' をコピー
                </button>
            """, height=80)
        except: st.write("ハック中...")

st.caption("Produced by Maria & BLACK")
