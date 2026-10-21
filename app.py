import base64
import io
from openai import OpenAI
from PIL import Image
import streamlit as st

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

st.title("🈛 部首識別助手 (Groq 極速版)")
st.write("請拍照或上傳包含漢字的圖片：")

# 讀取 Groq API Key
api_key = st.secrets.get("GROQ_API_KEY", "")

if not api_key:
    api_key = st.text_input("請輸入 Groq API Key (gsk_...)：", type="password")

if api_key:
    # 指向 Groq 的 API 伺服器
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key.strip(),
    )

    img_file = st.camera_input("📷 拍照辨識") or st.file_uploader("📁 或上傳圖片檔案", type=["jpg", "jpeg", "png"])

    if img_file:
        # 讀取圖片並進行適度壓縮，以符合 API 傳輸限制
        image = Image.open(img_file).convert("RGB")
        image.thumbnail((800, 800))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

        prompt = """
        你是一個專為小學一年級學生設計的繁體中文「部首識別助手」。
        請仔細看這張圖片裡的漢字，並找出它的「部首」。
        只需要輸出該字的部首（例如：艹、水、木、女）。
        絕對不要輸出任何解釋、拼音或標點符號。
        """

        with st.spinner("正在使用 Groq 視覺模型極速辨識中..."):
            try:
                response = client.chat.completions.create(
                   model="llama-3.2-90b-vision",  # 如果此名稱依然報錯，請改填 "llama-3.2-11b-vision-preview"
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }],
                    temperature=0.1,
                    max_tokens=15,
                )

                # 提取並清理模型輸出的文字
                content = response.choices[0].message.content.strip()
                clean_r = content.replace("#", "").replace("*", "").replace("`", "").replace(".", "")

                st.write("---")
                st.subheader("辨識結果：")
                st.markdown(f'<div class="huge-font">{clean_r}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ 辨識發生錯誤：{e}")
