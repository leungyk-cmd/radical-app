import base64
import io
import json
import re
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
    return response

  if hasattr(response, "choices") and response.choices:
    content = response.choices[0].message.content
    return content if content is not None else ""

  if isinstance(response, dict):
    return response.get("choices", [{}])[0].get("message", {}).get("content", "")

  return str(response) if response else ""


# 安全提取部首的強健函式
def extract_radical_safe(raw_text):
  if not raw_text or not raw_text.strip():
    return None

  # 1. 清除可能包覆在外的 Markdown 語法 (```json ... ```)
  clean_text = (
      re.sub(r"```(?:json)?", "", raw_text, flags=re.IGNORECASE)
      .replace("```", "")
      .strip()
  )

  # 2. 嘗試解析 JSON
  try:
    data = json.loads(clean_text)
    if isinstance(data, dict):
      result = data.get("radical") or data.get("部首") or data.get("result")
      if result:
        return str(result).strip()
  except Exception:
    pass

  # 3. 若 JSON 解析失敗，直接採用純文字（過濾掉 OK、RECEIVED 等無效詞）
  if clean_text.upper() in ["OK", "OK.", "RECEIVED", "CONFIRMED", "YES", ""]:
    return None

  return clean_text


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
    # 讀取圖片並壓縮
    image = Image.open(img_file).convert("RGB")
    image.thumbnail((500, 500))

    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=80)
    base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    prompt_text = (
        "請辨識這張圖片中的繁體中文漢字，並找出該字的「部首」。"
        '請以 JSON 格式輸出，例如：{"radical": "艹"}'
    )

    candidate_models = ["gpt-4o-mini", "gpt-4o"]

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
              max_tokens=100,
          )

          raw_text = parse_response_text(response)
          radical_result = extract_radical_safe(raw_text)

          if not radical_result:
            raise ValueError(
                f"模型 {model_name} 回傳無法解析的內容：{raw_text}"
            )

          clean_r = (
              radical_result.replace("#", "")
              .replace("*", "")
              .replace(".", "")
              .replace("`", "")
          )

          st.write("---")
          st.subheader("辨識結果：")
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
