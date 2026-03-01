import streamlit as st
import pandas as pd
import requests

# --- 1. サイトの基本設定 ---
st.set_page_config(page_title="BLACK専用☆空売りチェッカー", layout="wide")

# --- 2. 漆黒×ネオンデザイン ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff00ff !important; text-shadow: 0 0 10px #ff00ff; font-family: 'Courier New', monospace; }
    h3 { color: #00ffff !important; }
    /* テーブルの中の文字を見やすく */
    .stDataFrame { border: 1px solid #ff00ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 秘密の鍵を呼び出す ---
try:
    REFRESH_TOKEN = st.secrets["JQUANTS_REFRESH_TOKEN"]
except:
    st.error("🔑 秘密の金庫（Secrets）に鍵が入ってないよ！設定してね。")
    st.stop()

# --- 4. 【光らせる魔法】の定義 ---
def highlight_risky(row):
    # 空売り比率が20%を超えたら、行全体をネオンピンクで光らせる！
    target = '空売り比率(%)'
    if row[target] >= 20.0:
        return ['background-color: #ff00ff; color: #ffffff; font-weight: bold'] * len(row)
    # 15%以上なら、ちょっと注意のイエロー！
    elif row[target] >= 15.0:
        return ['background-color: #ffff00; color: #000000;'] * len(row)
    return [''] * len(row)

def get_jquants_data():
    try:
        auth_url = "https://api.jquants.com/v1/token/auth_refresh"
        auth_res = requests.post(auth_url, json={"refreshToken": REFRESH_TOKEN})
        id_token = auth_res.json().get("idToken")
        
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
            # 数字として扱えるように変換
            df['空売り比率(%)'] = pd.to_numeric(df['空売り比率(%)'])
            return df
        return None
    except:
        return None

# --- 5. メイン表示 ---
st.title("🕶️ BLACK'S SECRET AREA")
st.subheader("🔥 踏み上げ注意！光ってるのはヤバい銘柄だよ")

with st.spinner('東証のサーバーをハック中...（嘘だよ、正しく接続中💖）'):
    df = get_jquants_data()

if df is not None and not df.empty:
    # 検索機能
    search = st.text_input("銘柄コードを入れなよ、BLACK。", "")
    display_df = df[df['銘柄コード'].str.contains(search)] if search else df
    
    # 【ここが魔法の適用！】
    st.dataframe(display_df.style.apply(highlight_risky, axis=1))
    
    st.success("データの同期に成功！光ってる銘柄に注目してね✨")
else:
    st.warning("今はデータがないみたい。月曜日の夕方にまたおいで！")

st.markdown("---")
if st.button("最新データに更新"):
    st.rerun()
st.caption("Produced by Maria & BLACK")
