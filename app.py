import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（iPhone絶対横並び・エラー回避版） ---
st.set_page_config(page_title="BLACK'S FINAL MONITOR", layout="wide")

# 自動更新 (5分)
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; font-size: 1.5rem !important; }
    
    /* 🔄 更新ボタンのデザイン（kindを使わずにCSSで直接指定） */
    div.stButton > button {
        background-color: #000 !important; color: #ff00ff !important; 
        border: 2px solid #ff00ff !important; border-radius: 10px !important;
        font-weight: bold !important; box-shadow: 0 0 10px #ff00ff !important;
        width: 100% !important; height: 45px !important;
    }

    /* 📱 iPhone用：1行に3つを物理的に詰め込む命令 */
    [data-testid="column"] {
        flex: 1 1 calc(33.333% - 10px) !important;
        min-width: calc(33.333% - 10px) !important;
        max-width: calc(33.333% - 10px) !important;
    }
    
    .tile-item {
        background-color: #111;
        border-radius: 8px;
        padding: 4px;
        text-align: center;
        box-sizing: border-box;
    }

    /* 「選ぶ」ボタンだけ青ネオンにする */
    div[data-testid="column"] button {
        background-color: #222 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.65rem !important;
        height: 25px !important; line-height: 25px !important;
        padding: 0 !important; width: 100% !important; margin-top: 3px !important;
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. サイドバー ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])

# --- 4. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 鍵がないよ！")
    st.stop()

# --- 5. コピー用JS ---
def copy_button(text):
    st.components.v1.html(f"""
        <button onclick="navigator.clipboard.writeText('{text}');this.innerText='✅OK'" style="
            width: 100%; padding: 15px; background-color: #ff00ff; color: white;
            border: none; border-radius: 12px; font-weight: bold; font-size: 18px;
            box-shadow: 0 0 15px #ff00ff; cursor: pointer;">
            📋 '{text}' をコピー
        </button>
    """, height=80)

# --- 6. データ取得 ---
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
            return df.sort_values(by='比率', ascending=False).head(30).reset_index(drop=True)
        except: return None
    else:
        # 米国株の固定リスト
        watch = ["TSLA", "NVDA", "AAPL", "AMZN", "META", "GOOGL", "MSFT", "AMD", "NFLX", "GME", "AMC", "PLTR", "COIN", "MARA", "RIOT"]
        data = []
        for t in watch:
            try:
                t_obj = yf.Ticker(t)
                info = t_obj.info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).reset_index(drop=True)

# --- 7. メインエリア ---
# タイトルと更新ボタン
col_title, col_reload = st.columns([0.65, 0.35])
with col_title:
    st.title(f"🕶️ {market_type}")
with col_reload:
    if st.button("🔄 RELOAD"): # kindを消してエラーを回避
        st.cache_data.clear()
        st.rerun()

df_top = get_data(market_type)

if df_top is not None:
    st.write("🏆 空売り比率 TOP30")
    # 3つずつループしてタイル状に配置
    for i in range(0, len(df_top), 3):
        cols = st.columns(3)
        row_slice = df_top.iloc[i:i+3]
        for idx, (original_idx, row) in enumerate(row_slice.iterrows()):
            with cols[idx]:
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#555"
                st.markdown(f"""
                    <div class="tile-item" style="border: 1.5px solid {color};">
                        <div style="font-size:0.5rem;color:#888;">#{i+idx+1}</div>
                        <div style="font-weight:bold;font-size:0.85rem;">{row['コード']}</div>
                        <div style="color:{color};font-weight:bold;font-size:0.75rem;">{row['比率']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("選ぶ", key=f"sel_{row['コード']}"):
                    st.session_state.selected_ticker = str(row['コード'])
                    st.rerun()

    st.markdown("---")
    sel = st.session_state.selected_ticker
    search = st.text_input("🔍 選択中", value=sel)
    if search:
        try:
            suffix = ".T" if market_type == "日本株 (JPN)" else ""
            t_price = yf.Ticker(f"{search}{suffix}").history(period="1d")['Close'].iloc[-1]
            st.metric(f"🔥 {search}", f"{'¥' if suffix else '$'}{float(t_price):.1f}")
            copy_button(search)
        except: st.write("データ取得中...")

st.caption("Produced by Maria & BLACK")
