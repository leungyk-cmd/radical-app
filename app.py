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

st.title("部首識別助手")
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
        image_bytes = img_file.getvalue()
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
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        prompt
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=300,
                        # 關閉所有安全過濾機制
                        safety_settings=[
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                            types.SafetySetting(
                                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                                threshold=types.HarmBlockThreshold.BLOCK_NONE,
                            ),
                        ]
                    )
                )

                # 正常回傳文字時的處理
                if response.text:
                    content = response.text.strip()
                    clean_r = content.replace("#", "").replace("*", "").replace("`", "").replace(".", "")

                    st.write("---")
                    st.subheader("辨識結果：")
                    st.markdown(f'<div class="huge-font">{clean_r}</div>', unsafe_allow_html=True)
                else:
                    # 終極除錯機制：直接印出 API 拒絕回傳的真實原因
                    st.error("⚠️ 模型依然回傳為空！我們來看看它到底發生了什麼事：")
                    
                    if response.candidates:
                        finish_reason = response.candidates[0].finish_reason
                        st.warning(f"🔍 官方中斷原因代碼 (Finish Reason): {finish_reason}")
                        
                        if str(finish_reason) == "SAFETY":
                            st.info("💡 診斷：還是被安全機制擋下了！可能是圖片裡的筆畫太像某些敏感符號。")
                        elif str(finish_reason) == "MAX_TOKENS":
                            st.info("💡 診斷：字數限制設定太小，導致它還沒說完就被切斷了。")
                        else:
                            st.info("💡 診斷：未知的阻擋原因，請參考下方的原始資料。")
                    
                    # 將整包原始資料顯示在畫面上，方便排查
                    st.write("📦 原始回傳資料：")
                    st.write(response)

            except Exception as e:
                st.error(f"❌ 辨識發生錯誤：{e}")
