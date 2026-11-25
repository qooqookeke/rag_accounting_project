import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.config import settings
from google import genai

client = genai.Client(api_key=settings.GEMINI_API_KEY)

test_candidates = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest"
]

print("🧪 최신 Gemini 모델 응답 테스트 시작...")
for cand in test_candidates:
    try:
        resp = client.models.generate_content(
            model=cand,
            contents="안녕하세요. 간단히 한 문장으로 인사해 주세요."
        )
        if resp and resp.text:
            print(f"🎉 성공! 작동하는 모델: [{cand}] -> 응답: {resp.text.strip()}")
            break
    except Exception as e:
        print(f"❌ 실패 [{cand}]: {e}")
