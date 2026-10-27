import streamlit as st
from google import genai
from google.genai import types

# 頁面標題與佈局設定
st.set_page_config(page_title="部首識別助手", page_icon="🈛", layout="centered")

# 自訂 CSS 巨型字體
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

st.title("部首識別助手 (Google Gemini 版)")
st.write("請拍照或上傳包含漢字的圖片：")

# 讀取 Gemini API Key
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    api_key = st.text_input("請輸入 Google Gemini API Key：", type="password")

if api_key:
    # 初始化 Gemini 客戶端
    client = genai.Client(api_key=api_key.strip())

    img_file = st.camera_input("📷 拍照辨識") or st.file_uploader("📁 或上傳圖片檔案", type=["jpg", "jpeg", "png"])

    if img_file:
        # 讀取圖片的二進位資料
        image_bytes = img_file.getvalue()

        # 判斷圖片格式以設定對應的 MIME 類型
        mime_type = "image/jpeg"
        if img_file.name.lower().endswith(".png"):
            mime_type = "image/png"

        prompt = """
        你是一個專為小學一年級學生設計的繁體中文「部首識別助手」。
        請仔細看這張圖片裡的漢字，並找出它的「部首」。
        
        【嚴格規則】
        1. 只需要輸出該字的部首。
        2. 如果是變形部首（例如：艹、氵、扌、灬），請一律輸出「字典裡的正式部首本字」（例如：艸、水、手、火）。
        3. 絕對不要輸出任何解釋、拼音或標點符號。
        """

        with st.spinner("正在使用 Google Gemini 視覺模型辨識中..."):
            try:
                # 呼叫 Gemini 3.8 Flash 模型
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=mime_type,
                        ),
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=15,
                    )
                )

                # 提取並清理模型輸出的文字
                content = response.text.strip()
                clean_r = content.replace("#", "").replace("*", "").replace("`", "").replace(".", "")

                st.write("---")
                st.subheader("辨識結果：")
                st.markdown(f'<div class="huge-font">{clean_r}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ 辨識發生錯誤：{e}")
