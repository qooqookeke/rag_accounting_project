import re
import sys
from pathlib import Path

# 프로젝트 루트 경로를 sys.path에 추가하여 어디서든 실행 가능하게 설정
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from typing import List, Dict, Any
from src.config import settings

class YetaChunker:
    """
    연말정산 문서 특화 의미론적 청커(Semantic Chunker)
    - 글자 수 기반이 아닌, [조문] 및 [FAQ 항목] 단위로 온전하게 분할하여
      단서 조항이나 핵심 요건이 잘려나가는 것을 방지합니다.
    """

    def __init__(self):
        # [소득세법 제50조 ...], [조세특례제한법 ...], [2024 국세청 ...] 형태의 헤더 매칭 정규식
        self.header_pattern = re.compile(r"^\[(.*?)\]", re.MULTILINE)

    def chunk_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """단일 텍스트 파일을 읽어 의미 단위 청크 리스트로 분할합니다."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = []
        # 헤더를 기준으로 텍스트 분할
        raw_sections = re.split(r"(?=\n\[)", content.strip())

        for idx, section in enumerate(raw_sections):
            section = section.strip()
            if not section:
                continue

            # 대괄호 안의 제목 추출
            match = self.header_pattern.search(section)
            header_title = match.group(1) if match else "기타"
            
            # 카테고리 및 법령 참조(law_ref) 자동 추출
            category = self._infer_category(header_title, section)
            law_ref = self._infer_law_ref(header_title)

            chunk = {
                "doc_id": f"{file_path.stem}_{idx:03d}",
                "title": header_title,
                "text": section,
                "category": category,
                "law_ref": law_ref,
                "source": file_path.name,
                "char_length": len(section),
            }
            chunks.append(chunk)

        return chunks

    def chunk_all_raw_data(self) -> List[Dict[str, Any]]:
        """data/raw/ 폴더에 있는 모든 원본 파일을 청킹합니다."""
        all_chunks = []
        for file_path in settings.RAW_DATA_DIR.glob("*.txt"):
            file_chunks = self.chunk_file(file_path)
            all_chunks.extend(file_chunks)
        return all_chunks

    def _infer_category(self, title: str, text: str) -> str:
        """문서 제목 및 본문 키워드를 분석하여 연말정산 카테고리를 분류합니다."""
        combined = f"{title} {text}"
        if "월세" in combined or "주거" in combined:
            return "월세액세액공제"
        elif "의료비" in combined or "안경" in combined or "산후조리원" in combined:
            return "의료비세액공제"
        elif "교육비" in combined or "학원" in combined:
            return "교육비세액공제"
        elif "신용카드" in combined or "현금영수증" in combined:
            return "신용카드등소득공제"
        elif "추가공제" in combined or "경로우대" in combined or "한부모" in combined:
            return "추가공제"
        elif "기본공제" in combined or "부양가족" in combined:
            return "기본공제"
        return "기타공제"

    def _infer_law_ref(self, title: str) -> str:
        """제목에서 관련 법조문명을 추출합니다."""
        if "소득세법" in title or "조세특례제한법" in title:
            # 예: 소득세법 제50조 (기본공제) -> 소득세법 제50조
            match = re.search(r"((?:소득세법|조세특례제한법)\s+제\d+(?:조의\d+)?(?:조)?)", title)
            if match:
                return match.group(1)
        return "국세청 안내지침"


if __name__ == "__main__":
    # 청커 단독 테스트 실행
    chunker = YetaChunker()
    chunks = chunker.chunk_all_raw_data()
    
    print(f"✅ 총 분할된 청크 수: {len(chunks)}개\n")
    for i, c in enumerate(chunks, 1):
        print(f"[{i}] ID: {c['doc_id']} | 카테고리: {c['category']} | 출처: {c['law_ref']}")
        print(f"    제목: {c['title']} ({c['char_length']}자)")
        print(f"    본문 미리보기: {c['text'][:60]}...\n")
