import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from typing import List, Dict, Any, Optional
import chromadb
from src.config import settings
from src.core.embedder import YetaEmbedder

class YetaRetriever:
    """
    사용자의 자연어 질문을 받아 로컬 ChromaDB에서 가장 관련성이 높은 연말정산 청크를 검색하는 검색기
    """
    COLLECTION_NAME = "yeta_knowledge"

    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(
            path=str(settings.CHROMA_PERSIST_DIR)
        )
        self.collection = self.chroma_client.get_collection(name=self.COLLECTION_NAME)
        self.embedder = YetaEmbedder()

    def search(
        self,
        query: str,
        top_k: int = 3,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        질문과 가장 유사한 상위 K개의 문서를 반환합니다.
        - category_filter가 주어지면 해당 공제 카테고리만 메타데이터 필터링합니다.
        """
        # 1. 질문을 벡터로 변환
        query_vector = self.embedder.embed_query(query)

        # 2. 메타데이터 필터 조건 설정 (Swagger UI의 기본값 "string"이나 빈 문자열 방어)
        where_condition = None
        if category_filter and category_filter.strip().lower() not in ["", "string", "null", "none", "all", "전체"]:
            where_condition = {"category": category_filter.strip()}

        # 3. ChromaDB 유사도 검색
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_condition
        )

        # 3-1. 만약 필터 조건 때문에 결과가 0건이면, 필터를 풀고 전체에서 재검색 (Fallback)
        if (not results or not results["documents"] or len(results["documents"][0]) == 0) and where_condition:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=None
            )

        formatted_results = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]
            ids = results["ids"][0]

            for i in range(len(docs)):
                # 코사인 거리(distance)를 유사도 점수(0~1)로 변환: 1 - distance
                similarity_score = round(1.0 - dists[i], 4)
                formatted_results.append({
                    "id": ids[i],
                    "score": similarity_score,
                    "title": metas[i].get("title", ""),
                    "category": metas[i].get("category", ""),
                    "law_ref": metas[i].get("law_ref", ""),
                    "source": metas[i].get("source", ""),
                    "text": docs[i]
                })

        return formatted_results


if __name__ == "__main__":
    retriever = YetaRetriever()

    # 테스트해 볼 실제 세무 질문 3가지
    test_queries = [
        "총급여 6천만원인데 월세 세액공제 조건이랑 한도가 어떻게 돼?",
        "시력교정용 안경 맞춘 것도 연말정산에 포함돼?",
        "맞벌이 부부인데 자녀 공제는 남편이랑 아내 중에 누가 받아야 유리해?"
    ]

    for q in test_queries:
        print(f"\n==================================================")
        print(f"🔍 질문: '{q}'")
        print(f"==================================================")
        hits = retriever.search(q, top_k=2)
        for rank, hit in enumerate(hits, 1):
            print(f"[{rank}위] 유사도 점수: {hit['score']*100:.1f}% | 카테고리: {hit['category']} | 출처: {hit['law_ref']}")
            print(f"     제목: {hit['title']}")
            print(f"     내용 미리보기: {hit['text'][:120]}...\n")
