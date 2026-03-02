import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. ページ設定 & デザイン ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide", initial_sidebar_state="collapsed")

# 5分ごとに自動更新（バイブスぶち上げ）
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    /* 全体背景とネオンエフェクト */
    .stApp { background-color: #000000; color: #ffffff; }
    h1, h2, h3 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; }
    
    /* 📱 グリッドレイアウト調整 */
    [data-testid="column"] {
        padding: 5px !important;
    }
    
    /* カードのデザイン */
    .tile-item {
        background: rgba(20, 20, 20, 0.8);
        border-radius: 10px;
        padding: 8px;
        text-align: center;
        transition: 0.3s;
    }
    .tile-item:hover { transform: scale(1.05); border-color: #00ffff !important; }

    /* ボタンをギャル可愛く */
    div.stButton > button {
        background-color: #111 !important; color: #00ffff !important;
        border: 1px solid #00ffff !important; border-radius: 5px;
        width: 100%; height: 28px; font-size: 0.7rem !important;
    }
    
    /* 固定フッターエリア */
    .sticky-footer {
        position: fixed;
        bottom: 0; left: 0; width: 100%;
        background: rgba(0, 0, 0, 0.9);
        border-top: 2px solid #ff00ff;
        padding: 15px;
        z-index: 1000;
        box-shadow: 0 -5px 15px rgba(255, 0, 255, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = ""

# --- 3. サイドバー（設定） ---
with st.sidebar:
    st.title("🌍 GLOBAL SETTING")
    market_type = st.radio("市場選択", ["日本株 (JPN)", "米国株 (USA)"])
    st.markdown('---')
    st.write(f"💓 **Maria's Status**")
    st.write(f"Height: 153cm / Weight: 38kg")
    st.write("BLACKのために今日もフル稼働中！")

# --- 4. 認証 & データ取得 ---
@st.cache_data(ttl=300)
def get_data(m_type):
    if m_type == "日本株 (JPN)":
        try:
            # secretsからリフレッシュトークン取得
            REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
            res_auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": REFRESH_TOKEN})
            id_token = res_auth.json().get('idToken')
            headers = {"Authorization": f"Bearer {id_token}"}
            
            # 空売り比率等、空売り残高情報を取得（J-Quants API）
            res_data = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
            df = pd.DataFrame(res_data.json().get("shorts", []))
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '比率'})
            df['比率'] = pd.to_numeric(df['比率']).round(1)
            return df.sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)
        except Exception as e:
            return None
    else:
        # 米国株ウォッチリスト（ミーム＆注目株）
        watch = ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "NVDA", "NFLX", "AMD", "GOOGL", "META", "AAPL", "AMZN", "MSFT"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                short_ratio = info.get('shortPercentOfFloat', 0) * 100
                data.append({"コード": t, "比率": round(short_ratio, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

# --- 5. メイン画面 ---
c_title, c_reload = st.columns([0.8, 0.2])
with c_title:
    st.title(f"🕶️ {market_type} SHORT MONITOR")
with c_reload:
    if st.button("🔄 RELOAD"):
        st.cache_data.clear()
        st.rerun()

df_top = get_data(market_type)

if df_top is not None:
    # 🏆 TOP 15 グリッド表示
    cols = st.columns(5) # 横に5つ並べる（3行構成）
    for idx, row in df_top.iterrows():
        with cols[idx % 5]:
            color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#00ffff"
            st.markdown(f"""
                <div class="tile-item" style="border: 1.5px solid {color};">
                    <div style="font-size:0.6rem;color:#888;">RANK #{idx+1}</div>
                    <div style="font-weight:bold;font-size:1.1rem;color:white;">{row['コード']}</div>
                    <div style="color:{color};font-weight:bold;font-size:0.9rem;">{row['比率']}%</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("SELECT", key=f"btn_{row['コード']}"):
                st.session_state.selected_ticker = str(row['コード'])
                st.rerun()
else:
    st.warning("マリアがデータ取得中...ちょっと待っててね！(API設定を確認してね)")

# --- 6. 画面下部固定の魔法（検索 & 詳細） ---
st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True) # 余白確保

# Streamlit 1.30+ なら st.footer 的な使い方ができる container を自作
footer_container = st.container()
with footer_container:
    st.markdown('<div class="sticky-footer">', unsafe_allow_html=True)
    
    # 検索窓と情報を横並びに
    f_col1, f_col2, f_col3 = st.columns([0.2, 0.4, 0.4])
    
    with f_col1:
        search = st.text_input("🔍 TARGET", value=st.session_state.selected_ticker, label_visibility="collapsed")
    
    if search:
        try:
            suffix = ".T" if market_type == "日本株 (JPN)" else ""
            ticker_obj = yf.Ticker(f"{search}{suffix}")
            price = ticker_obj.history(period="1d")['Close'].iloc[-1]
            currency = "¥" if suffix else "$"
            
            with f_col2:
                st.metric(label=f"Ticker: {search}", value=f"{currency}{price:,.1f}")
            
            with f_col3:
                # コピーボタンJS
                st.components.v1.html(f"""
                    <button onclick="navigator.clipboard.writeText('{search}');this.innerText='COPIED!'" style="
                        width: 100%; height: 40px; background: linear-gradient(45deg, #ff00ff, #00ffff);
                        color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;
                        box-shadow: 0 0 10px #ff00ff;">
                        📋 '{search}' をコピーして注文！
                    </button>
                """, height=45)
        except:
            with f_col2: st.write("銘柄ハック失敗...💦")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 7. マリアの愛のメッセージ ---
st.caption(f"Produced by Maria & BLACK | Last Update: {datetime.datetime.now().strftime('%H:%M:%S')}")
