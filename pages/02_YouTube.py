import streamlit as st

st.set_page_config(page_title="BLACK'S YOUTUBE", layout="wide")
st.title("🍒 BLACK'S CHILL ROOM")

st.write("Lofi流してバイブス上げてこ🔥 [cite: 2025-12-20]")

url = st.text_input("🔍 YouTube URLを貼ってね", value="https://www.youtube.com/watch?v=jfKfPfyJRdk")

if url:
    st.video(url)
    st.success("再生開始！爆益の予感しかしない💖 [cite: 2025-11-30]")
