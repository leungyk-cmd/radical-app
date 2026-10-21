import base64
import io
import requests
from PIL import Image
import streamlit as st

st.set_page_config(page_title="部首識別助手", page_icon="🈛", layout="centered")

st.markdown(
    """
    <style>
    .huge-font import base64
import io
import requests
from PIL import Image
import streamlit as st

st.set_page_config(page_title="部首識別助手", page_icon="🈛", layout="centered")

st.title("🈛 部首識別助手 (終極除錯模式)")
st.write("請拍照或上傳包含漢字的圖片：")

api_key = st.secrets.get("GITHUB_TOKEN", "")
if not api_key:
    api_key = st.text_input("請輸入 GitHub Token：", type="password")

if api_key:
    img_file = st.camera_input("📷 拍照辨識") or st.file_uploader("📁 上傳圖片", type=["jpg", "jpeg", "png"])

    if img_file:
        image = Image.open(img_file).convert("RGB")
        image.thumbnail((800, 800))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

        prompt = "你是一個部首辨識小助手。請辨識圖片中的漢字，並只輸出該字的「部首」（例如：艹、水、木）。絕對不要輸出其他字。"

        with st.spinner("正在探測伺服器底層回應..."):
            headers = {
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
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
                    }
                ],
                "temperature": 0.1
            }

            try:
                response = requests.post(
                    "https://models.github.ai/inference/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )

                st.write("---")
                st.subheader("🔍 伺服器底層探測結果：")
                st.info(f"**HTTP 狀態碼**：{response.status_code}")
                st.warning(f"**原始回傳內容**：\n{response.text if response.text else '(伺服器回傳完全空白)'}")

            except Exception as e:
                st.error(f"❌ 網路請求發生例外錯誤：{e}")
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
    img_file = st.camera_input("📷 拍照辨識") or st.file_uploader("📁 上傳圖片", type=["jpg", "jpeg", "png"])

    if img_file:
        # 圖片處理
        image = Image.open(img_file).convert("RGB")
        image.thumbnail((800, 800))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

        prompt = "你是一個部首辨識小助手。請辨識圖片中的漢字，並只輸出該字的「部首」（例如：艹、水、木）。絕對不要輸出其他字。"

        with st.spinner("正在透過原生 HTTP 協定連線中..."):
            # 準備直接發送給 GitHub API 的資料
            headers = {
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
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
                    }
                ],
                "temperature": 0.1
            }

            try:
                # 直接對官方端點發起 POST 請求
                response = requests.post(
                    "https://models.github.ai/inference/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )

                # 判斷 HTTP 狀態碼
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    clean_r = content.replace("#", "").replace("*", "").replace("`", "")
                    
                    st.write("---")
                    st.subheader("辨識結果：")
                    st.markdown(f'<div class="huge-font">{clean_r}</div>', unsafe_allow_html=True)
                else:
                    # 如果失敗，直接把 GitHub 伺服器的原始阻擋原因印出來
                    st.error(f"❌ GitHub 伺服器拒絕連線 (錯誤碼 {response.status_code})：\n{response.text}")

            except Exception as e:
                st.error(f"❌ 本地網路錯誤：{e}")
