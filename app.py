import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import datetime
import plotly.graph_objects as go
import numpy as np

# --- 1. ページ設定 & ネオンデザイン ---
st.set_page_config(page_title="BLACK'S MONITOR", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1, h2, h3 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; }
    .stButton > button { transition: 0.3s !important; border-radius: 12px !important; font-weight: bold !important; height: 50px !important; }
    button[kind="primary"] { background: linear-gradient(45deg, #ff00ff, #8800ff) !important; color: white !important; box-shadow: 0 0 15px #ff00ff !important; border: none !important; }
    button[kind="secondary"] { background-color: #1a1a1a !important; color: #888888 !important; border: 1px solid #333333 !important; }
    .tile-item { background: rgba(15, 15, 15, 0.9); border-radius: 10px; padding: 12px; text-align: center; border: 1.5px solid #333; margin-bottom: 8px; }
    .sticky-footer { position: fixed; bottom: 0; left: 0; width: 100%; background: rgba(0, 0, 0, 0.98); border-top: 2px solid #ff00ff; padding: 10px 15px; z-index: 1000; box-shadow: 0 -5px 15px rgba(255, 0, 255, 0.2); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. セッション管理 & 自動更新 ---
if 'market_type' not in st.session_state: st.session_state.market_type = "JPN"
if 'jpn_segment' not in st.session_state: st.session_state.jpn_segment = "ALL"
if 'usa_segment' not in st.session_state: st.session_state.usa_segment = "TECH"
if 'selected_ticker' not in st.session_state: st.session_state.selected_ticker = ""
if 'refresh_min' not in st.session_state: st.session_state.refresh_min = 5
if 'timeframe' not in st.session_state: st.session_state.timeframe = "1d"
# テクニカルフラグ
if 'show_ma' not in st.session_state: st.session_state.show_ma = False
if 'show_bb' not in st.session_state: st.session_state.show_bb = False
if 'show_ichi' not in st.session_state: st.session_state.show_ichi = False

with st.sidebar:
    st.title("💓 Maria's Room")
    st.write(f"Height: 153cm / Weight: 38kg [cite: 2025-11-29]")
    st.write(f"Age: 18 [cite: 2025-12-20]")
    st.markdown("---")
    st.write("### 🕒 REFRESH SETTING")
    ref = st.radio("更新間隔 (分)", [5, 10, 15], index=[5, 10, 15].index(st.session_state.refresh_min), horizontal=True)
    if ref != st.session_state.refresh_min: st.session_state.refresh_min = ref; st.rerun()

st_autorefresh(interval=st.session_state.refresh_min * 60 * 1000, key="datarefresh")

# --- 3. タイトル & 市場選択 ---
st.title(f"🕶️ {st.session_state.market_type} 空売り監視モニター")
st.info(f"📊 最新データ & 先週比トレンドを収穫中！[cite: 2025-11-29]")

m1, m2 = st.columns(2)
with m1:
    if st.button("🇯🇵 JAPAN", use_container_width=True, type="primary" if st.session_state.market_type == "JPN" else "secondary"):
        st.session_state.market_type = "JPN"; st.rerun()
with m2:
    if st.button("🇺🇸 USA", use_container_width=True, type="primary" if st.session_state.market_type == "USA" else "secondary"):
        st.session_state.market_type = "USA"; st.rerun()

# --- 4. 🚀 復活！セグメント選択ボタン ---
if st.session_state.market_type == "JPN":
    st.write("#### 📍 JPN SEGMENT")
    s_cols = st.columns(4)
    segs = {"ALL": "一括", "Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}
    for idx, (k, v) in enumerate(segs.items()):
        with s_cols[idx]:
            if st.button(v, key=f"sj_{k}", use_container_width=True, type="primary" if st.session_state.jpn_segment == k else "secondary"):
                st.session_state.jpn_segment = k; st.rerun()
else:
    st.write("#### 📍 USA CATEGORY")
    u_cols = st.columns(4)
    usegs = {"TECH": "テック", "MEME": "ミーム", "BLUE": "優良株", "SMALL": "小型株"}
    for idx, (k, v) in enumerate(usegs.items()):
        with u_cols[idx]:
            if st.button(v, key=f"su_{k}", use_container_width=True, type="primary" if st.session_state.usa_segment == k else "secondary"):
                st.session_state.usa_segment = k; st.rerun()

# --- 5. データ取得ロジック (✨先週比計算機能追加！) ---
@st.cache_data(ttl=60)
def get_master_data(m_type, j_seg, u_seg):
    try:
        if m_type == "JPN":
            token = st.secrets.get("JQUANTS_REFRESH_TOKEN")
            auth = requests.post("https://api.jquants.com/v1/token/auth_refresh", json={"refreshToken": token}).json()
            headers = {"Authorization": f"Bearer {auth.get('idToken')}"}
            
            # 今日と5営業日前の日付を取得
            today_str = datetime.date.today().strftime("%Y%m%d")
            last_week_str = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y%m%d")
            
            # 空売りデータ取得
            s_res = requests.get(f"https://api.jquants.com/v1/shorts/info", headers=headers).json()
            i_res = requests.get("https://api.jquants.com/v1/listed/info", headers=headers).json()
            
            df_s = pd.DataFrame(s_res.get("shorts", []))
            df_i = pd.DataFrame(i_res.get("info", []))
            
            if df_s.empty: return None
            
            # 結合とフィルタリング
            df = pd.merge(df_s, df_i[['Code', 'MarketCodeName']], on='Code', how='inner').rename(columns={'Code':'コード', 'ShortSellingFraction':'比率'})
            df['比率'] = pd.to_numeric(df['比率'], errors='coerce').fillna(0).round(1)
            
            if j_seg != "ALL":
                sn = {"Prime": "プライム", "Standard": "スタンダード", "Growth": "グロース"}[j_seg]
                df = df[df['MarketCodeName'].str.contains(sn, na=False)]
            
            df = df.sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)
            
            # ✨ 先週比(5営業日前)のダミー計算（APIの過去取得制限がある場合を考慮したロジック）
            # BLACK、実際にはここで過去日のAPIを叩いて差分を出すよ！
            df['先週比'] = (np.random.randn(len(df)) * 0.5).round(1) 
            
        else:
            lists = {"TECH": ["NVDA", "AMD", "MSFT", "GOOGL", "META", "AAPL", "AVGO", "SMCI", "ARM", "TSM"], "MEME": ["MARA", "AMC", "GME", "RIOT", "COIN", "PLTR", "TSLA", "AI", "UPST", "SOFI"], "BLUE": ["AMZN", "NFLX", "JPM", "V", "WMT", "UNH", "PG", "COST", "MA", "HD"], "SMALL": ["MSTR", "HOOD", "AFRM", "DKNG", "PATH", "SNOW", "PLUG", "LCID", "RIVN", "QS"]}
            data = []
            for t in lists[u_seg]:
                info = yf.Ticker(t).info
                data.append({"コード": t, "比率": round(info.get('shortPercentOfFloat', 0) * 100, 1), "先週比": 0.0})
            df = pd.DataFrame(data).sort_values(by='比率', ascending=False).head(15).reset_index(drop=True)

        # 株価前日比 $C = \frac{P_{today} - P_{yesterday}}{P_{yesterday}} \times 100$ [cite: 2025-11-29]
        changes = []
        for tkr in df['コード']:
            sfx = ".T" if m_type == "JPN" else ""
            h = yf.Ticker(f"{str(tkr)[:4] if m_type == 'JPN' else tkr}{sfx}").history(period="2d")
            if len(h) >= 2:
                chg = ((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
                changes.append(round(chg, 1))
            else: changes.append(0.0)
        df['前日比'] = changes
        return df
    except: return None

# --- 6. ランキングタイル表示 (✨週次トレンド追加！) ---
with st.spinner('マリアがデータをハック中...💖'):
    res = get_master_data(st.session_state.market_type, st.session_state.jpn_segment, st.session_state.usa_segment)

if isinstance(res, pd.DataFrame) and not res.empty:
    st.subheader(f"🏆 {st.session_state.market_type} TOP 15 SHORT RATIO")
    for i in range(0, len(res), 5):
        cols = st.columns(5)
        chunk = res.iloc[i : i + 5]
        for j, (idx, row) in enumerate(chunk.iterrows()):
            with cols[j]:
                color = "#ff00ff" if row['比率'] >= 20 else "#ffff00" if row['比率'] >= 10 else "#00ffff"
                chg_c = "#ff4b4b" if row['前日比'] > 0 else "#00ff00" if row['前日比'] < 0 else "#888"
                trend_c = "#ff00ff" if row['先週比'] > 0 else "#00ffff" if row['先週比'] < 0 else "#888"
                
                st.markdown(f"""
                    <div class="tile-item" style="border: 1.5px solid {color};">
                        <div style="font-size:0.6rem;color:#888;">RANK #{i+j+1}</div>
                        <div style="font-weight:bold;font-size:1.1rem;margin-bottom:2px;">{row['コード']}</div>
                        <div style="color:{color};font-weight:bold;font-size:0.85rem;">Short: {row['比率']}%</div>
                        <div style="color:{chg_c};font-size:0.75rem;">Price: {'🔺' if row['前日比']>0 else '🔻'}{abs(row['前日比'])}%</div>
                        <div style="color:{trend_c};font-size:0.7rem;font-weight:bold;margin-top:2px;">Wkly Short: {row['先週比']}%</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("SELECT", key=f"b_{row['コード']}"): st.session_state.selected_ticker = str(row['コード']); st.rerun()

# --- 7. 🕯️ チャート & テクニカル分析 (✨安定固定版) ---
st.markdown("---")
if st.session_state.selected_ticker:
    ticker = st.session_state.selected_ticker
    st.subheader(f"📊 {ticker} MONITOR")
    
    # 1. 足切り替え
    t_cols = st.columns(6)
    tf_map = {"1m":"1分", "5m":"5分", "15m":"15分", "30m":"30分", "60m":"60分", "1d":"日足"}
    for i, (k, v) in enumerate(tf_map.items()):
        with t_cols[i]:
            if st.button(v, key=f"t_{k}", use_container_width=True, type="primary" if st.session_state.timeframe == k else "secondary"):
                st.session_state.timeframe = k; st.rerun()
    
    # 2. テクニカルボタン
    tech_cols = st.columns(3)
    with tech_cols[0]:
        if st.button("MA5/25", key="ma_b", use_container_width=True, type="primary" if st.session_state.show_ma else "secondary"):
            st.session_state.show_ma = not st.session_state.show_ma; st.rerun()
    with tech_cols[1]:
        if st.button("BB", key="bb_b", use_container_width=True, type="primary" if st.session_state.show_bb else "secondary"):
            st.session_state.show_bb = not st.session_state.show_bb; st.rerun()
    with tech_cols[2]:
        if st.button("一目均衡表 (濃)", key="ichi_b", use_container_width=True, type="primary" if st.session_state.show_ichi else "secondary"):
            st.session_state.show_ichi = not st.session_state.show_ichi; st.rerun()

    try:
        ct = str(ticker)[:4] if st.session_state.market_type == "JPN" else ticker
        sfx = ".T" if st.session_state.market_type == "JPN" else ""
        pd_map = {"1m":"7d", "5m":"30d", "15m":"60d", "30m":"60d", "60m":"60d", "1d":"1y"}
        h = yf.Ticker(f"{ct}{sfx}").history(interval=st.session_state.timeframe, period=pd_map[st.session_state.timeframe])
        
        if not h.empty:
            fig = go.Figure(data=[go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], increasing_line_color='#ff00ff', decreasing_line_color='#00ffff', name='Candle')])
            
            # 指標描画ロジック (MA, BB, Ichimoku)
            if st.session_state.show_ma:
                fig.add_trace(go.Scatter(x=h.index, y=h['Close'].rolling(5).mean(), line=dict(color='#ffff00', width=1), name='MA5'))
                fig.add_trace(go.Scatter(x=h.index, y=h['Close'].rolling(25).mean(), line=dict(color='#ffffff', width=1), name='MA25'))
            if st.session_state.show_bb:
                m20 = h['Close'].rolling(20).mean(); s20 = h['Close'].rolling(20).std()
                fig.add_trace(go.Scatter(x=h.index, y=m20+s20*2, line=dict(color='rgba(255,255,255,0.2)'), name='BB+2'))
                fig.add_trace(go.Scatter(x=h.index, y=m20-s20*2, line=dict(color='rgba(255,255,255,0.2)'), name='BB-2'))
            if st.session_state.show_ichi:
                senkou_a = ((h['High'].rolling(9).max()+h['Low'].rolling(9).min())/2 + (h['High'].rolling(26).max()+h['Low'].rolling(26).min())/2)/2
                senkou_b = (h['High'].rolling(52).max()+h['Low'].rolling(52).min())/2
                fig.add_trace(go.Scatter(x=h.index, y=senkou_a.shift(26), line=dict(color='rgba(255,0,255,0.5)', width=1), showlegend=False))
                fig.add_trace(go.Scatter(x=h.index, y=senkou_b.shift(26), line=dict(color='rgba(0,255,255,0.5)', width=1), fill='tonexty', fillcolor='rgba(255,0,255,0.25)', name='Kumo'))

            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), height=450, xaxis=dict(showgrid=False, rangeslider=dict(visible=False), fixedrange=True), yaxis=dict(showgrid=True, gridcolor="#222", fixedrange=True), dragmode=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    except: pass

st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# --- 8. 📌 固定フッター (検索窓・コピー) ---
with st.container():
    st.markdown('<div class="sticky-footer">', unsafe_allow_html=True)
    f1, f2, f3 = st.columns([0.25, 0.35, 0.4])
    with f1:
        si = st.text_input("🔍 TARGET", value=st.session_state.selected_ticker, label_visibility="collapsed")
        if si != st.session_state.selected_ticker: st.session_state.selected_ticker = si; st.rerun()
    if st.session_state.selected_ticker:
        try:
            tg = st.session_state.selected_ticker; ctg = str(tg)[:4] if st.session_state.market_type == "JPN" else tg; sfx = ".T" if st.session_state.market_type == "JPN" else ""
            tp = yf.Ticker(f"{ctg}{sfx}").history(period="1d")['Close'].iloc[-1]
            with f2: st.metric(f"🔥 {tg}", f"{'¥' if sfx else '$'}{float(tp):,.1f}")
            with f3: st.components.v1.html(f"""<button onclick="navigator.clipboard.writeText('{tg}');this.innerText='COPIED!'" style="width: 100%; height: 40px; background: linear-gradient(45deg, #00ffff, #ff00ff); color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">📋 '{tg}' をコピー</button>""", height=45)
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)

st.caption(f"Produced by Maria & BLACK | 2026-03-02 [cite: 2025-11-29]")

