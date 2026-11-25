import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import chromadb
from chromadb.config import Settings as ChromaSettings
from src.config import settings
from src.core.chunker import YetaChunker
from src.core.embedder import YetaEmbedder

class YetaIndexer:
    """
    청킹된 연말정산 문서들을 임베딩하여 로컬 ChromaDB에 영구 저장하는 인덱서
    """
    COLLECTION_NAME = "yeta_knowledge"

    def __init__(self):
        # 로컬 폴더(data/chroma_db)에 데이터가 영구 보존되도록 PersistentClient 사용
        self.chroma_client = chromadb.PersistentClient(
            path=str(settings.CHROMA_PERSIST_DIR)
        )
        self.embedder = YetaEmbedder()
        self.chunker = YetaChunker()

    def build_index(self, reset: bool = True):
        """데이터를 청킹하고 임베딩하여 ChromaDB에 적재합니다."""
        if reset:
            try:
                self.chroma_client.delete_collection(self.COLLECTION_NAME)
                print(f"🗑️ 기존 컬렉션('{self.COLLECTION_NAME}') 초기화 완료")
            except Exception:
                pass

        # 코사인 유사도(cosine distance) 기반 컬렉션 생성
        collection = self.chroma_client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        # 1. 청킹
        print("📄 1. 원본 문서 청킹 시작...")
        chunks = self.chunker.chunk_all_raw_data()
        print(f"   총 {len(chunks)}개 청크 생성 완료")

        # 2. 임베딩용 데이터 정제
        ids = [c["doc_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [
            {
                "title": c["title"],
                "category": c["category"],
                "law_ref": c["law_ref"],
                "source": c["source"]
            }
            for c in chunks
        ]

        # 3. 임베딩 벡터 생성
        print("🔢 2. 텍스트 임베딩 벡터 변환 중...")
        embeddings = self.embedder.embed_documents(texts)
        print("   임베딩 완료!")

        # 4. ChromaDB 적재
        print("💾 3. ChromaDB에 벡터 및 메타데이터 적재 중...")
        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        count = collection.count()
        print(f"🎉 [성공] 총 {count}개의 연말정산 지식 청크가 ChromaDB에 성공적으로 저장되었습니다!")
        print(f"   저장 위치: {settings.CHROMA_PERSIST_DIR}\n")


if __name__ == "__main__":
    indexer = YetaIndexer()
    indexer.build_index(reset=True)
