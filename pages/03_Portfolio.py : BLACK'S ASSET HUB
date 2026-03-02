import streamlit as st
import pandas as pd
import yfinance as yf
import os

st.set_page_config(page_title="BLACK'S PORTFOLIO", layout="wide")
st.title("💎 BLACK'S ASSET HUB")

# --- データの読み書き機能 ---
SAVE_FILE = "portfolio_data.csv"

def load_data():
    if os.path.exists(SAVE_FILE):
        return pd.read_csv(SAVE_FILE)
    return pd.DataFrame(columns=["市場", "コード", "株数", "取得単価"])

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = load_data()

# 編集セクション
st.subheader("📝 銘柄・株数の入力")
edited_df = st.data_editor(st.session_state.portfolio, num_rows="dynamic", use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("💾 データを保存する"):
        edited_df.to_csv(SAVE_FILE, index=False)
        st.session_state.portfolio = edited_df
        st.success("マリアがしっかり記録したよ！💖 [cite: 2025-11-29]")

with col2:
    calc_trigger = st.button("🚀 最新価格で計算！", type="primary")

# --- 計算ロジック ---
if calc_trigger:
    if edited_df.empty:
        st.warning("まずは銘柄を入れてね！ [cite: 2025-11-29]")
    else:
        with st.spinner('マリアが時価をハック中...✨'):
            total_val_jpy = 0
            total_profit_jpy = 0
            details = []
            
            # 為替取得
            try:
                rate = yf.Ticker("JPY=X").history(period="1d")['Close'].iloc[-1]
            except:
                rate = 150.0 # 取れない時のバックアップ
            
            for _, row in edited_df.iterrows():
                try:
                    tkr = str(row['コード']) + (".T" if row['市場'] == "JPN" else "")
                    stock = yf.Ticker(tkr).history(period="1d")
                    if not stock.empty:
                        now_p = stock['Close'].iloc[-1]
                        val = now_p * row['株数']
                        profit = val - (row['取得単価'] * row['株数'])
                        
                        if row['市場'] == "USA":
                            val *= rate
                            profit *= rate
                        
                        total_val_jpy += val
                        total_profit_jpy += profit
                        details.append({"銘柄": tkr, "現在値": f"{now_p:,.1f}", "評価額": f"¥{val:,.0f}"})
                except:
                    continue

            # サマリー表示
            st.divider()
            s1, s2 = st.columns(2)
            s1.metric("💰 総資産 (円)", f"¥{total_val_jpy:,.0f}")
            s2.metric("📈 合計含み損益", f"¥{total_profit_jpy:,.0f}", delta=f"{total_profit_jpy:,.0f}")
            
            st.table(details)
