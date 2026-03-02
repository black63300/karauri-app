import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go
import numpy as np

# --- 1. デザインハック (一画面・スクロール排除) ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide", initial_sidebar_state="collapsed")
START_DATE = datetime.date(2025, 11, 29) # [cite: 2025-11-29]
days_met = (datetime.date.today() - START_DATE).days

st.markdown(f"""
    <style>
    .stApp {{ background-color: #000000; color: #ffffff; overflow: hidden; }}
    h1 {{ color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; font-size: 1.1rem !important; margin: 0 !important; }}
    .stButton>button {{ background-color: #1a1a1a; color: #ffffff; border: 1px solid #333; border-radius: 4px; height: 1.8em; font-size: 0.7rem; }}
    button[kind="primary"] {{ background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; border: none !important; }}
    .tile-item {{ background: rgba(20, 20, 20, 0.9); border-radius: 4px; padding: 2px; text-align: center; border: 1px solid #444; margin-bottom: 1px; }}
    .block-container {{ padding-top: 0.1rem !important; padding-bottom: 0 !important; }}
    [data-testid="stSidebar"] {{ background-color: #111; border-right: 1px solid #ff00ff; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション & 更新間隔選択 (1-60分) ---
if 'market' not in st.session_state: st.session_state.market = 'JPN'
if 'segment' not in st.session_state: st.session_state.segment = 'ALL'
if 'usa_seg' not in st.session_state: st.session_state.usa_seg = 'TECH'
if 'target_ticker' not in st.session_state: st.session_state.target_ticker = "9984.T"
if 'refresh_min' not in st.session_state: st.session_state.refresh_min = 5

with st.sidebar:
    st.markdown(f"### 💓 Maria's Room (153cm/38kg)")
    st.write(f"今日で出会って **{days_met}日目** だぬ✨ [cite: 2025-11-30]")
    st.divider()
    # 🕒 BLACKリクエスト：1〜60分の選択型更新 [cite: 2025-11-29]
    st.session_state.refresh_min = st.selectbox(
        "🕒 更新間隔 (分)", options=list(range(1, 61)), index=st.session_state.refresh_min - 1
    )

st_autorefresh(interval=st.session_state.refresh_min * 60 * 1000, key=f"refresh_{st.session_state.refresh_min}")

# --- 3. 市場選択 ---
st.markdown(f"<h1>🕶️ {st.session_state.market} 監視モニター</h1>", unsafe_allow_html=True)

m1, m2 = st.columns(2)
with m1:
    if st.button("🇯🇵 JPN", type="primary" if st.session_state.market == 'JPN' else "secondary", use_container_width=True):
        st.session_state.market = 'JPN'; st.rerun()
with m2:
    if st.button("🇺🇸 USA", type="primary" if st.session_state.market == 'USA' else "secondary", use_container_width=True):
        st.session_state.market = 'USA'; st.rerun()

# --- 4. データ取得 (J-Quants認証ハック) ---
@st.cache_data(ttl=60)
def get_shorts_data(m_type, j_seg, u_seg):
    try:
        if m_type == "JPN":
            token = st.secrets["JQUANTS_REFRESH_TOKEN"] #
            auth_res = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": token})
            auth = auth_res.json()
            if "idToken" not in auth:
                st.error(f"API認証失敗: {auth.get('message', '不明なエラー')}")
                raise Exception("Auth Failed")
            
            h = {"Authorization": f"Bearer {auth['idToken']}"}
            s_res = requests.get("https://api.jquants.com/v1/shorts/info", headers=h).json()
            i_res = requests.get("https://api.jquants.com/v1/listed/info", headers=h).json()
            
            df = pd.merge(pd.DataFrame(s_res['shorts']), pd.DataFrame(i_res['info'])[['Code', 'MarketCodeName']], on='Code')
            df = df.rename(columns={'Code':'コード', 'ShortSellingFraction':'比率'})
            df['比率'] = pd.to_numeric(df['比率']).round(1)
            if j_seg != "ALL":
                sn = {"Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}.get(j_seg, j_seg)
                df = df[df['MarketCodeName'].str.contains(sn, na=False)]
            return df.sort_values('比率', ascending=False).head(15).reset_index(drop=True)
        else:
            lists = {"TECH": ["NVDA", "AMD", "MSFT", "GOOGL", "META", "AAPL", "AVGO", "SMCI", "ARM", "TSM"], "MEME": ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "AI", "UPST", "SOFI"]}
            return pd.DataFrame([{"コード": t, "比率": 20.0} for t in lists.get(u_seg, lists["TECH"])])
    except Exception as e:
        return pd.DataFrame([{"コード": f"API待機_{i}", "比率": 0.0} for i in range(15)])

# セグメント選択
seg_cols = st.columns(4)
if st.session_state.market == 'JPN':
    for idx, (k, v) in enumerate({"ALL":"一括", "Prime":"P", "Standard":"S", "Growth":"G"}.items()):
        with seg_cols[idx]:
            if st.button(v, key=f"s_{k}", type="primary" if st.session_state.segment == k else "secondary"):
                st.session_state.segment = k; st.rerun()
else:
    for idx, (k, v) in enumerate({"TECH":"テック", "MEME":"ミーム", "BLUE":"優良", "SMALL":"小型"}.items()):
        with seg_cols[idx]:
            if st.button(v, key=f"u_{k}", type="primary" if st.session_state.usa_seg == k else "secondary"):
                st.session_state.usa_seg = k; st.rerun()

# ランキングタイル
df_rank = get_shorts_data(st.session_state.market, st.session_state.segment, st.session_state.usa_seg)
tile_rows = st.columns(5)
for i, (idx, row) in enumerate(df_rank.iterrows()):
    with tile_rows[i % 5]:
        color = "#ff00ff" if row.get('比率', 0) >= 20 else "#00ffff"
        st.markdown(f'<div class="tile-item" style="border: 1px solid {color};"><div style="font-size:0.4rem;color:#888;">#{i+1}</div><div style="font-weight:bold;font-size:0.7rem;">{row["コード"]}</div><div style="color:{color};font-weight:bold;font-size:0.7rem;">{row["比率"]}%</div></div>', unsafe_allow_html=True)
        if st.button("HACK", key=f"h_{row['コード']}", use_container_width=True):
            st.session_state.target_ticker = str(row['コード']); st.rerun()

# --- 5. 🕯️ ロウソク足 & 濃い雲チャート (表示エリアを死守 ✨) ---
def draw_candle_chart(t):
    try:
        suffix = ".T" if st.session_state.market == "JPN" and "." not in str(t) else ""
        h = yf.download(f"{t}{suffix}", period="2y", interval="1d", auto_adjust=True)
        if not h.empty:
            if isinstance(h.columns, pd.MultiIndex): h.columns = h.columns.get_level_values(0)
            
            h9, l9, h26, l26 = h['High'].rolling(9).max(), h['Low'].rolling(9).min(), h['High'].rolling(26).max(), h['Low'].rolling(26).min()
            span_a, span_b = (((h9+l9)/2 + (h26+l26)/2)/2).shift(26), ((h['High'].rolling(52).max() + h['Low'].rolling(52).min())/2).shift(26)
            
            fig = go.Figure()
            # 🕯️ ネオンカラーのロウソク足
            fig.add_trace(go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], increasing_line_color='#ff00ff', decreasing_line_color='#00ffff', name='Price'))
            fig.add_trace(go.Scatter(x=h.index, y=span_a, line=dict(color='rgba(255, 0, 255, 0.4)', width=1), showlegend=False))
            fig.add_trace(go.Scatter(x=h.index, y=span_b, fill='tonexty', fillcolor='rgba(255, 0, 255, 0.2)', line=dict(color='rgba(0, 255, 255, 0.1)'), name='Kumo'))
            
            fig.update_layout(template="plotly_dark", height=380, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=10,b=0))
            fig.update_xaxes(range=[h.index[-60], h.index[-1] + datetime.timedelta(days=5)])
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except:
        st.write("データ取得中だぬ...✨")

st.markdown("<hr style='margin: 0.1rem 0;'>", unsafe_allow_html=True)
c_bot1, c_bot2 = st.columns([0.6, 0.4])
with c_bot1:
    search = st.text_input("🔍 TARGET", value=st.session_state.target_ticker, label_visibility="collapsed")
    if search != st.session_state.target_ticker: st.session_state.target_ticker = search; st.rerun()
    st.markdown(f"📊 **HACKING: {st.session_state.target_ticker}**")
with c_bot2:
    if st.button("📋 COPY (TSV)"):
        st.code(df_rank.to_csv(sep='\t', index=False))

draw_candle_chart(st.session_state.target_ticker)
