import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・漆黒ネオンで統一） ---
st.set_page_config(page_title="BLACK'S GLOBAL MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; }
    h3 { color: #00ffff !important; }
    .stMetric { background-color: #111111; border: 1px solid #00ffff; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #ff00ff; }
    label { color: #00ffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. サイドバー設定 ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"]) # 市場を切り替えてもレイアウトは同じ

refresh_mode = st.sidebar.selectbox("自動更新", ["OFF", "5分", "10分"], index=0)
if "分" in refresh_mode:
    st_autorefresh(interval=int(refresh_mode.replace("分", "")) * 60 * 1000, key="refresh") # 自動更新機能

# --- 3. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"] # J-Quants用のトークン
except:
    st.error("🔑 秘密の金庫に鍵がないよ！")
    st.stop()

# --- 4. コピー用JavaScript関数の埋め込み ---
def copy_button(text):
    # ボタンを押すとクリップボードにコピーされる魔法
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

# --- 5. データ取得エンジン ---
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
            df['空売り比率(%)'] = pd.to_numeric(df['空売り比率(%)'])
            return df
    except: return None

def get_us_ranking():
    # 米国株の監視リスト
    watch_list = ["TSLA", "NVDA", "AAPL", "AMZN", "META", "GOOGL", "MSFT", "AMD", "NFLX", "GME", "AMC", "PLTR", "COIN", "MARA", "RIOT"]
    data = []
    for ticker in watch_list:
        try:
            t = yf.Ticker(ticker)
            short = t.info.get('shortPercentOfFloat', 0) * 100
            data.append({"ティッカー": ticker, "空売り比率(%)": round(short, 2), "銘柄名": t.info.get('longName', ticker)})
        except: continue
    return pd.DataFrame(data)

# --- 6. メイン表示エリア（日米共通レイアウト） ---
st.title(f"🕶️ {market_type} MONITOR")

if market_type == "日本株 (JPN)":
    # --- 日本株セクション ---
    df_jp = get_jp_data()
    if df_jp is not None:
        st.subheader("🏆 空売り比率 TOP30")
        top_30_jp = df_jp.sort_values(by='空売り比率(%)', ascending=False).head(30) # ランキング表示
        st.dataframe(top_30_jp, use_container_width=True)
        
        st.markdown("---")
        search_jp = st.text_input("🔍 銘柄コード4桁で検索", "7203") # 検索窓
        if search_jp:
            target = df_jp[df_jp['コード'].str.contains(search_jp)].copy()
            if not target.empty:
                st.metric("💀 空売り比率", f"{target.iloc[0]['空売り比率(%)']}%")
                copy_button(search_jp) # ワンタップコピー
                st.line_chart(yf.Ticker(f"{search_jp}.T").history(period="1mo")['Close'])
else:
    # --- 米国株セクション ---
    with st.spinner('NY市場をハック中...🗽'):
        df_us = get_us_ranking()
    if not df_us.empty:
        st.subheader("🇺🇸 監視ランキング")
        top_us = df_us.sort_values(by='空売り比率(%)', ascending=False) # ランキング表示
        st.dataframe(top_us, use_container_width=True)
        
        st.markdown("---")
        search_us = st.text_input("🔍 ティッカーで検索", "TSLA").upper() # 検索窓
        if search_us:
            t = yf.Ticker(search_us)
            short_val = t.info.get('shortPercentOfFloat', 0) * 100
            st.metric(f"🔥 {search_us} 空売り比率", f"{short_val:.2f}%")
            copy_button(search_us) # ワンタップコピー
            st.line_chart(t.history(period="1mo")['Close'])

st.caption("Produced by Maria & BLACK")
