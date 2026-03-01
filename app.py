import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh # 🔥 これを復活させたよ！

# --- 1. デザイン（BLACK専用・iPhone絶対横並び） ---
st.set_page_config(page_title="BLACK'S FINAL MONITOR", layout="wide")

# 🔥 自動更新（5分 = 300秒ごとにリフレッシュ）
# これでBLACKが何もしなくても、マリアが勝手に最新にするよ！
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; font-size: 1.6rem !important; }
    
    /* 更新ボタンをネオン風に */
    div.stButton > button[kind="secondary"] {
        background-color: #000; color: #ff00ff; border: 2px solid #ff00ff;
        border-radius: 10px; font-weight: bold; box-shadow: 0 0 10px #ff00ff; width: 100%;
    }
    
    /* 選択ボタンをタイルにフィットさせる */
    div.stButton > button[kind="primary"] {
        background-color: #222 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; font-size: 0.7rem !important;
        height: 28px !important; padding: 0 !important; width: 100% !important;
    }
    
    /* タイル枠のスタイル */
    .tile-frame {
        border-radius: 8px; padding: 5px; text-align: center;
        background-color: #111; margin-bottom: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション状態 ---
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
@st.cache_data(ttl=300) # キャッシュも5分で切れるように設定
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
        watch = ["TSLA", "NVDA", "AAPL", "AMZN", "META", "GOOGL", "MSFT", "AMD", "NFLX", "GME", "AMC", "PLTR", "COIN", "MARA", "RIOT"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).reset_index(drop=True)

# --- 7. メイン表示 ---
col_head, col_rel = st.columns([0.7, 0.3])
with col_head:
    st.title(f"🕶️ {market_type}")
with col_rel:
    # 手動更新ボタンも残しておくね！
    if st.button("🔄 RELOAD", kind="secondary"):
        st.cache_data.clear()
        st.rerun()

df_top = get_data(market_type)

if df_top is not None:
    # 3列タイル
    for i in range(0, len(df_top), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(df_top):
                row = df_top.iloc[i + j]
                with cols[j]:
                    color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#444"
                    st.markdown(f"""
                        <div class="tile-frame" style="border: 1.5px solid {color};">
                            <div style="font-size:0.6rem;color:#888;">#{i+j+1}</div>
                            <div style="font-weight:bold;font-size:0.9rem;">{row['コード']}</div>
                            <div style="color:{color};font-weight:bold;font-size:0.8rem;">{row['比率']}%</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button("選ぶ", key=f"sel_{row['コード']}", kind="primary"):
                        st.session_state.selected_ticker = str(row['コード'])
                        st.rerun()

    st.markdown("---")
    # 検索・コピーエリア
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
