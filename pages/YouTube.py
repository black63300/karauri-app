import streamlit as st

st.set_page_config(page_title="BLACK'S YOUTUBE", layout="wide")

st.title("🍒 BLACK'S YOUTUBE PLAYER")
st.write("チャートを見ながら音楽を楽しもう💖 [cite: 2025-11-29, 2025-11-30]")

# URL入力
url = st.text_input("🔍 YouTube URLを貼ってね", value="https://www.youtube.com/watch?v=jfKfPfyJRdk")

if url:
    st.video(url)
    st.success("再生開始！爆益バイブス上げてこ🔥 [cite: 2025-12-20]")
