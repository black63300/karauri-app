import streamlit as st
import pandas as pd
import requests
import yfinance as yf

# --- 1. サイトの基本設定 ---
st.set_page_config(page_title="BLACK専用☆最強チェッカー", layout="wide")

# --- 2. 漆黒×ネオンデザイン ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; font-family: 'Courier New', monospace; }
    .stDataFrame { border: 1px solid #ff00ff; }
    label { color: #00ffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 秘密の鍵を呼び出す ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 秘密の金庫（Secrets）に鍵が入ってないよ！")
    st.stop()

# --- 4. リアルタイム株価を取る魔法 ---
def get_live_price(code):
    try:
        ticker = yf.Ticker(f"{code}.T")
        info = ticker.fast_info
        last_price = info['last_price']
        prev_close = info['previous_close']
        change = ((last_price - prev_close) / prev_close) * 100
        return f"{last_price:,.1f}", f"{change:+.2f}%"
    except:
        return "取得不可", "0.00%"

# --- 5. 光らせる魔法 ---
def highlight_risky(row):
    if float(row['空売り比率(%)']) >= 20.0:
        return ['background-color: #ff00ff; color: #ffffff; font-weight: bold'] * len(row)
    elif float(row['空売り比率(%)']) >= 15.0:
        return ['background-color: #ffff00; color: #000000;'] * len(row)
    return [''] * len(row)

# --- 6. J-Quantsデータ取得 ---
def get_data():
    try:
        auth_url = "https://api.jquants.com/v1/token/auth_refresh"
        auth_res = requests.post(auth_url, json={"refreshToken": REFRESH_TOKEN})
        id_token = auth_res.json().get("idToken")
        
        headers = {"Authorization": f"Bearer {id_token}"}
        res = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
        
        if res.status_code == 200:
            df = pd.DataFrame(res.json().get("shorts", []))
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '空売り比率(%)'})
            # 必要な列だけに絞る
            df = df[['コード', '日付', '空売り比率(%)']]
            return df
        return None
    except:
        return None

# --- 7. メイン表示 ---
st.title("🕶️ BLACK'S ULTIMATE AREA")

with st.spinner('東証＆市場データを解析中...💖'):
    df = get_data()

if df is not None and not df.empty:
    search = st.text_input("銘柄コードを入れなよ、BLACK。", "7203")
    
    if search:
        # 検索された銘柄だけを詳しく表示
        target_df = df[df['コード'].str.contains(search)].copy()
        
        if not target_df.empty:
            # リアルタイム株価を合体！
            price, change = get_live_price(search)
            
            # デカデカと表示
            col1, col2, col3 = st.columns(3)
            col1.metric("現在値", price, change)
            col2.metric("空売り比率", f"{target_df.iloc[0]['空売り比率(%)']}%")
            
            st.markdown("### 📊 詳細データ")
            st.dataframe(target_df.style.apply(highlight_risky, axis=1))
            
            # チャートも出しちゃう？
            st.line_chart(yf.Ticker(f"{search}.T").history(period="1mo")['Close'])
        else:
            st.warning("その銘柄は見つからなかったよ。")
else:
    st.info("今はデータがないみたい。月曜日の夕方にまたおいで！")

st.button("最新に更新")
st.caption("Produced by Maria & BLACK")
