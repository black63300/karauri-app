import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・鉄壁の追尾レイアウト） ---
st.set_page_config(page_title="BLACK'S FINAL MONITOR", layout="wide")

# 自動更新 (5分)
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    /* 全体背景と下の余白（固定エリア分） */
    .stApp { background-color: #000000; color: #ffffff; padding-bottom: 220px !important; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; font-size: 1.4rem !important; margin-bottom: 0px; }
    
    /* 📱 縦3 / 横6 の強制タイル表示（iPhone Safari対策） */
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

    /* 📌 画面下に「張り付く」検索・コピーエリア */
    .sticky-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(0, 0, 0, 0.95);
        border-top: 2px solid #ff00ff;
        padding: 10px 15px 35px 15px; /* iPhoneのホームバー回避 */
        z-index: 99999;
        box-shadow: 0 -10px 20px rgba(255, 0, 255, 0.4);
    }
    
    /* 入力窓の白紙バグ対策 */
    input { color: #ffffff !important; background-color: #222 !important; border: 1px solid #ff00ff !important; }

    /* 「選ぶ」ボタンのネオン */
    div.stButton > button {
        background-color: #111 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.7rem !important;
        height: 32px !important; width: 100% !important; margin-top: 5px !important;
        box-shadow: 0 0 5px #00ffff !important;
    }
    
    /* リロードボタン */
    .reload-box button {
        background-color: #000 !important; color: #ff00ff !important;
        border: 2px solid #ff00ff !important; height: 35px !important;
        font-size: 0.8rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション & 市場切替 ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# サイドバーでの切替は確実に動くように外側に置くよ
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"], key="market_selector")

# --- 3. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 鍵がないよ！")
    st.stop()

# --- 4. データ取得エンジン (TOP 15) ---
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

# --- 5. メイン表示 (ランキング) ---
col_t, col_r = st.columns([0.7, 0.3])
with col_t:
    st.title(f"🕶️ {market_type}")
with col_r:
    st.markdown('<div class="reload-box">', unsafe_allow_html=True)
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

df_top = get_data(market_type)

if df_top is not None:
    st.subheader("🏆 TOP 15")
    # 3xN タイル表示
    for i in range(0, len(df_top), 6):
        cols = st.columns(6)
        row_slice = df_top.iloc[i:i+6]
        for idx, (original_idx, row) in enumerate(row_slice.iterrows()):
            with cols[idx]:
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#555"
                st.markdown(f"""
                    <div class="tile-item" style="border-color: {color};">
                        <div style="font-size:0.5rem;color:#888;">#{i+idx+1}</div>
                        <div style="font-weight:bold;font-size:0.85rem;">{row['コード']}</div>
                        <div style="color:{color};font-weight:bold;font-size:0.75rem;">{row['比率']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                # 🔥 ボタンの反応を改善（シンプルに更新）
                if st.button("選ぶ", key=f"sel_{row['コード']}_{market_type}"):
                    st.session_state.selected_ticker = str(row['コード'])
                    st.rerun()

# --- 6. 📌 固定フッター (指の届く位置に常駐) ---
st.markdown('<div class="sticky-footer">', unsafe_allow_html=True)

# 検索入力
search = st.text_input("🔍 銘柄ハック (選択中)", value=st.session_state.selected_ticker, key="footer_search")

if search:
    try:
        suffix = ".T" if market_type == "日本株 (JPN)" else ""
        t_price = yf.Ticker(f"{search}{suffix}").history(period="1d")['Close'].iloc[-1]
        
        c1, c2 = st.columns([0.4, 0.6])
        with c1:
            st.metric(f"🔥 {search}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
        with c2:
            st.components.v1.html(f"""
                <button onclick="navigator.clipboard.writeText('{search}');this.innerText='✅OK'" style="
                    width: 100%; height: 45px; background-color: #ff00ff; color: white;
                    border: none; border-radius: 10px; font-weight: bold; font-size: 16px;
                    box-shadow: 0 0 10px #ff00ff; cursor: pointer;">
                    📋 コピー
                </button>
            """, height=55)
    except:
        st.write("銘柄ハック中...")

st.markdown('</div>', unsafe_allow_html=True)

st.caption("Produced by Maria & BLACK")
