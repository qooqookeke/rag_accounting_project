import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.api.schemas import QueryRequest, QueryResponse, HealthResponse
from src.llm.chain import YetaRAGChain

# FastAPI 인스턴스 생성
app = FastAPI(
    title="🏛️ Yeta-RAG API (연말정산 세무 지식 엔진)",
    description="국세청 연말정산 안내서 및 소득세법 조문 기반의 근거 인용(Citation) 세무 상담 API",
    version="1.0.0"
)

# 웹사이트/위젯 어디서나 호출 가능하도록 CORS 전면 개방
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG 체인 인스턴스 (서버 시작 시 1회 초기화)
rag_chain = YetaRAGChain()

@app.get("/", summary="API 루트 안내")
def read_root():
    return {
        "message": "🏛️ Yeta-RAG 연말정산 전문 API 서버가 정상 동작 중입니다.",
        "docs_url": "/docs",
        "health_check": "/health"
    }

@app.get("/health", response_model=HealthResponse, summary="시스템 헬스체크")
def health_check():
    try:
        count = rag_chain.retriever.collection.count()
        return {
            "status": "healthy",
            "version": "1.0.0",
            "collection_name": rag_chain.retriever.COLLECTION_NAME,
            "indexed_documents": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@app.post("/api/v1/chat", response_model=QueryResponse, summary="연말정산 세무 상담 및 근거 인용 답변")
@app.post("/api/v1/query", response_model=QueryResponse, summary="연말정산 세무 상담 (하위 호환 alias)")
def chat_with_tax_rag(request: QueryRequest):
    """
    사용자의 질문을 받아 관련 세법 조문/해설서를 검색한 뒤,
    정확한 법적 근거와 함께 LLM 답변을 생성하여 반환합니다.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="질문 내용을 입력해 주세요.")

    try:
        result = rag_chain.run(
            query=request.query,
            top_k=request.top_k,
            category_filter=request.category_filter
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG 파이프라인 처리 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
