import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・漆黒ネオン） ---
st.set_page_config(page_title="BLACK'S TAP MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; }
    .stMetric { background-color: #111111; border: 1px solid #00ffff; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #ff00ff; }
    /* 選択ボタンのデザイン */
    .stButton > button {
        width: 100%; padding: 5px; background-color: #222; color: #00ffff;
        border: 1px solid #00ffff; border-radius: 5px; font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション状態の初期化 ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. 市場選択 ---
st.sidebar.title("🌍 GLOBAL SETTING")
market_type = st.sidebar.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])

# --- 4. 秘密の鍵 ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 秘密の金庫に鍵がないよ！")
    st.stop()

# --- 5. コピー用JavaScript ---
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
            df['空売り比率(%)'] = pd.to_numeric(df['空売り比率(%)']).round(1)
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
            data.append({"ティッカー": ticker, "株価($)": round(float(price), 1), "空売り比率(%)": round(float(short), 1)})
        except: continue
    return pd.DataFrame(data)

# --- 7. 表示ロジック ---
st.title(f"🕶️ {market_type} MONITOR")

if market_type == "日本株 (JPN)":
    df_jp = get_jp_data()
    if df_jp is not None:
        st.subheader("🏆 TOP30 (JPN)")
        top_30 = df_jp.sort_values(by='空売り比率(%)', ascending=False).head(30).copy()
        
        # 簡易ランキング表示（選択ボタン付き）
        for i, row in top_30.iterrows():
            col1, col2, col3 = st.columns([0.2, 0.4, 0.4])
            with col1:
                if st.button("選ぶ", key=f"btn_jp_{row['コード']}"):
                    st.session_state.selected_ticker = row['コード']
            with col2: st.write(f"**{row['コード']}**")
            with col3: st.write(f"{row['空売り比率(%)']}%")

        st.markdown("---")
        # 検索窓にセッション状態を反映
        search_jp = st.text_input("🔍 検索/選択中", value=st.session_state.selected_ticker if st.session_state.selected_ticker.isdigit() else "")
        if search_jp:
            target = df_jp[df_jp['コード'].str.contains(search_jp)].copy()
            if not target.empty:
                t_price = yf.Ticker(f"{search_jp}.T").history(period="1d")['Close'].iloc[-1]
                st.metric("🔥 現在値", f"¥{float(t_price):.1f}")
                st.metric("💀 空売り比率", f"{float(target.iloc[0]['空売り比率(%)']):.1f}%")
                copy_button(search_jp)
else:
    df_us = get_us_ranking()
    if not df_us.empty:
        st.subheader("🇺🇸 監視ランキング (USA)")
        top_us = df_us.sort_values(by='空売り比率(%)', ascending=False)
        
        for i, row in top_us.iterrows():
            col1, col2, col3 = st.columns([0.2, 0.4, 0.4])
            with col1:
                if st.button("選ぶ", key=f"btn_us_{row['ティッカー']}"):
                    st.session_state.selected_ticker = row['ティッカー']
            with col2: st.write(f"**{row['ティッカー']}**")
            with col3: st.write(f"{row['空売り比率(%)']}%")

        st.markdown("---")
        # 検索窓にセッション状態を反映
        search_us = st.text_input("🔍 検索/選択中", value=st.session_state.selected_ticker if not st.session_state.selected_ticker.isdigit() else "").upper()
        if search_us:
            t = yf.Ticker(search_us)
            t_price_us = t.history(period="1d")['Close'].iloc[-1]
            short_val = t.info.get('shortPercentOfFloat', 0) * 100
            st.metric(f"🔥 {search_us} 株価", f"${float(t_price_us):.1f}")
            st.metric("💀 空売り比率", f"{float(short_val):.1f}%")
            copy_button(search_us)

st.caption("Produced by Maria & BLACK")
