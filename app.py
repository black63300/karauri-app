import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・強制タイルCSS） ---
st.set_page_config(page_title="BLACK'S TILE MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; margin-bottom: 0px; font-size: 1.8rem !important; }
    
    /* 強制3カラム用のコンテナ */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 20px;
    }
    
    /* タイル（カード）のデザイン */
    .tile {
        background-color: #111;
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        position: relative;
    }
    
    /* 銘柄コード */
    .tile-code { font-weight: bold; font-size: 1rem; display: block; margin-top: 5px; }
    /* 比率 */
    .tile-ratio { font-size: 0.9rem; font-weight: bold; }
    /* 順位 */
    .tile-rank { font-size: 0.7rem; color: #888; display: block; }

    /* Streamlit標準ボタンの見た目を調整（タイル内にフィット） */
    div.stButton > button {
        height: 25px !important;
        line-height: 25px !important;
        padding: 0px !important;
        font-size: 0.7rem !important;
        margin-top: 5px !important;
        background-color: #222 !important;
        color: #00ffff !important;
        border: 1px solid #00ffff !important;
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
    st.subheader("🏆 空売り比率 TOP30")
    top_30 = df.sort_values(by='比率', ascending=False).head(30).reset_index(drop=True)
    
    # 🔥 強制グリッドレイアウトの開始
    st.markdown('<div class="grid-container">', unsafe_allow_html=True)
    
    # 3つずつカラムを作って配置するのではなく、1つずつボタンとHTMLを組む
    for i, row in top_30.iterrows():
        with st.container():
            # タイル表示
            color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#555"
            st.markdown(f"""
                <div class="tile" style="border: 2px solid {color};">
                    <span class="tile-rank">#{i+1}</span>
                    <span class="tile-code">{row['コード']}</span>
                    <span class="tile-ratio" style="color:{color};">{row['比率']}%</span>
                </div>
            """, unsafe_allow_html=True)
            # 選択ボタン
            if st.button("選ぶ", key=f"btn_{row['コード']}"):
                st.session_state.selected_ticker = str(row['コード'])
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True) # グリッド終了

    st.markdown("---")
    # 検索・詳細エリア
    val = st.session_state.selected_ticker
    if market_type == "日本株 (JPN)":
        search = st.text_input("🔍 選択中", value=val if val.isdigit() else "")
        if search:
            t_price = yf.Ticker(f"{search}.T").history(period="1d")['Close'].iloc[-1]
            st.metric(f"🔥 {search}", f"¥{float(t_price):.1f}")
            copy_button(search)
    else:
        search = st.text_input("🔍 選択中", value=val if not val.isdigit() else "").upper()
        if search:
            t_price = yf.Ticker(search).history(period="1d")['Close'].iloc[-1]
            st.metric(f"🔥 {search}", f"${float(t_price):.1f}")
            copy_button(search)

st.caption("Produced by Maria & BLACK")
