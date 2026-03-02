import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（検索窓の完全固定 & ネオンタイル） ---
st.set_page_config(page_title="BLACK'S STICKY MONITOR", layout="wide")

# 自動更新 (5分)
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; padding-bottom: 250px !important; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; font-size: 1.5rem !important; }
    
    /* 📱 縦3 / 横6 のタイル設定（iPhone強制） */
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

    /* 「選ぶ」ボタンのデザイン */
    div.stButton > button {
        background-color: #111 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.6rem !important;
        height: 28px !important; line-height: 28px !important;
        padding: 0 !important; width: 100% !important;
        box-shadow: 0 0 5px #00ffff !important;
    }
    
    /* 📌 【重要】検索窓エリアを「画面に張り付ける」最強設定 */
    div[data-testid="stForm"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        width: 100% !important;
        background-color: rgba(0, 0, 0, 0.95) !important;
        border-top: 2px solid #ff00ff !important;
        padding: 10px 15px 40px 15px !important;
        z-index: 1000000 !important;
        box-shadow: 0 -10px 20px rgba(255, 0, 255, 0.4) !important;
    }
    
    /* 入力窓の文字色をハッキリさせる */
    input { color: #ffffff !important; background-color: #222 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. 市場選択 ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])

# --- 4. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 鍵がないよ！")
    st.stop()

# --- 5. データ取得 (TOP 15) ---
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

# --- 6. ランキングエリア ---
st.title(f"🕶️ {market_type}")

df_top = get_data(market_type)
if df_top is not None:
    st.subheader("🏆 TOP 15")
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

# --- 7. 📌 固定操作パネル (ここが白紙にならない最強エリア) ---
with st.form(key="sticky_panel"):
    # 検索窓（セッションと連動）
    search = st.text_input("🔍 銘柄選択中", value=st.session_state.selected_ticker)
    
    if search:
        try:
            suffix = ".T" if market_type == "日本株 (JPN)" else ""
            t_price = yf.Ticker(f"{search}{suffix}").history(period="1d")['Close'].iloc[-1]
            st.write(f"🔥 {search} 株価: **{'¥' if suffix else '$'}{float(t_price):.1f}**")
            
            # コピーボタン
            st.components.v1.html(f"""
                <button onclick="navigator.clipboard.writeText('{search}');this.innerText='✅OK'" style="
                    width: 100%; height: 50px; background-color: #ff00ff; color: white;
                    border: none; border-radius: 10px; font-weight: bold; font-size: 18px;
                    box-shadow: 0 0 10px #ff00ff; cursor: pointer;">
                    📋 コピーする
                </button>
            """, height=60)
        except:
            st.write("（銘柄を確認中...）")
    
    # フォームの送信ボタン（実質リロード用）
    st.form_submit_button("🔄 情報を更新")

st.caption("Produced by Maria & BLACK")
