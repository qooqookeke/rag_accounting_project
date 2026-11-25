import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from typing import Dict, Any, Optional
from src.core.retriever import YetaRetriever
from src.llm.client import YetaLLMClient
from src.llm.prompts import build_rag_prompt

class YetaRAGChain:
    """
    [질문 수신] -> [ChromaDB 검색] -> [프롬프트 조립] -> [LLM 생성] -> [답변 및 출처 반환]
    전 과정을 관통하는 메인 RAG 파이프라인
    """
    def __init__(self):
        self.retriever = YetaRetriever()
        self.llm = YetaLLMClient()

    def run(self, query: str, top_k: int = 3, category_filter: Optional[str] = None) -> Dict[str, Any]:
        """사용자 질문에 대해 검색 및 답변을 생성합니다."""
        # 1. 벡터 검색 수행
        retrieved_docs = self.retriever.search(
            query=query,
            top_k=top_k,
            category_filter=category_filter
        )

        # 2. 프롬프트 조립
        rag_prompt = build_rag_prompt(query=query, context_documents=retrieved_docs)

        # 3. LLM 답변 생성
        llm_answer = self.llm.generate_response(rag_prompt)

        # 4. 출처 메타데이터 정리 (Citation)
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
