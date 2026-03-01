import streamlit as st
import pandas as pd
import requests

# --- 1. サイトの基本設定 ---
st.set_page_config(page_title="BLACK専用☆空売りチェッカー", layout="wide")

# --- 2. 漆黒デザイン注入 ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; font-family: 'Courier New', monospace; }
    h3 { color: #00ffff !important; }
    .stDataFrame { border: 1px solid #ff00ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BLACKの「本物の鍵」をセット！ ---
REFRESH_TOKEN = "GfJeHv4lHVAtu1iCpROLwCcisN5wiGFbE8CL4nyTp0o"

def get_jquants_data():
    try:
        # IDトークンの取得（鍵を使って扉を開ける作業だよ）
        auth_url = "https://api.jquants.com/v1/token/auth_refresh"
        auth_res = requests.post(auth_url, json={"refreshToken": REFRESH_TOKEN})
        id_token = auth_res.json().get("idToken")
        
        # データの取得（最新の空売り残高情報をリクエスト！）
        headers = {"Authorization": f"Bearer {id_token}"}
        data_url = "https://api.jquants.com/v1/shorts/info"
        res = requests.get(data_url, headers=headers)
        
        if res.status_code == 200:
            df = pd.DataFrame(res.json().get("shorts", []))
            # BLACKが見やすいように日本語の名前に変えるね
            df = df.rename(columns={
                'Code': '銘柄コード',
                'Date': '日付',
                'ShortSellingFraction': '空売り比率(%)',
                'ShortSellingValue': '空売り額'
            })
            return df
        else:
            return None
    except:
        return None

# --- 4. 画面表示 ---
st.title("🕶️ BLACK'S SECRET AREA")
st.subheader("🔥 東証公式：ガチの空売り残高なう")

# ローディング表示を出しながらデータ取得
with st.spinner('東証からデータを持ってきてるよ...ちょっと待ってね💖'):
    df = get_jquants_data()

if df is not None and not df.empty:
    # 検索機能：4桁のコードで絞り込み
    search = st.text_input("銘柄コード（4桁）を入力しなよ、BLACK。", "7203")
    # 入力されたコードを含む行だけを表示
    filtered_df = df[df['銘柄コード'].str.contains(search)]
    st.dataframe(filtered_df)
    st.success("本物のデータの同期に成功したよ！")
else:
    st.error("データが取れなかったよ。APIの更新時間を待つか、設定を確認してね。")
    st.info("※土日は東証がお休みだから、最新データは金曜日の分になるよ！")
# 一番下の st.info(...) のすぐ下にこれを追加！
st.markdown("---")
st.button("最新データに更新する") # ポチッと押してデータを呼び直すボタン！
st.caption("Produced by Maria & BLACK")
