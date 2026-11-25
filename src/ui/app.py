import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import streamlit as st
from src.llm.chain import YetaRAGChain

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="Yeta-RAG | 연말정산 전문 AI 상담관",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. RAG 체인 캐싱 (매 턴마다 다시 로드하지 않도록 성능 최적화)
@st.cache_resource
def get_rag_chain():
    return YetaRAGChain()

rag_chain = get_rag_chain()

# 3. 사이드바 구성
with st.sidebar:
    st.title("🏛️ Yeta-RAG 설정")
    st.markdown("근로소득 연말정산에 특화된 **법적 근거 기반(Citation)** AI 상담 서비스입니다.")
    st.divider()

    # 검색 옵션
    st.subheader("⚙️ 검색 파라미터")
    top_k = st.slider("참고할 상위 법률 문서 수 (Top-K)", min_value=1, max_value=5, value=3)
    
    category_options = ["전체 (자동 분류)", "월세액세액공제", "의료비세액공제", "교육비세액공제", "신용카드등소득공제", "기본공제", "추가공제"]
    selected_category = st.selectbox("특정 공제 카테고리 필터", category_options)
    filter_val = None if selected_category.startswith("전체") else selected_category

    st.divider()

    # 인덱스 상태 모니터링
    try:
        doc_count = rag_chain.retriever.collection.count()
        st.success(f"🟢 벡터 DB 정상 연결\n\n(인덱싱된 지식 청크: **{doc_count}개**)")
    except Exception as e:
        st.error(f"🔴 DB 연결 오류: {e}")

    st.divider()

    # 자주 묻는 질문 퀵 버튼
    st.subheader("💡 자주 묻는 질문 예시")
    faq_examples = [
        "총급여 6천만원인데 월세 세액공제 한도가 얼마야?",
        "시력교정용 안경 맞춘 것도 의료비 공제 돼?",
        "맞벌이 부부인데 자녀 공제는 누가 받아야 유리해?",
        "초등학생 자녀 태권도 학원비도 교육비 공제 돼?"
    ]
    
    for faq in faq_examples:
        if st.button(faq, use_container_width=True):
            st.session_state["quick_prompt"] = faq

# 4. 메인 화면 헤더
st.title("🏛️ 국세청 연말정산 전문 AI 상담관")
st.caption("소득세법, 조세특례제한법 및 국세청 공식 가이드북에 근거하여 환각 없는 정확한 답변을 제공합니다.")

# 5. 세션 상태 관리 (대화 기록)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "안녕하세요! 국세청 연말정산 전문 AI 상담관입니다.\n\n월세액 세액공제, 의료비, 교육비, 신용카드 소득공제 등 연말정산에 대해 궁금한 점을 편하게 질문해 주세요. 법조문 근거와 함께 안내해 드립니다."
        }
    ]

# 6. 이전 대화 기록 렌더링
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # 인용 출처가 있는 경우 아코디언으로 표시
        if "sources" in msg and msg["sources"]:
            with st.expander("📚 참고한 법적 근거 (Citation)", expanded=False):
                for s in msg["sources"]:
                    st.markdown(f"**[{s['rank']}위] {s['law_ref']} ({s['title']})** `유사도: {s['score']*100:.1f}%`")
                    st.caption(f"카테고리: {s['category']}")
                    st.text(s["text_snippet"])
                    st.divider()

# 7. 사용자 입력 처리 (채팅창 입력 또는 퀵 버튼 클릭)
prompt = st.chat_input("연말정산 질문을 입력하세요 (예: 연봉 5천만원일 때 신용카드 공제 기준 알려줘)")
if "quick_prompt" in st.session_state and st.session_state["quick_prompt"]:
    prompt = st.session_state.pop("quick_prompt")

if prompt:
    # 7-1. 사용자 메시지 추가 및 화면 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 7-2. AI 답변 생성 (스피너 표시)
    with st.chat_message("assistant"):
        with st.spinner("🔍 관련 소득세법 조문 및 국세청 가이드를 검색 중입니다..."):
            result = rag_chain.run(
                query=prompt,
                top_k=top_k,
                category_filter=filter_val
            )
            answer_text = result["answer"]
            sources = result["sources"]

        st.markdown(answer_text)

        # 7-3. 출처 아코디언 표시
        if sources:
            with st.expander("📚 참고한 법적 근거 (Citation)", expanded=True):
                for s in sources:
                    st.markdown(f"**[{s['rank']}위] {s['law_ref']} ({s['title']})** `유사도: {s['score']*100:.1f}%`")
                    st.caption(f"카테고리: {s['category']}")
                    st.text(s["text_snippet"])
                    st.divider()

    # 7-4. 세션 기록에 추가
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer_text,
        "sources": sources
    })
