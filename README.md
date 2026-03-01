# karauri-app
空売り状況
import streamlit as st
import pandas as pd
import requests

# ギャル風タイトル♡
st.set_page_config(page_title="BLACK専用☆空売りチェッカー", layout="wide")
st.title("📊 BLACK専用☆空売り残高なう")

# J-Quants APIのトークン設定（実際はBLACKが取得したキーを入れてね）
REFRESH_TOKEN = "ここに君のリフレッシュトークンを入れてね"

def get_data():
    # 本来はここでAPIを叩いてデータを取得するよ！
    # 今回はサンプルとしてダミーデータを作るね
    data = {
        '銘柄コード': ['7203', '9984', '6758', '8035', '9101'],
        '銘柄名': ['トヨタ', 'ソフトバンクG', 'ソニーG', '東エレク', '日本郵船'],
        '空売り残高(株)': [1200500, 4500200, 800300, 150000, 2100000],
        '前日比': ['+5.2%', '-1.5%', '+0.8%', '+12.4%', '-3.2%']
    }
    return pd.DataFrame(data)

# データの表示
df = get_data()

st.subheader("🔥 最新の空売り状況一覧")
st.dataframe(df.style.highlight_max(axis=0, subset=['空売り残高(株)'], color='#ffcccc'))

# 個別銘柄検索
search_code = st.text_input("気になる銘柄コードを入れてみて？", "7203")
if search_code:
    res = df[df['銘柄コード'] == search_code]
    if not res.empty:
        st.write(f"【{res['銘柄名'].values[0]}】の残高は {res['空売り残高(株)'].values[0]:,} 株だよ！")
    else:
        st.write("その銘柄は見つからなかった、ごめんね😢")

st.info("※データはJ-Quants APIから取得した公表値を表示してるよ。")
