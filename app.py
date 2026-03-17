import streamlit as st
import yfinance as yf

st.set_page_config(page_title="機関投資家チェック", page_icon="💸")

st.title("💸 米国株 機関投資家動向チェックアプリ 💸")
st.write("yfinanceを使ってサクッと無料データ取ってくるよん！")

# ティッカー入力欄（スクショに合わせてKIDZにしておくね！）
ticker = st.text_input("ティッカーシンボルを入力してね（例: AAPL, TSLA, KIDZ）", "KIDZ")

if st.button("データ取得！"):
    with st.spinner("BLACKのためにデータ取ってくるね..."):
        try:
            # yfinanceでティッカー情報を取得
            stock = yf.Ticker(ticker)
            
            # 機関投資家の保有データを取得
            inst_holders = stock.institutional_holders
            
            if inst_holders is not None and not inst_holders.empty:
                st.success("取得完了！まじ最高かよ✨")
                st.dataframe(inst_holders)
            else:
                st.warning("あれ？データがないみたい。その銘柄は機関投資家のデータが公開されてないか、ティッカーが違うかも。ピエン🥺")
                
        except Exception as e:
            st.error(f"ヤバい、なんかエラー起きた: {e}")
