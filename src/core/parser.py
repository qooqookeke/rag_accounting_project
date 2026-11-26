import re
from pathlib import Path
from typing import Dict, Any, List

class YetaParser:
    """
    연말정산 원본 텍스트(.txt) 및 가이드북 PDF(.pdf) 문서의 구조를 추출하고 정제하는 파서
    """

    @staticmethod
    def parse_text_file(file_path: Path) -> List[Dict[str, Any]]:
        """텍스트 파일(.txt)에서 조문 및 문답 블록을 구조화하여 추출합니다."""
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        sections = []
        raw_blocks = re.split(r"(?=\n\[)", content.strip())

        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue

            match = re.match(r"^\[(.*?)\]", block)
            title = match.group(1) if match else "기타"
            body = block[match.end():].strip() if match else block

            sections.append({
                "title": title,
                "full_text": block,
                "body": body,
                "source": file_path.name,
                "file_type": "text"
            })

        return sections

    @staticmethod
    def parse_pdf_file(file_path: Path) -> List[Dict[str, Any]]:
        """
        PDF 파일(.pdf)에서 페이지별 텍스트 및 제목 구조를 추출합니다.
        - PyMuPDF(fitz) 라이브러리를 활용하여 페이지 단위로 파싱합니다.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PDF 파싱을 위해 pymupdf가 필요합니다. pip install pymupdf를 실행해 주세요.")

        doc = fitz.open(str(file_path))
        sections = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()
            if not text:
                continue

            # 페이지 첫 줄을 임시 제목으로 사용
            first_line = text.split("\n")[0].strip() if "\n" in text else text[:30]
            sections.append({
                "title": f"p.{page_num + 1} - {first_line[:40]}",
                "full_text": text,
                "page": page_num + 1,
                "source": file_path.name,
                "file_type": "pdf"
            })

        doc.close()
        return sections

    @staticmethod
    def parse_any(file_path: Path) -> List[Dict[str, Any]]:
        """확장자에 따라 적절한 파서를 자동 호출합니다."""
        ext = file_path.suffix.lower()
        if ext == ".txt":
            return YetaParser.parse_text_file(file_path)
        elif ext == ".pdf":
            return YetaParser.parse_pdf_file(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {ext} (지원 형식: .txt, .pdf)")

    @staticmethod
    def clean_text(text: str) -> str:
        """불필요한 공백 및 제어문자를 정제합니다."""
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


if __name__ == "__main__":
    from src.config import settings
    sample_file = settings.RAW_DATA_DIR / "yeta_laws_and_rules.txt"
    if sample_file.exists():
        parsed = YetaParser.parse_any(sample_file)
        print(f"✅ 텍스트 파싱 성공: {len(parsed)}개 섹션 추출")
        print(f"첫 번째 섹션 제목: {parsed[0]['title']}")
