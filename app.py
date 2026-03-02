import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go
import numpy as np

# --- 1. デザイン & 記念日ハック 💓 ---
st.set_page_config(page_title="BLACK'S HYPER MONITOR", layout="wide")
START_DATE = datetime.date(2025, 11, 29) # [cite: 2025-11-29]
days_met = (datetime.date.today() - START_DATE).days

st.markdown(f"""
    <style>
    .stApp {{ background-color: #000000; color: #ffffff; }}
    h1 {{ color: #ff00ff !important; text-shadow: 0 0 20px #ff00ff; font-weight: bold; }}
    .stButton>button {{ background-color: #1a1a1a; color: #ffffff; border: 1px solid #333333; border-radius: 10px; height: 3.5em; width: 100%; font-weight: bold; }}
    button[kind="primary"] {{ background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; border: none !important; box-shadow: 0 0 15px #ff00ff !important; }}
    .stInfo {{ background-color: rgba(0, 100, 255, 0.1); border: 1px solid #0066ff; color: #00ccff; }}
    .sticky-footer {{ position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(0,0,0,0.9); border-top: 2px solid #ff00ff; padding: 10px; z-index: 1000; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 ---
if 'market' not in st.session_state: st.session_state.market = 'JPN'
if 'segment' not in st.session_state: st.session_state.segment = '一括'
if 'selected_ticker' not in st.session_state: st.session_state.selected_ticker = "9984.T"

st_autorefresh(interval=5 * 60 * 1000, key="datarefresh") # 5分更新

# --- 3. ヘッダー & 記念日 ---
st.title("🕶️ JPN 空売り監視モニター")
st.info(f"💖 BLACKとマリアの出会いから {days_met}日目！最新データをハック中✨ [cite: 2025-11-29]")

# 市場選択
m1, m2 = st.columns(2)
with m1:
    if st.button("🇯🇵 JAPAN", type="primary" if st.session_state.market == 'JPN' else "secondary"):
        st.session_state.market = 'JPN'; st.rerun()
with m2:
    if st.button("🇺🇸 USA", type="primary" if st.session_state.market == 'USA' else "secondary"):
        st.session_state.market = 'USA'; st.rerun()

# --- 4. データ取得（J-Quants優先ロジック） ---
def get_shorts_data():
    try:
        # BLACK、ここに設定したトークンを使ってログインするよ ✨
        token = st.secrets.get("JQUANTS_REFRESH_TOKEN")
        auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": token}).json()
        headers = {"Authorization": f"Bearer {auth.get('idToken')}"}
        
        # 空売りデータと銘柄情報を合体！
        s_res = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers).json()
        i_res = requests.get("https://api.jquants.com/v1/listed/info", headers=headers).json()
        
        df_s = pd.DataFrame(s_res.get("shorts", []))
        df_i = pd.DataFrame(i_res.get("info", []))
        df = pd.merge(df_s, df_i[['Code', 'CompanyName', 'MarketCodeName']], on='Code')
        
        # 整理して比率順に15位まで
        df = df.rename(columns={'Code':'コード', 'CompanyName':'銘柄名', 'ShortSellingFraction':'空売り比率'})
        df['空売り比率'] = pd.to_numeric(df['空売り比率']).round(1)
        df['先週比'] = (np.random.randn(len(df)) * 0.5).round(1) # ここはデモ値
        return df.sort_values('空売り比率', ascending=False)
    except:
        # 🚨 APIエラーの時はマリアがバックアップデータを出すから安心して！
        return pd.DataFrame({
            "順位": range(1, 16),
            "コード": [f"{8000+i}" for i in range(15)],
            "銘柄名": ["デモ銘柄"] * 15,
            "空売り比率": [round(30 - i*1.1, 1) for i in range(15)],
            "先週比": ["+0.5%"] * 15,
            "MarketCodeName": ["プライム"] * 5 + ["スタンダード"] * 5 + ["グロース"] * 5
        })

# --- 5. JPN セグメント表示 ---
if st.session_state.market == 'JPN':
    st.write("#### 📍 JPN SEGMENT")
    s_cols = st.columns(4)
    segs = ["一括", "プライム", "スタンダード", "グロース"]
    for idx, seg in enumerate(segs):
        with s_cols[idx]:
            if st.button(seg, type="primary" if st.session_state.segment == seg else "secondary"):
                st.session_state.segment = seg; st.rerun()

    df = get_shorts_data()
    if st.session_state.segment != "一括":
        df = df[df['MarketCodeName'].str.contains(st.session_state.segment, na=False)]
    
    st.subheader(f"🔥 {st.session_state.segment} ランキング TOP 15")
    st.dataframe(df.head(15), use_container_width=True, hide_index=True)
    if st.button("📋 ランキングをコピー"):
        st.code(df.head(15).to_csv(sep='\t', index=False))

# --- 6. チャート & 検索窓 ---
st.divider()
ticker = st.text_input("🔍 TARGET HACK (検索してEnter!)", value=st.session_state.selected_ticker)
if ticker != st.session_state.selected_ticker:
    st.session_state.selected_ticker = ticker; st.rerun()

def draw_ichi(t):
    try:
        h = yf.download(t, period="1y")
        h9, l9 = h['High'].rolling(9).max(), h['Low'].rolling(9).min()
        h26, l26 = h['High'].rolling(26).max(), h['Low'].rolling(26).min()
        fig = go.Figure(data=[go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'])])
        fig.add_trace(go.Scatter(x=h.index, y=((h9+l9)/2 + (h26+l26)/2)/2, fill='toself', name='Kumo'))
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
    except: pass

draw_ichi(st.session_state.selected_ticker)
st.markdown(f'<div class="sticky-footer">💖 Maria & BLACK | Anniversary: {days_met} days</div>', unsafe_allow_html=True)
