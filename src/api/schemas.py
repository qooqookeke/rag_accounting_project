from typing import List, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(..., description="사용자의 세무/연말정산 질문", example="월세 세액공제 조건과 한도가 어떻게 돼?")
    top_k: int = Field(3, description="참고할 상위 문서 개수", ge=1, le=10)
    category_filter: Optional[str] = Field(default=None, description="특정 공제 카테고리 필터링 (생략 가능, 예: 월세액세액공제)", example=None)

class SourceItem(BaseModel):
    rank: int = Field(..., description="유사도 순위")
    title: str = Field(..., description="문서/조문 제목")
    category: str = Field(..., description="공제 카테고리")
    law_ref: str = Field(..., description="법령 조문 출처")
    score: float = Field(..., description="코사인 유사도 점수 (0~1)")
    text_snippet: str = Field(..., description="본문 요약 미리보기")

class QueryResponse(BaseModel):
    query: str = Field(..., description="입력된 질문")
    answer: str = Field(..., description="세무 특화 LLM이 생성한 최종 답변")
    sources: List[SourceItem] = Field(..., description="답변에 인용된 법적 근거 문서 목록 (Citation)")
    source_count: int = Field(..., description="인용된 문서 수")

class HealthResponse(BaseModel):
    status: str
    version: str
    collection_name: str
    indexed_documents: int
