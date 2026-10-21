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
    .status-info {
        font-size: 14px;
        color: #7f8c8d;
        text-align: center;
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
    image = Image.open(img_file).convert("RGB")
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=95)
    base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # 強化 Prompt：加入 Few-shot 範例與強烈的負向約束，防止 AI 回傳 "OK"
    system_prompt = """你是一個專為小學一年級學生設計的繁體中文「部首識別助手」。
任務：請識別圖片中的漢字，並只輸出該字的「部首」（繁體字）。

【嚴格規則】
1. 只輸出部首字（例如：艹、木、水、女），絕對不要輸出任何其他文字、拼音、標點符號。
2. 嚴禁輸出 "OK"、"Received"、"收到" 或任何英文說明！
3. 若有多個字，請逐行輸出各字的部首。

【範例】
- 若圖片字為「花」，請輸出：艹
- 若圖片字為「媽」，請輸出：女
- 若圖片字為「草」，請輸出：艹
"""

    candidate_models = [
        "gpt-4o-mini",
        "gpt-4o",
    ]

    with st.spinner("正在辨識部首中..."):
      success = False
      last_error = None

      for model_name in candidate_models:
        try:
          response = client.chat.completions.create(
              model=model_name,
              messages=[
                  {"role": "system", "content": system_prompt},
                  {
                      "role": "user",
                      "content": [
                          {"type": "text", "text": "請辨識這張圖片中漢字的部首："},
                          {
                              "type": "image_url",
                              "image_url": {
                                  "url": f"data:image/jpeg;base64,{base64_image}"
                              },
                          },
                      ],
                  },
              ],
              temperature=0.1,
          )

          response_text = parse_response_text(response).strip()

          # 若模型依然回傳 "OK" 等確認詞，觸發例外機制切換下一個模型
          if response_text.upper() in ["OK", "OK.", "RECEIVED", "RECEIVED.", ""]:
            raise ValueError(
                f"模型 {model_name} 誤回傳確認詞 ({response_text})，自動切換備用模型重新分析"
            )

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
