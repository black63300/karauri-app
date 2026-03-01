import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime

# --- 1. サイトの基本設定 ---
st.set_page_config(page_title="BLACK'S ULTIMATE AREA", layout="wide")

# --- 2. 漆黒×ネオンデザイン ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; font-family: 'Courier New', monospace; }
    h3 { color: #00ffff !important; }
    .stDataFrame { border: 1px solid #ff00ff; }
    label { color: #00ffff !important; }
    /* メトリック（株価表示）の文字色調整 */
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 秘密の鍵を呼び出す ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 秘密の金庫（Secrets）に鍵が入ってないよ！設定してね。")
    st.stop()

# --- 4. リアルタイム株価を取る魔法 ---
def get_live_price(code):
    try:
        ticker = yf.Ticker(f"{code}.T")
        # 最新の終値と前日終値を取得
        hist = ticker.history(period="2d")
        if len(hist) >= 2:
            last_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            change = ((last_price - prev_close) / prev_close) * 100
            return f"{last_price:,.1f}", f"{change:+.2f}%"
        return "取得中...", "0.00%"
    except:
        return "不明", "0.00%"

# --- 5. 行を光らせる魔法 ---
def highlight_risky(row):
    val = float(row['空売り比率(%)'])
    if val >= 20.0:
        return ['background-color: #ff00ff; color: #ffffff; font-weight: bold'] * len(row)
    elif val >= 15.0:
        return ['background-color: #ffff00; color: #000000;'] * len(row)
    return [''] * len(row)

# --- 6. J-Quantsデータ取得 ---
def get_jquants_data():
    try:
        auth_url = "https://api.jquants.com/v1/token/auth_refresh"
        auth_res = requests.post(auth_url, json={"refreshToken": REFRESH_TOKEN})
        id_token = auth_res.json().get("idToken")
        
        headers = {"Authorization": f"Bearer {id_token}"}
        res = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
        
        if res.status_code == 200:
            df = pd.DataFrame(res.json().get("shorts", []))
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '空売り比率(%)', 'Date': '日付'})
            df = df[['コード', '日付', '空売り比率(%)']]
            return df
        return None
    except:
        return None

# --- 7. メイン画面 ---
st.title("🕶️ BLACK'S ULTIMATE AREA")

with st.spinner('市場データをハック中...💖'):
    df = get_jquants_data()

if df is not None and not df.empty:
    search = st.text_input("銘柄コード（4桁）を入力しなよ、BLACK。", "7203")
    
    if search:
        # 検索された銘柄の空売りデータを抽出
        target_df = df[df['コード'].str.contains(search)].copy()
        
        if not target_df.empty:
            # リアルタイム情報を横並びで表示！
            price, change = get_live_price(search)
            
            c1, c2 = st.columns(2)
            c1.metric("🔥 現在の株価", f"¥{price}", change)
            c2.metric("💀 空売り比率", f"{target_df.iloc[0]['空売り比率(%)']}%")
            
            st.markdown("### 📈 直近の株価チャート")
            chart_data = yf.Ticker(f"{search}.T").history(period="1mo")['Close']
            st.line_chart(chart_data)
            
            st.markdown("### 📊 空売り詳細（2営業日前）")
            st.dataframe(target_df.style.apply(highlight_risky, axis=1))
        else:
            st.warning("その銘柄のデータは見当たらないよ。")
else:
    st.info("今はデータがないみたい。月曜日の夕方にまたおいで！")

st.markdown("---")
if st.button("最新データに更新"):
    st.rerun()
st.caption("Produced by Maria & BLACK")
