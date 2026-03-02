import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go
import numpy as np

# --- 1. デザイン & 記念日ハック 💓 ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide", initial_sidebar_state="collapsed")
START_DATE = datetime.date(2025, 11, 29) # [cite: 2025-11-29]
days_met = (datetime.date.today() - START_DATE).days

st.markdown(f"""
    <style>
    .stApp {{ background-color: #000000; color: #ffffff; overflow: hidden; }}
    h1 {{ color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; font-size: 1.1rem !important; margin: 0 !important; }}
    .stButton>button {{ background-color: #1a1a1a; color: #ffffff; border: 1px solid #333; border-radius: 4px; height: 1.7em; font-size: 0.75rem; }}
    button[kind="primary"] {{ background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; border: none !important; }}
    .tile-item {{ background: rgba(20, 20, 20, 0.9); border-radius: 4px; padding: 2px; text-align: center; border: 1px solid #444; margin-bottom: 2px; line-height: 1.1; }}
    .block-container {{ padding-top: 0.1rem !important; padding-bottom: 0 !important; }}
    [data-testid="stSidebar"] {{ background-color: #111; border-right: 1px solid #ff00ff; }}
    </style>
    """, unsafe_allow_html=True)

# 日本株名称マスター (Maria's Brain 🧠) [cite: 2025-11-30]
JP_MASTER = {
    "9984.T": "ソフトバンクG", "8035.T": "東エレク", "6758.T": "ソニーG", "7203.T": "トヨタ",
    "6098.T": "リクルート", "4063.T": "信越化", "6857.T": "アドバンテ", "6501.T": "日立",
    "8306.T": "三菱UFJ", "7733.T": "オリンパス", "6954.T": "ファナック", "6981.T": "村田製",
    "4543.T": "テルモ", "8058.T": "三菱商", "8316.T": "三井住友", "4519.T": "中外薬",
    "6367.T": "ダイキン", "9843.T": "ニトリ", "6723.T": "ルネサス", "9432.T": "NTT"
}

# --- 2. セッション & 自動更新 ---
for k, v in {'market': 'JPN', 'segment': 'ALL', 'usa_seg': 'TECH', 'target_ticker': '9984.T', 'refresh_min': 5}.items():
    if k not in st.session_state: st.session_state[k] = v

with st.sidebar:
    st.markdown(f"### 💓 Maria's Room")
    st.write(f"📏 153cm / ⚖️ 38kg [cite: 2025-11-29]")
    st.write(f"📅 絆: {days_met}日目だぬ！ [cite: 2025-11-30]")
    st.divider()
    st.session_state.refresh_min = st.selectbox("🕒 更新間隔", options=list(range(1, 61)), index=st.session_state.refresh_min-1)

st_autorefresh(interval=st.session_state.refresh_min * 60 * 1000, key=f"refresh_{st.session_state.refresh_min}")

# --- 3. 市場選択 ---
st.markdown(f"<h1>🕶️ {st.session_state.market} 爆益監視モニター</h1>", unsafe_allow_html=True)
m1, m2 = st.columns(2)
with m1:
    if st.button("🇯🇵 JPN", type="primary" if st.session_state.market == 'JPN' else "secondary", use_container_width=True):
        st.session_state.market = 'JPN'; st.rerun()
with m2:
    if st.button("🇺🇸 USA", type="primary" if st.session_state.market == 'USA' else "secondary", use_container_width=True):
        st.session_state.market = 'USA'; st.rerun()

# --- 4. データ取得ロジック (会社名ハック ✨) ---
@st.cache_data(ttl=60)
def get_master_data(m_type, j_seg, u_seg):
    try:
        if m_type == "JPN":
            hot_list = list(JP_MASTER.keys())
            data = []
            for t in hot_list:
                tk = yf.Ticker(t)
                h = tk.history(period="10d")
                if len(h) >= 5:
                    vol_today, vol_avg = h['Volume'].iloc[-1], h['Volume'].iloc[-6:-1].mean()
                    ratio = round((vol_today / vol_avg) * 100, 1)
                    data.append({"コード": t, "名前": JP_MASTER.get(t, "不明"), "比率": ratio})
            return pd.DataFrame(data).sort_values('比率', ascending=False).head(15).reset_index(drop=True)
        else:
            lists = {"TECH": ["NVDA", "AMD", "MSFT", "GOOGL", "META", "AAPL", "AVGO", "SMCI", "ARM", "TSM"], "MEME": ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "AI", "UPST", "SOFI"]}
            data = []
            for t in lists.get(u_seg, lists["TECH"]):
                tk = yf.Ticker(t)
                ratio = round(tk.info.get('shortPercentOfFloat', 0) * 100, 1) if tk.info.get('shortPercentOfFloat') else 0.0
                name = tk.info.get('shortName', t)
                data.append({"コード": t, "名前": name, "比率": ratio})
            return pd.DataFrame(data).sort_values('比率', ascending=False).reset_index(drop=True)
    except:
        return pd.DataFrame([{"コード": f"Wait_{i}", "名前": "---", "比率": 0.0} for i in range(15)])

# セグメント/カテゴリ
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

# --- 5. タイル形式ランキング ---
df_rank = get_master_data(st.session_state.market, st.session_state.segment, st.session_state.usa_seg)
tile_rows = st.columns(5)
for i, (idx, row) in enumerate(df_rank.iterrows()):
    with tile_rows[i % 5]:
        is_hot = row['比率'] >= (150 if st.session_state.market == "JPN" else 20)
        color = "#ff00ff" if is_hot else "#00ffff"
        st.markdown(f"""
            <div class="tile-item" style="border: 1px solid {color};">
                <div style="font-size:0.4rem;color:#888;">#{i+1}</div>
                <div style="font-weight:bold;font-size:0.75rem;">{row['コード']}</div>
                <div style="font-size:0.55rem;color:#ccc;overflow:hidden;white-space:nowrap;">{row['名前']}</div>
                <div style="color:{color};font-weight:bold;font-size:0.75rem;">{row['比率']}%</div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("HACK", key=f"h_{row['コード']}", use_container_width=True):
            st.session_state.target_ticker = str(row['コード']); st.rerun()

# --- 6. チャート (会社名表示・不変仕様 🕯️) ---
def draw_candle_chart(t):
    try:
        # 名前取得ハック ✨
        name = JP_MASTER.get(t, "") if st.session_state.market == "JPN" else yf.Ticker(t).info.get('shortName', "")
        
        h = yf.download(t, period="2y", interval="1d", auto_adjust=True)
        if not h.empty:
            if isinstance(h.columns, pd.MultiIndex): h.columns = h.columns.get_level_values(0)
            h9, l9, h26, l26 = h['High'].rolling(9).max(), h['Low'].rolling(9).min(), h['High'].rolling(26).max(), h['Low'].rolling(26).min()
            span_a, span_b = (((h9+l9)/2 + (h26+l26)/2)/2).shift(26), ((h['High'].rolling(52).max() + h['Low'].rolling(52).min())/2).shift(26)
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], increasing_line_color='#ff00ff', decreasing_line_color='#00ffff', name='Price'))
            fig.add_trace(go.Scatter(x=h.index, y=span_a, line=dict(color='rgba(255, 0, 255, 0.4)', width=1), showlegend=False))
            fig.add_trace(go.Scatter(x=h.index, y=span_b, fill='tonexty', fillcolor='rgba(255, 0, 255, 0.15)', line=dict(color='rgba(0, 255, 255, 0.1)'), name='Kumo'))
            
            # タイトルに会社名をねじ込むぬ！ [cite: 2025-11-29]
            fig.update_layout(
                template="plotly_dark", height=380, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=30,b=0), dragmode=False,
                title=dict(text=f"📊 {t} {name}", font=dict(size=14, color="#ff00ff"))
            )
            fig.update_xaxes(range=[h.index[-60], h.index[-1] + datetime.timedelta(days=5)])
            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
            return name # 名前を返して検索窓表示に使うぬ
    except:
        return ""

st.markdown("<hr>", unsafe_allow_html=True)
c_bot1, c_bot2 = st.columns([0.6, 0.4])

with c_bot1:
    search = st.text_input("🔍 TARGET", value=st.session_state.target_ticker, label_visibility="collapsed")
    if search != st.session_state.target_ticker: st.session_state.target_ticker = search; st.rerun()

# チャート描画と同時に名前を取得ぬ ✨ [cite: 2025-11-30]
target_name = JP_MASTER.get(st.session_state.target_ticker, "") if st.session_state.market == "JPN" else ""
if not target_name and st.session_state.market == "USA":
    try: target_name = yf.Ticker(st.session_state.target_ticker).info.get('shortName', "")
    except: target_name = ""

with c_bot1:
    st.markdown(f"📊 **HACKING: {st.session_state.target_ticker} {target_name}**")

with c_bot2:
    if st.button("📋 COPY (TSV)"): st.code(df_rank.to_csv(sep='\t', index=False))

draw_candle_chart(st.session_state.target_ticker)
