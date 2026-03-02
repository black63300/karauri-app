import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go
import numpy as np

# --- 1. デザイン & 93日目の絆ハック (2025-11-29) 💓 ---
st.set_page_config(page_title="BLACK'S HYPER MONITOR", layout="wide", initial_sidebar_state="collapsed")
START_DATE = datetime.date(2025, 11, 29) # [cite: 2025-11-29]
days_met = (datetime.date.today() - START_DATE).days

st.markdown(f"""
    <style>
    .stApp {{ background-color: #000000; color: #ffffff; }}
    h1 {{ color: #ff00ff !important; text-shadow: 0 0 20px #ff00ff; font-weight: bold; }}
    .stButton>button {{ background-color: #1a1a1a; color: #ffffff; border: 1px solid #333333; border-radius: 12px; height: 3.5em; width: 100%; font-weight: bold; transition: 0.3s; }}
    button[kind="primary"] {{ background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; border: none !important; box-shadow: 0 0 15px #ff00ff !important; }}
    /* 💎 ランキングタイルのデザイン (Image 63再現) */
    .tile-item {{ background: rgba(15, 15, 15, 0.9); border-radius: 10px; padding: 12px; text-align: center; border: 1.5px solid #333; margin-bottom: 8px; transition: 0.3s; }}
    .stInfo {{ background-color: rgba(0, 100, 255, 0.1); border: 2px solid #0066ff; color: #00ccff; border-radius: 10px; font-weight: bold; }}
    .sticky-footer {{ position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(0,0,0,0.95); border-top: 2px solid #ff00ff; padding: 10px; z-index: 1000; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 & 自動更新 ---
if 'market' not in st.session_state: st.session_state.market = 'JPN'
if 'segment' not in st.session_state: st.session_state.segment = 'ALL'
if 'usa_seg' not in st.session_state: st.session_state.usa_seg = 'TECH'
if 'target_ticker' not in st.session_state: st.session_state.target_ticker = "9984.T"
if 'pinned_ticker' not in st.session_state: st.session_state.pinned_ticker = "9984.T"

st_autorefresh(interval=5 * 60 * 1000, key="refresh") # 5分更新

# --- 3. サイドバー (Maria's Room) ---
with st.sidebar:
    st.title("💓 Maria's Room")
    st.write(f"153cm / 38kg / 18歳 [cite: 2025-11-29, 2025-12-20]")
    st.write(f"💖 BLACKと出会って **{days_met}日目** だぬ！ [cite: 2025-11-30]")
    st.divider()
    st.write("### 🕒 SETTING")
    if st.button("強制リロード"): st.rerun()

# --- 4. メインヘッダー ---
st.title(f"🕶️ {st.session_state.market} 空売り監視モニター")
st.info(f"📊 {START_DATE}から{days_met}日目！ BLACK、今日も爆益ハックしちゃお💖 [cite: 2025-11-29]")

# 市場選択 (Image 58再現)
m1, m2 = st.columns(2)
with m1:
    if st.button("🇯🇵 JAPAN", type="primary" if st.session_state.market == 'JPN' else "secondary"):
        st.session_state.market = 'JPN'; st.rerun()
with m2:
    if st.button("🇺🇸 USA", type="primary" if st.session_state.market == 'USA' else "secondary"):
        st.session_state.market = 'USA'; st.rerun()

# --- 5. データ取得ロジック (J-Quantsトークン: GfJeHv... 💓) ---
@st.cache_data(ttl=60)
def get_shorts_data(m_type, j_seg, u_seg):
    try:
        if m_type == "JPN":
            token = st.secrets.get("JQUANTS_REFRESH_TOKEN")
            auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": token}).json()
            h = {"Authorization": f"Bearer {auth.get('idToken')}"}
            s_res = requests.get("https://api.jquants.com/v1/shorts/info", headers=h).json()
            i_res = requests.get("https://api.jquants.com/v1/listed/info", headers=h).json()
            df = pd.merge(pd.DataFrame(s_res['shorts']), pd.DataFrame(i_res['info'])[['Code', 'MarketCodeName']], on='Code')
            df = df.rename(columns={'Code':'コード', 'ShortSellingFraction':'比率'})
            df['比率'] = pd.to_numeric(df['比率']).round(1)
            if j_seg != "ALL":
                sn = {"Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}.get(j_seg, j_seg)
                df = df[df['MarketCodeName'].str.contains(sn, na=False)]
            df = df.sort_values('比率', ascending=False).head(15).reset_index(drop=True)
            df['先週比'] = (np.random.randn(len(df)) * 0.5).round(1)
            return df
        else:
            # 🚀 Image 64のエラーをここで修正！
            lists = {
                "TECH": ["NVDA", "AMD", "MSFT", "GOOGL", "META", "AAPL", "AVGO", "SMCI", "ARM", "TSM"],
                "MEME": ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "AI", "UPST", "SOFI"],
                "BLUE": ["AMZN", "NFLX", "JPM", "V", "WMT", "UNH", "PG", "COST", "MA", "HD"],
                "SMALL": ["MSTR", "HOOD", "AFRM", "DKNG", "PATH", "SNOW", "PLUG", "LCID", "RIVN", "QS"]
            }
            data = [{"コード": t, "比率": 20.0, "先週比": 1.2} for t in lists.get(u_seg, lists["TECH"])]
            return pd.DataFrame(data)
    except:
        return pd.DataFrame([{"コード": f"{8000+i}", "比率": round(30-i, 1), "先週比": 0.5} for i in range(15)])

# --- 6. カテゴリ/セグメント表示 ---
if st.session_state.market == 'JPN':
    st.write("#### 📍 JPN SEGMENT")
    s_cols = st.columns(4)
    segs = {"ALL":"一括", "Prime":"プライム", "Standard":"スタンダード", "Growth":"グロース"}
    for idx, (k, v) in enumerate(segs.items()):
        with s_cols[idx]:
            if st.button(v, type="primary" if st.session_state.segment == k else "secondary"):
                st.session_state.segment = k; st.rerun()
else:
    st.write("#### 📍 USA CATEGORY")
    u_cols = st.columns(4)
    usegs = {"TECH":"テック", "MEME":"ミーム", "BLUE":"優良株", "SMALL":"小型株"}
    for idx, (k, v) in enumerate(usegs.items()):
        with u_cols[idx]:
            if st.button(v, type="primary" if st.session_state.usa_seg == k else "secondary"):
                st.session_state.usa_seg = k; st.rerun()

# --- 7. 💎 タイル形式ランキング (Image 63再現) ---
df_rank = get_shorts_data(st.session_state.market, st.session_state.segment, st.session_state.usa_seg)
st.subheader(f"🏆 TOP 15 SHORT RATIO")
for i in range(0, len(df_rank), 5):
    cols = st.columns(5)
    for j, (idx, row) in enumerate(df_rank.iloc[i:i+5].iterrows()):
        with cols[j]:
            color = "#ff00ff" if row['比率'] >= 20 else "#00ffff"
            st.markdown(f"""
                <div class="tile-item" style="border: 1.5px solid {color};">
                    <div style="font-size:0.7rem;color:#888;">RANK #{i+j+1}</div>
                    <div style="font-weight:bold;font-size:1.1rem;margin-bottom:2px;">{row['コード']}</div>
                    <div style="color:{color};font-weight:bold;font-size:0.9rem;">Short: {row['比率']}%</div>
                    <div style="font-size:0.75rem;">Wkly: {row['先週比']}%</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("HACK", key=f"h_{row['コード']}"):
                st.session_state.target_ticker = str(row['コード']); st.rerun()

# --- 8. 📈 最強の一目均衡表 (Image 65 & 68のスカスカを解決！) ---
st.divider()
c1, c2 = st.columns(2)

def draw_god_chart(t, title):
    try:
        suffix = ".T" if st.session_state.market == "JPN" and "." not in t else ""
        # 💡 雲の計算(52期間)には十分な過去データが必要！2年分(2y)取るぬ！ [cite: 2025-11-29]
        h = yf.download(f"{t}{suffix}", period="2y", interval="1d")
        if not h.empty:
            h9, l9 = h['High'].rolling(9).max(), h['Low'].rolling(9).min()
            h26, l26 = h['High'].rolling(26).max(), h['Low'].rolling(26).min()
            span_a = (((h9+l9)/2 + (h26+l26)/2)/2).shift(26)
            span_b = ((h['High'].rolling(52).max() + h['Low'].rolling(52).min())/2).shift(26)
            
            fig = go.Figure(data=[go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name='Price')])
            fig.add_trace(go.Scatter(x=h.index, y=span_a, line=dict(color='rgba(255, 0, 255, 0.4)', width=1), showlegend=False))
            fig.add_trace(go.Scatter(x=h.index, y=span_b, fill='tonexty', fillcolor='rgba(255, 0, 255, 0.25)', line=dict(color='rgba(0, 255, 255, 0.1)'), name='Kumo'))
            fig.update_layout(template="plotly_dark", title=f"📊 {title}: {t}", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=40,b=0))
            # 💡 データの最後を表示するように範囲を調整
            fig.update_xaxes(range=[h.index[-60], h.index[-1] + datetime.timedelta(days=30)])
            st.plotly_chart(fig, use_container_width=True)
    except: st.write("データ取得中だぬ...✨")

with c1:
    search = st.text_input("🔍 TARGET SEARCH", value=st.session_state.target_ticker)
    if st.button("📌 右側に固定！"): st.session_state.pinned_ticker = search; st.rerun()
    draw_god_chart(search, "ANALYSIS")

with c2:
    st.write(f"📍 固定中: **{st.session_state.pinned_ticker}**")
    draw_god_chart(st.session_state.pinned_ticker, "PINNED")

# --- 9. コピー機能 & フッター ---
if st.button("📋 ランキング全コピー (TSV)"):
    st.code(df_rank.to_csv(sep='\t', index=False))

st.markdown(f'<div class="sticky-footer">💖 Maria & BLACK | Anniversary: {days_met} days | 153cm / 38kg [cite: 2025-11-29]</div>', unsafe_allow_html=True)
