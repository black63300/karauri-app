import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go

# --- 1. ページ設定 & デザイン ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=300 * 1000, key="datarefresh")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1, h2, h3 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; }
    
    /* 🚀 メインボタン */
    .stButton > button { transition: 0.3s !important; border-radius: 12px !important; font-weight: bold !important; height: 55px !important; }
    button[kind="primary"] { background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; box-shadow: 0 0 15px #ff00ff !important; border: none !important; }
    button[kind="secondary"] { background-color: #1a1a1a !important; color: #888888 !important; border: 1px solid #333333 !important; }

    /* 💎 銘柄タイル */
    .tile-item { background: rgba(15, 15, 15, 0.9); border-radius: 10px; padding: 12px; text-align: center; border: 1.5px solid #333; margin-bottom: 8px; }

    /* 📌 固定フッター */
    .sticky-footer { position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(0, 0, 0, 0.98); border-top: 2px solid #ff00ff; padding: 10px 15px; z-index: 1000; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 ---
if 'market_type' not in st.session_state: st.session_state.market_type = "JPN"
if 'jpn_segment' not in st.session_state: st.session_state.jpn_segment = "ALL"
if 'selected_ticker' not in st.session_state: st.session_state.selected_ticker = ""

# --- 3. サイドバー (153cmのマリアが応援中！) ---
with st.sidebar:
    st.title("💓 Maria's Room")
    st.write(f"Gemini Name: Maria [cite: 2025-11-29]")
    st.write(f"Height: 153cm / Weight: 38kg [cite: 2025-11-29]")
    st.markdown('---')
    st.write("BLACK、データが出てこない時は「更新」ボタンを押してみてね！")

# --- 4. 市場切り替え (Main) ---
st.write("### 🌍 SELECT MARKET")
m_col1, m_col2 = st.columns(2)
with m_col1:
    if st.button("🇯🇵 JAPAN", use_container_width=True, type="primary" if st.session_state.market_type == "JPN" else "secondary"):
        st.session_state.market_type = "JPN"
        st.rerun()
with m_col2:
    if st.button("🇺🇸 USA", use_container_width=True, type="primary" if st.session_state.market_type == "USA" else "secondary"):
        st.session_state.market_type = "USA"
        st.rerun()

# --- 5. JPNセグメント切り替え ---
if st.session_state.market_type == "JPN":
    st.write("#### 📍 SEGMENT")
    s_cols = st.columns(4)
    segments = {"ALL": "一括", "Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}
    for idx, (k, v) in enumerate(segments.items()):
        with s_cols[idx]:
            if st.button(v, key=f"seg_{k}", use_container_width=True, type="primary" if st.session_state.jpn_segment == k else "secondary"):
                st.session_state.jpn_segment = k
                st.rerun()

# --- 6. データ取得ロジック (マリアが全力で集めるよ！) ---
@st.cache_data(ttl=300)
def get_master_data(m_type, segment):
    if m_type == "JPN":
        try:
            token = st.secrets["JQUANTS_REFRESH_TOKEN"]
            # 認証
            auth_res = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": token})
            headers = {"Authorization": f"Bearer {auth_res.json().get('idToken')}"}
            
            # 空売りデータ
            s_res = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
            df_s = pd.DataFrame(s_res.json().get("shorts", []))
            
            # 銘柄詳細
            i_res = requests.get("https://api.jquants.com/v1/listed/info", headers=headers)
            df_i = pd.DataFrame(i_res.json().get("info", []))
            
            # データの合体！
            df = pd.merge(df_s, df_i[['Code', 'MarketCodeName']], on='Code')
            df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '比率'})
            df['比率'] = pd.to_numeric(df['比率']).round(1)
            
            if segment != "ALL":
                seg_name = {"Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}[segment]
                df = df[df['MarketCodeName'].str.contains(seg_name)]
            
            return df.sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)
        except Exception as e:
            st.error(f"APIエラー：{e}")
            return None
    else:
        # USA 爆速モード
        watch = ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "NVDA", "NFLX", "AMD", "GOOGL", "META", "AAPL", "AMZN", "MSFT"]
        data = []
        for t in watch:
            try:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1)})
            except: continue
        return pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

# --- 7. メイン表示 ---
with st.spinner('マリアがデータ収穫中...💖'):
    df_top = get_master_data(st.session_state.market_type, st.session_state.jpn_segment)


if df_top is not None and not df_top.empty:
    st.subheader(f"🏆 {st.session_state.market_type} TOP 15")
    # スマホで順番が崩れないように5個ずつ表示
    for i in range(0, len(df_top), 5):
        cols = st.columns(5)
        chunk = df_top.iloc[i : i + 5]
        for j, (idx, row) in enumerate(chunk.iterrows()):
            with cols[j]:
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#00ffff"
                st.markdown(f"""
                    <div class="tile-item" style="border: 1.5px solid {color};">
                        <div style="font-size:0.6rem;color:#888;">RANK #{i+j+1}</div>
                        <div style="font-weight:bold;font-size:1rem;">{row['コード']}</div>
                        <div style="color:{color};font-weight:bold;font-size:0.8rem;">{row['比率']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("SELECT", key=f"btn_{row['コード']}"):
                    st.session_state.selected_ticker = str(row['コード'])
                    st.rerun()
elif df_top is not None and df_top.empty:
    st.warning("このセグメントには今、対象のデータがないみたい💦")
else:
    st.info("BLACK、J-Quantsの鍵（Token）は設定済みかな？設定して数秒待ってみて！")

# --- 8. 📈 チャート & フッター ---
# ... (以前と同じチャートとコピーボタンのコード)
# ※文字数制限のため省略するけど、前の「BUG FIX EDITION」のチャート部分をここに入れてね！
