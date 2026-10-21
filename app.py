import streamlit as st
from groq import Groq
from PIL import Image
import base64
import io

# 頁面標題與佈局設定
st.set_page_config(page_title="部首識別助手", page_icon="", layout="centered")

# 自訂 CSS 樣式：將部首字體放大到極大，並置中顯示
st.markdown("""
    <style>
    .huge-font {
        font-size: 130px !important;
        font-weight: bold;
        color: #2C3E50;
        text-align: center;
        line-height: 1.2;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.title(" 部首識別助手")
st.write("請拍照或上傳包含漢字的圖片：")

# 從系統設定讀取 API Key
api_key = st.secrets.get("GROQ_API_KEY", "")

if not api_key:
    api_key = st.text_input("請輸入 Groq API Key (gsk_...)：", type="password")

if api_key:
    client = Groq(api_key=api_key)

    # 提供「拍照」與「上傳圖片」雙功能
    img_file = st.camera_input("📷 拍照辨識") or st.file_uploader("📁 或上傳圖片檔案", type=["jpg", "jpeg", "png"])

    if img_file:
        # 讀取圖片並轉為 RGB 格式
        image = Image.open(img_file).convert("RGB")
        
        # 將圖片轉換為 Base64 編碼，供 Groq API 讀取
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        prompt = """
        你是一個專為小學一年級學生設計的繁體中文「部首識別助手」。
        請識別圖片中的文字，並找出該字的「部首」。
        只需要輸出該字或該些字的部首，絕對不要添加任何解釋、拼音或標點符號。
        若有多個字，請逐行輸出部首。
        """

        with st.spinner("正在高速辨識部首中..."):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                    },
                                },
                            ],
                        }
                    ],
                    model="llama-3.2-90b-vision-preview",
                    temperature=0.1,
                )
                
                response_text = chat_completion.choices[0].message.content.strip()
                radicals = response_text.split("\n")

                st.write("---")
                st.subheader("辨識結果：")
                for r in radicals:
                    clean_r = r.strip().replace("#", "").replace("*", "")
                    if clean_r:
                        # 以 CSS 巨型字體呈現部首
                        st.markdown(f'<div class="huge-font">{clean_r}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"辨識發生錯誤：{e}")
