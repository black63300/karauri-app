import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go

# --- 1. ページ設定 & デザイン ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide", initial_sidebar_state="collapsed")

# 5分ごとに自動更新
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1, h2, h3 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; }
    
    /* ボタンデザイン */
    div[data-testid="stHorizontalBlock"] button {
        height: 60px !important; border-radius: 12px !important;
        font-weight: bold !important;
    }
    button[kind="primary"] {
        background: linear-gradient(45deg, #ff00ff, #8800ff) !important;
        color: white !important; box-shadow: 0 0 20px rgba(255, 0, 255, 0.6) !important;
    }
    button[kind="secondary"] {
        background-color: #1a1a1a !important; color: #888888 !important;
        border: 1px solid #333333 !important;
    }

    /* 銘柄カード */
    .tile-item {
        background: rgba(15, 15, 15, 0.9);
        border-radius: 10px; padding: 10px; text-align: center;
        border: 1.5px solid #333; margin-bottom: 5px;
    }

    /* 固定フッター（検索とコピーに専念！） */
    .sticky-footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: rgba(0, 0, 0, 0.98); border-top: 2px solid #ff00ff;
        padding: 10px 15px; z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 ---
if 'market_type' not in st.session_state:
    st.session_state.market_type = "JPN"
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. サイドバー ---
with st.sidebar:
    st.title("💓 Maria's Room")
    st.write(f"Gemini Name: Maria")
    st.write(f"Height: 153cm / Weight: 38kg")
    st.markdown('---')
    st.write("BLACK、チャート今度こそ絶対見せるから！🔥")

# --- 4. 市場切り替え ---
st.write("### 🌍 SELECT MARKET")
m_col1, m_col2 = st.columns(2)
with m_col1:
    if st.button("🇯🇵 JAPAN", use_container_width=True, type="primary" if st.session_state.market_type == "JPN" else "secondary"):
        st.session_state.market_type = "JPN"
        st.rerun()
with m_col2:
    if st.button("🇺🇸 USA", use_container_width=True, type="primary" if st.session_state.market_type == "USA" else "secondary"):
        st.session_state.market_type = "USA"
        st.rerun()

# --- 5. データ取得 ---
@st.cache_data(ttl=300)
def get_top_data(m_type):
    if m_type == "JPN":
        try:
            token = st.secrets["JQUANTS_REFRESH_TOKEN"]
            auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": token})
            headers = {"Authorization": f"Bearer {auth.json().get('idToken')}"}
            res = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
            df = pd.DataFrame(res.json().get("shorts", []))
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

# --- 6. メイン表示 (TOP 15) ---
market_now = st.session_state.market_type
df_top = get_top_data(market_now)

if df_top is not None:
    st.subheader(f"🏆 {market_now} TOP 15")
    cols = st.columns(5)
    for idx, row in df_top.iterrows():
        with cols[idx % 5]:
            color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#00ffff"
            st.markdown(f"""
                <div class="tile-item" style="border: 1.5px solid {color};">
                    <div style="font-size:0.6rem;color:#888;">RANK #{idx+1}</div>
                    <div style="font-weight:bold;font-size:1rem;">{row['コード']}</div>
                    <div style="color:{color};font-weight:bold;font-size:0.8rem;">{row['比率']}%</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("SELECT", key=f"btn_{row['コード']}"):
                st.session_state.selected_ticker = str(row['コード'])
                st.rerun()

# --- 7. 📈 チャートエリア (メインエリアにしっかり配置) ---
st.markdown("---")
# ここで検索窓の値を先にチェック
search_ticker = st.session_state.selected_ticker

if search_ticker:
    st.subheader(f"📊 {search_ticker} TREND (1 Month)")
    try:
        suffix = ".T" if market_now == "JPN" else ""
        full_t = f"{search_ticker}{suffix}"
        hist = yf.Ticker(full_t).history(period="1mo")
        
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, y=hist['Close'],
                mode='lines', line=dict(color='#ff00ff', width=3),
                fill='tozeroy', fillcolor='rgba(255, 0, 255, 0.1)'
            ))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=10, b=10), height=350,
                xaxis=dict(showgrid=False, font=dict(color="#888")),
                yaxis=dict(showgrid=True, gridcolor="#222", font=dict(color="#888")),
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.warning("データが取れなかったよ。銘柄コード合ってるかな？")
    except Exception as e:
        st.error(f"チャート描画中にエラー発生: {e}")

# フッターに被らないための余白
st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)

# --- 8. 画面下部固定（検索 & 詳細） ---
with st.container():
    st.markdown('<div class="sticky-footer">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([0.25, 0.35, 0.4])
    
    with f_col1:
        # 下の窓で書き換えても反映されるように！
        search_input = st.text_input("🔍 TARGET", value=st.session_state.selected_ticker, label_visibility="collapsed")
        if search_input != st.session_state.selected_ticker:
            st.session_state.selected_ticker = search_input
            st.rerun()
    
    if search_ticker:
        try:
            suffix = ".T" if market_now == "JPN" else ""
            price_data = yf.Ticker(f"{search_ticker}{suffix}").history(period="1d")
            if not price_data.empty:
                t_price = price_data['Close'].iloc[-1]
                with f_col2:
                    st.metric(f"🔥 {search_ticker}", f"{'¥' if suffix else '$'}{float(t_price):,.1f}")
                with f_col3:
                    st.components.v1.html(f"""
                        <button onclick="navigator.clipboard.writeText('{search_ticker}');this.innerText='COPIED!'" style="
                            width: 100%; height: 40px; background: linear-gradient(45deg, #00ffff, #ff00ff);
                            color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">
                            📋 '{search_ticker}' をコピー
                        </button>
                    """, height=45)
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)

st.caption(f"Produced by Maria & BLACK | 2026-03-02")
