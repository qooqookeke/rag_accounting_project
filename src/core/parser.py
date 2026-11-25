import re
from pathlib import Path
from typing import Dict, Any, List

class YetaParser:
    """
    연말정산 원본 텍스트 및 PDF 문서의 구조(제목, 법령 조문, 본문)를 추출하고 정제하는 파서
    """

    @staticmethod
    def parse_text_file(file_path: Path) -> List[Dict[str, Any]]:
        """텍스트 파일에서 조문 및 문답 블록을 구조화하여 추출합니다."""
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
                "source": file_path.name
            })

        return sections

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
        parsed = YetaParser.parse_text_file(sample_file)
        print(f"✅ 파싱 성공: {len(parsed)}개 섹션 추출")
        print(f"첫 번째 섹션 제목: {parsed[0]['title']}")
