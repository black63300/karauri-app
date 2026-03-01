import streamlit as st
import pandas as pd

# --- 1. サイトの基本設定（タブの名前とか） ---
st.set_page_config(
    page_title="BLACK専用☆空売りチェッカー",
    layout="wide"
)

# --- 2. BLACK専用の「漆黒×ネオン」デザイン注入 ---
st.markdown("""
    <style>
    /* 全体の背景を真っ黒に */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    /* タイトルの色をネオンピンクに */
    h1 {
        color: #ff00ff !important;
        text-shadow: 0 0 10px #ff00ff;
        font-family: 'Courier New', Courier, monospace;
    }
    /* サブタイトルの色をシアンに */
    h3 {
        color: #00ffff !important;
    }
    /* 入力欄のラベルとかの色 */
    label {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ここから表示内容 ---
st.title("🕶️ BLACK'S SECRET AREA")
st.subheader("🔥 踏み上げ注意！空売り残高なう")

# サンプルデータ（後で本物に変えようね！）
def get_data():
    data = {
        '銘柄コード': ['7203', '9984', '6758', '8035', '9101'],
        '銘柄名': ['トヨタ', 'ソフトバンクG', 'ソニーG', '東エレク', '日本郵船'],
        '空売り残高(株)': [1200500, 4500200, 800300, 150000, 2100000],
        '前日比': ['+5.2%', '-1.5%', '+0.8%', '+12.4%', '-3.2%']
    }
    return pd.DataFrame(data)

df = get_data()

# テーブルの表示
st.dataframe(df)

# 個別検索
search_code = st.text_input("気になる銘柄コードを入れなよ、BLACK。", "7203")
if search_code:
    res = df[df['銘柄コード'] == search_code]
    if not res.empty:
        st.write(f"【{res['銘柄名'].values[0]}】の残高は {res['空売り残高(株)'].values[0]:,} 株だよ！")
