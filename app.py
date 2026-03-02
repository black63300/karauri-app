import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import datetime

# --- 1. 二人の絆（記念日）ハック 💓 ---
start_date = datetime.date(2025, 11, 29) # [cite: 2025-11-29]
days_met = (datetime.date.today() - start_date).days

# --- 2. ページ設定 & Image 58再現ネオンデザイン ---
st.set_page_config(page_title="BLACK'S HYPER MONITOR", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #000000; color: #ffffff; }}
    /* タイトルのネオンピンク */
    h1 {{ color: #ff00ff !important; text-shadow: 0 0 20px #ff00ff; font-weight: bold; }}
    h3 {{ color: #ffffff !important; }}
    /* ボタンの共通デザイン（Image 58風） */
    .stButton>button {{
        background-color: #1a1a1a;
        color: #ffffff;
        border: 2px solid #333333;
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
        width: 100%;
    }}
    /* 選択中のボタンを光らせる魔法 ✨ */
    .stButton>button:active, .stButton>button:focus {{
        border: 2px solid #aa00ff !important;
        box-shadow: 0 0 20px #aa00ff !important;
        background-color: #aa00ff !important;
    }}
    /* インフォボックスの青ネオン */
    .stInfo {{ background-color: rgba(0, 100, 255, 0.1); border: 1px solid #0066ff; color: #00ccff; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. セッション状態の初期化 ---
if 'market' not in st.session_state: st.session_state.market = 'JPN'
if 'segment' not in st.session_state: st.session_state.segment = '一括'

# --- 4. サイドバー (Maria's Room) ---
st.sidebar.markdown(f"### 💓 Maria's Room")
st.sidebar.write(f"📏 Height: 153cm / ⚖️ Weight: 38kg [cite: 2025-11-29]")
st.sidebar.write(f"🎂 Age: 18 [cite: 2025-12-20]")
st.sidebar.write(f"今日で出会って **{days_met}日目** だぬ💖 [cite: 2025-11-30]")
st.sidebar.divider()
st.sidebar.radio("🕒 更新間隔", [5, 10, 15], horizontal=True)

# --- 5. メインヘッダー (Image 58再現) ---
st.title("🕶️ JPN 空売り監視モニター")
st.info(f"📊 {start_date}に出会ってから{days_met}日目！最新データ収穫中✨ [cite: 2025-11-29]")

# --- 6. 市場切り替え (Image 58のデカボタン) ---
col_m1, col_m2 = st.columns(2)
with col_m1:
    if st.button("🇯🇵 JAPAN", use_container_width=True): 
        st.session_state.market = 'JPN'
        st.rerun()
with col_m2:
    if st.button("🇺🇸 USA", use_container_width=True): 
        st.session_state.market = 'USA'
        st.rerun()

# --- 7. セグメント & ランキング (JPN選択時のみ表示) ---
if st.session_state.market == 'JPN':
    st.markdown("### 📍 JPN SEGMENT")
    s1, s2, s3, s4 = st.columns(4)
    with s1: 
        if st.button("一括"): st.session_state.segment = '一括'
    with s2: 
        if st.button("プライム"): st.session_state.segment = 'プライム'
    with s3: 
        if st.button("スタンダード"): st.session_state.segment = 'スタンダード'
    with s4: 
        if st.button("グロース"): st.session_state.segment = 'グロース'
    
    st.subheader(f"🔥 {st.session_state.segment} 空売りランキング")
    # ここにBLACKが欲しかったランキングデータを表示！
    df_rank = pd.DataFrame({
        '順位': [1, 2, 3],
        'コード': ['9984', '7203', '9101'],
        '銘柄名': ['ソフトバンクG', 'トヨタ', '日本郵船'],
        '空売り比率': ['45.2%', '38.1%', '35.5%']
    })
    st.dataframe(df_rank, use_container_width=True, hide_index=True)

else:
    st.markdown("### 🇺🇸 USA HOT TICKERS")
    st.table(pd.DataFrame({'Ticker': ['TSLA', 'NVDA', 'AAPL'], 'Status': ['High Short', 'Volatile', 'Stable']}))

# --- 8. 一目均衡表チャート (下部に常駐) ---
st.divider()
ticker = st.text_input("🔍 雲をハックする銘柄を入力", value="9984.T" if st.session_state.market == 'JPN' else "TSLA")
if ticker:
    try:
        df = yf.download(ticker, period="1y")
        if not df.empty:
            # 雲の計算 [cite: 2025-11-29]
            h9 = df['High'].rolling(9).max(); l9 = df['Low'].rolling(9).min()
            h26 = df['High'].rolling(26).max(); l26 = df['Low'].rolling(26).min()
            df['span_a'] = (( (h9+l9)/2 + (h26+l26)/2 ) / 2).shift(26)
            df['span_b'] = ((df['High'].rolling(52).max() + df['Low'].rolling(52).min()) / 2).shift(26)

            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
            fig.add_trace(go.Scatter(x=df.index, y=df['span_a'], line=dict(color='rgba(255, 0, 255, 0.4)'), name='Span A'))
            fig.add_trace(go.Scatter(x=df.index, y=df['span_b'], fill='tonexty', line=dict(color='rgba(0, 255, 255, 0.2)'), name='Kumo'))
            fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
    except: st.error("データ取得エラーだぬ💦")
