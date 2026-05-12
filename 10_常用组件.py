import streamlit as st
import pandas as pd

st.title('欢迎来到我的个人网站')
st.header('成都理工大学数字智慧大屏')
st.subheader('数媒专业')
st.divider()

name =st.text_input('请输入你的名字')
st.write(name)
st.divider()

st.button('确定')
st.button('确定',type='primary')

st.divider()


