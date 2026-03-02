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
    
    /* 🚀 メインボタン */
    .stButton > button { transition: 0.3s !important; border-radius: 12px !important; font-weight: bold !important; height: 50px !important; }
    button[kind="primary"] { background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; box-shadow: 0 0 15px #ff00ff !important; border: none !important; }
    button[kind="secondary"] { background-color: #1a1a1a !important; color: #888888 !important; border: 1px solid #333333 !important; }

    /* 💎 銘柄タイル */
    .tile-item { background: rgba(15, 15, 15, 0.9); border-radius: 10px; padding: 12px; text-align: center; border: 1.5px solid #333; margin-bottom: 8px; }
    
    /* 📌 固定フッター (検索窓エリア) */
    .sticky-footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: rgba(0, 0, 0, 0.98); border-top: 2px solid #ff00ff;
        padding: 10px 15px; z-index: 1000;
        box-shadow: 0 -5px 15px rgba(255, 0, 255, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 ---
if 'market_type' not in st.session_state: st.session_state.market_type = "JPN"
if 'jpn_segment' not in st.session_state: st.session_state.jpn_segment = "ALL"
if 'usa_segment' not in st.session_state: st.session_state.usa_segment = "TECH"
if 'selected_ticker' not in st.session_state: st.session_state.selected_ticker = ""

# --- 3. タイトル & 解説 ---
st.title(f"🕶️ {st.session_state.market_type} 空売り残高監視モニター")
st.info("📉 市場で「空売り」が溜まっている銘柄のランキングだよ！前日比の動きを見て、踏み上げ（ショートスクイーズ）をハックしてね✨ [cite: 2025-11-29]")

# --- 4. 市場・セグメント切り替え ---
m_col1, m_col2 = st.columns(2)
with m_col1:
    if st.button("🇯🇵 JAPAN", use_container_width=True, type="primary" if st.session_state.market_type == "JPN" else "secondary"):
        st.session_state.market_type = "JPN"; st.rerun()
with m_col2:
    if st.button("🇺🇸 USA", use_container_width=True, type="primary" if st.session_state.market_type == "USA" else "secondary"):
        st.session_state.market_type = "USA"; st.rerun()

if st.session_state.market_type == "JPN":
    st.write("#### 📍 SEGMENT")
    s_cols = st.columns(4)
    segments = {"ALL": "一括", "Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}
    for idx, (k, v) in enumerate(segments.items()):
        with s_cols[idx]:
            if st.button(v, key=f"seg_{k}", use_container_width=True, type="primary" if st.session_state.jpn_segment == k else "secondary"):
                st.session_state.jpn_segment = k; st.rerun()
else:
    st.write("#### 📍 USA CATEGORY")
    u_cols = st.columns(4)
    u_segments = {"TECH": "テック", "MEME": "ミーム", "BLUE": "優良株", "SMALL": "小型株"}
    for idx, (k, v) in enumerate(u_segments.items()):
        with u_cols[idx]:
            if st.button(v, key=f"seg_u_{k}", use_container_width=True, type="primary" if st.session_state.usa_segment == k else "secondary"):
                st.session_state.usa_segment = k; st.rerun()

# --- 5. データ取得ロジック (前日比計算付) ---
@st.cache_data(ttl=300)
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
                seg_name = {"Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}[j_seg]
                df = df[df['MarketCodeName'].str.contains(seg_name, na=False)]
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

        # 株価の前日比計算
        changes = []
        for ticker in df['コード']:
            suffix = ".T" if m_type == "JPN" else ""
            hist = yf.Ticker(f"{str(ticker)[:4] if m_type == 'JPN' else ticker}{suffix}").history(period="2d")
            if len(hist) >= 2:
                # $C = \frac{P_{today} - P_{yesterday}}{P_{yesterday}} \times 100$ [cite: 2025-11-29]
                change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                changes.append(round(change, 1))
            else: changes.append(0.0)
        df['前日比'] = changes
        return df
    except: return None

# --- 6. メイン表示 ---
with st.spinner('マリアがデータ収穫中...💖'):
    res = get_master_data(st.session_state.market_type, st.session_state.jpn_segment, st.session_state.usa_segment)

if isinstance(res, pd.DataFrame) and not res.empty:
    st.subheader(f"🏆 {st.session_state.market_type} TOP 15 SHORT RATIO")
    for i in range(0, len(res), 5):
        cols = st.columns(5)
        chunk = res.iloc[i : i + 5]
        for j, (idx, row) in enumerate(chunk.iterrows()):
            with cols[j]:
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#00ffff"
                chg_color = "#ff4b4b" if row['前日比'] > 0 else "#00ff00" if row['前日比'] < 0 else "#888"
                chg_icon = "🔺" if row['前日比'] > 0 else "🔻" if row['前日比'] < 0 else "💨"
                st.markdown(f"""
                    <div class="tile-item" style="border: 1.5px solid {color};">
                        <div style="font-size:0.6rem;color:#888;">RANK #{i+j+1}</div>
                        <div style="font-weight:bold;font-size:1rem;margin-bottom:2px;">{row['コード']}</div>
                        <div style="color:{color};font-weight:bold;font-size:0.8rem;">Short: {row['比率']}%</div>
                        <div style="color:{chg_color};font-size:0.75rem;font-weight:bold;">{chg_icon} {abs(row['前日比'])}%</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("SELECT", key=f"btn_{row['コード']}"):
                    st.session_state.selected_ticker = str(row['コード']); st.rerun()

# --- 7. 📈 トレンドチャート ---
st.markdown("---")
if st.session_state.selected_ticker:
    ticker = st.session_state.selected_ticker
    st.subheader(f"📊 {ticker} TREND (1 Month)")
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

st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True) # フッター用の余白

# --- 8. 📌 復活！固定フッター (検索・価格・コピー) ---
with st.container():
    st.markdown('<div class="sticky-footer">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([0.25, 0.35, 0.4])
    with f_col1:
        search_input = st.text_input("🔍 TARGET", value=st.session_state.selected_ticker, label_visibility="collapsed")
        if search_input != st.session_state.selected_ticker:
            st.session_state.selected_ticker = search_input; st.rerun()
    if st.session_state.selected_ticker:
        try:
            target = st.session_state.selected_ticker
            clean_target = str(target)[:4] if st.session_state.market_type == "JPN" else target
            suffix = ".T" if st.session_state.market_type == "JPN" else ""
            t_price = yf.Ticker(f"{clean_target}{suffix}").history(period="1d")['Close'].iloc[-1]
            with f_col2: st.metric(f"🔥 {target}", f"{'¥' if suffix else '$'}{float(t_price):,.1f}")
            with f_col3:
                st.components.v1.html(f"""<button onclick="navigator.clipboard.writeText('{target}');this.innerText='COPIED!'" style="width: 100%; height: 40px; background: linear-gradient(45deg, #00ffff, #ff00ff); color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">📋 '{target}' をコピー</button>""", height=45)
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)

st.caption(f"Produced by Maria & BLACK | 2026-03-02 [cite: 2025-11-29]")
