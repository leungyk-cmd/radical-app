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
  client = OpenAI(
      base_url="https://models.github.ai/inference",
      api_key=api_key.strip(),
  )

  img_file = st.camera_input("📷 拍照辨識") or st.file_uploader(
      "📁 或上傳圖片檔案", type=["jpg", "jpeg", "png"]
  )

  if img_file:
    # 1. 轉為 PNG 高畫質無損格式，清晰保留繁體字筆畫
    image = Image.open(img_file).convert("RGB")
    image.thumbnail((1024, 1024))

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    prompt_text = (
        "這是一張中文漢字的照片。請辨識圖片中的字，並告訴我它的「部首」（繁體字）。\n【規則】請只輸出一個部首漢字（如：艹、女、木、水）。"
    )

    candidate_models = ["gpt-4o-mini", "gpt-4o", "Phi-3.5-vision-instruct"]

    with st.spinner("正在認真看圖辨識部首中..."):
      success = False
      radical_result = None

      for model_name in candidate_models:
        try:
          response = client.chat.completions.create(
              model=model_name,
              messages=[
                  {
                      "role": "system",
                      "content": (
                          "你是一位小學國語老師，專門辨識漢字並找出「部首」。"
                      ),
                  },
                  {
                      "role": "user",
                      "content": [
                          {
                              "type": "image_url",
                              "image_url": {
                                  "url": f"data:image/png;base64,{base64_image}"
                              },
                          },
                          {"type": "text", "text": prompt_text},
                      ],
                  },
              ],
              temperature=0.1,
              max_tokens=30,
          )

          content = (
              response.choices[0].message.content if response.choices else ""
          )
          if content:
            clean_text = (
                content.strip()
                .replace("#", "")
                .replace("*", "")
                .replace(".", "")
                .replace("`", "")
            )

            # 過濾掉非部首字詞
            if clean_text and clean_text.upper() not in [
                "OK",
                "OK.",
                "RECEIVED",
                "CONFIRMED",
                "YES",
                "NO",
            ]:
              radical_result = clean_text
              success = True
              break
        except Exception:
          continue

      st.write("---")
      if success and radical_result:
        st.subheader("辨識結果：")
        for r in radical_result.split("\n"):
          r_clean = r.strip()
          if r_clean:
            st.markdown(
                f'<div class="huge-font">{r_clean}</div>',
                unsafe_allow_html=True,
            )
      else:
        st.warning(
            "📷"
            " 圖片辨識較不明顯，請試著把字拍得更清晰、光源更充足一些，再重新嘗試一次喔！"
        )
