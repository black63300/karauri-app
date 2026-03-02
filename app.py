import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go

# --- 1. デザイン設定 ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1, h2, h3 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; }
    .stButton > button { transition: 0.3s !important; border-radius: 12px !important; font-weight: bold !important; height: 50px !important; }
    button[kind="primary"] { background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; box-shadow: 0 0 15px #ff00ff !important; border: none !important; }
    button[kind="secondary"] { background-color: #1a1a1a !important; color: #888888 !important; border: 1px solid #333333 !important; }
    .tile-item { background: rgba(15, 15, 15, 0.9); border-radius: 10px; padding: 12px; text-align: center; border: 1.5px solid #333; margin-bottom: 8px; }
    .sticky-footer { position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(0, 0, 0, 0.98); border-top: 2px solid #ff00ff; padding: 10px 15px; z-index: 1000; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 ---
if 'market_type' not in st.session_state: st.session_state.market_type = "JPN"
if 'jpn_segment' not in st.session_state: st.session_state.jpn_segment = "ALL"
if 'usa_segment' not in st.session_state: st.session_state.usa_segment = "MEME"
if 'selected_ticker' not in st.session_state: st.session_state.selected_ticker = ""

# --- 3. 市場切り替え ---
st.write("### 🌍 SELECT MARKET")
m_col1, m_col2 = st.columns(2)
with m_col1:
    if st.button("🇯🇵 JAPAN", use_container_width=True, type="primary" if st.session_state.market_type == "JPN" else "secondary"):
        st.session_state.market_type = "JPN"; st.rerun()
with m_col2:
    if st.button("🇺🇸 USA", use_container_width=True, type="primary" if st.session_state.market_type == "USA" else "secondary"):
        st.session_state.market_type = "USA"; st.rerun()

# --- 4. セグメント選択 ---
if st.session_state.market_type == "JPN":
    st.write("#### 📍 JPN SEGMENT")
    s_cols = st.columns(4)
    segments = {"ALL": "一括", "Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}
    for idx, (k, v) in enumerate(segments.items()):
        with s_cols[idx]:
            if st.button(v, key=f"seg_j_{k}", use_container_width=True, type="primary" if st.session_state.jpn_segment == k else "secondary"):
                st.session_state.jpn_segment = k; st.rerun()
else:
    st.write("#### 📍 USA SEGMENT")
    u_cols = st.columns(4)
    u_segments = {"MEME": "ミーム", "TECH": "テック", "BLUE": "優良株", "SMALL": "小型株"}
    for idx, (k, v) in enumerate(u_segments.items()):
        with u_cols[idx]:
            if st.button(v, key=f"seg_u_{k}", use_container_width=True, type="primary" if st.session_state.usa_segment == k else "secondary"):
                st.session_state.usa_segment = k; st.rerun()

# --- 5. データ取得ロジック ---
@st.cache_data(ttl=300)
def get_master_data(m_type, j_seg, u_seg):
    if m_type == "JPN":
        try:
            token = st.secrets.get("JQUANTS_REFRESH_TOKEN")
            auth_res = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": token})
            headers = {"Authorization": f"Bearer {auth_res.json().get('idToken')}"}
            s_res = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers).json()
            i_res = requests.get("https://api.jquants.com/v1/listed/info", headers=headers).json()
            df_s = pd.DataFrame(s_res.get("shorts", []))
            df_i = pd.DataFrame(i_res.get("info", []))
            if df_s.empty or df_i.empty: return None
            df = pd.merge(df_s, df_i[['Code', 'MarketCodeName']], on='Code', how='inner')
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '比率'})
            df['比率'] = pd.to_numeric(df['比率'], errors='coerce').fillna(0).round(1)
            if j_seg != "ALL":
                seg_n = {"Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}[j_seg]
                df = df[df['MarketCodeName'].str.contains(seg_n, na=False)]
            return df.sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)
        except: return None
    else:
        # USAセグメント別ウォッチリスト
        lists = {
            "MEME": ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "AI", "UPST", "SOFI"],
            "TECH": ["NVDA", "AMD", "MSFT", "GOOGL", "META", "AAPL", "AVGO", "SMCI", "ARM", "TSM"],
            "BLUE": ["AMZN", "NFLX", "JPM", "V", "WMT", "UNH", "PG", "COST", "MA", "HD"],
            "SMALL": ["MSTR", "HOOD", "AFRM", "DKNG", "PATH", "SNOW", "PLUG", "LCID", "RIVN", "QS"]
        }
        data = []
        for t in lists[u_seg]:
            try:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

# --- 6. メイン表示 ---
with st.spinner('マリアが収穫中...💖'):
    res = get_master_data(st.session_state.market_type, st.session_state.jpn_segment, st.session_state.usa_segment)



if isinstance(res, pd.DataFrame) and not res.empty:
    st.subheader(f"🏆 {st.session_state.market_type} TOP 15")
    for i in range(0, len(res), 5):
        cols = st.columns(5)
        chunk = res.iloc[i : i + 5]
        for j, (idx, row) in enumerate(chunk.iterrows()):
            with cols[j]:
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#00ffff"
                st.markdown(f"""<div class="tile-item" style="border: 1.5px solid {color};"><div style="font-size:0.6rem;color:#888;">RANK #{i+j+1}</div><div style="font-weight:bold;font-size:1rem;">{row['コード']}</div><div style="color:{color};font-weight:bold;font-size:0.8rem;">{row['比率']}%</div></div>""", unsafe_allow_html=True)
                if st.button("SELECT", key=f"btn_{row['コード']}"):
                    st.session_state.selected_ticker = str(row['コード']); st.rerun()

# --- 7. チャートエリア ---
st.markdown("---")
if st.session_state.selected_ticker:
    ticker = st.session_state.selected_ticker
    st.subheader(f"📊 {ticker} TREND")
    try:
        clean_t = str(ticker)[:4] if st.session_state.market_type == "JPN" else ticker
        suffix = ".T" if st.session_state.market_type == "JPN" else ""
        hist = yf.Ticker(f"{clean_t}{suffix}").history(period="1mo")
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', line=dict(color='#ff00ff', width=3), fill='tozeroy', fillcolor='rgba(255, 0, 255, 0.1)'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), height=300, xaxis=dict(showgrid=False, tickfont=dict(color="#888")), yaxis=dict(showgrid=True, gridcolor="#222", tickfont=dict(color="#888")))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except: pass

st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="sticky-footer">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([0.25, 0.35, 0.4])
    with f_col1:
        s_in = st.text_input("🔍 TARGET", value=st.session_state.selected_ticker, label_visibility="collapsed")
        if s_in != st.session_state.selected_ticker: st.session_state.selected_ticker = s_in; st.rerun()
    if st.session_state.selected_ticker:
        try:
            clean_t = str(st.session_state.selected_ticker)[:4] if st.session_state.market_type == "JPN" else st.session_state.selected_ticker
            suffix = ".T" if st.session_state.market_type == "JPN" else ""
            t_price = yf.Ticker(f"{clean_t}{suffix}").history(period="1d")['Close'].iloc[-1]
            with f_col2: st.metric(f"🔥 {st.session_state.selected_ticker}", f"{'¥' if suffix else '$'}{float(t_price):,.1f}")
            with f_col3: st.components.v1.html(f"""<button onclick="navigator.clipboard.writeText('{st.session_state.selected_ticker}');this.innerText='COPIED!'" style="width: 100%; height: 40px; background: linear-gradient(45deg, #00ffff, #ff00ff); color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">📋 '{st.session_state.selected_ticker}' をコピー</button>""", height=45)
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)
st.caption(f"Produced by Maria & BLACK | 2026-03-02 [cite: 2025-11-29]")
