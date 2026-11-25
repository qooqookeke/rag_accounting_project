import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.config import settings
from src.llm.prompts import TAX_ADVISOR_SYSTEM_PROMPT

class YetaLLMClient:
    """
    LLM 추론 인터페이스 (최신 Gemini 3.x 세대 지원)
    - 2026년 최신 구글 모델: gemini-3.8-flash, gemini-3.7-flash, gemini-flash-latest
    """
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.provider = settings.LLM_PROVIDER.lower()
        self.client = None
        # 2026년 구글 AI 최신 활성 모델 목록 (우선순위 순서)
        self.target_models = [
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.5-flash",
            "gemini-flash-latest",
            "gemini-3-flash-preview",
            "gemini-3.1-pro-preview"
        ]
        self.active_model = self.target_models[0]
        self._init_client()

    def _init_client(self):
        if self.provider == "gemini":
            if self.api_key and self.api_key != "your_gemini_api_key_here":
                try:
                    from google import genai
                    self.client = genai.Client(api_key=self.api_key)
                    print(f"✅ Gemini API 클라이언트 초기화 완료! (타깃 모델: {self.active_model})")
                except Exception as e:
                    print(f"⚠️ Gemini 클라이언트 초기화 실패: {e}")
                    self.client = None
            else:
                self.client = None
                print("ℹ️ GEMINI_API_KEY 미설정 데모 모드")

    def generate_response(self, user_prompt: str) -> str:
        """프롬프트를 LLM에 전달하여 답변 텍스트를 생성합니다."""
        if self.client and self.provider == "gemini":
            last_error = None
            for model_name in self.target_models:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=user_prompt,
                        config={
                            "system_instruction": TAX_ADVISOR_SYSTEM_PROMPT,
                            "temperature": 0.2,
                        }
                    )
                    if response and response.text:
                        self.active_model = model_name
                        return response.text
                except Exception as e:
                    last_error = e
                    continue

            return f"[API 호출 오류] 지원 가능한 모델을 찾지 못했습니다: {str(last_error)}"

        # 데모 모드 응답
        return (
            "💡 [안내: 데모 모드 응답]\n\n"
            "현재 .env 파일에 유효한 Gemini API 키가 설정되지 않아 데모 요약을 반환합니다."
        )


if __name__ == "__main__":
    llm = YetaLLMClient()
    res = llm.generate_response("총급여 6천만원일 때 월세 공제 한도 알려줘")
    print("생성 결과:\n", res)
