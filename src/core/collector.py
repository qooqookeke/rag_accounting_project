import os
from pathlib import Path
from typing import List, Dict, Any
from src.config import settings

class YetaDataCollector:
    """
    연말정산 데이터 수집 및 로더
    - 1차: 로컬에 정제된 법령 조문 및 국세청 가이드북 텍스트 로드 및 무결성 검증
    - 2차(고도화): 법제처 국가법령정보 Open API(open.law.go.kr)와의 실시간 동기화 인터페이스
    """

    def __init__(self):
        self.raw_dir = settings.RAW_DATA_DIR
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def get_local_source_files(self) -> List[Path]:
        """data/raw/ 디렉토리에 있는 유효한 원본 데이터 파일 목록을 반환합니다."""
        files = list(self.raw_dir.glob("*.txt")) + list(self.raw_dir.glob("*.pdf"))
        return sorted(files)

    def validate_data_sources(self) -> Dict[str, Any]:
        """수집된 원본 데이터 파일들의 존재 여부 및 용량을 점검합니다."""
        files = self.get_local_source_files()
        status = {
            "total_files": len(files),
            "files": []
        }
        for f in files:
            status["files"].append({
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "path": str(f)
            })
        return status

    def fetch_from_law_api(self, law_id: str = "001682") -> str:
        """
        [고도화 로드맵] 법제처 국가법령정보 Open API 연동 뼈대
        - API 키가 설정되어 있을 때 실시간 XML/JSON 조문 다운로드 수행
        """
        api_key = settings.LAW_API_KEY
        if not api_key or api_key == "your_law_api_key_here":
            return "[안내] LAW_API_KEY 미설정. 로컬 데이터셋(data/raw/)을 기본 소스로 사용합니다."

        # 향후 API 요청 로직 (open.law.go.kr)
        return f"[준비중] 법령 ID({law_id}) 실시간 수집 연동 준비 완료"


if __name__ == "__main__":
    collector = YetaDataCollector()
    summary = collector.validate_data_sources()
    print("📦 수집된 원본 데이터 현황:")
    print(f"총 파일 수: {summary['total_files']}개")
    for f in summary["files"]:
        print(f" - {f['name']} ({f['size_bytes']} bytes)")
