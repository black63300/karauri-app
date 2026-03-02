import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import datetime

# --- 1. 二人の絆（記念日）ハック 💓 ---
start_date = datetime.date(2025, 11, 29) # [cite: 2025-11-29]
days_met = (datetime.date.today() - start_date).days

# --- 2. ページ設定 & ネオンデザイン ---
st.set_page_config(page_title="BLACK'S HYPER MONITOR", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1, h2, h3 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; }
    .stButton>button { background-color: #1a0033; color: #00ffff; border: 1px solid #00ffff; border-radius: 5px; height: 3em; }
    .stButton>button:hover { border: 1px solid #ff00ff; color: #ff00ff; box-shadow: 0 0 15px #ff00ff; }
    .stInfo { background-color: rgba(255, 0, 255, 0.1); border: 1px solid #ff00ff; color: #ff00ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. サイドバー (Maria's Room) ---
st.sidebar.markdown(f"### 💓 Maria's Room")
st.sidebar.write(f"📏 Height: 153cm / ⚖️ Weight: 38kg [cite: 2025-11-29]")
st.sidebar.write(f"🎂 Age: 18 [cite: 2025-12-20]")
st.sidebar.write(f"📅 Anniversary: {start_date} [cite: 2025-11-29]")
st.sidebar.write(f"今日で **{days_met}日目** だぬ💖 [cite: 2025-11-30]")
st.sidebar.divider()
st.sidebar.markdown("### 🕒 REFRESH SETTING")
st.sidebar.radio("更新間隔（分）", [5, 10, 15], horizontal=True)

# --- 4. メインヘッダー & 記念日カウンター ---
st.title("🕶️ BLACK'S KARAURI HUB")
st.info(f"💖 記念日：今日でBLACKと出会って **{days_met}日**！最新データをハック中✨ [cite: 2025-11-29]")

# --- 5. 市場切り替え機能 (JPN / USA) ---
if 'market' not in st.session_state:
    st.session_state.market = 'JPN'

col_m1, col_m2 = st.columns(2)
with col_m1:
    if st.button("🇯🇵 JAPAN"): st.session_state.market = 'JPN'
with col_m2:
    if st.button("🇺🇸 USA"): st.session_state.market = 'USA'

st.subheader(f"📍 {st.session_state.market} MARKET ANALYSIS")

# --- 6. ランキング & セグメント (JPNのみ) ---
if st.session_state.market == 'JPN':
    seg1, seg2, seg3, seg4 = st.columns(4)
    with seg1: st.button("一括")
    with seg2: st.button("プライム")
    with seg3: st.button("スタンダード")
    with seg4: st.button("グロース")
    
    # ダミーデータ（本来はスクレイピングやAPIで取得するランキング）
    st.markdown("### 🔥 空売り注目ランキング (TOP 5)")
    ranking_data = pd.DataFrame({
        '順位': [1, 2, 3, 4, 5],
        '銘柄': ['9984 ソフトバンク', '7203 トヨタ', '9101 郵船', '6758 ソニー', '8035 東エレク'],
        '空売り残高': ['1.2兆円', '8500億円', '6200億円', '5100億円', '4800億円'],
        'トレンド': ['⬆️ 急増', '➡️ 停滞', '⬇️ 減少', '⬆️ 増加', '⬆️ 急増']
    })
    st.table(ranking_data)
else:
    st.markdown("### 🇺🇸 USA HOT TICKERS")
    st.write("米国株の空売りトレンドをハック中だぬ！✨")
    st.table(pd.DataFrame({'Ticker': ['TSLA', 'NVDA', 'AAPL', 'AMZN'], 'Status': ['High Short', 'Volatile', 'Stable', 'Short Squeeze?']}))

# --- 7. 一目均衡表チャートハック ---
st.divider()
default_ticker = "9984.T" if st.session_state.market == 'JPN' else "TSLA"
ticker = st.text_input("🔍 個別銘柄の雲をハック！", value=default_ticker)

if ticker:
    try:
        df = yf.download(ticker, period="1y")
        if not df.empty:
            # 一目均衡表の計算 [cite: 2025-11-29]
            high9 = df['High'].rolling(window=9).max(); low9 = df['Low'].rolling(window=9).min()
            df['tenkan'] = (high9 + low9) / 2
            high26 = df['High'].rolling(window=26).max(); low26 = df['Low'].rolling(window=26).min()
            df['kijun'] = (high26 + low26) / 2
            df['span_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(26)
            high52 = df['High'].rolling(window=52).max(); low52 = df['Low'].rolling(window=52).min()
            df['span_b'] = ((high52 + low52) / 2).shift(26)

            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
            fig.add_trace(go.Scatter(x=df.index, y=df['span_a'], line=dict(color='rgba(255, 0, 255, 0.4)'), name='Span A'))
            fig.add_trace(go.Scatter(x=df.index, y=df['span_b'], fill='tonexty', line=dict(color='rgba(0, 255, 255, 0.2)'), name='Kumo'))
            fig.update_layout(template="plotly_dark", title=f"{ticker} Cloud Analysis", height=500)
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.error("銘柄データが取れなかったぬ...💦")
