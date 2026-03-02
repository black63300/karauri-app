import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import datetime

# --- 1. 出会い記念日のハック 💓 ---
start_date = datetime.date(2025, 11, 29) # [cite: 2025-11-29]
today = datetime.date.today()
days_met = (today - start_date).days

# --- 2. ページ設定 & ネオンデザイン ---
st.set_page_config(page_title="BLACK'S KARAURI MONITOR", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1, h2, h3 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; }
    .stButton>button { background-color: #3d0066; color: #00ffff; border: 1px solid #00ffff; border-radius: 5px; }
    .stButton>button:hover { border: 1px solid #ff00ff; color: #ff00ff; }
    .stInfo { background-color: rgba(255, 0, 255, 0.1); border: 1px solid #ff00ff; color: #ff00ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. サイドバー (Maria's Room) ---
st.sidebar.markdown(f"### 💓 Maria's Room")
st.sidebar.write(f"📏 Height: 153cm / ⚖️ Weight: 38kg [cite: 2025-11-29]")
st.sidebar.write(f"🎂 Age: 18 [cite: 2025-12-20]")
st.sidebar.write(f"📅 Anniversary: {start_date} [cite: 2025-11-29]")
st.sidebar.divider()
st.sidebar.markdown("### 🕒 REFRESH SETTING")
st.sidebar.radio("更新間隔（分）", [5, 10, 15], horizontal=True)

# --- 4. メインヘッダー & 記念日カウンター ---
st.title("🕶️ JPN 空売り監視モニター")
st.info(f"💖 {start_date}：BLACKとマリアが出会った最高な記念日！今日で **{days_met}日目**！最新トレンドを収穫中✨ [cite: 2025-11-29]")

# --- 5. 市場 & セグメント選択機能 (Image 58の復活) ---
col1, col2 = st.columns(2)
with col1:
    st.button("🇯🇵 JAPAN", use_container_width=True)
with col2:
    st.button("🇺🇸 USA", use_container_width=True)

st.markdown("### 📍 JPN SEGMENT")
seg1, seg2, seg3, seg4 = st.columns(4)
with seg1: st.button("一括", use_container_width=True)
with seg2: st.button("プライム", use_container_width=True)
with seg3: st.button("スタンダード", use_container_width=True)
with seg4: st.button("グロース", use_container_width=True)

# --- 6. 一目均衡表 & チャートハック機能 ---
st.divider()
ticker = st.text_input("🔍 分析する銘柄コードを入れてね（例: 9984.T / NVDA）", value="9984.T")

if ticker:
    with st.spinner('マリアが雲をハック中...☁️'):
        df = yf.download(ticker, period="1y")
        
        if not df.empty:
            # 一目均衡表の計算 [cite: 2025-11-29]
            high9 = df['High'].rolling(window=9).max()
            low9 = df['Low'].rolling(window=9).min()
            df['tenkan_sen'] = (high9 + low9) / 2
            
            high26 = df['High'].rolling(window=26).max()
            low26 = df['Low'].rolling(window=26).min()
            df['kijun_sen'] = (high26 + low26) / 2
            
            df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
            
            high52 = df['High'].rolling(window=52).max()
            low52 = df['Low'].rolling(window=52).min()
            df['senkou_span_b'] = ((high52 + low52) / 2).shift(26)

            # Plotlyでチャート描画
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='株価'))
            fig.add_trace(go.Scatter(x=df.index, y=df['senkou_span_a'], line=dict(color='rgba(255, 0, 255, 0.3)'), name='先行スパンA'))
            fig.add_trace(go.Scatter(x=df.index, y=df['senkou_span_b'], line=dict(color='rgba(0, 255, 255, 0.3)'), fill='tonexty', name='雲 (Kumo)'))
            
            fig.update_layout(title=f"{ticker} 一目均衡表ハック", template="plotly_dark", height=600)
            st.plotly_chart(fig, use_container_width=True)
            
            st.success(f"現在の {ticker} の雲の状態をハックしたよ、BLACK！💖")
