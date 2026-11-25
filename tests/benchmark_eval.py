import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.core.retriever import YetaRetriever

# 🎯 연말정산 정량 평가용 골든 테스트셋 10종
GOLDEN_TEST_SET = [
    {
        "id": "Q01",
        "query": "총급여 6천만원인데 월세 세액공제 한도가 얼마야?",
        "expected_law_ref": "조세특례제한법 제95조의2",
        "expected_category": "월세액세액공제"
    },
    {
        "id": "Q02",
        "query": "주민등록상 세대원인데 월세 공제 받을 수 있나요?",
        "expected_law_ref": "국세청 안내지침",
        "expected_category": "월세액세액공제"
    },
    {
        "id": "Q03",
        "query": "시력보정용 안경 맞춘 것도 연말정산 의료비 공제 되나요?",
        "expected_law_ref": "국세청 안내지침",
        "expected_category": "의료비세액공제"
    },
    {
        "id": "Q04",
        "query": "산후조리원 지출 비용 의료비 세액공제 요건과 한도",
        "expected_law_ref": "국세청 안내지침",
        "expected_category": "의료비세액공제"
    },
    {
        "id": "Q05",
        "query": "본인 및 난임시술비 의료비 세액공제율은 몇 퍼센트인가요?",
        "expected_law_ref": "소득세법 제59조의4",
        "expected_category": "의료비세액공제"
    },
    {
        "id": "Q06",
        "query": "맞벌이 부부인 경우 자녀 기본공제는 누가 받는 것이 유리한가요?",
        "expected_law_ref": "국세청 안내지침",
        "expected_category": "기본공제"
    },
    {
        "id": "Q07",
        "query": "부양가족 1인당 인적공제 기본공제 금액과 나이 소득 요건",
        "expected_law_ref": "소득세법 제50조",
        "expected_category": "기본공제"
    },
    {
        "id": "Q08",
        "query": "70세 이상 부모님 모실 때 경로우대자 추가공제 금액",
        "expected_law_ref": "소득세법 제51조",
        "expected_category": "추가공제"
    },
    {
        "id": "Q09",
        "query": "초등학생 자녀 태권도 피아노 학원비 교육비 공제 가능한가요?",
        "expected_law_ref": "국세청 안내지침",
        "expected_category": "교육비세액공제"
    },
    {
        "id": "Q10",
        "query": "신용카드와 체크카드 현금영수증 공제율 및 기본 한도 차이",
        "expected_law_ref": "조세특례제한법 제126조의2",
        "expected_category": "신용카드등소득공제"
    }
]

def run_benchmark():
    """10개 표준 질문에 대해 Top-1, Top-3 적중률 및 MRR, 응답 지연시간을 정량 측정합니다."""
    retriever = YetaRetriever()
    
    total = len(GOLDEN_TEST_SET)
    top1_hits = 0
    top3_hits = 0
    reciprocal_ranks = []
    latencies = []

    print("=" * 70)
    print("📊 [Yeta-RAG] 검색 엔진 정량 평가 벤치마크 (Quantitative Benchmark)")
    print(f"   테스트 케이스 수: {total}개 | 평가 지표: Hit@1, Hit@3, MRR, Latency")
    print("=" * 70)

    for case in GOLDEN_TEST_SET:
        start_t = time.perf_counter()
        results = retriever.search(query=case["query"], top_k=3)
        latency_ms = (time.perf_counter() - start_t) * 1000
        latencies.append(latency_ms)

        expected_law = case["expected_law_ref"]
        expected_cat = case["expected_category"]

        # Hit 판정
        hit_rank = 0
        for rank, r in enumerate(results, 1):
            if expected_law in r["law_ref"] or expected_cat in r["category"]:
                hit_rank = rank
                break

        if hit_rank == 1:
            top1_hits += 1
            top3_hits += 1
            reciprocal_ranks.append(1.0)
            status = "✅ Top-1 Hit"
        elif 1 < hit_rank <= 3:
            top3_hits += 1
            reciprocal_ranks.append(1.0 / hit_rank)
            status = f"🔵 Top-{hit_rank} Hit"
        else:
            reciprocal_ranks.append(0.0)
            status = "❌ Miss"

        print(f"[{case['id']}] {case['query'][:35]}... -> {status} ({latency_ms:.1f}ms)")

    hit_rate_1 = (top1_hits / total) * 100
    hit_rate_3 = (top3_hits / total) * 100
    mrr = sum(reciprocal_ranks) / total
    avg_latency = sum(latencies) / total

    print("\n" + "=" * 70)
    print("🏆 [최종 정량 평가 벤치마크 결과]")
    print(f" • Hit Rate @ 1 (Top-1 정확도) : {hit_rate_1:.1f}% ({top1_hits}/{total})")
    print(f" • Hit Rate @ 3 (Top-3 적중률) : {hit_rate_3:.1f}% ({top3_hits}/{total})")
    print(f" • MRR (Mean Reciprocal Rank)  : {mrr:.3f}")
    print(f" • 평균 검색 지연시간 (Latency) : {avg_latency:.1f} ms")
    print("=" * 70)

    return {
        "hit_rate_1": hit_rate_1,
        "hit_rate_3": hit_rate_3,
        "mrr": mrr,
        "avg_latency_ms": avg_latency
    }

if __name__ == "__main__":
    run_benchmark()
