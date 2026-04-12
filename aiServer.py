from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import base64
import json
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY        = os.getenv("OPENAI_API_KEY")
GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")

VISION_API_URL = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_API_KEY}"


# ─────────────────────────────────────────
#  HTML 서빙
# ─────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# ─────────────────────────────────────────
#  OCR API
# ─────────────────────────────────────────

@app.route("/api/ocr", methods=["POST"])
def ocr():
    if "image" not in request.files:
        return jsonify({"error": "이미지 파일이 없습니다."}), 400

    image_data   = request.files["image"].read()
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    payload = {
        "requests": [{
            "image": {"content": image_base64},
            "features": [{"type": "TEXT_DETECTION"}],
            "imageContext": {"languageHints": ["ko", "en"]},
        }]
    }

    response = requests.post(VISION_API_URL, json=payload)
    if response.status_code != 200:
        return jsonify({"error": f"Google API 오류: {response.text}"}), 500

    try:
        annotations = response.json()["responses"][0].get("textAnnotations", [])
        if not annotations:
            return jsonify({"text": "", "message": "텍스트를 찾을 수 없습니다."})
        return jsonify({"text": annotations[0]["description"]})
    except (KeyError, IndexError) as e:
        return jsonify({"error": f"응답 파싱 오류: {str(e)}"}), 500


# ─────────────────────────────────────────
#  알람 파싱 API
# ─────────────────────────────────────────

@app.route("/api/parse-alarm", methods=["POST"])
def parse_alarm():
    body     = request.get_json()
    ocr_text = body.get("text", "")

    if not ocr_text:
        return jsonify({"error": "텍스트가 없습니다."}), 400

    prompt = f"""다음은 약 봉투(또는 처방전)에서 OCR로 추출한 텍스트야.
텍스트에 등장하는 모든 의약품을 찾아 각각의 복약 정보를 추출해 아래 형식의 JSON만 반환해.
다른 말은 절대 하지 마.

반환 형식:
{{
  "drugs": [
    {{
      "drugName": "타이레놀 500mg",
      "times": ["08:00", "12:00", "18:00"],
      "dose": "1정",
      "instruction": "식후 30분"
    }},
    {{
      "drugName": "가스모틴 5mg",
      "times": ["08:00", "12:00", "18:00"],
      "dose": "1정",
      "instruction": "식전 30분"
    }}
  ]
}}

[drugName 추출 규칙]
- 의약품(약) 이름만 추출해. 병원명, 약국명, 환자명, 날짜, 주소는 절대 포함하지 마.
- 약 이름은 한글/영문 제품명으로 표기되고, "정", "캡슐", "mg", "ml" 같은 단위가 붙는 경우가 많아.
- 약 이름을 찾을 수 없으면 "복약 알람"으로 써.

[times 추출 규칙 - 각 약마다 개별 적용]
- "1일 3회" → ["08:00", "12:00", "18:00"]
- "1일 2회" → ["08:00", "18:00"]
- "1일 1회" → ["08:00"]
- "취침 전" → ["22:00"]
- 명시된 시각이 있으면 그 시각을 사용해 (예: "오전 8시" → "08:00")
- 해당 약의 복용 정보를 찾을 수 없으면 ["08:00"]으로 설정해.
- 약마다 복용 횟수/시간이 다를 수 있으니 반드시 개별적으로 추출해.

[기타 규칙]
- 약이 1개뿐이어도 반드시 drugs 배열에 담아서 반환해.
- 약을 하나도 찾지 못한 경우에만 drugs를 빈 배열로 반환해.

OCR 텍스트:
{ocr_text}

JSON:"""

    raw = ""
    try:
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "max_tokens": 600,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        if not res.ok:
            return jsonify({"error": f"OpenAI 오류: {res.text}"}), 500

        raw    = res.json()["choices"][0]["message"]["content"].strip()
        raw    = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        return jsonify(parsed)

    except json.JSONDecodeError:
        return jsonify({"error": "AI 응답을 JSON으로 파싱할 수 없습니다.", "raw": raw}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────
#  챗봇 대화 API
# ─────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    body     = request.get_json()
    messages = body.get("messages", [])

    if not messages:
        return jsonify({"error": "메시지가 없습니다."}), 400

    system_msg = {
        "role": "system",
        "content": (
            "당신은 '약쉬워' 앱의 친근한 약사 AI 챗봇입니다. "
            "의약품 정보, 복약 지도, 건강 관련 질문에 답변해주세요. "
            "항상 한국어로 답변하고, 의학적 진단은 제공하지 마세요. "
            "쉬운 말로 3~5문장으로 간결하게 답변하세요. "
            "마지막에 '더 궁금한 점이 있으면 언제든 물어보세요 😊' 한 마디를 추가하세요."
        )
    }

    try:
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "max_tokens": 500,
                "messages": [system_msg] + messages[-10:]
            }
        )
        if not res.ok:
            return jsonify({"error": res.json().get("error", {}).get("message", "OpenAI 오류")}), 500

        result = res.json()["choices"][0]["message"]["content"].strip()
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("✅ 약쉬워 서버 시작: http://localhost:5000")
    app.run(debug=True, port=5000)
