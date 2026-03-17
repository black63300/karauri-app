import streamlit as st
import requests
import pandas as pd

# APIキーの設定（自分で取得したキーをここに入れてね！）
API_KEY = "YOUR_API_KEY_HERE"

st.set_page_config(page_title="機関投資家チェック", page_icon="💸")

st.title("💸 米国株 機関投資家動向チェックアプリ 💸")
st.write("最新の13F報告書ベースの機関投資家保有データを表示するよん！")

# ティッカー入力欄
ticker = st.text_input("ティッカーシンボルを入力してね（例: AAPL, TSLA）", "AAPL")

if st.button("データ取得！"):
    with st.spinner("BLACKのためにデータ取ってくるね..."):
        # Financial Modeling Prep APIのエンドポイント例
        url = f"https://financialmodelingprep.com/api/v4/institutional-ownership/institutional-investors-ownership-percentage?symbol={ticker}&apikey={API_KEY}"
        
        try:
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    # データをデータフレームに変換して表示
                    df = pd.DataFrame(data)
                    st.success("取得完了！まじ最高かよ✨")
                    st.dataframe(df)
                else:
                    st.warning("あれ？データがないみたい。ティッカー合ってる？ピエン🥺")
            else:
                st.error("エラー発生！APIキーとか通信状態を確認してみて泣")
                
        except Exception as e:
            st.error(f"ヤバい、なんかエラー起きた: {e}")
