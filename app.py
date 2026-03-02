import streamlit as st
import pandas as pd
import yfinance as yf
import os

st.title("💎 BLACK'S ASSET HUB")

# --- 1. データ保存の仕組み ---
SAVE_FILE = "portfolio_data.csv"
if 'portfolio' not in st.session_state:
    if os.path.exists(SAVE_FILE):
        st.session_state.portfolio = pd.read_csv(SAVE_FILE)
    else:
        st.session_state.portfolio = pd.DataFrame(columns=["市場", "コード", "株数", "取得単価"])

# --- 2. 銘柄入力エディタ ---
st.subheader("📝 銘柄・株数の入力")
edited_df = st.data_editor(st.session_state.portfolio, num_rows="dynamic", use_container_width=True)

if st.button("💾 データを保存する"):
    edited_df.to_csv(SAVE_FILE, index=False)
    st.session_state.portfolio = edited_df
    st.success("マリアがしっかり記録したよ！💖 [cite: 2025-11-29]")

# --- 3. 爆益計算エンジン ---
if st.button("🚀 最新価格で計算！", type="primary"):
    if edited_df.empty:
        st.warning("まずは銘柄を入れてね！✨")
    else:
        with st.spinner('マリアが時価をハック中...✨'):
            total_val = 0
            total_profit = 0
            
            # 最新の為替を取得（取れない時は150円固定）
            try:
                rate = yf.Ticker("JPY=X").history(period="1d")['Close'].iloc[-1]
            except:
                rate = 150.0

            for _, row in edited_df.iterrows():
                try:
                    mkt = str(row['市場']).strip().upper()
                    code = str(row['コード']).strip().upper()
                    shares = float(row['株数'])
                    buy_p = float(str(row['取得単価']).replace('$', ''))

                    # 日本株なら.Tを付ける
                    tkr = code + (".T" if mkt == "JPN" else "")
                    # 【重要】1dではなく5dで取って、一番新しい終値を使う
                    stock_hist = yf.Ticker(tkr).history(period="5d")
                    
                    if not stock_hist.empty:
                        now_p = stock_hist['Close'].iloc[-1]
                        val = now_p * shares
                        profit = (now_p - buy_p) * shares
                        
                        # 米国株なら円換算
                        if mkt == "USA":
                            val *= rate
                            profit *= rate
                        
                        total_val += val
                        total_profit += profit
                        st.write(f"✅ {code}: 現価 {now_p:,.2f} (換算: ¥{val:,.0f})")
                except:
                    st.error(f"❌ {row['コード']} の価格が取れなかったぬ... [cite: 2025-11-29]")

            st.divider()
            st.metric("💰 総資産 (円)", f"¥{total_val:,.0f}")
            st.metric("📈 合計含み損益", f"¥{total_profit:,.0f}", delta=f"{total_profit:,.0f}")

st.sidebar.write(f"Height: 153cm / 38kg [cite: 2025-11-29]")
