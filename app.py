import base64
import io
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    ImageContentItem,
    ImageUrl,
    SystemMessage,
    TextContentItem,
    UserMessage,
)
from azure.core.credentials import AzureKeyCredential
from PIL import Image
import streamlit as st

st.set_page_config(page_title="部首識別助手", page_icon="🈛", layout="centered")

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

st.title("🈛 部首識別助手")
st.write("請拍照或上傳包含漢字的圖片：")

api_key = st.secrets.get("GITHUB_TOKEN", "")
if not api_key:
    api_key = st.text_input("請輸入 GitHub Token：", type="password")

if api_key:
    # 改用微軟官方原生 SDK 與最新的 GitHub Endpoint
    client = ChatCompletionsClient(
        endpoint="https://models.github.ai/inference",
        credential=AzureKeyCredential(api_key.strip()),
    )

    img_file = st.camera_input("📷 拍照辨識") or st.file_uploader("📁 上傳圖片", type=["jpg", "jpeg", "png"])

    if img_file:
        image = Image.open(img_file).convert("RGB")
        image.thumbnail((800, 800))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

        prompt = "你是一個部首辨識小助手。請辨識圖片中的漢字，並只輸出該字的「部首」（例如：艹、水、木）。絕對不要輸出其他字。"

        with st.spinner("正在以原生 SDK 連線辨識中..."):
            try:
                response = client.complete(
                    messages=[
                        SystemMessage(content=prompt),
                        UserMessage(content=[
                            TextContentItem(text="請告訴我這個字的部首是什麼？"),
                            ImageContentItem(
                                image_url=ImageUrl(url=f"data:image/jpeg;base64,{base64_image}")
                            ),
                        ]),
                    ],
                    model="gpt-4o",
                    temperature=0.1,
                )

                content = response.choices[0].message.content.strip()
                clean_r = content.replace("#", "").replace("*", "").replace("`", "")
                
                st.write("---")
                st.subheader("辨識結果：")
                st.markdown(f'<div class="huge-font">{clean_r}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"系統錯誤：{e}")
