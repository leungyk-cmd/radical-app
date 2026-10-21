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

st.title("🈛 部首識別助手")
st.write("請拍照或上傳包含漢字的圖片：")

# 讀取 GitHub Token
api_key = st.secrets.get("GITHUB_TOKEN", "")

if not api_key:
  api_key = st.text_input(
      "請輸入 GitHub Token (ghp_...)：", type="password"
  )

if api_key:
  # 使用 GitHub Models 最新官方正式 Endpoint
  client = OpenAI(
      base_url="https://models.github.ai/inference",
      api_key=api_key.strip(),
  )

  img_file = st.camera_input("📷 拍照辨識") or st.file_uploader(
      "📁 或上傳圖片檔案", type=["jpg", "jpeg", "png"]
  )

  if img_file:
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

    # 備援模型清單
    candidate_models = [
        "gpt-4o-mini",
        "gpt-4o",
        "Phi-3.5-vision-instruct",
    ]

    with st.spinner("正在辨識部首中..."):
      success = False
      last_error = None

      for model_name in candidate_models:
        try:
          response = client.chat.completions.create(
              model=model_name,
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
          )

          response_text = response.choices[0].message.content.strip()
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
          success = True
          break
        except Exception as e:
          last_error = e
          continue

      if not success:
        st.error(f"辨識發生錯誤：{last_error}")
