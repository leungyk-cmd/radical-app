import base64
import io
import json
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


# 多重型態相容解析函式
def parse_response_text(response):
  if isinstance(response, str):
    try:
      data = json.loads(response)
      if isinstance(data, dict) and "choices" in data:
        return data["choices"][0]["message"]["content"]
    except Exception:
      pass
    return response

  if hasattr(response, "choices"):
    return response.choices[0].message.content

  if isinstance(response, dict):
    return response.get("choices", [{}])[0].get("message", {}).get("content", "")

  return str(response)


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
    # 讀取圖片並進行自動縮放壓縮 (解決 Base64 過大被 API 截斷問題)
    image = Image.open(img_file).convert("RGB")
    image.thumbnail((800, 800))  # 將圖片等比例縮放至 800px 以內

    buffered = io.BytesIO()
    image.save(
        buffered, format="JPEG", quality=85
    )  # 壓縮 JPEG 品質至 85%，降至約 50KB
    base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    prompt_text = (
        "圖片裡有一個繁體中文漢字，請找出該字的「部首」。"
        "【規則】請只輸出一個繁體字部首（如：艹、女、木、水），絕對不要輸出"
        ' "OK"、標點符號或任何說明文字。'
    )

    candidate_models = ["gpt-4o-mini", "gpt-4o"]

    with st.spinner("正在高速辨識部首中..."):
      success = False
      last_error = None

      for model_name in candidate_models:
        try:
          response = client.chat.completions.create(
              model=model_name,
              messages=[{
                  "role": "user",
                  "content": [
                      {"type": "text", "text": prompt_text},
                      {
                          "type": "image_url",
                          "image_url": {
                              "url": f"data:image/jpeg;base64,{base64_image}"
                          },
                      },
                  ],
              }],
              temperature=0.1,
              max_tokens=20,  # 強制限制輸出長度，防止多餘廢話
          )

          response_text = parse_response_text(response).strip()

          # 若模型依然回傳無效文字，觸發切換
          if response_text.upper() in [
              "OK",
              "OK.",
              "RECEIVED",
              "RECEIVED.",
              "",
          ]:
            raise ValueError(f"模型 {model_name} 回傳無效文字 ({response_text})")

          radicals = response_text.split("\n")

          st.write("---")
          st.subheader("辨識結果：")
          for r in radicals:
            clean_r = (
                r.strip()
                .replace("#", "")
                .replace("*", "")
                .replace(".", "")
                .replace("`", "")
            )
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
