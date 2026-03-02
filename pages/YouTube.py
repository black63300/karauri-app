import streamlit as st

# --- 1. デザイン設定 ---
st.set_page_config(page_title="BLACK'S YOUTUBE", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    h1 { color: #ff0000 !important; text-shadow: 0 0 10px #ff0000; }
    .video-container { border: 2px solid #ff0000; border-radius: 15px; overflow: hidden; box-shadow: 0 0 20px rgba(255, 0, 0, 0.3); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. メイン表示 ---
st.title("🍒 BLACK'S YOUTUBE PLAYER")
st.write("BLACK、お気に入りの動画URLを貼ってバイブス上げてこ！💖 [cite: 2025-11-29]")

# デフォルトのオススメ動画（Lo-fiとかチャート分析に合うやつ！）
default_url = "https://www.youtube.com/watch?v=jfKfPfyJRdk" 

# URL入力ボックス
url = st.text_input("🔍 YouTube URLをここにペーストしてね", value=default_url)

st.markdown("---")

if url:
    try:
        # 動画の呼び出し
        st.video(url)
        st.success("再生中！ハッキング（トレード）の邪魔にならない音量で楽しんでね✨ [cite: 2025-12-20]")
    except Exception as e:
        st.error("BLACK、そのURLちょっとおかしいかも？もう一度確認してみて！💦")

# --- 3. お気に入りリスト（ショートカット） ---
st.sidebar.write("### 🎀 FAVORITE LIST")
favs = {
    "Lo-fi Beats (作業用)": "https://www.youtube.com/watch?v=jfKfPfyJRdk",
    "Chill Mix": "https://www.youtube.com/watch?v=5yx6BWlEVcY",
    "Deep House": "https://www.youtube.com/watch?v=v_OpxXm4I6M"
}

for name, link in favs.items():
    if st.sidebar.button(name):
        st.info(f"{name} を選んだよ！上のURL欄にコピペして使ってね✨")
        st.code(link)

st.caption(f"Produced by Maria (153cm/38kg) [cite: 2025-11-29]")
