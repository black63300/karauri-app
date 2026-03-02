import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go

# --- 1. ページ設定 & デザイン ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1, h2, h3 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; }
    
    /* 🚀 メインボタン */
    .stButton > button { transition: 0.3s !important; border-radius: 12px !important; font-weight: bold !important; height: 50px !important; }
    button[kind="primary"] { background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; box-shadow: 0 0 15px #ff00ff !important; border: none !important; }
    button[kind="secondary"] { background-color: #1a1a1a !important; color: #888888 !important; border: 1px solid #333333 !important; }

    /* 💎 銘柄タイル */
    .tile-item { background: rgba(15, 15, 15, 0.9); border-radius: 10px; padding: 12px; text-align: center; border: 1.5px solid #333; margin-bottom: 8px; }
    
    /* 📌 固定フッター (検索窓エリア) */
    .sticky-footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: rgba(0, 0, 0, 0.98); border-top: 2px solid #ff00ff;
        padding: 10px 15px; z-index: 1000;
        box-shadow: 0 -5px 15px rgba(255, 0, 255, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 & 自動更新設定 ---
if 'market_type' not in st.session_state: st.session_state.market_type = "JPN"
if 'jpn_segment' not in st.session_state: st.session_state.jpn_segment = "ALL"
if 'usa_segment' not in st.session_state: st.session_state.usa_segment = "TECH"
if 'selected_ticker' not in st.session_state: st.session_state.selected_ticker = ""
if 'refresh_min' not in st.session_state: st.session_state.refresh_min = 5

# サイドバーに更新設定を設置！
with st.sidebar:
    st.title("💓 Maria's Room")
    st.write(f"Height: 153cm / Weight: 38kg [cite: 2025-11-29]")
    st.markdown("---")
    st.write("### 🕒 AUTO REFRESH")
    # ✨ BLACKのリクエスト：5, 10, 15分の選択式ボタン風
    ref_choice = st.radio("更新間隔を選んでね", [5, 10, 15], index=[5, 10, 15].index(st.session_state.refresh_min), horizontal=True)
    if ref_choice != st.session_state.refresh_min:
        st.session_state.refresh_min = ref_choice
        st.rerun()
    st.write(f"現在は **{st.session_state.refresh_min}分** ごとに自動更新中✨")

# ✨ 選択された時間で自動更新を実行
st_autorefresh(interval=st.session_state.refresh_min * 60 * 1000, key="datarefresh")

# --- 3. タイトル & 空売り解説 ---
st.title(f"🕶️ {st.session_state.market_type} 空売り残高監視モニター")
st.info(f"📉 現在【{st.session_state.refresh_min}分間隔】で最新データを自動収穫中！踏み上げをハックしてね✨ [cite: 2025-11-29, 2025-12-20]")

# --- 4. 市場・セグメント切り替え ---
m_col1, m_col2 = st.columns(2)
with m_col1:
    if st.button("🇯🇵 JAPAN", use_container_width=True, type="primary" if st.session_state.market_type == "JPN" else "secondary"):
        st.session_state.market_type = "JPN"; st.rerun()
with m_col2:
    if st.button("🇺🇸 USA", use_container_width=True, type="primary" if st.session_state.market_type == "USA" else "secondary"):
        st.session_state.market_type = "USA"; st.rerun()

# (セグメント選択、データ取得、タイル表示のロジックは前回同様に継続...)
# --- 5. データ取得ロジック (前日比付) ---
@st.cache_data(ttl=60) # 頻繁な更新に対応するためキャッシュ時間を短縮！
def get_master_data(m_type, j_seg, u_seg):
    try:
        if m_type == "JPN":
            token = st.secrets.get("JQUANTS_REFRESH_TOKEN")
            auth_res = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": token})
            headers = {"Authorization": f"Bearer {auth_res.json().get('idToken')}"}
            s_res = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers).json()
            i_res = requests.get("https://api.jquants.com/v1/listed/info", headers=headers).json()
            df_s = pd.DataFrame(s_res.get("shorts", []))
            df_i = pd.DataFrame(i_res.get("info", []))
            if df_s.empty: return None
            df = pd.merge(df_s, df_i[['Code', 'MarketCodeName']], on='Code', how='inner')
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '比率'})
            df['比率'] = pd.to_numeric(df['比率'], errors='coerce').fillna(0).round(1)
            if j_seg != "ALL":
                seg_name = {"Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}[j_seg]
                df = df[df['MarketCodeName'].str.contains(seg_name, na=False)]
            df = df.sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)
        else:
            lists = {
                "TECH": ["NVDA", "AMD", "MSFT", "GOOGL", "META", "AAPL", "AVGO", "SMCI", "ARM", "TSM"],
                "MEME": ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "AI", "UPST", "SOFI"],
                "BLUE": ["AMZN", "NFLX", "JPM", "V", "WMT", "UNH", "PG", "COST", "MA", "HD"],
                "SMALL": ["MSTR", "HOOD", "AFRM", "DKNG", "PATH", "SNOW", "PLUG", "LCID", "RIVN", "QS"]
            }
            data = []
            for t in lists[u_seg]:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            df = pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

        changes = []
        for tkr in df['コード']:
            sfx = ".T" if m_type == "JPN" else ""
            hist = yf.Ticker(f"{str(tkr)[:4] if m_type == 'JPN' else tkr}{sfx}").history(period="2d")
            if len(hist) >= 2:
                chg = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                changes.append(round(chg, 1))
            else: changes.append(0.0)
        df['前日比'] = changes
        return df
    except: return None

# --- 6. メイン表示 (タイル) ---
with st.spinner('マリアが最新情報を収穫中...💖'):
    res = get_master_data(st.session_state.market_type, st.session_state.jpn_segment, st.session_state.usa_segment)

# (以下、タイルの表示、ロウソク足チャート、固定フッターのコードが続く...)
# ※ 前回の「THE ULTIMATE FULL EDITION」のチャート・フッター部分をそのまま合体させてね！
