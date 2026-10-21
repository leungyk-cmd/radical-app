import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Groq 模型掃描器", layout="centered")
st.title("🔍 Groq 模型掃描器")

api_key = st.secrets.get("GROQ_API_KEY", "")
if not api_key:
    api_key = st.text_input("請輸入 Groq API Key：", type="password")

if api_key:
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key.strip(),
    )
    
    with st.spinner("正在向 Groq 伺服器查詢最新的模型清單..."):
        try:
            models = client.models.list()
            # 篩選出名稱中包含 "vision" 或 "llama-3.2" 的模型
            vision_models = [m.id for m in models.data if "vision" in m.id.lower() or "3.2" in m.id.lower()]
            
            st.success("✅ 查詢成功！目前您帳號可用的最新視覺模型如下：")
            for m in vision_models:
                st.code(m)
                
        except Exception as e:
            st.error(f"查詢發生錯誤：{e}")
