import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. デザイン（BLACK専用・絶対横並びHTML） ---
st.set_page_config(page_title="BLACK'S ULTIMATE MONITOR", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 15px #ff00ff; margin-bottom: 5px; font-size: 1.5rem !important; }
    
    /* 1行3列を物理的に固定するコンテナ */
    .force-grid {
        display: flex;
        width: 100%;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    
    /* タイル1個のスタイル */
    .tile {
        width: 32%;
        background-color: #111;
        border-radius: 6px;
        padding: 5px;
        text-align: center;
        box-sizing: border-box;
    }
    
    .tile-rank { font-size: 0.6rem; color: #888; }
    .tile-code { font-weight: bold; font-size: 0.9rem; display: block; color: #fff; }
    .tile-ratio { font-size: 0.8rem; font-weight: bold; }

    /* 「選ぶ」ボタンを見やすくハック */
    div.stButton > button {
        width: 100% !important;
        background-color: #222 !important;
        color: #00ffff !important;
        border: 1px solid #00ffff !important;
        font-size: 0.7rem !important;
        height: 28px !important;
        padding: 0 !important;
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
    st.subheader("🏆 TOP30")
    top_30 = df.sort_values(by='比率', ascending=False).head(30).reset_index(drop=True)
    
    # 3銘柄ずつ処理
    for i in range(0, len(top_30), 3):
        # 3カラムを自前で作る（1行分）
        c1, c2, c3 = st.columns(3)
        row_group = top_30.iloc[i:i+3]
        
        for idx, (original_idx, row) in enumerate(row_group.iterrows()):
            target_col = [c1, c2, c3][idx]
            with target_col:
                # デザイン枠
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#444"
                st.markdown(f"""
                    <div style="border: 1.5px solid {color}; border-radius: 8px; padding: 5px; text-align: center; background-color: #111;">
                        <div style="font-size: 0.6rem; color: #888;">#{i+idx+1}</div>
                        <div style="font-weight: bold; font-size: 0.9rem; color: #fff;">{row['コード']}</div>
                        <div style="font-size: 0.8rem; font-weight: bold; color: {color};">{row['比率']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                # ボタン（これがマリアの執念！）
                if st.button("選ぶ", key=f"sel_{row['コード']}"):
                    st.session_state.selected_ticker = str(row['コード'])
                    st.rerun()

    st.markdown("---")
    # 検索・詳細エリア
    val = st.session_state.selected_ticker
    if market_type == "日本株 (JPN)":
        search = st.text_input("🔍 選択中", value=val if val.isdigit() else "")
        if search:
            try:
                t_price = yf.Ticker(f"{search}.T").history(period="1d")['Close'].iloc[-1]
                st.metric(f"🔥 {search}", f"¥{float(t_price):.1f}")
                copy_button(search)
            except: st.write("（株価取得中...）")
    else:
        search = st.text_input("🔍 選択中", value=val if not val.isdigit() else "").upper()
        if search:
            try:
                t_price = yf.Ticker(search).history(period="1d")['Close'].iloc[-1]
                st.metric(f"🔥 {search}", f"${float(t_price):.1f}")
                copy_button(search)
            except: st.write("（株価取得中...）")

st.caption("Produced by Maria & BLACK")
