import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・漆黒ネオン） ---
st.set_page_config(page_title="BLACK'S RANKING MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; }
    .stMetric { background-color: #111111; border: 1px solid #00ffff; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #ff00ff; }
    /* テーブルの見た目もハック */
    .stDataFrame { border: 1px solid #ff00ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. サイドバー設定 ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])

refresh_mode = st.sidebar.selectbox("自動更新", ["OFF", "5分", "10分"], index=0)
if "分" in refresh_mode:
    st_autorefresh(interval=int(refresh_mode.replace("分", "")) * 60 * 1000, key="refresh")

# --- 3. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 秘密の金庫に鍵がないよ！")
    st.stop()

# --- 4. データ取得エンジン ---
def get_jp_data():
    try:
        auth_url = "https://api.jquants.com/v1/token/auth_refresh"
        res_auth = requests.post(auth_url, json={"refreshToken": REFRESH_TOKEN})
        token = res_auth.json().get("idToken")
        headers = {"Authorization": f"Bearer {token}"}
        res_data = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
        if res_data.status_code == 200:
            df = pd.DataFrame(res_data.json().get("shorts", []))
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '空売り比率(%)', 'Date': '日付'})
            df['空売り比率(%)'] = pd.to_numeric(df['空売り比率(%)'])
            return df
        return None
    except: return None

def highlight_risky(row):
    # 20%以上はネオンピンク、15%以上はイエロー
    val = float(row['空売り比率(%)'])
    if val >= 20.0: return ['background-color: #ff00ff; color: #ffffff; font-weight: bold'] * len(row)
    elif val >= 15.0: return ['background-color: #ffff00; color: #000000;'] * len(row)
    return [''] * len(row)

# --- 5. メイン表示 ---
st.title(f"🕶️ {market_type} MONITOR")

if market_type == "日本株 (JPN)":
    df_jp = get_jp_data()
    
    if df_jp is not None and not df_jp.empty:
        # 🔥 空売り比率 TOP30 リスト表示
        st.subheader("🏆 空売り比率ランキング TOP30")
        top_30 = df_jp.sort_values(by='空売り比率(%)', ascending=False).head(30)
        st.dataframe(top_30.style.apply(highlight_risky, axis=1), use_container_width=True)
        
        st.write("---")
        
        # 個別検索機能
        search_jp = st.text_input("銘柄コードで詳細をハック...", "7203")
        if search_jp:
            target = df_jp[df_jp['コード'].str.contains(search_jp)].copy()
            if not target.empty:
                st.metric("💀 ターゲットの空売り比率", f"{target.iloc[0]['空売り比率(%)']}%")
                st.line_chart(yf.Ticker(f"{search_jp}.T").history(period="1mo")['Close'])
    else:
        st.info("今はデータがないみたい。月曜日の夕方を待とう！")

else:
    # 米国株は yfinance で一括ランキング取得が難しいため、BLACKの注目銘柄を並べる形式がおすすめ
    st.info("米国株は個別ティッカー（TSLA等）を入力してチェックしてね！")
    search_us = st.text_input("ティッカー入力", "TSLA").upper()
    if search_us:
        t = yf.Ticker(search_us)
        short = t.info.get('shortPercentOfFloat', 0) * 100
        st.metric(f"🔥 {search_us} 空売り比率", f"{short:.2f}%")
        st.line_chart(t.history(period="1mo")['Close'])

st.caption("Produced by Maria & BLACK")
