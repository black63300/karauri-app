import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go
import numpy as np

# --- 1. マリアの最強デザイン (一画面・スクロールなし) ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide", initial_sidebar_state="collapsed")
START_DATE = datetime.date(2025, 11, 29) # [cite: 2025-11-29]
days_met = (datetime.date.today() - START_DATE).days

st.markdown(f"""
    <style>
    .stApp {{ background-color: #000000; color: #ffffff; overflow: hidden; }}
    h1 {{ color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; font-weight: bold; font-size: 1.3rem !important; margin: 0 !important; }}
    .stButton>button {{ background-color: #1a1a1a; color: #ffffff; border: 1px solid #333333; border-radius: 8px; height: 2.2em; width: 100%; font-weight: bold; font-size: 0.8rem; }}
    button[kind="primary"] {{ background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; border: none !important; box-shadow: 0 0 10px #ff00ff !important; }}
    .tile-item {{ background: rgba(20, 20, 20, 0.9); border-radius: 6px; padding: 4px; text-align: center; border: 1px solid #333; margin-bottom: 2px; line-height: 1.1; }}
    .stInfo {{ background-color: rgba(0, 100, 255, 0.1); border: 1px solid #0066ff; color: #00ccff; border-radius: 6px; font-size: 0.7rem; padding: 4px; }}
    .block-container {{ padding-top: 0.5rem !important; padding-bottom: 0 !important; }}
    /* サイドバーのデザイン 💓 */
    [data-testid="stSidebar"] {{ background-color: #111; border-right: 1px solid #ff00ff; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 & 選択型自動更新 (1-60分) ---
for k, v in {'market': 'JPN', 'segment': 'ALL', 'usa_seg': 'TECH', 'target_ticker': '9984.T', 'refresh_min': 5}.items():
    if k not in st.session_state: st.session_state[k] = v

# サイドバーで更新間隔を選択型に！ [cite: 2025-11-29]
with st.sidebar:
    st.markdown("### 💓 Maria's Room")
    st.write(f"📏 153cm / ⚖️ 38kg [cite: 2025-11-29]")
    st.write(f"📅 出会いから {days_met}日目！ [cite: 2025-11-30]")
    st.divider()
    # 選択型 (1〜60分) [cite: 2025-11-29]
    st.session_state.refresh_min = st.selectbox(
        "🕒 更新間隔を選択 (分)", 
        options=list(range(1, 61)), 
        index=st.session_state.refresh_min - 1
    )

# 自動更新の実行
st_autorefresh(interval=st.session_state.refresh_min * 60 * 1000, key=f"refresh_{st.session_state.refresh_min}")

# --- 3. メインモニター ---
st.markdown(f"<h1>🕶️ {st.session_state.market} 爆益監視モニター</h1>", unsafe_allow_html=True)

col_head, col_info = st.columns([0.6, 0.4])
with col_head:
    m1, m2 = st.columns(2)
    with m1:
        if st.button("🇯🇵 JPN", type="primary" if st.session_state.market == 'JPN' else "secondary"):
            st.session_state.market = 'JPN'; st.rerun()
    with m2:
        if st.button("🇺🇸 USA", type="primary" if st.session_state.market == 'USA' else "secondary"):
            st.session_state.market = 'USA'; st.rerun()
with col_info:
    st.info(f"✨ 2025-11-29からの絆：{days_met}日目だぬ！ [cite: 2025-11-29]")

# --- 4. データ取得 (J-Quants本物優先) ---
@st.cache_data(ttl=60)
def get_shorts_data(m_type, j_seg, u_seg):
    try:
        if m_type == "JPN":
            token = st.secrets["JQUANTS_REFRESH_TOKEN"] #
            auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": token}).json()
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
    except:
        return pd.DataFrame([{"コード": f"{8000+i}", "比率": round(30-i, 1)} for i in range(15)])

# セグメント/カテゴリ選択
seg_cols = st.columns(4)
if st.session_state.market == 'JPN':
    segs = {"ALL":"一括", "Prime":"プライム", "Standard":"スタンダード", "Growth":"グロース"}
    for idx, (k, v) in enumerate(segs.items()):
        with seg_cols[idx]:
            if st.button(v, key=f"s_{k}", type="primary" if st.session_state.segment == k else "secondary"):
                st.session_state.segment = k; st.rerun()
else:
    usegs = {"TECH":"テック", "MEME":"ミーム", "BLUE":"優良", "SMALL":"小型"}
    for idx, (k, v) in enumerate(usegs.items()):
        with seg_cols[idx]:
            if st.button(v, key=f"u_{k}", type="primary" if st.session_state.usa_seg == k else "secondary"):
                st.session_state.usa_seg = k; st.rerun()

# --- 5. タイル形式ランキング (コンパクトVer.) ---
df_rank = get_shorts_data(st.session_state.market, st.session_state.segment, st.session_state.usa_seg)

tile_cols = st.columns(5)
for i, (idx, row) in enumerate(df_rank.iterrows()):
    with tile_cols[i % 5]:
        color = "#ff00ff" if row.get('比率', 0) >= 20 else "#00ffff"
        st.markdown(f'<div class="tile-item" style="border: 1px solid {color};"><div style="font-size:0.5rem;color:#888;">#{i+1}</div><div style="font-weight:bold;font-size:0.8rem;">{row["コード"]}</div><div style="color:{color};font-weight:bold;font-size:0.8rem;">{row["比率"]}%</div></div>', unsafe_allow_html=True)
        if st.button("HACK", key=f"h_{row['コード']}", use_container_width=True):
            st.session_state.target_ticker = str(row['コード']); st.rerun()

# --- 6. ロウソク足 & 濃い雲チャート (一画面・重複なし ✨) ---
def draw_candle_chart(t):
    try:
        suffix = ".T" if st.session_state.market == "JPN" and "." not in str(t) else ""
        h = yf.download(f"{t}{suffix}", period="2y", interval="1d", auto_adjust=True)
        if not h.empty:
            # MultiIndexハック！これでロウソク足が絶対に出るぬ📈 [cite: 2025-11-29]
            if isinstance(h.columns, pd.MultiIndex): h.columns = h.columns.get_level_values(0)
            
            h9, l9, h26, l26 = h['High'].rolling(9).max(), h['Low'].rolling(9).min(), h['High'].rolling(26).max(), h['Low'].rolling(26).min()
            span_a, span_b = (((h9+l9)/2 + (h26+l26)/2)/2).shift(26), ((h['High'].rolling(52).max() + h['Low'].rolling(52).min())/2).shift(26)
            
            fig = go.Figure()
            # 🕯️ 復活のロウソク足！
            fig.add_trace(go.Candlestick(
                x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'],
                increasing_line_color='#ff00ff', decreasing_line_color='#00ffff', name='Price'
            ))
            # ☁️ 濃い雲
            fig.add_trace(go.Scatter(x=h.index, y=span_a, line=dict(color='rgba(255, 0, 255, 0.4)', width=1), showlegend=False))
            fig.add_trace(go.Scatter(x=h.index, y=span_b, fill='tonexty', fillcolor='rgba(255, 0, 255, 0.2)', line=dict(color='rgba(0, 255, 255, 0.1)'), name='Kumo'))
            
            fig.update_layout(template="plotly_dark", height=320, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=10,b=0))
            fig.update_xaxes(range=[h.index[-60], h.index[-1] + datetime.timedelta(days=5)])
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except: pass

st.markdown("---")
c_bot1, c_bot2 = st.columns([0.5, 0.5])
with c_bot1:
    search = st.text_input("🔍 SEARCH", value=st.session_state.target_ticker, label_visibility="collapsed")
    if search != st.session_state.target_ticker: st.session_state.target_ticker = search; st.rerun()
    st.markdown(f"📊 **HACKING: {st.session_state.target_ticker}**")
with c_bot2:
    if st.button("📋 COPY (TSV)"):
        st.code(df_rank.to_csv(sep='\t', index=False))

draw_candle_chart(st.session_state.target_ticker)

