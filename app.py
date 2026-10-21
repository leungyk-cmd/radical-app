import base64
import io
from openai import OpenAI
from PIL import Image
import streamlit as st

st.set_page_config(page_title="部首識別助手", page_icon="🈛", layout="centered")

st.title("🈛 部首識別助手 (診斷模式)")
st.write("請拍照或上傳包含漢字的圖片：")

api_key = st.secrets.get("GITHUB_TOKEN", "")
if not api_key:
  api_key = st.text_input("請輸入 GitHub Token：", type="password")

if api_key:
  client = OpenAI(
      base_url="https://models.github.ai/inference",
      api_key=api_key.strip(),
  )

  img_file = st.camera_input("📷 拍照辨識") or st.file_uploader("📁 上傳圖片", type=["jpg", "jpeg", "png"])

  if img_file:
    image = Image.open(img_file).convert("RGB")
    image.thumbnail((800, 800))
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # 完全解除限制，用最自然的語氣詢問
    prompt_text = "請仔細看這張圖片，裡面寫了什麼中文字？請告訴我這個字的部首是什麼？"

    with st.spinner("正在測試 AI 視覺連線中..."):
      try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ],
            }],
        )

        content = response.choices[0].message.content
        st.success("✅ 辨識完成！AI 的原始回應如下：")
        st.write("---")
        st.info(content)

      except Exception as e:
        st.error(f"❌ 系統錯誤：{e}")
