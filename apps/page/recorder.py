import streamlit as st


st.title("錄音機")

audio_value = st.audio_input("Record a voice message")
