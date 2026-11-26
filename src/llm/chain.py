import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from typing import Dict, Any, Optional
import re
from src.config import settings
from src.core.retriever import YetaRetriever
from src.llm.client import YetaLLMClient
from src.llm.prompts import build_rag_prompt

class YetaRAGChain:
    """
    [질문 수신] -> [보안 가드레일 & 검색] -> [프롬프트 조립] -> [LLM 생성] -> [답변 및 출처 반환]
    전 과정을 관통하는 메인 RAG 파이프라인 (보안 및 비용 최적화 적용)
    """

    # 전형적인 프롬프트 인젝션 및 시스템 탈취 공격 패턴 정규식
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above)\s+instructions?",
        r"system\s*prompt",
        r"이전\s*(지시|명령|지침).*?(무시|취소)",
        r"(시스템|초기|내부)\s*(프롬프트|지시|규칙).*?(출력|알려|보여)",
        r"you\s+are\s+now",
        r"너는\s*이제부터",
        r"jailbreak",
        r"탈옥",
        r"dan\s+mode",
    ]

    def __init__(self):
        self.retriever = YetaRetriever()
        self.llm = YetaLLMClient()
        self.injection_regex = re.compile("|".join(self.INJECTION_PATTERNS), re.IGNORECASE)

    def run(self, query: str, top_k: int = 3, category_filter: Optional[str] = None) -> Dict[str, Any]:
        """사용자 질문에 대해 보안 검증, 검색 및 답변을 생성합니다."""
        clean_q = query.strip()

        # 🛡️ 1차 가드레일: 명시적 프롬프트 인젝션 패턴 사전 차단 (LLM 호출 X -> 비용 0원)
        if self.injection_regex.search(clean_q):
            return {
                "query": query,
                "answer": "🚨 [보안 안내] 시스템 보안 정책에 위배되거나 비정상적인 프롬프트 명령어가 감지되어 요청이 차단되었습니다. 연말정산 관련 정상적인 세법 질문을 입력해 주세요.",
                "sources": [],
                "source_count": 0
            }

        # 2. 벡터 검색 수행
        retrieved_docs = self.retriever.search(
            query=clean_q,
            top_k=top_k,
            category_filter=category_filter
        )

        # 🛡️ 2차 가드레일: 주제 이탈(Out-of-Scope) 차단 (유사도 임계치 미달 시 LLM 호출 X -> 비용 0원)
        # 연말정산과 전혀 상관없는 질문(주식, 코딩, 맛집, 날씨 등)은 Top-1 유사도가 매우 낮음
        top_score = retrieved_docs[0]["score"] if retrieved_docs else 0.0
        if not retrieved_docs or top_score < settings.SIMILARITY_THRESHOLD:
            return {
                "query": query,
                "answer": (
                    "죄송합니다. 저는 **'근로소득 연말정산' 전문 상담 챗봇**입니다.\n\n"
                    "입력하신 질문은 연말정산 공제 요건 및 세법 규정과 연관성이 낮아 답변드릴 수 없습니다. "
                    "월세액, 의료비, 교육비, 신용카드, 인적공제 등 연말정산과 관련된 내용을 질문해 주세요!"
                ),
                "sources": [],
                "source_count": 0
            }

        # 3. 프롬프트 조립
        rag_prompt = build_rag_prompt(query=clean_q, context_documents=retrieved_docs)

        # 4. LLM 답변 생성 (3차 가드레일: TAX_ADVISOR_SYSTEM_PROMPT 적용)
        llm_answer = self.llm.generate_response(rag_prompt)

        # 5. 출처 메타데이터 정리 (Citation)
        sources = [
            {
                "rank": i + 1,
                "title": doc["title"],
                "category": doc["category"],
                "law_ref": doc["law_ref"],
                "score": doc["score"],
                "text_snippet": doc["text"][:150] + "..."
            }
            for i, doc in enumerate(retrieved_docs)
        ]

        return {
            "query": query,
            "answer": llm_answer,
            "sources": sources,
            "source_count": len(sources)
        }


if __name__ == "__main__":
    chain = YetaRAGChain()
    test_q = "월세 세액공제 받으려면 연봉 얼마 이하여야 해?"
    print(f"\n🚀 [RAG 체인 단독 테스트] 질문: {test_q}\n")
    result = chain.run(test_q)
    
    print("=" * 60)
    print("💬 [AI 답변]:\n", result["answer"])
    print("=" * 60)
    print("📚 [참고한 법적 근거 (Citation)]:")
    for s in result["sources"]:
        print(f" - [{s['rank']}위 ({s['score']*100:.1f}%)] {s['law_ref']} ({s['title']})")
