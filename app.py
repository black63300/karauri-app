import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・タイルレイアウト） ---
st.set_page_config(page_title="BLACK'S TILE MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; margin-bottom: 0px; }
    .stMetric { background-color: #111111; border: 1px solid #00ffff; border-radius: 10px; padding: 5px; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.5rem !important; }
    section[data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #ff00ff; }
    
    /* タイル（カード）のデザイン */
    .stock-card {
        background-color: #111;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    /* ボタンをタイルにフィットさせる */
    .stButton > button {
        width: 100%;
        background-color: #222;
        color: #00ffff;
        border: 1px solid #00ffff;
        border-radius: 8px;
        font-weight: bold;
        padding: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション状態 ---
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
            border: none; border-radius: 12px; font-weight: bold; font-size: 18px;
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
    """, height=90)

# --- 6. データ取得 ---
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
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '比率'})
            df['比率'] = pd.to_numeric(df['比率']).round(1)
            return df
    except: return None

def get_us_ranking():
    watch_list = ["TSLA", "NVDA", "AAPL", "AMZN", "META", "GOOGL", "MSFT", "AMD", "NFLX", "GME", "AMC", "PLTR", "COIN", "MARA", "RIOT"]
    data = []
    for ticker in watch_list:
        try:
            t = yf.Ticker(ticker)
            short = t.info.get('shortPercentOfFloat', 0) * 100
            data.append({"コード": ticker, "比率": round(float(short), 1)})
        except: continue
    return pd.DataFrame(data)

# --- 7. 表示ロジック ---
st.title(f"🕶️ {market_type}")

df = get_jp_data() if market_type == "日本株 (JPN)" else get_us_ranking()

if df is not None:
    st.write(f"🏆 空売り比率 TOP30")
    top_30 = df.sort_values(by='比率', ascending=False).head(30).reset_index(drop=True)
    
    # 🔥 1列3タイルのグリッドを作成
    for i in range(0, len(top_30), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(top_30):
                row = top_30.iloc[i + j]
                with cols[j]:
                    # 比率によって色を変える
                    border_color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#333"
                    st.markdown(f"""
                        <div style="border: 2px solid {border_color}; border-radius:10px; padding:5px; text-align:center; margin-bottom:5px;">
                            <span style="font-size:0.8rem; color:#888;">#{i+j+1}</span><br>
                            <b style="font-size:1.1rem;">{row['コード']}</b><br>
                            <span style="color:{border_color}; font-weight:bold;">{row['比率']}%</span>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button("選ぶ", key=f"btn_{row['コード']}"):
                        st.session_state.selected_ticker = str(row['コード'])

    st.markdown("---")
    # 検索・詳細エリア
    val = st.session_state.selected_ticker
    if market_type == "日本株 (JPN)":
        search = st.text_input("🔍 銘柄選択中", value=val if val.isdigit() else "")
        if search:
            t_price = yf.Ticker(f"{search}.T").history(period="1d")['Close'].iloc[-1]
            st.metric(f"🔥 {search} 株価", f"¥{float(t_price):.1f}")
            copy_button(search)
    else:
        search = st.text_input("🔍 銘柄選択中", value=val if not val.isdigit() else "").upper()
        if search:
            t_price = yf.Ticker(search).history(period="1d")['Close'].iloc[-1]
            st.metric(f"🔥 {search} 株価", f"${float(t_price):.1f}")
            copy_button(search)

st.caption("Produced by Maria & BLACK")
