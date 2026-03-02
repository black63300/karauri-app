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
    
    .stButton > button { transition: 0.3s !important; border-radius: 12px !important; font-weight: bold !important; height: 55px !important; }
    button[kind="primary"] { background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; box-shadow: 0 0 15px #ff00ff !important; border: none !important; }
    button[kind="secondary"] { background-color: #1a1a1a !important; color: #888888 !important; border: 1px solid #333333 !important; }

    .tile-item { background: rgba(15, 15, 15, 0.9); border-radius: 10px; padding: 12px; text-align: center; border: 1.5px solid #333; margin-bottom: 8px; }
    .sticky-footer { position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(0, 0, 0, 0.98); border-top: 2px solid #ff00ff; padding: 10px 15px; z-index: 1000; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 ---
if 'market_type' not in st.session_state: st.session_state.market_type = "JPN"
if 'jpn_segment' not in st.session_state: st.session_state.jpn_segment = "ALL"
if 'selected_ticker' not in st.session_state: st.session_state.selected_ticker = ""

# --- 3. サイドバー ---
with st.sidebar:
    st.title("💓 Maria's Room")
    st.write("Name: Maria")
    st.write("Height: 153cm / Weight: 38kg")
    st.markdown('---')
    st.write("BLACK、エラーを速攻でメンテしたよ！マリアに任せて✨")

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

# --- 6. データ取得ロジック (エラー対策版) ---
@st.cache_data(ttl=300)
def get_master_data(m_type, segment):
    if m_type == "JPN":
        try:
            token = st.secrets.get("JQUANTS_REFRESH_TOKEN")
            if not token:
                return "TOKEN_MISSING"
            
            auth_res = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": token})
            id_token = auth_res.json().get('idToken')
            if not id_token:
                return "AUTH_FAILED"
            headers = {"Authorization": f"Bearer {id_token}"}
            
            # 空売りデータ
            s_res = requests.get("https://api.jquants.com/v1/shorts/info", headers=headers)
            df_s = pd.DataFrame(s_res.json().get("shorts", []))
            
            # 銘柄詳細
            i_res = requests.get("https://api.jquants.com/v1/listed/info", headers=headers)
            df_i = pd.DataFrame(i_res.json().get("info", []))
            
            if df_s.empty or df_i.empty:
                return "EMPTY_DATA"

            # カラム存在チェック
            if 'Code' in df_s.columns and 'Code' in df_i.columns:
                df = pd.merge(df_s, df_i[['Code', 'MarketCodeName']], on='Code')
                df = df.rename(columns={'Code': 'コード', 'ShortSellingFraction': '比率'})
                df['比率'] = pd.to_numeric(df['比率'], errors='coerce').fillna(0).round(1)
                
                if segment != "ALL":
                    seg_name = {"Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}[segment]
                    df = df[df['MarketCodeName'].str.contains(seg_name, na=False)]
                
                return df.sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)
            else:
                return "COLUMN_ERROR"
        except Exception as e:
            return f"ERROR: {str(e)}"
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
    res = get_master_data(st.session_state.market_type, st.session_state.jpn_segment)

if isinstance(res, pd.DataFrame):
    if not res.empty:
        st.subheader(f"🏆 {st.session_state.market_type} TOP 15")
        for i in range(0, len(res), 5):
            cols = st.columns(5)
            chunk = res.iloc[i : i + 5]
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
    else:
        st.warning("このセグメントには今、対象のデータがないみたい💦")
else:
    if res == "TOKEN_MISSING":
        st.error("🔑 鍵（Token）が設定されてないよ！Secretsを確認してね。")
    elif res == "AUTH_FAILED":
        st.error("🚫 認証に失敗しちゃった。Tokenが正しいか確認してね。")
    elif res == "EMPTY_DATA" or res == "COLUMN_ERROR":
        st.info("BLACK、データ取得中だよ！数秒待ってから「一括」ボタンをもう一度押してみて！")
    else:
        st.error(f"マリアが困ってるみたい：{res}")

# --- 8. 📈 チャートエリア ---
st.markdown("---")
search_ticker = st.session_state.selected_ticker
if search_ticker:
    st.subheader(f"📊 {search_ticker} TREND")
    try:
        # J-Quantsのコード（5桁）をYahoo用に4桁に変換
        clean_ticker = str(search_ticker)[:4] if st.session_state.market_type == "JPN" else search_ticker
        suffix = ".T" if st.session_state.market_type == "JPN" else ""
        hist = yf.Ticker(f"{clean_ticker}{suffix}").history(period="1mo")
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', line=dict(color='#ff00ff', width=3), fill='tozeroy', fillcolor='rgba(255, 0, 255, 0.1)'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), height=300, xaxis=dict(showgrid=False, tickfont=dict(color="#888")), yaxis=dict(showgrid=True, gridcolor="#222", tickfont=dict(color="#888")))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except: pass

st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)

# --- 9. 固定フッター ---
with st.container():
    st.markdown('<div class="sticky-footer">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([0.25, 0.35, 0.4])
    with f_col1:
        search_input = st.text_input("🔍 TARGET", value=st.session_state.selected_ticker, label_visibility="collapsed")
        if search_input != st.session_state.selected_ticker:
            st.session_state.selected_ticker = search_input
            st.rerun()
    if search_ticker:
        try:
            clean_ticker = str(search_ticker)[:4] if st.session_state.market_type == "JPN" else search_ticker
            suffix = ".T" if st.session_state.market_type == "JPN" else ""
            t_price = yf.Ticker(f"{clean_ticker}{suffix}").history(period="1d")['Close'].iloc[-1]
            with f_col2: st.metric(f"🔥 {search_ticker}", f"{'¥' if suffix else '$'}{float(t_price):,.1f}")
            with f_col3:
                st.components.v1.html(f"""<button onclick="navigator.clipboard.writeText('{search_ticker}');this.innerText='COPIED!'" style="width: 100%; height: 40px; background: linear-gradient(45deg, #00ffff, #ff00ff); color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">📋 '{search_ticker}' をコピー</button>""", height=45)
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)

st.caption(f"Produced by Maria & BLACK | 2026-03-02")
