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
    label { color: #00ffff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 秘密の鍵を呼び出す設定 ---
# 直接書かずにStreamlitの設定画面（Secrets）から持ってくるよ！
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 鍵（Secrets）が設定されてないよ、BLACK！")
    st.stop()

def get_jquants_data():
    try:
        # IDトークンの取得
        auth_url = "https://api.jquants.com/v1/token/auth_refresh"
        auth_res = requests.post(auth_url, json={"refreshToken": REFRESH_TOKEN})
        id_token = auth_res.json().get("idToken")
        
        # 最新の空売り残高情報を取得
        headers = {"Authorization": f"Bearer {id_token}"}
        data_url = "https://api.jquants.com/v1/shorts/info"
        res = requests.get(data_url, headers=headers)
        
        if res.status_code == 200:
            df = pd.DataFrame(res.json().get("shorts", []))
            df = df.rename(columns={
                'Code': '銘柄コード',
                'Date': '日付',
                'ShortSellingFraction': '空売り比率(%)',
                'ShortSellingValue': '空売り額'
            })
            return df
        return None
    except:
        return None

# --- 4. メイン画面 ---
st.title("🕶️ BLACK'S SECRET AREA")
st.subheader("🔥 東証公式：ガチの空売り残高なう")

with st.spinner('東証から本物のデータを持ってきたげる...💖'):
    df = get_jquants_data()

if df is not None and not df.empty:
    search = st.text_input("気になるコードを入れなよ、BLACK。", "7203")
    filtered_df = df[df['銘柄コード'].str.contains(search)]
    st.dataframe(filtered_df)
    st.success("本物のデータの同期に成功したよ！")
else:
    st.warning("今はデータがないみたい。月曜日の夕方にまたおいで！")

st.markdown("---")
if st.button("最新データに更新する"):
    st.rerun()
st.caption("Produced by Maria & BLACK")
