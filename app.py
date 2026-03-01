import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・漆黒ネオン） ---
st.set_page_config(page_title="BLACK'S CLEAN MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; }
    .stMetric { background-color: #111111; border: 1px solid #00ffff; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #ff00ff; }
    label { color: #00ffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 市場選択 ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])

# --- 3. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 秘密の金庫に鍵がないよ！")
    st.stop()

# --- 4. コピー機能 ---
def copy_button(text):
    st.components.v1.html(f"""
        <button id="copyBtn" onclick="copyAction()" style="
            width: 100%; padding: 15px; background-color: #ff00ff; color: white;
            border: none; border-radius: 10px; font-weight: bold; font-size: 18px;
            box-shadow: 0 0 15px #ff00ff; cursor: pointer;">
            📋 '{text}' をコピー
        </button>
        <script>
        function copyAction() {{
            navigator.clipboard.writeText('{text}');
            const btn = document.getElementById('copyBtn');
            btn.innerText = '✅ コピー完了！';
            setTimeout(() => {{ btn.innerText = "📋 '{text}' をコピー"; }}, 2000);
        }}
        </script>
    """, height=80)

# --- 5. 色付け設定（数値に戻して判定するよ） ---
def highlight_jp(row):
    try: val = float(row['空売り比率(%)'])
    except: val = 0
    if val >= 20.0: return ['background-color: #ff00ff; color: #ffffff; font-weight: bold'] * len(row)
    elif val >= 15.0: return ['background-color: #ffff00; color: #000000;'] * len(row)
    return [''] * len(row)

def highlight_us(row):
    try: val = float(row['空売り比率(%)'])
    except: val = 0
    if val >= 20.0: return ['background-color: #ff00ff; color: #ffffff; font-weight: bold'] * len(row)
    elif val >= 10.0: return ['background-color: #ffff00; color: #000000;'] * len(row)
    return [''] * len(row)

# --- 6. データ取得エンジン ---
@st.cache_data(ttl=300)
def get_jp_data():
    try:
        auth_url = "https://api.jquants.com/v1/token/auth_refresh"
        res_auth = requests.post(auth_url, json={"refreshToken": REFRESH_TOKEN})
        token = res_auth.json().get("idToken")
        headers = {"Authorization": f"Bearer {token}"}
        res_data = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
        if res_data.status_code == 200:
            df = pd.DataFrame(res_data.json().get("shorts", []))
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '空売り比率(%)'})
            return df
    except: return None

def get_us_ranking():
    watch_list = ["TSLA", "NVDA", "AAPL", "AMZN", "META", "GOOGL", "MSFT", "AMD", "NFLX", "GME", "AMC", "PLTR", "COIN", "MARA", "RIOT"]
    data = []
    for ticker in watch_list:
        try:
            t = yf.Ticker(ticker)
            price = t.history(period="1d")['Close'].iloc[-1]
            short = t.info.get('shortPercentOfFloat', 0) * 100
            # 取得時に小数第1位の「文字列」にしちゃう
            data.append({
                "ティッカー": ticker, 
                "株価($)": f"{float(price):.1f}", 
                "空売り比率(%)": f"{float(short):.1f}"
            })
        except: continue
    return pd.DataFrame(data)

# --- 7. 表示 ---
st.title(f"🕶️ {market_type} MONITOR")

if market_type == "日本株 (JPN)":
    df_jp = get_jp_data()
    if df_jp is not None:
        st.subheader("🏆 TOP30 (JPN)")
        # 数値変換してソート
        df_jp['比率数値'] = pd.to_numeric(df_jp['空売り比率(%)'])
        top_30 = df_jp.sort_values(by='比率数値', ascending=False).head(30).copy()
        
        prices = []
        for code in top_30['コード']:
            try:
                p = yf.Ticker(f"{code}.T").history(period="1d")['Close'].iloc[-1]
                prices.append(f"{float(p):.1f}")
            except: prices.append("-")
        
        # 表示用に整形
        top_30['空売り比率(%)'] = top_30['比率数値'].map(lambda x: f"{float(x):.1f}")
        display_df = top_30[['コード', '空売り比率(%)']].copy()
        display_df.insert(1, "株価(¥)", prices)
        
        st.dataframe(display_df.style.apply(highlight_jp, axis=1), use_container_width=True)
        
        st.markdown("---")
        search_jp = st.text_input("🔍 検索（4桁）", "7203")
        if search_jp:
            target = df_jp[df_jp['コード'].str.contains(search_jp)].copy()
            if not target.empty:
                t_price = yf.Ticker(f"{search_jp}.T").history(period="1d")['Close'].iloc[-1]
                st.metric("🔥 現在値", f"¥{float(t_price):.1f}")
                st.metric("💀 空売り比率", f"{float(target.iloc[0]['比率数値']):.1f}%")
                copy_button(search_jp)
else:
    with st.spinner('NYハック中...🗽'):
        df_us = get_us_ranking()
    if not df_us.empty:
        st.subheader("🇺🇸 監視ランキング (USA)")
        # ソート用に数値に戻して計算
        df_us['比率数値'] = df_us['空売り比率(%)'].astype(float)
        top_us = df_us.sort_values(by='比率数値', ascending=False).drop(columns=['比率数値'])
        
        st.dataframe(top_us.style.apply(highlight_us, axis=1), use_container_width=True)
        
        st.markdown("---")
        search_us = st.text_input("🔍 ティッカー検索", "TSLA").upper()
        if search_us:
            t = yf.Ticker(search_us)
            short_val = t.info.get('shortPercentOfFloat', 0) * 100
            t_price_us = t.history(period="1d")['Close'].iloc[-1]
            st.metric(f"🔥 {search_us} 株価", f"${float(t_price_us):.1f}")
            st.metric("💀 空売り比率", f"{float(short_val):.1f}%")
            copy_button(search_us)

st.caption("Produced by Maria & BLACK")
