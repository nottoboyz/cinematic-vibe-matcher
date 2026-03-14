import streamlit as st
import pandas as pd

st.title("🎬 ทดสอบ Streamlit")
st.header("นี่คือ Header")
st.write("นี่คือข้อความธรรมดา — write() ใส่อะไรก็ได้เลย")

name = st.text_input("🎬 ทดสอบ Streamlit")
k = st.slider("จำนวนผลลัพธ์", min_value=1, max_value=10, value=5)

st.write(f"คุณพิมพ์ : {name}")
st.write(f"ต้องการ: {k} ผลลัพธ์")

if st.button("ค้นหา"):
    st.write(f"🔍 กำลังค้นหา '{name}' จำนวน {k} ผลลัพธ์")

df = pd.DataFrame({
    "เพลง": ["Song A", "Song B", "Song C"],
    "Score": [0.95, 0.87, 0.76]
})
st.dataframe(df.head(k))
st.bar_chart(df.set_index("เพลง"))