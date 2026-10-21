import base64
import io
from groq import Groq
from PIL import Image
import requests
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

api_key = st.secrets.get("GROQ_API_KEY", "")

if not api_key:
  api_key = st.text_input("請輸入 Groq API Key (gsk_...)：", type="password")


# 運用 Groq 的 /v1/models API 自動尋找可用的 Vision 模型
def get_active_groq_vision_model(key):
  try:
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      models_data = response.json().get("data", [])
      # 篩選出 ID 包含 "vision" 且狀態開啟的模型
      vision_models = [
          m["id"] for m in models_data if "vision" in m["id"].lower()
      ]
      if vision_models:
        return vision_models[0]  # 自動取得第一個可用的視覺模型
  except Exception:
    pass
  return None


if api_key:
  client = Groq(api_key=api_key)

  img_file = st.camera_input("📷 拍照辨識") or st.file_uploader(
      "📁 或上傳圖片檔案", type=["jpg", "jpeg", "png"]
  )

  if img_file:
    # 自動向 Groq 查詢最新的 Vision 模型 ID
    active_vision_model = get_active_groq_vision_model(api_key)

    if not active_vision_model:
      st.error("Groq 目前暫無開啟中的 Vision (圖片辨識) 模型，請稍後再試。")
    else:
      image = Image.open(img_file).convert("RGB")
      buffered = io.BytesIO()
      image.save(buffered, format="JPEG")
      base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

      prompt = """
            你是一個專為小學一年級學生設計的繁體中文「部首識別助手」。
            請識別圖片中的文字，並找出該字的「部首」。
            只需要輸出該字或該些字的部首，絕對不要添加任何解釋、拼音或標點符號。
            若有多個字，請逐行輸出部首。
            """

      with st.spinner(f"正在透過 ({active_vision_model}) 辨識部首中..."):
        try:
          chat_completion = client.chat.completions.create(
              messages=[{
                  "role": "user",
                  "content": [
                      {"type": "text", "text": prompt},
                      {
                          "type": "image_url",
                          "image_url": {
                              "url": f"data:image/jpeg;base64,{base64_image}"
                          },
                      },
                  ],
              }],
              model=active_vision_model,  # 動態使用查詢到的模型名稱
              temperature=0.1,
          )

          response_text = (
              chat_completion.choices[0].message.content.strip()
          )
          radicals = response_text.split("\n")

          st.write("---")
          st.subheader("辨識結果：")
          for r in radicals:
            clean_r = r.strip().replace("#", "").replace("*", "")
            if clean_r:
              st.markdown(
                  f'<div class="huge-font">{clean_r}</div>',
                  unsafe_allow_html=True,
              )
        except Exception as e:
          st.error(f"辨識發生錯誤：{e}")
