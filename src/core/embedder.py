import sys
from pathlib import Path

# 프로젝트 루트 경로를 sys.path에 추가
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from typing import List
from sentence_transformers import SentenceTransformer
from src.config import settings

class YetaEmbedder:
    """
    텍스트를 다차원 의미 벡터(숫자 배열)로 변환하는 로컬 임베더
    - 모델: BAAI/bge-m3 (또는 설정된 한국어 임베딩 모델)
    - 완전 무료, 로컬 장비(CPU/MPS)에서 자립 구동
    """
    _instance = None

    def __new__(cls):
        # 모델을 매번 새로 로드하지 않고 메모리에 한 번만 올리는 싱글톤 패턴
        if cls._instance is None:
            cls._instance = super(YetaEmbedder, cls).__new__(cls)
            print(f"🔄 임베딩 모델 로딩 중... ({settings.EMBEDDING_MODEL_NAME})")
            try:
                # 1. 이미 다운로드된 로컬 캐시에서 오프라인 초고속 로드 시도
                cls._instance.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, local_files_only=True)
            except Exception:
                # 2. 로컬 캐시가 없는 경우 허깅페이스 허브에서 다운로드
                cls._instance.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            print("✅ 임베딩 모델 로드 완료!")
        return cls._instance

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """여러 문서 청크를 벡터 리스트로 변환합니다."""
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """사용자의 단일 질문을 벡터로 변환합니다."""
        embedding = self.model.encode(query, normalize_embeddings=True)
        return embedding.tolist()


if __name__ == "__main__":
    # 임베더 단독 테스트
    embedder = YetaEmbedder()
    test_text = "월세 세액공제 조건이 어떻게 되나요?"
    vector = embedder.embed_query(test_text)
    print(f"질문: '{test_text}'")
    print(f"변환된 벡터 차원 수: {len(vector)}차원")
    print(f"벡터 값 샘플 (앞 5개): {vector[:5]}")
