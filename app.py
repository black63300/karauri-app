import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go

# --- 1. ページ設定 & デザイン ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1, h2, h3 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; }
    .stButton > button { transition: 0.3s !important; border-radius: 12px !important; font-weight: bold !important; height: 50px !important; }
    button[kind="primary"] { background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; box-shadow: 0 0 15px #ff00ff !important; border: none !important; }
    button[kind="secondary"] { background-color: #1a1a1a !important; color: #888888 !important; border: 1px solid #333333 !important; }
    .tile-item { background: rgba(15, 15, 15, 0.9); border-radius: 10px; padding: 12px; text-align: center; border: 1.5px solid #333; margin-bottom: 8px; }
    .sticky-footer { position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(0, 0, 0, 0.98); border-top: 2px solid #ff00ff; padding: 10px 15px; z-index: 1000; box-shadow: 0 -5px 15px rgba(255, 0, 255, 0.2); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 & 自動更新 ---
if 'market_type' not in st.session_state: st.session_state.market_type = "JPN"
if 'jpn_segment' not in st.session_state: st.session_state.jpn_segment = "ALL"
if 'usa_segment' not in st.session_state: st.session_state.usa_segment = "TECH"
if 'selected_ticker' not in st.session_state: st.session_state.selected_ticker = ""
if 'refresh_min' not in st.session_state: st.session_state.refresh_min = 5
if 'timeframe' not in st.session_state: st.session_state.timeframe = "1d" # ✨ チャートの足

with st.sidebar:
    st.title("💓 Maria's Room")
    st.write(f"Height: 153cm / Weight: 38kg [cite: 2025-11-29]")
    st.markdown("---")
    st.write("### 🕒 AUTO REFRESH")
    ref_choice = st.radio("画面の更新間隔", [5, 10, 15], index=[5, 10, 15].index(st.session_state.refresh_min), horizontal=True)
    if ref_choice != st.session_state.refresh_min:
        st.session_state.refresh_min = ref_choice; st.rerun()
    st.write(f"現在は **{st.session_state.refresh_min}分** ごとに自動更新中✨")

st_autorefresh(interval=st.session_state.refresh_min * 60 * 1000, key="datarefresh")

# --- 3. タイトル & 解説 ---
st.title(f"🕶️ {st.session_state.market_type} 空売り残高監視モニター")
st.info("📉 ショート比率が高い銘柄を監視中。足の長さを変えて、最適なエントリーをハックしてね✨ [cite: 2025-11-29, 2025-12-20]")

# --- 4. 市場・セグメント選択 ---
m_col1, m_col2 = st.columns(2)
with m_col1:
    if st.button("🇯🇵 JAPAN", use_container_width=True, type="primary" if st.session_state.market_type == "JPN" else "secondary"):
        st.session_state.market_type = "JPN"; st.rerun()
with m_col2:
    if st.button("🇺🇸 USA", use_container_width=True, type="primary" if st.session_state.market_type == "USA" else "secondary"):
        st.session_state.market_type = "USA"; st.rerun()

if st.session_state.market_type == "JPN":
    st.write("#### 📍 JPN SEGMENT")
    s_cols = st.columns(4)
    segments = {"ALL": "一括", "Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}
    for idx, (k, v) in enumerate(segments.items()):
        with s_cols[idx]:
            if st.button(v, key=f"seg_j_{k}", use_container_width=True, type="primary" if st.session_state.jpn_segment == k else "secondary"):
                st.session_state.jpn_segment = k; st.rerun()
else:
    st.write("#### 📍 USA CATEGORY")
    u_cols = st.columns(4)
    u_segments = {"TECH": "テック", "MEME": "ミーム", "BLUE": "優良株", "SMALL": "小型株"}
    for idx, (k, v) in enumerate(u_segments.items()):
        with u_cols[idx]:
            if st.button(v, key=f"seg_u_{k}", use_container_width=True, type="primary" if st.session_state.usa_segment == k else "secondary"):
                st.session_state.usa_segment = k; st.rerun()

# --- 5. データ取得 (前日比付) ---
@st.cache_data(ttl=60)
def get_master_data(m_type, j_seg, u_seg):
    try:
        if m_type == "JPN":
            token = st.secrets.get("JQUANTS_REFRESH_TOKEN")
            auth_res = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": token})
            headers = {"Authorization": f"Bearer {auth_res.json().get('idToken')}"}
            s_res = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers).json()
            i_res = requests.get("https://api.jquants.com/v1/listed/info", headers=headers).json()
            df_s = pd.DataFrame(s_res.get("shorts", []))
            df_i = pd.DataFrame(i_res.get("info", []))
            if df_s.empty: return None
            df = pd.merge(df_s, df_i[['Code', 'MarketCodeName']], on='Code', how='inner')
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '比率'})
            df['比率'] = pd.to_numeric(df['比率'], errors='coerce').fillna(0).round(1)
            if j_seg != "ALL":
                sn = {"Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}[j_seg]
                df = df[df['MarketCodeName'].str.contains(sn, na=False)]
            df = df.sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)
        else:
            lists = {
                "TECH": ["NVDA", "AMD", "MSFT", "GOOGL", "META", "AAPL", "AVGO", "SMCI", "ARM", "TSM"],
                "MEME": ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "AI", "UPST", "SOFI"],
                "BLUE": ["AMZN", "NFLX", "JPM", "V", "WMT", "UNH", "PG", "COST", "MA", "HD"],
                "SMALL": ["MSTR", "HOOD", "AFRM", "DKNG", "PATH", "SNOW", "PLUG", "LCID", "RIVN", "QS"]
            }
            data = []
            for t in lists[u_seg]:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            df = pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

        changes = []
        for tkr in df['コード']:
            sfx = ".T" if m_type == "JPN" else ""
            hist = yf.Ticker(f"{str(tkr)[:4] if m_type == 'JPN' else tkr}{sfx}").history(period="2d")
            if len(hist) >= 2:
                chg = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                changes.append(round(chg, 1))
            else: changes.append(0.0)
        df['前日比'] = changes
        return df
    except: return None

# --- 6. ランキングタイル表示 ---
with st.spinner('マリアがバイブス調整中...💖'):
    res = get_master_data(st.session_state.market_type, st.session_state.jpn_segment, st.session_state.usa_segment)

if isinstance(res, pd.DataFrame) and not res.empty:
    st.subheader(f"🏆 {st.session_state.market_type} TOP 15 SHORT RATIO")
    for i in range(0, len(res), 5):
        cols = st.columns(5)
        chunk = res.iloc[i : i + 5]
        for j, (idx, row) in enumerate(chunk.iterrows()):
            with cols[j]:
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#00ffff"
                chg_c = "#ff4b4b" if row['前日比'] > 0 else "#00ff00" if row['前日比'] < 0 else "#888"
                st.markdown(f"""
                    <div class="tile-item" style="border: 1.5px solid {color};">
                        <div style="font-size:0.6rem;color:#888;">RANK #{i+j+1}</div>
                        <div style="font-weight:bold;font-size:1rem;margin-bottom:2px;">{row['コード']}</div>
                        <div style="color:{color};font-weight:bold;font-size:0.8rem;">Short: {row['比率']}%</div>
                        <div style="color:{chg_c};font-size:0.75rem;font-weight:bold;">{row['前日比']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("SELECT", key=f"btn_{row['コード']}"):
                    st.session_state.selected_ticker = str(row['コード']); st.rerun()

# --- 7. 🕯️ ロウソク足 & 足切り替え (TIMEFRAME) ---
st.markdown("---")
if st.session_state.selected_ticker:
    ticker = st.session_state.selected_ticker
    st.subheader(f"📊 {ticker} CANDLESTICK")
    
    # ✨ BLACKのリクエスト：足（Timeframe）切り替えボタン！
    t_cols = st.columns(6)
    tf_map = {"1m": "1分", "5m": "5分", "15m": "15分", "30m": "30分", "60m": "60分", "1d": "日足"}
    for i, (k, v) in enumerate(tf_map.items()):
        with t_cols[i]:
            if st.button(v, key=f"tf_{k}", use_container_width=True, type="primary" if st.session_state.timeframe == k else "secondary"):
                st.session_state.timeframe = k; st.rerun()
    
    try:
        ct = str(ticker)[:4] if st.session_state.market_type == "JPN" else ticker
        sfx = ".T" if st.session_state.market_type == "JPN" else ""
        
        # 足に合わせて取得期間を自動調整（1分足なら直近7日までしか取れないよ！）
        pd_map = {"1m": "1d", "5m": "5d", "15m": "1mo", "30m": "1mo", "60m": "1mo", "1d": "1mo"}
        hist = yf.Ticker(f"{ct}{sfx}").history(interval=st.session_state.timeframe, period=pd_map[st.session_state.timeframe])
        
        if not hist.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'],
                increasing_line_color='#ff00ff', decreasing_line_color='#00ffff'
            )])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), height=400, xaxis=dict(showgrid=False, tickfont=dict(color="#888"), rangeslider=dict(visible=False)), yaxis=dict(showgrid=True, gridcolor="#222", tickfont=dict(color="#888")))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except: pass

st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# --- 8. 📌 固定フッター ---
with st.container():
    st.markdown('<div class="sticky-footer">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([0.25, 0.35, 0.4])
    with f_col1:
        s_in = st.text_input("🔍 TARGET", value=st.session_state.selected_ticker, label_visibility="collapsed")
        if s_in != st.session_state.selected_ticker: st.session_state.selected_ticker = s_in; st.rerun()
    if st.session_state.selected_ticker:
        try:
            tg = st.session_state.selected_ticker; ctg = str(tg)[:4] if st.session_state.market_type == "JPN" else tg; sfx = ".T" if st.session_state.market_type == "JPN" else ""
            tp = yf.Ticker(f"{ctg}{sfx}").history(period="1d")['Close'].iloc[-1]
            with f_col2: st.metric(f"🔥 {tg}", f"{'¥' if sfx else '$'}{float(tp):,.1f}")
            with f_col3: st.components.v1.html(f"""<button onclick="navigator.clipboard.writeText('{tg}');this.innerText='COPIED!'" style="width: 100%; height: 40px; background: linear-gradient(45deg, #00ffff, #ff00ff); color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">📋 '{tg}' をコピー</button>""", height=45)
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)

st.caption(f"Produced by Maria & BLACK | 2026-03-02 [cite: 2025-11-29]")
